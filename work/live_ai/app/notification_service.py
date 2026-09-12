from __future__ import annotations

import json, os, threading, time
from datetime import date, datetime
from pathlib import Path

from .db import connect, now

FIREBASE_CREDENTIALS = Path(os.getenv("FIREBASE_CREDENTIALS", "/etc/renewpro/firebase-service-account.json"))
_firebase_app = None
_worker_started = False


def _settings(con=None):
    owns = con is None
    if owns:
        ctx = connect(); con = ctx.__enter__()
    try:
        row = con.execute("SELECT * FROM notification_settings WHERE id=1").fetchone()
        result = dict(row) if row else {}
        try: result["threshold_days"] = sorted(set(int(x) for x in json.loads(result.get("threshold_days") or "[]") if int(x) > 0))
        except Exception: result["threshold_days"] = [30,45,60,90]
        for key in ("enabled","stock_created"): result[key] = bool(result.get(key))
        return result
    finally:
        if owns: ctx.__exit__(None,None,None)


def _vehicle_name(row):
    return " ".join(str(row.get(k) or "").strip() for k in ("brand","model","version")).strip() or "Araç"


def _render(template, row, days=0):
    values={"plate":row.get("plate") or "Araç", "vehicle":_vehicle_name(row), "days":days}
    try: return str(template).format(**values)
    except Exception: return str(template)


def _firebase():
    global _firebase_app
    if _firebase_app is not None: return _firebase_app
    if not FIREBASE_CREDENTIALS.exists(): return None
    import firebase_admin
    from firebase_admin import credentials
    try: _firebase_app = firebase_admin.get_app()
    except ValueError: _firebase_app = firebase_admin.initialize_app(credentials.Certificate(str(FIREBASE_CREDENTIALS)))
    return _firebase_app


def _send_tokens(tokens, title, body, target_url="/"):
    if not tokens or not _firebase(): return {"sent":0,"failed":0,"disabled":[]}
    from firebase_admin import messaging
    message=messaging.MulticastMessage(
        notification=messaging.Notification(title=title,body=body),
        data={"url":target_url,"title":title,"body":body}, tokens=tokens,
        webpush=messaging.WebpushConfig(fcm_options=messaging.WebpushFCMOptions(link="https://renewpanel.xyz"+target_url))
    )
    response=messaging.send_each_for_multicast(message)
    dead=[]
    for idx,item in enumerate(response.responses):
        if not item.success and item.exception and any(x in str(item.exception).lower() for x in ("unregistered","registration-token-not-registered","invalid argument")):
            dead.append(tokens[idx])
    if dead:
        with connect() as con: con.executemany("UPDATE push_subscriptions SET active=0 WHERE token=?",[(x,) for x in dead])
    return {"sent":response.success_count,"failed":response.failure_count,"disabled":dead}


def _active_tokens(con):
    return [r["token"] for r in con.execute("SELECT token FROM push_subscriptions WHERE active=1").fetchall()]


def create_notification(event_key, event_type, title, body, vehicle_id=None, target_url="/", send=True):
    with connect() as con:
        exists=con.execute("SELECT id FROM notifications WHERE event_key=?",(event_key,)).fetchone()
        if exists: return {"created":False,"id":exists["id"],"sent":0}
        cur=con.execute("INSERT INTO notifications(user_id,vehicle_id,event_key,event_type,title,body,target_url,created_at) VALUES(NULL,?,?,?,?,?,?,?)",
                        (vehicle_id,event_key,event_type,title,body,target_url,now()))
        nid=cur.lastrowid; tokens=_active_tokens(con)
    result=_send_tokens(tokens,title,body,target_url) if send else {"sent":0,"failed":0}
    if result.get("sent"):
        with connect() as con: con.execute("UPDATE notifications SET sent_at=? WHERE id=?",(now(),nid))
    return {"created":True,"id":nid,**result}


def notify_stock_created(vehicle):
    settings=_settings()
    if not settings.get("enabled") or not settings.get("stock_created"): return
    vid=vehicle.get("id")
    create_notification(
        f"stock-created:{vid}","stock_created",
        _render(settings.get("stock_created_title"),vehicle),
        _render(settings.get("stock_created_body"),vehicle),vid,
        f"/?page=vehicle360&plate={vehicle.get('plate','')}"
    )


def run_stock_checks(force_send=False):
    with connect() as con:
        settings=_settings(con)
        if not settings.get("enabled"): return {"checked":0,"created":0,"sent":0}
        rows=[dict(r) for r in con.execute("SELECT * FROM vehicles WHERE status='STOCK' AND purchase_date IS NOT NULL").fetchall()]
    checked=created=sent=0
    today=date.today()
    for row in rows:
        try: days=max(0,(today-date.fromisoformat(str(row["purchase_date"])[:10])).days)
        except Exception: continue
        checked+=1
        for threshold in settings["threshold_days"]:
            if days < threshold: continue
            result=create_notification(
                f"stock-age:{row['id']}:{threshold}","stock_age",
                _render(settings.get("title_template"),row,days),
                _render(settings.get("body_template"),row,days),row["id"],
                f"/?page=vehicle360&plate={row.get('plate','')}",send=force_send or not _quiet_now(settings)
            )
            created+=int(result.get("created",False));sent+=int(result.get("sent",0))
    return {"checked":checked,"created":created,"sent":sent}


def _quiet_now(settings):
    try:
        current=datetime.now().strftime("%H:%M"); start=settings.get("quiet_start") or "22:00"; end=settings.get("quiet_end") or "08:00"
        return (start <= current < end) if start < end else (current >= start or current < end)
    except Exception: return False


def start_worker():
    global _worker_started
    if _worker_started:return
    _worker_started=True
    def loop():
        time.sleep(30)
        while True:
            try: run_stock_checks()
            except Exception: pass
            time.sleep(900)
    threading.Thread(target=loop,name="renew-notifications",daemon=True).start()

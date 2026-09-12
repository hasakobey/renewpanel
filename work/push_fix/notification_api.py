from __future__ import annotations

import json
import secrets
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from .db import connect, now, log
from .notification_service import _render, _settings, _send_tokens, create_notification, run_stock_checks

router=APIRouter(prefix="/api/notifications",tags=["notifications"])

FIREBASE_PUBLIC={
  "apiKey":"AIzaSyC0dSWVPNfT9str9wo-BLro5xoMyQnvC6s",
  "authDomain":"renew-43298.firebaseapp.com",
  "projectId":"renew-43298",
  "storageBucket":"renew-43298.firebasestorage.app",
  "messagingSenderId":"343449047493",
  "appId":"1:343449047493:web:3f28664b43242b00ce3bac",
  "measurementId":"G-V81QFG7EEQ"
}
PUBLIC_VAPID="BJ4d7BpFsNpaBW29V0vvs0_k6J09VnkpKfJ1umtKRMrOOPo7xk3yxM2PVtlY4jHbsVBzJUwQ98sBJw6DjXTXltE"

class SubscriptionIn(BaseModel):
    token:str
    device_name:str="Tarayıcı"
    platform:str="web"

class SettingsIn(BaseModel):
    enabled:bool=True
    stock_created:bool=True
    threshold_days:list[int]=[30,45,60,90]
    title_template:str="{plate} stok uyarısı"
    body_template:str="{plate} plakalı {vehicle}, {days} gündür stokta."
    stock_created_title:str="Yeni araç stoğa eklendi"
    stock_created_body:str="{plate} plakalı {vehicle} stoğa eklendi."
    quiet_start:str="22:00"
    quiet_end:str="08:00"
    daily_digest_time:str="09:00"

class ManualNotificationIn(BaseModel):
    vehicle_id:int|None=None
    topic:str="vehicle"
    icon:str="🚗"
    title:str
    body:str

@router.get("")
def notification_center(request:Request):
    uid=request.state.user["id"]
    with connect() as con:
        rows=[dict(r) for r in con.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT 200").fetchall()]
        devices=[dict(r) for r in con.execute("SELECT id,device_name,platform,active,created_at,last_seen_at FROM push_subscriptions WHERE user_id=? ORDER BY id DESC",(uid,)).fetchall()]
        unread=con.execute("SELECT COUNT(*) n FROM notifications WHERE read_at IS NULL").fetchone()["n"]
        vehicles=[dict(r) for r in con.execute("SELECT id,plate,brand,model,version,purchase_date FROM vehicles WHERE status='STOCK' ORDER BY brand,model,plate").fetchall()]
    return {"firebase":FIREBASE_PUBLIC,"vapidKey":PUBLIC_VAPID,"settings":_settings(),"notifications":rows,"devices":devices,"vehicles":vehicles,"unread":unread}

@router.post("/subscribe")
def subscribe(x:SubscriptionIn,request:Request):
    token=x.token.strip()
    if len(token)<30:raise HTTPException(400,"Geçersiz bildirim cihaz anahtarı.")
    uid=request.state.user["id"]
    with connect() as con:
        con.execute("""INSERT INTO push_subscriptions(user_id,token,device_name,platform,active,created_at,last_seen_at)
          VALUES(?,?,?,?,1,?,?) ON CONFLICT(token) DO UPDATE SET user_id=excluded.user_id,device_name=excluded.device_name,
          platform=excluded.platform,active=1,last_seen_at=excluded.last_seen_at""",(uid,token,x.device_name[:100],x.platform[:50],now(),now()))
    log("notification",uid,"SUBSCRIBE",f"Bildirim cihazı bağlandı: {x.device_name[:100]}")
    return {"ok":True}

@router.delete("/devices/{device_id}")
def remove_device(device_id:int,request:Request):
    with connect() as con: con.execute("DELETE FROM push_subscriptions WHERE id=? AND user_id=?",(device_id,request.state.user["id"]))
    return {"ok":True}

@router.post("/settings")
def save_notification_settings(x:SettingsIn):
    days=sorted(set(int(v) for v in x.threshold_days if 1<=int(v)<=3650))
    if not days:raise HTTPException(400,"En az bir stok günü eşiği belirleyin.")
    if any(len(v)>300 for v in (x.title_template,x.body_template,x.stock_created_title,x.stock_created_body)):
        raise HTTPException(400,"Bildirim şablonu çok uzun.")
    with connect() as con:
        con.execute("""UPDATE notification_settings SET enabled=?,stock_created=?,threshold_days=?,title_template=?,body_template=?,
          stock_created_title=?,stock_created_body=?,quiet_start=?,quiet_end=?,daily_digest_time=?,updated_at=? WHERE id=1""",
          (int(x.enabled),int(x.stock_created),json.dumps(days),x.title_template,x.body_template,x.stock_created_title,
           x.stock_created_body,x.quiet_start,x.quiet_end,x.daily_digest_time,now()))
    log("notification","settings","UPDATE","Bildirim ayarları güncellendi")
    return {"ok":True,"settings":_settings()}

@router.post("/test")
def test_notification(request:Request):
    uid=request.state.user["id"]
    with connect() as con: tokens=[r["token"] for r in con.execute("SELECT token FROM push_subscriptions WHERE user_id=? AND active=1",(uid,)).fetchall()]
    if not tokens:raise HTTPException(400,"Önce bu cihazda bildirimleri açın.")
    result=_send_tokens(tokens,"RENEW PRO test bildirimi","Bildirim bağlantısı başarıyla çalışıyor.","/?page=notifications")
    return {"ok":True,**result}

@router.post("/manual")
def manual_notification(x:ManualNotificationIn,request:Request):
    title=x.title.strip();body=x.body.strip()
    topics={"vehicle":"Araç Bildirimi","important":"Önemli","reminder":"Hatırlatma","general":"Genel Duyuru"}
    icons={"🚗","⚠️","⏰","📢","💰","🔍","✅","📌"}
    if x.topic not in topics:raise HTTPException(400,"Geçersiz bildirim konusu.")
    if x.icon not in icons:raise HTTPException(400,"Geçersiz bildirim ikonu.")
    if x.topic=="vehicle" and not x.vehicle_id:raise HTTPException(400,"Araç bildirimi için araç seçimi zorunludur.")
    if not title:raise HTTPException(400,"Bildirim başlığı zorunludur.")
    if not body:raise HTTPException(400,"Bildirim açıklaması zorunludur.")
    if len(title)>100:raise HTTPException(400,"Bildirim başlığı en fazla 100 karakter olabilir.")
    if len(body)>500:raise HTTPException(400,"Bildirim açıklaması en fazla 500 karakter olabilir.")
    vehicle=None
    if x.vehicle_id:
        with connect() as con: row=con.execute("SELECT * FROM vehicles WHERE id=? AND status='STOCK'",(x.vehicle_id,)).fetchone()
        if not row:raise HTTPException(404,"Seçilen stok aracı bulunamadı.")
        vehicle=dict(row)
    context=vehicle or {"plate":"","brand":"","model":"","version":""}
    rendered_title=_render(title,context)
    rendered_body=_render(body,context)
    if x.topic=="important" and not rendered_title.startswith("ÖNEMLİ"):
        rendered_title=f"ÖNEMLİ • {rendered_title}"
    rendered_title=f"{x.icon} {rendered_title}"
    result=create_notification(
        f"manual:{now()}:{secrets.token_hex(5)}",f"manual_{x.topic}",rendered_title,rendered_body,
        vehicle["id"] if vehicle else None,
        f"/?page=vehicle360&plate={vehicle.get('plate','')}" if vehicle else "/?page=notifications"
    )
    log("notification",result.get("id","manual"),"MANUAL_SEND",f"{topics[x.topic]} • {(vehicle or {}).get('plate','')} • {rendered_title}")
    return {"ok":True,"topic":x.topic,"title":rendered_title,"body":rendered_body,**result}

@router.post("/run-check")
def run_check(): return {"ok":True,**run_stock_checks(force_send=True)}

@router.post("/{notification_id}/read")
def mark_read(notification_id:int):
    with connect() as con: con.execute("UPDATE notifications SET read_at=COALESCE(read_at,?) WHERE id=?",(now(),notification_id))
    return {"ok":True}

@router.post("/read-all")
def mark_all_read():
    with connect() as con: con.execute("UPDATE notifications SET read_at=COALESCE(read_at,?)",(now(),))
    return {"ok":True}

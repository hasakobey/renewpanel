from __future__ import annotations
import hashlib, hmac, os, secrets, json
from datetime import datetime, timedelta
from .db import connect, now
from .auth_context import current_user_id,current_username,current_ip

PERMISSION_LABELS={
 "dashboard.view":"Dashboard Görüntüleme",
 "stocks.view":"Güncel Stok Görüntüleme",
 "stocks.edit":"Güncel Stok Düzenleme",
 "sales.view":"Satılan Araçlar Görüntüleme",
 "sales.edit":"Satış Düzenleme",
 "acquisitions.view":"Aylık Alımlar Görüntüleme",
 "acquisitions.edit":"Aylık Alım Düzenleme",
 "expertise.view":"Ekspertiz Görüntüleme",
 "expertise.edit":"Ekspertiz Düzenleme",
 "performance.view":"Danışman Performansı",
 "settings.view":"Parametreleri Görüntüleme",
 "settings.edit":"Parametreleri Düzenleme",
 "imports.use":"Excel Aktarım / Ana Excel",
 "reports.view":"Raporlar / Excel Çıktıları",
 "media.view":"Araç Medya Görüntüleme",
 "media.edit":"Araç Medya Düzenleme",
 "audit.view":"İşlem Geçmişi",
 "users.manage":"Kullanıcı & Yetki Yönetimi",
 "backup.use":"Yedek Alma"
}
ALL_PERMISSIONS=list(PERMISSION_LABELS)

ROLE_DEFAULTS={
 "administrator":ALL_PERMISSIONS,
 "manager":[p for p in ALL_PERMISSIONS if p!="users.manage"],
 "editor":["dashboard.view","stocks.view","stocks.edit","sales.view","sales.edit","acquisitions.view","acquisitions.edit",
           "expertise.view","expertise.edit","performance.view","reports.view","media.view","media.edit","imports.use"],
 "viewer":["dashboard.view","stocks.view","sales.view","acquisitions.view","expertise.view","performance.view","reports.view","media.view"]
}

def hash_password(password:str)->str:
    salt=os.urandom(16)
    dk=hashlib.pbkdf2_hmac("sha256",password.encode("utf-8"),salt,200_000)
    return f"pbkdf2_sha256$200000${salt.hex()}${dk.hex()}"

def verify_password(password:str,encoded:str)->bool:
    try:
        alg,it,salt_hex,digest_hex=encoded.split("$")
        if alg!="pbkdf2_sha256":return False
        dk=hashlib.pbkdf2_hmac("sha256",password.encode("utf-8"),bytes.fromhex(salt_hex),int(it))
        return hmac.compare_digest(dk.hex(),digest_hex)
    except:return False

def permissions_json(role:str,permissions=None):
    vals=permissions if permissions is not None else ROLE_DEFAULTS.get(role,ROLE_DEFAULTS["viewer"])
    vals=[x for x in vals if x in ALL_PERMISSIONS]
    return json.dumps(sorted(set(vals)),ensure_ascii=False)

def parse_permissions(raw,role="viewer"):
    if role=="administrator":return set(ALL_PERMISSIONS)
    try:return set(json.loads(raw or "[]"))
    except:return set()

def ensure_default_admin():
    with connect() as con:
        r=con.execute("SELECT id FROM users WHERE role='administrator' LIMIT 1").fetchone()
        if not r:
            con.execute("""INSERT INTO users(username,full_name,password_hash,role,permissions,active,must_change_password,created_at,updated_at)
              VALUES(?,?,?,?,?,1,1,?,?)""",
              ("administrator","Administrator",hash_password("Renew@2026"),"administrator",permissions_json("administrator"),now(),now()))

def authenticate(username,password):
    with connect() as con:
        r=con.execute("SELECT * FROM users WHERE lower(username)=lower(?) AND active=1",(username.strip(),)).fetchone()
        if not r or not verify_password(password,r["password_hash"]):return None
        return dict(r)

def create_session(user_id:int, ip_address='', user_agent=''):
    token=secrets.token_urlsafe(40)
    expires=(datetime.now()+timedelta(hours=12)).isoformat(timespec="seconds")
    with connect() as con:
        con.execute("DELETE FROM user_sessions WHERE expires_at<?",(now(),))
        csrf=secrets.token_urlsafe(32)
        con.execute("INSERT INTO user_sessions(token,user_id,expires_at,created_at,csrf_token,last_seen_at,ip_address,user_agent) VALUES(?,?,?,?,?,?,?,?)",(token,user_id,expires,now(),csrf,now(),ip_address,user_agent))
    return token,csrf

def get_user_by_session(token):
    if not token:return None
    with connect() as con:
        r=con.execute("""SELECT u.*,s.csrf_token AS session_csrf,s.last_seen_at AS session_last_seen,s.ip_address AS session_ip,s.user_agent AS session_user_agent FROM user_sessions s JOIN users u ON u.id=s.user_id WHERE s.token=? AND s.expires_at>=? AND u.active=1""",(token,now())).fetchone()
        return dict(r) if r else None

def delete_session(token):
    if not token:return
    with connect() as con:con.execute("DELETE FROM user_sessions WHERE token=?",(token,))

def public_user(u):
    return {"id":u["id"],"username":u["username"],"full_name":u["full_name"],"role":u["role"],
            "permissions":sorted(parse_permissions(u.get("permissions"),u.get("role"))),
            "active":bool(u["active"]),"must_change_password":bool(u["must_change_password"])}

def has_permission(user,permission):
    if not user:return False
    if user.get("role")=="administrator":return True
    return permission in parse_permissions(user.get("permissions"),user.get("role"))

def required_permission(path,method):
    # Auth endpoints handled separately.
    if path.startswith("/api/users"):return "users.manage"
    if path.startswith("/api/mail-config"):return "settings.edit" if method!="GET" else "settings.view"
    if path.startswith("/api/audit"):return "audit.view"
    if path.startswith("/api/backup"):return "backup.use"
    if path.startswith("/api/settings") or path.startswith("/api/rules") or path.startswith("/api/sale-types") or path.startswith("/api/income-types") or path.startswith("/api/consultants"):
        return "settings.edit" if method!="GET" else "settings.view"
    if path.startswith("/api/import") or path.startswith("/api/master"):return "imports.use"
    if path.startswith("/api/report") or path.startswith("/api/export") or path.startswith("/api/template"):return "reports.view"
    if path.startswith("/api/media") or path.startswith("/api/photos"):
        return "media.edit" if method!="GET" else "media.view"
    if path.startswith("/api/stocks"):return "stocks.edit" if method!="GET" else "stocks.view"
    if path.startswith("/api/sales"):return "sales.edit" if method!="GET" else "sales.view"
    if path.startswith("/api/acquisitions"):return "acquisitions.edit" if method!="GET" else "acquisitions.view"
    if path.startswith("/api/expertise"):return "expertise.edit" if method!="GET" else "expertise.view"
    if path.startswith("/api/performance"):return "performance.view"
    if path.startswith("/api/dashboard") or path.startswith("/api/vehicle-card") or path.startswith("/api/vehicle-sources"):return "dashboard.view"
    return None

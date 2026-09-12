from datetime import datetime,timedelta
from fastapi import HTTPException
from .db import connect,now
MAX_FAILS=5
LOCK_MINUTES=15
IDLE_MINUTES=30

def ensure_security_tables():
    with connect() as con:
        con.execute('CREATE TABLE IF NOT EXISTS login_security(username TEXT PRIMARY KEY,fail_count INTEGER NOT NULL DEFAULT 0,locked_until TEXT,last_fail_at TEXT)')
        cols={r['name'] for r in con.execute('PRAGMA table_info(user_sessions)').fetchall()}
        for name,typ in [('csrf_token','TEXT'),('last_seen_at','TEXT'),('ip_address','TEXT'),('user_agent','TEXT')]:
            if name not in cols: con.execute(f'ALTER TABLE user_sessions ADD COLUMN {name} {typ}')

def password_policy(p):
    if len(p)<10: raise HTTPException(400,'Şifre en az 10 karakter olmalı.')
    if not any(c.isupper() for c in p): raise HTTPException(400,'Şifre en az 1 büyük harf içermeli.')
    if not any(c.islower() for c in p): raise HTTPException(400,'Şifre en az 1 küçük harf içermeli.')
    if not any(c.isdigit() for c in p): raise HTTPException(400,'Şifre en az 1 rakam içermeli.')
    if not any(not c.isalnum() for c in p): raise HTTPException(400,'Şifre en az 1 özel karakter içermeli.')

def is_locked(username):
    with connect() as con:r=con.execute('SELECT * FROM login_security WHERE lower(username)=lower(?)',(username,)).fetchone()
    if not r or not r['locked_until']: return False,None
    try:
        u=datetime.fromisoformat(r['locked_until'])
        return (datetime.now()<u,u)
    except:return False,None

def record_fail(username):
    with connect() as con:
        r=con.execute('SELECT * FROM login_security WHERE lower(username)=lower(?)',(username,)).fetchone()
        c=(r['fail_count'] if r else 0)+1
        lock=(datetime.now()+timedelta(minutes=LOCK_MINUTES)).isoformat(timespec='seconds') if c>=MAX_FAILS else None
        con.execute('INSERT INTO login_security(username,fail_count,locked_until,last_fail_at) VALUES(?,?,?,?) ON CONFLICT(username) DO UPDATE SET fail_count=excluded.fail_count,locked_until=excluded.locked_until,last_fail_at=excluded.last_fail_at',(username,c,lock,now()))
    return c,lock

def clear_fail(username):
    with connect() as con:con.execute('DELETE FROM login_security WHERE lower(username)=lower(?)',(username,))

def touch_session(token):
    with connect() as con:con.execute('UPDATE user_sessions SET last_seen_at=? WHERE token=?',(now(),token))

def idle_expired(last_seen):
    if not last_seen:return False
    try:return datetime.now()-datetime.fromisoformat(last_seen)>timedelta(minutes=IDLE_MINUTES)
    except:return False

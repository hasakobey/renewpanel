from __future__ import annotations
import sqlite3, shutil, tarfile
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime

BASE = Path(__file__).resolve().parents[1]
DB_PATH = BASE / "data" / "renew.db"
BACKUP_DIR = BASE / "backups"

SCHEMA = """
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS settings(
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  value_type TEXT NOT NULL DEFAULT 'text',
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS purchase_rules(
  name TEXT PRIMARY KEY,
  apply_sks INTEGER NOT NULL DEFAULT 0,
  apply_fixed INTEGER NOT NULL DEFAULT 1,
  active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS sale_types(
  name TEXT PRIMARY KEY,
  active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS income_types(
  name TEXT PRIMARY KEY,
  active INTEGER NOT NULL DEFAULT 1,
  description TEXT
);

CREATE TABLE IF NOT EXISTS consultants(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  active INTEGER NOT NULL DEFAULT 1,
  target_sales INTEGER NOT NULL DEFAULT 0,
  target_profit REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS vehicles(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  plate TEXT NOT NULL UNIQUE,
  model_year INTEGER,
  km INTEGER,
  brand TEXT,
  model TEXT,
  version TEXT,
  color TEXT,
  fuel TEXT,
  transmission TEXT,
  purchase_date TEXT,
  purchase_type TEXT,
  purchase_price REAL NOT NULL DEFAULT 0,
  list_price REAL NOT NULL DEFAULT 0,
  target_profit REAL NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'STOCK',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sales(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  vehicle_id INTEGER,
  plate TEXT NOT NULL,
  vehicle_info TEXT,
  model_year INTEGER,
  purchase_type TEXT,
  purchase_price REAL NOT NULL DEFAULT 0,
  purchase_date TEXT,
  sale_date TEXT NOT NULL,
  extra_expense REAL NOT NULL DEFAULT 0,
  customer TEXT,
  sale_type TEXT,
  sale_price REAL NOT NULL DEFAULT 0,
  consultant TEXT,
  insurance_income REAL NOT NULL DEFAULT 0,
  credit_income REAL NOT NULL DEFAULT 0,
  warranty_income REAL NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(vehicle_id) REFERENCES vehicles(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS acquisitions(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  purchase_date TEXT NOT NULL,
  plate TEXT NOT NULL,
  model_year INTEGER,
  km INTEGER NOT NULL DEFAULT 0,
  brand TEXT, model TEXT, version TEXT, color TEXT, fuel TEXT, transmission TEXT,
  purchase_type TEXT,
  acquired_by TEXT NOT NULL,
  purchase_price REAL NOT NULL DEFAULT 0,
  expense REAL NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS expertise(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  consultant TEXT NOT NULL,
  month TEXT NOT NULL,
  done_count INTEGER NOT NULL DEFAULT 0,
  converted_count INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL,
  UNIQUE(consultant, month)
);

CREATE TABLE IF NOT EXISTS import_history(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  import_type TEXT NOT NULL,
  file_name TEXT,
  mode TEXT,
  sales_count INTEGER NOT NULL DEFAULT 0,
  stock_count INTEGER NOT NULL DEFAULT 0,
  expertise_count INTEGER NOT NULL DEFAULT 0,
  consultant_count INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stock_monthly_snapshots(
  month TEXT NOT NULL,
  plate TEXT NOT NULL,
  data_json TEXT NOT NULL,
  captured_at TEXT NOT NULL,
  source TEXT NOT NULL DEFAULT 'carry_forward',
  PRIMARY KEY(month, plate)
);
CREATE INDEX IF NOT EXISTS idx_stock_snapshot_month ON stock_monthly_snapshots(month);



CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  full_name TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'viewer',
  permissions TEXT NOT NULL DEFAULT '[]',
  active INTEGER NOT NULL DEFAULT 1,
  must_change_password INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_sessions(
  token TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL,
  expires_at TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_log(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entity TEXT NOT NULL,
  entity_id TEXT,
  action TEXT NOT NULL,
  details TEXT,
  username TEXT,
  user_id INTEGER,
  old_value TEXT,
  new_value TEXT,
  ip_address TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notification_settings(
  id INTEGER PRIMARY KEY CHECK(id=1),
  enabled INTEGER NOT NULL DEFAULT 1,
  stock_created INTEGER NOT NULL DEFAULT 1,
  threshold_days TEXT NOT NULL DEFAULT '[30,45,60,90]',
  title_template TEXT NOT NULL DEFAULT '{plate} stok uyarısı',
  body_template TEXT NOT NULL DEFAULT '{plate} plakalı {vehicle}, {days} gündür stokta.',
  stock_created_title TEXT NOT NULL DEFAULT 'Yeni araç stoğa eklendi',
  stock_created_body TEXT NOT NULL DEFAULT '{plate} plakalı {vehicle} stoğa eklendi.',
  quiet_start TEXT NOT NULL DEFAULT '22:00',
  quiet_end TEXT NOT NULL DEFAULT '08:00',
  daily_digest_time TEXT NOT NULL DEFAULT '09:00',
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS push_subscriptions(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  token TEXT NOT NULL UNIQUE,
  device_name TEXT,
  platform TEXT,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notifications(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  vehicle_id INTEGER,
  event_key TEXT NOT NULL UNIQUE,
  event_type TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  target_url TEXT NOT NULL DEFAULT '/',
  read_at TEXT,
  sent_at TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY(vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
);
"""

DEFAULT_SETTINGS = {
    "notary_expense": ("2602", "number"),
    "expertise_expense": ("3900", "number"),
    "control150_expense": ("1900", "number"),
    "insurance_expense": ("2500", "number"),
    "sks_monthly_rate": ("0.035", "number"),
    "excel_compatibility_mode": ("1", "number"),
}
DEFAULT_RULES = [
    ("NAKİT", 1, 1, 1),
    ("TAKAS", 1, 1, 1),
    ("İHALE", 1, 1, 1),
    ("ŞİRKET ARACI", 0, 0, 1),
]
DEFAULT_SALE_TYPES = ["NAKİT", "TAKAS", "KREDİ KARTI", "KREDİ", "FİNASMAN KURULUŞU"]
DEFAULT_INCOME_TYPES = [
    ("SİGORTA-KASKO", 1, "Satıştan oluşan ek gelir"),
    ("KREDİ", 1, "Kredi / finansman ek geliri"),
    ("UZATILMIŞ GARANTİ", 1, "Garanti satışından oluşan ek gelir"),
]
DEFAULT_CONSULTANTS = ["ONUR İPEK", "HASAN HÜSEYİN SÜRMELİ"]

def now():
    return datetime.now().isoformat(timespec="seconds")

@contextmanager
def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

def init_db():
    with connect() as con:
        con.executescript(SCHEMA)
        # V7.15 audit/user migration for existing databases.
        cols={r["name"] for r in con.execute("PRAGMA table_info(audit_log)").fetchall()}
        for name,typ in [("username","TEXT"),("user_id","INTEGER"),("old_value","TEXT"),("new_value","TEXT"),("ip_address","TEXT")]:
            if name not in cols:
                con.execute(f"ALTER TABLE audit_log ADD COLUMN {name} {typ}")
        for k,(v,t) in DEFAULT_SETTINGS.items():
            con.execute("INSERT OR IGNORE INTO settings(key,value,value_type,updated_at) VALUES(?,?,?,?)",(k,v,t,now()))
        for row in DEFAULT_RULES:
            con.execute("INSERT OR IGNORE INTO purchase_rules(name,apply_sks,apply_fixed,active) VALUES(?,?,?,?)",row)
        for name in DEFAULT_SALE_TYPES:
            con.execute("INSERT OR IGNORE INTO sale_types(name,active) VALUES(?,1)",(name,))
        for name,active,desc in DEFAULT_INCOME_TYPES:
            con.execute("INSERT OR IGNORE INTO income_types(name,active,description) VALUES(?,?,?)",(name,active,desc))
        for name in DEFAULT_CONSULTANTS:
            con.execute("INSERT OR IGNORE INTO consultants(name,active,target_sales,target_profit) VALUES(?,1,0,0)",(name,))
        con.execute("""INSERT OR IGNORE INTO notification_settings(
          id,enabled,stock_created,threshold_days,title_template,body_template,stock_created_title,stock_created_body,
          quiet_start,quiet_end,daily_digest_time,updated_at) VALUES(1,1,1,'[30,45,60,90]',?,?,?,?,?,?,?,?)""",
          ("{plate} stok uyarısı","{plate} plakalı {vehicle}, {days} gündür stokta.","Yeni araç stoğa eklendi",
           "{plate} plakalı {vehicle} stoğa eklendi.","22:00","08:00","09:00",now()))

def backup_db():
    if not DB_PATH.exists():
        return None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    p = BACKUP_DIR / f"renew_{datetime.now():%Y%m%d_%H%M%S}.db"
    shutil.copy2(DB_PATH, p)
    p.chmod(0o640)
    return p

def backup_full():
    """Create a restorable code + database + vehicle-media archive without following backup symlinks."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.chmod(0o750)
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    final=BACKUP_DIR/f"renew_full_{stamp}.tar.gz"
    temp=BACKUP_DIR/f".renew_full_{stamp}.tmp"
    media=BASE/"vehicle_media"
    try:
        with tarfile.open(temp,"w:gz") as tar:
            for name in ("app","templates","assets","requirements.txt"):
                source=BASE/name
                if source.exists(): tar.add(source,arcname=f"app_live/{name}",recursive=True)
            if DB_PATH.exists(): tar.add(DB_PATH,arcname="app_live/data/renew.db")
            if media.exists(): tar.add(media,arcname="app_live/vehicle_media",recursive=True)
        temp.replace(final);final.chmod(0o640)
        # Keep the latest 10 full archives; database-only backups retain their existing history.
        for old in sorted(BACKUP_DIR.glob("renew_full_*.tar.gz"),key=lambda x:x.stat().st_mtime,reverse=True)[10:]:
            old.unlink(missing_ok=True)
        return final
    finally:
        temp.unlink(missing_ok=True)

def log(entity, entity_id, action, details="", old_value="", new_value=""):
    from .auth_context import current_user_id,current_username,current_ip
    uid=current_user_id.get(); uname=current_username.get() or "SYSTEM"; ip=current_ip.get() or ""
    with connect() as con:
        con.execute(
            "INSERT INTO audit_log(entity,entity_id,action,details,username,user_id,old_value,new_value,ip_address,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (entity, str(entity_id) if entity_id is not None else None, action, details, uname, uid, old_value, new_value, ip, now())
        )

from __future__ import annotations
import sqlite3, shutil
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

def backup_db():
    if not DB_PATH.exists():
        return None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    p = BACKUP_DIR / f"renew_{datetime.now():%Y%m%d_%H%M%S}.db"
    shutil.copy2(DB_PATH, p)
    return p

def log(entity, entity_id, action, details="", old_value="", new_value=""):
    from .auth_context import current_user_id,current_username,current_ip
    uid=current_user_id.get(); uname=current_username.get() or "SYSTEM"; ip=current_ip.get() or ""
    with connect() as con:
        con.execute(
            "INSERT INTO audit_log(entity,entity_id,action,details,username,user_id,old_value,new_value,ip_address,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (entity, str(entity_id) if entity_id is not None else None, action, details, uname, uid, old_value, new_value, ip, now())
        )

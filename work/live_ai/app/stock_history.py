from __future__ import annotations

import calendar
import json
import re
from datetime import date

from .db import now

MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


def valid_month(month: str) -> bool:
    if not MONTH_RE.match(str(month or "")):
        return False
    try:
        year, value = map(int, month.split("-"))
        return 1 <= value <= 12 and year >= 2000
    except Exception:
        return False


def ensure_stock_history(con):
    con.execute("""
        CREATE TABLE IF NOT EXISTS stock_monthly_snapshots(
          month TEXT NOT NULL,
          plate TEXT NOT NULL,
          data_json TEXT NOT NULL,
          captured_at TEXT NOT NULL,
          source TEXT NOT NULL DEFAULT 'carry_forward',
          PRIMARY KEY(month, plate)
        )
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_stock_snapshot_month ON stock_monthly_snapshots(month)")


def _active_rows(con):
    return [dict(row) for row in con.execute(
        "SELECT * FROM vehicles WHERE status='STOCK' ORDER BY purchase_date,id"
    ).fetchall()]


def capture_stock_month(con, month: str, rows=None, source="import"):
    if not valid_month(month):
        raise ValueError("Geçerli çalışma dönemi zorunludur (YYYY-AA).")
    ensure_stock_history(con)
    snapshot_rows = list(rows) if rows is not None else _active_rows(con)
    con.execute("DELETE FROM stock_monthly_snapshots WHERE month=?", (month,))
    stamp = now()
    for row in snapshot_rows:
        data = dict(row)
        plate = str(data.get("plate") or "").strip()
        if not plate:
            continue
        con.execute(
            "INSERT INTO stock_monthly_snapshots(month,plate,data_json,captured_at,source) VALUES(?,?,?,?,?)",
            (month, plate, json.dumps(data, ensure_ascii=False, default=str), stamp, source),
        )
    return len(snapshot_rows)


def stock_month_source(con, month: str):
    ensure_stock_history(con)
    exact = con.execute(
        "SELECT COUNT(*) count, MAX(captured_at) captured_at, MAX(source) source FROM stock_monthly_snapshots WHERE month=?",
        (month,),
    ).fetchone()
    if exact and exact["count"]:
        return month, "exact", exact["source"], exact["captured_at"]
    previous = con.execute(
        "SELECT MAX(month) month FROM stock_monthly_snapshots WHERE month<?", (month,)
    ).fetchone()
    if previous and previous["month"]:
        return previous["month"], "carry_forward", "carry_forward", None
    return None, "live_fallback", "live", None


def load_stock_month(con, month: str):
    if not valid_month(month):
        return _active_rows(con), {"requested_month": month, "source_month": None, "mode": "live_fallback"}
    source_month, mode, source, captured_at = stock_month_source(con, month)
    if not source_month:
        return _active_rows(con), {"requested_month": month, "source_month": None, "mode": mode}
    rows = []
    for record in con.execute(
        "SELECT data_json FROM stock_monthly_snapshots WHERE month=? ORDER BY json_extract(data_json,'$.purchase_date'), json_extract(data_json,'$.id')",
        (source_month,),
    ).fetchall():
        rows.append(json.loads(record["data_json"]))
    return rows, {
        "requested_month": month,
        "source_month": source_month,
        "mode": mode,
        "source": source,
        "captured_at": captured_at,
    }


def stock_as_of(month: str):
    if not valid_month(month):
        return None
    today = date.today()
    current = f"{today.year:04d}-{today.month:02d}"
    if month >= current:
        return today.isoformat()
    year, value = map(int, month.split("-"))
    return date(year, value, calendar.monthrange(year, value)[1]).isoformat()

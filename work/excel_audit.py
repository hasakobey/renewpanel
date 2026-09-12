from __future__ import annotations

import json
import math
import tempfile
from datetime import date, timedelta
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

from app.db import connect
from app.calc import sale_calc, stock_calc, get_settings, get_rule
from app.xlsx_service import export_master, master_preview, TEMPLATE

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main", "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}


def sheet_paths(book: Path):
    with ZipFile(book) as z:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        relmap = {r.attrib["Id"]: r.attrib["Target"] for r in rels}
        out = {}
        for s in wb.find("m:sheets", NS):
            name = s.attrib["name"]
            rid = s.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
            target = relmap[rid].lstrip("/")
            if not target.startswith("xl/"):
                target = "xl/" + target
            out[name] = target
        return out


def formulas(book: Path, sheet: str):
    path = sheet_paths(book)[sheet]
    with ZipFile(book) as z:
        root = ET.fromstring(z.read(path))
    return {c.attrib["r"]: (c.find("m:f", NS).text or "") for c in root.findall(".//m:c", NS) if c.find("m:f", NS) is not None}


def close(a, b, tol=0.01):
    return math.isclose(float(a), float(b), rel_tol=0, abs_tol=tol)


def expected_sale(row, settings, rule):
    buy = float(row.get("purchase_price") or 0)
    sell = float(row.get("sale_price") or 0)
    days = (date.fromisoformat(row["sale_date"]) - date.fromisoformat(row["purchase_date"])).days
    fixed = bool(rule.get("apply_fixed"))
    j = settings.get("notary_expense", 0) if buy and fixed else 0
    k = settings.get("expertise_expense", 0) if buy else 0
    l = settings.get("control150_expense", 0) if buy else 0
    m = settings.get("insurance_expense", 0) if buy and fixed else 0
    n = float(row.get("extra_expense") or 0)
    o = buy * settings.get("sks_monthly_rate", 0) * days / 30 if buy and rule.get("apply_sks") else 0
    p = j + k + l + m + n + o
    q = buy + p
    v = sell - q
    ac = sum(float(row.get(k) or 0) for k in ("insurance_income", "credit_income", "warranty_income"))
    return {"sks_days": days, "total_expense": p, "total_cost": q, "net_profit": v, "net_margin": v / sell if sell else 0, "performance_profit": v + ac}


def run():
    report = {"checks": [], "warnings": [], "errors": []}
    settings = get_settings()
    with connect() as con:
        counts = {
            "sales": con.execute("select count(*) from sales").fetchone()[0],
            "stock": con.execute("select count(*) from vehicles where status='STOCK'").fetchone()[0],
            "consultants": con.execute("select count(*) from consultants").fetchone()[0],
        }
        rule_rows = [dict(r) for r in con.execute("select * from purchase_rules order by rowid")]

    main_before = formulas(TEMPLATE, "ARAÇ VERİ GİRİŞİ")
    extra_before = formulas(TEMPLATE, "EXTRA STOK BİLGİSİ")
    report["template"] = str(TEMPLATE)
    report["db_counts"] = counts
    report["formula_counts_before"] = {"main": len(main_before), "extra": len(extra_before)}

    with tempfile.TemporaryDirectory(prefix="renew_excel_audit_") as td:
        exported = Path(td) / "RENEW_AUDIT_EXPORT.xlsx"
        export_master(exported)
        main_after = formulas(exported, "ARAÇ VERİ GİRİŞİ")
        extra_after = formulas(exported, "EXTRA STOK BİLGİSİ")
        preview = master_preview(exported)
        report["exported_preview"] = preview["summary"]
        report["formula_counts_after"] = {"main": len(main_after), "extra": len(extra_after)}
        required_main = [f"{col}{r}" for r in range(4, 304) for col in ("A", "I", "J", "K", "L", "M", "O", "P", "Q", "U", "V", "W", "X", "AC", "AD")]
        required_extra = [f"{col}{r}" for r in range(7, 307) for col in ("A", "J", "P", "Q", "R", "S")]
        missing_main = [x for x in required_main if x not in main_after]
        missing_extra = [x for x in required_extra if x not in extra_after]
        report["checks"].append({"name": "Ana formül hücreleri", "pass": not missing_main, "expected": len(required_main), "missing": missing_main[:10]})
        report["checks"].append({"name": "Stok formül hücreleri", "pass": not missing_extra, "expected": len(required_extra), "missing": missing_extra[:10]})
        bad_tokens = ("#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A")
        bad = [(cell, f) for cell, f in {**main_after, **extra_after}.items() if any(t in f for t in bad_tokens)]
        report["checks"].append({"name": "Formül hata belirteçleri", "pass": not bad, "bad": bad[:10]})
        report["checks"].append({"name": "Dışa aktar kayıt sayıları", "pass": preview["summary"]["sales_count"] == counts["sales"] and preview["summary"]["stock_count"] == counts["stock"], "preview": preview["summary"]})
        Path("/tmp/RENEW_AUDIT_EXPORT.xlsx").write_bytes(exported.read_bytes())

    base = {
        "purchase_price": 1_000_000,
        "sale_price": 1_250_000,
        "purchase_date": "2026-01-01",
        "sale_date": "2026-02-15",
        "extra_expense": 12_500,
        "insurance_income": 8_000,
        "credit_income": 6_000,
        "warranty_income": 4_000,
    }
    for rule in rule_rows[:8]:
        row = dict(base, purchase_type=rule["name"])
        actual = sale_calc(row)
        expected = expected_sale(row, settings, rule)
        keys = ("sks_days", "total_expense", "total_cost", "net_profit", "net_margin", "performance_profit")
        ok = all(close(actual[k], expected[k]) for k in keys)
        report["checks"].append({"name": f"Satış matematiği: {rule['name']}", "pass": ok, "actual": {k: actual[k] for k in keys}, "expected": expected})

    fixed_excel = sum(float(settings.get(k, 0)) for k in ("notary_expense", "expertise_expense", "control150_expense", "insurance_expense"))
    for rule in rule_rows[:8]:
        row = {"purchase_price": 1_000_000, "list_price": 1_250_000, "purchase_date": (date.today() - timedelta(days=45)).isoformat(), "purchase_type": rule["name"]}
        actual = stock_calc(row, date.today())
        finance = 1_000_000 * float(settings.get("sks_monthly_rate", 0)) * 45 / 30
        expected_total = 1_000_000 + fixed_excel + finance
        if not close(actual["total_cost"], expected_total):
            report["warnings"].append({"name": f"Stok/Excel sabit gider farkı: {rule['name']}", "backend_total": actual["total_cost"], "excel_total": expected_total, "difference": actual["total_cost"] - expected_total, "rule": {"apply_sks": rule["apply_sks"], "apply_fixed": rule["apply_fixed"]}})

    report["status"] = "PASS" if not report["errors"] and all(c["pass"] for c in report["checks"]) else "FAIL"
    report["warning_count"] = len(report["warnings"])
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run()

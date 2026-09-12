from __future__ import annotations

import json, os, sqlite3, tempfile, traceback
from pathlib import Path
from zipfile import ZipFile

from app import db
from app.calc import sale_calc, stock_calc
from app.xlsx_service import export_master, master_preview, apply_master_import

results=[]
def check(name, ok, detail=""):
    results.append({"name":name,"ok":bool(ok),"detail":str(detail)})

live_db=db.DB_PATH
with db.connect() as con:
    integrity=con.execute("PRAGMA integrity_check").fetchone()[0]
    fk=con.execute("PRAGMA foreign_key_check").fetchall()
    sales=[dict(r) for r in con.execute("SELECT * FROM sales ORDER BY sale_date,id").fetchall()]
    stocks=[dict(r) for r in con.execute("SELECT * FROM vehicles WHERE status='STOCK' ORDER BY id").fetchall()]
    acquisitions=[dict(r) for r in con.execute("SELECT * FROM acquisitions ORDER BY purchase_date,id").fetchall()]
    expertise=[dict(r) for r in con.execute("SELECT * FROM expertise ORDER BY month,consultant").fetchall()]
    settings={r['key']:r['value'] for r in con.execute("SELECT * FROM settings").fetchall()}
    duplicate_sales=con.execute("SELECT upper(replace(plate,' ','')),sale_date,count(*) c FROM sales GROUP BY 1,2 HAVING c>1").fetchall()
    duplicate_stock=con.execute("SELECT upper(replace(plate,' ','')),count(*) c FROM vehicles WHERE status='STOCK' GROUP BY 1 HAVING c>1").fetchall()

check("SQLite integrity",integrity=="ok",integrity)
check("Foreign keys",not fk,f"violations={len(fk)}")
check("Duplicate sales",not duplicate_sales,f"duplicates={len(duplicate_sales)}")
check("Duplicate stock",not duplicate_stock,f"duplicates={len(duplicate_stock)}")
check("Required settings",all(k in settings for k in ['notary_expense','expertise_expense','control150_expense','insurance_expense','sks_monthly_rate','excel_compatibility_mode']),sorted(settings))

math_errors=[]
for r in sales:
    c=sale_calc(r)
    expected_exp=c['notary']+c['expertise']+c['control150']+c['insurance']+c['extra_expense']+c['sks_finance']
    expected_cost=float(r.get('purchase_price') or 0)+expected_exp if r.get('purchase_price') else 0
    expected_perf=c['net_profit']+c['extra_income']
    if abs(c['total_expense']-expected_exp)>0.01 or abs(c['total_cost']-expected_cost)>0.01 or abs(c['performance_profit']-expected_perf)>0.01: math_errors.append(r['plate'])
check("Sales math identities",not math_errors,math_errors)

company_errors=[]
for r in sales:
    if str(r.get('purchase_type') or '').strip().upper() in ('ŞİRKET ARACI','SIRKET ARACI'):
        c=sale_calc(r)
        if c['notary']!=0 or c['insurance']!=0 or c['sks_finance']!=0: company_errors.append({"plate":r['plate'],"notary":c['notary'],"insurance":c['insurance'],"finance":c['sks_finance']})
check("Company vehicle expenses disabled",not company_errors,company_errors)

stock_errors=[]
for r in stocks:
    c=stock_calc(r)
    expected=float(r.get('purchase_price') or 0)+c['fixed_expense']+c['sks_finance'] if r.get('purchase_price') else 0
    if abs(c['total_cost']-expected)>0.01 or c['sks_days']<0: stock_errors.append(r['plate'])
check("Stock math identities",not stock_errors,stock_errors)

months=sorted({str(r.get('sale_date') or '')[:7] for r in sales if r.get('sale_date')})
test_months=sorted(set(months+['2026-09']))
export_details=[]
export_files={}
with tempfile.TemporaryDirectory(prefix='renew_accept_') as td:
    root=Path(td)
    for month in test_months:
        out=root/f"renew_{month}.xlsx"; export_master(out,month); export_files[month]=out
        preview=master_preview(out)
        expected_sales=sum(str(x.get('sale_date') or '')[:7]==month for x in sales)
        exp_rows=preview['expertise']
        expected_exp={x['consultant']:(x['done_count'],x['converted_count']) for x in expertise if x['month']==month}
        actual_exp={x['consultant']:(x['done_count'],x['converted_count']) for x in exp_rows}
        exp_ok=all(actual_exp.get(name,(0,0))==vals for name,vals in expected_exp.items()) and (month in {x['month'] for x in expertise} or all(v==(0,0) for v in actual_exp.values()))
        with ZipFile(out) as z:
            formula_count=sum(z.read(n).count(b'<f') for n in z.namelist() if n.startswith('xl/worksheets/sheet') and n.endswith('.xml'))
        ok=preview['summary']['sales_count']==expected_sales and preview['summary']['stock_count']==len(stocks) and exp_ok and formula_count>0
        export_details.append({"month":month,"expected_sales":expected_sales,"actual_sales":preview['summary']['sales_count'],"stock":preview['summary']['stock_count'],"expertise_ok":exp_ok,"formulas":formula_count})
        check(f"Monthly Excel {month}",ok,export_details[-1])

    # Round-trip September workbook into an isolated empty database.
    source=export_files['2026-09']
    isolated=root/'isolated.db'; isolated_backups=root/'backups'
    db.DB_PATH=isolated; db.BACKUP_DIR=isolated_backups; db.init_db()
    summary=apply_master_import(source,'replace','acceptance_2026_09.xlsx')
    with db.connect() as con:
        iso_integrity=con.execute("PRAGMA integrity_check").fetchone()[0]
        iso_sales=con.execute("SELECT count(*) FROM sales").fetchone()[0]
        iso_stock=con.execute("SELECT count(*) FROM vehicles WHERE status='STOCK'").fetchone()[0]
        iso_exp=con.execute("SELECT count(*) FROM expertise WHERE done_count<>0 OR converted_count<>0").fetchone()[0]
    check("Isolated Excel round-trip",iso_integrity=='ok' and iso_sales==0 and iso_stock==len(stocks) and iso_exp==0,{"integrity":iso_integrity,"sales":iso_sales,"stock":iso_stock,"nonzero_expertise":iso_exp,"summary":summary})
    db.DB_PATH=live_db

media_root=Path('/opt/renewpro/app_live/vehicle_media')
missing_media=[]
for r in stocks:
    key=''.join(ch for ch in str(r.get('plate') or '').upper() if ch.isalnum())
    folder=media_root/key/'original'
    if not folder.exists() or not any(x.is_file() and x.suffix.lower() in {'.jpg','.jpeg','.png','.webp'} for x in folder.iterdir()): missing_media.append(r['plate'])
check("Stock media coverage",not missing_media,{"missing":missing_media,"total_stock":len(stocks)})

print(json.dumps({"summary":{"passed":sum(x['ok'] for x in results),"failed":sum(not x['ok'] for x in results),"sales":len(sales),"stocks":len(stocks),"acquisitions":len(acquisitions),"expertise_rows":len(expertise)},"results":results},ensure_ascii=False,indent=2))

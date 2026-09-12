import importlib.util,sys
from pathlib import Path
sys.path.insert(0,'/opt/renewpro/app_live')
from app import calc
from app.auth_service import required_permission
from pydantic import ValidationError
spec=importlib.util.spec_from_file_location('app.form_finance_test',Path(__file__).with_name('form_finance.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
calc.get_settings=lambda:{'notary_expense':2602,'expertise_expense':3900,'control150_expense':1900,'insurance_expense':2500,'sks_monthly_rate':.035}
rule=lambda t:{'found':t in ['NAKİT','ŞİRKET ARACI'],'apply_fixed':t=='NAKİT','apply_sks':t=='NAKİT'}
calc.get_rule=rule;m.get_rule=rule
count=0
for kind in ['stock','sale']:
 for ptype in ['NAKİT','ŞİRKET ARACI']:
  for amount in [0,100000,1234567.89]:
   for selling in [0,90000,1600000]:
    x=m.FinanceInput(month='2026-08',purchase_date='2026-08-01',sale_date='2026-08-20',purchase_type=ptype,purchase_price=amount,list_price=selling,sale_price=selling,extra_expense=1250,insurance_income=500)
    r=m.preview(x,kind);expected=calc.stock_calc(x.model_dump(),r['as_of']) if kind=='stock' else calc.sale_calc(x.model_dump())
    assert r['calc']==expected
    assert r['fixed_expense']==sum(r['expenses'].values())
    if kind=='stock':assert abs(r['fixed_expense']-expected['fixed_expense'])<1e-8
    if ptype=='ŞİRKET ARACI':assert r['expenses']['notary']==r['expenses']['insurance']==r['daily_finance']==0
    count+=1
assert required_permission('/api/stocks/financial-preview','POST')=='stocks.edit'
assert required_permission('/api/sales/financial-preview','POST')=='sales.edit'
try:m.FinanceInput(purchase_price=float('nan'));raise AssertionError('NaN accepted')
except ValidationError:pass
try:m.preview(m.FinanceInput(month='2026-19'),'stock');raise AssertionError('Bad month accepted')
except m.HTTPException:pass
print('PASS',count,'calculation equivalence cases; company exemptions, permissions, nonfinite and month validation')
import json
sample=m.preview(m.FinanceInput(month='2026-08',purchase_date='2026-08-01',purchase_type='NAKİT',purchase_price=100000,list_price=130000),'stock')
Path(__file__).with_name('preview_sample.json').write_text(json.dumps(sample),encoding='utf-8')

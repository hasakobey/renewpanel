"""Read-only form previews backed by the existing Excel-compatible engine."""
from datetime import date, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict
from .calc import stock_calc, sale_calc, get_rule, _date
from .stock_history import stock_as_of, valid_month

router=APIRouter()

class FinanceInput(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    month:str=''
    purchase_type:str=''
    purchase_date:str=''
    sale_date:str=''
    purchase_price:float=0
    list_price:float=0
    sale_price:float=0
    extra_expense:float=0
    insurance_income:float=0
    credit_income:float=0
    warranty_income:float=0

def preview(x:FinanceInput,kind:str):
    row=x.model_dump()
    if x.month and not valid_month(x.month):raise HTTPException(422,'Geçersiz çalışma dönemi')
    if not _date(x.purchase_date):raise HTTPException(422,'Alış tarihi girin')
    if kind=='sale' and not _date(x.sale_date):raise HTTPException(422,'Satış tarihi girin')
    rule=get_rule(x.purchase_type)
    if not rule.get('found'):raise HTTPException(422,'Tanımlı bir alım türü seçin')
    if kind=='stock':
        as_of=stock_as_of(x.month) if x.month else date.today().isoformat()
        result=stock_calc(row,as_of)
        # The sale engine exposes the very same fixed-expense components individually.
        breakdown=sale_calc({**row,'sale_date':str(as_of),'sale_price':x.list_price,'extra_expense':0,
                             'insurance_income':0,'credit_income':0,'warranty_income':0})
        tomorrow=stock_calc(row,_date(as_of)+timedelta(days=1))
        daily=tomorrow['sks_finance']-result['sks_finance']
        selling=x.list_price;profit=result['estimated_profit']
        margin=profit/selling if selling and x.purchase_price else None
    else:
        result=breakdown=sale_calc(row)
        tomorrow=sale_calc({**row,'sale_date':str(_date(x.sale_date)+timedelta(days=1))})
        daily=tomorrow['sks_finance']-result['sks_finance']
        profit=result['net_profit'];margin=result['net_margin'] if x.sale_price else None
    expenses={k:breakdown[k] for k in ['notary','expertise','control150','insurance']}
    return {'calc':result,'expenses':expenses,'fixed_expense':sum(expenses.values()),
            'profit':profit,'margin':margin,'daily_finance':daily,
            'apply_fixed':bool(rule.get('apply_fixed')),'apply_sks':bool(rule.get('apply_sks')),
            'as_of':str(as_of) if kind=='stock' else x.sale_date}

@router.post('/api/stocks/financial-preview')
def stock_preview(x:FinanceInput):return preview(x,'stock')

@router.post('/api/sales/financial-preview')
def sale_preview(x:FinanceInput):return preview(x,'sale')

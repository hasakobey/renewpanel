from __future__ import annotations
from datetime import date, datetime
from .db import connect

def _date(v):
    if not v: return None
    if isinstance(v, date): return v
    try: return datetime.fromisoformat(str(v)[:10]).date()
    except Exception: return None

def get_settings():
    with connect() as con:
        rows = con.execute("SELECT key,value,value_type FROM settings").fetchall()
    out={}
    for r in rows:
        if r["value_type"]=="number":
            try: out[r["key"]]=float(r["value"])
            except Exception: out[r["key"]]=0.0
        else: out[r["key"]]=r["value"]
    return out

def get_rule(purchase_type):
    """
    Excel ARAÇ VERİ GİRİŞİ O sütunu VLOOKUP + IFERROR kullanır.
    Alım türü ALIM AYARLARI'nda bulunmuyorsa SKS=0 olmalıdır.
    """
    with connect() as con:
        r=con.execute("SELECT * FROM purchase_rules WHERE upper(trim(name))=upper(trim(?))",(purchase_type or "",)).fetchone()
    if not r:
        return {"name":purchase_type or "", "apply_sks":0, "apply_fixed":0, "active":0, "found":False}
    d=dict(r); d["found"]=True; return d

def days_between(start, end=None):
    s=_date(start); e=_date(end) if end else date.today()
    if not s: return 0
    return max(0,(e-s).days)

def sale_calc(row):
    """
    Birebir mevcut RENEW Excel formülü:
      I = satış tarihi - alış tarihi
      J = GİDER B4 (Noter)       [F doluysa]
      K = GİDER B5 (Ekspertiz)   [F doluysa]
      L = GİDER B6 (150 Nokta)   [F doluysa]
      M = GİDER B7 (Sigorta)     [F doluysa]
      O = VLOOKUP(E, ALIM AYARLARI, 2) EVET ise F*B8*I/30, bulunamazsa 0
      P = SUM(J:O)
      Q = F + P
      U = T - F
      V = T - Q
      W = V / T
      AC = Z+AA+AB
      AD = V+AC

    Not: ALIM AYARLARI C sütunu mevcut Excel formülünde J/M giderlerini kapatmıyor.
    Excel Uyumluluk Modu açıkken backend aynı davranır.
    """
    s=get_settings()
    rule=get_rule(row.get("purchase_type"))
    buy=float(row.get("purchase_price") or 0)
    sell=float(row.get("sale_price") or 0)
    sks=days_between(row.get("purchase_date"), row.get("sale_date"))

    excel_mode=bool(int(s.get("excel_compatibility_mode",1) or 0))
    # Excel'deki gerçek satır davranışı:
    # J (Noter) ve M (Sigorta) ALIM AYARLARI C="EVET" ise uygulanır.
    # K (Ekspertiz) ve L (150 Nokta) alış bedeli varsa her zaman uygulanır.
    # Tanımsız alım türü VLOOKUP/IFERROR davranışı gereği fixed=0, sks=0 kabul edilir.
    fixed=bool(rule.get("apply_fixed"))
    notary=s.get("notary_expense",0) if buy and fixed else 0
    expertise=s.get("expertise_expense",0) if buy else 0
    control=s.get("control150_expense",0) if buy else 0
    insurance=s.get("insurance_expense",0) if buy and fixed else 0

    extra=float(row.get("extra_expense") or 0)
    fin=buy*s.get("sks_monthly_rate",0)*sks/30 if buy and rule.get("apply_sks") else 0
    total_expense=notary+expertise+control+insurance+extra+fin
    total_cost=buy+total_expense if buy else 0
    gross=sell-buy if buy and sell else 0
    net=sell-total_cost if sell else 0
    ratio=net/sell if sell else 0
    extra_income=float(row.get("insurance_income") or 0)+float(row.get("credit_income") or 0)+float(row.get("warranty_income") or 0)
    perf=net+extra_income
    status="SATILDI" if row.get("sale_date") else ("STOKTA" if buy else "")
    return {
        "sks_days":sks,"notary":notary,"expertise":expertise,"control150":control,"insurance":insurance,
        "extra_expense":extra,"sks_finance":fin,"total_expense":total_expense,"total_cost":total_cost,
        "gross_profit":gross,"net_profit":net,"net_margin":ratio,"stock_status":status,
        "insurance_income":float(row.get("insurance_income") or 0),
        "credit_income":float(row.get("credit_income") or 0),
        "warranty_income":float(row.get("warranty_income") or 0),
        "extra_income":extra_income,"performance_profit":perf,
        "purchase_rule_found":bool(rule.get("found")),"excel_compatibility_mode":excel_mode
    }

def stock_calc(row, as_of=None):
    """
    EXTRA STOK BİLGİSİ birebir:
      J = TODAY - I
      P = GİDER AYARLARI B10 = B4:B7 toplamı
      Q = M * B8 * J / 30
      R = M + P + Q
      S = N - R
    """
    s=get_settings()
    buy=float(row.get("purchase_price") or 0)
    sell=float(row.get("list_price") or 0)
    sks=days_between(row.get("purchase_date"), as_of)
    rule=get_rule(row.get("purchase_type"))
    # Güncel stok da ALIM AYARLARI ile aynı motoru kullanır.
    # Ekspertiz + 150 Nokta alış varsa temel gider; Noter/Sigorta sabit-gider kuralına bağlıdır.
    fixed=(s.get("expertise_expense",0)+s.get("control150_expense",0)) if buy else 0
    if buy and rule.get("apply_fixed"):
        fixed += s.get("notary_expense",0)+s.get("insurance_expense",0)
    fin=buy*s.get("sks_monthly_rate",0)*sks/30 if buy and rule.get("apply_sks") else 0
    total=buy+fixed+fin if buy else 0
    profit=sell-total if sell and buy else 0
    return {"sks_days":sks,"fixed_expense":fixed,"sks_finance":fin,"total_cost":total,"estimated_profit":profit}

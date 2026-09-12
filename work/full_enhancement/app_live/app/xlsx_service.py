from __future__ import annotations
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree as ET
from datetime import datetime, date, timedelta
import re, shutil, tempfile, os
from .db import connect, now, backup_db, log
from .calc import sale_calc, stock_calc

BASE=Path(__file__).resolve().parents[1]
TEMPLATE=BASE/"templates"/"RENEW_MASTER_SABLON.xlsx"

NS_MAIN="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG="http://schemas.openxmlformats.org/package/2006/relationships"
ET.register_namespace("",NS_MAIN)
ET.register_namespace("r",NS_REL)

def col_index(ref):
    m=re.match(r"([A-Z]+)",ref); n=0
    for ch in m.group(1): n=n*26+ord(ch)-64
    return n-1

def excel_date_to_iso(v):
    if v in ("",None): return ""
    try:
        n=float(v)
        d=date(1899,12,30)+timedelta(days=n)
        return d.isoformat()
    except Exception:
        s=str(v).strip()
        for fmt in ("%Y-%m-%d","%d.%m.%Y","%d/%m/%Y"):
            try:return datetime.strptime(s,fmt).date().isoformat()
            except Exception: pass
    return ""

def iso_to_excel(v):
    if not v:return ""
    d=datetime.fromisoformat(str(v)[:10]).date()
    return (d-date(1899,12,30)).days

class XlsxReader:
    def __init__(self,path):
        self.path=Path(path)
        self.z=ZipFile(self.path)
        self.shared=[]
        if "xl/sharedStrings.xml" in self.z.namelist():
            root=ET.fromstring(self.z.read("xl/sharedStrings.xml"))
            for si in root.findall(f"{{{NS_MAIN}}}si"):
                self.shared.append("".join(t.text or "" for t in si.iter(f"{{{NS_MAIN}}}t")))
        wb=ET.fromstring(self.z.read("xl/workbook.xml"))
        rels=ET.fromstring(self.z.read("xl/_rels/workbook.xml.rels"))
        rmap={e.attrib["Id"]:e.attrib["Target"] for e in rels}
        self.sheets={}
        for s in wb.find(f"{{{NS_MAIN}}}sheets"):
            rid=s.attrib[f"{{{NS_REL}}}id"]; target=rmap[rid]
            self.sheets[s.attrib["name"]]=("xl/"+target if not target.startswith("/") else target.lstrip("/"))

    def sheet_rows(self,name):
        root=ET.fromstring(self.z.read(self.sheets[name]))
        out=[]
        for row in root.find(f"{{{NS_MAIN}}}sheetData"):
            vals={}
            for c in row.findall(f"{{{NS_MAIN}}}c"):
                idx=col_index(c.attrib["r"]); typ=c.attrib.get("t"); v=c.find(f"{{{NS_MAIN}}}v")
                if typ=="s" and v is not None: val=self.shared[int(v.text)]
                elif typ=="inlineStr":
                    isel=c.find(f"{{{NS_MAIN}}}is")
                    val="".join(t.text or "" for t in isel.iter(f"{{{NS_MAIN}}}t")) if isel is not None else ""
                else: val=v.text if v is not None else ""
                vals[idx]=val
            if vals:
                mx=max(vals); arr=[""]*(mx+1)
                for k,v in vals.items(): arr[k]=v
                out.append((int(row.attrib.get("r","0")),arr))
        return out

def _norm_header(v):
    s=str(v or '').strip().upper()
    tr=str.maketrans({'İ':'I','I':'I','Ş':'S','Ğ':'G','Ü':'U','Ö':'O','Ç':'C'})
    s=s.translate(tr)
    s=re.sub(r'\s+',' ',s)
    return s

def _safe_number(v, default=0.0):
    if v in ('',None): return default
    if isinstance(v,(int,float)): return float(v)
    s=str(v).strip().upper().replace('TL','').replace('₺','').replace(' ','')
    if not s:return default
    # Turkish formatted numbers: 1.250.000,50 / 1.250.000 / 1250000
    if ',' in s:
        s=s.replace('.','').replace(',','.')
    elif s.count('.')>1:
        s=s.replace('.','')
    else:
        # a single dot followed by exactly 3 digits is generally a thousands separator here
        m=re.fullmatch(r'-?\d+\.\d{3}',s)
        if m:s=s.replace('.','')
    s=re.sub(r'[^0-9.\-]','',s)
    try:return float(s)
    except Exception:return default

def _find_header_row(rows, required_aliases):
    aliases={_norm_header(x) for x in required_aliases}
    best=None;best_score=-1
    for pos,(rn,arr) in enumerate(rows[:40]):
        hs={_norm_header(x) for x in arr if str(x or '').strip()}
        score=len(hs & aliases)
        if score>best_score:
            best=(pos,rn,arr);best_score=score
    if not best or best_score<2:
        raise ValueError('Excel başlık satırı bulunamadı. Beklenen alanlardan Plaka / Marka / Model gibi sütunlar tespit edilemedi.')
    return best

def rows_as_dicts(path,sheet_index=0,required_aliases=None):
    r=XlsxReader(path)
    names=list(r.sheets)
    if not names:raise ValueError('Excel içinde çalışma sayfası bulunamadı.')
    if sheet_index>=len(names):raise ValueError('İstenen Excel sayfası bulunamadı.')
    name=names[sheet_index]; rows=r.sheet_rows(name)
    if not rows:return []
    if required_aliases:
        pos,header_rn,headers=_find_header_row(rows,required_aliases)
        data_rows=rows[pos+1:]
    else:
        headers=rows[0][1];data_rows=rows[1:]
    res=[]
    for rn,arr in data_rows:
        d={str(h).strip():(arr[i] if i<len(arr) else '') for i,h in enumerate(headers) if str(h).strip()}
        d['__excel_row__']=rn
        res.append(d)
    return res

def _pick(d,*names):
    norm={_norm_header(k):v for k,v in d.items() if not str(k).startswith('__')}
    for n in names:
        key=_norm_header(n)
        if key in norm and norm[key] not in ('',None):return norm[key]
    return ''

def import_stock_source(path):
    rows=rows_as_dicts(path,0,['Plaka','Marka','Model','Model Yılı','Alış Fiyatı','Noter Alış Tarihi'])
    out=[];errors=[]
    for d in rows:
        row_no=d.get('__excel_row__','?')
        plate=str(_pick(d,'Plaka','Eski Plaka','Yeni Plaka')).strip()
        if not plate:continue
        try:
            sale_price=_pick(d,'Minimum Satış Fiyatı','Esnaf Satış Fiyatı','Anlaşılan Fiyat','Satış Fiyatı')
            out.append({
                'plate':plate,
                'model_year':int(_safe_number(_pick(d,'Model Yılı'),0)) or None,
                'km':int(_safe_number(_pick(d,'Alış Km','KM','Alış KM'),0)),
                'brand':str(_pick(d,'Marka')).strip(),
                'model':str(_pick(d,'Model')).strip(),
                'version':str(_pick(d,'Versiyon','Version')).strip(),
                'color':str(_pick(d,'Renk')).strip(),
                'purchase_date':excel_date_to_iso(_pick(d,'Noter Alış Tarihi','Alış Tarihi')),
                'fuel':str(_pick(d,'Yakıt')).strip(),
                'transmission':str(_pick(d,'Vites')).strip(),
                'purchase_price':_safe_number(_pick(d,'Alış Fiyatı','Noter Alış Fiyatı'),0),
                'list_price':_safe_number(sale_price,0),
                'target_profit':_safe_number(_pick(d,'Hedef Kazanç','Hedef Kar','Hedef Kâr'),0),
                'purchase_type':str(_pick(d,'Alış Şekli','Alım Türü','Alış Türü')).strip() or 'NAKİT'
            })
        except Exception as e:
            errors.append(f'{row_no}. satır: {e}')
    if errors and not out:
        raise ValueError('Stok satırları okunamadı: '+' | '.join(errors[:5]))
    if not out:
        raise ValueError('Plaka bilgisi bulunan stok kaydı tespit edilemedi.')
    return out

def import_sales_source(path,month):
    rows=rows_as_dicts(path,0,['Noter Satış Tarihi','Plaka','Satıcı','Alış Fiyatı','Anlaşılan Fiyat'])
    out=[]
    for d in rows:
        sale_date=excel_date_to_iso(_pick(d,'Noter Satış Tarihi','Satış Tarihi'))
        if not sale_date or sale_date[:7]!=month:continue
        plate=str(_pick(d,'Plaka','Yeni Plaka','Eski Plaka')).strip()
        if not plate:continue
        vi=' '.join(str(_pick(d,k)).strip() for k in ('Marka','Model','Versiyon') if str(_pick(d,k)).strip())
        out.append({
          'sale_date':sale_date,'plate':plate,'vehicle_info':vi,
          'model_year':int(_safe_number(_pick(d,'Model Yılı'),0)) or None,
          'purchase_type':str(_pick(d,'Alış Şekli','Alım Türü')).strip() or 'NAKİT',
          'purchase_price':_safe_number(_pick(d,'Alış Fiyatı','Noter Alış Fiyatı'),0),
          'purchase_date':excel_date_to_iso(_pick(d,'Noter Alış Tarihi','Alış Tarihi')),
          'extra_expense':_safe_number(_pick(d,'Masraf','Ek Masraf'),0),
          'customer':str(_pick(d,'Satış Müşteri','Müşteri Bilgileri')).strip(),
          'sale_type':str(_pick(d,'Satış Şekli','Satış Türü')).strip() or 'NAKİT',
          'sale_price':_safe_number(_pick(d,'Anlaşılan Fiyat','Noter Satış Fiyatı','Satış Bedeli'),0),
          'consultant':str(_pick(d,'Satıcı','Satış Danışmanı')).strip(),
          'insurance_income':0,'credit_income':0,'warranty_income':0
        })
    if not out:
        raise ValueError(f'{month} dönemi için plaka ve satış tarihi eşleşen satış kaydı bulunamadı.')
    return out

def seed_from_master_if_empty():
    with connect() as con:
        c=con.execute("SELECT COUNT(*) c FROM sales").fetchone()["c"]
        s=con.execute("SELECT COUNT(*) c FROM vehicles").fetchone()["c"]
    if c or s or not TEMPLATE.exists():return
    r=XlsxReader(TEMPLATE)
    # Seed sales from ARAÇ VERİ GİRİŞİ cached values
    rows=r.sheet_rows("ARAÇ VERİ GİRİŞİ")
    hdr=next((arr for rn,arr in rows if rn==3),[])
    idx={h:i for i,h in enumerate(hdr)}
    with connect() as con:
        now=datetime.now().isoformat(timespec="seconds")
        for rn,a in rows:
            if rn<4:continue
            get=lambda h: a[idx[h]] if h in idx and idx[h]<len(a) else ""
            if not str(get("PLAKA")).strip() or not str(get("ALIŞ BEDELİ")).strip():continue
            status=str(get("STOK DURUMU")).strip()
            if status=="SATILDI":
                con.execute("""INSERT OR IGNORE INTO sales(
                    plate,vehicle_info,model_year,purchase_type,purchase_price,purchase_date,sale_date,extra_expense,
                    customer,sale_type,sale_price,consultant,insurance_income,credit_income,warranty_income,created_at,updated_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(
                    str(get("PLAKA")).strip(),str(get("OTOMOBİL BİLGİLERİ")).strip(),
                    int(float(get("M.YILI") or 0)) or None,str(get("ALIM TÜRÜ")).strip(),
                    float(get("ALIŞ BEDELİ") or 0),excel_date_to_iso(get("ALIŞ TARİHİ")),excel_date_to_iso(get("SATIŞ TARİHİ")),
                    float(get("EK MASRAF") or 0),str(get("MÜŞTERİ BİLGİLERİ")).strip(),str(get("SATIŞ TÜRÜ")).strip(),
                    float(get("SATIŞ BEDELİ") or 0),str(get("SATIŞ DANIŞMANI")).strip(),
                    float(get("SİGORTA-KASKO GELİRİ") or 0),float(get("KREDİ GELİRİ") or 0),float(get("UZATILMIŞ GARANTİ GELİRİ") or 0),
                    now,now
                ))
        # Seed active stock from EXTRA STOK
        rows2=r.sheet_rows("EXTRA STOK BİLGİSİ"); hdr2=next((arr for rn,arr in rows2 if rn==6),[]); ix={h:i for i,h in enumerate(hdr2)}
        for rn,a in rows2:
            if rn<7:continue
            get=lambda h: a[ix[h]] if h in ix and ix[h]<len(a) else ""
            plate=str(get("PLAKA")).strip()
            if not plate:continue
            con.execute("""INSERT OR IGNORE INTO vehicles(
              plate,model_year,km,brand,model,version,color,fuel,transmission,purchase_date,purchase_type,purchase_price,list_price,target_profit,status,created_at,updated_at)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(
              plate,int(float(get("MODEL YILI") or 0)) or None,int(float(get("KM") or 0)),
              str(get("MARKA")).strip(),str(get("MODEL")).strip(),str(get("VERSİYON")).strip(),str(get("RENK")).strip(),
              str(get("YAKIT")).strip(),str(get("VİTES")).strip(),excel_date_to_iso(get("ALIŞ TARİHİ")),"NAKİT",
              float(get("ALIŞ FİYATI") or 0),float(get("SATIŞ FİYATI") or 0),float(get("HEDEF KAZANÇ") or 0),"STOCK",now,now
            ))

# --- Safe master export ---
def _sheet_paths(z):
    wb=ET.fromstring(z.read("xl/workbook.xml")); rels=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rmap={e.attrib["Id"]:e.attrib["Target"] for e in rels}; out={}
    for s in wb.find(f"{{{NS_MAIN}}}sheets"):
        target=rmap[s.attrib[f"{{{NS_REL}}}id"]]
        out[s.attrib["name"]]="xl/"+target if not target.startswith("/") else target.lstrip("/")
    return out

def _ensure_row(sd,rownum):
    for r in sd.findall(f"{{{NS_MAIN}}}row"):
        if int(r.attrib.get("r","0"))==rownum:return r
    r=ET.Element(f"{{{NS_MAIN}}}row",{"r":str(rownum)})
    children=list(sd); pos=len(children)
    for i,x in enumerate(children):
        if int(x.attrib.get("r","0"))>rownum:pos=i;break
    sd.insert(pos,r); return r

def _cell(row,ref):
    for c in row.findall(f"{{{NS_MAIN}}}c"):
        if c.attrib.get("r")==ref:return c
    c=ET.Element(f"{{{NS_MAIN}}}c",{"r":ref}); row.append(c); return c

def _set(cell,value,numeric=False):
    # Preserve style attr 's', replace only content.
    for child in list(cell):cell.remove(child)
    if value in ("",None):
        cell.attrib.pop("t",None);return
    if numeric:
        cell.attrib.pop("t",None)
        v=ET.SubElement(cell,f"{{{NS_MAIN}}}v");v.text=str(float(value))
    else:
        cell.set("t","inlineStr"); isel=ET.SubElement(cell,f"{{{NS_MAIN}}}is");t=ET.SubElement(isel,f"{{{NS_MAIN}}}t");t.text=str(value)

def _export_master_legacy(dest):
    if not TEMPLATE.exists():raise FileNotFoundError(TEMPLATE)
    with connect() as con:
        sales=[dict(r) for r in con.execute("SELECT * FROM sales ORDER BY sale_date,id").fetchall()]
        stocks=[dict(r) for r in con.execute("SELECT * FROM vehicles WHERE status='STOCK' ORDER BY purchase_date,id").fetchall()]
    fd,tmp_name=tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)
    tmp=Path(tmp_name)
    with ZipFile(TEMPLATE,"r") as zin, ZipFile(tmp,"w",ZIP_DEFLATED) as zout:
        paths=_sheet_paths(zin)
        replacements={}
        # Main data entry inputs only. Formula cells remain template formulas.
        path=paths["ARAÇ VERİ GİRİŞİ"]; root=ET.fromstring(zin.read(path)); sd=root.find(f"{{{NS_MAIN}}}sheetData")
        main_cols={"B":"vehicle_info","C":"model_year","D":"plate","E":"purchase_type","F":"purchase_price","G":"purchase_date",
                   "H":"sale_date","N":"extra_expense","R":"customer","S":"sale_type","T":"sale_price","Y":"consultant",
                   "Z":"insurance_income","AA":"credit_income","AB":"warranty_income"}
        # clear existing input area
        for rr in range(4,304):
            row=_ensure_row(sd,rr)
            for col in main_cols:
                _set(_cell(row,f"{col}{rr}"),"")
        for i,s in enumerate(sales[:300],start=4):
            row=_ensure_row(sd,i)
            for col,key in main_cols.items():
                v=s.get(key)
                numeric=key in {"model_year","purchase_price","extra_expense","sale_price","insurance_income","credit_income","warranty_income"}
                if key in {"purchase_date","sale_date"}: v=iso_to_excel(v); numeric=True
                _set(_cell(row,f"{col}{i}"),v,numeric)
        replacements[path]=ET.tostring(root,encoding="utf-8",xml_declaration=True)

        path2=paths["EXTRA STOK BİLGİSİ"]; root2=ET.fromstring(zin.read(path2)); sd2=root2.find(f"{{{NS_MAIN}}}sheetData")
        stock_cols={"B":"plate","C":"model_year","D":"km","E":"brand","F":"model","G":"version","H":"color","I":"purchase_date",
                    "K":"fuel","L":"transmission","M":"purchase_price","N":"list_price","O":"target_profit"}
        for rr in range(7,307):
            row=_ensure_row(sd2,rr)
            for col in stock_cols:_set(_cell(row,f"{col}{rr}"),"")
        for i,s in enumerate(stocks[:300],start=7):
            row=_ensure_row(sd2,i)
            for col,key in stock_cols.items():
                v=s.get(key); numeric=key in {"model_year","km","purchase_price","list_price","target_profit"}
                if key=="purchase_date":v=iso_to_excel(v);numeric=True
                _set(_cell(row,f"{col}{i}"),v,numeric)
        replacements[path2]=ET.tostring(root2,encoding="utf-8",xml_declaration=True)

        for item in zin.infolist():
            if item.filename=="xl/calcChain.xml":continue
            data=replacements.get(item.filename,zin.read(item.filename))
            zout.writestr(item,data)
    Path(dest).parent.mkdir(parents=True,exist_ok=True)
    shutil.move(tmp,dest)
    return Path(dest)

def _num(v, default=0.0):
    try:
        if v in ("",None): return default
        return float(v)
    except Exception:
        return default

def _yes(v):
    return str(v or "").strip().upper() in ("EVET","YES","1","TRUE","AKTİF","AKTIF")

def _row_map_by_number(rows):
    return {rn:arr for rn,arr in rows}

def master_preview(path):
    """
    Reads the RENEW master workbook and returns normalized data.
    Dashboard and consultant performance are intentionally NOT imported as raw values;
    they are derived from sales/stock/expertise/settings after import.
    """
    r=XlsxReader(path)
    required={"ARAÇ VERİ GİRİŞİ","EXTRA STOK BİLGİSİ","GİDER AYARLARI","ALIM AYARLARI","DANIŞMAN AYARLARI","EXPERTİZ TAKİP"}
    missing=sorted(required-set(r.sheets))
    if missing:
        raise ValueError("Ana RENEW Excel formatında eksik sayfalar: "+", ".join(missing))

    # Sales
    sales=[]
    rows=r.sheet_rows("ARAÇ VERİ GİRİŞİ")
    hdr=next((arr for rn,arr in rows if rn==3),[])
    ix={str(h).strip():i for i,h in enumerate(hdr) if str(h).strip()}
    def gv(a,h):
        i=ix.get(h); return a[i] if i is not None and i<len(a) else ""
    for rn,a in rows:
        if rn<4: continue
        plate=str(gv(a,"PLAKA") or "").strip()
        buy=_num(gv(a,"ALIŞ BEDELİ"))
        if not plate or not buy: continue
        sale_date=excel_date_to_iso(gv(a,"SATIŞ TARİHİ"))
        status=str(gv(a,"STOK DURUMU") or "").strip().upper()
        # Sale is considered sold if sale date or sale price exists or Excel status says SOLD
        if status=="SATILDI" or sale_date or _num(gv(a,"SATIŞ BEDELİ"))>0:
            sales.append({
              "plate":plate,
              "vehicle_info":str(gv(a,"OTOMOBİL BİLGİLERİ") or "").strip(),
              "model_year":int(_num(gv(a,"M.YILI"),0)) or None,
              "purchase_type":str(gv(a,"ALIM TÜRÜ") or "NAKİT").strip() or "NAKİT",
              "purchase_price":buy,
              "purchase_date":excel_date_to_iso(gv(a,"ALIŞ TARİHİ")),
              "sale_date":sale_date or excel_date_to_iso(gv(a,"ALIŞ TARİHİ")),
              "extra_expense":_num(gv(a,"EK MASRAF")),
              "customer":str(gv(a,"MÜŞTERİ BİLGİLERİ") or "").strip(),
              "sale_type":str(gv(a,"SATIŞ TÜRÜ") or "NAKİT").strip() or "NAKİT",
              "sale_price":_num(gv(a,"SATIŞ BEDELİ")),
              "consultant":str(gv(a,"SATIŞ DANIŞMANI") or "").strip(),
              "insurance_income":_num(gv(a,"SİGORTA-KASKO GELİRİ")),
              "credit_income":_num(gv(a,"KREDİ GELİRİ")),
              "warranty_income":_num(gv(a,"UZATILMIŞ GARANTİ GELİRİ")),
            })

    # Active stock
    stocks=[]
    rows=r.sheet_rows("EXTRA STOK BİLGİSİ")
    hdr=next((arr for rn,arr in rows if rn==6),[])
    ix={str(h).strip():i for i,h in enumerate(hdr) if str(h).strip()}
    def sv(a,h):
        i=ix.get(h); return a[i] if i is not None and i<len(a) else ""
    for rn,a in rows:
        if rn<7: continue
        plate=str(sv(a,"PLAKA") or "").strip()
        if not plate: continue
        stocks.append({
          "plate":plate,
          "model_year":int(_num(sv(a,"MODEL YILI"),0)) or None,
          "km":int(_num(sv(a,"KM"),0)),
          "brand":str(sv(a,"MARKA") or "").strip(),
          "model":str(sv(a,"MODEL") or "").strip(),
          "version":str(sv(a,"VERSİYON") or "").strip(),
          "color":str(sv(a,"RENK") or "").strip(),
          "fuel":str(sv(a,"YAKIT") or "").strip(),
          "transmission":str(sv(a,"VİTES") or "").strip(),
          "purchase_date":excel_date_to_iso(sv(a,"ALIŞ TARİHİ")),
          "purchase_type":"NAKİT",
          "purchase_price":_num(sv(a,"ALIŞ FİYATI")),
          "list_price":_num(sv(a,"SATIŞ FİYATI")),
          "target_profit":_num(sv(a,"HEDEF KAZANÇ"))
        })

    # Expense settings
    settings={}
    rows=r.sheet_rows("GİDER AYARLARI")
    for rn,a in rows:
        if rn<4 or len(a)<2: continue
        k=str(a[0] or "").strip()
        v=_num(a[1],0)
        if k=="Noter Masrafı": settings["notary_expense"]=v
        elif k=="Ekspertiz Masrafı": settings["expertise_expense"]=v
        elif k=="150 Nokta Kontrol": settings["control150_expense"]=v
        elif k=="Sigorta Gideri": settings["insurance_expense"]=v
        elif k=="SKS Aylık Finansman Oranı": settings["sks_monthly_rate"]=v

    # Purchase rules
    rules=[]
    rows=r.sheet_rows("ALIM AYARLARI")
    for rn,a in rows:
        if rn<4 or not a: continue
        name=str(a[0] or "").strip()
        if not name: continue
        rules.append({
          "name":name,
          "apply_sks":1 if len(a)>1 and _yes(a[1]) else 0,
          "apply_fixed":1 if len(a)>2 and _yes(a[2]) else 0,
          "active":1 if len(a)>3 and _yes(a[3]) else 0
        })

    # Sale types + extra income settings
    sale_types=[]; income_types=[]
    rows=r.sheet_rows("SATIŞ AYARLARI") if "SATIŞ AYARLARI" in r.sheets else []
    for rn,a in rows:
        if rn<4: continue
        if len(a)>0:
            name=str(a[0] or "").strip()
            if name:
                sale_types.append({"name":name,"active":1 if len(a)>1 and _yes(a[1]) else 0})
        if len(a)>3:
            name=str(a[3] or "").strip()
            if name:
                income_types.append({"name":name,"active":1 if len(a)>4 and _yes(a[4]) else 0,
                                     "description":str(a[5] or "").strip() if len(a)>5 else ""})

    # Consultants
    consultants=[]
    rows=r.sheet_rows("DANIŞMAN AYARLARI")
    for rn,a in rows:
        if rn<4 or not a: continue
        name=str(a[0] or "").strip()
        if not name: continue
        consultants.append({
          "name":name,
          "active":1 if len(a)>1 and _yes(a[1]) else 0,
          "target_sales":int(_num(a[2],0)) if len(a)>2 else 0,
          "target_profit":_num(a[3],0) if len(a)>3 else 0
        })

    # Expertise. Workbook itself does not carry a month dimension, so assign to most recent
    # sales month; if there are no sales use current month.
    months=[s["sale_date"][:7] for s in sales if s.get("sale_date")]
    expertise_month=max(months) if months else datetime.now().strftime("%Y-%m")
    expertise=[]
    rows=r.sheet_rows("EXPERTİZ TAKİP")
    for rn,a in rows:
        # Master Excel: gerçek personel alanı 4:13; alt satırlar toplam/özet alanıdır.
        if rn < 4 or rn > 13 or not a: continue
        name=str(a[0] or "").strip()
        if not name or name.replace(".","",1).isdigit(): continue
        expertise.append({
          "consultant":name,
          "month":expertise_month,
          "done_count":int(_num(a[1],0)) if len(a)>1 else 0,
          "converted_count":int(_num(a[2],0)) if len(a)>2 else 0
        })

    sale_months=sorted(set(s["sale_date"][:7] for s in sales if s.get("sale_date")))
    stock_purchase_months=sorted(set(s["purchase_date"][:7] for s in stocks if s.get("purchase_date")))

    return {
      "sales":sales,"stocks":stocks,"settings":settings,"rules":rules,
      "sale_types":sale_types,"income_types":income_types,
      "consultants":consultants,"expertise":expertise,
      "summary":{
        "sales_count":len(sales),"stock_count":len(stocks),"consultant_count":len(consultants),
        "expertise_people":len(expertise),"settings_count":len(settings),"rules_count":len(rules),
        "sale_months":sale_months,"stock_purchase_months":stock_purchase_months,
        "expertise_month":expertise_month,
        "sales_revenue":sum(x["sale_price"] for x in sales),
        "stock_purchase_total":sum(x["purchase_price"] for x in stocks),
        "stock_sale_total":sum(x["list_price"] for x in stocks),
      }
    }

def apply_master_import(path, mode="replace", file_name="RENEW_MASTER.xlsx"):
    """
    replace = backup current DB, then replace operational records/settings with workbook.
    merge   = upsert stocks by plate and sales by plate+sale_date; settings/rules/consultants update.
    The uploaded workbook becomes the new master template after successful import.
    """
    data=master_preview(path)
    from .db import backup_db, log, now
    backup_db()

    with connect() as con:
        if mode=="replace":
            con.execute("DELETE FROM expertise")
            con.execute("DELETE FROM sales")
            con.execute("DELETE FROM vehicles")
            con.execute("DELETE FROM consultants")
            con.execute("DELETE FROM purchase_rules")

        # settings
        for k,v in data["settings"].items():
            con.execute("""INSERT INTO settings(key,value,value_type,updated_at) VALUES(?,?, 'number',?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value,value_type='number',updated_at=excluded.updated_at""",
                        (k,str(v),now()))

        # purchase rules
        for r in data["rules"]:
            con.execute("""INSERT INTO purchase_rules(name,apply_sks,apply_fixed,active) VALUES(?,?,?,?)
            ON CONFLICT(name) DO UPDATE SET apply_sks=excluded.apply_sks,apply_fixed=excluded.apply_fixed,active=excluded.active""",
                        (r["name"],r["apply_sks"],r["apply_fixed"],r["active"]))

        # sale / income settings
        if mode=="replace":
            con.execute("DELETE FROM sale_types")
            con.execute("DELETE FROM income_types")
        for st in data.get("sale_types",[]):
            con.execute("""INSERT INTO sale_types(name,active) VALUES(?,?)
            ON CONFLICT(name) DO UPDATE SET active=excluded.active""",(st["name"],st["active"]))
        for it in data.get("income_types",[]):
            con.execute("""INSERT INTO income_types(name,active,description) VALUES(?,?,?)
            ON CONFLICT(name) DO UPDATE SET active=excluded.active,description=excluded.description""",
                        (it["name"],it["active"],it.get("description","")))

        # consultants
        for c in data["consultants"]:
            con.execute("""INSERT INTO consultants(name,active,target_sales,target_profit) VALUES(?,?,?,?)
            ON CONFLICT(name) DO UPDATE SET active=excluded.active,target_sales=excluded.target_sales,target_profit=excluded.target_profit""",
                        (c["name"],c["active"],c["target_sales"],c["target_profit"]))

        # stocks
        t=now()
        for v in data["stocks"]:
            ex=con.execute("SELECT id FROM vehicles WHERE upper(replace(plate,' ',''))=upper(replace(?,' ',''))",(v["plate"],)).fetchone()
            if ex:
                sets=",".join(f"{k}=?" for k in v if k!="plate")
                con.execute(f"UPDATE vehicles SET {sets},plate=?,status='STOCK',updated_at=? WHERE id=?",
                            tuple(v[k] for k in v if k!="plate")+(v["plate"],t,ex["id"]))
            else:
                keys=list(v)+["status","created_at","updated_at"]
                con.execute(f"INSERT INTO vehicles({','.join(keys)}) VALUES({','.join('?'*len(keys))})",
                            tuple(v.values())+("STOCK",t,t))

        # sales
        for s in data["sales"]:
            if mode=="merge":
                ex=con.execute("""SELECT id FROM sales WHERE upper(replace(plate,' ',''))=upper(replace(?,' ','')) AND sale_date=?""",
                               (s["plate"],s["sale_date"])).fetchone()
            else:
                ex=None
            if ex:
                sets=",".join(f"{k}=?" for k in s)
                con.execute(f"UPDATE sales SET {sets},updated_at=? WHERE id=?",tuple(s.values())+(t,ex["id"]))
            else:
                keys=list(s)+["created_at","updated_at"]
                con.execute(f"INSERT INTO sales({','.join(keys)}) VALUES({','.join('?'*len(keys))})",
                            tuple(s.values())+(t,t))

        # expertise
        for e in data["expertise"]:
            con.execute("""INSERT INTO expertise(consultant,month,done_count,converted_count,updated_at) VALUES(?,?,?,?,?)
            ON CONFLICT(consultant,month) DO UPDATE SET done_count=excluded.done_count,converted_count=excluded.converted_count,updated_at=excluded.updated_at""",
                        (e["consultant"],e["month"],e["done_count"],e["converted_count"],t))

        con.execute("""INSERT INTO import_history(import_type,file_name,mode,sales_count,stock_count,expertise_count,consultant_count,created_at)
        VALUES('MASTER',?,?,?,?,?,?,?)""",
                    (file_name,mode,len(data["sales"]),len(data["stocks"]),len(data["expertise"]),len(data["consultants"]),t))

    # Make the successfully imported workbook the new export template.
    TEMPLATE.parent.mkdir(parents=True,exist_ok=True)
    if TEMPLATE.exists():
        archive=BASE/"backups"/f"MASTER_SABLON_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
        archive.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(TEMPLATE,archive)
    shutil.copy2(path,TEMPLATE)
    log("master_excel","template","IMPORT",f"{file_name} | {mode}")
    return data["summary"]

def _set_formula(cell, formula):
    # Keep style attributes, replace value/formula payload only.
    for child in list(cell): cell.remove(child)
    cell.attrib.pop("t",None)
    f=ET.SubElement(cell,f"{{{NS_MAIN}}}f"); f.text=formula

def _ensure_main_formulas(root, start=4, end=303):
    sd=root.find(f"{{{NS_MAIN}}}sheetData")
    for rr in range(start,end+1):
        row=_ensure_row(sd,rr)
        formulas={
          "A":f'''IF(D{rr}="","",ROW()-3)''',
          "I":f'''IF(G{rr}="","",IF(H{rr}="",TODAY()-G{rr},H{rr}-G{rr}))''',
          "J":f'''IF(F{rr}="","",IFERROR(IF(VLOOKUP(E{rr},'ALIM AYARLARI'!$A$4:$D$20,3,FALSE)="EVET",'GİDER AYARLARI'!$B$4,0),0))''',
          "K":f'''IF(F{rr}="","",'GİDER AYARLARI'!$B$5)''',
          "L":f'''IF(F{rr}="","",'GİDER AYARLARI'!$B$6)''',
          "M":f'''IF(F{rr}="","",IFERROR(IF(VLOOKUP(E{rr},'ALIM AYARLARI'!$A$4:$D$20,3,FALSE)="EVET",'GİDER AYARLARI'!$B$7,0),0))''',
          "O":f'''IF(OR(F{rr}="",I{rr}=""),"",IFERROR(IF(VLOOKUP(E{rr},'ALIM AYARLARI'!$A$4:$D$20,2,FALSE)="EVET",F{rr}*'GİDER AYARLARI'!$B$8*I{rr}/30,0),0))''',
          "P":f'''IF(F{rr}="","",SUM(J{rr}:O{rr}))''',
          "Q":f'''IF(F{rr}="","",F{rr}+P{rr})''',
          "U":f'''IF(OR(F{rr}="",T{rr}=""),"",T{rr}-F{rr})''',
          "V":f'''IF(T{rr}="","",T{rr}-Q{rr})''',
          "W":f'''IFERROR(V{rr}/T{rr},"")''',
          "X":f'''IF(F{rr}="","",IF(H{rr}="","STOKTA","SATILDI"))''',
          "AC":f'''IF(F{rr}="","",SUM(Z{rr}:AB{rr}))''',
          "AD":f'''IF(T{rr}="","",V{rr}+AC{rr})'''
        }
        for col,formula in formulas.items():
            _set_formula(_cell(row,f"{col}{rr}"),formula)

def _ensure_extra_formulas(root, start=7, end=306):
    sd=root.find(f"{{{NS_MAIN}}}sheetData")
    for rr in range(start,end+1):
        row=_ensure_row(sd,rr)
        formulas={
          "A":f'''IF(B{rr}="","",ROW()-6)''',
          "J":f'''IF(I{rr}="","",MAX(0,TODAY()-I{rr}))''',
          "P":f'''IF(M{rr}="","",'GİDER AYARLARI'!$B$10)''',
          "Q":f'''IF(OR(M{rr}="",J{rr}=""),"",M{rr}*'GİDER AYARLARI'!$B$8*J{rr}/30)''',
          "R":f'''IF(M{rr}="","",M{rr}+P{rr}+Q{rr})''',
          "S":f'''IF(OR(N{rr}="",R{rr}=""),"",N{rr}-R{rr})'''
        }
        for col,formula in formulas.items():
            _set_formula(_cell(row,f"{col}{rr}"),formula)

# -------- V6 export override: template-preserving + settings/rules/consultants/expertise --------
def _write_sheet_rows_in_zip(zin, replacements, path, start_row, row_count, col_map, records):
    root=ET.fromstring(replacements.get(path, zin.read(path)))
    sd=root.find(f"{{{NS_MAIN}}}sheetData")
    # clear only editable columns
    for rr in range(start_row,start_row+row_count):
        row=_ensure_row(sd,rr)
        for col in col_map:
            _set(_cell(row,f"{col}{rr}"),"")
    for i,rec in enumerate(records[:row_count],start=start_row):
        row=_ensure_row(sd,i)
        for col,(key,kind) in col_map.items():
            v=rec.get(key,"")
            numeric=(kind=="n")
            if kind=="date":
                v=iso_to_excel(v) if v else ""; numeric=True
            _set(_cell(row,f"{col}{i}"),v,numeric)
    replacements[path]=ET.tostring(root,encoding="utf-8",xml_declaration=True)

def export_master(dest, month=None):
    if not TEMPLATE.exists(): raise FileNotFoundError(TEMPLATE)
    with connect() as con:
        _sales=[dict(r) for r in con.execute("SELECT * FROM sales ORDER BY sale_date,id").fetchall()]
        _stocks=[dict(r) for r in con.execute("SELECT * FROM vehicles WHERE status='STOCK' ORDER BY purchase_date,id").fetchall()]
        sales=[]; _seen_sales=set()
        for r in _sales:
            k=("".join(str(r.get("plate") or "").upper().split()), str(r.get("sale_date") or "")[:10])
            if k in _seen_sales: continue
            _seen_sales.add(k); sales.append(r)
        stocks=[]; _seen_stocks=set()
        for r in _stocks:
            k="".join(str(r.get("plate") or "").upper().split())
            if not k or k in _seen_stocks: continue
            _seen_stocks.add(k); stocks.append(r)
        settings={r["key"]:r["value"] for r in con.execute("SELECT * FROM settings").fetchall()}
        rules=[dict(r) for r in con.execute("SELECT * FROM purchase_rules ORDER BY rowid").fetchall()]
        sale_types=[dict(r) for r in con.execute("SELECT * FROM sale_types ORDER BY rowid").fetchall()]
        income_types=[dict(r) for r in con.execute("SELECT * FROM income_types ORDER BY rowid").fetchall()]
        consultants=[dict(r) for r in con.execute("SELECT * FROM consultants ORDER BY id").fetchall()]
        if not month:
            mr=con.execute("SELECT MAX(month) m FROM expertise").fetchone()
            month=mr["m"] if mr and mr["m"] else datetime.now().strftime("%Y-%m")
        expertise=[dict(r) for r in con.execute("SELECT * FROM expertise WHERE month=? ORDER BY consultant",(month,)).fetchall()]

    fd,tmp_name=tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)
    tmp=Path(tmp_name)
    with ZipFile(TEMPLATE,"r") as zin, ZipFile(tmp,"w",ZIP_DEFLATED) as zout:
        paths=_sheet_paths(zin); replacements={}

        main_map={"B":("vehicle_info","s"),"C":("model_year","n"),"D":("plate","s"),"E":("purchase_type","s"),
                  "F":("purchase_price","n"),"G":("purchase_date","date"),"H":("sale_date","date"),"N":("extra_expense","n"),
                  "R":("customer","s"),"S":("sale_type","s"),"T":("sale_price","n"),"Y":("consultant","s"),
                  "Z":("insurance_income","n"),"AA":("credit_income","n"),"AB":("warranty_income","n")}
        _write_sheet_rows_in_zip(zin,replacements,paths["ARAÇ VERİ GİRİŞİ"],4,300,main_map,sales)
        # Replace fragile shared/manual formula pattern with explicit row formulas.
        _main_path=paths["ARAÇ VERİ GİRİŞİ"]
        _main_root=ET.fromstring(replacements[_main_path]); _ensure_main_formulas(_main_root,4,303)
        replacements[_main_path]=ET.tostring(_main_root,encoding="utf-8",xml_declaration=True)

        stock_map={"B":("plate","s"),"C":("model_year","n"),"D":("km","n"),"E":("brand","s"),"F":("model","s"),
                   "G":("version","s"),"H":("color","s"),"I":("purchase_date","date"),"K":("fuel","s"),"L":("transmission","s"),
                   "M":("purchase_price","n"),"N":("list_price","n"),"O":("target_profit","n")}
        _write_sheet_rows_in_zip(zin,replacements,paths["EXTRA STOK BİLGİSİ"],7,300,stock_map,stocks)
        _extra_path=paths["EXTRA STOK BİLGİSİ"]
        _extra_root=ET.fromstring(replacements[_extra_path]); _ensure_extra_formulas(_extra_root,7,306)
        replacements[_extra_path]=ET.tostring(_extra_root,encoding="utf-8",xml_declaration=True)

        # GİDER AYARLARI
        if "GİDER AYARLARI" in paths:
            path=paths["GİDER AYARLARI"]; root=ET.fromstring(zin.read(path)); sd=root.find(f"{{{NS_MAIN}}}sheetData")
            vals={4:float(settings.get("notary_expense",0)),5:float(settings.get("expertise_expense",0)),
                  6:float(settings.get("control150_expense",0)),7:float(settings.get("insurance_expense",0)),
                  8:float(settings.get("sks_monthly_rate",0))}
            for rr,v in vals.items(): _set(_cell(_ensure_row(sd,rr),f"B{rr}"),v,True)
            replacements[path]=ET.tostring(root,encoding="utf-8",xml_declaration=True)

        # ALIM AYARLARI
        if "ALIM AYARLARI" in paths:
            path=paths["ALIM AYARLARI"]; root=ET.fromstring(zin.read(path)); sd=root.find(f"{{{NS_MAIN}}}sheetData")
            for rr in range(4,21):
                row=_ensure_row(sd,rr)
                for col in "ABCD": _set(_cell(row,f"{col}{rr}"),"")
            for i,r in enumerate(rules[:17],start=4):
                row=_ensure_row(sd,i)
                _set(_cell(row,f"A{i}"),r["name"])
                _set(_cell(row,f"B{i}"),"EVET" if r["apply_sks"] else "HAYIR")
                _set(_cell(row,f"C{i}"),"EVET" if r["apply_fixed"] else "HAYIR")
                _set(_cell(row,f"D{i}"),"EVET" if r["active"] else "HAYIR")
            replacements[path]=ET.tostring(root,encoding="utf-8",xml_declaration=True)

        # SATIŞ AYARLARI
        if "SATIŞ AYARLARI" in paths:
            path=paths["SATIŞ AYARLARI"]; root=ET.fromstring(zin.read(path)); sd=root.find(f"{{{NS_MAIN}}}sheetData")
            for rr in range(4,21):
                row=_ensure_row(sd,rr)
                for col in ["A","B","D","E","F"]: _set(_cell(row,f"{col}{rr}"),"")
            for i,r in enumerate(sale_types[:17],start=4):
                row=_ensure_row(sd,i); _set(_cell(row,f"A{i}"),r["name"]); _set(_cell(row,f"B{i}"),"EVET" if r["active"] else "HAYIR")
            for i,r in enumerate(income_types[:17],start=4):
                row=_ensure_row(sd,i); _set(_cell(row,f"D{i}"),r["name"]); _set(_cell(row,f"E{i}"),"EVET" if r["active"] else "HAYIR"); _set(_cell(row,f"F{i}"),r.get("description",""))
            replacements[path]=ET.tostring(root,encoding="utf-8",xml_declaration=True)

        # DANIŞMAN AYARLARI
        if "DANIŞMAN AYARLARI" in paths:
            path=paths["DANIŞMAN AYARLARI"]; root=ET.fromstring(zin.read(path)); sd=root.find(f"{{{NS_MAIN}}}sheetData")
            for rr in range(4,104):
                row=_ensure_row(sd,rr)
                for col in "ABCD": _set(_cell(row,f"{col}{rr}"),"")
            for i,r in enumerate(consultants[:100],start=4):
                row=_ensure_row(sd,i); _set(_cell(row,f"A{i}"),r["name"]); _set(_cell(row,f"B{i}"),"EVET" if r["active"] else "HAYIR")
                _set(_cell(row,f"C{i}"),r["target_sales"],True); _set(_cell(row,f"D{i}"),r["target_profit"],True)
            replacements[path]=ET.tostring(root,encoding="utf-8",xml_declaration=True)

        # EXPERTİZ TAKİP: 4:13 giriş alanı; toplam/özet/formül satırları korunur.
        if "EXPERTİZ TAKİP" in paths:
            path=paths["EXPERTİZ TAKİP"]; root=ET.fromstring(zin.read(path)); sd=root.find(f"{{{NS_MAIN}}}sheetData")
            for rr in range(4,14):
                row=_ensure_row(sd,rr)
                for col in ["A","B","C"]: _set(_cell(row,f"{col}{rr}"),"")
            for i,r in enumerate(expertise[:10],start=4):
                row=_ensure_row(sd,i)
                _set(_cell(row,f"A{i}"),r["consultant"])
                _set(_cell(row,f"B{i}"),r["done_count"],True)
                _set(_cell(row,f"C{i}"),r["converted_count"],True)
            replacements[path]=ET.tostring(root,encoding="utf-8",xml_declaration=True)

        for item in zin.infolist():
            if item.filename=="xl/calcChain.xml": continue
            zout.writestr(item,replacements.get(item.filename,zin.read(item.filename)))

    Path(dest).parent.mkdir(parents=True,exist_ok=True)
    shutil.move(tmp,dest)
    return Path(dest)

# -------- V6 full master seed override --------
def seed_from_master_if_empty():
    """
    First launch: seed ALL workbook configuration, not only sales/stock.
    Includes EXPERTİZ TAKİP, DANIŞMAN AYARLARI, ALIM/SATIŞ/GİDER settings.
    """
    with connect() as con:
        counts=con.execute("""SELECT
          (SELECT COUNT(*) FROM sales) s,
          (SELECT COUNT(*) FROM vehicles) v,
          (SELECT COUNT(*) FROM expertise) e""").fetchone()
    if counts["s"] or counts["v"] or counts["e"] or not TEMPLATE.exists():
        return
    data=master_preview(TEMPLATE)
    t=now()
    with connect() as con:
        for k,v in data["settings"].items():
            con.execute("""INSERT INTO settings(key,value,value_type,updated_at) VALUES(?,?,'number',?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at""",(k,str(v),t))
        for r in data["rules"]:
            con.execute("""INSERT INTO purchase_rules(name,apply_sks,apply_fixed,active) VALUES(?,?,?,?)
            ON CONFLICT(name) DO UPDATE SET apply_sks=excluded.apply_sks,apply_fixed=excluded.apply_fixed,active=excluded.active""",
                        (r["name"],r["apply_sks"],r["apply_fixed"],r["active"]))
        if data.get("sale_types"):
            con.execute("DELETE FROM sale_types")
            for r in data["sale_types"]: con.execute("INSERT INTO sale_types(name,active) VALUES(?,?)",(r["name"],r["active"]))
        if data.get("income_types"):
            con.execute("DELETE FROM income_types")
            for r in data["income_types"]: con.execute("INSERT INTO income_types(name,active,description) VALUES(?,?,?)",(r["name"],r["active"],r.get("description","")))
        for c in data["consultants"]:
            con.execute("""INSERT INTO consultants(name,active,target_sales,target_profit) VALUES(?,?,?,?)
            ON CONFLICT(name) DO UPDATE SET active=excluded.active,target_sales=excluded.target_sales,target_profit=excluded.target_profit""",
                        (c["name"],c["active"],c["target_sales"],c["target_profit"]))
        for v in data["stocks"]:
            keys=list(v)+["status","created_at","updated_at"]
            con.execute(f"INSERT OR REPLACE INTO vehicles({','.join(keys)}) VALUES({','.join('?'*len(keys))})",tuple(v.values())+("STOCK",t,t))
        for s in data["sales"]:
            keys=list(s)+["created_at","updated_at"]
            con.execute(f"INSERT INTO sales({','.join(keys)}) VALUES({','.join('?'*len(keys))})",tuple(s.values())+(t,t))
        for e in data["expertise"]:
            con.execute("""INSERT INTO expertise(consultant,month,done_count,converted_count,updated_at) VALUES(?,?,?,?,?)
            ON CONFLICT(consultant,month) DO UPDATE SET done_count=excluded.done_count,converted_count=excluded.converted_count,updated_at=excluded.updated_at""",
                        (e["consultant"],e["month"],e["done_count"],e["converted_count"],t))

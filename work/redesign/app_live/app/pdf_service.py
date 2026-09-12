from __future__ import annotations
# === RENEW_UNICODE_PDF_FONT_FIX_BEGIN ===
# ReportLab standart Helvetica fontlarini Unicode/Turkce destekli
# DejaVu Sans ile ayni font adlari altinda override eder.
from reportlab.pdfbase import pdfmetrics as _renew_pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont as _RenewTTFont

_RENEW_FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
_RENEW_FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

_renew_pdfmetrics.registerFont(
    _RenewTTFont("RenewUnicode", _RENEW_FONT_REGULAR)
)
_renew_pdfmetrics.registerFont(
    _RenewTTFont("RenewUnicodeBold", _RENEW_FONT_BOLD)
)

# Standart font adlarini da override et; mevcut rapor kodunu degistirmeden
# Canvas, Paragraph, TableStyle ve sample stylesheet'leri Unicode kullanir.
_renew_pdfmetrics.registerFont(
    _RenewTTFont("Helvetica", _RENEW_FONT_REGULAR)
)
_renew_pdfmetrics.registerFont(
    _RenewTTFont("Helvetica-Bold", _RENEW_FONT_BOLD)
)
_renew_pdfmetrics.registerFont(
    _RenewTTFont("Helvetica-Oblique", _RENEW_FONT_REGULAR)
)
_renew_pdfmetrics.registerFont(
    _RenewTTFont("Helvetica-BoldOblique", _RENEW_FONT_BOLD)
)

# Family eslesmesi: <b> ve benzeri Paragraph gecisleri icin.
_renew_pdfmetrics.registerFontFamily(
    "Helvetica",
    normal="Helvetica",
    bold="Helvetica-Bold",
    italic="Helvetica-Oblique",
    boldItalic="Helvetica-BoldOblique",
)
# === RENEW_UNICODE_PDF_FONT_FIX_END ===

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER
from .calc import sale_calc, stock_calc
from .db import connect, BASE

REPORTS=BASE/"reports"

def _register_fonts():
    candidates=[
      (r"C:\Windows\Fonts\arial.ttf",r"C:\Windows\Fonts\arialbd.ttf"),
      (r"C:\Windows\Fonts\calibri.ttf",r"C:\Windows\Fonts\calibrib.ttf")
    ]
    for regular,bold in candidates:
        if Path(regular).exists():
            try:
                pdfmetrics.registerFont(TTFont("RenewFont",regular))
                if Path(bold).exists(): pdfmetrics.registerFont(TTFont("RenewFontBold",bold))
                else: pdfmetrics.registerFont(TTFont("RenewFontBold",regular))
                return "RenewFont","RenewFontBold"
            except Exception: pass
    return "Helvetica","Helvetica-Bold"

FONT,FONT_BOLD=_register_fonts()

def money(v): return f"{float(v or 0):,.0f} TL".replace(",", ".")

def _styles():
    st=getSampleStyleSheet()
    st.add(ParagraphStyle(name="RT",parent=st["Title"],fontName=FONT_BOLD,fontSize=16,leading=19,textColor=colors.HexColor("#0F172A"),spaceAfter=7))
    st.add(ParagraphStyle(name="RS",parent=st["BodyText"],fontName=FONT,fontSize=8,leading=11,textColor=colors.HexColor("#64748B"),spaceAfter=8))
    st.add(ParagraphStyle(name="RH",parent=st["Heading2"],fontName=FONT_BOLD,fontSize=10.5,textColor=colors.HexColor("#1E3A8A"),spaceBefore=7,spaceAfter=5))
    return st

def _footer(canvas,doc):
    canvas.saveState()
    canvas.setFont(FONT,7)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.drawString(28,16,"Çayan Tarsus RENEW • Localhost Yönetim Sistemi")
    canvas.drawRightString(doc.pagesize[0]-28,16,f"Sayfa {doc.page}")
    canvas.restoreState()

def _table(data,widths=None,profit_index=None):
    t=Table(data,repeatRows=1,colWidths=widths)
    style=[
      ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1E3A5F")),
      ("TEXTCOLOR",(0,0),(-1,0),colors.white),
      ("FONTNAME",(0,0),(-1,0),FONT_BOLD),
      ("FONTNAME",(0,1),(-1,-1),FONT),
      ("FONTSIZE",(0,0),(-1,-1),6.7),
      ("GRID",(0,0),(-1,-1),0.25,colors.HexColor("#CBD5E1")),
      ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
      ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F8FAFC")])
    ]
    if profit_index is not None:
        for i,row in enumerate(data[1:],start=1):
            try:
                raw=row[profit_index]
                n=float(str(raw).replace("TL","").replace(".","").replace(",",".").strip())
            except: n=0
            if n<0:
                style.append(("BACKGROUND",(0,i),(-1,i),colors.HexColor("#FEE2E2")))
                style.append(("TEXTCOLOR",(profit_index,i),(profit_index,i),colors.HexColor("#B91C1C")))
            elif n>0:
                style.append(("TEXTCOLOR",(profit_index,i),(profit_index,i),colors.HexColor("#15803D")))
    t.setStyle(TableStyle(style));return t

def _doc(path,land=True):
    return SimpleDocTemplate(str(path),pagesize=landscape(A4) if land else A4,rightMargin=22,leftMargin=22,topMargin=28,bottomMargin=28)

def sales_report(month):
    REPORTS.mkdir(parents=True,exist_ok=True);out=REPORTS/f"Satis_Karlilik_{month}.pdf"
    with connect() as con: rows=[dict(r) for r in con.execute("SELECT * FROM sales WHERE substr(sale_date,1,7)=? ORDER BY sale_date,plate",(month,)).fetchall()]
    cc=[sale_calc(r) for r in rows];st=_styles();story=[
      Paragraph("AYLIK SATIŞ & KÂRLILIK RAPORU",st["RT"]),
      Paragraph(f"Dönem: {month} • Satış: {len(rows)} • Ciro: {money(sum(r['sale_price'] for r in rows))} • Performans Kârı: {money(sum(c['performance_profit'] for c in cc))}",st["RS"])
    ]
    data=[["Tarih","Plaka","Araç","Alım Türü","Alış","SKS","Gider","Maliyet","Satış","Net Kâr","Perf. Kâr","Danışman"]]
    for r,c in zip(rows,cc):data.append([r["sale_date"],r["plate"],r["vehicle_info"],r["purchase_type"],money(r["purchase_price"]),c["sks_days"],money(c["total_expense"]),money(c["total_cost"]),money(r["sale_price"]),money(c["net_profit"]),money(c["performance_profit"]),r["consultant"]])
    story.append(_table(data,[48,55,125,65,58,30,58,65,58,58,58,80],10));_doc(out).build(story,onFirstPage=_footer,onLaterPages=_footer);return out

def stock_report():
    REPORTS.mkdir(parents=True,exist_ok=True);out=REPORTS/"Guncel_Stok_Raporu.pdf"
    with connect() as con: rows=[dict(r) for r in con.execute("SELECT * FROM vehicles WHERE status='STOCK' ORDER BY purchase_date,plate").fetchall()]
    cc=[stock_calc(r) for r in rows];st=_styles();story=[Paragraph("GÜNCEL STOK & SKS RAPORU",st["RT"]),Paragraph(f"Aktif stok: {len(rows)} • Toplam stok maliyeti: {money(sum(c['total_cost'] for c in cc))} • Tahmini kâr: {money(sum(c['estimated_profit'] for c in cc))}",st["RS"])]
    data=[["Plaka","Araç","Yıl","KM","Alış Tarihi","SKS","Alış","Satış","Sabit Gider","SKS Finansman","Maliyet","Tahmini Kâr"]]
    for r,c in zip(rows,cc):data.append([r["plate"],f"{r['brand']} {r['model']} {r['version']}".strip(),r["model_year"] or "",r["km"] or 0,r["purchase_date"],c["sks_days"],money(r["purchase_price"]),money(r["list_price"]),money(c["fixed_expense"]),money(c["sks_finance"]),money(c["total_cost"]),money(c["estimated_profit"])])
    story.append(_table(data,[55,135,30,45,60,28,60,60,62,70,65,65],11));_doc(out).build(story,onFirstPage=_footer,onLaterPages=_footer);return out

def purchase_report(month):
    REPORTS.mkdir(parents=True,exist_ok=True);out=REPORTS/f"Alim_Performans_{month}.pdf"
    with connect() as con: rows=[dict(r) for r in con.execute("SELECT * FROM vehicles WHERE substr(purchase_date,1,7)=? ORDER BY purchase_date,plate",(month,)).fetchall()]
    st=_styles();story=[Paragraph("AYLIK ALIM PERFORMANS RAPORU",st["RT"]),Paragraph(f"Dönem: {month} • Alınan araç: {len(rows)} • Alış değeri: {money(sum(r['purchase_price'] for r in rows))}",st["RS"])]
    data=[["Tarih","Plaka","Marka","Model","Versiyon","Yıl","KM","Alım Türü","Alış","Liste Satış","Durum"]]
    for r in rows:data.append([r["purchase_date"],r["plate"],r["brand"],r["model"],r["version"],r["model_year"] or "",r["km"] or 0,r["purchase_type"],money(r["purchase_price"]),money(r["list_price"]),r["status"]])
    story.append(_table(data,[55,55,55,55,120,30,45,65,65,65,45]));_doc(out).build(story,onFirstPage=_footer,onLaterPages=_footer);return out

def consultant_report(month):
    REPORTS.mkdir(parents=True,exist_ok=True);out=REPORTS/f"Danisman_Performans_{month}.pdf"
    with connect() as con:
        consultants=[dict(r) for r in con.execute("SELECT * FROM consultants WHERE active=1 ORDER BY name").fetchall()]
        sales=[dict(r) for r in con.execute("SELECT * FROM sales WHERE substr(sale_date,1,7)=?",(month,)).fetchall()]
    st=_styles();story=[Paragraph("DANIŞMAN PERFORMANS RAPORU",st["RT"]),Paragraph(f"Dönem: {month}",st["RS"])]
    data=[["Danışman","Satış","Ciro","Perf. Kâr","Araç Başı","Ort. SKS","Hedef Satış","Hedef Kâr","Satış Hedef %"]]
    for c in consultants:
        rr=[x for x in sales if (x.get("consultant") or "").strip().upper()==c["name"].strip().upper()];cc=[sale_calc(x) for x in rr];perf=sum(x["performance_profit"] for x in cc)
        data.append([c["name"],len(rr),money(sum(x["sale_price"] for x in rr)),money(perf),money(perf/len(rr) if rr else 0),f"{sum(x['sks_days'] for x in cc)/len(cc):.1f}" if cc else "0",c["target_sales"],money(c["target_profit"]),f"%{(len(rr)/c['target_sales']*100 if c['target_sales'] else 0):.1f}"])
    story.append(_table(data,[120,40,75,75,70,45,55,75,55],3));_doc(out).build(story,onFirstPage=_footer,onLaterPages=_footer);return out

def expertise_report(month):
    REPORTS.mkdir(parents=True,exist_ok=True);out=REPORTS/f"Ekspertiz_Takip_{month}.pdf"
    with connect() as con:
        rows=[dict(r) for r in con.execute("SELECT * FROM expertise WHERE month=? ORDER BY consultant",(month,)).fetchall()]
        exp_cost=float((con.execute("SELECT value FROM settings WHERE key='expertise_expense'").fetchone() or {"value":3900})["value"])
    st=_styles();story=[Paragraph("EKSPERTİZ TAKİP RAPORU",st["RT"]),Paragraph(f"Dönem: {month} • Personel: {len(rows)} • Toplam ekspertiz: {sum(r['done_count'] for r in rows)}",st["RS"])]
    data=[["Personel","Yapılan Ekspertiz","Alıma Dönüşen","Dönüşüm","Toplam Maliyet","Alım Başı Maliyet"]]
    for r in rows:
        cost=r["done_count"]*exp_cost
        data.append([r["consultant"],r["done_count"],r["converted_count"],f"%{(r['converted_count']/r['done_count']*100 if r['done_count'] else 0):.1f}",money(cost),money(cost/r["converted_count"] if r["converted_count"] else 0)])
    story.append(_table(data,[145,80,80,65,90,95]));_doc(out,False).build(story,onFirstPage=_footer,onLaterPages=_footer);return out

def profit_loss_report(month):
    REPORTS.mkdir(parents=True,exist_ok=True);out=REPORTS/f"Kar_Zarar_Analizi_{month}.pdf"
    with connect() as con: rows=[dict(r) for r in con.execute("SELECT * FROM sales WHERE substr(sale_date,1,7)=? ORDER BY sale_date,plate",(month,)).fetchall()]
    pairs=[(r,sale_calc(r)) for r in rows];pairs.sort(key=lambda x:x[1]["performance_profit"])
    st=_styles();story=[Paragraph("KÂR / ZARAR ANALİZİ",st["RT"]),Paragraph(f"Dönem: {month} • Zararlı satış: {sum(c['performance_profit']<0 for _,c in pairs)} • Toplam performans kârı: {money(sum(c['performance_profit'] for _,c in pairs))}",st["RS"])]
    data=[["Tarih","Plaka","Araç","Danışman","Alış","Gider","Maliyet","Satış","SKS","Net Kâr","Perf. Kâr"]]
    for r,c in pairs:data.append([r["sale_date"],r["plate"],r["vehicle_info"],r["consultant"],money(r["purchase_price"]),money(c["total_expense"]),money(c["total_cost"]),money(r["sale_price"]),c["sks_days"],money(c["net_profit"]),money(c["performance_profit"])])
    story.append(_table(data,[50,55,135,90,62,62,65,62,30,62,62],10));_doc(out).build(story,onFirstPage=_footer,onLaterPages=_footer);return out

def critical_stock_report():
    REPORTS.mkdir(parents=True,exist_ok=True);out=REPORTS/"Kritik_SKS_Stok_Raporu.pdf"
    with connect() as con: rows=[dict(r) for r in con.execute("SELECT * FROM vehicles WHERE status='STOCK' ORDER BY purchase_date").fetchall()]
    pairs=[(r,stock_calc(r)) for r in rows];pairs.sort(key=lambda x:x[1]["sks_days"],reverse=True)
    st=_styles();story=[Paragraph("KRİTİK SKS / STOK RİSK RAPORU",st["RT"]),Paragraph("0–30 normal • 31–60 takip • 61–90 aksiyon • 90+ kritik",st["RS"])]
    data=[["Plaka","Araç","Alış Tarihi","SKS","Alış","Liste Satış","Finansman","Maliyet","Tahmini Kâr","Risk"]]
    for r,c in pairs:
        risk="KRİTİK" if c["sks_days"]>90 else "AKSİYON" if c["sks_days"]>60 else "TAKİP" if c["sks_days"]>30 else "NORMAL"
        data.append([r["plate"],f"{r['brand']} {r['model']} {r['version']}".strip(),r["purchase_date"],c["sks_days"],money(r["purchase_price"]),money(r["list_price"]),money(c["sks_finance"]),money(c["total_cost"]),money(c["estimated_profit"]),risk])
    story.append(_table(data,[55,135,60,30,65,65,65,65,65,50],8));_doc(out).build(story,onFirstPage=_footer,onLaterPages=_footer);return out

def management_report(month):
    REPORTS.mkdir(parents=True,exist_ok=True);out=REPORTS/f"Yonetici_Tam_Rapor_{month}.pdf"
    with connect() as con:
        sales=[dict(r) for r in con.execute("SELECT * FROM sales WHERE substr(sale_date,1,7)=?",(month,)).fetchall()]
        stocks=[dict(r) for r in con.execute("SELECT * FROM vehicles WHERE status='STOCK' ORDER BY purchase_date").fetchall()]
        exp=[dict(r) for r in con.execute("SELECT * FROM expertise WHERE month=?",(month,)).fetchall()]
    sc=[sale_calc(x) for x in sales];stc=[stock_calc(x) for x in stocks];st=_styles()
    story=[Paragraph("AYLIK YÖNETİCİ TAM RAPORU",st["RT"]),Paragraph(f"Dönem: {month}",st["RS"]),Paragraph("Yönetici KPI Özeti",st["RH"])]
    kpi=[["KPI","Değer"],["Satış Adedi",len(sales)],["Ciro",money(sum(r["sale_price"] for r in sales))],["Net Kâr",money(sum(c["net_profit"] for c in sc))],["Performans Kârı",money(sum(c["performance_profit"] for c in sc))],["Güncel Stok",len(stocks)],["Stok Maliyeti",money(sum(c["total_cost"] for c in stc))],["Tahmini Stok Kârı",money(sum(c["estimated_profit"] for c in stc))],["90+ Kritik Stok",sum(c["sks_days"]>90 for c in stc)],["Ekspertiz",sum(r["done_count"] for r in exp)],["Alıma Dönüşen",sum(r["converted_count"] for r in exp)]]
    story.append(_table(kpi,[180,150]));story.append(Spacer(1,8));story.append(Paragraph("Satış Detayı",st["RH"]))
    data=[["Tarih","Plaka","Araç","Danışman","Satış","Maliyet","SKS","Perf. Kâr"]]
    for r,c in zip(sales,sc):data.append([r["sale_date"],r["plate"],r["vehicle_info"],r["consultant"],money(r["sale_price"]),money(c["total_cost"]),c["sks_days"],money(c["performance_profit"])])
    story.append(_table(data,[55,60,160,100,75,80,35,80],7));story.append(PageBreak());story.append(Paragraph("Güncel Stok / Risk",st["RH"]))
    data=[["Plaka","Araç","SKS","Alış","Satış","Finansman","Maliyet","Tahmini Kâr"]]
    for r,c in zip(stocks,stc):data.append([r["plate"],f"{r['brand']} {r['model']} {r['version']}".strip(),c["sks_days"],money(r["purchase_price"]),money(r["list_price"]),money(c["sks_finance"]),money(c["total_cost"]),money(c["estimated_profit"])])
    story.append(_table(data,[60,165,35,75,75,80,80,80],7));_doc(out).build(story,onFirstPage=_footer,onLaterPages=_footer);return out

def acquisition_report(month):
    REPORTS.mkdir(parents=True,exist_ok=True);out=REPORTS/f"Aylik_Alim_Kaynak_{month}.pdf"
    with connect() as con:rows=[dict(r) for r in con.execute("SELECT * FROM acquisitions WHERE substr(purchase_date,1,7)=? ORDER BY purchase_date,id",(month,)).fetchall()]
    st=_styles();total=sum(r["purchase_price"] for r in rows);exp=sum(r["expense"] for r in rows)
    story=[Paragraph(f"Aylık Araç Alım & Kaynak Raporu • {month}",st["RT"]),Paragraph("Araç bazında alım tarihi, kaynak/ekspertiz personeli, alım türü ve maliyet takibi.",st["RS"]),Paragraph(f"Toplam araç: {len(rows)} • Alış: {money(total)} • Masraf: {money(exp)} • Toplam maliyet: {money(total+exp)}",st["RH"])]
    data=[["Tarih","Plaka","Araç","Alım Türü","Alınan Kişi","Alış","Masraf","Toplam"]]
    for r in rows:data.append([r["purchase_date"],r["plate"]," ".join(str(r.get(k) or "") for k in ("brand","model","version")).strip(),r["purchase_type"],r["acquired_by"],money(r["purchase_price"]),money(r["expense"]),money(r["purchase_price"]+r["expense"])])
    story.append(_table(data,[52,58,150,65,105,68,60,70]));doc=_doc(out,True);doc.build(story,onFirstPage=_footer,onLaterPages=_footer);return out

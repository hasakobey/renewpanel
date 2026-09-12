from __future__ import annotations
from datetime import datetime
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
from .calc import sale_calc, stock_calc
from .db import connect, BASE

REPORTS=BASE/"reports"
NAVY=colors.HexColor("#0B2545"); BLUE=colors.HexColor("#1769AA")
GREEN=colors.HexColor("#16875B"); RED=colors.HexColor("#C53D3D")
AMBER=colors.HexColor("#B7791F"); INK=colors.HexColor("#14253D")
MUTED=colors.HexColor("#65758B"); LINE=colors.HexColor("#D9E3EF")
SOFT=colors.HexColor("#F5F8FC")

def _register_fonts():
    candidates=[
      ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
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
    st.add(ParagraphStyle(name="RT",parent=st["Title"],fontName=FONT_BOLD,fontSize=17,leading=21,textColor=NAVY,spaceAfter=3))
    st.add(ParagraphStyle(name="RS",parent=st["BodyText"],fontName=FONT,fontSize=8.2,leading=12,textColor=MUTED,spaceAfter=10))
    st.add(ParagraphStyle(name="RH",parent=st["Heading2"],fontName=FONT_BOLD,fontSize=11,textColor=NAVY,spaceBefore=9,spaceAfter=6))
    st.add(ParagraphStyle(name="EMPTY",parent=st["BodyText"],fontName=FONT,fontSize=9,textColor=MUTED,alignment=TA_CENTER))
    return st

def _footer(canvas,doc):
    canvas.saveState()
    width,height=doc.pagesize
    canvas.setFillColor(NAVY);canvas.rect(0,height-8*mm,width,8*mm,fill=1,stroke=0)
    canvas.setFillColor(colors.white);canvas.setFont(FONT_BOLD,8)
    canvas.drawString(doc.leftMargin,height-5.2*mm,"R  RENEW PRO")
    canvas.setFont(FONT,6.7);canvas.drawRightString(width-doc.rightMargin,height-5.2*mm,"Çayan Tarsus • Yönetim Raporlama Merkezi")
    canvas.setStrokeColor(LINE);canvas.line(doc.leftMargin,12*mm,width-doc.rightMargin,12*mm)
    canvas.setFont(FONT,6.5);canvas.setFillColor(MUTED)
    canvas.drawString(doc.leftMargin,7.5*mm,f"Oluşturulma: {datetime.now():%d.%m.%Y %H:%M}")
    canvas.drawRightString(width-doc.rightMargin,7.5*mm,f"Sayfa {doc.page}")
    canvas.restoreState()

def _kpis(items):
    cells=[]
    for label,value,tone in items:
        color={"green":GREEN,"red":RED,"amber":AMBER}.get(tone,NAVY)
        p=Paragraph(f'<font size="7" color="{MUTED.hexval()}"><b>{label.upper()}</b></font><br/><font size="13" color="{color.hexval()}"><b>{value}</b></font>',_styles()["RS"])
        cells.append(p)
    while len(cells)%4: cells.append("")
    t=Table([cells[i:i+4] for i in range(0,len(cells),4)],colWidths=[125]*4,hAlign="LEFT")
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),SOFT),("BOX",(0,0),(-1,-1),.6,LINE),("INNERGRID",(0,0),(-1,-1),.6,LINE),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),9),("RIGHTPADDING",(0,0),(-1,-1),9),("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
    return t

def _intro(title,subtitle,month=None):
    st=_styles();period=f" • Dönem: {month}" if month else " • Güncel durum"
    return [Spacer(1,2*mm),Paragraph(title,st["RT"]),Paragraph(subtitle+period,st["RS"])]

def _table(data,widths=None,profit_index=None):
    if len(data)==1:
        t=Table([[Paragraph("Bu dönem için kayıt bulunmuyor.",_styles()["EMPTY"])]],colWidths=[sum(widths) if widths else 500])
        t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),SOFT),("BOX",(0,0),(-1,-1),.6,LINE),("TOPPADDING",(0,0),(-1,-1),18),("BOTTOMPADDING",(0,0),(-1,-1),18)]));return t
    t=Table(data,repeatRows=1,colWidths=widths)
    style=[
      ("BACKGROUND",(0,0),(-1,0),NAVY),
      ("TEXTCOLOR",(0,0),(-1,0),colors.white),
      ("FONTNAME",(0,0),(-1,0),FONT_BOLD),
      ("FONTNAME",(0,1),(-1,-1),FONT),
      ("FONTSIZE",(0,0),(-1,-1),6.7),
      ("LINEBELOW",(0,0),(-1,-1),0.25,LINE),
      ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
      ("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4),
      ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
      ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,SOFT])
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
    return SimpleDocTemplate(str(path),pagesize=landscape(A4) if land else A4,rightMargin=12*mm,leftMargin=12*mm,topMargin=16*mm,bottomMargin=17*mm,title="RENEW PRO Yönetim Raporu",author="RENEW PRO")

def sales_report(month):
    REPORTS.mkdir(parents=True,exist_ok=True);out=REPORTS/f"Satis_Karlilik_{month}.pdf"
    with connect() as con: rows=[dict(r) for r in con.execute("SELECT * FROM sales WHERE substr(sale_date,1,7)=? ORDER BY sale_date,plate",(month,)).fetchall()]
    cc=[sale_calc(r) for r in rows];st=_styles();perf=sum(c['performance_profit'] for c in cc)
    story=_intro("Aylık Satış & Kârlılık Raporu","Araç bazlı maliyet, satış ve performans görünümü",month)
    story += [_kpis([("Satış adedi",len(rows),"blue"),("Ciro",money(sum(r['sale_price'] for r in rows)),"blue"),("Net kâr",money(sum(c['net_profit'] for c in cc)),"green"),("Performans kârı",money(perf),"green" if perf>=0 else "red")]),Paragraph("Satış Detayı",st["RH"])]
    data=[["Tarih","Plaka","Araç","Alım Türü","Alış","SKS","Gider","Maliyet","Satış","Net Kâr","Perf. Kâr","Danışman"]]
    for r,c in zip(rows,cc):data.append([r["sale_date"],r["plate"],r["vehicle_info"],r["purchase_type"],money(r["purchase_price"]),c["sks_days"],money(c["total_expense"]),money(c["total_cost"]),money(r["sale_price"]),money(c["net_profit"]),money(c["performance_profit"]),r["consultant"]])
    story.append(_table(data,[48,55,125,65,58,30,58,65,58,58,58,80],10));_doc(out).build(story,onFirstPage=_footer,onLaterPages=_footer);return out

def stock_report():
    REPORTS.mkdir(parents=True,exist_ok=True);out=REPORTS/"Guncel_Stok_Raporu.pdf"
    with connect() as con: rows=[dict(r) for r in con.execute("SELECT * FROM vehicles WHERE status='STOCK' ORDER BY purchase_date,plate").fetchall()]
    cc=[stock_calc(r) for r in rows];st=_styles();story=_intro("Güncel Stok & SKS Raporu","Stok maliyeti, bekleme riski ve tahmini kârlılık")
    story += [_kpis([("Aktif stok",len(rows),"blue"),("Stok maliyeti",money(sum(c['total_cost'] for c in cc)),"blue"),("Tahmini kâr",money(sum(c['estimated_profit'] for c in cc)),"green"),("90+ kritik",sum(c['sks_days']>90 for c in cc),"red")]),Paragraph("Aktif Stok Detayı",st["RH"])]
    data=[["Plaka","Araç","Yıl","KM","Alış Tarihi","SKS","Alış","Satış","Sabit Gider","SKS Finansman","Maliyet","Tahmini Kâr"]]
    for r,c in zip(rows,cc):data.append([r["plate"],f"{r['brand']} {r['model']} {r['version']}".strip(),r["model_year"] or "",r["km"] or 0,r["purchase_date"],c["sks_days"],money(r["purchase_price"]),money(r["list_price"]),money(c["fixed_expense"]),money(c["sks_finance"]),money(c["total_cost"]),money(c["estimated_profit"])])
    story.append(_table(data,[55,135,30,45,60,28,60,60,62,70,65,65],11));_doc(out).build(story,onFirstPage=_footer,onLaterPages=_footer);return out

def purchase_report(month):
    REPORTS.mkdir(parents=True,exist_ok=True);out=REPORTS/f"Alim_Performans_{month}.pdf"
    with connect() as con: rows=[dict(r) for r in con.execute("SELECT * FROM vehicles WHERE substr(purchase_date,1,7)=? ORDER BY purchase_date,plate",(month,)).fetchall()]
    st=_styles();story=_intro("Aylık Alım Performans Raporu","Dönem içinde stoğa katılan araçların maliyet görünümü",month)
    story += [_kpis([("Alınan araç",len(rows),"blue"),("Alış değeri",money(sum(r['purchase_price'] for r in rows)),"blue"),("Liste satış",money(sum(r['list_price'] for r in rows)),"green"),("Ortalama alış",money(sum(r['purchase_price'] for r in rows)/len(rows) if rows else 0),"blue")]),Paragraph("Alım Detayı",st["RH"])]
    data=[["Tarih","Plaka","Marka","Model","Versiyon","Yıl","KM","Alım Türü","Alış","Liste Satış","Durum"]]
    for r in rows:data.append([r["purchase_date"],r["plate"],r["brand"],r["model"],r["version"],r["model_year"] or "",r["km"] or 0,r["purchase_type"],money(r["purchase_price"]),money(r["list_price"]),r["status"]])
    story.append(_table(data,[55,55,55,55,120,30,45,65,65,65,45]));_doc(out).build(story,onFirstPage=_footer,onLaterPages=_footer);return out

def consultant_report(month):
    REPORTS.mkdir(parents=True,exist_ok=True);out=REPORTS/f"Danisman_Performans_{month}.pdf"
    with connect() as con:
        consultants=[dict(r) for r in con.execute("SELECT * FROM consultants WHERE active=1 ORDER BY name").fetchall()]
        sales=[dict(r) for r in con.execute("SELECT * FROM sales WHERE substr(sale_date,1,7)=?",(month,)).fetchall()]
    st=_styles();perf_total=sum(sale_calc(x)['performance_profit'] for x in sales)
    story=_intro("Danışman Performans Raporu","Hedef, ciro, kâr ve stok bekleme performansı",month)
    story += [_kpis([("Aktif danışman",len(consultants),"blue"),("Toplam satış",len(sales),"blue"),("Toplam ciro",money(sum(x['sale_price'] for x in sales)),"blue"),("Performans kârı",money(perf_total),"green" if perf_total>=0 else "red")]),Paragraph("Danışman Karnesi",st["RH"])]
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
    st=_styles();done=sum(r['done_count'] for r in rows);converted=sum(r['converted_count'] for r in rows)
    story=_intro("Ekspertiz Takip Raporu","Personel bazlı aktivite, dönüşüm ve maliyet",month)
    story += [_kpis([("Personel",len(rows),"blue"),("Ekspertiz",done,"blue"),("Alıma dönüşen",converted,"green"),("Dönüşüm",f"%{converted/done*100:.1f}" if done else "%0","green")]),Paragraph("Personel Detayı",st["RH"])]
    data=[["Personel","Yapılan Ekspertiz","Alıma Dönüşen","Dönüşüm","Toplam Maliyet","Alım Başı Maliyet"]]
    for r in rows:
        cost=r["done_count"]*exp_cost
        data.append([r["consultant"],r["done_count"],r["converted_count"],f"%{(r['converted_count']/r['done_count']*100 if r['done_count'] else 0):.1f}",money(cost),money(cost/r["converted_count"] if r["converted_count"] else 0)])
    story.append(_table(data,[145,80,80,65,90,95]));_doc(out,False).build(story,onFirstPage=_footer,onLaterPages=_footer);return out

def profit_loss_report(month):
    REPORTS.mkdir(parents=True,exist_ok=True);out=REPORTS/f"Kar_Zarar_Analizi_{month}.pdf"
    with connect() as con: rows=[dict(r) for r in con.execute("SELECT * FROM sales WHERE substr(sale_date,1,7)=? ORDER BY sale_date,plate",(month,)).fetchall()]
    pairs=[(r,sale_calc(r)) for r in rows];pairs.sort(key=lambda x:x[1]["performance_profit"])
    st=_styles();perf=sum(c['performance_profit'] for _,c in pairs)
    story=_intro("Kâr / Zarar Analizi","Satışların performans kârına göre karşılaştırması",month)
    story += [_kpis([("Toplam satış",len(rows),"blue"),("Kârlı / başabaş",sum(c['performance_profit']>=0 for _,c in pairs),"green"),("Zararlı satış",sum(c['performance_profit']<0 for _,c in pairs),"red"),("Performans kârı",money(perf),"green" if perf>=0 else "red")]),Paragraph("Araç Bazlı Analiz",st["RH"])]
    data=[["Tarih","Plaka","Araç","Danışman","Alış","Gider","Maliyet","Satış","SKS","Net Kâr","Perf. Kâr"]]
    for r,c in pairs:data.append([r["sale_date"],r["plate"],r["vehicle_info"],r["consultant"],money(r["purchase_price"]),money(c["total_expense"]),money(c["total_cost"]),money(r["sale_price"]),c["sks_days"],money(c["net_profit"]),money(c["performance_profit"])])
    story.append(_table(data,[50,55,135,90,62,62,65,62,30,62,62],10));_doc(out).build(story,onFirstPage=_footer,onLaterPages=_footer);return out

def critical_stock_report():
    REPORTS.mkdir(parents=True,exist_ok=True);out=REPORTS/"Kritik_SKS_Stok_Raporu.pdf"
    with connect() as con: rows=[dict(r) for r in con.execute("SELECT * FROM vehicles WHERE status='STOCK' ORDER BY purchase_date").fetchall()]
    pairs=[(r,stock_calc(r)) for r in rows];pairs.sort(key=lambda x:x[1]["sks_days"],reverse=True)
    st=_styles();story=_intro("Kritik SKS / Stok Risk Raporu","0–30 normal • 31–60 takip • 61–90 aksiyon • 90+ kritik")
    story += [_kpis([("Normal",sum(c['sks_days']<=30 for _,c in pairs),"green"),("Takip",sum(30<c['sks_days']<=60 for _,c in pairs),"amber"),("Aksiyon",sum(60<c['sks_days']<=90 for _,c in pairs),"amber"),("Kritik",sum(c['sks_days']>90 for _,c in pairs),"red")]),Paragraph("Risk Sıralaması",st["RH"])]
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
    perf=sum(c["performance_profit"] for c in sc)
    story=_intro("Aylık Yönetici Tam Raporu","Satış, stok, kârlılık, SKS ve ekspertiz yönetim özeti",month)
    story += [_kpis([("Satış adedi",len(sales),"blue"),("Ciro",money(sum(r["sale_price"] for r in sales)),"blue"),("Performans kârı",money(perf),"green" if perf>=0 else "red"),("Güncel stok",len(stocks),"blue")]),_kpis([("Stok maliyeti",money(sum(c["total_cost"] for c in stc)),"blue"),("Tahmini stok kârı",money(sum(c["estimated_profit"] for c in stc)),"green"),("90+ kritik stok",sum(c["sks_days"]>90 for c in stc),"red"),("Ekspertiz / alım",f"{sum(r['done_count'] for r in exp)} / {sum(r['converted_count'] for r in exp)}","blue")]),Paragraph("Satış Detayı",st["RH"])]
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
    story=_intro("Aylık Araç Alım & Kaynak Raporu","Araç, kaynak personeli, alım türü ve maliyet takibi",month)
    story += [_kpis([("Toplam araç",len(rows),"blue"),("Alış toplamı",money(total),"blue"),("Masraf",money(exp),"amber"),("Toplam maliyet",money(total+exp),"blue")]),Paragraph("Alım Kaynak Detayı",st["RH"])]
    data=[["Tarih","Plaka","Araç","Alım Türü","Alınan Kişi","Alış","Masraf","Toplam"]]
    for r in rows:data.append([r["purchase_date"],r["plate"]," ".join(str(r.get(k) or "") for k in ("brand","model","version")).strip(),r["purchase_type"],r["acquired_by"],money(r["purchase_price"]),money(r["expense"]),money(r["purchase_price"]+r["expense"])])
    story.append(_table(data,[52,58,150,65,105,68,60,70]));doc=_doc(out,True);doc.build(story,onFirstPage=_footer,onLaterPages=_footer);return out

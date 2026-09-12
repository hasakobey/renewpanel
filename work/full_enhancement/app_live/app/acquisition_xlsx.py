from pathlib import Path
import xlsxwriter
from .db import connect, BASE

def export_acquisitions(month):
    with connect() as con:
        rows=[dict(r) for r in con.execute("SELECT * FROM acquisitions WHERE substr(purchase_date,1,7)=? ORDER BY purchase_date,id",(month,)).fetchall()]
    out=BASE/"reports"/f"AYLIK_ALIM_{month}.xlsx";out.parent.mkdir(exist_ok=True)
    wb=xlsxwriter.Workbook(out)
    ws=wb.add_worksheet("AYLIK ALIM TAKİBİ")
    title=wb.add_format({"bold":True,"font_color":"white","bg_color":"#173F6B","font_size":16,"align":"center","valign":"vcenter"})
    head=wb.add_format({"bold":True,"font_color":"white","bg_color":"#245A87","align":"center","valign":"vcenter","text_wrap":True,"border":1})
    body=wb.add_format({"border":1,"border_color":"#D8E1EA"})
    money=wb.add_format({"num_format":'#,##0 "TL"',"border":1,"border_color":"#D8E1EA"})
    ws.merge_range("A1:Q1","RENEW • AYLIK ARAÇ ALIM & KAYNAK TAKİBİ",title);ws.set_row(0,28)
    heads=["SIRA","ALIM TARİHİ","AY","PLAKA","MODEL YILI","KM","MARKA","MODEL","VERSİYON","RENK","YAKIT","VİTES","ALIM TÜRÜ","ALINAN KİŞİ / EKSPERTİZ PERSONELİ","ALIŞ FİYATI","MASRAF","TOPLAM ALIŞ MALİYETİ"]
    for c,h in enumerate(heads):ws.write(2,c,h,head)
    for i,r in enumerate(rows,1):
        vals=[i,r["purchase_date"],month,r["plate"],r["model_year"] or "",r["km"],r["brand"],r["model"],r["version"],r["color"],r["fuel"],r["transmission"],r["purchase_type"],r["acquired_by"],r["purchase_price"],r["expense"],r["purchase_price"]+r["expense"]]
        for c,v in enumerate(vals):ws.write(i+2,c,v,money if c>=14 else body)
    ws.freeze_panes(3,0);ws.autofilter(2,0,max(2,len(rows)+2),16)
    widths=[7,13,13,14,11,12,15,18,28,14,15,13,16,28,16,14,19]
    for c,w in enumerate(widths):ws.set_column(c,c,w)
    # Özet
    sm=wb.add_worksheet("AYLIK ÖZET")
    sm.merge_range("A1:F1",f"AYLIK ALIM YÖNETİM ÖZETİ • {month}",title)
    total=sum(r["purchase_price"] for r in rows);exp=sum(r["expense"] for r in rows)
    for rr,(k,v) in enumerate([("Toplam Araç",len(rows)),("Toplam Alış",total),("Toplam Masraf",exp),("Toplam Maliyet",total+exp)],2):
        sm.write(rr,0,k,head);sm.write(rr,1,v,money if rr>2 else body)
    by={}
    for r in rows:
        d=by.setdefault(r["acquired_by"],[0,0,0]);d[0]+=1;d[1]+=r["purchase_price"];d[2]+=r["expense"]
    sm.write_row(7,0,["ALINAN KİŞİ","ARAÇ","ALIŞ TOPLAMI","MASRAF","TOPLAM"],head)
    for rr,(name,v) in enumerate(sorted(by.items()),8):
        sm.write(rr,0,name,body);sm.write(rr,1,v[0],body);sm.write(rr,2,v[1],money);sm.write(rr,3,v[2],money);sm.write(rr,4,v[1]+v[2],money)
    sm.set_column("A:A",28);sm.set_column("B:E",18)
    wb.close();return out

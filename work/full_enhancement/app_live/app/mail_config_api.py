from pathlib import Path
import json
from fastapi import APIRouter, HTTPException
from .db import log

router=APIRouter(prefix="/api/mail-config",tags=["mail-config"])
BASE=Path(__file__).resolve().parents[1]
FILE=BASE/"data"/"mail_config.json"

DEFAULT={
 "templates":[
  {"id":"tahsilat","name":"Kredi Kartı Tahsilat Maili","module":"tahsilat","type":"Kredi Kartı Tahsilat","active":True,
   "subject":"Kredi Kartı Tahsilat Hk.",
   "to":"seval.avseven@cayan.com.tr;muhasebe@cayan.com.tr;tahsilatsorgu@cayan.com.tr",
   "cc":"emirhan.cayan.cayan@ys.renault.com.tr;denizhan.cayan.cayan@ys.renault.com.tr",
   "body":"Merhaba,\n\nAşağıda bilgileri bulunan müşterimizin kredi kartı tahsilat işlemi için desteğinizi rica ederim.\n\nMÜŞTERİ BİLGİLERİ\n\nAlıcı Adı Soyadı: {alici}\nT.C. Kimlik No: {tc}\nCep Telefonu: {cep}\n\nÖDEME BİLGİLERİ\n\nÇekilecek Tutar: {tutar}\nKredi Kartı Kullanımı: {kart_tipi}\n\nİlgili tutarın belirtilen kredi kartı/kartları üzerinden tahsilat işleminin gerçekleştirilmesini rica ederim.\n\nİyi çalışmalar."},
  {"id":"odeme","name":"Ödeme Bildirimi","module":"odeme","type":"Ödeme Bildirimi","active":True,
   "subject":"{isim} - {tutar} - {banka}",
   "to":"seval.avseven@cayan.com.tr;muhasebe@cayan.com.tr;tahsilatsorgu@cayan.com.tr",
   "cc":"emirhan.cayan.cayan@ys.renault.com.tr;denizhan.cayan.cayan@ys.renault.com.tr",
   "body":"Merhaba,\n\n{isim} isimli müşterimiz tarafından {banka} hesabımıza {tutar} tutarında ödeme gönderimi sağlanmıştır.\n\nKontrolünü sağlayabilir miyiz?\n\nİyi çalışmalar."},
  {"id":"sigorta","name":"Sigorta İptali","module":"sigorta","type":"Sigorta İptali","active":True,
   "subject":"{plaka} - Sigorta İptali Hk.","to":"muhasebe@cayan.com.tr;Sezen.Tanrisever@kocstellantissigorta.com.tr","cc":"",
   "body":"Merhaba,\n\n{plaka} plakalı aracın sigorta iptal işlemini gerçekleştirebilir misiniz?\n\nİyi çalışmalar,\nSaygılarımla."},
  {"id":"devir","name":"Devir İşlemi Maili","module":"devir","type":"Devir İşlemi","active":True,
   "subject":"Çayan Devir Hk.","to":"g.n.d@hotmail.com","cc":"",
   "body":"Merhaba,\n\nÇayan Otomotiv adına {yetkili} ({yetkili_unvan}) imza yetkilisidir.\nAraç bedeli {tutar}'dir.\nAraç {km}'dedir.\n{plaka_durumu}\n\nİyi çalışmalar."}
 ],
 "custom_vars":[],
 "authorities":[
  {"id":"ali","name":"Ali Çayan","title":"İmza Yetkilisi","phone":""},
  {"id":"emirhan","name":"Emirhan Çayan","title":"İmza Yetkilisi","phone":""},
  {"id":"denizhan","name":"Denizhan Çayan","title":"İmza Yetkilisi","phone":""},
  {"id":"onur","name":"Onur İpek","title":"Yetkili Personel","phone":""}
 ]
}

def normalize(d):
    base={x["id"]:x for x in DEFAULT["templates"]}
    if not isinstance(d,dict): d={}
    arr=d.get("templates",[])
    if not isinstance(arr,list): arr=[]
    found=set()
    for x in arr:
        if not isinstance(x,dict): continue
        xid=x.get("id","")
        if xid in base:
            x.setdefault("module",base[xid].get("module",xid))
            x.setdefault("type",base[xid].get("type",xid))
            x.setdefault("active",True)
            x.setdefault("subject",base[xid].get("subject",""))
            x.setdefault("to",base[xid].get("to",""))
            x.setdefault("cc",base[xid].get("cc",""))
            x.setdefault("body",base[xid].get("body",""))
            found.add(xid)
        else:
            x.setdefault("module","general");x.setdefault("type","Özel Şablon");x.setdefault("active",True)
    for xid,x in base.items():
        if xid not in found: arr.append(json.loads(json.dumps(x)))
    d["templates"]=arr
    if not isinstance(d.get("custom_vars"),list):d["custom_vars"]=[]
    if not isinstance(d.get("authorities"),list) or not d["authorities"]:d["authorities"]=json.loads(json.dumps(DEFAULT["authorities"]))
    return d

def load():
    if not FILE.exists():
        FILE.parent.mkdir(parents=True,exist_ok=True)
        FILE.write_text(json.dumps(DEFAULT,ensure_ascii=False,indent=2),encoding="utf-8")
        return json.loads(json.dumps(DEFAULT))
    try:
        d=normalize(json.loads(FILE.read_text(encoding="utf-8")))
        FILE.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8")
        return d
    except:
        return json.loads(json.dumps(DEFAULT))

def save(d):
    if not isinstance(d,dict):raise HTTPException(400,"Geçersiz mail yapılandırması.")
    templates=d.get("templates",[])
    authorities=d.get("authorities",[])
    if not isinstance(templates,list) or not templates:raise HTTPException(400,"En az bir mail şablonu bulunmalıdır.")
    if not isinstance(authorities,list) or not authorities:raise HTTPException(400,"En az bir devir yetkilisi bulunmalıdır.")
    clean=normalize({"templates":templates,"custom_vars":d.get("custom_vars",[]),"authorities":authorities})
    FILE.parent.mkdir(parents=True,exist_ok=True)
    FILE.write_text(json.dumps(clean,ensure_ascii=False,indent=2),encoding="utf-8")
    log("mail_config","global","UPDATE","Mail şablonları / yetkililer güncellendi")
    return clean

@router.get("")
def get_config():
    return load()

@router.put("")
def put_config(payload:dict):
    return save(payload)

@router.post("/reset")
def reset_config():
    FILE.parent.mkdir(parents=True,exist_ok=True)
    FILE.write_text(json.dumps(DEFAULT,ensure_ascii=False,indent=2),encoding="utf-8")
    log("mail_config","global","RESET","Mail ayarları varsayılana döndürüldü")
    return json.loads(json.dumps(DEFAULT))

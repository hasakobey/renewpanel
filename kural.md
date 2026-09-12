# KURAL.md — Değişmez Kurallar

Bu dosyaya **sadece kullanıcının söylediği** kurallar eklenir. Claude kendi
yorumuyla, kendi inisiyatifiyle buraya yeni bir kural EKLEMEZ. Bir kural
belirsizse veya eksikse, tahmin edilmez — kullanıcıya sorulur.

## 1. /biziz — kesinlikle karışılmaz

`renewpanel.xyz/biziz` alanına hiçbir koşulda, hiçbir gerekçeyle dokunulmaz.
Ayrı bir sistemdir, kendi Supabase bağlantısı vardır. Okuma, yazma, deploy,
"yanlışlıkla" da dahil — kesinlikle yok. Override yoktur.

## 2. RENEW PRO — Excel matematiği korunur

Kolon yapısı, sayfa adları, hücre biçimleri (tarih/para/yüzde), formüller ve
hesaplamalar değişmez. Başarı ölçütü:

```
Excel → uygulama → dışa aktarım → Excel'de düzenleme → tekrar içe aktarım
```

Bu döngüde değerler ve matematik birebir aynı kalmadan değişiklik tamamlanmış
sayılmaz. Formüller gereksiz yere sabit değere çevrilmez.

Referans şablonlar (üzerine yazılmaz, kopyası alınır):
`RENEW_MASTER_SABLON.xlsx`, `KULLANICI_ORIJINALI_DOKUNMA.xlsx`

Korumalı kod: `calc.py`, `xlsx_service.py`, `form_finance.py`

**Alım türü kuralı:** Şirket aracında noter ve sigorta gideri **kapalı**;
ekspertiz ve 150 nokta **açık**; SKS finansmanı alım kuralına göre. Doğru
olan uygulama tarafıdır (₺1.005.800). Excel formülü (₺1.010.902) fazladan
₺5.102 gider ekliyor — bu fark hâlâ açık bir iş, düzeltilene kadar Excel
tarafı referans alınmaz, uygulama tarafı doğru kabul edilir.

## 3. Parametreler (ALIM AYARLARI) merkezi korunur

Alım türü, noter/sigorta/ekspertiz/150 nokta gibi gider parametreleri
`Parametreler` (ALIM AYARLARI) merkezinden yönetilir. Proje büyüdükçe bu
merkez **kaldırılmaz** — yeni alanlar/parametreler bu merkeze eklenerek
genişletilir, dağınık/tekil sabit değerlerle değiştirilmez.

## 4. kart.renewpanel.xyz — matematik korunur

Taksit/faiz hesap mantığı (`renewKartTotals`, oran tablosu) değiştirilmez.
Doğrulanmış referans: 100.000 ₺ / 12 taksit → %32,98, ₺11.081,56. Görsel
değişiklikler bu hesaplamaya dokunmaz.

## 5. Excel'den web-native'e geçiş — ileride, aşamalı

Proje artık Excel'in birebir aynası olmak zorunda değil; hedef sistemi
resmileştirip profesyonelleştirmek. Excel'e dışa aktarım her zaman çalışmalı
olacak şekilde korunur. Kullanıcı ileride Excel tarafının korunma zorunluluğunu
tamamen kaldırıp sistemi tam web-native hale getirmeyi planlıyor — bu geçiş
kullanıcı açıkça talimat verdiğinde yapılır, kendiliğinden başlatılmaz.

---
name: canli-degisiklik
description: RENEW PRO veya kart.renewpanel.xyz üzerinde canlıya bir değişiklik uygulanacağı zaman kullanılır - yedek alma, tek kaynak dosyada düzenleme, SHA256 doğrulama, nginx/HTTPS kontrolü ve gerekirse geri dönüş sırasını yürütür. Kullanıcı "canlıya al", "siteye işle", "deploy et", "yedeğini al ve yap" dediğinde tetiklenir.
---

# Canlı değişiklik akışı

Bu akış atlanmaz. Her adımın sonucu kullanıcıya raporlanır.

## 1. Başlangıç durumunu belirle

Değiştirilecek dosyanın **canlı** hâlini oku. Yerel kopyanın güncel olduğunu
varsayma — `*_ops.py fetch` ile çek veya SFTP ile indir, SHA256'sını al.

```
certutil -hashfile <yerel_dosya> SHA256
```

Canlı dosya ile yerel kopya farklıysa **önce bunu kullanıcıya bildir**, sonra
devam et. Farkın sebebi çoğu zaman başka bir oturumda yapılmış değişikliktir.

## 2. Yedek al

Tarihli ve geri dönülebilir:

```
/opt/renewpro/backups/<is_adi>_<YYYYMMDD_HHMMSS>
```

Büyük paketlerde tek toplu yedek yeterli. Küçük görsel düzeltmelerde
(bir rengin koyulaştırılması, bir kartın kaldırılması) kullanıcı her seferinde
yedek istemiyor — yedek almadığını açıkça yaz.

Veritabanına dokunan işlemlerde `.db` yedeği **ayrıca** alınır.

## 3. Tek temiz kaynak dosyada düzenle

Canlı dosyaya yama ekleme. Yeni davranış gerekiyorsa:

- Mevcut bir `renew_*_v1.css/js` dosyasını güncelle, ya da
- Yeni bir isimli katman dosyası ekle ve `index.html`'e tek satır bağla

Aynı CSS seçicisini veya JS fonksiyonunu ikinci kez tanımlama — bu projede
tasarım kaymalarının bilinen sebebi budur.

## 4. Yerelde doğrula

- `.py` → sözdizimi kontrolü
- `.js` → `node --check`
- `.html` → `<script>` / `<style>` açılış-kapanış sayıları eşit mi
- Excel'e dokunulduysa: içe/dışa aktarım döngüsü ve formül taraması

Hook'lar bunların bir kısmını otomatik yapar; başarısızsa düzelt, devam etme.

## 5. Aktar

Geçici dosya + atomik yeniden adlandırma kullan (`.new` → `posix_rename`),
izinleri `0644` yap. Aktarımdan sonra yerel ↔ canlı SHA256 karşılaştır.

## 6. Kontrol et

Sırayla, hepsi geçmeli:

- `nginx -t` → başarılı
- `systemctl is-active renewpro.service` → active
- HTTPS ana sayfa → 200, HTTP → 301
- Değişen CSS/JS dosyaları → 200
- Tarayıcı konsolunda yeni hata/uyarı yok
- `/biziz` → 200 ve etkilenmemiş

## 7. Başarısızsa

Hemen son sağlam yedeğe dön, dönüşü doğrula, sonra kullanıcıya neyin
başarısız olduğunu ve mevcut durumu yaz. Yarım bırakma.

## Rapor formatı

Kullanıcıya şu başlıklarla dön:

```
Yapılanlar:      (madde madde)
Korunanlar:      (Excel, matematik, /biziz, veri)
Kontroller:      (nginx, servis, HTTPS, hash, konsol)
Yedek:           (tam yol)
```

Sonunda "Ctrl + F5 ile yenileyebilirsin" hatırlatmasını ekle.

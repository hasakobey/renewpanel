# RENEW PRO — Proje Kılavuzu

Bu klasör, canlı sistemlerin yerel çalışma kopyası ve dağıtım (deploy) scriptlerini içerir.

## Sistemler

| | RENEW PRO | Kart Paneli | /biziz |
|---|---|---|---|
| Adres | renewpanel.xyz | kart.renewpanel.xyz | renewpanel.xyz/biziz |
| Teknoloji | FastAPI + Uvicorn, SQLite | Tek dosya statik HTML | Ayrı sistem, Supabase |
| Canlı yol | `/opt/renewpro/app_live` | `/var/www/kart.renewpanel.xyz/index.html` | — |
| Veritabanı | `/var/lib/renewpro/data/renew.db` | — | — |
| Servis | `renewpro.service` → 127.0.0.1:8765 | Nginx statik | — |
| Sunucu | 45.195.231.20 (tek sunucu, hepsi burada) | | |

## Değişmez kurallar

**[kural.md](kural.md) bu dosyanın üzerinde önceliklidir** — sadece kullanıcının
söylediği kurallar orada durur, Claude kendi inisiyatifiyle ekleme yapmaz.
Çelişki olursa kural.md geçerlidir.


1. **`/biziz` alanına hiçbir koşulda dokunulmaz.** Ayrı bir sistemdir, kendi
   Supabase bağlantısı vardır. Hook bunu zorla engeller, override yoktur.

2. **Excel matematiği korunur.** Kolon yapısı, sayfa adları, hücre biçimleri
   (tarih/para/yüzde), formüller ve hesaplar değişmez. Başarı ölçütü:

   ```
   Excel → uygulama → dışa aktarım → Excel'de düzenleme → tekrar içe aktarım
   ```

   Bu döngüde değerler ve matematik birebir aynı kalmadan değişiklik
   tamamlanmış sayılmaz. Formüller gereksiz yere sabit değere çevrilmez.

   Referans şablonlar: `RENEW_MASTER_SABLON.xlsx`,
   `KULLANICI_ORIJINALI_DOKUNMA.xlsx` — üzerine yazılmaz, kopyası alınır.

   Korumalı kod: `calc.py`, `xlsx_service.py`, `form_finance.py`.

3. **Alım türü kuralı.** Şirket aracında noter ve sigorta gideri **kapalı**;
   ekspertiz ve 150 nokta **açık**; SKS finansmanı alım kuralına göre.
   Doğru olan uygulama tarafıdır (₺1.005.800). Excel formülü (₺1.010.902)
   fazladan ₺5.102 gider ekliyor — `EXTRA STOK BİLGİSİ` sayfasındaki sabit
   gider formülü alım türüne bağlanarak düzeltilmeli. **Bu iş hâlâ açık.**

4. **Dönem mantığı.** Güncel stok aylara devreder. Satış, aylık alım,
   ekspertiz ve danışman performansı aya özeldir; yeni ay boş başlar.
   Geçmiş ay salt okunurdur, geçmiş silinmez. Yıllık analiz tüm ayları kapsar.
   Ekim'de aktarım yapılmazsa Eylül stoğu aynen devreder.

5. **Canlıya patch biriktirilmez.** Geçmişte tasarım kaymalarının ana sebebi
   canlı dosyaya arka arkaya eklenen `RENEW_*` yamaları, aynı CSS seçicilerinin
   ve JS fonksiyonlarının defalarca tanımlanmasıydı. Düzenleme tek temiz kaynak
   dosyada yapılır, doğrulanır, sonra aktarılır.

6. **Sırlar koda yazılmaz.** `.env` veya ortam değişkeni kullanılır.

## Canlı değişiklik akışı

Her canlı işlem bu sırayı izler — adım atlanmaz:

1. Mevcut canlı dosyayı ve yapılandırmayı **oku**, gerçek başlangıç durumunu belirle
2. **Tarihli yedek al** (`/opt/renewpro/backups/...`)
3. Değişikliği **tek temiz kaynak dosyada** yap
4. **Yerel ↔ canlı SHA256** karşılaştır
5. `nginx -t` → başarılı olmalı
6. Servis durumu (`renewpro.service` aktif), **HTTPS 200**, HTTP→HTTPS 301
7. Tarayıcı konsolunda hata/uyarı yok
8. Başarısızsa **son sağlam yedeğe dön**

Küçük görsel düzeltmelerde her seferinde yeni yedek alınmaz (kullanıcı isteği);
büyük paketlerde tek toplu yedek alınır.

## Klasör yapısı

```
work/
  live_ai/            # RENEW PRO ana uygulama çalışma kopyası (app/, app/static/)
  live_current/       # canlıdan çekilen güncel kopya
  reference_release/  # before/ + static/  → frontend release aşaması
  kart*/              # kart.renewpanel.xyz çalışmaları (kart_v4 en güncel)
  nginx/              # nginx yapılandırma kopyası
  *_ops.py            # SSH/SFTP dağıtım scriptleri (fetch / backup / stage / deploy)
  deploy_*.py         # tek seferlik dağıtım scriptleri
output/, outputs/     # üretilen PDF/Excel çıktıları
tmp/                  # geçici test scriptleri
```

`*_ops.py` dosyaları `video_v2_ops.py` içindeki `ssh()` fonksiyonunu ortak
kullanır; bağlantı bilgileri `deploy_video_studio.py` içinden AST ile okunur.

## Modül durumu

**Aktif:** Dashboard (Glass Wave KPI + 6 bölüm ayracı), Profilim, Güncel Stok,
Satılan Araçlar, Aylık Alımlar, Araç Fotoğrafları (1–25 slot stüdyo),
Bildirim Merkezi (Firebase push), PDF Rapor Merkezi (9 tür), Excel Merkezi,
Ctrl+K global arama, gece 03:15 otomatik yedek.

**Pasif ama silinmedi:** Araç 360° (menüde PASİF görünür).

**Kaldırıldı:** Ödeme Merkezi, Mail Şablonları, AI İlan Asistanı.

## Yedekler

**Tam sistem yedeği — 11.09.2026:**
- Sunucu: `/root/RENEW_FULL_BACKUP_20260911_101129` (168 MB, 6 arşiv + SHA256SUMS, tümü doğrulandı)
- Yerel: `backups/RENEW_FULL_BACKUP_20260911_101129` (kod + db + nginx + systemd + kart; `vehicle_media` sadece sunucuda)
- DB `PRAGMA integrity_check`: ok (hem canlı hem yedek)

**Kart düzeltmesi öncesi:** `/root/KART_BEFORE_DCL_FIX_20260911_104116`

**Karantina (adım 2, taşındı — silinmedi):** `/root/QUARANTINE_20260911_122701`
- RENEW PRO: 6 adet `.bak_*` dosyası (kod referansı yoktu, 404 doğrulandı)
- kart sitesi: `/demo/`, `/backups/` (nginx `try_files` SPA fallback devam ediyor, sorun değil)

## Yapılan çalışmalar

### 11.09.2026 — kart.renewpanel.xyz "yenileyince eski tasarım" düzeltmesi

**Kök neden:** `renew-stitch-v1.css`'in 185 kuralı `body.rst-v1` sınıfına bağlı; bu
sınıfı ekleyen `init()` ise `window.load`'da çalışıyordu. `load` sayfanın en son
olayı olduğu için (canlı ölçüm: DCL 535 ms → load 841 ms, gecikmenin kaynağı
821 ms'lik Google Fonts isteği) arada **306 ms boyunca eski düzen boyanıyordu.**

**Çözüm:** 4 script'in tetiği `window.load` → `DOMContentLoaded`. Ayrıca `?v=`
sürümleri artırıldı ve 404 veren `renew.ico` `<link>` etiketi kaldırıldı.
Toplam 11 satır değişti. Hesaplama koduna, oran tablosuna, `renewKartTotals`'a
dokunulmadı — canlıda doğrulandı (100.000 ₺ / 12 taksit → %32,98, ₺11.081,56).

**Sonuç:** tasarım 325 ms yerine 164 ms'de uygulanıyor, konsol hatası 0.

**Bu işte öğrenilenler — tekrar etme:**
- `<script>` etiketlerini saymak HTML bütünlüğü ölçmez; JS template literal'i
  içindeki `<script>` metni etiket değildir. Ayrıştırıcı gibi ilerle: her
  açılıştan sonra ilk `</script>`'e atla. (`work/claude_html_validate.py`)
- `requestAnimationFrame` gizli/arka plan sekmesinde çalışmaz. Sayfa kurulum
  kodunu rAF'a bağlama.
- `defer` script'ler `readyState='interactive'` ile çalışır. `'loading'`
  kontrolü yaparsan hemen çalışırlar ve satır-içi `DOMContentLoaded`
  kurucularından ÖNCE devreye girerler. `'complete'` kontrolü kullan.
- Tarayıcı konsol tamponu gezinmeler arası taşınabiliyor. Hata var mı diye
  bakarken sayfa-başı `window.addEventListener('error', ...)` yakalayıcısı
  kullan; konsol dökümüne güvenme.

## Araçlar (work/claude_*.py)

| Betik | İş |
|---|---|
| `claude_conn.py` | Ortak SSH; önce env değişkenleri, yoksa eski dosya |
| `claude_inventory.py` | Salt okunur canlı envanter |
| `claude_backup.py` | Tam sistem yedeği + doğrulama |
| `claude_pull_backup.py` | Yedeği yerele indirip hash karşılaştırma |
| `claude_analyze.py` | Ölü dosya / tekrar / bütünlük analizi |
| `claude_html_validate.py` | Ayrıştırıcı-doğru script/style + JS sözdizimi kontrolü |
| `claude_kart_*.py` | Kart sitesi: fetch / stage / patch / verify / A-B / deploy |

## Açık işler

**Sıradaki — temizlik adım 2 (onaylandı, sonraya bırakıldı):**
Halka açık dosyaları karantinaya taşı. Aşağıdakiler giriş yapmadan 200 dönüyor:
```
https://renewpanel.xyz/static/app.js.bak_20260902_155437        (146 KB eski kod)
https://renewpanel.xyz/static/index.html.bak_20260902_155437
https://renewpanel.xyz/static/renew_forms_v1.css.bak_20260902_155437
https://renewpanel.xyz/static/payment_center.html               (kaldırılmış modül)
https://renewpanel.xyz/static/payment_hub.html
https://kart.renewpanel.xyz/demo/
```

**Temizlik adım 3–4:**
- 12 referanssız statik dosyayı arşivle (370 KB): `dashboard_reference_v3.*`,
  `renew_dashboard_stitch.*`, `renew_ui_stitch_v2.*`, firebase compat dosyaları
- 60 adet 4+ kez tanımlı CSS seçicisi ve 39 adet çift tanımlı JS fonksiyonunu
  birleştir (`app.js` 156 KB tek parça; `updateMailTemplateDraft` 3 kez)
- Kart sitesi: 100 KB satır-içi CSS'i (18 blok) ve 52 KB satır-içi JS'i (6 blok)
  harici dosyalara ayır; referanssız `renew-kart-512.png` + `renew-kart-icon.png`

**Ürün işleri:**
- Araç 360° sistemini yeniden aktifleştir (pasif, silinmedi)
- Stitch yenileme paketlerini değerlendir (kullanıcı ayrıca iletecek)
- Excel `EXTRA STOK BİLGİSİ` sabit gider formülü düzeltmesi (₺5.102 farkı)
- 2026 verisinin eski sistemden aktarımı (önce test ortamı + mutabakat raporu)
- Excel içe aktarım fark/onay ekranı (yeni / değişen / çakışan kayıt)
- Yıllık analiz ekranı (Ocak–Aralık karşılaştırma)
- Yedekten dönüş provası (yedek almak yetmez, geri yükleme test edilmeli)
- Gerçek cihaz kabul testi (iPhone / Android / tablet)
- Araç fotoğrafları eksik (stok araçlarının aktif klasörleri boş)

**Kullanıcının ayrıca istediği yön:** proje artık Excel'in birebir aynası olmak
zorunda değil, ama **Excel'e dışa aktarım her zaman çalışmalı.** Amaç sistemi
resmileştirip profesyonelleştirmek.

**Bekleyen inceleme:** `diegosouzapw/OmniRoute` (AI gateway) raporu,
`rebelytics/one-skill-to-rule-them-all` incelemesi.

### 11.09.2026 — payment-center hayaleti kaldırıldı (adım 2 devamı, canlıda)

Menüden kaldırılmış "Ödeme Merkezi" bölümü CSS'te `display:none!important`
ile gizliydi ama `<iframe src="payment_center.html">` CSS'ten bağımsız olarak
her sayfa yüklemesinde arka planda çalışıyordu → `/api/mail-config`'e 401
(haftada 109 istek, log kirliliği). Doğrulama: 20 sayfadan yalnızca
`payment-center` ve `mail-templates` nav'dan erişilemiyordu; CSS'te
`!important` ID seçici `.page.active` kuralını her koşulda eziyor, hash/route
ile de açılamıyordu (router grep boş döndü).

**Kaldırılan (temiz, izole):**
- `index.html`: `<section id="payment-center">` (iframe dahil)
- `app.js`: `reloadPaymentCenter`, `openPaymentCenterNewTab`,
  `syncPaymentFrameHeight` + 2 event listener, V7.24 `page()` router yaması
  (`_pageV724` monkey-patch)
- `style.css`: 15 adet V7.20/V7.22 yama kuralı (`.payment-center-shell`,
  `#paymentCenterFrame`)
- `renew_dashboard_v26.css`: `#payment-center,#mail-templates` → `#mail-templates`
- Orphan dosyalar karantinaya: `payment_center.html`, `payment_hub.html`
  (`/root/QUARANTINE_20260911_123913`)

**Bilerek DOKUNULMAYAN:** `saveMailTemplates()`/`saveMailTemplatesV725()`
içindeki `document.getElementById('paymentCenterFrame')` + `postMessage`
çağrıları (4 yer) — `if(f)` korumalı, frame yok olunca sessizce no-op olur,
hata vermez. Mail-templates modülüne müdahale değil.

**Yedek:** `/opt/renewpro/backups/paymentcenter_removal_20260911_123913`
**Canlı doğrulama:** `paymentCenterFrame`/`payment-center` DOM'da yok,
`mail-templates` korunuyor, konsol hatası 0.

**mail-templates modülü kaldırılmadı — ayrı, daha büyük iş:** 3 nesil kopya
kod (`loadMailTemplates` / `loadMailTemplatesV725`, `saveMailTemplates` /
`saveMailTemplatesV725`), 15+ iç içe fonksiyon, `authorityPeople` (Devir
yetkilileri) verisi. UI'dan erişilemez durumda ama kod hacmi büyük;
kendi başına bir temizlik oturumu gerektirir. **Kullanıcı onayı olmadan
dokunma.**

**Bu turda tekrar eden ders:** Bir özelliği "menüden kaldırıldı" diye ölü
sanma — arka plan işleri (iframe `src`, `DOMContentLoaded` auto-load,
router monkey-patch'leri) CSS/nav görünürlüğünden bağımsız çalışabilir.
Kaldırmadan önce: (1) nav/route ile gerçekten erişilemez mi doğrula,
(2) fonksiyon adını TÜM varyasyonlarıyla (`sync*`, `open*`, `reload*`)
tara — ilk taramada 2 fonksiyon bulundum, tam tarama 7 kalıntı çıkardı,
(3) deploy kontrol scriptinde `/biziz/` her zaman 308 döner, bunu hata
sanıp gereksiz rollback yapma (bu turda bir kez oldu, düzeltildi).

### 11.09.2026 — Giriş ekranı auth-switch tasarımına geçirildi (canlıda)

21st.dev "Auth Switch" bileşeninin diyagonal dalga panolu, sekmeli görsel
diline uyarlandı (React/Tailwind yok, elle vanilla HTML/CSS/JS). İki panel:
"Personel Girişi" (gerçek form, varsayılan aktif) ve "Kart İşlemleri"
(kredi kartı temalı tanıtım kartı → kart.renewpanel.xyz yeni sekmede açılır,
davranış aynı, sadece görsel). Dalga efekti `clip-path:polygon()` ile.

**Yeni dosyalar:** `renew_login_switch_v1.css`, `renew_login_switch_v1.js`
(sadece sekme geçişini yönetir, `#loginForm.onsubmit`'e dokunmaz).
**index.html:** `#loginOverlay` içeriği yeniden yapılandırıldı, dış ID'ler
(`loginOverlay/loginForm/loginUsername/loginPassword/loginMessage`) korundu.
**app.js:** kesin ölü ilk `$('#loginForm').onsubmit=...` bloğu silindi
(satır ~1077); ikinci/aktif blok (~1185) ve `user_admin_v2.js`'e dokunulmadı.

**Yedek:** `/opt/renewpro/backups/login_redesign_20260911_144927`

**Canlıda doğrulandı:** masaüstü + mobil (375px) görsel, sekme geçiş
animasyonu, klavye ok tuşu gezintisi, kart linkinin yeni sekmede açılması,
yanlış şifreyle gerçek `/api/auth/login` çağrısı → doğru hata mesajı
("Kalan deneme: 4") → overlay açık kalıyor. Konsol hatası yok (401'ler
girişten önce API korumasının normal davranışı, önceden de vardı).

**Görsel iyileştirme turu 1 (aynı gün):** İlk sürüm (üstte sekme çubuğu) beğenilmedi.
Eklendi: kredi kartı mockup'ı, dalga bandına renk kayması, mavi geçiş efekti
(`MutationObserver` ile mevcut auth koduna dokunmadan).

**Görsel iyileştirme turu 2 — TAM YENİDEN YAPILANDIRMA:** Kullanıcı referans
görseli paylaştı: 21st.dev "Auth Switch" aslında SEKME DEĞİL, yan yana ikiye
bölünmüş panel (sol: eğri kesimli renkli panel, sağ: beyaz form), masaüstünde
`display:grid;grid-template-columns:1fr 1.15fr`, mobilde (≤640px) alt alta
yığılıyor (`clip-path:polygon()` eğri her ikisinde de farklı açıyla). Tab
yapısı (`role=tablist` vb.) tamamen kaldırıldı — artık iki panel HER ZAMAN
aynı anda görünür: sol = kart mockup + "Kart İşlemleri" + CTA (dış link),
sağ = gerçek giriş formu. Onay tiki rengi sarı daire + BEYAZ tik (önceki
navy tikti, kullanıcı marka renklerine uymadığını belirtti, düzeltildi).

`renew_login_switch_v1.css/js` içinde, `/opt/renewpro/backups/login_polish_*`
yedekleri var, hepsi hash doğrulamalı dağıtıldı. Canlıda 1200px ve 650px
genişlikte ekran görüntüsüyle doğrulandı — masaüstünde yan yana, mobilde
alt alta doğru render ediyor.

**Görsel iyileştirme turu 3 — kredi kartı mockup'ı kaldırıldı:** Kullanıcı
kart mockup'ını istemedi ("kafana göre ekleme yapma"), referans görsele
sadık kalınması istendi. `.renew-visa-card` bloğu tamamen kaldırıldı. Sol
panel artık sadece başlık+açıklama+pil CTA (referanstaki "New here?" bloğu
gibi). Sağ paneldeki `<label>Metin<input></label>` yapısı, referanstaki
ikonlu pil input tasarımına çevrildi: `<label class="renew-pill-field">`
içinde emoji ikon + `placeholder` (görünür etiket metni kaldırıldı, id/name/
required/autocomplete DEĞİŞMEDİ). `.btn.primary` global class'ına DOKUNULMADI
— pil şekli sadece `.renew-split-white form .btn.primary` scope'unda, sitenin
başka yerindeki butonları etkilemiyor. Canlıda 1200px'de doğrulandı.

**Görsel iyileştirme turu 4 — önbellek + logo düzeltmesi:** Kullanıcının
telefonunda düz/kaymalı bir görünüm çıktı; sebep büyük ihtimalle
`renew_login_switch_v1.css/js?v=1.0.0-1` sürüm dizesinin HİÇ artırılmamış
olması (4 dağıtım boyunca aynı `?v=`, tarayıcı eski sürümü önbellekten
gösterebilir). `?v=1.0.4-1` yapıldı. Ayrıca kullanıcı "sarı detay kötü, eski
logo olsun" dedi: `.login-logo` için eklediğim sarı-arkaplan/navy-yazı
override'ı tamamen kaldırıldı — orijinal `style.css` kuralı (`background:
#173f6b` lacivert kare, beyaz "R") kendiliğinden geri geldi, hiç dokunulmadı.
**Ders:** Statik varlık dosyalarında `?v=` sürümünü HER dağıtımda artır,
sabit bırakma.

**Görsel iyileştirme turu 5 — renk birliği:** Kullanıcı "renkleri sevmedim,
aynı olsun" dedi. Kendi uydurduğum token'lar (`--renew-navy/--renew-blue`
karışımı + hareketli gradyan animasyonu) kaldırıldı; sol panel artık giriş
ekranının ZATEN var olan orijinal gradyanını kullanıyor:
`linear-gradient(135deg,#0f1c2e,#173f6b)` — `style.css` içindeki
`.login-overlay` ile birebir aynı. Mavi geçiş efekti de aynı iki renge
sabitlendi. Başarı tiki sarıdan, sitenin zaten "başarı" için kullandığı
yeşile (`--green:#16a34a`) çevrildi. `renewWaveShift` keyframe'i artık
kullanılmadığı için silindi. `?v=1.0.5-1`.
**Kural:** Bu projede yeni renk uydurma — mevcut `style.css` / `:root`
token'larından veya o ekranda hâlihazırda kullanılan tam hex değerinden al.

**Görsel iyileştirme turu 6 — CSS özgüllük hatası (ÖNEMLİ DERS):** Input
alanları şerit gibi değil, ikon üstte/yazı altta yığılmış görünüyordu. Sebep:
`style.css` içindeki **`.login-card label{display:grid;gap:5px}`**
(özgüllük 0,1,1) benim tek class'lı `.renew-pill-field{display:flex}`
kuralımı (0,1,0) eziyordu. Çözüm: tüm pill kuralları `.login-card` ile
prefixlenip 0,2,x'e çıkarıldı. Ayrıca yazılar kalınlaştırıldı (`font-weight:700`,
placeholder dahil), köşeler yumuşatıldı (kart 28px, input/buton 14px).
`?v=1.0.6-1`.
**Kural:** Bu projede `style.css` çok sayıda `.login-card label`,
`.card .btn` gibi **element+class kombinasyonu** içeriyor. Yeni bir katman
dosyasında tek class'lı kural yazarken önce `getComputedStyle` ile gerçekten
uygulanıp uygulanmadığını DOĞRULA — ekran görüntüsüne bakıp "olmuş" sanma.

**Onemli teknik ders — bu oturumda 2. kez:** `requestAnimationFrame` bu tarayıcı
test ortamında (Claude Browser preview paneli gizliyken) hiç çalışmıyor —
kart.renewpanel.xyz düzeltmesinde de aynı sorun çıkmıştı. Geçiş tetikleyicileri
için rAF yerine `setTimeout` kullan. Ayrıca: **panel gizliyken CSS `transition`
(hem `clip-path` hem `transform`) hiç interpolasyon yapmıyor** — izole testle
doğrulandı, bu ortam kısıtı, gerçek tarayıcılarda sorun değil. Görsel/animasyon
doğrulaması gerektiğinde önce `tabs_context` ile panelin gizli olup olmadığını
kontrol et; gizliyse ekran görüntüsüne güvenme, JS tarafından ölçülebilir
durumları (`classList`, `computedStyle` zaman damgalı) kontrol et.

### 12.09.2026 — Dashboard "Precision Automotive" redesign (canlıda)

Kullanıcı stitch referans tasarım (DESIGN.md + örnek HTML) verdi, "birebir
aynı görünsün, içerik/veri değişmesin" istedi. `renew_dashboard_stitch_v2.css/js`
— SADECE `#dashboard`, sol menüye dokunulmadı.

**Yöntem:** Var olan render fonksiyonları (`kpis()`, `renderDashboard()`,
`renderRenewAlerts()`, `renderDashAcquisitions()`) ZİNCİRLENDİ — orijinal
veri/hesap kodu hiç değişmedi, sadece DOM son haliyle yeniden biçimlendirildi.
KPI'lar 2 gruba ayrıldı + SVG ikon, "Dikkat Gerektirenler"/Dönem Karşılaştırma/
Risk dağılımı/Kâr-Zarar/mini satış listeleri/Alınan Araçlar/Ekspertiz özeti
hepsi bu şekilde yeniden kuruldu. Renkler sadece DESIGN.md'dekiler (yeni renk
uydurulmadı). Fontlar (Inter+Space Grotesk) CSP (`style-src 'self'`) yüzünden
Google Fonts'tan çekilemedi — yerelde barındırıldı (`static/fonts/`).

**ÖNEMLİ DERS — eski `#id>*` / `#id>*:nth-child()` kalıntıları:**
`dashboard_pro_v3.css` ve `renew_dashboard_polish_v1.css` içinde `#dashKpis>*`,
`#risk>*:nth-child(1..4)`, `#monthCompare>*`, `#profitSplit>*:first-child/
:last-child` gibi ID+evrensel-seçici kuralları, ESKİ düz yapıya (örn. `#risk`
içinde doğrudan 4 kutu) göre yazılmıştı. Yeni DOM'da aynı pozisyondaki
elemanlar (örn. yeni `.pa-risk-bar` `#risk`'in 1. çocuğu) bu kuralları
FARKINDA OLMADAN miras alıyor (min-height, background, border-color, hatta
tamamen farklı bir rengi zorluyor). Çözüm: konteyneri değiştiren her JS
DOM-yeniden-yapılandırmasından sonra, o konteynerin ID'siyle `grep` yapıp
`#id>*` / `#id>*:nth-child` / `#id .split` gibi kalıntı kuralları bul, ID
içeren eşit/daha yüksek özgüllükte sıfırlama yaz. Sadece `!important` eklemek
yetmez — **aynı özgüllükte iki `!important` çakışırsa özgüllük kazanır**,
kaynak sırası değil (bu oturumda 2. kez öğrenilen spesifik ders: `height` ile
`min-height` de ayrı kısıtlardır, height'ı ezmek min-height'ı sıfırlamaz).

**Not — bulgu, kapsam dışı bırakıldı:** `user_admin_v2.js` da `#loginForm`'a
kendi `loginSubmit`'ini atıyor (`DOMContentLoaded`+`setTimeout` ile, app.js'in
senkron atamalarından sonra) — fiilen çalışan handler bu olabilir. ID
sözleşmesi aynı olduğu için yeni tasarımı etkilemiyor, davranış test edildi
ve doğru çalışıyor. İleride ayrı bir temizlik konusu olabilir.

### 12.09.2026 — Dashboard ince ayar turu (animasyon/boşluk/ikon/plaka)

Kullanıcı geri bildirimi: animasyonlar karmaşık, boşluklar fazla, "SKS
Finansman" KPI'ının üstünde fazladan bir ikon var, plaka görünümü
beğenildi → dashboard'da her yere uygulanmalı.

- 10 bloklu staggered giriş animasyonu tek `rdsFadeIn` (opacity-only) ile
  değiştirildi; kart/KPI hover'larındaki `translateY` kaldırıldı (sadece
  gölge/border geçişi kaldı).
- Kart/KPI/alert/compare/mini-satır dolgu ve gap değerleri ~%20-30 azaltıldı.
- **Kök neden bulundu:** `dashboard_pro_v3.js`'teki eski `decorateKpis()`
  fonksiyonu, KPI'ları YENİDEN gruplandırdığımız için artık `#dashKpis`'in
  doğrudan çocuğu olan 2 `.kpi-group` sarmalayıcıyı "tekil KPI kartı" sanıp
  emoji ikon + renk sınıfı basıyordu. Bu dosya kapalı IIFE olduğu için
  düzeltilemiyor — `renew_dashboard_stitch_v2.js`'e `cleanupLegacyKpiDecoration()`
  eklendi, hem senkron hem `setTimeout(...,0)` ile (script-yükleme-sırası
  nedeniyle `dashboard_pro_v3.js`'in `DOMContentLoaded`'a ertelenmiş sarma
  işlemi benim render'ımdan SONRA çalışabiliyor) çağrılıyor.
- `.pa-mini-plate` → `.pa-plate` olarak birleştirildi, mini satış listeleri +
  Kritik SKS tablosu + Bu Ay Alınan Araçlar kartlarının hepsinde aynı rozet.

### 12.09.2026 — Stok/Satış/Aylık Alım formları "Precision Automotive" + Canlı Finansal Analiz (canlıda)

Kullanıcı yeni stitch referansı verdi (form modalı + canlı finansal analiz
paneli, ayrıca mobil form). `renew_forms_stitch_v1.css/js` eklendi —
`openStock/openSale/openSell` (zaten `renew_forms_v1.js` tarafından
sarmalanmış) ZİNCİRE bir kez daha eklendi, `openAcquisition` (V7.10, kendi
bağımsız kod yolu) sadece CSS ile restyle edildi. Alan id/name, submit/API
akışı hiç değişmedi.

**Canlı Finansal Analiz paneli** (Stok ve Satış formlarına eklendi):
hesap `calc.py`'deki `stock_calc`/`sale_calc` ile **birebir aynı formülü**
JS'de tekrar eder (Ayarlar merkezindeki `notary_expense/expertise_expense/
control150_expense/insurance_expense/sks_monthly_rate` + `purchase_rules`
üzerinden, ek backend isteği yok — sadece submit anında zaten var olan
`/api/sales/preview` ayrı kalır). ŞİRKET ARACI seçilince noter+sigorta
muafiyeti canlı düşüyor; test değeri kural.md'deki ₺5.102 farkla birebir
eşleşti. Aylık Alım formunda gerçek sistemde zaten olmayan bir "kâr" hesabı
İCAT EDİLMEDİ — orada hâlâ sadece "alış + ek masraf" toplamı var (doğrusu bu).

**Bug 1 — `window.SETTINGS` her zaman `undefined`:** `app.js` üst seviyede
`let SETTINGS={}` ile tanımlanıyor; ES modülü olmayan `<script>` içinde üst
seviye `let`/`const` **`window` nesnesine eklenmez** (yalnızca `var` eklenir).
`window.SETTINGS && SETTINGS.rules` gibi bir koruma bu yüzden sessizce boş
döner. Aynı dosyadaki diğer script'ler (`renew_dashboard_stitch_v2.js` dahil)
`SETTINGS`'e ÇIPLAK identifier olarak erişiyor (global lexical scope, farklı
`<script>` etiketleri arasında paylaşılıyor) — yeni kodda da `window.X`
değil, `typeof X!=='undefined' && X...` kalıbı kullanılmalı.

**Bug 2 — `<aside>` etiketi `style.css`'teki global sidebar seçicisiyle
çakıştı:** Finans panelini `<aside class="pa-finance-panel">` olarak
oluşturdum; `style.css`'te bare `aside{background:linear-gradient(...);
height:100vh;position:sticky}` (sol menü için yazılmış) tüm `<aside>`
elemanlarını hedefliyor, class'tan bağımsız olarak devreye giriyor. Panel
lacivert/sidebar gibi göründü. **Ders:** Yeni bir eleman oluştururken
semantik HTML etiketi (`aside/header/nav/main` vb.) yerine `<div>` tercih
et, ya da önce `style.css`'te o bare etiket için global bir kural olup
olmadığını grep'le — özellikle bu proje sol menüyü `<aside>` ile kurmuş.

### 12.09.2026 — karpathy-guidelines skill eklendi

Kullanıcı `multica-ai/andrej-karpathy-skills` reposunu paylaştı, proje
skill'i olarak kaydedilmesini istedi. `skills/karpathy-guidelines/SKILL.md`
içeriği `.claude/skills/karpathy-guidelines/SKILL.md`'ye taşındı (proje
skill dizini standardı). Davranış rehberi: düşün-önce-kodla, sadelik,
cerrahi değişiklik, hedef-odaklı doğrulama. Canlı uygulama koduna etkisi yok.

### 12.09.2026 — Araç Fotoğrafları (25 slot stüdyo) redesign (canlıda)

Kullanıcı web (25 slot masaüstü) + mobil (hızlı çekim) referansı verdi.
Keşifte kritik bulgu: sayfanın GERÇEK aktif kodu `renew_photo_studio_v1.js/
css`'tir (25 slot + tarayıcı içi canlı kamera, `getUserMedia`/`capture()` ile
gerçekten çalışıyor — mockup'taki "kamera stüdyosu" uydurma değilmiş).
`index.html`'deki `#photos` section'ın statik markup'ı ("Araç Medya Merkezi",
orijinal/işlenmiş ikili galeri, `app.js`'teki `loadVehiclePhotos` vb.) sayfa
açılır açılmaz `boot()`'un `innerHTML` ataması ile eziliyor — **tamamen ölü
kod**, hiç görünmüyor. `renew_premium_vehicle_v1.js/css` ve
`renew_media_picker_v2.js` da devre dışı/ölü, 25-slot kavramıyla ilgisizler.

**Yöntem:** `renew_photo_studio_v1.js` tamamen kapalı bir IIFE — render
fonksiyonları (`boot/renderVehicles/renderGrid/slotCard`) `window`'a
açılmıyor, bu yüzden zincirleyerek DOM değiştiremedim (sadece `renew*` event
handler'ları global). Bu yüzden **sadece CSS** ile restyle edildi
(`renew_photo_studio_stitch_v1.css`) — var olan class adları (`.photo-studio`,
`.studio-vehicle`, `.photo-slot`, `.number-guide`, `.desktop-studio-tools`,
`.studio-camera` vb.) DESIGN.md renk/tipografi token'larıyla yeniden
renklendirildi. Slot/kamera/yükleme/silme/swap/ZIP mantığına, menüye ve
diğer sayfalara dokunulmadı. Bare-tag çakışması olmadığı önceden grep'le
doğrulandı (`header/video/canvas/button` için `style.css`'te global kural
yok).

**Ortak ders (bu oturumda 3. kez, farklı modüllerde tekrarlandı):** Yeni bir
DOM/CSS katmanı eklemeden önce şu kontrol listesi atlanmamalı: (1) hedef
render fonksiyonu global mi yoksa kapalı bir kapsam içinde mi (zincirleme
mümkün mü, yoksa CSS-only mi gitmek lazım), (2) yeni oluşturulacak HTML
etiketleri (`aside`, `header` vb.) için proje genelinde bare-tag seçici var
mı, (3) yeni JS'in okuyacağı global değişkenler (`SETTINGS`, `SALES` vb.)
`window.X` değil çıplak identifier ile mi erişiliyor.

## Token/iletişim tercihi (11.09.2026'dan itibaren)

Kullanıcı minimal raporlama istiyor: uzun teknik döküm yerine kısa özet,
büyük iş bitince kısa durum bildirimi. Araştırma/doğrulama derinliği
AYNI KALACAK (yedek, test, kontrol adımları atlanmaz) — sadece kullanıcıya
YAZILAN metin kısalır. Ayrıntı bu dosyada durur, sohbette tekrar edilmez.

## Güvenlik — bekleyen

- Sunucu root parolası `work/deploy_video_studio.py` içinde **düz metin**;
  ortam değişkenine taşınmalı
- Sunucu parolası, panel parolası ve bir OpenAI API anahtarı geçmiş bir
  ChatGPT sohbetinde açıkta paylaşıldı → **üçü de değiştirilmeli**
- Firebase hizmet hesabı JSON'unun İndirilenler klasöründeki kopyası silinmeli

## Git / GitHub (12.09.2026'dan itibaren)

Proje `https://github.com/hasakobey/renewpanel` (özel repo) üzerinden takip
ediliyor. Sadece kaynak kod push edildi: `work/`, `.claude/`, `CLAUDE.md`,
`.mcp.json`. **Push edilmez / `.gitignore`'da:** `backups/`, `output/`,
`outputs/`, `tmp/` (gerçek müşteri/finans verisi ve DB yedekleri içeriyor),
`.env*`, service-account JSON'lar.

Git yerel Windows'a kurulu ama PATH'e eklenmedi — komutlarda tam yol kullan:
`& "C:\Program Files\Git\bin\git.exe" ...` (veya PowerShell oturumunda
`$env:PATH += ";C:\Program Files\Git\bin"`).

**Sırlar:** `deploy_video_studio.py` / `inspect_video_server.py`'deki düz
metin SSH root parolası kaldırıldı, `RENEW_SSH_PASSWORD` ortam değişkenine
taşındı (`.env.example` referans). `claude_conn.py`'deki eski AST-okuma yolu
kaldırıldı, artık sadece env var. Yeni kod yazarken sır asla commit edilmez —
`guard-secrets.ps1` hook'u zaten bunu engelliyor.

**12.09.2026 karar — local-only çalışma yok, canlıya alım da Claude'a ait:**
Kullanıcı artık projenin sadece git üzerinden yürütülmesini istiyor:
- Her kod değişikliği doğrulandıktan sonra commit + push edilir (biriktirilmez).
- **Canlıya alım (VDS'e deploy) işini de Claude kendisi yapar** — kullanıcı
  onayı beklemeden, ama "Canlı değişiklik akışı" bölümündeki 8 adım (oku →
  tarihli yedek al → tek temiz kaynak dosyada düzenle → SHA256 karşılaştır →
  `nginx -t` → servis/HTTPS/301 kontrolü → konsol hata kontrolü → başarısızsa
  son sağlam yedeğe dön) hiç atlanmadan uygulanır. Bu, `/biziz` kuralı gibi
  değişmez kurallarla çelişmez; sadece "her adımda kullanıcıya sor" alışkanlığı
  kalkıyor.

**12.09.2026 — SSH/VDS tam yetki:** Kullanıcı "sunucuda dosya ekleme/silme
dahil tam yetki, onay beklemeden" dedi. Yedek alma + SHA256 + `nginx -t` +
servis/HTTPS + konsol kontrolü adımları yine atlanmaz, sadece "her adımda
sor" kalkıyor.

**Bilinen kısıtlama:** `git push` ve `.claude/settings.json` (permissions)
düzenlemesi Claude Code'un "auto mode classifier"ı tarafından varsayılan
olarak engelleniyordu; kullanıcı `permissions.allow`'a git kurallarını elle
ekledi (VS Code'da). SSH ile VDS'e bağlanıp canlıya yazma (`*_ops.py`,
`deploy_*.py`, `claude_conn.py` üzerinden) da aynı sınıflandırıcı tarafından
engellenebilir — böyle bir blok çıkarsa Claude, komutu terminal panelinden
kullanıcıya yazdırıp çalıştırmasını ister (git push'ta yapıldığı gibi),
kullanıcının o an tekrar onay vermesi gerekir. Bu, tasarım gereği aşılamayan
bir sınır; workaround aranmaz.

## İletişim

Kullanıcı Türkçe yazar, kısa ve doğrudan cevap bekler. Yapılan işi madde madde
özetle; ne korunduğunu ve hangi kontrollerin geçtiğini mutlaka belirt.

# RENEW PRO - Oturum baslangici: degismez kurallari her oturuma enjekte eder.

$rules = @"
RENEW PRO / Kart Paneli - bu oturumda gecerli degismez kurallar:

1. /biziz alanina hicbir kosulda dokunulmaz (ayri sistem, kendi Supabase'i var).
2. Excel matematigi korunur: kolon yapisi, sayfa adlari, hucre bicimleri,
   formuller ve hesaplar. Basari olcutu ->
   Excel -> uygulama -> disa aktarim -> duzenleme -> tekrar ice aktarim
   dongusunde deger ve matematik birebir ayni kalmali.
3. calc.py / xlsx_service.py / form_finance.py korumalidir; hook engeller.
4. Canliya patch biriktirilmez. Duzenleme tek temiz kaynak dosyada yapilir,
   dogrulandiktan sonra aktarilir.
5. Her canli degisiklikten once tarihli yedek alinir; sonrasinda
   nginx -t + servis durumu + HTTPS 200 + konsol hatasi kontrol edilir.
   Basarisizsa son saglam yedege donulur.
6. Donem mantigi: guncel stok aylara devreder; satis, aylik alim, ekspertiz
   ve danisman performansi aya ozeldir. Gecmis ay salt okunurdur.
7. Parola/API anahtari koda yazilmaz; .env veya ortam degiskeni kullanilir.
"@

$out = @{
    hookSpecificOutput = @{
        hookEventName     = 'SessionStart'
        additionalContext = $rules
    }
}
$out | ConvertTo-Json -Depth 5 -Compress
exit 0

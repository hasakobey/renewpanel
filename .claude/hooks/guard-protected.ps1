# RENEW PRO - Korumali dosya bekcisi (PreToolUse: Edit/Write/MultiEdit/NotebookEdit)
# Excel matematigi, hesaplama modulleri ve /biziz alani izinsiz degistirilemez.
# Gecici izin:  $env:RENEW_ALLOW_PROTECTED = '1'

$raw = [Console]::In.ReadToEnd()
if (-not $raw) { exit 0 }
try { $p = $raw | ConvertFrom-Json } catch { exit 0 }

$path = $null
if ($p.tool_input) {
    if ($p.tool_input.PSObject.Properties.Name -contains 'file_path')     { $path = $p.tool_input.file_path }
    elseif ($p.tool_input.PSObject.Properties.Name -contains 'notebook_path') { $path = $p.tool_input.notebook_path }
}
if (-not $path) { exit 0 }

$norm = ($path -replace '/', '\')
$leaf = Split-Path $norm -Leaf

# --- /biziz: mutlak dokunulmaz, override yok ---
if ([regex]::IsMatch($norm, '(^|\\|:)biziz(\\|$)')) {
    [Console]::Error.WriteLine(@"
ENGELLENDI: /biziz alanina yazma denemesi -> $path

/biziz ayri bir sistemdir (kendi Supabase baglantisi var) ve bu projenin
degismez kurali geregi hicbir kosulda degistirilmez. Bu koruma devre disi
birakilamaz. Kullaniciya durumu bildir ve baska bir yol iste.
"@)
    exit 2
}

if ($env:RENEW_ALLOW_PROTECTED -eq '1') { exit 0 }

# --- Matematik / Excel cekirdegi ---
$mathFiles = @('calc.py', 'xlsx_service.py', 'form_finance.py')
if ($mathFiles -contains $leaf) {
    [Console]::Error.WriteLine(@"
ENGELLENDI: Matematik/Excel cekirdek dosyasi -> $leaf

Projenin degismez ana kurali: Excel kolon yapisi, sayfa adlari, hucre
bicimleri ve hesaplama matematigi korunur. Bu dosyalar ancak su sira
tamamlandiktan sonra degistirilebilir:

  1. Kullanicidan bu dosya icin ACIK onay al.
  2. Once referans testini calistir (Excel -> uygulama -> disa aktarim ->
     duzenleme -> tekrar ice aktarim) ve mevcut sonuclari kaydet.
  3. Degisiklikten sonra ayni testi tekrarla; kurus farki bile olmamali.
  4. Onay ve test sonrasi:  \$env:RENEW_ALLOW_PROTECTED = '1'  ile tekrar dene.

Simdilik degisikligi baska bir dosyada (ayri katman) yapmayi degerlendir.
"@)
    exit 2
}

# --- Referans Excel sablonlari ---
if ([regex]::IsMatch($leaf, '(?i)^(RENEW_MASTER_SABLON|KULLANICI_ORIJINALI_DOKUNMA)\.xlsx$')) {
    [Console]::Error.WriteLine(@"
ENGELLENDI: Referans Excel sablonu -> $leaf

Bu dosyalar dogrulama referansidir; uzerine yazilmaz. Kopyasini al,
kopya uzerinde calis ve farki kullaniciya sun.
"@)
    exit 2
}

exit 0

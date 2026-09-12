# RENEW PRO - Sir/parola bekcisi (PreToolUse: Edit/Write/MultiEdit)
# Duz metin parola, API anahtari veya ozel anahtarin dosyaya yazilmasini engeller.
# Gecici izin:  $env:RENEW_ALLOW_SECRET = '1'

$raw = [Console]::In.ReadToEnd()
if (-not $raw) { exit 0 }
try { $p = $raw | ConvertFrom-Json } catch { exit 0 }
if ($env:RENEW_ALLOW_SECRET -eq '1') { exit 0 }

$chunks = New-Object System.Collections.Generic.List[string]
$ti = $p.tool_input
if ($ti) {
    $names = $ti.PSObject.Properties.Name
    if ($names -contains 'content')    { $chunks.Add([string]$ti.content) }
    if ($names -contains 'new_string') { $chunks.Add([string]$ti.new_string) }
    if ($names -contains 'edits') {
        foreach ($e in $ti.edits) {
            if ($e.PSObject.Properties.Name -contains 'new_string') { $chunks.Add([string]$e.new_string) }
        }
    }
}
if ($chunks.Count -eq 0) { exit 0 }
$text = ($chunks -join "`n")
if ([string]::IsNullOrWhiteSpace($text)) { exit 0 }

$rules = @(
    @{ Name = 'OpenAI API anahtari';        Pattern = 'sk-[A-Za-z0-9_\-]{20,}' },
    @{ Name = 'Google/Firebase API key';    Pattern = 'AIza[0-9A-Za-z_\-]{30,}' },
    @{ Name = 'Ozel anahtar (PEM)';         Pattern = '-----BEGIN [A-Z ]*PRIVATE KEY-----' },
    @{ Name = 'Duz metin parola';           Pattern = '(?i)(password|passwd|sifre)\s*[=:]\s*["''][^"'']{4,}["'']' },
    @{ Name = 'Sunucu root parolasi';       Pattern = '(?i)username\s*=\s*["'']root["''].{0,80}password' }
)

# Not: PowerShell 5.1'de -match, degiskende tutulan kalipla tutarsiz sonuc
# verebiliyor; bu yuzden dogrudan .NET regex kullaniliyor.
$hits = @()
foreach ($r in $rules) {
    if ([regex]::IsMatch($text, $r.Pattern)) { $hits += $r.Name }
}
if ($hits.Count -eq 0) { exit 0 }

$list = ($hits -join ', ')
[Console]::Error.WriteLine(@"
ENGELLENDI: Dosyaya duz metin sir yazilmak uzere -> $list

Bu projede sunucu parolasi ve API anahtarlari daha once sohbette acikta
kaldi; ayni hatayi kod tarafinda tekrarlama. Bunun yerine:

  - Degeri .env dosyasina veya ortam degiskenine koy
    (ornek: os.environ['RENEW_SSH_PASSWORD'])
  - Kod icinde yalnizca degisken adini kullan
  - .env dosyasini paylasma, ciktiya yazdirma

Gercekten gerekiyorsa once kullaniciya sor, sonra:
  \$env:RENEW_ALLOW_SECRET = '1'
"@)
exit 2

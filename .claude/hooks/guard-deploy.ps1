# RENEW PRO - Canli sunucu bekcisi (PreToolUse: Bash/PowerShell)
# Canliya dokunan her komutu onaya dusurur ve kontrol listesini hatirlatir.

$raw = [Console]::In.ReadToEnd()
if (-not $raw) { exit 0 }
try { $p = $raw | ConvertFrom-Json } catch { exit 0 }

$cmd = ''
if ($p.tool_input -and ($p.tool_input.PSObject.Properties.Name -contains 'command')) {
    $cmd = [string]$p.tool_input.command
}
if ([string]::IsNullOrWhiteSpace($cmd)) { exit 0 }

# Canliya dokunan / uzak sunucuda is yapan komut kaliplari
$deployPatterns = @(
    '_ops\.py',
    'deploy_[A-Za-z0-9_]*\.py',
    'rollback_[A-Za-z0-9_]*\.py',
    '\bssh\b',
    '\bscp\b',
    '\bsftp\b',
    'paramiko',
    '45\.195\.231\.20',
    'renewpanel\.xyz',
    'systemctl\s+(restart|stop|reload)',
    'nginx\s+-s\s+reload'
)

# Not: PowerShell 5.1'de -match, degiskende tutulan kalipla tutarsiz sonuc
# verebiliyor; bu yuzden dogrudan .NET regex kullaniliyor.
$matched = $null
foreach ($pat in $deployPatterns) {
    if ([regex]::IsMatch($cmd, $pat)) { $matched = $pat; break }
}
if (-not $matched) { exit 0 }

# Yikici komutlar: onay degil, dogrudan red
if ([regex]::IsMatch($cmd, '(?i)(rm\s+-rf\s+/|DROP\s+TABLE|DELETE\s+FROM|truncate|mkfs|>\s*/var/lib/renewpro)')) {
    [Console]::Error.WriteLine(@"
ENGELLENDI: Canli sistemde yikici komut tespit edildi.

Komut: $cmd

Bu proje geri donulemez islemlere kapalidir. Once yedek al, sonra
kullaniciya ne yapmak istedigini tam olarak anlat ve acik onay iste.
"@)
    exit 2
}

$reason = @"
CANLI SUNUCU ISLEMI (eslesen kalip: $matched)

Calistirmadan once kontrol listesi:
  1. Tarihli yedek alindi mi?  (/opt/renewpro/backups/... veya /root/...)
  2. Degisiklik tek temiz kaynak dosyada mi yapildi? (canliya patch biriktirme YOK)
  3. Yerel <-> canli SHA256 karsilastirmasi planlandi mi?
  4. Sonrasinda: nginx -t, servis durumu, HTTPS 200, tarayici konsolu kontrolu
  5. Basarisiz olursa hangi yedege donulecek, belli mi?
  6. /biziz alanina dokunulmuyor, degil mi?

Onaylarsan calistiriyorum.
"@

$out = @{
    hookSpecificOutput = @{
        hookEventName            = 'PreToolUse'
        permissionDecision       = 'ask'
        permissionDecisionReason = $reason
    }
}
$out | ConvertTo-Json -Depth 5 -Compress
exit 0

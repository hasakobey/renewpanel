# RENEW PRO - Duzenleme sonrasi sozdizimi kontrolu (PostToolUse: Edit/Write/MultiEdit)
# Bozuk script canliya gitmeden yakalanir. (Gecmiste kapanmamis <script> blogu
# tasarim kaymalarinin ana sebebiydi.)

$raw = [Console]::In.ReadToEnd()
if (-not $raw) { exit 0 }
try { $p = $raw | ConvertFrom-Json } catch { exit 0 }

$path = $null
if ($p.tool_input -and ($p.tool_input.PSObject.Properties.Name -contains 'file_path')) {
    $path = $p.tool_input.file_path
}
if (-not $path) { exit 0 }
if (-not (Test-Path -LiteralPath $path)) { exit 0 }

$ext = [System.IO.Path]::GetExtension($path).ToLowerInvariant()
$problem = $null

if ($ext -eq '.py') {
    $py = Get-Command python -ErrorAction SilentlyContinue
    if ($py) {
        # Tek satir olmali: cok satirli -c argumani tirnak kaybina ugruyor.
        $code = "import ast,sys;ast.parse(open(sys.argv[1],encoding='utf-8').read())"
        $out = & $py.Source -c $code $path 2>&1
        if ($LASTEXITCODE -ne 0) { $problem = ($out | Out-String).Trim() }
    }
}
elseif ($ext -eq '.js' -or $ext -eq '.mjs') {
    $node = Get-Command node -ErrorAction SilentlyContinue
    if ($node) {
        $out = & $node.Source --check $path 2>&1
        if ($LASTEXITCODE -ne 0) { $problem = ($out | Out-String).Trim() }
    }
}
elseif ($ext -eq '.html' -or $ext -eq '.htm') {
    $text = Get-Content -LiteralPath $path -Raw -Encoding UTF8
    if ($null -ne $text) {
        $open  = ([regex]::Matches($text, '(?i)<script\b')).Count
        $close = ([regex]::Matches($text, '(?i)</script\s*>')).Count
        if ($open -ne $close) {
            $problem = "Kapanmamis <script> blogu: $open adet <script>, $close adet </script>."
        } else {
            $so = ([regex]::Matches($text, '(?i)<style\b')).Count
            $sc = ([regex]::Matches($text, '(?i)</style\s*>')).Count
            if ($so -ne $sc) {
                $problem = "Kapanmamis <style> blogu: $so adet <style>, $sc adet </style>."
            }
        }
    }
}

if ($problem) {
    [Console]::Error.WriteLine("SOZDIZIMI HATASI -> $path`n`n$problem`n`nBu dosya canliya gitmeden duzeltilmeli.")
    exit 2
}
exit 0

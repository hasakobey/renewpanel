import re, shutil, subprocess
from pathlib import Path
STAGE = Path(__file__).resolve().parent / "login_clean"
html = (STAGE/"index.html").read_text(encoding="utf-8")
css = (STAGE/"renew_login_switch_v1.css").read_text(encoding="utf-8")
js = (STAGE/"renew_login_switch_v1.js").read_text(encoding="utf-8")

print("=== ID korunumu ===")
for i in ("loginOverlay","loginForm","loginUsername","loginPassword","loginMessage","cardPortalLink"):
    print(f"  {i}: {html.count(chr(39)+i+chr(39)) + html.count(chr(34)+i+chr(34))}")

divo, divc = len(re.findall(r'<div\b', html)), len(re.findall(r'</div>', html))
print(f"<div> denge: {divo}/{divc}")
so, sc = len(re.findall(r'<script\b', html, re.I)), len(re.findall(r'</script\s*>', html, re.I))
print(f"<script> denge: {so}/{sc}")

print("\nCSS { } denge:", css.count('{'), '/', css.count('}'))
node = shutil.which("node")
r = subprocess.run([node,"--check",str(STAGE/"renew_login_switch_v1.js")], capture_output=True, text=True)
print("node --check:", "OK" if r.returncode==0 else "HATA:"+r.stderr[:200])
print("tab/role kalintisi (temizlenmis olmali):", "role=\"tablist\"" in html, "role=\"tab\"" in html)
print("check yesil-beyaz:", "check{width:72px" in css.replace('\n','') and "color:#fff" in css)

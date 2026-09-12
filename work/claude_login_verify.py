import re, shutil, subprocess
from pathlib import Path
STAGE = Path(__file__).resolve().parent / "login_clean"

html = (STAGE/"index.html").read_text(encoding="utf-8")
js = (STAGE/"app.js").read_text(encoding="utf-8")
css = (STAGE/"renew_login_switch_v1.css").read_text(encoding="utf-8")
newjs = (STAGE/"renew_login_switch_v1.js").read_text(encoding="utf-8")

print("=== HTML ID korunumu ===")
for i in ("loginOverlay","loginForm","loginUsername","loginPassword","loginMessage"):
    print(f"  {i}: {html.count('id=\"'+i+'\"')}")

so, sc = len(re.findall(r'<script\b', html, re.I)), len(re.findall(r'</script\s*>', html, re.I))
print(f"<script> denge: {so}/{sc}")
divo = len(re.findall(r'<div\b', html)); divc = len(re.findall(r'</div>', html))
print(f"<div> denge: {divo}/{divc}")
seco = len(re.findall(r'<section\b', html)); secc = len(re.findall(r'</section>', html))
print(f"<section> denge: {seco}/{secc}")

print("\n=== app.js ===")
node = shutil.which("node")
p = STAGE/"app.js"
r = subprocess.run([node,"--check",str(p)], capture_output=True, text=True)
print("node --check app.js:", "OK" if r.returncode==0 else "HATA: "+r.stderr[:200])
print("olu blok kaldi mi:", "CURRENT_USER=j;$('#loginOverlay')" in js)
print("ikinci blok korunuyor mu:", "getElementById('loginForm').onsubmit=async" in js)

print("\n=== yeni JS ===")
p2 = STAGE/"renew_login_switch_v1.js"
r2 = subprocess.run([node,"--check",str(p2)], capture_output=True, text=True)
print("node --check yeni js:", "OK" if r2.returncode==0 else "HATA: "+r2.stderr[:200])

print("\n=== CSS denge ===")
print(f"{{ }}: {css.count('{')}/{css.count('}')}")

print("\n=== yasakli icerik ===")
for name, text in (("index.html",html),("app.js",js),("css",css),("js",newjs)):
    bad = [x for x in ("__errs","127.0.0.1","console.log(") if x in text]
    print(f"  {name}: {bad or 'temiz'}")

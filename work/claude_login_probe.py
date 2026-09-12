import re
from pathlib import Path
STAGE = Path(__file__).resolve().parent / "login_clean"
html = (STAGE/"index.html").read_text(encoding="utf-8")
js = (STAGE/"app.js").read_text(encoding="utf-8")

m = re.search(r'<div id="loginOverlay"', html)
print("=== index.html loginOverlay bolgesi ===")
print(html[m.start():m.start()+1400])

print("\n=== app.js ilk (olu) blok, satir 1077 civari ===")
lines = js.split("\n")
for i in range(1074, 1090):
    print(i+1, "|", lines[i][:180])

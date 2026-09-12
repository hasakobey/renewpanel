"""Kart sitesi yamasi: tasarimi window.load yerine DOMContentLoaded'da uygula.

Neden: renew-stitch-v1.css'in 185 kuralinin tamami body.rst-v1 sinifina bagli.
Bu sinifi ekleyen init() su an window.load'da calisiyor; load ise sayfanin
EN SON olayi (Google Fonts dahil her istek biter, olculen gecikme 306 ms).
O sureye kadar tarayici eski duzeni boyuyor -> "yenileyince eski tasarim".

Cozum: script'ler zaten `defer`, yani DOM ayristirilmis halde calisiyorlar.
Tetigi DOMContentLoaded'a alip requestAnimationFrame ile sarmaliyoruz.
rAF, stil hesaplamasindan sonra ve boyamadan once calisir; boylece
getComputedStyle(...) okuyan kisimlar dogru deger gorur.

Calisma kopyalari uzerinde calisir, canliya dokunmaz.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

STAGE = Path(__file__).resolve().parent / "kart_clean"

JS_FILES = [
    "kart-console-v1.js",
    "kart-interactive-v4.js",
    "renew-stitch-v1.js",
    "renew-stitch-details.js",
]

OLD_A = "if(document.readyState!=='complete')window.addEventListener('load',init);else init()"
OLD_B = "if(document.readyState==='complete')init();else window.addEventListener('load',init)"
# NOT: requestAnimationFrame KULLANILMAZ. rAF gizli/arka plan sekmesinde hic
# calismaz; sayfa arka planda acilirsa tasarim hic uygulanmaz. (Yerelde
# visibilityState='hidden' ile dogrulandi.) Dogrudan cagri guvenli: script'ler
# `defer` oldugu icin DOM ayristirilmis ve onlerindeki render-blocking
# stylesheet'ler uygulanmis durumda, yani getComputedStyle dogru deger okur.
#
# SIRALAMA: '.rc-workspace' yapisini satir-ici renew-compact-workspace-v2-js
# kuruyor ve o DOMContentLoaded'i dinliyor. `defer` script'ler ayristirma
# bitince readyState='interactive' ile calisir; orada init()'i HEMEN cagirirsak
# workspace henuz yokken devreye gireriz (test: rstActions=false + 2 JS hatasi).
# Bu yuzden 'loading' degil 'complete' kontrolu yapiyoruz: interactive
# durumunda da dinleyici kaydedilir ve DOMContentLoaded'da, satir-ici
# kurucudan SONRA calisir (dinleyiciler kayit sirasina gore tetiklenir).
NEW = ("if(document.readyState==='complete')init();"
       "else document.addEventListener('DOMContentLoaded',init)")

# index.html: surum yukseltme + olu favicon referansi
VERSION_BUMPS = [
    ("kart-console-v1.js?v=5", "kart-console-v1.js?v=6"),
    ("kart-interactive-v4.js?v=5", "kart-interactive-v4.js?v=6"),
    ("renew-stitch-v1.js?v=2", "renew-stitch-v1.js?v=3"),
    ("renew-stitch-details.js?v=1", "renew-stitch-details.js?v=2"),
]


def node_check(path):
    node = shutil.which("node")
    if not node:
        return "node yok, atlandi"
    r = subprocess.run([node, "--check", str(path)], capture_output=True, text=True)
    if r.returncode == 0:
        return "OK"
    return "HATA: " + (r.stderr or "").strip().splitlines()[-1][:140]


def main():
    print("=== JS tetik degisikligi ===\n")
    changed = []
    for name in JS_FILES:
        path = STAGE / name
        text = path.read_text(encoding="utf-8")

        if OLD_A in text:
            new_text = text.replace(OLD_A, NEW)
            kalip = "A"
        elif OLD_B in text:
            new_text = text.replace(OLD_B, NEW)
            kalip = "B"
        else:
            print(f"{name:<26} BEKLENEN KALIP YOK - atlandi")
            continue

        if new_text == text:
            print(f"{name:<26} degisiklik olusmadi")
            continue

        path.write_text(new_text, encoding="utf-8", newline="")
        status = node_check(path)
        print(f"{name:<26} kalip {kalip}  ->  sozdizimi {status}")
        if status != "OK":
            print("   !! geri aliniyor")
            path.write_text(text, encoding="utf-8", newline="")
            continue
        changed.append(name)

    print("\n=== index.html ===\n")
    idx = STAGE / "index.html"
    html = idx.read_text(encoding="utf-8")
    before = html

    for old, new in VERSION_BUMPS:
        if old in html:
            html = html.replace(old, new)
            print(f"surum  {old}  ->  {new}")
        else:
            print(f"surum  {old}  BULUNAMADI")

    # renew.ico 404 veriyor; olu <link> etiketini kaldir
    ico = re.search(r'<link\b[^>]*href="renew\.ico"[^>]*>\s*', html, re.I)
    if ico:
        html = html[:ico.start()] + html[ico.end():]
        print(f"kaldirildi  {ico.group(0).strip()}   (canlida 404 donuyordu)")
    else:
        print("renew.ico link etiketi bulunamadi")

    if html != before:
        idx.write_text(html, encoding="utf-8", newline="")
        print(f"\nindex.html yazildi  ({len(before):,} -> {len(html):,} bayt)")
        changed.append("index.html")

    print("\n=== degisen dosyalar ===")
    for n in changed:
        print("  " + n)
    return 0


if __name__ == "__main__":
    sys.exit(main())

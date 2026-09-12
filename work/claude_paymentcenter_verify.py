"""payment-center kaldirma sonrasi dogrulama: diff, HTML/JS/CSS butunlugu,
kalan referans kontrolu, mail-templates'e dokunulmadigi kaniti."""
import difflib
import re
import shutil
import subprocess
import sys
from pathlib import Path

STAGE = Path(__file__).resolve().parent / "paycenter_clean"
LIVE = STAGE / "live"
FILES = ["index.html", "app.js", "style.css", "renew_dashboard_v26.css"]


def diff_summary(name):
    live_t = (LIVE / name).read_text(encoding="utf-8", errors="replace")
    new_t = (STAGE / name).read_text(encoding="utf-8", errors="replace")
    diff = list(difflib.unified_diff(live_t.splitlines(), new_t.splitlines(),
                                     lineterm="", n=1))
    added = sum(1 for d in diff if d.startswith("+") and not d.startswith("+++"))
    removed = sum(1 for d in diff if d.startswith("-") and not d.startswith("---"))
    print(f"{name:<26} eklenen {added:>3} satir, silinen {removed:>3} satir  "
          f"({len(live_t):,} -> {len(new_t):,} bayt)")
    return diff


def main():
    print("=== 1. diff ozeti ===")
    for name in FILES:
        diff_summary(name)

    print("\n=== 2. index.html butunlugu ===")
    html = (STAGE / "index.html").read_text(encoding="utf-8")
    so = len(re.findall(r'<script\b', html, re.I))
    sc = len(re.findall(r'</script\s*>', html, re.I))
    sections = re.findall(r'<section\s+id="([a-z0-9-]+)"', html)
    print(f"  <script> acilis/kapanis: {so}/{sc}")
    print(f"  section sayisi: {len(sections)}  (once 20 idi, simdi {len(sections)} olmali)")
    print(f"  'payment-center' hala geciyor mu: {'payment-center' in html}")
    print(f"  'mail-templates' hala orada mi (DOKUNULMAMALI): {'mail-templates' in html}")
    print(f"  paymentCenterFrame kalintisi: {'paymentCenterFrame' in html}")

    print("\n=== 3. app.js sozdizimi + fonksiyon kontrolu ===")
    node = shutil.which("node")
    js_path = STAGE / "app.js"
    if node:
        r = subprocess.run([node, "--check", str(js_path)], capture_output=True, text=True)
        print(f"  node --check: {'OK' if r.returncode == 0 else 'HATA: ' + r.stderr[:200]}")
    js = js_path.read_text(encoding="utf-8")
    print(f"  reloadPaymentCenter kaldi mi: {'reloadPaymentCenter' in js}")
    print(f"  openPaymentCenterNewTab kaldi mi: {'openPaymentCenterNewTab' in js}")
    print(f"  mail-template fonksiyonlari hala orada mi (DOKUNULMAMALI):")
    for fn in ("renderMailTplPreview", "selectMailTemplate", "renderAuthorityManager"):
        print(f"    {fn}: {fn in js}")

    print("\n=== 4. CSS butunlugu ===")
    css = (STAGE / "style.css").read_text(encoding="utf-8")
    open_b = css.count("{")
    close_b = css.count("}")
    print(f"  style.css {{ }} dengesi: {open_b}/{close_b}  {'OK' if open_b == close_b else 'DENGESIZ !!'}")
    print(f"  payment-center-shell kalintisi: {'.payment-center-shell' in css}")
    print(f"  paymentCenterFrame kalintisi: {'#paymentCenterFrame' in css}")

    dcss = (STAGE / "renew_dashboard_v26.css").read_text(encoding="utf-8")
    ob2, cb2 = dcss.count("{"), dcss.count("}")
    print(f"  renew_dashboard_v26.css {{ }} dengesi: {ob2}/{cb2}  {'OK' if ob2 == cb2 else 'DENGESIZ !!'}")
    print(f"  #mail-templates hala gizli mi (KORUNMALI): "
          f"{'#mail-templates{display:none!important}' in dcss.replace(chr(10),'').replace(' ','')}")

    print("\n=== 5. Diger dosyalarda kalan payment_center.html referansi ===")
    remaining = []
    for name in ("index.html", "app.js"):
        text = (STAGE / name).read_text(encoding="utf-8")
        if "payment_center" in text or "payment-center" in text:
            remaining.append(name)
    print("  kalan referans:", remaining if remaining else "yok")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""payment-center hayaletini kaldirir: HTML bolumu + izole JS fonksiyonlari + CSS.

Kapsam (dogrulandi -> claude_payment_extract.py, claude_mailtpl_reach2.py):
  - <section id="payment-center">...</section>  (index.html, 600 karakter)
  - reloadPaymentCenter(), openPaymentCenterNewTab()  (yalnizca bu bolumden
    cagriliyor, app.js icinde baska hicbir yerden cagrilmiyor)
  - style.css: .payment-center-shell, #paymentCenterFrame kurallari
  - renew_dashboard_v26.css: #payment-center hala orada ama artik section
    yok, referans kalinca zararsiz oldugu icin YALNIZCA #payment-center
    kismi cikarilir, #mail-templates KORUNUR (o bolum hala duruyor)

mail-templates BU KAPSAMA DAHIL DEGIL.
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

STAGE = Path(__file__).resolve().parent / "paycenter_clean"


def node_check(path):
    node = shutil.which("node")
    if not node:
        return "node yok, atlandi"
    r = subprocess.run([node, "--check", str(path)], capture_output=True, text=True)
    return "OK" if r.returncode == 0 else "HATA: " + (r.stderr or "").strip().splitlines()[-1][:150]


def section_bounds(html, section_id):
    m = re.search(rf'<section\s+id="{re.escape(section_id)}"[^>]*>', html)
    if not m:
        return None
    pos = m.end()
    depth = 1
    for tag in re.finditer(r'<section\b[^>]*>|</section\s*>', html[pos:], re.I):
        if tag.group(0).lower().startswith('</'):
            depth -= 1
            if depth == 0:
                return m.start(), pos + tag.end()
        else:
            depth += 1
    return None


def main():
    print("=== 1. index.html: <section id=\"payment-center\"> kaldirma ===")
    idx = STAGE / "index.html"
    html = idx.read_text(encoding="utf-8")
    b = section_bounds(html, "payment-center")
    if not b:
        print("BULUNAMADI - islem durduruldu")
        return 1
    removed_html = html[b[0]:b[1]]
    print(f"kaldirilan: {len(removed_html)} karakter")
    new_html = html[:b[0]] + html[b[1]:]
    # bosluk temizligi: bos satirin ardindaki satiri koru
    idx.write_text(new_html, encoding="utf-8", newline="")
    print(f"index.html: {len(html):,} -> {len(new_html):,} bayt")

    print("\n=== 2. app.js: reloadPaymentCenter / openPaymentCenterNewTab kaldirma ===")
    appjs_path = STAGE / "app.js"
    js = appjs_path.read_text(encoding="utf-8")

    # tek satirlik fonksiyon govdeleri (dogrulandi -> tek satirda tanimli)
    for fn in ("reloadPaymentCenter", "openPaymentCenterNewTab"):
        # /* yorum */ function AD(){ ... }
        pat = re.compile(
            rf'(?:/\*[^*]*\*/\s*)?function\s+{re.escape(fn)}\s*\(\)\s*\{{[^}}]*\}}\s*')
        m = pat.search(js)
        if not m:
            print(f"  {fn}: KALIP BULUNAMADI - atlandi (elle kontrol et)")
            continue
        print(f"  {fn}: kaldirildi -> {m.group(0)[:100].strip()}...")
        js = js[:m.start()] + js[m.end():]

    appjs_path.write_text(js, encoding="utf-8", newline="")
    status = node_check(appjs_path)
    print(f"\napp.js sozdizimi: {status}")
    if status != "OK":
        print("!! sozdizimi hatasi - islem durduruldu, dosyalar degistirilmedi sayilmali")
        return 1

    print("\n=== 3. style.css: payment-center-shell / paymentCenterFrame kurallari ===")
    css_path = STAGE / "style.css"
    css = css_path.read_text(encoding="utf-8")
    before_len = len(css)
    removed_rules = []
    for pat in [
        r'/\*[^*]*ÖDEME MERKEZİ[^*]*\*/\s*',
        r'\.payment-center-shell\s*\{[^}]*\}\s*',
        r'#paymentCenterFrame\s*\{[^}]*\}\s*',
        r'#payment-center\s+\.hero[^{]*\{[^}]*\}\s*',
    ]:
        for m in list(re.finditer(pat, css)):
            removed_rules.append(m.group(0).strip()[:70])
        css = re.sub(pat, '', css)
    css_path.write_text(css, encoding="utf-8", newline="")
    print(f"style.css: {before_len:,} -> {len(css):,} bayt  ({len(removed_rules)} kural/yorum kaldirildi)")
    for r in removed_rules:
        print(f"  - {r}")

    print("\n=== 4. renew_dashboard_v26.css: yalnizca #payment-center kismi ===")
    dcss_path = STAGE / "renew_dashboard_v26.css"
    dcss = dcss_path.read_text(encoding="utf-8")
    before_len2 = len(dcss)
    # #payment-center,#mail-templates{...} -> #mail-templates{...}
    new_dcss, n = re.subn(
        r'#payment-center\s*,\s*(#mail-templates)\s*\{',
        r'\1{',
        dcss)
    if n:
        dcss_path.write_text(new_dcss, encoding="utf-8", newline="")
        print(f"renew_dashboard_v26.css: {before_len2:,} -> {len(new_dcss):,} bayt")
        print("  '#payment-center,#mail-templates{...}' -> '#mail-templates{...}'")
    else:
        print("  KALIP BULUNAMADI - dosya degistirilmedi (zararsiz, bos secici kalirdi)")

    print("\n=== ozet ===")
    print("degisen dosyalar: index.html, app.js, style.css"
          + (", renew_dashboard_v26.css" if n else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())

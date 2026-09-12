"""payment-center / mail-templates temizligi icin ilgili TUM kod parcalarini
tam sinirlariyla cikarir. Salt okunur inceleme; hicbir dosyaya yazmaz."""
import re
import sys

from claude_conn import ssh

STATIC = "/opt/renewpro/app_live/app/static"


def section_bounds(html, section_id):
    """<section id="X" ...> ile eslesen kapanis </section>'i bulur (basit sayac)."""
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
    client = ssh()
    try:
        sftp = client.open_sftp()
        index = sftp.open(f"{STATIC}/index.html", "r").read().decode("utf-8", errors="replace")
        appjs = sftp.open(f"{STATIC}/app.js", "r").read().decode("utf-8", errors="replace")

        print("=" * 70)
        print("1. index.html: <section id=\"payment-center\">...</section>")
        print("=" * 70)
        b = section_bounds(index, "payment-center")
        if b:
            start_line = index.count("\n", 0, b[0]) + 1
            end_line = index.count("\n", 0, b[1]) + 1
            print(f"satir {start_line}-{end_line}  ({b[1]-b[0]} karakter)\n")
            print(index[b[0]:b[1]])
        else:
            print("BULUNAMADI (esleme basarisiz - dikkat)")

        print("\n" + "=" * 70)
        print("2. index.html: <section id=\"mail-templates\">...</section>")
        print("=" * 70)
        b2 = section_bounds(index, "mail-templates")
        if b2:
            start_line = index.count("\n", 0, b2[0]) + 1
            end_line = index.count("\n", 0, b2[1]) + 1
            print(f"satir {start_line}-{end_line}  ({b2[1]-b2[0]} karakter)")
            preview = index[b2[0]:b2[1]]
            print(preview[:800] + ("\n...[kisaltildi]..." if len(preview) > 800 else ""))
        else:
            print("BULUNAMADI")

        print("\n" + "=" * 70)
        print("3. app.js icinde payment/mail-template fonksiyon adlari")
        print("=" * 70)
        fn_names = set()
        for pat in [r'function\s+(reloadPaymentCenter|openPaymentCenterNewTab)\b',
                    r'function\s+(\w*[Mm]ailT[eE]mplate\w*)\b',
                    r'function\s+(\w*[Mm]ailTpl\w*)\b']:
            fn_names |= set(re.findall(pat, appjs))
        print("bulunan fonksiyonlar:", sorted(fn_names))

        print("\n--- her fonksiyonun index.html'de kac yerden cagrildigi ---")
        for fn in sorted(fn_names):
            count_html = len(re.findall(re.escape(fn) + r'\(', index))
            count_js = len(re.findall(re.escape(fn) + r'\(', appjs)) - 1  # tanimin kendisi haric degil, kaba sayim
            print(f"  {fn:<30} index.html'de {count_html} kez, app.js'de {count_js+1} kez")

        print("\n" + "=" * 70)
        print("4. Nav/menu HTML'inde 'payment' veya 'mail-template' icın <a>/<li> var mi")
        print("=" * 70)
        for m in re.finditer(r'.{0,50}(payment-center|mail-templates).{0,120}', index):
            frag = " ".join(m.group(0).split())
            if 'href' in frag.lower() or 'data-page' in frag.lower() or '<a ' in frag.lower() or '<li' in frag.lower():
                print("  " + frag[:200])

        print("\n(yukarida hic satir yoksa: menude bu sayfalara giden hicbir gorunur")
        print(" ogeye rastlanmadi demektir.)")
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

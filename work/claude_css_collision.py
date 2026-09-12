"""renew-stitch-v1.css ile ONDAN SONRA gelen satir-ici <style> bloklarinin cakismasi.

Ayni secici hem stitch dosyasinda hem sonraki satir-ici blokta tanimliysa,
satir-ici olan kazanir (esit ozgullukte sonraki kural ezer) -> yeni tasarim
kismen gorunmez.
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KART = ROOT.parent / "tmp" / "analiz" / "kart.renewpanel.xyz"
INDEX = ROOT / "kart_clean" / "index.work.html"
STITCH = KART / "renew-stitch-v1.css"

OPEN_STYLE = re.compile(r"<style\b[^>]*>", re.I)
CLOSE_STYLE = re.compile(r"</style\s*>", re.I)


def selectors(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out = defaultdict(int)
    for m in re.finditer(r"(?:^|[}\n])\s*([^{}@\n][^{}]{0,300}?)\s*\{", css):
        raw = m.group(1).strip()
        if not raw or raw.startswith("@") or len(raw) > 160:
            continue
        for part in raw.split(","):
            part = " ".join(part.split())
            if part and not part[0].isdigit():
                out[part] += 1
    return out


def main():
    text = INDEX.read_text(encoding="utf-8", errors="replace")

    link = re.search(r'<link\b[^>]*renew-stitch-v1\.css[^>]*>', text, re.I)
    if not link:
        print("renew-stitch-v1.css referansi bulunamadi")
        return 1
    cut = link.end()
    print(f"renew-stitch-v1.css referansi: satir "
          f"{text.count(chr(10), 0, link.start()) + 1}\n")

    # Bu noktadan SONRAKI satir-ici <style> bloklari
    later = []
    pos = cut
    while True:
        m = OPEN_STYLE.search(text, pos)
        if not m:
            break
        c = CLOSE_STYLE.search(text, m.end())
        if not c:
            break
        later.append((text.count(chr(10), 0, m.start()) + 1,
                      text[m.end():c.start()]))
        pos = c.end()

    print(f"stitch'ten SONRA gelen satir-ici <style> blogu: {len(later)}")
    for ln, body in later:
        print(f"  satir {ln:>5}  {len(body)/1024:>5.1f} KB")

    stitch_sels = selectors(STITCH.read_text(encoding="utf-8", errors="replace"))
    print(f"\nrenew-stitch-v1.css icindeki secici: {len(stitch_sels)}")

    later_sels = defaultdict(list)
    for ln, body in later:
        for sel in selectors(body):
            later_sels[sel].append(ln)

    collisions = sorted(set(stitch_sels) & set(later_sels))
    print(f"satir-ici bloklardaki secici     : {len(later_sels)}")
    print(f"\nCAKISAN SECICI: {len(collisions)}\n")
    for sel in collisions:
        lines = ", ".join(str(x) for x in sorted(set(later_sels[sel])))
        print(f"  {sel[:60]:<60} stitch'te {stitch_sels[sel]}x -> satir {lines}")

    if not collisions:
        print("  cakisma yok - stitch stilleri eziliyor gorunmuyor")
    return 0


if __name__ == "__main__":
    sys.exit(main())

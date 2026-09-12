"""HTML ayristirici davranisini taklit eden dogru script/style dogrulayicisi.

Onemli: tarayici bir <script> blogunu YALNIZCA `</script` dizisini gorunce bitirir.
Blok govdesindeki `<script>` metni etiket degildir. Bu yuzden acilis etiketlerini
saymak yanlis sonuc verir; govdeyi atlayarak ilerlemek gerekir.

Ayrica her satir-ici script'in JS sozdizimini `node --check` ile dogrular ve
stil siralamasini (harici stylesheet vs satir-ici <style>) raporlar.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

OPEN_SCRIPT = re.compile(r"<script\b([^>]*)>", re.I)
CLOSE_SCRIPT = re.compile(r"</script\s*>", re.I)
OPEN_STYLE = re.compile(r"<style\b[^>]*>", re.I)
CLOSE_STYLE = re.compile(r"</style\s*>", re.I)
SRC_ATTR = re.compile(r"""\bsrc\s*=\s*["']([^"']+)["']""", re.I)


def line_of(text, idx):
    return text.count("\n", 0, idx) + 1


def scan_scripts(text):
    """Ayristirici gibi ilerle: her acilistan sonra ilk kapanisa atla."""
    blocks = []
    pos = 0
    while True:
        m = OPEN_SCRIPT.search(text, pos)
        if not m:
            break
        attrs = m.group(1)
        body_start = m.end()
        c = CLOSE_SCRIPT.search(text, body_start)
        if not c:
            blocks.append({
                "line": line_of(text, m.start()), "attrs": attrs.strip(),
                "closed": False, "body": text[body_start:], "src": None,
            })
            break
        src = SRC_ATTR.search(attrs)
        blocks.append({
            "line": line_of(text, m.start()), "attrs": attrs.strip(),
            "closed": True, "body": text[body_start:c.start()],
            "src": src.group(1) if src else None,
        })
        pos = c.end()
    return blocks


def scan_styles(text):
    blocks = []
    pos = 0
    while True:
        m = OPEN_STYLE.search(text, pos)
        if not m:
            break
        c = CLOSE_STYLE.search(text, m.end())
        if not c:
            blocks.append({"line": line_of(text, m.start()), "closed": False,
                           "start": m.start(), "size": len(text) - m.end()})
            break
        blocks.append({"line": line_of(text, m.start()), "closed": True,
                       "start": m.start(), "size": c.start() - m.end()})
        pos = c.end()
    return blocks


def check_js(body):
    node = shutil.which("node")
    if not node:
        return None
    if not body.strip():
        return "bos"
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                     encoding="utf-8") as fh:
        fh.write(body)
        tmp = fh.name
    try:
        r = subprocess.run([node, "--check", tmp], capture_output=True, text=True)
        if r.returncode == 0:
            return "OK"
        err = (r.stderr or "").strip().splitlines()
        detail = next((l for l in err if "SyntaxError" in l), err[-1] if err else "?")
        return "HATA: " + detail[:120]
    finally:
        Path(tmp).unlink(missing_ok=True)


def main():
    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8", errors="replace")
    print(f"dosya: {path.name}   {len(text)/1024:.0f} KB\n")

    scripts = scan_scripts(text)
    inline = [b for b in scripts if not b["src"]]
    external = [b for b in scripts if b["src"]]
    unclosed = [b for b in scripts if not b["closed"]]

    print(f"script blogu   : {len(scripts)}  ({len(external)} harici, {len(inline)} satir-ici)")
    print(f"kapanmamis     : {len(unclosed)}"
          + ("  <-- SORUN" if unclosed else "  -> hepsi kapali"))
    for b in unclosed:
        print(f"    satir {b['line']}: <script {b['attrs']}>")

    print("\n--- satir-ici script JS sozdizimi ---")
    bad = 0
    for b in inline:
        res = check_js(b["body"])
        tag = f"<script {b['attrs']}>" if b["attrs"] else "<script>"
        size = len(b["body"]) / 1024
        if res and res.startswith("HATA"):
            bad += 1
        print(f"  satir {b['line']:>5}  {tag[:44]:<44} {size:>6.1f} KB  {res}")
    print(f"\n  sozdizimi hatali blok: {bad}")

    styles = scan_styles(text)
    unclosed_s = [b for b in styles if not b["closed"]]
    total_css = sum(b["size"] for b in styles)
    print(f"\n--- <style> ---")
    print(f"blok sayisi: {len(styles)}   kapanmamis: {len(unclosed_s)}   "
          f"toplam satir-ici CSS: {total_css/1024:.0f} KB")

    print("\n--- yukleme sirasi (kim kimi eziyor) ---")
    events = []
    for m in re.finditer(r'<link\b[^>]*\brel\s*=\s*["\']?stylesheet["\']?[^>]*>', text, re.I):
        href = re.search(r"""\bhref\s*=\s*["']([^"']+)["']""", m.group(0), re.I)
        events.append((m.start(), "harici CSS", href.group(1) if href else "?"))
    for b in styles:
        events.append((b["start"], "satir-ici <style>", f"{b['size']/1024:.0f} KB"))
    events.sort()
    for pos, kind, what in events:
        print(f"  satir {line_of(text, pos):>5}  {kind:<18} {what}")

    last_link = max((p for p, k, _ in events if k == "harici CSS"), default=None)
    last_style = max((p for p, k, _ in events if k == "satir-ici <style>"), default=None)
    if last_link is not None and last_style is not None:
        print()
        if last_style > last_link:
            print("  SONUC: son satir-ici <style>, son harici stylesheet'ten SONRA geliyor.")
            print("         Ayni ozgulluk seviyesinde satir-ici CSS harici dosyayi EZER.")
        else:
            print("  SONUC: harici stylesheet en sonda; satir-ici stilleri eziyor.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

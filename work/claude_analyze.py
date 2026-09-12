"""Yedek uzerinde olu dosya / tekrar / butunluk analizi. Canliya dokunmaz."""
import re
import sys
import tarfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKUP = ROOT / "backups" / "RENEW_FULL_BACKUP_20260911_101129"
WORK = ROOT / "tmp" / "analiz"


def extract():
    if WORK.exists():
        import shutil
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    links = []
    for name in ("app_live.tar.gz", "kart_site.tar.gz"):
        with tarfile.open(BACKUP / name) as tf:
            members = []
            for m in tf.getmembers():
                if m.issym() or m.islnk():
                    links.append((m.name, m.linkname))
                    continue
                members.append(m)
            tf.extractall(WORK, members=members, filter="data")
    if links:
        print("Arsivdeki sembolik baglantilar (acilmadi):")
        for src, dst in links:
            print(f"  {src} -> {dst}")
    return WORK / "app_live" / "app", WORK / "kart.renewpanel.xyz"


def h(title):
    print("\n" + "=" * 64)
    print("== " + title)
    print("=" * 64)


def analyze_static(app):
    static = app / "static"
    index = (static / "index.html").read_text(encoding="utf-8", errors="replace")
    referenced = set(re.findall(r'/static/([A-Za-z0-9_.\-]+\.(?:css|js))', index))
    on_disk = {p.name for p in static.iterdir() if p.is_file()}

    h("1. OLU STATIK DOSYALAR (index.html referans vermiyor)")
    dead = sorted(n for n in on_disk
                  if n not in referenced
                  and n.endswith(('.css', '.js', '.html')))
    total = 0
    for n in dead:
        size = (static / n).stat().st_size
        total += size
        flag = ""
        if '.bak' in n:
            flag = "  <-- YEDEK DOSYASI, /static/ uzerinden herkese acik"
        elif n.endswith('.html'):
            flag = "  <-- ayri sayfa, dogrudan acilabilir"
        print(f"  {size:>9,}  {n}{flag}")
    print(f"\n  toplam {len(dead)} dosya, {total/1024:.0f} KB")

    h("2. EKSIK REFERANS (index.html cagiriyor ama dosya yok -> 404)")
    missing = sorted(referenced - on_disk)
    if missing:
        for n in missing:
            print(f"  EKSIK: {n}")
    else:
        print("  yok - referans verilen 44 dosyanin tamami mevcut")

    return static, referenced, on_disk


def analyze_css(static, referenced):
    h("3. TEKRARLANAN CSS SECICILERI (sonraki tanim oncekini eziyor)")
    sel_files = defaultdict(list)
    for name in sorted(referenced):
        if not name.endswith('.css'):
            continue
        text = (static / name).read_text(encoding="utf-8", errors="replace")
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
        for m in re.finditer(r'(^|[}\n])\s*([^{}@\n][^{}]{0,200}?)\s*\{', text):
            sel = m.group(2).strip()
            if not sel or sel.startswith('@') or len(sel) > 120:
                continue
            for part in sel.split(','):
                part = part.strip()
                if part:
                    sel_files[part].append(name)

    worst = sorted(((len(v), k, Counter(v)) for k, v in sel_files.items()
                    if len(v) >= 4), reverse=True)[:20]
    for count, sel, files in worst:
        spread = len(files)
        print(f"  {count:>3}x  {sel[:58]:<58} ({spread} dosyada)")
    print(f"\n  4+ kez tanimlanan secici sayisi: "
          f"{sum(1 for v in sel_files.values() if len(v) >= 4)}")


def analyze_js(static, referenced):
    h("4. TEKRARLANAN JS FONKSIYONLARI")
    fn_files = defaultdict(list)
    for name in sorted(referenced):
        if not name.endswith('.js'):
            continue
        text = (static / name).read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r'(?:^|\n)\s*(?:async\s+)?function\s+([A-Za-z_$][\w$]*)', text):
            fn_files[m.group(1)].append(name)
        for m in re.finditer(r'(?:^|\n)\s*(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:function\b|\()', text):
            fn_files[m.group(1)].append(name)

    dupes = sorted(((len(v), k, v) for k, v in fn_files.items() if len(v) > 1),
                   reverse=True)[:20]
    for count, fn, files in dupes:
        uniq = sorted(set(files))
        where = ", ".join(uniq) if len(uniq) > 1 else f"{uniq[0]} (ayni dosyada {count}x)"
        print(f"  {count}x  {fn:<34} {where[:90]}")
    print(f"\n  birden fazla tanimlanan fonksiyon: "
          f"{sum(1 for v in fn_files.values() if len(v) > 1)}")


def analyze_html_integrity(static):
    h("5. HTML BUTUNLUGU")
    for name in ("index.html",):
        text = (static / name).read_text(encoding="utf-8", errors="replace")
        so, sc = len(re.findall(r'<script\b', text, re.I)), len(re.findall(r'</script\s*>', text, re.I))
        yo, yc = len(re.findall(r'<style\b', text, re.I)), len(re.findall(r'</style\s*>', text, re.I))
        print(f"  {name}: <script> {so}/{sc}   <style> {yo}/{yc}   "
              f"{'DENGELI' if so == sc and yo == yc else 'DENGESIZ !!'}")
        inline = sum(len(m) for m in re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', text, re.S | re.I))
        print(f"  index.html icindeki satir-ici script: {inline/1024:.1f} KB")


def analyze_py(app):
    h("6. IMPORT EDILMEYEN PYTHON MODULLERI")
    mods = {p.stem: p for p in app.glob("*.py") if p.stem != "__init__"}
    all_text = "\n".join(p.read_text(encoding="utf-8", errors="replace")
                         for p in app.glob("*.py"))
    for stem in sorted(mods):
        if stem == "main":
            continue
        used = re.search(rf'\b(?:from|import)\s+\.?{re.escape(stem)}\b', all_text)
        if not used:
            print(f"  kullanilmiyor gibi: {stem}.py ({mods[stem].stat().st_size:,} bayt)")
    print("  (main.py giris noktasi, listelenmez)")


def analyze_kart(kart):
    h("7. KART SITESI")
    index = (kart / "index.html").read_text(encoding="utf-8", errors="replace")
    print(f"  index.html: {len(index)/1024:.0f} KB")
    so, sc = len(re.findall(r'<script\b', index, re.I)), len(re.findall(r'</script\s*>', index, re.I))
    yo, yc = len(re.findall(r'<style\b', index, re.I)), len(re.findall(r'</style\s*>', index, re.I))
    print(f"  <script> {so}/{sc}   <style> {yo}/{yc}   "
          f"{'DENGELI' if so == sc and yo == yc else 'DENGESIZ !!'}")
    inline_css = sum(len(m) for m in re.findall(r'<style[^>]*>(.*?)</style>', index, re.S | re.I))
    inline_js = sum(len(m) for m in re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', index, re.S | re.I))
    print(f"  satir-ici CSS: {inline_css/1024:.0f} KB    satir-ici JS: {inline_js/1024:.0f} KB")

    refs = set(re.findall(r'(?:src|href)="([A-Za-z0-9_.\-]+\.(?:css|js))"', index))
    on_disk = {p.name for p in kart.iterdir() if p.is_file() and p.suffix in ('.css', '.js')}
    print(f"\n  index.html'in cagirdigi: {sorted(refs)}")
    print(f"  diskte olan             : {sorted(on_disk)}")
    dead = sorted(on_disk - refs)
    if dead:
        print(f"  OLU: {dead}")

    print("\n  web kokundeki alt klasorler (herkese acik):")
    for d in sorted(p for p in kart.iterdir() if p.is_dir()):
        n = len(list(d.rglob('*')))
        print(f"    {d.name}/  ({n} dosya)  <-- disaridan erisilebilir")

    # Tekrarlanan CSS blogu tespiti
    blocks = re.findall(r'<style[^>]*>(.*?)</style>', index, re.S | re.I)
    if len(blocks) > 1:
        print(f"\n  {len(blocks)} ayri <style> blogu var - patch birikimi gostergesi")
    sels = Counter()
    for b in blocks:
        b = re.sub(r'/\*.*?\*/', '', b, flags=re.S)
        for m in re.finditer(r'(^|[}\n])\s*([^{}@\n][^{}]{0,200}?)\s*\{', b):
            for part in m.group(2).split(','):
                part = part.strip()
                if part and len(part) < 100:
                    sels[part] += 1
    top = [(c, s) for s, c in sels.most_common(12) if c >= 3]
    if top:
        print("\n  satir-ici CSS'te en cok tekrarlanan seciciler:")
        for c, s in top:
            print(f"    {c:>3}x  {s[:60]}")


def main():
    app, kart = extract()
    static, referenced, on_disk = analyze_static(app)
    analyze_css(static, referenced)
    analyze_js(static, referenced)
    analyze_html_integrity(static)
    analyze_py(app)
    analyze_kart(kart)
    print("\n" + "=" * 64)
    print("Analiz tamamlandi. Hicbir canli dosyaya dokunulmadi.")


if __name__ == "__main__":
    sys.exit(main())

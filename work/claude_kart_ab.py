"""A/B test dizinlerini sifirdan kurar: yamali vs degistirilmemis canli.

Her ikisine de sayfa-basi hata yakalayici enjekte edilir (sadece olcum icin,
dagitilacak dosyalara girmez). Sonda/probe kullanilmaz.
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STAGE = ROOT / "kart_clean"
ASSETS = ROOT.parent / "tmp" / "analiz" / "kart.renewpanel.xyz"

PATCHED_DIR = STAGE / "ab_patched"
LIVE_DIR = STAGE / "ab_live"

EDITED = ["index.html", "kart-console-v1.js", "kart-interactive-v4.js",
          "renew-stitch-v1.js", "renew-stitch-details.js"]

CAPTURE = (
    "<script>window.__errs=[];"
    "window.addEventListener('error',function(e){"
    "window.__errs.push({msg:e.message,"
    "file:(e.filename||'').split('/').pop(),line:e.lineno,col:e.colno,"
    "stack:e.error&&e.error.stack?String(e.error.stack).slice(0,500):null})},true);"
    "window.addEventListener('unhandledrejection',function(e){"
    "window.__errs.push({msg:'unhandledrejection: '+e.reason})});"
    "</script>"
)


def build(target, source_of_edited):
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    for f in ASSETS.iterdir():
        if f.is_file():
            shutil.copy2(f, target / f.name)
    for name in EDITED:
        shutil.copy2(source_of_edited / name, target / name)

    idx = target / "index.html"
    text = idx.read_text(encoding="utf-8")
    i = text.lower().find("<head>")
    if i == -1:
        raise RuntimeError("<head> bulunamadi: " + str(idx))
    text = text[:i + 6] + CAPTURE + text[i + 6:]
    idx.write_text(text, encoding="utf-8", newline="")
    return len(list(target.iterdir()))


def main():
    n1 = build(PATCHED_DIR, STAGE)          # yamali calisma kopyalari
    n2 = build(LIVE_DIR, STAGE / "live")    # degistirilmemis canli
    print(f"ab_patched: {n1} dosya  ->  {PATCHED_DIR}")
    print(f"ab_live   : {n2} dosya  ->  {LIVE_DIR}")
    print("\nYakalayici yalnizca bu A/B dizinlerinde; dagitilacak dosyalarda yok.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

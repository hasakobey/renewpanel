"""TANI AMACLI: test kopyasindaki defer script'lerin init() basina durum sondasi ekler.

Sadece work/kart_clean/test icinde calisir. Canliya ve calisma kopyalarina dokunmaz.
"""
import sys
from pathlib import Path

TEST = Path(__file__).resolve().parent / "kart_clean" / "test"

TARGETS = [
    "kart-console-v1.js",
    "kart-interactive-v4.js",
    "renew-stitch-v1.js",
    "renew-stitch-details.js",
]

PROBE = (
    "window.__renewProbe=window.__renewProbe||[];"
    "window.__renewProbe.push({script:'%s',readyState:document.readyState,"
    "rcWorkspace:!!document.querySelector('.rc-workspace'),"
    "rcHistory:!!document.getElementById('rcHistory'),"
    "rcCompareBody:!!document.getElementById('rcCompareBody'),"
    "rcMiniActions:!!document.querySelector('.rc-mini-actions'),"
    "t:Math.round(performance.now())});"
)

ANCHOR = "function init(){"


def main():
    for name in TARGETS:
        path = TEST / name
        text = path.read_text(encoding="utf-8")
        if ANCHOR not in text:
            print(f"{name}: '{ANCHOR}' bulunamadi, atlandi")
            continue
        probe = PROBE % name
        text = text.replace(ANCHOR, ANCHOR + probe, 1)
        path.write_text(text, encoding="utf-8", newline="")
        print(f"{name}: sonda eklendi")
    print("\nSonda yalnizca test dizininde. Sayfayi acip window.__renewProbe'a bak.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

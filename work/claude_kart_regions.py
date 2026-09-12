"""Kapanmamis script bloklarinin sinirlarini incelemek icin bolge yazdirici."""
import sys
from pathlib import Path

DEFAULT = Path(__file__).resolve().parent / "kart_clean" / "index.work.html"

REGIONS = [
    ("A blogu acilis", 2347, 2356),
    ("A blogu bitisi / B acilisi", 2732, 2748),
    ("B blogu bitisi", 3044, 3054),
    ("C blogu (fin-kredi-pdf) acilis", 3150, 3160),
    ("C blogu bitisi / D acilisi", 3252, 3274),
]


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    for title, start, end in REGIONS:
        print("\n" + "=" * 70)
        print(f"== {title}   (satir {start}-{end})")
        print("=" * 70)
        for n in range(start, min(end + 1, len(lines)) + 1):
            if n - 1 < len(lines):
                text = lines[n - 1]
                if len(text) > 150:
                    text = text[:150] + " ...[kisaltildi]"
                print(f"{n:>5} | {text}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""index.html icindeki satir-ici script bloklarini ayri dosyalara cikarir (inceleme icin)."""
import re
import sys
from pathlib import Path

STAGE = Path(__file__).resolve().parent / "kart_clean"
OUT = STAGE / "inline"

PATTERN = re.compile(r"<script(?![^>]*\bsrc=)([^>]*)>(.*?)</script\s*>", re.S | re.I)


def main():
    src = STAGE / "live" / "index.html"
    text = src.read_text(encoding="utf-8", errors="replace")
    OUT.mkdir(parents=True, exist_ok=True)

    for i, m in enumerate(PATTERN.finditer(text), 1):
        line = text.count("\n", 0, m.start()) + 1
        attrs = m.group(1).strip()
        ident = re.search(r'id\s*=\s*["\']([^"\']+)["\']', attrs)
        name = ident.group(1) if ident else f"anon{i}"
        path = OUT / f"{i:02d}_{name}_satir{line}.js"
        path.write_text(m.group(2), encoding="utf-8")
        print(f"{path.name:<46} {len(m.group(2)):>7,} karakter  satir {line}")

    print(f"\ncikarildi -> {OUT}")

    # rcHistory nerede olusuyor
    print("\n=== 'rcHistory' gecen yerler ===")
    for path in sorted(OUT.glob("*.js")):
        body = path.read_text(encoding="utf-8")
        for m in re.finditer(r".{0,90}rcHistory.{0,90}", body, re.S):
            frag = " ".join(m.group(0).split())
            print(f"  {path.name}:")
            print(f"    ...{frag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

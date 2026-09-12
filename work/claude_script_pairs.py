"""kart index.html icindeki <script> acilis/kapanis eslemesini dogrular."""
import re
import sys
from pathlib import Path

DEFAULT = (Path(__file__).resolve().parent.parent
           / "tmp" / "analiz" / "kart.renewpanel.xyz" / "index.html")


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    text = path.read_text(encoding="utf-8", errors="replace")
    toks = [(m.start(), m.group(0))
            for m in re.finditer(r"<script\b[^>]*>|</script\s*>", text, re.I)]

    def line(i):
        return text.count("\n", 0, i) + 1

    print(f"dosya: {path.name}  ({len(text)/1024:.0f} KB)\n")
    unclosed = []
    i = 0
    while i < len(toks):
        pos, tag = toks[i]
        if tag.lower().startswith("</"):
            print(f"  !  satir {line(pos):>5}  FAZLA KAPANIS")
            i += 1
            continue
        short = tag if len(tag) <= 62 else tag[:62] + "..."
        if i + 1 < len(toks) and toks[i + 1][1].lower().startswith("</"):
            print(f"  OK   satir {line(pos):>5}  {short:<66} kapanis {line(toks[i+1][0])}")
            i += 2
        else:
            print(f"  HATA satir {line(pos):>5}  {short:<66} KAPANIS YOK")
            unclosed.append((line(pos), tag))
            i += 1

    print(f"\nkapanmamis <script>: {len(unclosed)}")
    for ln, tag in unclosed:
        print(f"  satir {ln}: {tag[:90]}")

    if unclosed:
        first = unclosed[0][0]
        print(f"\nTarayici ilk kapanmamis script'ten ({first}. satir) sonrasini")
        print("o script'in govdesi sayar; sonraki tum HTML ve script'ler calismaz.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

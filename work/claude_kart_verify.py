"""Yamali calisma kopyalarini canli surumle karsilastirir. Sadece beklenen fark olmali."""
import difflib
import sys
from pathlib import Path

STAGE = Path(__file__).resolve().parent / "kart_clean"
LIVE = STAGE / "live"

FILES = ["index.html", "kart-console-v1.js", "kart-interactive-v4.js",
         "renew-stitch-v1.js", "renew-stitch-details.js"]

CRLF = b"\r\n"
BOM = b"\xef\xbb\xbf"
NL = chr(10)


def main():
    total = 0
    for name in FILES:
        live_b = (LIVE / name).read_bytes()
        new_b = (STAGE / name).read_bytes()
        live_t = live_b.decode("utf-8", errors="replace")
        new_t = new_b.decode("utf-8", errors="replace")

        print("=" * 70)
        print("== " + name)
        print("=" * 70)
        print("  bayt : {:,} -> {:,}  ({:+,})".format(
            len(live_b), len(new_b), len(new_b) - len(live_b)))
        print("  satir: {:,} -> {:,}".format(
            live_t.count(NL) + 1, new_t.count(NL) + 1))
        print("  CRLF : canli {}  yeni {}".format(
            live_b.count(CRLF), new_b.count(CRLF)))
        print("  BOM  : " + ("VAR - SORUN" if new_b.startswith(BOM) else "yok"))

        diff = list(difflib.unified_diff(
            live_t.splitlines(), new_t.splitlines(),
            lineterm="", n=0, fromfile="canli", tofile="yeni"))
        body = [d for d in diff
                if d.startswith(("+", "-")) and not d.startswith(("+++", "---"))]
        print("  degisen satir: {}".format(len(body)))
        total += len(body)
        for d in body[:16]:
            content = d[1:].strip()
            if len(content) > 140:
                content = content[:140] + " ...[kisaltildi]"
            print("    {} {}".format(d[0], content))
        if len(body) > 16:
            print("    ... {} satir daha".format(len(body) - 16))
        print()

    print("TOPLAM degisen satir: {}".format(total))
    return 0


if __name__ == "__main__":
    sys.exit(main())

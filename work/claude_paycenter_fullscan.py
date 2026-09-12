"""app.js'de payment-center ile ilgili TUM izleri (fonksiyon adi varyasyonlari
dahil) bulur. Ilk taramada 2 fonksiyon bulundu ama 2 kalinti daha cikti;
bu yuzden kapsamli bir tarama gerekiyor."""
import re
import sys
from pathlib import Path

STAGE = Path(__file__).resolve().parent / "paycenter_clean"

NEEDLES = ["paymentCenterFrame", "PaymentCenter", "payment-center",
           "syncPaymentFrameHeight", "PaymentFrameHeight", "openPaymentCenter"]


def main():
    js = (STAGE / "app.js").read_text(encoding="utf-8")
    print(f"app.js: {len(js):,} bayt (bu ANDAKI - reloadPaymentCenter/openPaymentCenterNewTab zaten kaldirilmis)\n")

    hits = []
    for needle in NEEDLES:
        for m in re.finditer(re.escape(needle), js):
            hits.append(m.start())
    hits = sorted(set(hits))

    print(f"toplam eslesme konumu: {len(hits)}\n")

    # yakin konumlari grupla (200 karakter icinde ise ayni blok)
    groups = []
    for pos in hits:
        if groups and pos - groups[-1][-1] < 200:
            groups[-1].append(pos)
        else:
            groups.append([pos])

    for i, g in enumerate(groups, 1):
        start = max(0, g[0] - 150)
        end = min(len(js), g[-1] + 250)
        line = js.count("\n", 0, g[0]) + 1
        print(f"--- grup {i}  (satir ~{line}) ---")
        print(js[start:end])
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

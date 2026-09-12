"""Adim 2: sifir-referans, halka acik dosyalari karantinaya tasir. SILMEZ.

Kapsam (dogrulandi -> claude_quarantine_check.py):
  - RENEW PRO static/*.bak_* (kod icinde referans yok, trafik ~1 istek = test)
  - kart.renewpanel.xyz/demo/ ve /backups/ (nginx'te ozel tanim yok, dusuk trafik)

payment_center.html / payment_hub.html BU ADIMA DAHIL DEGIL: payment_center.html
canli iframe tarafindan hala cekiliyor (haftada 109 istek); once index.html/app.js
uzerinde ayri bir temizlik gerekiyor.
"""
import sys
from datetime import datetime

from claude_conn import ssh, run

STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
QUARANTINE = f"/root/QUARANTINE_{STAMP}"

STATIC = "/opt/renewpro/app_live/app/static"
KART = "/var/www/kart.renewpanel.xyz"

MOVES = [
    (f"{STATIC}/app.js.bak_20260902_155437", "renewpro/app.js.bak_20260902_155437"),
    (f"{STATIC}/app.js.bak_20260902_154344", "renewpro/app.js.bak_20260902_154344"),
    (f"{STATIC}/index.html.bak_20260902_155437", "renewpro/index.html.bak_20260902_155437"),
    (f"{STATIC}/index.html.bak_20260902_154344", "renewpro/index.html.bak_20260902_154344"),
    (f"{STATIC}/renew_media_picker_v2.js.bak_20260902_154344", "renewpro/renew_media_picker_v2.js.bak_20260902_154344"),
    (f"{STATIC}/renew_forms_v1.css.bak_20260902_155437", "renewpro/renew_forms_v1.css.bak_20260902_155437"),
    (f"{KART}/demo", "kart/demo"),
    (f"{KART}/backups", "kart/backups"),
]


def main():
    client = ssh()
    try:
        run(client, f"mkdir -p {QUARANTINE}/renewpro {QUARANTINE}/kart")

        print("=== tasima oncesi son kontrol (curl 200/404) ===")
        checks = [
            ("app.js.bak_155437", "https://renewpanel.xyz/static/app.js.bak_20260902_155437"),
            ("index.html.bak_155437", "https://renewpanel.xyz/static/index.html.bak_20260902_155437"),
            ("kart /demo/", "https://kart.renewpanel.xyz/demo/"),
        ]
        for label, url in checks:
            _, out, _ = run(client, f"curl -s -o /dev/null -w '%{{http_code}}' {url}", check=False)
            print(f"  {label:<24} tasima oncesi: {out.strip()}")

        print("\n=== tasima ===")
        for src, dst in MOVES:
            code, out, err = run(client, f"test -e {src} && echo VAR || echo YOK", check=False)
            if out.strip() != "VAR":
                print(f"  {src:<70} zaten yok, atlandi")
                continue
            run(client, f"mv {src} {QUARANTINE}/{dst}")
            print(f"  {src}")
            print(f"    -> {QUARANTINE}/{dst}")

        print("\n=== tasima sonrasi kontrol (404 beklenir) ===")
        for label, url in checks:
            _, out, _ = run(client, f"curl -s -o /dev/null -w '%{{http_code}}' {url}", check=False)
            ok = out.strip() == "404"
            print(f"  {label:<24} tasima sonrasi: {out.strip()}  {'OK' if ok else 'BEKLENMEDIK - hala erisiliyor!'}")

        print("\n=== ana site kontrolleri (etkilenmemeli) ===")
        main_checks = [
            ("renewpanel https", "https://renewpanel.xyz/"),
            ("kart https", "https://kart.renewpanel.xyz/"),
            ("biziz", "https://renewpanel.xyz/biziz/"),
        ]
        for label, url in main_checks:
            _, out, _ = run(client, f"curl -s -o /dev/null -w '%{{http_code}}' {url}", check=False)
            print(f"  {label:<20} {out.strip()}")

        run(client, f"cd {QUARANTINE} && find . -type f -exec sha256sum {{}} \\; > SHA256SUMS.txt")
        _, out, _ = run(client, f"du -sh {QUARANTINE} | cut -f1")
        print(f"\nKARANTINA: {QUARANTINE}  ({out.strip()})")
        _, out, _ = run(client, f"find {QUARANTINE} -type f | sort")
        print(out.rstrip())
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

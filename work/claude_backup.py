"""Tam sistem yedegi: uygulama + veritabani + nginx + systemd + kart sitesi + medya.

/biziz'e dokunulmaz. Sembolik baglantilar takip edilir (data dizini symlink).
"""
import sys
from datetime import datetime

from claude_conn import ssh, run

STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BASE = f"/root/RENEW_FULL_BACKUP_{STAMP}"

PARTS = [
    ("app_live.tar.gz",
     "tar -czf {b}/app_live.tar.gz --exclude='.venv' --exclude='__pycache__' "
     "--exclude='vehicle_media' -C /opt/renewpro app_live"),
    ("data.tar.gz",
     "tar -czhf {b}/data.tar.gz -C /var/lib/renewpro data"),
    ("vehicle_media.tar.gz",
     "tar -czhf {b}/vehicle_media.tar.gz -C /opt/renewpro/app_live vehicle_media "
     "2>/dev/null || echo 'vehicle_media yok'"),
    ("kart_site.tar.gz",
     "tar -czf {b}/kart_site.tar.gz -C /var/www kart.renewpanel.xyz"),
    ("nginx.tar.gz",
     "tar -czf {b}/nginx.tar.gz -C /etc/nginx sites-available sites-enabled nginx.conf"),
    ("systemd.tar.gz",
     "tar -czhf {b}/systemd.tar.gz -C /etc/systemd/system renewpro.service"),
]


def main():
    client = ssh()
    try:
        print(f"Yedek dizini: {BASE}\n")
        run(client, f"mkdir -p {BASE}")

        # Yedek oncesi DB butunlugu
        _, out, _ = run(
            client,
            "/opt/renewpro/.venv/bin/python -c \"import sqlite3;"
            "c=sqlite3.connect('/var/lib/renewpro/data/renew.db');"
            "print(c.execute('PRAGMA integrity_check').fetchone()[0])\"",
            check=False,
        )
        print("DB butunlugu (yedek oncesi):", out.strip())

        # Tutarli DB kopyasi (canli yazma sirasinda bozulmasin)
        run(client,
            "/opt/renewpro/.venv/bin/python -c \"import sqlite3;"
            f"s=sqlite3.connect('/var/lib/renewpro/data/renew.db');"
            f"d=sqlite3.connect('{BASE}/renew.db');s.backup(d);d.close();s.close()\"")
        print("renew.db  -> tutarli kopya alindi")

        for name, tmpl in PARTS:
            code, out, err = run(client, tmpl.format(b=BASE), check=False)
            _, size, _ = run(client, f"du -h {BASE}/{name} 2>/dev/null | cut -f1", check=False)
            status = size.strip() or "OLUSMADI"
            print(f"{name:24s} -> {status}")
            if err.strip() and "vehicle_media yok" not in err:
                print("   uyari:", err.strip()[:200])

        # Manifest
        run(client, f"cd {BASE} && sha256sum * > SHA256SUMS.txt")
        run(client, f"chmod -R 600 {BASE}/renew.db {BASE}/data.tar.gz")

        _, out, _ = run(client, f"ls -la {BASE}")
        print("\n--- yedek icerigi ---")
        print(out.rstrip())

        _, out, _ = run(client, f"du -sh {BASE} | cut -f1")
        print("\nTOPLAM:", out.strip())

        # Dogrulama: arsivler acilabiliyor mu
        print("\n--- arsiv dogrulama ---")
        for name, _ in PARTS:
            code, out, _ = run(client, f"tar -tzf {BASE}/{name} > /dev/null 2>&1 && echo OK || echo BOZUK",
                               check=False)
            print(f"{name:24s} -> {out.strip()}")

        _, out, _ = run(
            client,
            f"/opt/renewpro/.venv/bin/python -c \"import sqlite3;"
            f"c=sqlite3.connect('{BASE}/renew.db');"
            "print('integrity', c.execute('PRAGMA integrity_check').fetchone()[0]);"
            "print('stok', c.execute('SELECT COUNT(*) FROM stock').fetchone()[0] if 1 else 0)\"",
            check=False,
        )
        print("\nYedekteki DB:", out.strip() or "kontrol edilemedi")
        print("\nYEDEK YOLU:", BASE)
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())

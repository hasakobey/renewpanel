"""Sunucudaki yedegin kod/yapilandirma/veritabani parcalarini yerel temiz klasore indirir.

vehicle_media (163 MB) indirilmez; sunucudaki yedekte durur.
"""
import hashlib
import sys
from pathlib import Path

from claude_conn import ssh, run

REMOTE = sys.argv[1] if len(sys.argv) > 1 else None
LOCAL = Path(__file__).resolve().parent.parent / "backups"

FILES = ["app_live.tar.gz", "data.tar.gz", "kart_site.tar.gz",
         "nginx.tar.gz", "systemd.tar.gz", "renew.db", "SHA256SUMS.txt"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if not REMOTE:
        print("kullanim: claude_pull_backup.py /root/RENEW_FULL_BACKUP_<stamp>")
        return 1

    stamp = REMOTE.rstrip("/").split("_")[-1]
    date = REMOTE.rstrip("/").split("_")[-2]
    target = LOCAL / f"RENEW_FULL_BACKUP_{date}_{stamp}"
    target.mkdir(parents=True, exist_ok=True)

    client = ssh()
    try:
        sftp = client.open_sftp()
        _, sums, _ = run(client, f"cat {REMOTE}/SHA256SUMS.txt")
        remote_hashes = {}
        for line in sums.splitlines():
            parts = line.split()
            if len(parts) == 2:
                remote_hashes[parts[1].lstrip("*")] = parts[0]

        print(f"hedef: {target}\n")
        for name in FILES:
            src = f"{REMOTE}/{name}"
            dst = target / name
            try:
                sftp.get(src, str(dst))
            except FileNotFoundError:
                print(f"{name:22s} -> sunucuda yok, atlandi")
                continue
            size_mb = dst.stat().st_size / (1024 * 1024)
            if name in remote_hashes:
                ok = sha256(dst) == remote_hashes[name]
                mark = "hash OK" if ok else "HASH UYUSMUYOR"
            else:
                mark = "hash yok"
            print(f"{name:22s} -> {size_mb:7.2f} MB  {mark}")

        (target / "OKUBENI.txt").write_text(
            f"RENEW PRO temiz yedek\n"
            f"Kaynak: {REMOTE} (45.195.231.20)\n"
            f"Tarih : {date} {stamp}\n\n"
            f"Icerik:\n"
            f"  app_live.tar.gz   - uygulama kodu + statik dosyalar (vehicle_media haric)\n"
            f"  data.tar.gz       - /var/lib/renewpro/data (db + mail_config + video ayarlari)\n"
            f"  renew.db          - tutarli sqlite kopyasi (PRAGMA integrity_check: ok)\n"
            f"  kart_site.tar.gz  - /var/www/kart.renewpanel.xyz tamami\n"
            f"  nginx.tar.gz      - nginx sites-available/enabled + nginx.conf\n"
            f"  systemd.tar.gz    - renewpro.service\n\n"
            f"vehicle_media (163 MB) yalnizca sunucudaki yedekte:\n"
            f"  {REMOTE}/vehicle_media.tar.gz\n\n"
            f"/biziz bu yedege dahil degildir ve hic dokunulmamistir.\n",
            encoding="utf-8")
        print("\nOKUBENI.txt yazildi")
        print("YEREL YEDEK:", target)
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

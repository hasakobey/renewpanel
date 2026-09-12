"""Onceki hatali rollback sonrasi canlinin gercekten orijinal haline
dondugunu dogrular (salt okunur)."""
import hashlib
import sys
from pathlib import Path

from claude_conn import ssh

STAGE = Path(__file__).resolve().parent / "paycenter_clean"
STATIC = "/opt/renewpro/app_live/app/static"
FILES = ["index.html", "app.js", "style.css", "renew_dashboard_v26.css"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    client = ssh()
    try:
        sftp = client.open_sftp()
        for name in FILES:
            live = sftp.open(f"{STATIC}/{name}", "rb").read()
            original = (STAGE / "live" / name).read_bytes()
            match = sha(live) == sha(original)
            print(f"{name:<26} canli == orijinal (rollback oncesi hal): {'EVET' if match else 'HAYIR'}")
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

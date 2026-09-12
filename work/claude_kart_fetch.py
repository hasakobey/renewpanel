"""Kart sitesinin canli index.html'ini ceker ve yedekle karsilastirir. Salt okunur."""
import hashlib
import sys
from pathlib import Path

from claude_conn import ssh, run

ROOT = Path(__file__).resolve().parent.parent
STAGE = ROOT / "work" / "kart_clean"
REMOTE = "/var/www/kart.renewpanel.xyz/index.html"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    STAGE.mkdir(parents=True, exist_ok=True)
    client = ssh()
    try:
        sftp = client.open_sftp()
        live = STAGE / "index.live.html"
        sftp.get(REMOTE, str(live))
        data = live.read_bytes()
        print(f"canli index.html : {len(data):,} bayt")
        print(f"  SHA256         : {sha(data)}")

        _, out, _ = run(client, f"sha256sum {REMOTE}")
        print(f"  sunucu sha256  : {out.split()[0]}")
        print(f"  eslesme        : {'OK' if out.split()[0] == sha(data) else 'UYUSMUYOR'}")

        backup = ROOT / "tmp" / "analiz" / "kart.renewpanel.xyz" / "index.html"
        if backup.exists():
            same = sha(backup.read_bytes()) == sha(data)
            print(f"  yedekle ayni mi: {'EVET' if same else 'HAYIR - canli degismis'}")

        # Calisma kopyasi
        work = STAGE / "index.work.html"
        work.write_bytes(data)
        print(f"\ncalisma kopyasi: {work}")
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

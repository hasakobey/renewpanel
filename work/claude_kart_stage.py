"""Kart sitesinin duzenlenecek dosyalarini canlidan cekip calisma alanina koyar."""
import hashlib
import sys
from pathlib import Path

from claude_conn import ssh, run

ROOT = Path(__file__).resolve().parent
STAGE = ROOT / "kart_clean"
REMOTE_DIR = "/var/www/kart.renewpanel.xyz"

FILES = [
    "index.html",
    "kart-console-v1.js",
    "kart-interactive-v4.js",
    "renew-stitch-v1.js",
    "renew-stitch-details.js",
]


def main():
    STAGE.mkdir(parents=True, exist_ok=True)
    (STAGE / "live").mkdir(exist_ok=True)
    client = ssh()
    try:
        sftp = client.open_sftp()
        _, sums, _ = run(client, f"cd {REMOTE_DIR} && sha256sum " + " ".join(FILES))
        remote = {}
        for line in sums.splitlines():
            p = line.split()
            if len(p) == 2:
                remote[p[1]] = p[0]

        for name in FILES:
            src = f"{REMOTE_DIR}/{name}"
            live = STAGE / "live" / name
            sftp.get(src, str(live))
            data = live.read_bytes()
            local_hash = hashlib.sha256(data).hexdigest()
            ok = local_hash == remote.get(name)
            # duzenlenecek calisma kopyasi
            (STAGE / name).write_bytes(data)
            print(f"{name:<26} {len(data):>8,} bayt  hash {'OK' if ok else 'UYUSMUYOR'}")

        print("\n--- her JS dosyasinin calisma tetigi (son 160 karakter) ---")
        for name in FILES[1:]:
            text = (STAGE / name).read_text(encoding="utf-8", errors="replace")
            tail = text.rstrip()[-160:]
            print(f"\n{name}:\n  ...{tail}")
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""payment-center kaldirma: dosyalari canlidan cekip calisma alanina koyar."""
import hashlib
import sys
from pathlib import Path

from claude_conn import ssh, run

ROOT = Path(__file__).resolve().parent
STAGE = ROOT / "paycenter_clean"
STATIC = "/opt/renewpro/app_live/app/static"

FILES = ["index.html", "app.js", "style.css", "renew_dashboard_v26.css"]


def main():
    STAGE.mkdir(parents=True, exist_ok=True)
    (STAGE / "live").mkdir(exist_ok=True)
    client = ssh()
    try:
        sftp = client.open_sftp()
        _, sums, _ = run(client, f"cd {STATIC} && sha256sum " + " ".join(FILES))
        remote = {}
        for line in sums.splitlines():
            p = line.split()
            if len(p) == 2:
                remote[p[1]] = p[0]

        for name in FILES:
            live = STAGE / "live" / name
            sftp.get(f"{STATIC}/{name}", str(live))
            data = live.read_bytes()
            ok = hashlib.sha256(data).hexdigest() == remote.get(name)
            (STAGE / name).write_bytes(data)
            print(f"{name:<26} {len(data):>8,} bayt  hash {'OK' if ok else 'UYUSMUYOR'}")
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

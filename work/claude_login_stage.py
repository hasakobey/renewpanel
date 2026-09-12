"""Login yeniden tasarimi: canlidan index.html/app.js/style.css ceker."""
import hashlib, sys
from pathlib import Path
from claude_conn import ssh, run

STAGE = Path(__file__).resolve().parent / "login_clean"
STATIC = "/opt/renewpro/app_live/app/static"
FILES = ["index.html", "app.js", "style.css"]

def main():
    (STAGE / "live").mkdir(parents=True, exist_ok=True)
    client = ssh()
    try:
        sftp = client.open_sftp()
        _, sums, _ = run(client, f"cd {STATIC} && sha256sum " + " ".join(FILES))
        remote = {p.split()[1]: p.split()[0] for p in sums.splitlines() if len(p.split())==2}
        for name in FILES:
            live = STAGE / "live" / name
            sftp.get(f"{STATIC}/{name}", str(live))
            data = live.read_bytes()
            ok = hashlib.sha256(data).hexdigest() == remote.get(name)
            (STAGE / name).write_bytes(data)
            print(f"{name:<16} {len(data):>8,} bayt hash {'OK' if ok else 'UYUSMUYOR'}")
        # onsubmit bloklarini teyit
        _, out, _ = run(client, "grep -n \"loginForm').onsubmit\\|getElementById('loginForm')\" " + f"{STATIC}/app.js")
        print("\n--- grep onsubmit ---")
        print(out.rstrip())
    finally:
        client.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())

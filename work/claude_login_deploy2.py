"""Gorsel iyilestirme turu: index.html (kart mockup) + guncellenmis css/js.
app.js zaten onceki turda dagitildi, degismedi, bu turda dokunulmuyor."""
import hashlib, sys
from datetime import datetime
from pathlib import Path
from claude_conn import ssh, run

ROOT = Path(__file__).resolve().parent
STAGE = ROOT / "login_clean"
STATIC = "/opt/renewpro/app_live/app/static"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP = f"/opt/renewpro/backups/login_polish_{STAMP}"
FILES = ["index.html", "renew_login_switch_v1.css", "renew_login_switch_v1.js"]

def sha(d): return hashlib.sha256(d).hexdigest()

def main():
    payload = {n: (STAGE/n).read_bytes() for n in FILES}
    client = ssh()
    try:
        sftp = client.open_sftp()
        print("=== canli index.html teyit (onceki deploy'un ustune yaziliyor) ===")
        live_idx = sftp.open(f"{STATIC}/index.html","rb").read()
        prev_idx = (STAGE/"index.html").read_bytes()  # zaten guncel calisma kopyasi, karsilastirma icin onceki deploy sonrasi cekilecek
        _, out, _ = run(client, f"sha256sum {STATIC}/index.html")
        print("  canli hash:", out.split()[0][:16], "...")

        print("\n=== yedek ===")
        run(client, f"mkdir -p {BACKUP}")
        run(client, f"cp -p {STATIC}/index.html {STATIC}/renew_login_switch_v1.css {STATIC}/renew_login_switch_v1.js {BACKUP}/")
        print("YEDEK:", BACKUP)

        print("\n=== aktarim ===")
        for name in FILES:
            target = f"{STATIC}/{name}"; tmp = target+".new"
            with sftp.open(tmp,"wb") as fh: fh.write(payload[name])
            sftp.chmod(tmp, 0o644); sftp.posix_rename(tmp, target)
            print(f"  {name} aktarildi")

        print("\n=== hash dogrulama ===")
        ok = True
        _, out, _ = run(client, f"cd {STATIC} && sha256sum " + " ".join(FILES))
        remote = {p.split()[1]: p.split()[0] for p in out.splitlines() if len(p.split())==2}
        for name in FILES:
            m = remote.get(name)==sha(payload[name]); print(f"  {name}: {'OK' if m else 'UYUSMUYOR'}"); ok=ok and m

        code, out, err = run(client, "nginx -t", check=False)
        print("nginx -t:", "basarili" if code==0 else "HATA"); ok = ok and code==0
        _, out, _ = run(client, "curl -s -o /dev/null -w '%{http_code}' https://renewpanel.xyz/", check=False)
        print("ana panel:", out.strip()); ok = ok and out.strip()=="200"

        if not ok:
            print("\n!! GERI DONULUYOR")
            run(client, f"cp -p {BACKUP}/* {STATIC}/")
            return 1
        print("\n=== TAMAM ===")
        return 0
    finally:
        client.close()

if __name__ == "__main__":
    sys.exit(main())

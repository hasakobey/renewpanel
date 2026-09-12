"""Kart sitesi yamasini canliya alir: yedek -> atomik aktarim -> dogrulama -> gerekirse geri donus.

Dogrulanan degisiklik: 4 script'in tetigi window.load -> DOMContentLoaded,
surum (?v=) yukseltmeleri, 404 veren renew.ico <link> etiketinin kaldirilmasi.
Matematik, hesaplama fonksiyonlari ve oran tablolari DEGISMEDI.
"""
import hashlib
import sys
from datetime import datetime

from pathlib import Path
from claude_conn import ssh, run

ROOT = Path(__file__).resolve().parent
STAGE = ROOT / "kart_clean"
REMOTE_DIR = "/var/www/kart.renewpanel.xyz"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP = f"/root/KART_BEFORE_DCL_FIX_{STAMP}"

FILES = ["index.html", "kart-console-v1.js", "kart-interactive-v4.js",
         "renew-stitch-v1.js", "renew-stitch-details.js"]

FORBIDDEN = ["__errs", "__renewProbe", "127.0.0.1:889", "127.0.0.1:890"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    # 1. Guvenlik: tani amacli kod sizmis mi
    print("=== dagitim oncesi denetim ===")
    payload = {}
    for name in FILES:
        data = (STAGE / name).read_bytes()
        text = data.decode("utf-8", errors="replace")
        for bad in FORBIDDEN:
            if bad in text:
                print(f"DURDURULDU: {name} icinde tani kodu var -> {bad}")
                return 1
        payload[name] = data
        print(f"  {name:<26} {len(data):>8,} bayt  temiz")

    client = ssh()
    try:
        sftp = client.open_sftp()

        # 2. Canli hala bekledigimiz surumde mi
        print("\n=== canli surum kontrolu ===")
        for name in FILES:
            live = sftp.open(f"{REMOTE_DIR}/{name}", "rb").read()
            expected = (STAGE / "live" / name).read_bytes()
            if sha(live) != sha(expected):
                print(f"DURDURULDU: {name} canlida degismis. Once yeniden incele.")
                return 1
            print(f"  {name:<26} beklenen surum  OK")

        # 3. Yedek
        print("\n=== yedek ===")
        run(client, f"mkdir -p {BACKUP}")
        run(client, "cp -p " + " ".join(f"{REMOTE_DIR}/{n}" for n in FILES) + f" {BACKUP}/")
        run(client, f"cd {BACKUP} && sha256sum * > SHA256SUMS.txt")
        _, out, _ = run(client, f"ls -la {BACKUP}")
        print(out.rstrip())
        print(f"\nYEDEK: {BACKUP}")

        # 4. Atomik aktarim
        print("\n=== aktarim ===")
        for name in FILES:
            target = f"{REMOTE_DIR}/{name}"
            tmp = target + ".new"
            with sftp.open(tmp, "wb") as fh:
                fh.write(payload[name])
            sftp.chmod(tmp, 0o644)
            sftp.posix_rename(tmp, target)
            print(f"  {name:<26} aktarildi")

        # 5. Hash dogrulama
        print("\n=== hash dogrulama (yerel <-> canli) ===")
        ok = True
        _, out, _ = run(client, f"cd {REMOTE_DIR} && sha256sum " + " ".join(FILES))
        remote = {}
        for line in out.splitlines():
            p = line.split()
            if len(p) == 2:
                remote[p[1]] = p[0]
        for name in FILES:
            match = remote.get(name) == sha(payload[name])
            print(f"  {name:<26} {'OK' if match else 'UYUSMUYOR'}")
            ok = ok and match

        # 6. Nginx + HTTP
        print("\n=== servis kontrolleri ===")
        code, out, err = run(client, "nginx -t", check=False)
        print("  nginx -t:", "basarili" if code == 0 else "BASARISIZ")
        if code != 0:
            print(err.strip())
            ok = False

        checks = [
            ("kart https", "curl -s -o /dev/null -w '%{http_code}' https://kart.renewpanel.xyz/"),
            ("kart http ", "curl -s -o /dev/null -w '%{http_code}' http://kart.renewpanel.xyz/"),
            ("stitch css", "curl -s -o /dev/null -w '%{http_code}' https://kart.renewpanel.xyz/renew-stitch-v1.css"),
            ("stitch js ", "curl -s -o /dev/null -w '%{http_code}' https://kart.renewpanel.xyz/renew-stitch-v1.js"),
            ("biziz     ", "curl -s -o /dev/null -w '%{http_code}' https://renewpanel.xyz/biziz/"),
            ("ana panel ", "curl -s -o /dev/null -w '%{http_code}' https://renewpanel.xyz/"),
        ]
        for label, cmd in checks:
            _, out, _ = run(client, cmd, check=False)
            status = out.strip()
            good = status in ("200", "301", "302", "308")
            print(f"  {label}: {status} {'' if good else '<-- BEKLENMEDIK'}")
            if not good:
                ok = False

        # 7. Sonuc / geri donus
        if not ok:
            print("\n!! KONTROL BASARISIZ - yedege donuluyor")
            run(client, "cp -p " + " ".join(f"{BACKUP}/{n}" for n in FILES) + f" {REMOTE_DIR}/")
            _, out, _ = run(client, "curl -s -o /dev/null -w '%{http_code}' https://kart.renewpanel.xyz/",
                            check=False)
            print("  geri donus sonrasi kart https:", out.strip())
            return 1

        print("\n=== TAMAM ===")
        print(f"Geri donmek icin: cp -p {BACKUP}/*.{{html,js}} {REMOTE_DIR}/")
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())

"""payment-center kaldirmayi canliya alir: yedek -> atomik aktarim -> dogrulama
-> payment_center.html/payment_hub.html karantinaya -> son kontroller -> gerekirse geri donus.

Dogrulanan degisiklik (bkz. claude_paymentcenter_verify.py):
  - index.html: <section id="payment-center"> kaldirildi (600 karakter)
  - app.js: reloadPaymentCenter, openPaymentCenterNewTab, syncPaymentFrameHeight
    + dinleyicileri, V7.24 page() router yamasi kaldirildi (19 satir)
  - style.css: 15 payment-center-shell/paymentCenterFrame kurali kaldirildi
  - renew_dashboard_v26.css: #payment-center,#mail-templates -> #mail-templates
  - mail-templates modulune HIC DOKUNULMADI (bilerek, ayri risk kategorisi)
Matematik, hesaplama kodu, veritabani DEGISMEDI.
"""
import hashlib
import sys
from datetime import datetime
from pathlib import Path

from claude_conn import ssh, run

ROOT = Path(__file__).resolve().parent
STAGE = ROOT / "paycenter_clean"
STATIC = "/opt/renewpro/app_live/app/static"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP = f"/opt/renewpro/backups/paymentcenter_removal_{STAMP}"
QUARANTINE = f"/root/QUARANTINE_{STAMP}"

FILES = ["index.html", "app.js", "style.css", "renew_dashboard_v26.css"]
ORPHANED = ["payment_center.html", "payment_hub.html"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    payload = {}
    for name in FILES:
        data = (STAGE / name).read_bytes()
        payload[name] = data
        print(f"  {name:<26} {len(data):>8,} bayt hazir")

    client = ssh()
    try:
        sftp = client.open_sftp()

        print("\n=== canli surum kontrolu ===")
        for name in FILES:
            live = sftp.open(f"{STATIC}/{name}", "rb").read()
            expected = (STAGE / "live" / name).read_bytes()
            if sha(live) != sha(expected):
                print(f"DURDURULDU: {name} canlida degismis.")
                return 1
            print(f"  {name:<26} beklenen surum OK")

        print("\n=== yedek ===")
        run(client, f"mkdir -p {BACKUP}")
        run(client, "cp -p " + " ".join(f"{STATIC}/{n}" for n in FILES) + f" {BACKUP}/")
        run(client, f"cd {BACKUP} && sha256sum * > SHA256SUMS.txt")
        print(f"YEDEK: {BACKUP}")

        print("\n=== aktarim ===")
        for name in FILES:
            target = f"{STATIC}/{name}"
            tmp = target + ".new"
            with sftp.open(tmp, "wb") as fh:
                fh.write(payload[name])
            sftp.chmod(tmp, 0o644)
            sftp.posix_rename(tmp, target)
            print(f"  {name:<26} aktarildi")

        print("\n=== hash dogrulama ===")
        ok = True
        _, out, _ = run(client, f"cd {STATIC} && sha256sum " + " ".join(FILES))
        remote = {p.split()[1]: p.split()[0] for p in out.splitlines() if len(p.split()) == 2}
        for name in FILES:
            match = remote.get(name) == sha(payload[name])
            print(f"  {name:<26} {'OK' if match else 'UYUSMUYOR'}")
            ok = ok and match

        print("\n=== servis kontrolleri ===")
        code, out, err = run(client, "nginx -t", check=False)
        print("  nginx -t:", "basarili" if code == 0 else "BASARISIZ: " + err[:200])
        ok = ok and code == 0

        # NOT: /biziz/ HER ZAMAN 308 doner (kendi ic yonlendirmesi, bu proje
        # boyunca defalarca dogrulandi) - bu bir hata degil, beklenen davranis.
        checks = [
            ("ana panel https", "curl -s -o /dev/null -w '%{http_code}' https://renewpanel.xyz/", {"200"}),
            ("ana panel app.js", "curl -s -o /dev/null -w '%{http_code}' https://renewpanel.xyz/static/app.js", {"200"}),
            ("biziz", "curl -s -o /dev/null -w '%{http_code}' https://renewpanel.xyz/biziz/", {"308"}),
            ("korumali API 401", "curl -s -o /dev/null -w '%{http_code}' https://renewpanel.xyz/api/stock", {"401"}),
        ]
        for label, cmd, expected in checks:
            _, out, _ = run(client, cmd, check=False)
            status = out.strip()
            good = status in expected
            print(f"  {label:<20} {status} {'' if good else '<-- BEKLENMEDIK (beklenen: ' + '/'.join(expected) + ')'}")
            if not good:
                ok = False

        if not ok:
            print("\n!! KONTROL BASARISIZ - yedege donuluyor")
            run(client, "cp -p " + " ".join(f"{BACKUP}/{n}" for n in FILES) + f" {STATIC}/")
            _, out, _ = run(client, "curl -s -o /dev/null -w '%{http_code}' https://renewpanel.xyz/", check=False)
            print("  geri donus sonrasi ana panel:", out.strip())
            return 1

        print("\n=== payment_center.html / payment_hub.html karantinaya ===")
        run(client, f"mkdir -p {QUARANTINE}")
        for name in ORPHANED:
            code, out, _ = run(client, f"test -f {STATIC}/{name} && echo VAR || echo YOK", check=False)
            if out.strip() != "VAR":
                print(f"  {name}: zaten yok, atlandi")
                continue
            run(client, f"mv {STATIC}/{name} {QUARANTINE}/{name}")
            print(f"  {name} -> {QUARANTINE}/{name}")
        run(client, f"cd {QUARANTINE} && sha256sum * > SHA256SUMS.txt 2>/dev/null || true")

        print("\n=== orphan dosyalarin 404 dogrulamasi ===")
        for name in ORPHANED:
            _, out, _ = run(client, f"curl -s -o /dev/null -w '%{{http_code}}' https://renewpanel.xyz/static/{name}", check=False)
            print(f"  {name:<26} {out.strip()}  {'OK' if out.strip()=='404' else 'BEKLENMEDIK'}")

        print("\n=== TAMAM ===")
        print(f"kod yedegi   : {BACKUP}")
        print(f"orphan karantina: {QUARANTINE}")
        print(f"geri donus   : cp -p {BACKUP}/* {STATIC}/")
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())

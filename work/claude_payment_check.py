"""payment_center.html canli mi olu mu? Menu 'kaldirildi' dendi ama kod hala
bagli gorunuyor. Salt okunur inceleme."""
import re
import sys

from claude_conn import ssh, run

STATIC = "/opt/renewpro/app_live/app/static"


def main():
    client = ssh()
    try:
        sftp = client.open_sftp()

        print("=== index.html: iframe cevresi (satir 270-295) ===")
        index = sftp.open(f"{STATIC}/index.html", "r").read().decode("utf-8", errors="replace")
        lines = index.split("\n")
        for i in range(269, min(296, len(lines))):
            print(f"{i+1:>5} | {lines[i][:170]}")

        print("\n=== iframe'in sarmalayici elemani gizli mi (display:none / hidden)? ===")
        m = re.search(r'<[^>]*paymentCenterFrame[^>]*>', index)
        if m:
            start = max(0, m.start() - 400)
            print(index[start:m.end()][-500:])

        print("\n=== app.js: payment_center kullanan fonksiyonlar (baglam) ===")
        appjs = sftp.open(f"{STATIC}/app.js", "r").read().decode("utf-8", errors="replace")
        for m in re.finditer(r'.{200}payment_center.{100}', appjs, re.S):
            frag = " ".join(m.group(0).split())
            print("  ..." + frag[-320:])
            print()

        print("=== 'Ödeme Merkezi' metni menude gorunur mu (CSS ile gizlenmis mi)? ===")
        for m in re.finditer(r'.{80}[ÖO]deme Merkezi.{80}', index):
            print("  ..." + " ".join(m.group(0).split()))

        print("\n=== payment/Odeme menu ogesi CSS'te display:none mi? ===")
        css_files = ["style.css", "renew_enhancement_v1.css", "renew_dashboard_v26.css"]
        for name in css_files:
            try:
                css = sftp.open(f"{STATIC}/{name}", "r").read().decode("utf-8", errors="replace")
            except FileNotFoundError:
                continue
            for m in re.finditer(r'[^{}]{0,60}payment[^{}]{0,60}\{[^}]{0,200}\}', css, re.I):
                print(f"  [{name}] " + " ".join(m.group(0).split()))

        print("\n=== nginx access log: payment_center isteklerinin Referer'i ===")
        _, out, _ = run(
            client,
            "grep 'payment_center' /var/log/nginx/access.log 2>/dev/null | tail -20 "
            "| grep -oE '\"[A-Z]+ [^\"]+\" [0-9]+ [0-9]+ \"[^\"]*\"' || echo yok",
            check=False)
        print(out.rstrip())

        print("\n=== son erisim zamanlari ===")
        _, out, _ = run(
            client,
            "grep 'payment_center' /var/log/nginx/access.log 2>/dev/null | tail -5",
            check=False)
        print(out.rstrip())
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

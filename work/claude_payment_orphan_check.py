"""Duzenlenen index.html/app.js disinda, tum uygulamada payment_center.html
veya payment_hub.html'e baska referans var mi? (backend main.py, diger JS
dosyalari, nginx dahil). Amac: bu iki HTML dosyasini da karantinaya alip
alamayacagimizi netlestirmek."""
import sys

from claude_conn import ssh, run

APP = "/opt/renewpro/app_live/app"


def main():
    client = ssh()
    try:
        print("=== grep: tum app/ altinda 'payment_center' veya 'payment_hub' ===")
        _, out, _ = run(
            client,
            f"grep -rn --exclude-dir=__pycache__ -E 'payment_center|payment_hub' {APP} "
            f"--include='*.py' --include='*.js' --include='*.html' --include='*.css' "
            f"2>/dev/null | grep -v '/app/static/index.html:' | grep -v '/app/static/app.js:'",
            check=False)
        print(out.rstrip() or "  (index.html ve app.js disinda referans yok)")

        print("\n=== nginx: ozel yol tanimi var mi ===")
        _, out, _ = run(
            client,
            "grep -n 'payment' /etc/nginx/sites-available/* 2>/dev/null",
            check=False)
        print(out.rstrip() or "  ozel tanim yok")

        print("\n=== main.py: /api/mail-config veya payment ile ilgili route ===")
        _, out, _ = run(
            client,
            f"grep -n -i 'payment' {APP}/main.py 2>/dev/null",
            check=False)
        print(out.rstrip() or "  ilgili route yok")
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

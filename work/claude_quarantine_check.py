"""Karantinaya alinacak dosyalar gercekten kullanilmiyor mu? Salt okunur kontrol."""
import sys

from claude_conn import ssh, run

APP = "/opt/renewpro/app_live"
STATIC = APP + "/app/static"
KART = "/var/www/kart.renewpanel.xyz"

# (aciklama, tam yol)
CANDIDATES = [
    ("eski yedek", STATIC + "/app.js.bak_20260902_155437"),
    ("eski yedek", STATIC + "/app.js.bak_20260902_154344"),
    ("eski yedek", STATIC + "/index.html.bak_20260902_155437"),
    ("eski yedek", STATIC + "/index.html.bak_20260902_154344"),
    ("eski yedek", STATIC + "/renew_media_picker_v2.js.bak_20260902_154344"),
    ("eski yedek", STATIC + "/renew_forms_v1.css.bak_20260902_155437"),
    ("kaldirilmis modul", STATIC + "/payment_center.html"),
    ("kaldirilmis modul", STATIC + "/payment_hub.html"),
]

DIRS = [
    ("web kokunde demo", KART + "/demo"),
    ("web kokunde yedek", KART + "/backups"),
]


def main():
    client = ssh()
    try:
        print("=== 1. Dosyalar mevcut mu, boyutlari ===")
        for label, path in CANDIDATES:
            code, out, _ = run(client, f"ls -la {path} 2>/dev/null", check=False)
            print(f"  {label:<18} {out.strip() if out.strip() else 'YOK: ' + path}")

        print("\n=== 2. Dizinler ===")
        for label, path in DIRS:
            code, out, _ = run(client, f"ls -la {path} 2>/dev/null | head -10", check=False)
            print(f"\n  {label} -> {path}")
            print("    " + (out.strip().replace("\n", "\n    ") if out.strip() else "YOK"))

        print("\n=== 3. Referans taramasi (kod icinde adi geciyor mu) ===")
        names = [p.rsplit("/", 1)[1] for _, p in CANDIDATES]
        names += ["payment_center", "payment_hub", "/demo"]
        for name in sorted(set(names)):
            cmd = (
                "grep -rIl --exclude-dir=.venv --exclude-dir=__pycache__ "
                "--exclude-dir=backups --exclude='*.bak_*' "
                f"-F -- '{name}' {APP}/app {KART}/index.html 2>/dev/null | head -8"
            )
            _, out, _ = run(client, cmd, check=False)
            hits = [x for x in out.strip().splitlines() if x]
            if hits:
                print(f"\n  {name}")
                for h in hits:
                    # hangi satirda
                    _, ctx, _ = run(
                        client,
                        f"grep -n -F -- '{name}' {h} 2>/dev/null | head -3", check=False)
                    print(f"    {h}")
                    for line in ctx.strip().splitlines()[:3]:
                        print(f"       {line.strip()[:130]}")
            else:
                print(f"  {name:<46} referans YOK")

        print("\n=== 4. Nginx bu yollari ozel olarak tanimliyor mu ===")
        _, out, _ = run(
            client,
            "grep -nE 'payment|demo|backups|\\.bak' /etc/nginx/sites-available/* 2>/dev/null || "
            "echo '  ozel tanim yok'", check=False)
        print(out.rstrip())

        print("\n=== 5. Son 7 gunde bu dosyalara erisim olmus mu (nginx access log) ===")
        _, out, _ = run(
            client,
            "grep -hoE '(payment_(center|hub)\\.html|[A-Za-z0-9_.]+\\.bak_[0-9_]+|/demo/)' "
            "/var/log/nginx/access.log /var/log/nginx/access.log.1 2>/dev/null "
            "| sort | uniq -c | sort -rn | head -15 || echo '  kayit yok'", check=False)
        print(out.rstrip() or "  kayit yok")
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

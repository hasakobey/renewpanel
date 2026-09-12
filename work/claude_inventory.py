"""Salt okunur envanter: canli sistemin gercek durumunu cikarir.

Hicbir dosya degistirilmez, /biziz'e dokunulmaz.
"""
import sys
from claude_conn import ssh, run

SECTIONS = [
    ("SERVIS DURUMU", [
        "systemctl is-active renewpro.service nginx || true",
        "systemctl show -p MainPID -p NRestarts --value renewpro.service",
    ]),
    ("SURUM / PYTHON", [
        "/opt/renewpro/.venv/bin/python -V 2>&1 || true",
        "grep -rhoE 'version[\"'\"'\"']?\\s*[:=]\\s*[\"'\"'\"']?[0-9]+\\.[0-9]+\\.[0-9]+' /opt/renewpro/app_live/app/main.py | head -5 || true",
    ]),
    ("HTTP KONTROL", [
        "curl -s -o /dev/null -w 'renewpanel https=%{http_code}\\n' https://renewpanel.xyz/",
        "curl -s -o /dev/null -w 'renewpanel http =%{http_code}\\n' http://renewpanel.xyz/",
        "curl -s -o /dev/null -w 'kart       https=%{http_code}\\n' https://kart.renewpanel.xyz/",
        "curl -s -o /dev/null -w 'biziz      https=%{http_code}\\n' https://renewpanel.xyz/biziz/",
    ]),
    ("DISK / DB", [
        "df -h / | tail -1",
        "ls -la /var/lib/renewpro/data/ 2>/dev/null || true",
        "/opt/renewpro/.venv/bin/python -c \"import sqlite3;c=sqlite3.connect('/var/lib/renewpro/data/renew.db');print('integrity',c.execute('PRAGMA integrity_check').fetchone()[0]);print('tables',len(c.execute(\\\"SELECT name FROM sqlite_master WHERE type='table'\\\").fetchall()))\" 2>&1 || true",
    ]),
    ("UYGULAMA DOSYALARI", [
        "find /opt/renewpro/app_live/app -maxdepth 1 -type f -name '*.py' -printf '%10s  %p\\n' | sort -rn",
    ]),
    ("STATIK DOSYALAR", [
        "find /opt/renewpro/app_live/app/static -maxdepth 1 -type f -printf '%10s  %f\\n' | sort -rn | head -60",
        "echo '--- toplam ---'",
        "find /opt/renewpro/app_live/app/static -maxdepth 1 -type f | wc -l",
    ]),
    ("INDEX.HTML REFERANSLARI", [
        "grep -oE '/static/[A-Za-z0-9_.-]+\\.(css|js)' /opt/renewpro/app_live/app/static/index.html | sed 's#/static/##' | sort -u",
    ]),
    ("KART SITESI", [
        "ls -la /var/www/kart.renewpanel.xyz/",
        "sha256sum /var/www/kart.renewpanel.xyz/*.html 2>/dev/null || true",
    ]),
    ("NGINX", [
        "nginx -t 2>&1",
        "ls -la /etc/nginx/sites-enabled/",
    ]),
    ("YEDEKLER", [
        "ls -1dt /opt/renewpro/backups/* 2>/dev/null | head -15",
        "echo '--- /root ---'",
        "ls -1dt /root/RENEW* /root/KART* 2>/dev/null | head -15",
    ]),
    ("SON HATALAR", [
        "journalctl -u renewpro.service --since '7 days ago' -p err --no-pager 2>/dev/null | tail -15 || true",
        "echo '--- nginx error ---'",
        "tail -15 /var/log/nginx/error.log 2>/dev/null || true",
    ]),
]


def main():
    client = ssh()
    try:
        for title, cmds in SECTIONS:
            print("\n" + "=" * 62)
            print("== " + title)
            print("=" * 62)
            for cmd in cmds:
                _, out, err = run(client, cmd, check=False)
                text = (out + err).rstrip()
                if text:
                    print(text)
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())

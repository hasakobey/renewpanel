"""kart/demo tasindigi halde neden hala 200 donuyor? Salt okunur teshis."""
import sys

from claude_conn import ssh, run

KART = "/var/www/kart.renewpanel.xyz"


def main():
    client = ssh()
    try:
        print("=== 1. Dizin gercekten yerinde mi ===")
        _, out, _ = run(client, f"ls -la {KART}/demo 2>&1", check=False)
        print(" ", out.strip())

        print("\n=== 2. Baska bir demo dizini/dosyasi var mi (sembolik link dahil) ===")
        _, out, _ = run(client, f"find / -xdev -iname 'demo' -maxdepth 6 2>/dev/null | grep -v proc", check=False)
        print(out.rstrip() or "  bulunamadi")
        _, out, _ = run(client, "find /var/www /opt -iname 'demo*' 2>/dev/null", check=False)
        print(out.rstrip())

        print("\n=== 3. nginx open_file_cache / sendfile ayarlari ===")
        _, out, _ = run(client, "grep -rn 'open_file_cache\\|sendfile' /etc/nginx/nginx.conf /etc/nginx/sites-available/* 2>/dev/null", check=False)
        print(out.rstrip() or "  ayar yok (varsayilan)")

        print("\n=== 4. nginx server block: kart.renewpanel.xyz root/alias ===")
        _, out, _ = run(client, "cat /etc/nginx/sites-available/kart.renewpanel.xyz", check=False)
        print(out.rstrip())

        print("\n=== 5. Taze curl (dogrudan, -v ile) ===")
        _, out, _ = run(client, "curl -sv https://kart.renewpanel.xyz/demo/ 2>&1 | head -30", check=False)
        print(out.rstrip())

        print("\n=== 6. nginx worker'lari yeniden mi baslatilmali (reload olmadan acik fd kalir mi) ===")
        _, out, _ = run(client, "systemctl show -p MainPID --value nginx && ps -o pid,etimes,cmd -p $(systemctl show -p MainPID --value nginx)", check=False)
        print(out.rstrip())

        print("\n=== 7. Cache/CDN basligi var mi ===")
        _, out, _ = run(client, "curl -sI https://kart.renewpanel.xyz/demo/", check=False)
        print(out.rstrip())
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

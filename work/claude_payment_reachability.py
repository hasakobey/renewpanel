"""payment-center / mail-templates sayfalarina ulasan HERHANGI bir yol var mi?
Router mantigini ve nav elemanlarini tarar. Salt okunur."""
import re
import sys

from claude_conn import ssh

STATIC = "/opt/renewpro/app_live/app/static"


def main():
    client = ssh()
    try:
        sftp = client.open_sftp()
        index = sftp.open(f"{STATIC}/index.html", "r").read().decode("utf-8", errors="replace")
        appjs = sftp.open(f"{STATIC}/app.js", "r").read().decode("utf-8", errors="replace")

        print("=== index.html: 'payment-center' / 'mail-templates' gecen TUM yerler ===")
        for target in ("payment-center", "mail-templates"):
            print(f"\n-- {target} --")
            for m in re.finditer(re.escape(target), index):
                line = index.count("\n", 0, m.start()) + 1
                ctx = index[max(0, m.start()-70):m.start()+40].replace("\n", " ")
                print(f"  satir {line}: ...{ctx}")

        print("\n=== app.js: goToPage/showPage/route fonksiyonlari 'payment-center' iceriyor mu ===")
        for m in re.finditer(r'.{60}(payment-center|mail-templates).{60}', appjs):
            frag = " ".join(m.group(0).split())
            print("  ..." + frag)

        print("\n=== nav/menu ogeleri: data-page veya onclick ile hangi sayfalara gidiliyor ===")
        nav_targets = set(re.findall(r'data-page="([a-z0-9-]+)"', index))
        nav_targets |= set(re.findall(r"goToPage\('([a-z0-9-]+)'\)", index))
        nav_targets |= set(re.findall(r"showPage\('([a-z0-9-]+)'\)", index))
        print("  nav'dan ulasilan sayfalar:", sorted(nav_targets))
        print("  'payment-center' bu listede mi:", 'payment-center' in nav_targets)
        print("  'mail-templates' bu listede mi:", 'mail-templates' in nav_targets)

        print("\n=== TUM <section id=...> sayfalari vs nav'dan ulasilanlar ===")
        all_sections = set(re.findall(r'<section id="([a-z0-9-]+)"', index))
        unreachable = all_sections - nav_targets
        print("  toplam section:", len(all_sections))
        print("  nav'dan ulasilamayan section'lar:", sorted(unreachable))
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

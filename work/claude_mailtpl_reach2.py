"""mail-templates GERCEKTEN erisilemez mi, yoksa router/hash uzerinden mi acilabiliyor?
Ayrica authorityPeople/renderAuthorityManager baska aktif akislarla bagli mi?"""
import re
import sys

from claude_conn import ssh

STATIC = "/opt/renewpro/app_live/app/static"


def main():
    client = ssh()
    try:
        sftp = client.open_sftp()
        appjs = sftp.open(f"{STATIC}/app.js", "r").read().decode("utf-8", errors="replace")
        index = sftp.open(f"{STATIC}/index.html", "r").read().decode("utf-8", errors="replace")
        css = sftp.open(f"{STATIC}/style.css", "r").read().decode("utf-8", errors="replace")

        def line_of(text, pos):
            return text.count("\n", 0, pos) + 1

        print("=== 1. Router/goToPage/_pageV725 fonksiyon tanimi ===")
        for name in ("_pageV725", "goToPage", "function.*Page"):
            for m in re.finditer(rf'function\s+{name}\s*\([^)]*\)\s*\{{', appjs):
                start = m.start()
                snippet = appjs[start:start+500]
                print(f"\n-- {name} (satir {line_of(appjs, start)}) --")
                print(snippet)

        print("\n=== 2. Hash/URL ile sayfa acma (location.hash, #mail-templates) ===")
        for m in re.finditer(r'.{60}(location\.hash|hashchange|#mail-templates|#payment-center).{60}', appjs):
            print("  ..." + " ".join(m.group(0).split()))
        for m in re.finditer(r'.{60}(location\.hash|hashchange|#mail-templates|#payment-center).{60}', index):
            print("  [html] ..." + " ".join(m.group(0).split()))

        print("\n=== 3. authorityPeople / renderAuthorityManager baska nerelerde geciyor ===")
        for name in ("authorityPeople", "renderAuthorityManager"):
            print(f"\n-- {name} --")
            for m in re.finditer(re.escape(name), appjs):
                ln = line_of(appjs, m.start())
                ctx = appjs[max(0, m.start()-60):m.start()+50]
                print(f"  satir {ln}: ...{' '.join(ctx.split())}")

        print("\n=== 4. 'devir' veya 'Devir' gecen fonksiyon adlari (Cayan Alis/Devir akisi) ===")
        devir_fns = set(re.findall(r'function\s+(\w*[Dd]evir\w*)\s*\(', appjs))
        print("  fonksiyonlar:", sorted(devir_fns))
        for fn in sorted(devir_fns):
            uses_mail = bool(re.search(
                rf'function\s+{re.escape(fn)}\s*\([^)]*\)\s*\{{[^}}]{{0,2000}}(mailTpl|MailTemplate|authorityPeople)',
                appjs, re.S))
            print(f"    {fn}: mail-template/authority kullaniyor mu -> {uses_mail}")

        print("\n=== 5. CSS ozgullugu: .page.active mail-templates gizlemeyi eziyor mu ===")
        for m in re.finditer(r'\.page\.active\s*\{[^}]*\}', css):
            print("  " + " ".join(m.group(0).split()))
        for m in re.finditer(r'#mail-templates[^{]*\{[^}]*\}', css):
            print("  " + " ".join(m.group(0).split()))
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

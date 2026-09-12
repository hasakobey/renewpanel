"""Yogun kullanilan mail-template fonksiyonlarinin gercek CAGRI yerlerini bulur
(tanimlarini degil). Bu fonksiyonlar sadece gizli mail-templates bolumunden mi
cagriliyor, yoksa baska aktif akislardan da mi (sigorta/devir/nakit-takas)?"""
import re
import sys

from claude_conn import ssh

STATIC = "/opt/renewpro/app_live/app/static"

HEAVY = ["renderMailTplPreview", "selectMailTemplate", "updateMailTemplateDraft",
         "renderMailTemplateList", "renderMailTplVars", "applyMailTplText",
         "mailTplSampleVars", "persistMailTemplates", "insertMailTplVar",
         "loadMailTemplates", "loadMailTemplatesV725"]


def main():
    client = ssh()
    try:
        sftp = client.open_sftp()
        appjs = sftp.open(f"{STATIC}/app.js", "r").read().decode("utf-8", errors="replace")
        index = sftp.open(f"{STATIC}/index.html", "r").read().decode("utf-8", errors="replace")

        def line_of(text, pos):
            return text.count("\n", 0, pos) + 1

        for fn in HEAVY:
            print("=" * 70)
            print(f"== {fn}")
            print("=" * 70)
            # tanim satirini disla
            def_pat = re.compile(rf'function\s+{re.escape(fn)}\s*\(')
            call_pat = re.compile(rf'(?<![\w.])(?:window\.)?{re.escape(fn)}\s*\(')

            def_lines = {line_of(appjs, m.start()) for m in def_pat.finditer(appjs)}
            calls = []
            for m in call_pat.finditer(appjs):
                ln = line_of(appjs, m.start())
                if ln in def_lines:
                    continue
                ctx = appjs[max(0, m.start()-70):m.start()+30]
                calls.append((ln, " ".join(ctx.split())))

            print(f"tanim satiri: {sorted(def_lines)}")
            print(f"gercek cagri sayisi (tanim haric): {len(calls)}")
            for ln, ctx in calls[:8]:
                print(f"  satir {ln}: ...{ctx}")
            if len(calls) > 8:
                print(f"  ... {len(calls)-8} cagri daha")

            in_html = len(re.findall(re.escape(fn) + r'\(', index))
            print(f"index.html'de gecen (onclick vb.): {in_html}")
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

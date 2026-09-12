import re
t = open(r'C:\Users\Hasan\Documents\Codex\2026-08-31\referenced-chatgpt-conversation-this-is-an\work\kart_clean\test\index.html', encoding='utf-8').read()
for needle in ['rc-workspace','rc-mini-actions','btn-container','rc-summary-pane']:
    print('===', needle)
    for m in re.finditer(re.escape(needle), t):
        ln = t.count(chr(10), 0, m.start()) + 1
        zone = 'GERCEK HTML' if ln < 2351 else 'INLINE SCRIPT ICINDE (satir 2351+)'
        ctx = t[max(0,m.start()-60):m.start()+40].replace(chr(10),' ')
        print('   satir {:>5}  {:<34} ...{}'.format(ln, zone, ctx[-70:]))
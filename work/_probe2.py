import re
p = r'C:\Users\Hasan\Documents\Codex\2026-08-31\referenced-chatgpt-conversation-this-is-an\work\kart_clean\test\index.html'
t = open(p, encoding='utf-8').read()
lines = t.split(chr(10))
for ln in (3318, 3332, 3333, 3334, 3335):
    if ln-1 < len(lines):
        s = lines[ln-1]
        print('--- satir', ln, '(', len(s), 'karakter )')
        print('   basi :', s[:120])
        print('   sonu :', s[-200:] if len(s) > 200 else '(ayni)')
print()
print('=== inline bloklarin tetikleri ===')
for m in re.finditer(r'<script(?![^>]*\bsrc=)([^>]*)>(.*?)</script\s*>', t, re.S|re.I):
    ln = t.count(chr(10),0,m.start())+1
    body = m.group(2)
    trig = []
    if re.search(r"addEventListener\(\s*'load'", body): trig.append('window.load')
    if 'DOMContentLoaded' in body: trig.append('DOMContentLoaded')
    if not trig: trig.append('dogrudan/parse aninda')
    print('  satir {:>5}  {:<44} {}'.format(ln, (m.group(1).strip() or '<script>')[:44], ' + '.join(trig)))
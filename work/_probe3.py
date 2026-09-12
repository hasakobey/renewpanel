import re
p = r'C:\Users\Hasan\Documents\Codex\2026-08-31\referenced-chatgpt-conversation-this-is-an\work\paycenter_clean\app.js'
t = open(p, encoding='utf-8').read()
for m in re.finditer(r'.{120}payment_center.{80}', t, re.S):
    ln = t.count(chr(10), 0, m.start()) + 1
    print('satir', ln, ':', ' '.join(m.group(0).split()))
import re
p = r'C:\Users\Hasan\Documents\Codex\2026-08-31\referenced-chatgpt-conversation-this-is-an\work\paycenter_clean\app.js'
t = open(p, encoding='utf-8').read()
print('payment_center count:', t.count('payment_center'))
print('payment-center count:', t.count('payment-center'))
for name in ('payment_center','payment-center'):
    idx = 0
    while True:
        i = t.find(name, idx)
        if i == -1: break
        ln = t.count(chr(10),0,i)+1
        print(name, 'satir', ln, ':', ' '.join(t[max(0,i-100):i+80].split()))
        idx = i+1
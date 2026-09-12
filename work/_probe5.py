p = r'C:\Users\Hasan\Documents\Codex\2026-08-31\referenced-chatgpt-conversation-this-is-an\work\paycenter_clean\app.js'
t = open(p, encoding='utf-8').read()
i = t.find('syncPaymentFrameHeight')
print(t[max(0,i-40):i+900])
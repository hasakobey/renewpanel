import re
t = open(r'C:\Users\Hasan\Documents\Codex\2026-08-31\referenced-chatgpt-conversation-this-is-an\work\login_clean\index.html', encoding='utf-8').read()
for m in re.finditer(r'[^{}]*#loginOverlay[^{}]*\{[^}]*\}', t):
    print(m.group(0))
    print('---')
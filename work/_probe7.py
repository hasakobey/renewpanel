import re
from pathlib import Path
html = (Path(r'C:\Users\Hasan\Documents\Codex\2026-08-31\referenced-chatgpt-conversation-this-is-an\work\login_clean\index.html')).read_text(encoding='utf-8')
links = re.findall(r'<link rel=\"stylesheet\"[^>]*>', html)
print('son 3 CSS link:'); [print(' ', l) for l in links[-3:]]
scripts = re.findall(r'<script src=\"[^\"]+\"></script>', html)
print('son 3 script:'); [print(' ', s) for s in scripts[-3:]]
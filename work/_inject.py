from pathlib import Path
p = Path(r'C:\Users\Hasan\Documents\Codex\2026-08-31\referenced-chatgpt-conversation-this-is-an\work') / 'kart_clean' / 'test' / 'index.html'
t = p.read_text(encoding='utf-8')
probe = ('<script>window.__errs=[];window.addEventListener(\'error\',function(e){'
         'window.__errs.push({msg:e.message,file:(e.filename||\'\').split(\'/\').pop(),'
         'line:e.lineno,col:e.colno,stack:e.error&&e.error.stack?String(e.error.stack).slice(0,600):null})},true);</script>')
if '__errs' in t:
    print('sonda zaten var')
else:
    i = t.lower().find('<head>')
    t = t[:i+6] + probe + t[i+6:]
    p.write_text(t, encoding='utf-8', newline='')
    print('hata yakalayici <head> icine eklendi')
from pathlib import Path
from urllib.parse import urlsplit
import re
from video_v2_ops import ssh

root=Path(__file__).resolve().parent
c=ssh();s=c.open_sftp()
try:
    data=s.open('/opt/renewpro/app_live/app/static/index.html','rb').read().decode('utf-8')
    (root/'renew_export_index.html').write_text(data,encoding='utf-8')
    print('HTML bytes',len(data))
    cache={}
    def asset(url):
        path=urlsplit(url).path
        if not path.startswith('/static/') or '..' in path.split('/'):
            raise ValueError('Unexpected asset path')
        if path not in cache:
            cache[path]=s.open('/opt/renewpro/app_live/app'+path,'rb').read().decode('utf-8')
        return cache[path]
    def css(match):
        tag=match.group(0)
        href=re.search(r'href=["\']([^"\']+)',tag)
        if not href or not urlsplit(href[1]).path.endswith('.css'): return tag
        return '<style data-original-source="'+href[1]+'">\n'+asset(href[1]).replace('</style','<\\/style')+'\n</style>'
    data=re.sub(r'<link\b[^>]*>',css,data,flags=re.I)
    def script(match):
        attrs,content=match.group(1),match.group(2)
        src=re.search(r'src=["\']([^"\']+)',attrs)
        if src:
            content=asset(src[1])
        return '<script type="text/plain" data-design-source="'+(src[1] if src else 'inline')+'">\n'+content.replace('</script','<\\/script')+'\n</script>'
    data=re.sub(r'<script\b([^>]*)>(.*?)</script\s*>',script,data,flags=re.I|re.S)
    # Design handoff is deliberately inert: no logins, API requests or live mutations.
    security='<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; img-src data:; script-src \'none\'; connect-src \'none\'; form-action \'none\'; base-uri \'none\'">'
    data=re.sub(r'<head>', '<head>\n'+security,data,count=1,flags=re.I)
    note='<!-- RENEW PRO: current front-end design reference. CSS and JavaScript sources are embedded. Scripts are intentionally inactive; dynamic screens require the original backend. No database, session, customer export or server configuration is included. -->\n'
    data=note+data
    patterns=[r'sk-(?:proj-)?[A-Za-z0-9_-]{20,}',r'AIza[0-9A-Za-z_-]{25,}',r'-----BEGIN (?:RSA )?PRIVATE KEY-----',r'eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}']
    redacted=0
    for pattern in patterns:
        data,count=re.subn(pattern,'[REDACTED_FOR_DESIGN_HANDOFF]',data)
        redacted+=count
    out=root.parent/'output'/'RENEW_PRO_STITCH_TASARIM_KAYNAKLARI.html'
    out.write_text(data,encoding='utf-8')
    print('Embedded assets',len(cache),'Redacted credentials',redacted,'Bytes',out.stat().st_size)
    print('Output',out)
finally:
    s.close();c.close()

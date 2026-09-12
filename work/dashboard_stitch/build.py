from pathlib import Path
import re
r=Path(__file__).parent
html=(r/'before/index.html').read_text(encoding='utf-8')
html=re.sub(r'<script src="/static/renew_dashboard_sections_v1.js[^\"]*"></script>','',html)
html=html.replace('</head>','<link rel="stylesheet" href="/static/renew_dashboard_stitch.css?v=1"></head>')
html=html.replace('</body>','<script src="/static/renew_dashboard_stitch.js?v=1"></script></body>')
(r/'index.html').write_text(html,encoding='utf-8')
fixture=re.sub(r'<script\b[^>]*>.*?</script>','',html,flags=re.S|re.I)
fixture=re.sub(r'<iframe\b[^>]*>.*?</iframe>','',fixture,flags=re.S|re.I)
fixture=fixture.replace('/static/','before/').replace('before/renew_dashboard_stitch.css','renew_dashboard_stitch.css')
fixture=fixture.replace('</head>','<style>#loginOverlay{display:none!important}</style></head>')
scripts='<script>window.fetch=async()=>new Response("{}",{status:401,headers:{"Content-Type":"application/json"}});</script>'
for name in ['app.js','dashboard_pro_v3.js','renew_dashboard_v26.js','renew_dashboard_bottom_v1.js','renew_glass_wave_v1.js','renew_dashboard_polish_v1.js']:
 scripts+=f'<script src="before/{name}"></script>'
scripts+='<script src="renew_dashboard_stitch.js"></script><script src="fixture_data.js"></script>'
fixture=fixture.replace('</body>',scripts+'</body>')
(r/'fixture.html').write_text(fixture,encoding='utf-8')

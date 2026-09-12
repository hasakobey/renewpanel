from pathlib import Path
import re
r=Path(__file__).parent
html=(r/'before/index.html').read_text(encoding='utf-8')
html=html.replace('</head>','<link rel="stylesheet" href="/static/renew_ui_stitch_v2.css?v=2"></head>')
html=html.replace('</body>','<script src="/static/renew_ui_stitch_v2.js?v=2"></script></body>')
(r/'index.html').write_text(html,encoding='utf-8')
fixture=re.sub(r'<script\b[^>]*>.*?</script>','',html,flags=re.S|re.I)
fixture=re.sub(r'<iframe\b[^>]*>.*?</iframe>','',fixture,flags=re.S|re.I)
fixture=fixture.replace('/static/','before/').replace('before/renew_ui_stitch_v2.css','renew_ui_stitch_v2.css')
fixture=fixture.replace('</head>','<style>#loginOverlay{display:none!important}</style></head>')
scripts='<script src="fixture_network.js"></script>'
names=re.findall(r'<script src="/static/([\w.-]+\.js)',html)
for name in names:
 if name=='user_admin_v2.js':continue
 scripts+=f'<script src="{name if name=="renew_ui_stitch_v2.js" else "before/"+name}"></script>'
scripts+='<script src="fixture_data.js"></script>'
fixture=fixture.replace('</body>',scripts+'</body>')
(r/'fixture.html').write_text(fixture,encoding='utf-8')
# All module assets above are the exact live files. Only auth and network are isolated.
data=(r.parent/'dashboard_stitch/fixture_data.js').read_text(encoding='utf-8')
data=data.replace('sales_target_rate:.4}', 'sales_target_rate:.4,avg_sks:7.3,revenue:5000000,performance_profit:96438,avg_profit:24109.5,target_profit:0}')
(r/'fixture_data.js').write_text(data+'\n'+(r/'fixture_extra.js').read_text(encoding='utf-8'),encoding='utf-8')

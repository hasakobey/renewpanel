from pathlib import Path
import re
r=Path(__file__).parent
html=(r/'before/index.html').read_text(encoding='utf-8')
html=html.replace('</head>','<link rel="stylesheet" href="/static/dashboard_reference_v3.css?v=3"></head>')
html=html.replace('</body>','<script src="/static/dashboard_reference_v3.js?v=3"></script></body>')
(r/'index.html').write_text(html,encoding='utf-8')
fixture=re.sub(r'<script\b[^>]*>.*?</script>','',html,flags=re.S|re.I);fixture=re.sub(r'<iframe\b[^>]*>.*?</iframe>','',fixture,flags=re.S|re.I)
fixture=fixture.replace('/static/','before/').replace('before/dashboard_reference_v3.css','dashboard_reference_v3.css').replace('</head>','<style>#loginOverlay{display:none!important}</style></head>')
names=re.findall(r'<script src="/static/([\w.-]+\.js)',html);scripts='<script src="../ui_stitch_full/fixture_network.js"></script>'
for n in names:
 if n=='user_admin_v2.js':continue
 if n=='dashboard_reference_v3.js':scripts+='<script src="dashboard_reference_v3.js"></script>'
 else:scripts+=f'<script src="before/{n}"></script>'
scripts+='<script src="fixture_data.js"></script>';fixture=fixture.replace('</body>',scripts+'</body>');(r/'fixture.html').write_text(fixture,encoding='utf-8')
data=(r.parent/'dashboard_stitch/fixture_data.js').read_text(encoding='utf-8').replace('sales_target_rate:.4}', 'sales_target_rate:.4,avg_sks:7.3,revenue:5000000,performance_profit:96438,avg_profit:24109.5,target_profit:0}')
(r/'fixture_data.js').write_text(data,encoding='utf-8')

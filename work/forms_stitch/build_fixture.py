from pathlib import Path
import re
r=Path(__file__).parent
text=(r/'before/index.html').read_text(encoding='utf-8')
text=re.sub(r'<script\b[^>]*>.*?</script>','',text,flags=re.S|re.I)
text=re.sub(r'<iframe\b[^>]*>.*?</iframe>','',text,flags=re.S|re.I)
text=text.replace('href="/static/','href="https://renewpanel.xyz/static/')
text=text.replace('</head>','<link rel="stylesheet" href="renew_forms_stitch.css"><style>#loginOverlay{display:none!important}.fixture-tools{position:fixed;top:0;right:0;z-index:99999;background:white;padding:4px}</style></head>')
fixture='''<div class="fixture-tools"><button onclick="openStock()">TEST STOK</button><button onclick="openSale()">TEST SATIŞ</button><button onclick="openAcquisition()">TEST ALIM</button></div>
<script>window.fetch=async()=>new Response('{}',{status:401,headers:{'Content-Type':'application/json'}});</script>
<script src="app.js"></script><script src="renew_forms_v1.js"></script><script src="renew_forms_stitch.js"></script>
<script>SETTINGS={rules:[{name:'NAKİT',active:1},{name:'ŞİRKET ARACI',active:1}],sale_types:[{name:'NAKİT',active:1}],consultants:[{name:'TEST DANIŞMAN',active:1}]};</script>'''
finance=r.parent/'finance_preview/preview_sample.json'
if finance.exists():
    fixture+='<script>const sampleFinance='+finance.read_text(encoding='utf-8')+';const fixtureFetch=window.fetch;window.fetch=async(u,o)=>String(u).endsWith("/financial-preview")?new Response(JSON.stringify(sampleFinance),{headers:{"Content-Type":"application/json"}}):fixtureFetch(u,o);</script><script src="renew_form_finance.js"></script>'
    text=text.replace('</head>','<link rel="stylesheet" href="renew_form_finance.css"></head>')
text=text.replace('</body>',fixture+'</body>')
(r/'fixture.html').write_text(text,encoding='utf-8')

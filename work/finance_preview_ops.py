from pathlib import Path
from video_v2_ops import ssh
r=Path(__file__).parent/'finance_preview';r.mkdir(exist_ok=True);(r/'before').mkdir(exist_ok=True)
c=ssh();s=c.open_sftp()
try:
 for n in ['main.py','calc.py','auth_context.py','auth_service.py','static/index.html','static/renew_forms_stitch.js','static/renew_forms_stitch.css']:
  for folder in [r,r/'before']:
   (folder/n).parent.mkdir(parents=True,exist_ok=True);s.get('/opt/renewpro/app_live/app/'+n,str(folder/n))
 print('Current backend and presentation fetched')
finally:s.close();c.close()

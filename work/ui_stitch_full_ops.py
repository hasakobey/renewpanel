from pathlib import Path
import re,sys
from datetime import datetime
from video_v2_ops import ssh,run
r=Path(__file__).parent/'ui_stitch_full';base='/opt/renewpro/app_live/app/static/'
assets=['renew_ui_stitch_v2.css','renew_ui_stitch_v2.js','index.html']
c=ssh();s=c.open_sftp()
try:
 if sys.argv[1]=='fetch':
  p=r/'before';p.mkdir(exist_ok=True,parents=True);s.get(base+'index.html',str(p/'index.html'))
  for name in set(re.findall(r'/static/([\w.-]+\.(?:css|js))',(p/'index.html').read_text(encoding='utf-8'))):s.get(base+name,str(p/name))
  for name in ['calc.py','form_finance.py']:s.get('/opt/renewpro/app_live/app/'+name,str(p/name))
  print('Live sources fetched; calculator baseline preserved')
 elif sys.argv[1]=='deploy':
  assert s.open(base+'index.html','rb').read()==(r/'before/index.html').read_bytes(),'Live index changed'
  for name in ['calc.py','form_finance.py']:assert s.open('/opt/renewpro/app_live/app/'+name,'rb').read()==(r/'before'/name).read_bytes(),'Calculator changed'
  backup='/opt/renewpro/backups/ui_stitch_full_'+datetime.now().strftime('%Y%m%d_%H%M%S')
  run(c,'mkdir -p '+backup+' && cp -p '+base+'index.html '+backup+'/index.html')
  try:
   for name in assets:
    s.put(str(r/name),base+name+'.new');s.chmod(base+name+'.new',0o644);s.posix_rename(base+name+'.new',base+name)
    assert s.open(base+name,'rb').read()==(r/name).read_bytes()
   run(c,'curl -fsS -o /dev/null -w "HTTPS %{http_code}\\n" https://renewpanel.xyz/')
  except Exception:
   run(c,'cp -p '+backup+'/index.html '+base+'index.html');raise
  print('BACKUP',backup)
finally:s.close();c.close()

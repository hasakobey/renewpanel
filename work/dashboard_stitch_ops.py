from pathlib import Path
import re,sys,hashlib
from datetime import datetime
from video_v2_ops import ssh,run
r=Path(__file__).parent/'dashboard_stitch';base='/opt/renewpro/app_live/app/static/'
c=ssh();s=c.open_sftp()
try:
 if sys.argv[1]=='fetch':
  p=r/'before';p.mkdir(exist_ok=True,parents=True)
  s.get(base+'index.html',str(p/'index.html'))
  html=(p/'index.html').read_text(encoding='utf-8')
  names=set(re.findall(r'/static/([\w.-]+\.(?:css|js))',html))
  for name in names:s.get(base+name,str(p/name))
  print('Fetched',len(names),'assets')
 elif sys.argv[1]=='deploy':
  assert s.open(base+'index.html','rb').read()==(r/'before/index.html').read_bytes(),'Live index changed'
  backup='/opt/renewpro/backups/dashboard_stitch_'+datetime.now().strftime('%Y%m%d_%H%M%S')
  run(c,'mkdir -p '+backup+' && cp -p '+base+'index.html '+backup+'/index.html')
  for name in ['renew_dashboard_stitch.css','renew_dashboard_stitch.js','index.html']:
   s.put(str(r/name),base+name+'.new');s.chmod(base+name+'.new',0o644);s.posix_rename(base+name+'.new',base+name)
   assert s.open(base+name,'rb').read()==(r/name).read_bytes()
  run(c,'curl -fsS -o /dev/null -w "HTTPS %{http_code}\\n" https://renewpanel.xyz/')
  print('BACKUP',backup)
finally:s.close();c.close()

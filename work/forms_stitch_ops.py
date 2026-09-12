from pathlib import Path
from datetime import datetime
import sys,hashlib
from video_v2_ops import ssh,run
r=Path(__file__).resolve().parent/'forms_stitch';r.mkdir(exist_ok=True)
base='/opt/renewpro/app_live/app/static/'
names=['index.html','app.js','renew_forms_v1.js','renew_forms_v1.css','renew_forms_fix_v2.css','renew_mobile_final_v2.css']
c=ssh();s=c.open_sftp();sha=lambda x:hashlib.sha256(x).digest()
try:
 if sys.argv[1]=='fetch':
  (r/'before').mkdir(exist_ok=True)
  for n in names:s.get(base+n,str(r/n));s.get(base+n,str(r/'before'/n))
  print('Fetched',len(names),'live source files')
 elif sys.argv[1]=='deploy':
  for n in names:
   assert sha(s.open(base+n,'rb').read())==sha((r/'before'/n).read_bytes()),'Concurrent change '+n
  backup='/opt/renewpro/backups/forms_stitch_'+datetime.now().strftime('%Y%m%d_%H%M%S')
  run(c,'mkdir -p '+backup+' && cp -p '+base+'index.html '+backup+'/ && nginx -t')
  try:
   for n in ['renew_forms_stitch.css','renew_forms_stitch.js','index.html']:
    s.put(str(r/n),base+n+'.new');s.chmod(base+n+'.new',0o644);s.posix_rename(base+n+'.new',base+n)
    assert sha(s.open(base+n,'rb').read())==sha((r/n).read_bytes())
   run(c,'curl -fsS -o /dev/null -w "HTTPS %{http_code}\\n" https://renewpanel.xyz/')
   print('BACKUP',backup)
  except Exception:
   run(c,'cp -p '+backup+'/index.html '+base+'index.html');raise
finally:s.close();c.close()

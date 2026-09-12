from pathlib import Path
from datetime import datetime
import re,sys
from video_v2_ops import ssh,run
r=Path(__file__).parent/'dashboard_reference_v3';base='/opt/renewpro/app_live/app/';static=base+'static/'
c=ssh();s=c.open_sftp()
try:
 if sys.argv[1]=='fetch':
  p=r/'before';p.mkdir(parents=True,exist_ok=True);s.get(static+'index.html',str(p/'index.html'))
  for n in set(re.findall(r'/static/([\w.-]+\.(?:css|js))',(p/'index.html').read_text(encoding='utf-8'))):s.get(static+n,str(p/n))
  for n in ['calc.py','form_finance.py']:s.get(base+n,str(p/n))
 elif sys.argv[1]=='deploy':
  assert s.open(static+'index.html','rb').read()==(r/'before/index.html').read_bytes(),'Live index changed'
  for n in ['calc.py','form_finance.py']:assert s.open(base+n,'rb').read()==(r/'before'/n).read_bytes(),'Calculation file changed'
  backup='/opt/renewpro/backups/dashboard_reference_v3_'+datetime.now().strftime('%Y%m%d_%H%M%S');run(c,'mkdir -p '+backup+' && cp -p '+static+'index.html '+backup+'/index.html')
  try:
   for n in ['dashboard_reference_v3.css','dashboard_reference_v3.js','index.html']:
    s.put(str(r/n),static+n+'.new');s.chmod(static+n+'.new',0o644);s.posix_rename(static+n+'.new',static+n)
    assert s.open(static+n,'rb').read()==(r/n).read_bytes()
   run(c,'curl -fsS -o /dev/null -w "HTTPS %{http_code}\\n" https://renewpanel.xyz/')
  except Exception:run(c,'cp -p '+backup+'/index.html '+static+'index.html');raise
  print('BACKUP',backup)
finally:s.close();c.close()

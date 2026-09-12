from pathlib import Path
from datetime import datetime
import hashlib,sys
from video_v2_ops import ssh,run
r=Path(__file__).parent/'finance_preview';base='/opt/renewpro/app_live/app/'
c=ssh();s=c.open_sftp();sha=lambda b:hashlib.sha256(b).digest()
try:
 stage='/opt/renewpro/finance_preview_stage'
 run(c,'mkdir -p '+stage)
 for n in ['form_finance.py','test_finance.py']:s.put(str(r/n),stage+'/'+n)
 run(c,'cd /opt/renewpro/app_live && /opt/renewpro/.venv/bin/python '+stage+'/test_finance.py')
 s.get(stage+'/preview_sample.json',str(r/'preview_sample.json'))
 if len(sys.argv)<2 or sys.argv[1]!='deploy':sys.exit(0)
 for n in ['main.py','calc.py','static/index.html','static/renew_forms_stitch.js','static/renew_forms_stitch.css']:
  assert sha(s.open(base+n,'rb').read())==sha((r/'before'/n).read_bytes()),'Concurrent change: '+n
 files=['form_finance.py','static/renew_form_finance.css','static/renew_form_finance.js','main.py','static/index.html']
 for n in files[:3]:
  try:s.stat(base+n)
  except FileNotFoundError:continue
  raise RuntimeError('New target already exists: '+n)
 backup='/opt/renewpro/backups/finance_preview_'+datetime.now().strftime('%Y%m%d_%H%M%S')
 run(c,'mkdir -p '+backup+'/static && cp -p '+base+'main.py '+backup+'/ && cp -p '+base+'static/index.html '+backup+'/static/')
 try:
  for n in files:
   s.put(str(r/n),base+n+'.new');s.chmod(base+n+'.new',0o644);s.posix_rename(base+n+'.new',base+n)
   assert sha(s.open(base+n,'rb').read())==sha((r/n).read_bytes())
  run(c,'/opt/renewpro/.venv/bin/python -m py_compile '+base+'main.py '+base+'form_finance.py && systemctl restart renewpro && systemctl is-active renewpro && nginx -t')
  run(c,'curl --retry 5 --retry-connrefused --retry-delay 1 -fsS -o /dev/null -w "HTTPS %{http_code}\\n" https://renewpanel.xyz/')
  print('BACKUP',backup)
 except Exception:
  run(c,'cp -p '+backup+'/main.py '+base+'main.py && cp -p '+backup+'/static/index.html '+base+'static/index.html && systemctl restart renewpro');raise
finally:s.close();c.close()

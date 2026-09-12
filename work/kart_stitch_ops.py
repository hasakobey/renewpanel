from pathlib import Path
from datetime import datetime
from video_v2_ops import ssh,run
import sys,hashlib
r=Path(__file__).resolve().parent/'kart_stitch';r.mkdir(exist_ok=True)
c=ssh();s=c.open_sftp();base='/var/www/kart.renewpanel.xyz/'
names=['index.html','renew-stitch-v1.css','renew-stitch-v1.js']
sha=lambda b:hashlib.sha256(b).digest()
try:
 if sys.argv[1]=='fetch':
  (r/'before').mkdir(exist_ok=True)
  for n in names:s.get(base+n,str(r/n));s.get(base+n,str(r/'before'/n))
 elif sys.argv[1]=='deploy':
  for n in names:
   with s.open(base+n,'rb') as f:assert sha(f.read())==sha((r/'before_motion'/n).read_bytes()),'Concurrent change '+n
  backup='/var/backups/kart-stitch-motion-'+datetime.now().strftime('%Y%m%d-%H%M%S')
  run(c,'mkdir '+backup+' && cp -p '+ ' '.join(base+n for n in names)+' '+backup+'/ && nginx -t')
  try:
   for n in ['renew-stitch-v1.css','renew-stitch-v1.js','renew-stitch-details.js','index.html']:
    s.put(str(r/n),base+n+'.new');s.chmod(base+n+'.new',0o644);s.posix_rename(base+n+'.new',base+n)
    with s.open(base+n,'rb') as f:assert sha(f.read())==sha((r/n).read_bytes())
    _,o,e=c.exec_command('curl -fsS https://kart.renewpanel.xyz/'+n+'?verify=v4');b=o.read();assert o.channel.recv_exit_status()==0 and sha(b)==sha((r/n).read_bytes())
    print('LOCAL/LIVE/HTTPS HASH MATCH',n)
   run(c,'nginx -t && curl -fsS -o /dev/null -w "HTTPS %{http_code}\\n" https://kart.renewpanel.xyz/')
   print('BACKUP',backup)
  except Exception:
   run(c,'cp -p '+backup+'/* '+base);raise
finally:s.close();c.close()

from pathlib import Path
from datetime import datetime
import sys,hashlib
from video_v2_ops import ssh,run
r=Path(__file__).resolve().parent/'kart_console';r.mkdir(exist_ok=True)
c=ssh();s=c.open_sftp();remote='/var/www/kart.renewpanel.xyz/'
sha=lambda b:hashlib.sha256(b).hexdigest()
try:
 if sys.argv[1]=='fetch':
  s.get(remote+'index.html',str(r/'baseline.html'));s.get(remote+'index.html',str(r/'index.html'))
  for n in ['mail-studio-v1.js','mail-studio-v1.css']:s.get(remote+n,str(r/n))
 elif sys.argv[1]=='deploy':
  with s.open(remote+'index.html','rb') as f:assert sha(f.read())==sha((r/'baseline.html').read_bytes())
  marker=b'<link rel="stylesheet" href="kart-console-v1.css?v=1"/><script defer src="kart-console-v1.js?v=1"></script>'
  assert (r/'index.html').read_bytes().replace(marker,b'')==(r/'baseline.html').read_bytes()
  backup='/var/backups/kart-console-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.html'
  run(c,'nginx -t && cp -p '+remote+'index.html '+backup)
  try:
   for n in ['kart-console-v1.css','kart-console-v1.js','index.html']:
    s.put(str(r/n),remote+n+'.new');s.chmod(remote+n+'.new',0o644);s.posix_rename(remote+n+'.new',remote+n)
    with s.open(remote+n,'rb') as f:assert sha(f.read())==sha((r/n).read_bytes())
    _,o,e=c.exec_command('curl -fsS https://kart.renewpanel.xyz/'+n+'?verify=console1');b=o.read();assert o.channel.recv_exit_status()==0 and sha(b)==sha((r/n).read_bytes())
    print('HASH LOCAL/LIVE/HTTPS OK',n)
   run(c,'nginx -t && curl -fsS -o /dev/null -w "HTTPS %{http_code}\\n" https://kart.renewpanel.xyz/')
   print('BACKUP',backup)
  except Exception:
   run(c,'cp -p '+backup+' '+remote+'index.html');raise
finally:s.close();c.close()

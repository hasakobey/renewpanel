from pathlib import Path
from video_v2_ops import ssh,run
import sys,hashlib,json
from datetime import datetime
r=Path(__file__).resolve().parent/'push_fix';r.mkdir(exist_ok=True)
c=ssh();s=c.open_sftp()
try:
 if sys.argv[1]=='fetch':
  for n in ['notification_service.py','notification_api.py','main.py','db.py','stock_history.py']:
   s.get('/opt/renewpro/app_live/app/'+n,str(r/n))
  run(c,"systemctl is-active renewpro; date -Is; rg -n 'notify_stock|notification_service|purchase|sale' /opt/renewpro/app_live/app/main.py | tail -70")
 elif sys.argv[1]=='stage':
  stage='/opt/renewpro/push_fix_stage'
  run(c,'mkdir -p '+stage)
  for n in ['notification_service.py','test_notifications.py']:s.put(str(r/n),stage+'/'+n)
  run(c,'/opt/renewpro/.venv/bin/python '+stage+'/test_notifications.py')
  run(c,"systemctl show renewpro -p ExecStart --value; cd /opt/renewpro/app_live && /opt/renewpro/.venv/bin/python -c \"from app.db import DB_PATH; import sqlite3; c=sqlite3.connect(DB_PATH); c.row_factory=sqlite3.Row; print(dict(c.execute('SELECT enabled,daily_digest_time FROM notification_settings WHERE id=1').fetchone())); print('ACTIVE_DEVICES',c.execute('SELECT count(*) FROM push_subscriptions WHERE active=1').fetchone()[0])\"")
 elif sys.argv[1]=='deploy':
  base='/opt/renewpro/app_live/app/'
  backup='/opt/renewpro/backups/push_fix_'+datetime.now().strftime('%Y%m%d_%H%M%S')
  run(c,'mkdir -p '+backup+' && cp -p '+base+'main.py '+base+'notification_service.py '+backup+'/')
  for n in ['main.py','notification_service.py']:
   s.put(str(r/n),base+n+'.new');s.chmod(base+n+'.new',0o644);s.posix_rename(base+n+'.new',base+n)
   with s.open(base+n,'rb') as f:assert hashlib.sha256(f.read()).digest()==hashlib.sha256((r/n).read_bytes()).digest()
  try:
   run(c,'cd /opt/renewpro/app_live && /opt/renewpro/.venv/bin/python -m py_compile app/main.py app/notification_service.py')
   run(c,"cd /opt/renewpro/app_live && /opt/renewpro/.venv/bin/python -c \"from app.db import DB_PATH; import sqlite3; c=sqlite3.connect(DB_PATH); c.row_factory=sqlite3.Row; c.execute('UPDATE notification_settings SET daily_digest_time=? WHERE id=1',('09:00',)); c.commit()\"")
   run(c,'systemctl restart renewpro && systemctl is-active renewpro && nginx -t')
   run(c,'curl --retry 5 --retry-connrefused --retry-delay 1 -fsS -o /dev/null -w "HTTPS %{http_code}\\n" https://renewpanel.xyz/')
   print('BACKUP',backup)
  except Exception:
   run(c,'cp -p '+backup+'/main.py '+backup+'/notification_service.py '+base+' && systemctl restart renewpro');raise
 elif sys.argv[1]=='status':
  run(c,"cd /opt/renewpro/app_live && /opt/renewpro/.venv/bin/python -c \"from app.db import DB_PATH; import sqlite3; c=sqlite3.connect(DB_PATH); print(c.execute(\\\"SELECT event_type,sent_at FROM notifications WHERE event_type='daily_stock_digest' ORDER BY id DESC LIMIT 1\\\").fetchall())\"")
  run(c,'systemctl is-active renewpro; journalctl -u renewpro --since "3 minutes ago" --no-pager -p err')
finally:s.close();c.close()

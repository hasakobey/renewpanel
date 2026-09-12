import importlib.util,sys,types,sqlite3,tempfile,contextlib
from pathlib import Path
from datetime import datetime,timezone
package=types.ModuleType('testapp');package.__path__=[];sys.modules['testapp']=package
tmp=tempfile.TemporaryDirectory();path=Path(tmp.name)/'test.db'
@contextlib.contextmanager
def connect():
 c=sqlite3.connect(path);c.row_factory=sqlite3.Row
 try:
  yield c;c.commit()
 finally:c.close()
db=types.ModuleType('testapp.db');db.connect=connect;db.now=lambda:datetime.now().isoformat();sys.modules['testapp.db']=db
history=types.ModuleType('testapp.stock_history');history.load_stock_month=lambda con,month:([{'purchase_date':'2026-01-01'},{'purchase_date':'2026-09-06'}],{});sys.modules['testapp.stock_history']=history
with connect() as c:
 c.executescript('''CREATE TABLE notification_settings(id INTEGER,enabled INTEGER,threshold_days TEXT,daily_digest_time TEXT);INSERT INTO notification_settings VALUES(1,1,'[30,60,90]','09:00');
 CREATE TABLE push_subscriptions(token TEXT,active INTEGER);
 INSERT INTO push_subscriptions VALUES('TEST',1);
 CREATE TABLE notifications(id INTEGER PRIMARY KEY,user_id INTEGER,vehicle_id INTEGER,event_key TEXT UNIQUE,event_type TEXT,title TEXT,body TEXT,target_url TEXT,created_at TEXT,sent_at TEXT);''')
spec=importlib.util.spec_from_file_location('testapp.notification_service',Path(__file__).with_name('notification_service.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
sent=[]
def send(tokens,title,body,url):sent.append(title);return {'sent':1,'failed':0}
m._send_tokens=send
assert not m.run_daily_digest(datetime(2026,9,8,5,59,tzinfo=timezone.utc))['created']
assert m.run_daily_digest(datetime(2026,9,8,6,0,tzinfo=timezone.utc))['created']
assert not m.run_daily_digest(datetime(2026,9,8,7,0,tzinfo=timezone.utc))['created']
assert m.run_daily_digest(datetime(2026,9,9,6,0,tzinfo=timezone.utc))['created']
for kind in ['sale_created','acquisition_created']:
 m.notify_transaction(kind,1,{'plate':'TEST'});m.notify_transaction(kind,1,{'plate':'TEST'})
assert len(sent)==4
def fail(*args):raise RuntimeError('simulated delivery failure')
m._send_tokens=fail;m.notify_transaction('sale_created',2,{'plate':'TEST'})
m._send_tokens=send;m.retry_pending_notifications();assert len(sent)==5
with connect() as c:
 assert c.execute('SELECT count(*) FROM notifications').fetchone()[0]==5
 assert c.execute('SELECT count(*) FROM notifications WHERE sent_at IS NULL').fetchone()[0]==0
 c.execute('UPDATE notification_settings SET enabled=0')
assert not m.run_daily_digest(datetime(2026,9,10,6,0,tzinfo=timezone.utc))['created']
print('PASS: Istanbul 09:00, before-time skip, daily dedup, next day, event dedup, delivery retry, disabled setting')
tmp.cleanup()

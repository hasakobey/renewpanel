from pathlib import Path
from datetime import datetime
import hashlib,sys
from video_v2_ops import ssh,run
root=Path(__file__).resolve().parent/'kart_mail'
names=['index.html','mail-studio-v1.css','mail-studio-v1.js']
base=root/'live_before_v2'
c=ssh();s=c.open_sftp();remote='/var/www/kart.renewpanel.xyz/'
sha=lambda b:hashlib.sha256(b).hexdigest()
try:
    if sys.argv[1]=='inspect':
        base.mkdir(exist_ok=True)
        for name in names:
            s.get(remote+name,str(base/name))
            print(name,'local matches live',sha((root/name).read_bytes())==sha((base/name).read_bytes()))
    elif sys.argv[1]=='deploy':
        for name in names:
            with s.open(remote+name,'rb') as f:assert sha(f.read())==sha((base/name).read_bytes()),'Concurrent change '+name
        assert (root/'index.html').read_bytes().replace(b'?v=2.0.0',b'?v=1.0.0')==(base/'index.html').read_bytes(),'Unexpected HTML change'
        run(c,'nginx -t')
        backup='/var/backups/kart-mail-v2-'+datetime.now().strftime('%Y%m%d-%H%M%S')
        run(c,'mkdir '+backup+' && cp -p '+ ' '.join(remote+n for n in names)+' '+backup+'/')
        try:
            for name in names[1:]+names[:1]:
                s.put(str(root/name),remote+name+'.new');s.chmod(remote+name+'.new',0o644);s.posix_rename(remote+name+'.new',remote+name)
                with s.open(remote+name,'rb') as f:assert sha(f.read())==sha((root/name).read_bytes())
                _,o,e=c.exec_command('curl -fsS https://kart.renewpanel.xyz/'+name+'?verify=v2')
                data=o.read();assert o.channel.recv_exit_status()==0 and sha(data)==sha((root/name).read_bytes())
                print('LOCAL / LIVE / HTTPS MATCH',name)
            run(c,'nginx -t && curl -fsS -o /dev/null -w "HTTPS %{http_code}\\n" https://kart.renewpanel.xyz/')
            print('BACKUP',backup)
        except Exception:
            run(c,'cp -p '+backup+'/* '+remote)
            raise
finally:
    s.close();c.close()

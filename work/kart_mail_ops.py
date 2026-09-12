from pathlib import Path
from video_v2_ops import ssh,run
import sys,hashlib
from datetime import datetime
root=Path(__file__).resolve().parent/'kart_mail';root.mkdir(exist_ok=True)
c=ssh();s=c.open_sftp();remote='/var/www/kart.renewpanel.xyz/index.html'
if sys.argv[1]=='fetch':
    s.get(remote,str(root/'baseline.html'));s.get(remote,str(root/'index.html'))
    print('BASELINE',hashlib.sha256((root/'baseline.html').read_bytes()).hexdigest())
elif sys.argv[1]=='deploy':
    digest=lambda data:hashlib.sha256(data).hexdigest()
    baseline=(root/'baseline.html').read_bytes()
    updated=(root/'index.html').read_bytes()
    injection=b'<link rel="stylesheet" href="mail-studio-v1.css?v=1.0.0"/>\n<script defer src="mail-studio-v1.js?v=1.0.0"></script>\n'
    assert updated.replace(injection,b'')==baseline, 'Unexpected core HTML changes'
    with s.open(remote,'rb') as f:assert digest(f.read())==digest(baseline),'Live changed; abort'
    run(c,'nginx -t')
    backup='/var/backups/kart-mail-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.html'
    run(c,'cp -p '+remote+' '+backup)
    print('BACKUP',backup)
    try:
        for name in ['mail-studio-v1.css','mail-studio-v1.js','index.html']:
            target='/var/www/kart.renewpanel.xyz/'+name
            s.put(str(root/name),target+'.ms-new');s.chmod(target+'.ms-new',0o644);s.posix_rename(target+'.ms-new',target)
            with s.open(target,'rb') as f:assert digest(f.read())==digest((root/name).read_bytes())
            print('LOCAL/LIVE HASH MATCH',name)
        run(c,'nginx -t && curl -fsS -o /dev/null -w "HTTPS %{http_code}\\n" https://kart.renewpanel.xyz/')
        for name in ['index.html','mail-studio-v1.css','mail-studio-v1.js']:
            _,out,err=c.exec_command('curl -fsS https://kart.renewpanel.xyz/'+name+'?verify=mailstudio')
            data=out.read();assert out.channel.recv_exit_status()==0
            assert digest(data)==digest((root/name).read_bytes()),'HTTPS mismatch '+name
            print('HTTPS HASH MATCH',name)
    except Exception:
        run(c,'cp -p '+backup+' '+remote)
        raise
s.close();c.close()

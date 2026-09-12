from pathlib import Path
from datetime import datetime
import hashlib, os, paramiko, shlex

ROOT=Path(__file__).resolve().parent
FILES=["app/main.py","app/video_studio.py","app/static/index.html","app/static/app.js","app/static/renew_video_studio_v1.css","app/static/renew_video_studio_v1.js"]
HOST=os.environ.get("RENEW_SSH_HOST","45.195.231.20")
USER=os.environ.get("RENEW_SSH_USER","root")
PASSWORD=os.environ["RENEW_SSH_PASSWORD"]
c=paramiko.SSHClient();c.set_missing_host_key_policy(paramiko.AutoAddPolicy());c.connect(HOST,username=USER,password=PASSWORD,timeout=25)
backup="/opt/renewpro/backups/video_studio_20260905_090424"
print("using backup",backup)
s=c.open_sftp()
for rel in FILES:
    local=ROOT/"live_ai"/rel; remote="/opt/renewpro/app_live/"+rel; temp=remote+".video-new"
    s.put(str(local),temp); s.chmod(temp,0o644); s.posix_rename(temp,remote)
    with s.open(remote,"rb") as f: remote_hash=hashlib.sha256(f.read()).hexdigest()
    local_hash=hashlib.sha256(local.read_bytes()).hexdigest(); print(rel,local_hash==remote_hash,local_hash)
s.close()
checks=[
 "chown renewpro:renewpro /opt/renewpro/app_live/app/main.py /opt/renewpro/app_live/app/video_studio.py /opt/renewpro/app_live/app/static/index.html /opt/renewpro/app_live/app/static/app.js /opt/renewpro/app_live/app/static/renew_video_studio_v1.css /opt/renewpro/app_live/app/static/renew_video_studio_v1.js",
 "/opt/renewpro/.venv/bin/python3 -m py_compile /opt/renewpro/app_live/app/main.py /opt/renewpro/app_live/app/video_studio.py",
 "systemctl restart renewpro.service && sleep 2 && systemctl is-active renewpro.service",
 "nginx -t",
 "curl -ksS -o /dev/null -w '%{http_code}' https://renewpanel.xyz/",
]
for cmd in checks:
    _,o,e=c.exec_command(cmd); code=o.channel.recv_exit_status(); print("$",cmd,"\n",o.read().decode(),e.read().decode(),"exit",code)
    if code: raise SystemExit(3)
print("BACKUP",backup)
c.close()

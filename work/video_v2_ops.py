"""Targeted RENEW deployment operations; credentials stay in existing local config."""
import ast, hashlib, json, sys, shlex
from pathlib import Path
from datetime import datetime
import paramiko

ROOT=Path(__file__).resolve().parent
FILES=['app/video_studio.py','app/video_render.py','app/static/renew_video_studio_v1.js','app/static/renew_video_studio_v1.css','app/static/index.html']
def ssh():
    tree=ast.parse((ROOT/'deploy_video_studio.py').read_text(encoding='utf-8'))
    call=next(n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='connect')
    args=[ast.literal_eval(x) for x in call.args]; kwargs={x.arg:ast.literal_eval(x.value) for x in call.keywords}
    c=paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy()); c.connect(*args,**kwargs); return c
def run(c,cmd):
    _,o,e=c.exec_command(cmd,timeout=900)
    out=o.read().decode('utf-8',errors='replace'); err=e.read().decode('utf-8',errors='replace'); code=o.channel.recv_exit_status()
    print(out,err,flush=True)
    if code: raise RuntimeError(f'Remote command exit {code}')
def main():
    c=ssh(); s=c.open_sftp(); action=sys.argv[1]
    if action=='inspect':
        folder=ROOT/'video_v2_baseline';folder.mkdir(exist_ok=True)
        for rel in FILES:
            if rel.endswith('video_render.py'):continue
            dst=folder/rel;dst.parent.mkdir(parents=True,exist_ok=True);s.get('/opt/renewpro/app_live/'+rel,str(dst))
            print(rel,'match',hashlib.sha256(dst.read_bytes()).hexdigest()==hashlib.sha256((ROOT/'live_ai'/rel).read_bytes()).hexdigest())
        run(c,"/opt/renewpro/.venv/bin/python -c \"import edge_tts,inspect; print('EDGE',edge_tts.__version__); print(inspect.signature(edge_tts.SubMaker)); print([x for x in dir(edge_tts.SubMaker) if not x.startswith('_')])\"")
        run(c,"pid=$(systemctl show -p MainPID --value renewpro.service); tr '\\0' '\\n' < /proc/$pid/environ | cut -d= -f1 | grep -E 'GEMINI|GOOGLE.*KEY|ELEVEN|AZURE.*SPEECH' || true")
    elif action=='backup':
        stamp=datetime.now().strftime('%Y%m%d_%H%M%S'); path='/opt/renewpro/backups/video_studio_v2_'+stamp
        run(c,'mkdir -p '+path+'/app/static && cp /opt/renewpro/app_live/app/video_studio.py '+path+'/app/ && cp /opt/renewpro/app_live/app/static/renew_video_studio_v1.js /opt/renewpro/app_live/app/static/renew_video_studio_v1.css /opt/renewpro/app_live/app/static/index.html '+path+'/app/static/ && find /opt/renewpro/app_live/vehicle_media -path "*/video/project.json" -print0 | tar --null -T - -czf '+path+'/projects.tar.gz')
        print('BACKUP',path)
    elif action=='stage':
        run(c,'mkdir -p /opt/renewpro/video_v2_stage/app/static')
        for rel in FILES:
            s.put(str(ROOT/'live_ai'/rel),'/opt/renewpro/video_v2_stage/'+rel)
        for name in ['db.py','auth_service.py','auth_context.py','stock_history.py']:
            run(c,'cp /opt/renewpro/app_live/app/'+name+' /opt/renewpro/video_v2_stage/app/'+name)
        s.put(str(ROOT/'test_video_v2.py'),'/opt/renewpro/video_v2_stage/test_video_v2.py')
        run(c,'chown -R renewpro:renewpro /opt/renewpro/video_v2_stage && cd /opt/renewpro/video_v2_stage && runuser -u renewpro -- /opt/renewpro/.venv/bin/python test_video_v2.py')
    elif action=='deploy':
        for rel in FILES:
            remote='/opt/renewpro/app_live/'+rel; local=ROOT/'live_ai'/rel
            if rel!='app/video_render.py':
                baseline=ROOT/'video_v2_baseline'/rel
                with s.open(remote,'rb') as f:before=hashlib.sha256(f.read()).hexdigest()
                if before!=hashlib.sha256(baseline.read_bytes()).hexdigest():raise RuntimeError('Live changed since baseline: '+rel)
            s.put(str(local),remote+'.v2new');s.chmod(remote+'.v2new',0o644);s.posix_rename(remote+'.v2new',remote)
            with s.open(remote,'rb') as f:ok=hashlib.sha256(f.read()).hexdigest()==hashlib.sha256(local.read_bytes()).hexdigest()
            print('HASH',rel,ok)
        run(c,'chown renewpro:renewpro '+ ' '.join('/opt/renewpro/app_live/'+x for x in FILES))
        run(c,'/opt/renewpro/.venv/bin/python -m py_compile /opt/renewpro/app_live/app/video_studio.py /opt/renewpro/app_live/app/video_render.py && systemctl restart renewpro && sleep 2 && systemctl is-active renewpro && nginx -t && curl -fsS -o /dev/null -w "HTTPS %{http_code}\\n" https://renewpanel.xyz/')
    elif action=='polish':
        expected={'app/static/renew_video_studio_v1.js':'58a5aa9f08d13a20d554df41c82a0ab4cac4c4dae3e00b9cdf466f7cf16922fe','app/static/renew_video_studio_v1.css':'2677d9ba6408c42ba541ef0b9ca8f5364eabb06cb207f57c755b47d9c990e8fc','app/static/index.html':'e7be5a6eb330ac7b4c7b180238ed81f9879c5bd080b3e7039cb8a90dbdc1c892'}
        for rel,digest in expected.items():
            with s.open('/opt/renewpro/app_live/'+rel,'rb') as f:
                if hashlib.sha256(f.read()).hexdigest()!=digest:raise RuntimeError('Concurrent change: '+rel)
        for rel in expected:
            remote='/opt/renewpro/app_live/'+rel;local=ROOT/'live_ai'/rel
            s.put(str(local),remote+'.v2new');s.chmod(remote+'.v2new',0o644);s.posix_rename(remote+'.v2new',remote)
            with s.open(remote,'rb') as f:assert hashlib.sha256(f.read()).digest()==hashlib.sha256(local.read_bytes()).digest()
            print('HASH OK',rel)
        run(c,'nginx -t && curl -fsS -o /dev/null -w "HTTPS %{http_code}\\n" https://renewpanel.xyz/')
    elif action=='fetch':
        local=ROOT.parent/'output'/'video_studio_v2';local.mkdir(parents=True,exist_ok=True)
        s.get(sys.argv[2],str(local/sys.argv[3]));print(str(local/sys.argv[3]))
    elif action=='command':run(c,sys.argv[2])
    s.close();c.close()
if __name__=='__main__':main()

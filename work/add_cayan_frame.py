from video_v2_ops import ssh, run, ROOT
import hashlib,sys
expected={'app/video_render.py':'602f758bbcbb151aed267cab0c27987f24e2bb89668baa5341686d9d54833963','app/static/renew_video_studio_v1.js':'d5fc611c71c5659d2c84b84db0422c91310b11ab8034afdd0b38342e3bd064a7','app/static/index.html':'ec4438b77962a60dc9a5cc82039cf6c58bac244b3643c5a65ef83a776c637615'}
# The exact baseline is checked before any live write.
asset='app/static/renew_cayan_cover_frame_v1.png'
c=ssh();s=c.open_sftp();stage='/opt/renewpro/cayan_frame_stage/'
if sys.argv[1]=='stage':
    run(c,'mkdir -p '+stage+'app/static')
    for rel in [*expected,asset]:s.put(str(ROOT/'live_ai'/rel),stage+rel)
    s.put(str(ROOT/'test_cayan_frame.py'),stage+'test_cayan_frame.py')
    run(c,'cd '+stage+' && /opt/renewpro/.venv/bin/python test_cayan_frame.py')
elif sys.argv[1]=='deploy':
    for rel,digest in expected.items():
        with s.open('/opt/renewpro/app_live/'+rel,'rb') as f:assert hashlib.sha256(f.read()).hexdigest()==digest,'Concurrent change: '+rel
    run(c,'mkdir -p /opt/renewpro/backups/cayan_frame_20260905/app/static && cp /opt/renewpro/app_live/app/video_render.py /opt/renewpro/backups/cayan_frame_20260905/app/ && cp /opt/renewpro/app_live/app/static/renew_video_studio_v1.js /opt/renewpro/app_live/app/static/index.html /opt/renewpro/backups/cayan_frame_20260905/app/static/')
    for rel in [asset,*expected]:
        remote='/opt/renewpro/app_live/'+rel;local=ROOT/'live_ai'/rel
        s.put(str(local),remote+'.new');s.chmod(remote+'.new',0o644);s.posix_rename(remote+'.new',remote)
        with s.open(remote,'rb') as f:assert hashlib.sha256(f.read()).digest()==hashlib.sha256(local.read_bytes()).digest()
        print('HASH OK',rel)
    run(c,'systemctl restart renewpro && sleep 2 && systemctl is-active renewpro && nginx -t && curl -fsS -o /dev/null -w "HTTPS %{http_code}\\n" https://renewpanel.xyz/')
s.close();c.close()

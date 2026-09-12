"""Publish only the eight authorized advertisement photos for this external render."""
import json,uuid,shlex
from pathlib import Path
from video_v2_ops import ssh,run

out=Path(__file__).resolve().parent.parent/'output'/'json2video';out.mkdir(parents=True,exist_ok=True)
c=ssh();s=c.open_sftp();root='/opt/renewpro/app_live/vehicle_media/10ANK557/'
with s.open(root+'meta.json') as f:meta=json.load(f)
with s.open(root+'video/project.json') as f:p=json.load(f)
token=uuid.uuid4().hex;folder='/opt/renewpro/app_live/app/static/j2v_'+token
run(c,'mkdir '+folder)
urls=[]
for i,n in enumerate(p['slots']):
    rel=meta['slots'][str(n)]
    assert rel.startswith('listing/') and '..' not in rel
    name=f'{i+1}.jpg';run(c,'cp '+shlex.quote(root+rel)+' '+folder+'/'+name+' && chmod 644 '+folder+'/'+name)
    urls.append('https://renewpanel.xyz/static/j2v_'+token+'/'+name)
frame='/opt/renewpro/app_live/app/static/renew_cayan_cover_frame_v1.png'
run(c,'ffmpeg -hide_banner -loglevel error -i '+frame+' -vf crop=1024:146:0:0 -frames:v 1 '+folder+'/header.png')
run(c,'ffmpeg -hide_banner -loglevel error -i '+frame+' -vf crop=1024:457:0:1079 -frames:v 1 '+folder+'/footer.png')
base='https://renewpanel.xyz/static/j2v_'+token
manifest={'folder':folder,'base':base,'photos':urls,'plate':'10ANK557','slots':p['slots'],'purpose':'JSON2Video user-authorized advertisement assets; no originals modified'}
(out/'assets.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False));s.close();c.close()

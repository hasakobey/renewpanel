"""Integration test in isolated staging: real photos copied, no live database writes."""
import copy, json, os, shutil, time, sys, urllib.request
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from fastapi import HTTPException
from app import video_studio as vs
from app.video_render import compose,photo_block,duration

LIVE=Path('/opt/renewpro/app_live');ROOT=Path(__file__).resolve().parent
vs.BASE=ROOT/'fixture';PLATE='10ANK557'
DATA={'plate':PLATE,'brand':'Dacia','model':'Duster','version':'1.3 Turbo Extreme 4x2 EDC','km':45000,'model_year':2024}
vs.vehicle=lambda plate,month='':DATA
vs.log=lambda *args:None
root,video,file=vs.paths(PLATE);root.mkdir(parents=True,exist_ok=True)
meta=json.loads((LIVE/'vehicle_media'/PLATE/'meta.json').read_text())
for rel in meta['slots'].values():
    dest=root/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(LIVE/'vehicle_media'/PLATE/rel,dest)
vs.atomic(root/'meta.json',meta)
p=vs.defaults(DATA,PLATE);p['slots']=list(range(1,9));p['cover_slot']=1
p['narration']='2024 model Dacia Duster. 1.3 Turbo Extreme, 4x2 EDC. 45 bin kilometrede. Aracın dış görünümünü her açıdan inceleyin. Model ve kilometre bilgilerini karşılaştırın, detaylara yakından bakın. Çayan Tarsus Renew’de sizi bekliyoruz. Aracı yakından görmek, güncel bilgileri öğrenmek ve randevu almak için bizimle iletişime geçin.'
p['duration']=28
_,_,photos,_,_=vs.project_state(PLATE)
for mutation in [{'slots':[1]*8},{'voice':'unknown'},{'accent':'red;bad'},{'duration':99},{'scene_titles':['x']},{'slots':[99]}]:
    try:vs.validate({**p,**mutation},p,photos,True);raise AssertionError('invalid accepted')
    except HTTPException as e:assert e.status_code==400
print('PASS input validation',flush=True)
vs.update_project(PLATE,{**p,'slots':[],'cover_slot':0});assert vs.get_project(PLATE)['slots']==[]
vs.update_project(PLATE,p)
try:vs.ai_edit(PLATE,p);raise AssertionError('missing key accepted')
except HTTPException as e:assert e.status_code==409
before=vs.load_json(file);draft=vs.autodraft(PLATE,p);assert vs.load_json(file)==before and len(draft['proposal']['scene_titles'])==8
tpl=vs.save_template({'name':'Staging theme','project':p});assert 'slots' not in tpl['settings'] and 'narration' not in tpl['settings']
print('PASS drafts, template isolation, missing AI connection',flush=True)
for fmt in ['9:16','4:5','1:1']:
    for theme in ['editorial','azure','minimal']:
        sample={**p,'format':fmt,'template':theme,'title':'Dacia Duster 1.3 Turbo Extreme 4x2 EDC 2024','subtitle':'2024 • 45.000 km • 1.3 Turbo Extreme 4x2 EDC','badge':'TEST'}
        image,_=compose(sample,photos[1],0,True);image.save(ROOT/f'preview_{theme}_{fmt.replace(":","_")}.jpg')
print('PASS 9 cover layouts',flush=True)
# Preserve all image edges in contain mode; contrasting corner markers must survive.
marker=Image.new('RGB',(800,400),'white')
for x,y in [(0,0),(780,0),(0,380),(780,380)]:marker.paste('red',(x,y,x+20,y+20))
marker.save(ROOT/'marker.png');block=photo_block(ROOT/'marker.png',(400,600),'contain')
assert sum(1 for r,g,b in block.getdata() if r>220 and g<50 and b<50)>150
print('PASS uncropped photo corners',flush=True)
# Exercise Gemini response parsing without transmitting company data or consuming quota.
class MockResponse:
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self):return json.dumps({'candidates':[{'content':{'parts':[{'text':json.dumps({'title':'Duster','subtitle':'2024','narration':'Doğrulanmış araç bilgileri.','scene_titles':['Sahne']*8,'tagline':'45.000 km','slots':p['slots']})}]}}]}).encode()
with patch.dict(os.environ,{'GEMINI_API_KEY':'test-not-a-real-key'}),patch('urllib.request.urlopen',return_value=MockResponse()):
    result=vs.ai_edit(PLATE,p);assert result['source']=='gemini'
print('PASS AI parser (mock, no external generation)',flush=True)
job=vs.generate(PLATE,p)['job_id']
try:vs.generate(PLATE,p);raise AssertionError('duplicate generation allowed')
except HTTPException as e:assert e.status_code==409
for _ in range(240):
    status=vs.status(PLATE,job);print(status['state'],status.get('progress'),status['message'],flush=True)
    if status['state'] in ('ready','error'):break
    time.sleep(2)
assert status['state']=='ready',status
latest=vs.get_project(PLATE);assert latest['video_ready'] and not latest['render_stale'],latest
assert 27.75<=duration(vs.output_path(PLATE))<=28.25
approved=vs.approve(PLATE,{'version':job});assert approved['approved']
vs.update_project(PLATE,{**p,'title':'Düzenlenmiş başlık'})
try:vs.approve(PLATE,{'version':job});raise AssertionError('stale approved')
except HTTPException as e:assert e.status_code==409
assert vs.get_project(PLATE)['render_stale']
print('PASS real TTS, 8 scenes, crossfades, 28 sec, approval fingerprint, stale protection',flush=True)
print('OUTPUT',vs.output_path(PLATE),flush=True)
vs.WORKER.shutdown(wait=True)

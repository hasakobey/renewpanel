import importlib.util,json,ast
from pathlib import Path
from PIL import Image,ImageChops
spec=importlib.util.spec_from_file_location('renderer','app/video_render.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
root=Path('/opt/renewpro/app_live/vehicle_media/10ANK557')
p=json.loads((root/'video/project.json').read_text());before=dict(p);p['template']='cayan_frame'
meta=json.loads((root/'meta.json').read_text());source=root/meta['slots'][str(p['slots'][0])]
frame=Image.open(m.FRAME_PATH).convert('RGB');header=frame.crop((0,0,1024,146)).resize((1080,154),Image.Resampling.LANCZOS)
for fmt,size in m.FORMATS.items():
    p['format']=fmt;im,box=m.compose(p,source,0,True)
    assert im.size==size and box[3]>0
    assert ImageChops.difference(im.crop((0,0,1080,154)),header).getbbox() is None
    im.save('preview_'+fmt.replace(':','_')+'.jpg',quality=95)
    print('PASS frame',fmt,box)
p['template']='editorial';im,box=m.compose(p,source,0,True);assert im.size==(1080,1080)
old=ast.parse(Path('/opt/renewpro/app_live/app/video_render.py').read_text());new=ast.parse(Path('app/video_render.py').read_text())
for name in ['synthesize','voice_audio']:
    a=next(n for n in old.body if getattr(n,'name',None)==name);b=next(n for n in new.body if getattr(n,'name',None)==name)
    assert ast.dump(a)==ast.dump(b)
print('PASS existing theme and unchanged TTS')
m.captions('1\n00:00:00,000 --> 00:00:02,000\nTest\n',Path('test.ass'),1920,1,margin_v=510)
assert ',78,78,510,1' in Path('test.ass').read_text(encoding='utf-8-sig')
print('PASS captions above contact footer; no project writes')

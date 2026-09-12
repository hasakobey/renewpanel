"""RENEW video compositor. Every output uses the same cover/scene compositor."""
from __future__ import annotations
import asyncio, hashlib, json, math, os, re, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

FORMATS = {'9:16': (1080,1920), '4:5': (1080,1350), '1:1': (1080,1080)}
STYLES = {
    'editorial': {'name':'Beyaz Editorial', 'accent':'#1764c0','background':'#f5f7fb','ink':'#18314c','fit':'contain'},
    'azure': {'name':'Azure Motion', 'accent':'#087dba','background':'#edf8fc','ink':'#123d55','fit':'blur'},
    'minimal': {'name':'Minimal Studio', 'accent':'#776345','background':'#f6f3ed','ink':'#34312c','fit':'contain'},
    'cayan_frame': {'name':'Çayan Kurumsal', 'accent':'#111111','background':'#f3f5f8','ink':'#111111','fit':'contain'},
}

FRAME_PATH = Path(__file__).parent/'static'/'renew_cayan_cover_frame_v1.png'

def compose_cayan(project, source, index):
    """Keep the supplied branding bands intact, adapting only the photo opening."""
    w,h=FORMATS[project['format']]
    with Image.open(FRAME_PATH) as raw: frame=raw.convert('RGB')
    # Boundaries in the approved 1024 x 1536 master. Never stretch its logos/text.
    sx=frame.width/1024;sy=frame.height/1536
    header=frame.crop((0,0,frame.width,round(146*sy)))
    footer=frame.crop((0,round(1079*sy),frame.width,frame.height))
    hh=round(header.height*w/frame.width);fh=round(footer.height*w/frame.width)
    image=Image.new('RGB',(w,h),'#f3f5f8')
    image.paste(header.resize((w,hh),Image.Resampling.LANCZOS),(0,0))
    image.paste(footer.resize((w,fh),Image.Resampling.LANCZOS),(0,h-fh))
    area=(w,h-hh-fh)
    block=photo_block(source,area,project['scene_fits'][index],'#f3f5f8',(project['focal_x']/100,project['focal_y']/100))
    image.paste(block,(0,hh))
    return image,(0,hh,*area)

def font(size, bold=False):
    names = [f'/usr/share/fonts/truetype/dejavu/DejaVuSans{"-Bold" if bold else ""}.ttf',
             'C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf']
    return ImageFont.truetype(next(x for x in names if Path(x).is_file()),max(11,int(size)))

def fittext(draw, text, width, size, bold=True):
    while size>18 and draw.textlength(text,font=font(size,bold))>width: size-=1
    if draw.textlength(text,font=font(size,bold))>width:
        while text and draw.textlength(text+'…',font=font(size,bold))>width:text=text[:-1]
        text+='…'
    return text, font(size,bold)

def textline(draw, xy, text, width, size, fill, bold=True):
    text,f=fittext(draw,str(text or ''),width,size,bold);draw.text(xy,text,font=f,fill=fill)

def photo_block(source: Path, size, fit='contain', bg='#e8edf4', focal=(.5,.5)):
    with Image.open(source) as raw: image=ImageOps.exif_transpose(raw).convert('RGB')
    w,h=size
    if fit=='fill':return ImageOps.fit(image,size,Image.Resampling.LANCZOS,centering=focal)
    block=Image.new('RGB',size,bg)
    if fit=='blur':
        block=ImageOps.fit(image,size,Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(35))
        block=Image.blend(block,Image.new('RGB',size,bg),.35)
    # Margin protects the entire vehicle during the small motion used by the renderer.
    fitted=ImageOps.contain(image,(int(w*.92),int(h*.92)),Image.Resampling.LANCZOS)
    block.paste(fitted,((w-fitted.width)//2,(h-fitted.height)//2))
    return block

def compose(project, source: Path, index=0, cover=False):
    if project['template']=='cayan_frame':return compose_cayan(project,source,index)
    w,h=FORMATS[project['format']]; scale=w/1080; margin=64
    style=STYLES[project['template']];accent=project['accent'];bg=style['background'];ink=style['ink']
    img=Image.new('RGB',(w,h),bg);d=ImageDraw.Draw(img)
    d.rounded_rectangle((margin,60,margin+64,124),16,fill=accent)
    d.text((margin+18,64),'R',font=font(43,True),fill='white')
    textline(d,(margin+85,63),project['brand_name'],w-300,29,ink)
    textline(d,(margin+86,105),'VİDEO KOLEKSİYONU',w-300,14,accent)
    textline(d,(w-190,84),project['plate'],145,20,ink)
    d.line((margin,150,w-margin,150),fill='#d9e0e8',width=2)
    title=project['title'] if cover else project['scene_titles'][index]
    if not title:title=project['title']
    title_size=74 if h>1400 else 57
    textline(d,(margin,191),title,w-2*margin,title_size,ink)
    textline(d,(margin,285 if h>1400 else 268),project['subtitle'],w-2*margin,27,accent,False)
    top=370 if h>1400 else 325
    bottom=h-440 if h>1400 else h-365
    area=(w-2*margin,bottom-top)
    block=photo_block(source,area,project['scene_fits'][index],bg,(project['focal_x']/100,project['focal_y']/100))
    mask=Image.new('L',area,0);ImageDraw.Draw(mask).rounded_rectangle((0,0,*area),22,fill=255)
    img.paste(block,(margin,top),mask);d=ImageDraw.Draw(img)
    # Scene-specific detail and closing CTA stay out of the vehicle photo.
    textline(d,(margin,bottom+30),project['tagline'] if cover else project['scene_titles'][index],w-2*margin,32,ink)
    if project['badge']:
        label,f=fittext(d,project['badge'],w-2*margin-38,23,True)
        bw=int(d.textlength(label,font=f))+36
        d.rounded_rectangle((margin,bottom+85,margin+bw,bottom+136),12,fill=accent)
        d.text((margin+18,bottom+95),label,font=f,fill='white')
    d.line((margin,h-164,w-margin,h-164),fill='#d9e0e8',width=2)
    textline(d,(margin,h-130),project['cta'],w-2*margin,27,ink)
    textline(d,(margin,h-82),project['contact'],w-2*margin,21,accent,False)
    for j in range(8):
        x=margin+j*(w-2*margin)/8
        d.rounded_rectangle((x,h-30,x+(w-2*margin)/8-9,h-25),2,fill=accent if j<=index else '#d4dde7')
    return img,(margin,top,area[0],area[1])

def run(args, work, timeout=300):
    completed=subprocess.run(args,cwd=work,capture_output=True,timeout=timeout)
    if completed.returncode:
        (work/'render-error.log').write_bytes(completed.stderr)
        raise RuntimeError('Video işlenemedi; üretim kaydı saklandı. Yeniden deneyin.')
    return completed.stdout

def duration(path):
    return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(path)],timeout=20))

async def synthesize(project, target: Path):
    import edge_tts
    communicate=edge_tts.Communicate(project['narration'],project['voice'],rate=f"{project['rate']:+d}%",pitch=f"{project['pitch']:+d}Hz",volume='+0%')
    subs=edge_tts.SubMaker()
    with target.open('wb') as output:
        async for chunk in communicate.stream():
            if chunk['type']=='audio':output.write(chunk['data'])
            elif chunk['type'] in ('WordBoundary','SentenceBoundary'):subs.feed(chunk)
    target.with_suffix('.srt').write_text(subs.get_srt(),encoding='utf-8')

def voice_audio(project, directory):
    identity=json.dumps({k:project[k] for k in ('narration','voice','rate','pitch')},sort_keys=True,ensure_ascii=False)
    key=hashlib.sha256(identity.encode()).hexdigest()[:24]
    target=directory/f'voice_{key}.mp3'
    if not target.exists():
        temp=directory/f'voice_{key}.part.mp3'
        asyncio.run(asyncio.wait_for(synthesize(project,temp),timeout=80))
        temp.replace(target); temp.with_suffix('.srt').replace(target.with_suffix('.srt'))
    return target

def ass_time(seconds):return f'{int(seconds)//3600}:{int(seconds)//60%60:02d}:{seconds%60:05.2f}'

def captions(srt, target, height, speed, delay=.25, margin_v=192):
    # These timings come from TTS boundaries and use the identical speech speed correction.
    header=f'[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: {height}\nWrapStyle: 0\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,DejaVu Sans,30,&H00FFFFFF,&H00FFFFFF,&H00301B0D,&H00301B0D,-1,0,0,0,100,100,0,0,3,12,0,2,78,78,192,1\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'
    def secs(s):
        h,m,v=s.replace(',','.').split(':');return int(h)*3600+int(m)*60+float(v)
    for block in re.split(r'\n\s*\n',srt.strip()):
        lines=block.splitlines()
        if len(lines)<3 or ' --> ' not in lines[1]:continue
        a,b=lines[1].split(' --> ');words=' '.join(lines[2:]).replace('\\','').replace('{','').replace('}','')
        # Avoid very long single lines in landscape-derived captions.
        parts=words.split();groups=[];current=[]
        for word in parts:
            current.append(word)
            if len(' '.join(current))>43:groups.append(' '.join(current));current=[]
        if current:groups.append(' '.join(current))
        start=secs(a)/speed+delay;end=secs(b)/speed+delay
        for i,text in enumerate(groups):
            sa=start+(end-start)*i/len(groups);sb=start+(end-start)*(i+1)/len(groups)
            header+=f'Dialogue: 0,{ass_time(sa)},{ass_time(sb)},Default,,0,0,0,,{text}\n'
    header=header.replace(',78,78,192,1\n',f',78,78,{margin_v},1\n')
    target.write_text(header,encoding='utf-8-sig')

def render(project, photos, work: Path, progress):
    work.mkdir(parents=True,exist_ok=True);voice=None;speed=1;total=float(project['duration'])
    if project['narration'].strip() and project['voice_enabled']:
        progress(8,'Türkçe seslendirme hazırlanıyor')
        voice=voice_audio(project,work.parent.parent/'audio')
        vd=duration(voice);speed=max(1,vd/(total-.75))
        if speed>1.30:raise ValueError('Seslendirme seçilen süre için uzun. Metni kısaltın veya süreyi 30 saniyeye çıkarın.')
    n=len(project['slots']);overlap=.4 if project['transition']!='cut' else 0
    length=(total+(n-1)*overlap)/n;frames=round(length*30);length=frames/30
    w,h=FORMATS[project['format']]
    for i,slot in enumerate(project['slots']):
        image,box=compose(project,photos[slot],i,cover=i==0); image.save(work/f'scene_{i}.png')
        if i==0:image.save(work/'cover.jpg',quality=95)
        x,y,bw,bh=box
        # Animate inside the protected photo area; labels and the canvas remain stationary.
        if project['motion']!='none':
            image.crop((x,y,x+bw,y+bh)).save(work/f'photo_{i}.png')
            z=f'1+0.035*on/{frames}' if project['motion']=='gentle' or i%2==0 else f'1.035-0.035*on/{frames}'
            filt=f"[1:v]scale={bw*2}:{bh*2},zoompan=z='{z}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={frames}:s={bw}x{bh}:fps=30[p];[0:v][p]overlay={x}:{y}:shortest=1,setsar=1,format=yuv420p[v]"
            args=['-loop','1','-framerate','30','-i',f'scene_{i}.png','-i',f'photo_{i}.png','-filter_complex',filt,'-map','[v]']
        else:args=['-loop','1','-framerate','30','-i',f'scene_{i}.png','-vf','setsar=1,format=yuv420p']
        run(['ffmpeg','-hide_banner','-loglevel','error','-y','-filter_complex_threads','1',*args,'-t',str(length),'-an','-c:v','libx264','-threads','2','-preset','veryfast','-crf','21',f'clip_{i}.mp4'],work)
        progress(15+int((i+1)*6),f'{i+1}/8 sahne hazır')
    current='clip_0.mp4';elapsed=length
    for i in range(1,n):
        out=f'mix_{i}.mp4'
        if overlap:
            transition={'fade':'fade','slide':'slideleft','smooth':'smoothleft'}[project['transition']]
            filt=f'[0:v]settb=AVTB,setpts=PTS-STARTPTS[a];[1:v]settb=AVTB,setpts=PTS-STARTPTS[b];[a][b]xfade=transition={transition}:duration=0.4:offset={elapsed-overlap:.5f},format=yuv420p[v]'
        else:filt='[0:v][1:v]concat=n=2:v=1:a=0,format=yuv420p[v]'
        run(['ffmpeg','-hide_banner','-loglevel','error','-y','-filter_complex_threads','1','-i',current,'-i',f'clip_{i}.mp4','-filter_complex',filt,'-map','[v]','-c:v','libx264','-threads','2','-preset','veryfast','-crf','21',out],work)
        current=out;elapsed+=length-overlap;progress(65+i*3,'Geçişler birleştiriliyor')
    args=['ffmpeg','-hide_banner','-loglevel','error','-y','-i',current]
    if voice:
        args+=['-i',str(voice),'-af',f'atempo={speed:.6f},loudnorm=I=-16:TP=-1.5:LRA=11,adelay=250|250,apad','-map','0:v','-map','1:a','-c:a','aac','-b:a','192k']
    if project['captions'] and voice and voice.with_suffix('.srt').is_file():
        captions(voice.with_suffix('.srt').read_text(encoding='utf-8'),work/'captions.ass',h,speed,margin_v=510 if project['template']=='cayan_frame' else 192)
        args+=['-vf','ass=captions.ass','-c:v','libx264','-threads','2','-preset','veryfast','-crf','21']
    else:args+=['-c:v','copy']
    args+=['-t',str(total),'-movflags','+faststart','video.mp4'];run(args,work)
    meta=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json','video.mp4'],work))
    measured=float(meta['format']['duration'])
    if abs(measured-total)>.25:raise ValueError('Video süresi doğrulanamadı.')
    (work/'media-info.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    progress(98,'Video ve ses doğrulandı')
    return {'duration':round(measured,2),'size':(work/'video.mp4').stat().st_size,'width':w,'height':h}

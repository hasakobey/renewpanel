from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import shutil, re, zipfile, json, os, subprocess, sys

router=APIRouter(prefix='/api/media',tags=['media-center'])
BASE=Path(__file__).resolve().parents[1]
ROOT=BASE/'vehicle_media'
PHOTO_EXT={'.jpg','.jpeg','.png','.webp'}
DOC_EXT={'.pdf','.jpg','.jpeg','.png','.webp','.doc','.docx','.xls','.xlsx','.txt'}
FOLDERS=('original','listing','documents','archive')

def safe_plate(v:str)->str:
    p=re.sub(r'[^A-Za-z0-9_-]','',str(v or '').upper())
    if not p: raise HTTPException(400,'Plaka zorunlu.')
    return p

def root_for(plate:str):
    root=ROOT/safe_plate(plate)
    for f in FOLDERS:(root/f).mkdir(parents=True,exist_ok=True)
    return root

def meta_path(root):return root/'meta.json'
def load_meta(root):
    d={'cover':'','order':[],'labels':{}}
    p=meta_path(root)
    if p.exists():
        try:
            x=json.loads(p.read_text(encoding='utf-8'))
            if isinstance(x,dict):d.update(x)
        except:pass
    return d

def save_meta(root,d):meta_path(root).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def clean_name(name,ext):
    s=re.sub(r'[<>:"/\\|?*]','-',str(name or '').strip()).strip('. ')
    return (s or 'dosya')[:100]+ext.lower()
def unique_path(folder,name):
    p=folder/name
    if not p.exists():return p
    i=2
    while True:
        q=folder/f'{p.stem}_{i}{p.suffix}'
        if not q.exists():return q
        i+=1

@router.get('/{plate}')
def list_media(plate:str):
    p=safe_plate(plate);root=root_for(p);meta=load_meta(root)
    out={'plate':p,'root':str(root),'cover':meta.get('cover',''),'folders':{}}
    for kind in FOLDERS:
        arr=[]
        for f in sorted((root/kind).iterdir(),key=lambda x:x.stat().st_mtime):
            if not f.is_file():continue
            ext=f.suffix.lower()
            if kind=='documents':
                if ext not in DOC_EXT:continue
            elif ext not in PHOTO_EXT:continue
            key=f'{kind}/{f.name}'
            arr.append({'name':f.name,'kind':kind,'size':f.stat().st_size,'url':f'/api/media/{p}/file/{kind}/{f.name}','is_cover':meta.get('cover')==key,'label':meta.get('labels',{}).get(key,''),'order':(meta.get('order',[]).index(key)+1) if key in meta.get('order',[]) else 9999})
        if kind=='listing':arr.sort(key=lambda x:(x['order'],x['name']))
        out['folders'][kind]=arr
    return out

@router.post('/upload')
async def upload_media(plate:str=Form(...),kind:str=Form('original'),files:list[UploadFile]=File(...)):
    p=safe_plate(plate);root=root_for(p)
    if kind not in FOLDERS:raise HTTPException(400,'Geçersiz klasör.')
    allowed=DOC_EXT if kind=='documents' else PHOTO_EXT;saved=[]
    for f in files:
        ext=Path(f.filename or '').suffix.lower()
        if ext not in allowed:continue
        stem=re.sub(r'[^A-Za-z0-9ÇĞİÖŞÜçğıöşü _-]','_',Path(f.filename or 'dosya').stem)[:60].strip() or 'dosya'
        target=unique_path(root/kind,clean_name(stem,ext))
        with target.open('wb') as w:shutil.copyfileobj(f.file,w)
        saved.append(target.name)
    return {'ok':True,'count':len(saved),'saved':saved,'plate':p,'kind':kind}

@router.get('/{plate}/file/{kind}/{name}')
def get_file(plate:str,kind:str,name:str):
    if kind not in FOLDERS:raise HTTPException(400,'Geçersiz klasör.')
    p=root_for(plate)/kind/Path(name).name
    if not p.exists():raise HTTPException(404,'Dosya bulunamadı.')
    return FileResponse(p)

@router.post('/{plate}/rename')
def rename_media(plate:str,payload:dict):
    kind=payload.get('kind');old=Path(str(payload.get('name',''))).name;new_title=str(payload.get('new_name','')).strip()
    if kind not in FOLDERS:raise HTTPException(400,'Geçersiz klasör.')
    root=root_for(plate);src=root/kind/old
    if not src.exists():raise HTTPException(404,'Dosya bulunamadı.')
    dst=unique_path(root/kind,clean_name(new_title,src.suffix));meta=load_meta(root);oldkey=f'{kind}/{src.name}';newkey=f'{kind}/{dst.name}'
    src.rename(dst)
    if meta.get('cover')==oldkey:meta['cover']=newkey
    meta['order']=[newkey if x==oldkey else x for x in meta.get('order',[])]
    if oldkey in meta.get('labels',{}):meta.setdefault('labels',{})[newkey]=meta['labels'].pop(oldkey)
    save_meta(root,meta);return {'ok':True,'name':dst.name}

@router.post('/{plate}/move')
def move_media(plate:str,payload:dict):
    src_kind=payload.get('from');dst_kind=payload.get('to');name=Path(str(payload.get('name',''))).name
    if src_kind not in FOLDERS or dst_kind not in FOLDERS:raise HTTPException(400,'Geçersiz klasör.')
    root=root_for(plate);src=root/src_kind/name
    if not src.exists():raise HTTPException(404,'Dosya bulunamadı.')
    dst=unique_path(root/dst_kind,src.name);meta=load_meta(root);oldkey=f'{src_kind}/{src.name}';newkey=f'{dst_kind}/{dst.name}'
    shutil.move(str(src),str(dst))
    if meta.get('cover')==oldkey:meta['cover']=newkey
    meta['order']=[newkey if x==oldkey else x for x in meta.get('order',[])]
    if oldkey in meta.get('labels',{}):meta.setdefault('labels',{})[newkey]=meta['labels'].pop(oldkey)
    save_meta(root,meta);return {'ok':True,'name':dst.name}

@router.post('/{plate}/cover')
def set_cover(plate:str,payload:dict):
    kind=payload.get('kind');name=Path(str(payload.get('name',''))).name
    if kind not in ('original','listing'):raise HTTPException(400,'Kapak fotoğrafı orijinal veya ilan klasöründen seçilebilir.')
    root=root_for(plate);p=root/kind/name
    if not p.exists():raise HTTPException(404,'Fotoğraf bulunamadı.')
    meta=load_meta(root);meta['cover']=f'{kind}/{name}';save_meta(root,meta);return {'ok':True}

@router.post('/{plate}/listing-order')
def listing_order(plate:str,payload:dict):
    names=[Path(str(x)).name for x in payload.get('names',[])];root=root_for(plate);meta=load_meta(root)
    valid=[f'listing/{x}' for x in names if (root/'listing'/x).exists()]
    rest=[f'listing/{f.name}' for f in (root/'listing').iterdir() if f.is_file() and f'listing/{f.name}' not in valid]
    meta['order']=valid+rest;save_meta(root,meta);return {'ok':True,'count':len(valid)}

@router.post('/{plate}/label')
def set_label(plate:str,payload:dict):
    kind=payload.get('kind');name=Path(str(payload.get('name',''))).name;label=str(payload.get('label','')).strip()
    if kind not in FOLDERS:raise HTTPException(400,'Geçersiz klasör.')
    root=root_for(plate);p=root/kind/name
    if not p.exists():raise HTTPException(404,'Dosya bulunamadı.')
    meta=load_meta(root);meta.setdefault('labels',{})[f'{kind}/{name}']=label;save_meta(root,meta);return {'ok':True}

@router.delete('/{plate}/{kind}/{name}')
def delete_media(plate:str,kind:str,name:str):
    if kind not in FOLDERS:raise HTTPException(400,'Geçersiz klasör.')
    root=root_for(plate);p=root/kind/Path(name).name;meta=load_meta(root);key=f'{kind}/{p.name}'
    if p.exists():p.unlink()
    if meta.get('cover')==key:meta['cover']=''
    meta['order']=[x for x in meta.get('order',[]) if x!=key];meta.get('labels',{}).pop(key,None);save_meta(root,meta);return {'ok':True}

@router.get('/{plate}/backup')
def backup_vehicle_media(plate:str):
    p=safe_plate(plate);root=root_for(p);out=root/f'{p}_MEDYA_YEDEK.zip'
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for f in root.rglob('*'):
            if f.is_file() and f!=out:z.write(f,f.relative_to(root))
    return FileResponse(out,filename=out.name,media_type='application/zip')

@router.get('/{plate}/listing-zip')
def listing_zip(plate:str):
    p=safe_plate(plate);root=root_for(p);meta=load_meta(root)
    files=[x for x in meta.get('order',[]) if x.startswith('listing/') and (root/x).exists()]
    for f in (root/'listing').iterdir():
        key=f'listing/{f.name}'
        if f.is_file() and f.suffix.lower() in PHOTO_EXT and key not in files:files.append(key)
    if not files:raise HTTPException(404,'İlan klasöründe fotoğraf yok.')
    out=root/f'{p}_ILAN_FOTOGRAFLARI.zip'
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for i,key in enumerate(files,1):
            f=root/key;z.write(f,f'{i:02d}_{p}_{f.name}')
    return FileResponse(out,filename=out.name,media_type='application/zip')

@router.post('/{plate}/open-folder')
def open_folder(plate:str):
    root=root_for(plate)
    try:
        if os.name=='nt':os.startfile(str(root))
        elif sys.platform=='darwin':subprocess.Popen(['open',str(root)])
        else:subprocess.Popen(['xdg-open',str(root)])
        return {'ok':True,'path':str(root)}
    except Exception as e:return {'ok':False,'path':str(root),'error':str(e)}

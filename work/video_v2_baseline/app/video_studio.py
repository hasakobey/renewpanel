from __future__ import annotations

import asyncio, json, re, subprocess, threading, uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from PIL import Image, ImageDraw, ImageFont, ImageOps

from .db import BASE, connect, log

router = APIRouter(prefix="/api/video-studio", tags=["video-studio"])
JOBS: dict[str, dict] = {}
LOCK = threading.Lock()


def clean_plate(value: str) -> str:
    plate = re.sub(r"[^A-Za-z0-9_-]", "", str(value or "").upper())
    if not plate:
        raise HTTPException(400, "Araç seçimi zorunlu.")
    return plate


def paths(plate: str):
    root = BASE / "vehicle_media" / clean_plate(plate)
    video = root / "video"
    video.mkdir(parents=True, exist_ok=True)
    return root, video, video / "project.json"


def load_json(path: Path, fallback=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback if fallback is not None else {}


def slots_for(root: Path):
    meta = load_json(root / "meta.json", {})
    result = {}
    for key, value in (meta.get("slots") or {}).items():
        try:
            slot = int(key); photo = root / str(value)
        except Exception:
            continue
        if 1 <= slot <= 25 and photo.is_file():
            result[slot] = photo
    return result


def vehicle(plate: str):
    with connect() as con:
        row = con.execute("SELECT * FROM vehicles WHERE upper(replace(plate,' ',''))=upper(replace(?,' ','')) ORDER BY id DESC LIMIT 1", (plate,)).fetchone()
        sale = con.execute("SELECT * FROM sales WHERE upper(replace(plate,' ',''))=upper(replace(?,' ','')) ORDER BY id DESC LIMIT 1", (plate,)).fetchone()
        acq = con.execute("SELECT * FROM acquisitions WHERE upper(replace(plate,' ',''))=upper(replace(?,' ','')) ORDER BY id DESC LIMIT 1", (plate,)).fetchone()
    data = dict(row) if row else (dict(acq) if acq else {})
    if sale and not data:
        data = dict(sale)
    return data


def default_text(data: dict, plate: str):
    name = " ".join(str(data.get(k) or "").strip() for k in ("brand", "model", "version")).strip()
    if not name:
        name = str(data.get("vehicle_info") or "Aracımız")
    year = data.get("model_year") or ""
    km = data.get("km")
    km_text = f"{int(km):,}".replace(",", ".") + " kilometrede" if km else ""
    return f"{year} model {name}. {km_text}. Detaylı görünümü, güçlü duruşu ve özenle hazırlanmış fotoğraflarıyla şimdi Çayan Tarsus Renew'de. Bilgi ve randevu için bizimle iletişime geçin.".replace(". .", ".")


def project_state(plate: str):
    p = clean_plate(plate); root, video, project_file = paths(p); photos = slots_for(root); data = vehicle(p)
    project = load_json(project_file, {})
    selected = [int(x) for x in project.get("slots", []) if int(x) in photos][:8]
    if not selected:
        selected = sorted(photos)[:8]
    project.update({
        "plate": p, "slots": selected, "cover_slot": int(project.get("cover_slot") or (selected[0] if selected else 0)),
        "title": project.get("title") or " ".join(str(data.get(k) or "") for k in ("brand", "model")).strip(),
        "subtitle": project.get("subtitle") or " ".join(filter(None, [str(data.get("model_year") or ""), str(data.get("version") or "")])).strip(),
        "narration": project.get("narration") or default_text(data, p), "voice": project.get("voice") or "tr-TR-AhmetNeural",
        "template": "renew-editorial", "approved": bool(project.get("approved")), "updated_at": project.get("updated_at"),
    })
    return project, data, photos, video, project_file


def save_project(path: Path, project: dict):
    project["updated_at"] = datetime.now().isoformat(timespec="seconds")
    path.write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")


@router.get("/{plate}")
def get_project(plate: str):
    project, data, photos, video, _ = project_state(plate)
    project["vehicle"] = {k: data.get(k) for k in ("brand", "model", "version", "model_year", "km", "color", "fuel", "transmission")}
    project["photos"] = [{"slot": n, "url": f"/api/media/{project['plate']}/file/listing/{photo.name}"} for n, photo in sorted(photos.items())]
    project["video_ready"] = (video / f"{project['plate']}_RENEW_VIDEO.mp4").is_file()
    return project


@router.post("/{plate}/project")
def update_project(plate: str, payload: dict):
    project, _, photos, _, project_file = project_state(plate)
    selected = [int(x) for x in payload.get("slots", []) if str(x).isdigit() and int(x) in photos]
    if len(selected) > 8:
        raise HTTPException(400, "En fazla 8 fotoğraf seçebilirsiniz.")
    for key in ("title", "subtitle", "narration", "voice"):
        if key in payload: project[key] = str(payload[key]).strip()
    project["slots"] = selected
    project["cover_slot"] = int(payload.get("cover_slot") or (selected[0] if selected else 0))
    project["approved"] = False
    save_project(project_file, project)
    return {"ok": True, "project": project}


def font(size, bold=False):
    candidates = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    return ImageFont.truetype(candidates[0], size)


def cover_image(source: Path, target: Path, project: dict):
    with Image.open(source) as raw:
        img = ImageOps.fit(raw.convert("RGB"), (1080, 1920), method=Image.Resampling.LANCZOS)
    shade = Image.new("RGBA", img.size, (0, 0, 0, 0)); draw = ImageDraw.Draw(shade)
    draw.rectangle((0, 0, 1080, 520), fill=(5, 20, 42, 165)); draw.rectangle((0, 1450, 1080, 1920), fill=(5, 20, 42, 185))
    img = Image.alpha_composite(img.convert("RGBA"), shade); draw = ImageDraw.Draw(img)
    draw.text((70, 90), "RENEW", font=font(32, True), fill="#78b7ff")
    draw.text((70, 155), project["plate"], font=font(76, True), fill="white")
    draw.text((70, 1485), project.get("title") or "Araç", font=font(58, True), fill="white")
    draw.text((70, 1570), project.get("subtitle") or "", font=font(34), fill="#d8e8f8")
    draw.rounded_rectangle((70, 1690, 500, 1795), 28, fill="#ffffff"); draw.text((105, 1718), "ÇAYAN TARSUS", font=font(30, True), fill="#0a315b")
    img.convert("RGB").save(target, quality=94)


def set_job(job_id, **values):
    with LOCK: JOBS.setdefault(job_id, {}).update(values)


def render_job(job_id: str, plate: str):
    try:
        project, _, photos, video, project_file = project_state(plate)
        chosen = project["slots"]
        if len(chosen) != 8: raise RuntimeError("Video üretmek için tam 8 fotoğraf seçin.")
        work = video / ("work_" + job_id); work.mkdir(parents=True, exist_ok=True)
        cover = work / "cover.jpg"; cover_image(photos[project["cover_slot"]], cover, project)
        sources = [cover] + [photos[n] for n in chosen if n != project["cover_slot"]]
        if len(sources) < 8: sources += [photos[project["cover_slot"]]] * (8-len(sources))
        set_job(job_id, progress=12, message="Seslendirme hazırlanıyor")
        voice = work / "voice.mp3"
        async def tts():
            import edge_tts
            await edge_tts.Communicate(project["narration"], project["voice"], rate="-4%").save(str(voice))
        asyncio.run(tts())
        set_job(job_id, progress=30, message="Fotoğraflar videoya işleniyor")
        clips=[]
        for i,src in enumerate(sources):
            clip=work/f"clip_{i:02d}.mp4"; clips.append(clip)
            vf="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0007,1.08)':d=105:s=1080x1920:fps=30,fade=t=in:st=0:d=0.28,fade=t=out:st=3.22:d=0.28,format=yuv420p"
            subprocess.run(["ffmpeg","-y","-loop","1","-i",str(src),"-t","3.5","-vf",vf,"-an","-c:v","libx264","-preset","veryfast","-crf","22","-pix_fmt","yuv420p",str(clip)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
            set_job(job_id,progress=30+int((i+1)*6),message=f"{i+1}/8 sahne hazırlandı")
        concat=work/"clips.txt"; concat.write_text("".join(f"file '{x.name}'\n" for x in clips),encoding="utf-8")
        silent=work/"silent.mp4"
        subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-c","copy",str(silent)],cwd=work,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        output = video / f"{plate}_RENEW_VIDEO.mp4"; temp = work / "render.mp4"
        subprocess.run(["ffmpeg","-y","-i",str(silent),"-i",str(voice),"-map","0:v","-map","1:a","-c:v","copy","-c:a","aac","-b:a","160k","-shortest","-movflags","+faststart",str(temp)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        temp.replace(output); project["approved"] = False; project["generated_at"] = datetime.now().isoformat(timespec="seconds"); save_project(project_file, project)
        set_job(job_id, state="ready", progress=100, message="Video hazır", video_url=f"/api/video-studio/{plate}/file?v={uuid.uuid4().hex[:8]}")
        log("video", plate, "GENERATE", "8 fotoğraflı video taslağı üretildi")
    except Exception as exc:
        set_job(job_id, state="error", message=str(exc)[-600:])


@router.post("/{plate}/generate")
def generate(plate: str, payload: dict):
    update_project(plate, payload)
    project, _, _, _, _ = project_state(plate)
    if len(project["slots"]) != 8: raise HTTPException(400, "Video üretmek için tam 8 fotoğraf seçin.")
    if project["cover_slot"] not in project["slots"]: raise HTTPException(400, "Kapak fotoğrafı seçilen 8 fotoğraf içinde olmalıdır.")
    job_id = uuid.uuid4().hex
    JOBS[job_id] = {"state":"queued", "progress":3, "message":"Üretim sırasına alındı", "plate":project["plate"]}
    threading.Thread(target=render_job, args=(job_id, project["plate"]), daemon=True).start()
    return {"ok": True, "job_id": job_id}


@router.get("/{plate}/status")
def status(plate: str, job_id: str):
    job = JOBS.get(job_id)
    if not job or job.get("plate") != clean_plate(plate): raise HTTPException(404, "Üretim işi bulunamadı.")
    return job


@router.get("/{plate}/file")
def video_file(plate: str):
    p=clean_plate(plate); _, video, _=paths(p); file=video/f"{p}_RENEW_VIDEO.mp4"
    if not file.is_file(): raise HTTPException(404,"Video henüz hazır değil.")
    return FileResponse(file, media_type="video/mp4", filename=file.name)


@router.post("/{plate}/approve")
def approve(plate: str):
    project, _, _, video, project_file=project_state(plate)
    if not (video/f"{project['plate']}_RENEW_VIDEO.mp4").is_file(): raise HTTPException(404,"Onaylanacak video bulunamadı.")
    project["approved"]=True; project["approved_at"]=datetime.now().isoformat(timespec="seconds"); save_project(project_file,project)
    log("video",project["plate"],"APPROVE","Video taslağı kullanıcı tarafından onaylandı")
    return {"ok":True,"approved":True}

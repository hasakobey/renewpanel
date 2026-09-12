from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import shutil, re, uuid, zipfile

router = APIRouter(prefix="/api/photos", tags=["photos"])
BASE = Path(__file__).resolve().parents[1]
ROOT = BASE / "vehicle_media"
ALLOWED = {".jpg", ".jpeg", ".png", ".webp"}

def safe_plate(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_-]", "", str(value or "").upper())
    if not value:
        raise HTTPException(400, "Plaka zorunlu.")
    return value

def ensure_dirs(plate: str):
    root = ROOT / safe_plate(plate)
    (root / "original").mkdir(parents=True, exist_ok=True)
    (root / "processed").mkdir(parents=True, exist_ok=True)
    return root

@router.get("/download-zip/{plate}/{kind}")
def download_zip(plate: str, kind: str):
    if kind not in ("original", "processed"):
        raise HTTPException(400, "Geçersiz klasör.")
    root = ensure_dirs(plate)
    files = [f for f in (root / kind).iterdir() if f.is_file() and f.suffix.lower() in ALLOWED]
    if not files:
        raise HTTPException(404, "ZIP için fotoğraf bulunamadı.")
    out = root / f"{safe_plate(plate)}_{kind}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, f.name)
    return FileResponse(out, filename=out.name, media_type="application/zip")

@router.post("/upload")
async def upload_photos(plate: str = Form(...), files: list[UploadFile] = File(...)):
    root = ensure_dirs(plate)
    saved = []
    for f in files:
        ext = Path(f.filename or "").suffix.lower()
        if ext not in ALLOWED:
            continue
        stem = re.sub(r"[^A-Za-z0-9_-]", "_", Path(f.filename or "photo").stem)[:40] or "photo"
        name = f"{stem}_{uuid.uuid4().hex[:8]}{ext}"
        with (root / "original" / name).open("wb") as w:
            shutil.copyfileobj(f.file, w)
        saved.append(name)
    return {"ok": True, "plate": safe_plate(plate), "count": len(saved), "saved": saved}

@router.get("/{plate}")
def list_photos(plate: str):
    root = ensure_dirs(plate)
    out = {"plate": safe_plate(plate), "original": [], "processed": []}
    for kind in ("original", "processed"):
        for f in sorted((root / kind).iterdir(), key=lambda p: p.stat().st_mtime):
            if f.is_file() and f.suffix.lower() in ALLOWED:
                out[kind].append({
                    "name": f.name,
                    "size": f.stat().st_size,
                    "url": f"/api/photos/{safe_plate(plate)}/{kind}/{f.name}"
                })
    return out

@router.post("/{plate}/copy-to-processed/{name}")
def copy_to_processed(plate: str, name: str):
    root = ensure_dirs(plate)
    src = root / "original" / Path(name).name
    if not src.exists():
        raise HTTPException(404, "Orijinal fotoğraf bulunamadı.")
    dst = root / "processed" / src.name
    shutil.copy2(src, dst)
    return {"ok": True, "name": dst.name}

@router.get("/{plate}/{kind}/{name}")
def get_photo(plate: str, kind: str, name: str):
    if kind not in ("original", "processed"):
        raise HTTPException(400, "Geçersiz klasör.")
    p = ensure_dirs(plate) / kind / Path(name).name
    if not p.exists():
        raise HTTPException(404, "Fotoğraf bulunamadı.")
    return FileResponse(p)

@router.delete("/{plate}/{kind}/{name}")
def delete_photo(plate: str, kind: str, name: str):
    if kind not in ("original", "processed"):
        raise HTTPException(400, "Geçersiz klasör.")
    p = ensure_dirs(plate) / kind / Path(name).name
    if p.exists():
        p.unlink()
    return {"ok": True}

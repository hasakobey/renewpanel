import hashlib
import os
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parent
HOST = os.environ.get("RENEW_SSH_HOST", "45.195.231.20")
USER = os.environ.get("RENEW_SSH_USER", "root")
PASSWORD = os.environ["RENEW_SSH_PASSWORD"]
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASSWORD, timeout=20)

commands = [
    "ffmpeg -y -loop 1 -i /opt/renewpro/app_live/vehicle_media/10ANK557/video/work_349d804deb294e9a89bd4c818be8a0d2/cover.jpg -t 3.5 -vf \"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0007,1.08)':d=105:s=1080x1920:fps=30,fade=t=in:st=0:d=.28,fade=t=out:st=3.22:d=.28,format=yuv420p\" -an -c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p /tmp/test-video.mp4 2>&1 | tail -40",
]
for cmd in commands:
    _, out, err = c.exec_command(cmd)
    print("$", cmd)
    print(out.read().decode(), err.read().decode())

sftp = c.open_sftp()
live_dir = ROOT / "live_current"
live_dir.mkdir(exist_ok=True)
for rel in ["app/main.py", "app/static/index.html", "app/static/app.js", "app/db.py"]:
    dst = live_dir / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    sftp.get("/opt/renewpro/app_live/" + rel, str(dst))
    local = ROOT / "live_ai" / rel
    print(rel, "live", hashlib.sha256(dst.read_bytes()).hexdigest(), "local", hashlib.sha256(local.read_bytes()).hexdigest())
sftp.close()
c.close()

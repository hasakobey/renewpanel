from datetime import datetime
import sys

sys.path.insert(0, "work")
from video_v2_ops import run, ssh

live = "/opt/renewpro/app_live/app/static/index.html"
source = "/opt/renewpro/backups/dashboard_stitch_20260909_132125/index.html"
safety = "/opt/renewpro/backups/manual_before_rollback_" + datetime.now().strftime("%Y%m%d_%H%M%S")

client = ssh()
try:
    _, stdout, stderr = client.exec_command(f"test -s {source}")
    if stdout.channel.recv_exit_status() != 0:
        raise RuntimeError("Selected backup index is missing or empty: " + stderr.read().decode())
    run(client, f"mkdir -p {safety} && cp -p {live} {safety}/index.html")
    run(client, f"cp -p {source} {live}")
    _, stdout, stderr = client.exec_command(f"cmp -s {source} {live}")
    if stdout.channel.recv_exit_status() != 0:
        raise RuntimeError("Restored file does not match selected backup")
    print(run(client, "curl -fsS -o /dev/null -w 'HTTPS %{http_code}\\n' 'https://renewpanel.xyz/?v=rollback-2'"))
    print("RESTORED", source)
    print("SAFETY", safety)
finally:
    client.close()

import sys

sys.path.insert(0, "work")
from video_v2_ops import run, ssh

client = ssh()
try:
    command = "find /opt/renewpro/backups -mindepth 1 -maxdepth 1 -type d -printf '%T@ %f\\n' | sort -nr | sed -n '1,12p'"
    print(run(client, command))
finally:
    client.close()

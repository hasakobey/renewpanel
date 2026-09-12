import hashlib
from claude_conn import ssh, run
local = open(r'C:\Users\Hasan\Documents\Codex\2026-08-31\referenced-chatgpt-conversation-this-is-an\work\login_clean\renew_login_switch_v1.js','rb').read()
c = ssh()
try:
    sftp = c.open_sftp()
    live = sftp.open('/opt/renewpro/app_live/app/static/renew_login_switch_v1.js','rb').read()
    print('local ==', hashlib.sha256(local).hexdigest())
    print('live  ==', hashlib.sha256(live).hexdigest())
    print('esit mi:', hashlib.sha256(local).digest()==hashlib.sha256(live).digest())
finally:
    c.close()
"""Scoped RENEW PRO frontend release; business/data files are read-only guards."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import shutil
import sys
from video_v2_ops import ssh, run

ROOT = Path(__file__).parent / 'reference_release'
BASE = '/opt/renewpro/app_live/app/'
PROTECTED = ['main.py', 'calc.py', 'form_finance.py']
ASSETS = ['renew_reference_core.css', 'renew_reference_core.js',
          'renew_reference_dashboard.css', 'renew_reference_dashboard.js',
          'renew_reference_forms.css', 'renew_reference_forms.js',
          'renew_reference_modules.css', 'renew_reference_modules.js']

def digest(data):
    return hashlib.sha256(data).hexdigest()

client = ssh()
sftp = client.open_sftp()
try:
    if sys.argv[1] == 'fetch':
        before, stage = ROOT / 'before', ROOT / 'static'
        before.mkdir(parents=True, exist_ok=True)
        stage.mkdir(exist_ok=True)
        sftp.get(BASE + 'static/index.html', str(before / 'index.html'))
        index = (before / 'index.html').read_text(encoding='utf-8')
        names = set(re.findall(r'/static/([\w.-]+\.(?:css|js))', index))
        for name in sorted(names):
            sftp.get(BASE + 'static/' + name, str(before / name))
        for path in before.iterdir():
            if path.is_file():
                shutil.copy2(path, stage / path.name)
        for name in PROTECTED:
            sftp.get(BASE + name, str(before / name))
        print('FETCHED', len(names), 'referenced frontend assets and protected code')
    elif sys.argv[1] == 'deploy':
        stage = ROOT / 'static'
        for name in PROTECTED:
            assert digest(sftp.open(BASE + name, 'rb').read()) == digest((ROOT/'before'/name).read_bytes()), 'Business file changed: ' + name
        assert sftp.open(BASE+'static/index.html','rb').read() == (ROOT/'before/index.html').read_bytes(), 'Live index changed'
        for name in ASSETS + ['index.html']:
            assert (stage/name).is_file() and (stage/name).stat().st_size > 0, 'Missing ' + name
        backup = '/opt/renewpro/backups/reference_release_' + datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        run(client, 'mkdir -p '+backup+' && cp -p '+BASE+'static/index.html '+backup+'/index.html')
        for name in ASSETS:
            try:
                sftp.stat(BASE+'static/'+name)
            except FileNotFoundError:
                continue
            raise RuntimeError('Asset name already exists: '+name)
        try:
            for name in ASSETS + ['index.html']:
                target = BASE+'static/'+name
                sftp.put(str(stage/name), target+'.new')
                sftp.chmod(target+'.new', 0o644)
                sftp.posix_rename(target+'.new', target)
                assert sftp.open(target,'rb').read() == (stage/name).read_bytes(), 'Transfer mismatch: '+name
            run(client, 'nginx -t && curl -fsS -o /dev/null -w "HTTPS %{http_code}\\n" https://renewpanel.xyz/')
            print('BACKUP', backup)
            print('BUSINESS_FILES_UNCHANGED')
        except Exception:
            run(client, 'cp -p '+backup+'/index.html '+BASE+'static/index.html')
            raise
    else:
        raise ValueError('Use fetch or deploy')
finally:
    sftp.close()
    client.close()

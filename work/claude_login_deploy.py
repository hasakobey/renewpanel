"""Login yeniden tasarimini canliya alir: yedek -> canli surum + olu blok teyidi
-> atomik aktarim -> hash dogrulama -> nginx/HTTPS kontrol -> basarisizsa geri donus."""
import hashlib, sys
from datetime import datetime
from pathlib import Path
from claude_conn import ssh, run

ROOT = Path(__file__).resolve().parent
STAGE = ROOT / "login_clean"
STATIC = "/opt/renewpro/app_live/app/static"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP = f"/opt/renewpro/backups/login_redesign_{STAMP}"

EXISTING = ["index.html", "app.js"]
NEWFILES = ["renew_login_switch_v1.css", "renew_login_switch_v1.js"]

DEAD_BLOCK = (
    "$('#loginForm').onsubmit=async e=>{\n"
    " e.preventDefault();const u=$('#loginUsername').value.trim(),p=$('#loginPassword').value;\n"
    " try{\n"
    "  const r=await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});\n"
    "  const j=await r.json();if(!r.ok)throw new Error(j.detail||'Giriş başarısız');\n"
    "  CURRENT_USER=j;$('#loginOverlay').classList.add('hidden');applyPermissions();$('#loginMessage').textContent='';\n"
    "  await refreshAll();if(CURRENT_USER.must_change_password)setTimeout(()=>openPasswordChange(true),200);\n"
    " }catch(err){$('#loginMessage').textContent='❌ '+err.message;}\n"
    "};\n"
)

def sha(data): return hashlib.sha256(data).hexdigest()

def main():
    payload = {n: (STAGE/n).read_bytes() for n in EXISTING + NEWFILES}
    client = ssh()
    try:
        sftp = client.open_sftp()
        print("=== canli teyit ===")
        for name in EXISTING:
            live = sftp.open(f"{STATIC}/{name}", "rb").read()
            expected = (STAGE/"live"/name).read_bytes()
            if sha(live) != sha(expected):
                print(f"DURDURULDU: {name} canlida degismis."); return 1
            print(f"  {name}: OK")
        live_js = sftp.open(f"{STATIC}/app.js", "rb").read().decode("utf-8")
        if DEAD_BLOCK not in live_js:
            print("DURDURULDU: olu blok canlida beklenen sekilde bulunamadi."); return 1
        print("  olu blok canlida teyit edildi")

        print("\n=== yedek ===")
        run(client, f"mkdir -p {BACKUP}")
        run(client, "cp -p " + " ".join(f"{STATIC}/{n}" for n in EXISTING) + f" {BACKUP}/")
        run(client, f"cd {BACKUP} && sha256sum * > SHA256SUMS.txt")
        print(f"YEDEK: {BACKUP}")

        print("\n=== aktarim ===")
        for name in EXISTING + NEWFILES:
            target = f"{STATIC}/{name}"; tmp = target + ".new"
            with sftp.open(tmp, "wb") as fh: fh.write(payload[name])
            sftp.chmod(tmp, 0o644); sftp.posix_rename(tmp, target)
            print(f"  {name} aktarildi")

        print("\n=== hash dogrulama ===")
        ok = True
        _, out, _ = run(client, f"cd {STATIC} && sha256sum " + " ".join(EXISTING+NEWFILES))
        remote = {p.split()[1]: p.split()[0] for p in out.splitlines() if len(p.split())==2}
        for name in EXISTING+NEWFILES:
            m = remote.get(name) == sha(payload[name])
            print(f"  {name}: {'OK' if m else 'UYUSMUYOR'}"); ok = ok and m

        print("\n=== kontroller ===")
        code, out, err = run(client, "nginx -t", check=False)
        print("nginx -t:", "basarili" if code==0 else "HATA:"+err[:150]); ok = ok and code==0
        checks = [
            ("ana panel", "curl -s -o /dev/null -w '%{http_code}' https://renewpanel.xyz/", {"200"}),
            ("yeni css", "curl -s -o /dev/null -w '%{http_code}' https://renewpanel.xyz/static/renew_login_switch_v1.css", {"200"}),
            ("yeni js", "curl -s -o /dev/null -w '%{http_code}' https://renewpanel.xyz/static/renew_login_switch_v1.js", {"200"}),
            ("app.js", "curl -s -o /dev/null -w '%{http_code}' https://renewpanel.xyz/static/app.js", {"200"}),
            ("biziz", "curl -s -o /dev/null -w '%{http_code}' https://renewpanel.xyz/biziz/", {"308"}),
        ]
        for label, cmd, exp in checks:
            _, out, _ = run(client, cmd, check=False)
            st = out.strip(); g = st in exp
            print(f"  {label}: {st} {'' if g else '<-- BEKLENMEDIK'}"); ok = ok and g

        if not ok:
            print("\n!! GERI DONULUYOR")
            run(client, "cp -p " + " ".join(f"{BACKUP}/{n}" for n in EXISTING) + f" {STATIC}/")
            for n in NEWFILES:
                run(client, f"rm -f {STATIC}/{n}", check=False)
            return 1

        print("\n=== TAMAM ===")
        print("YEDEK:", BACKUP)
        return 0
    finally:
        client.close()

if __name__ == "__main__":
    sys.exit(main())

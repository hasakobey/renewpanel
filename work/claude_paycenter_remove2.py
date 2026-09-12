"""payment-center kalintilarinin 2. turu: syncPaymentFrameHeight fonksiyonu +
DOMContentLoaded/resize dinleyicileri + V7.24 page() router yamasi.

DOKUNULMAYANLAR (mail-templates modulunun kendi icinde, ayri bir isle
degerlendirilecek): saveMailTemplates()/saveMailTemplatesV725() icindeki
document.getElementById('paymentCenterFrame') + postMessage cagrilari.
Bunlar 'if(f)' ile korunuyor; frame artik yok oldugu icin sessizce no-op
olurlar, hata vermezler.
"""
import shutil
import subprocess
import sys
from pathlib import Path

STAGE = Path(__file__).resolve().parent / "paycenter_clean"

BLOCK_A = (
    "function syncPaymentFrameHeight(){\n"
    "  const f=document.getElementById('paymentCenterFrame');if(!f)return;\n"
    "  try{const d=f.contentDocument||f.contentWindow?.document;if(!d)return;"
    "const h=Math.max(d.body?.scrollHeight||0,d.documentElement?.scrollHeight||0,680);"
    "f.style.height=Math.min(Math.max(h+8,680),1400)+'px'}catch(e){}\n"
    "}\n"
    "document.addEventListener('DOMContentLoaded',()=>{const f=document.getElementById"
    "('paymentCenterFrame');if(f)f.addEventListener('load',()=>{syncPaymentFrameHeight();"
    "setTimeout(syncPaymentFrameHeight,300);setTimeout(syncPaymentFrameHeight,900)})});\n"
    "window.addEventListener('resize',syncPaymentFrameHeight);\n"
)

BLOCK_B = (
    "/* V7.24 payment center fixed viewport: prevents layout jumps */\n"
    "syncPaymentFrameHeight=function(){};\n"
    "const _pageV724=page;\n"
    "page=function(id){_pageV724(id);if(id==='payment-center'){"
    "const f=document.getElementById('paymentCenterFrame');if(f){"
    "f.style.height='calc(100vh - 215px)';setTimeout(()=>{try{"
    "f.contentWindow?.postMessage({type:'renew-mail-config-updated'},location.origin)"
    "}catch(e){}},150)}}};\n"
)


def node_check(path):
    node = shutil.which("node")
    if not node:
        return "node yok, atlandi"
    r = subprocess.run([node, "--check", str(path)], capture_output=True, text=True)
    return "OK" if r.returncode == 0 else "HATA: " + (r.stderr or "").strip()[-300:]


def main():
    path = STAGE / "app.js"
    js = path.read_text(encoding="utf-8")
    before = len(js)

    for label, block in (("BLOCK_A (syncPaymentFrameHeight + dinleyiciler)", BLOCK_A),
                          ("BLOCK_B (V7.24 page() yamasi)", BLOCK_B)):
        n = js.count(block)
        if n != 1:
            print(f"{label}: TAM ESLESME BULUNAMADI ({n} kez) - islem durduruldu")
            print("--- beklenen ---")
            print(block[:200])
            return 1
        js = js.replace(block, "", 1)
        print(f"{label}: kaldirildi ({len(block)} karakter)")

    path.write_text(js, encoding="utf-8", newline="")
    print(f"\napp.js: {before:,} -> {len(js):,} bayt")

    status = node_check(path)
    print(f"sozdizimi: {status}")
    if status != "OK":
        print("!! sozdizimi hatasi - dosya bozuk kalabilir, elle incele")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

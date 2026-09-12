import time, json, urllib.request, http.cookiejar
base="https://renewpanel.xyz"; jar=http.cookiejar.CookieJar(); opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
def call(path, method="GET", body=None, csrf=None):
    data=json.dumps(body).encode() if body is not None else None; headers={"Content-Type":"application/json"}
    if csrf: headers["x-csrf-token"]=csrf
    with opener.open(urllib.request.Request(base+path,data=data,headers=headers,method=method),timeout=30) as r:return r.status,dict(r.headers),r.read()
status,_,raw=call("/api/auth/login","POST",{"username":"administrator","password":"Renew@2026"}); print("login",status); csrf=json.loads(raw)["csrf_token"]
status,_,raw=call("/api/video-studio/10ANK557"); print("project",status); p=json.loads(raw); print("photos",len(p["photos"]),"selected",p["slots"])
slots=[x["slot"] for x in p["photos"][:8]]
payload={"slots":slots,"cover_slot":slots[0],"title":"Dacia Duster 1.3 Turbo Extreme","subtitle":"2024 • 45.000 km • 4x2 EDC","narration":"2024 model Dacia Duster 1.3 Turbo Extreme 4x2 EDC. 45 bin kilometrede. Hatasız ve boyasız, serinin en dikkat çeken seçeneklerinden biri. Güçlü duruşu, konforlu sürüşü ve geniş yaşam alanıyla şimdi Çayan Tarsus Renew'de. Detaylı bilgi ve randevu için bizimle iletişime geçin.","voice":"tr-TR-AhmetNeural"}
status,_,raw=call("/api/video-studio/10ANK557/generate","POST",payload,csrf); print("generate",status,raw[:200]); job=json.loads(raw)["job_id"]
for _ in range(150):
    _,_,raw=call(f"/api/video-studio/10ANK557/status?job_id={job}"); q=json.loads(raw); print(q)
    if q.get("state") in ("ready","error"): break
    time.sleep(2)
if q.get("state")!="ready": raise SystemExit(2)
status,headers,raw=call("/api/video-studio/10ANK557/file"); print("file",status,headers.get("Content-Type"),len(raw))

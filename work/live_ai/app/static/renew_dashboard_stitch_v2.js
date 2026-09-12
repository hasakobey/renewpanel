/* RENEW_DASHBOARD_STITCH_V2 (JS)
   Kaynak: stitch_renew_pro_ui_redesign/precision_automotive_fleet_intelligence/
   Kapsam: SADECE #dashboard gorunumu. Veri/hesap mantigina dokunulmadi —
   asagidaki fonksiyonlar mevcut kpis()/renderRenewAlerts() cagrilarini
   ZINCIRLER (chain), ayni veriyi tuketip SADECE #dashKpis ve #dashAlerts
   icin ikon + gruplama ekler. Diger sayfalarin KPI'lari (stockKpis,
   salesKpis, expertiseKpis, perfKpis, ...) bu dosyadan ETKILENMEZ —
   kpis() sadece id==='#dashKpis' oldugunda ozel davranir, digerlerinde
   orijinal fonksiyonu aynen cagirir.
   Icerik/veri degismedi: ayni 12 KPI, ayni "Dikkat Gerektirenler" kayitlari,
   sadece ikon + gruplama + kart duzeni eklendi (kullanici talebi: "icerik
   ayni kalabilir, gorselligi degistir").
*/
(function(){
  const SVG = {
    car:'<path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9C2.1 11.1 2 11.5 2 12v4c0 .6.4 1 1 1h2m14 0a2 2 0 11-4 0m4 0a2 2 0 10-4 0m-10 0a2 2 0 11-4 0m4 0a2 2 0 10-4 0"/>',
    cart:'<path d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"/>',
    receipt:'<path d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>',
    tag:'<path d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"/>',
    trend:'<path d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>',
    clock:'<path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>',
    chart:'<path d="M8 13v7M12 6v14M16 10v10M4 20h16"/>',
    badge:'<path d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"/>',
    layers:'<path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>',
    warn:'<path d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>',
    down:'<path d="M17 7l-8.5 8.5M9 8l-.5 7.5M9 8h7.5"/>',
    target:'<path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0zm-4 0a5 5 0 11-10 0 5 5 0 0110 0z"/>',
    check:'<path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>',
    forward:'<path d="M9 5l7 7-7 7"/>'
  };
  function icon(name,cls){return `<svg class="${cls||''}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${SVG[name]||SVG.trend}</svg>`}

  /* ---------- 1) #dashKpis: 2 gruba ayir, ikon ekle (veri/etiket AYNI) ---------- */
  const DASH_ICON_ORDER=['car','cart','receipt','tag','trend','clock','trend','chart','badge','badge','layers','clock'];
  function kpiCard(x,iconName){
    const [label,value,cls,hint]=x;
    return `<div class="kpi ${cls||''}"><div class="kpi-top"><label>${label}</label><span class="kpi-icon">${icon(iconName)}</span></div><strong>${value}</strong><small>${hint||''}</small></div>`;
  }
  function renderDashKpisGrouped(a){
    const box=document.getElementById('dashKpis');if(!box)return;
    const groupA=a.slice(0,6),groupB=a.slice(6,12);
    const stockCount=(groupA[0]&&groupA[0][1])||'';
    let monthLabel='';try{monthLabel=typeof renewMonthLabel==='function'&&typeof month==='function'?renewMonthLabel(month()):''}catch(e){}
    box.innerHTML=`
      <div class="kpi-group">
        <div class="kpi-group-head"><h4>Grup A: Stok ve Sermaye Bağlanma Özeti</h4><span>Aktif ${esc(stockCount)} Portföy</span></div>
        <div class="kpi-grid">${groupA.map((x,i)=>kpiCard(x,DASH_ICON_ORDER[i])).join('')}</div>
      </div>
      <div class="kpi-group">
        <div class="kpi-group-head"><h4>Grup B: Gerçekleşen Satış ve Kârlılık Performansı</h4><span>${esc(monthLabel)} Kapanış Dönemi</span></div>
        <div class="kpi-grid">${groupB.map((x,i)=>kpiCard(x,DASH_ICON_ORDER[i+6])).join('')}</div>
      </div>`;
  }
  const _origKpis=kpis;
  kpis=function(id,a){
    if(id==='#dashKpis'&&Array.isArray(a)&&a.length===12){renderDashKpisGrouped(a);return}
    _origKpis(id,a);
  };

  /* ---------- 2) #dashAlerts: mevcut metni koruyarak ikon + footer ekle ---------- */
  function restyleAlerts(){
    const box=document.getElementById('dashAlerts');if(!box)return;
    box.querySelectorAll('.dash-alert').forEach(el=>{
      const title=el.querySelector('b')?.textContent||'';
      const desc=el.querySelector('small')?.textContent||'';
      const badge=el.querySelector('strong')?.textContent||'';
      const level=el.classList.contains('critical')?'critical':el.classList.contains('warning')?'warning':'success';
      const ic=level==='critical'?'warn':level==='warning'?'target':'check';
      const showBadge=level!=='success'&&badge&&badge!=='0';
      el.innerHTML=`
        <div class="dash-alert-row"><span class="dash-alert-icon">${icon(ic)}</span><span class="dash-alert-title">${esc(title)}</span>${showBadge?`<span class="dash-alert-badge">${esc(badge)}</span>`:''}</div>
        <p class="dash-alert-desc">${esc(desc)}</p>
        ${level==='success'?'':`<div class="dash-alert-foot"><span>Detayı incele</span>${icon('forward','dash-alert-arrow')}</div>`}`;
    });
  }
  if(typeof renderRenewAlerts==='function'){
    const _origAlerts=renderRenewAlerts;
    renderRenewAlerts=function(d){_origAlerts(d);restyleAlerts()};
  }
})();

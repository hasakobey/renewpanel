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

  /* ---------- 3) #monthCompare: buyuk sayi + yuzde rozeti karti ---------- */
  function compareCard(label,value,prevLabel,prevValue,changeFrac,deltaLabel){
    const up=changeFrac>=0;
    return `<div class="pa-compare">
      <div class="pa-compare-top"><span>${esc(label)}</span></div>
      <strong>${value}</strong>
      <small>${esc(prevLabel)}: <b>${prevValue}</b></small>
      <div class="pa-compare-badge ${up?'up':'down'}">${icon(up?'trend':'down')}<span>${up?'+':''}${(changeFrac*100).toFixed(1).replace('.',',')}%</span></div>
      <span class="pa-compare-delta">${esc(deltaLabel)}</span>
    </div>`;
  }
  function renderMonthCompareGrouped(d){
    const box=document.getElementById('monthCompare');if(!box||!d)return;
    const revDelta=money(d.sales_revenue-d.previous_revenue);
    const profDelta=money(d.sales_performance_profit-d.previous_performance_profit);
    const countDelta=(d.sales_count-d.previous_sales_count);
    box.innerHTML=
      compareCard('SATIŞ ADEDİ',d.sales_count+' Adet','Geçen ay',d.previous_sales_count+' Adet',d.sales_count_change,(countDelta>=0?'+':'')+countDelta+' Araç')+
      compareCard('AYLIK TOPLAM CİRO',money(d.sales_revenue),'Geçen ay',money(d.previous_revenue),d.revenue_change,(d.sales_revenue>=d.previous_revenue?'+':'')+revDelta)+
      compareCard('PERFORMANS KÂRI',money(d.sales_performance_profit),'Geçen ay',money(d.previous_performance_profit),d.profit_change,(d.sales_performance_profit>=d.previous_performance_profit?'+':'')+profDelta);
  }

  /* ---------- 4) Risk dagilimi: tek orantili cubuk + 4 kutu ---------- */
  function renderRiskGrouped(d){
    const box=document.getElementById('risk');if(!box||!d)return;
    const r=d.stock_risk||{};
    const tiers=[['0_30','0-30 Gün','normal'],['31_60','31-60 Gün','watch'],['61_90','61-90 Gün','action'],['90_plus','90+ Gün','critical']];
    const total=tiers.reduce((a,[k])=>a+Number(r[k]||0),0)||1;
    box.innerHTML=`
      <div class="pa-risk-bar">${tiers.map(([k])=>`<div class="pa-risk-bar-seg pa-risk-${k}" style="width:${Number(r[k]||0)/total*100}%"></div>`).join('')}</div>
      <div class="pa-risk-scale"><span>0 Gün</span><span>Kritik Eşik: 90 Gün+</span></div>
      <div class="pa-risk-grid">${tiers.map(([k,label,tone])=>`<div class="pa-risk-box pa-risk-${k}"><span class="pa-risk-dot"></span><label>${label}</label><strong>${r[k]||0} Araç</strong><small>%${(Number(r[k]||0)/total*100).toFixed(1)}</small></div>`).join('')}</div>`;
    const sum=document.getElementById('riskSummary');
    if(sum)sum.innerHTML=`<p class="hint">Ortalama stok SKS: <b>${d.stock_avg_sks.toFixed(1)} gün</b> • Kritik: <b>${d.stock_critical_count}</b></p>`;
  }

  /* ---------- 5) Satis Kar/Zarar dagilimi: SALES uzerinden gercek toplamlar ---------- */
  function renderProfitSplitGrouped(d){
    const box=document.getElementById('profitSplit');if(!box||!d)return;
    const rows=(typeof SALES!=='undefined'?SALES:[])||[];
    const profitRows=rows.filter(x=>(x.calc?.performance_profit||0)>=0);
    const lossRows=rows.filter(x=>(x.calc?.performance_profit||0)<0);
    const profitSum=profitRows.reduce((a,x)=>a+(x.calc?.performance_profit||0),0);
    const lossSum=lossRows.reduce((a,x)=>a+(x.calc?.performance_profit||0),0);
    const total=rows.length||1;
    const profitPct=profitRows.length/total*100, lossPct=lossRows.length/total*100;
    box.innerHTML=`
      <div class="pa-split-grid">
        <div class="pa-split-card good">
          <div class="pa-split-top"><span>Kârlı &amp; Başabaş Satış</span><em>%${profitPct.toFixed(1)} Başarı</em></div>
          <strong>${profitRows.length} Adet</strong>
          <small>Üretilen kâr hacmi:</small><b class="pa-split-amount">${money(profitSum)}</b>
          <div class="pa-split-bar"><div style="width:${profitPct}%"></div></div>
        </div>
        <div class="pa-split-card bad">
          <div class="pa-split-top"><span>Zararlı Satış</span><em>%${lossPct.toFixed(1)} Risk</em></div>
          <strong>${lossRows.length} Adet</strong>
          <small>Gerçekleşen zarar hacmi:</small><b class="pa-split-amount">${money(lossSum)}</b>
          <div class="pa-split-bar"><div style="width:${lossPct}%"></div></div>
        </div>
      </div>`;
  }

  /* ---------- 6) En Kârlı / Zarar Eden Satışlar: mini liste karti (ayni veri, tablo yerine kart) ---------- */
  function saleMiniRow(x,tone){
    return `<div class="pa-mini-row ${tone}">
      <span class="pa-mini-plate">${esc(x.plate)}</span>
      <div class="pa-mini-info"><b>${esc(x.vehicle_info||'')}</b><small>${esc(x.consultant||'')} • SKS: ${x.sks} Gün</small></div>
      <div class="pa-mini-amount"><b>${tone==='good'?'+':''}${money(x.profit)}</b></div>
    </div>`;
  }
  function renderTopLossSalesGrouped(d){
    const topBox=document.getElementById('topSales'),lossBox=document.getElementById('lossSales');
    if(topBox&&d.top_sales)topBox.innerHTML=(d.top_sales||[]).map(x=>saleMiniRow(x,'good')).join('')||'<div class="empty">Kayıt yok</div>';
    if(lossBox&&d.loss_sales)lossBox.innerHTML=(d.loss_sales||[]).map(x=>saleMiniRow(x,'bad')).join('')||'<div class="empty">Kayıt yok</div>';
  }

  /* ---------- 7) Kritik SKS Stoklari: SKS hucresine renkli rozet ekle (tablo yapisi AYNI) ---------- */
  function badgeForSks(days){
    const c=days<=30?'sks-ok':days<=60?'sks-watch':days<=90?'sks-action':'sks-critical';
    return `<span class="sksbadge ${c}">${days} Gün</span>`;
  }
  function restyleCriticalStock(){
    const box=document.getElementById('criticalStock');if(!box)return;
    box.querySelectorAll('table tbody tr').forEach(tr=>{
      const cell=tr.children[2];if(!cell)return;
      const n=parseInt(cell.textContent,10);if(Number.isFinite(n))cell.innerHTML=badgeForSks(n);
    });
  }

  /* ---------- 8) Bu Ay Alinan Araclar: en son 3 gercek kayit, mini kart (kategori uydurulmadi) ---------- */
  function renderDashAcquisitionsGrouped(){
    const box=document.getElementById('dashAcquisitions');if(!box)return;
    const rows=(typeof ACQUISITIONS!=='undefined'?ACQUISITIONS:[])||[];
    const recent=[...rows].sort((a,b)=>String(b.purchase_date||'').localeCompare(String(a.purchase_date||''))).slice(0,3);
    if(!recent.length){box.innerHTML='<div class="empty">Bu ay alım yok</div>';return}
    box.innerHTML=`<div class="pa-acq-grid">${recent.map(x=>`
      <div class="pa-acq-card">
        <label>${esc(x.purchase_type||'ALIM')}</label>
        <strong>${esc(x.plate)}</strong>
        <small>${esc(x.model_year||'')} ${esc(x.brand||'')} ${esc(x.model||'')}</small>
        <div class="pa-acq-foot"><span>Alış:</span><b>${money(x.purchase_price)}</b></div>
      </div>`).join('')}</div>`;
  }

  /* ---------- 9b) Stok Marka Dagilimi: satir+cubuk yerine 2 katmanli (isim/yuzde ustte, tam-genislik cubuk altta) ----------
     Veri AYNI (d.brand_distribution: name+count), sadece duzen degisti.
     Renkler sadece daha once tanimli --pa-* tokenlarindan (yeni renk yok). */
  const BRAND_COLORS=['var(--pa-primary)','var(--pa-cyan)','var(--pa-purple)','var(--pa-warning)','var(--pa-text-muted)'];
  function renderBrandDistGrouped(d){
    const box=document.getElementById('brandDist');if(!box||!d||!d.brand_distribution)return;
    const rows=d.brand_distribution||[];
    const total=rows.reduce((a,x)=>a+Number(x.count||0),0)||1;
    box.innerHTML=`<div class="pa-brand-list">${rows.map((x,i)=>{
      const pctVal=Number(x.count||0)/total*100;
      return `<div class="pa-brand-row">
        <div class="pa-brand-top"><span>${esc(x.name)}</span><b>${x.count} Araç • <em>%${pctVal.toFixed(1)}</em></b></div>
        <div class="pa-brand-track"><div class="pa-brand-fill" style="width:${pctVal}%;background:${BRAND_COLORS[i%BRAND_COLORS.length]}"></div></div>
      </div>`;
    }).join('')||'<div class="empty">Veri yok</div>'}</div>`;
  }

  /* ---------- 9) Ekspertiz Ozeti: gercek 3 metrik, renkli nokta satiri (kategori uydurulmadi) ---------- */
  function renderExpertiseSummaryGrouped(d){
    const box=document.getElementById('expertiseSummary');if(!box||!d)return;
    box.innerHTML=`<div class="pa-dot-list">
      <div class="pa-dot-row"><span class="pa-dot blue"></span><b>Yapılan Ekspertiz</b><strong>${d.expertise_done} Adet</strong></div>
      <div class="pa-dot-row"><span class="pa-dot green"></span><b>Alıma Dönüşen</b><strong>${d.expertise_converted} Adet</strong></div>
      <div class="pa-dot-row"><span class="pa-dot purple"></span><b>Dönüşüm Oranı</b><strong>${pct(d.expertise_rate)}</strong></div>
    </div>`;
  }

  const _prevRenderDashboard=renderDashboard;
  renderDashboard=function(d){
    _prevRenderDashboard(d);
    renderMonthCompareGrouped(d);
    renderRiskGrouped(d);
    renderProfitSplitGrouped(d);
    renderTopLossSalesGrouped(d);
    restyleCriticalStock();
    renderBrandDistGrouped(d);
    renderExpertiseSummaryGrouped(d);
  };

  /* #dashAcquisitions ayrica refreshAll() icinde renderDashAcquisitions()
     olarak renderDashboard'DAN SONRA da cagriliyor (renderAcquisitions()
     zincirinden) - o yuzden renderDashboard'a degil, dogrudan bu
     fonksiyona zincirlenir, yoksa kartimiz orijinal tablo ile ezilir. */
  if(typeof renderDashAcquisitions==='function'){
    const _prevDashAcq=renderDashAcquisitions;
    renderDashAcquisitions=function(){_prevDashAcq();renderDashAcquisitionsGrouped()};
  }
})();

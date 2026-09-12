(function(){
'use strict';

function norm(s){
  return (s||'').replace(/\s+/g,' ').trim().toLocaleUpperCase('tr-TR');
}

function numTR(v){
  if(v===null||v===undefined) return NaN;
  let s=String(v).replace(/\s/g,'').replace(/₺/g,'').replace(/TL/gi,'').replace(/%/g,'');
  if(s.includes('.')&&s.includes(',')) s=s.replace(/\./g,'').replace(',','.');
  else if(s.includes(',')) s=s.replace(',','.');
  else if((s.match(/\./g)||[]).length>1) s=s.replace(/\./g,'');
  s=s.replace(/[^0-9.\-]/g,'');
  return parseFloat(s);
}

function findHeader(headers,names){
  return headers.findIndex(h=>{
    const t=norm(h.textContent);
    return names.some(n=>t.includes(n));
  });
}

function decorateKpis(){
  const box=document.getElementById('dashKpis');
  if(!box) return;

  const cards=[...box.children];
  const map=[
    {keys:['GÜNCEL STOK'], cls:'rp-kpi-blue', icon:'🚗'},
    {keys:['STOK ALIŞ'], cls:'rp-kpi-green', icon:'🛒'},
    {keys:['STOK MALİYET'], cls:'rp-kpi-purple', icon:'🏷️'},
    {keys:['STOK SATIŞ'], cls:'rp-kpi-orange', icon:'🛍️'},
    {keys:['TAHMİNİ STOK KÂRI','TAHMINI STOK KARI'], cls:'rp-kpi-green', icon:'📈'},
    {keys:['SKS FİNANSMAN'], cls:'rp-kpi-red', icon:'💳'},
    {keys:['AYLIK SATIŞ'], cls:'rp-kpi-yellow', icon:'📊'},
    {keys:['AYLIK CİRO'], cls:'rp-kpi-blue', icon:'📶'},
    {keys:['NET KÂR','NET KAR'], cls:'rp-kpi-green', icon:'💰'},
    {keys:['PERFORMANS KÂRI','PERFORMANS KARI'], cls:'rp-kpi-purple', icon:'🎯'},
    {keys:['ORT. SATIŞ KÂRI','ORT. SATIS KARI'], cls:'rp-kpi-orange', icon:'%'},
    {keys:['ORT. SATIŞ SKS','ORT. SATIS SKS'], cls:'rp-kpi-blue', icon:'🕒'}
  ];

  cards.forEach(card=>{
    card.classList.remove('rp-kpi-blue','rp-kpi-green','rp-kpi-purple','rp-kpi-orange','rp-kpi-yellow','rp-kpi-red');
    const text=norm(card.textContent);
    const found=map.find(m=>m.keys.some(k=>text.includes(k)));
    if(found){
      card.classList.add(found.cls);
      let icon=card.querySelector('.rp-kpi-icon');
      if(!icon){
        icon=document.createElement('div');
        icon.className='rp-kpi-icon';
        card.appendChild(icon);
      }
      icon.textContent=found.icon;
    }
  });
}

function decorateCriticalStock(){
  const box=document.getElementById('criticalStock');
  if(!box) return;

  const table=box.querySelector('table');
  if(!table) return;

  const headers=[...table.querySelectorAll('thead th')];
  if(!headers.length) return;

  const sksIndex=findHeader(headers,['SKS']);
  const profitIndex=findHeader(headers,['TAHMİNİ KÂR','TAHMINI KAR','KÂR','KAR']);
  if(sksIndex<0) return;

  table.querySelectorAll('tbody tr').forEach(row=>{
    const cells=[...row.querySelectorAll('td')];
    const sksCell=cells[sksIndex];
    if(!sksCell) return;

    if(!sksCell.dataset.rpRaw) sksCell.dataset.rpRaw=sksCell.textContent.trim();
    const day=numTR(sksCell.dataset.rpRaw);
    if(isNaN(day)) return;

    row.classList.remove('rp-critical-row','rp-high-row');
    if(day>=91) row.classList.add('rp-critical-row');
    else if(day>=61) row.classList.add('rp-high-row');

    let cls='rp-sks-normal';
    if(day>=91) cls='rp-sks-critical';
    else if(day>=61) cls='rp-sks-high';
    else if(day>=31) cls='rp-sks-follow';

    sksCell.innerHTML='<span class="rp-sks-pill '+cls+'">'+Math.round(day)+'</span>';

    if(profitIndex>=0 && cells[profitIndex]){
      const pc=cells[profitIndex];
      if(!pc.dataset.rpRaw) pc.dataset.rpRaw=pc.textContent.trim();
      const p=numTR(pc.dataset.rpRaw);
      pc.classList.remove('rp-profit-good','rp-profit-bad');
      if(!isNaN(p)) pc.classList.add(p>=0?'rp-profit-good':'rp-profit-bad');
      pc.textContent=pc.dataset.rpRaw;
    }
  });
}

function extractRiskCounts(){
  const risk=document.getElementById('risk');
  if(!risk) return null;
  const items=[...risk.children];
  if(items.length<4) return null;

  return items.slice(0,4).map(el=>{
    const matches=(el.textContent.match(/\d+/g)||[]);
    if(!matches.length) return 0;
    return parseInt(matches[matches.length-1],10)||0;
  });
}

function decorateRiskBar(){
  const counts=extractRiskCounts();
  const summary=document.getElementById('riskSummary');
  if(!counts||!summary) return;

  const total=counts.reduce((a,b)=>a+b,0)||1;
  let bar=document.getElementById('rpRiskBar');
  if(!bar){
    bar=document.createElement('div');
    bar.id='rpRiskBar';
    summary.parentNode.insertBefore(bar,summary);
  }

  bar.innerHTML=counts.map(v=>'<span style="width:'+(v/total*100)+'%"></span>').join('');
  updateSidebarBadges(counts);
}

function decorateProfitBar(){
  const split=document.getElementById('profitSplit');
  if(!split) return;

  const children=[...split.children];
  if(children.length<2) return;

  const getCount=el=>{
    const m=(el.textContent.match(/\d+/g)||[]);
    return m.length?parseInt(m[m.length-1],10)||0:0;
  };

  const good=getCount(children[0]);
  const bad=getCount(children[1]);
  const total=(good+bad)||1;

  let bar=document.getElementById('rpProfitBar');
  if(!bar){
    bar=document.createElement('div');
    bar.id='rpProfitBar';
    split.parentNode.appendChild(bar);
  }

  bar.innerHTML=
    '<span class="good" style="width:'+(good/total*100)+'%"></span>'+
    '<span class="bad" style="width:'+(bad/total*100)+'%"></span>';
}

function updateSidebarBadges(counts){
  const navs=[...document.querySelectorAll('.app>aside button.nav')];
  const stock=navs.find(n=>norm(n.textContent).includes('GÜNCEL STOK'));
  if(!stock) return;

  stock.querySelectorAll('.rp-side-badge').forEach(x=>x.remove());

  const critical=counts[3]||0;
  const near=(counts[2]||0)+(counts[1]||0);

  if(critical>0){
    const b=document.createElement('span');
    b.className='rp-side-badge red';
    b.textContent=critical;
    b.title='90+ gün kritik stok';
    stock.appendChild(b);
  }else if(near>0){
    const b=document.createElement('span');
    b.className='rp-side-badge orange';
    b.textContent=near;
    b.title='31+ gün takip gerektiren stok';
    stock.appendChild(b);
  }
}

function buildActionCenter(){
  const dashboard=document.getElementById('dashboard');
  const source=document.getElementById('criticalStock');
  if(!dashboard||!source) return;

  const table=source.querySelector('table');
  if(!table) return;

  const headers=[...table.querySelectorAll('thead th')];
  if(!headers.length) return;

  const plateIndex=findHeader(headers,['PLAKA']);
  const vehicleIndex=findHeader(headers,['ARAÇ','ARAC']);
  const sksIndex=findHeader(headers,['SKS']);
  const profitIndex=findHeader(headers,['TAHMİNİ KÂR','TAHMINI KAR','KÂR','KAR']);
  if(sksIndex<0) return;

  const rows=[];
  table.querySelectorAll('tbody tr').forEach(row=>{
    const cells=[...row.querySelectorAll('td')];
    if(!cells.length) return;

    const day=numTR(cells[sksIndex].dataset.rpRaw||cells[sksIndex].textContent);
    if(isNaN(day)||day<61) return;

    rows.push({
      plate:plateIndex>=0?(cells[plateIndex]?.textContent.trim()||'Araç'):'Araç',
      vehicle:vehicleIndex>=0?(cells[vehicleIndex]?.textContent.trim()||''):'',
      day,
      profit:profitIndex>=0?(cells[profitIndex]?.dataset.rpRaw||cells[profitIndex]?.textContent.trim()||''):''
    });
  });

  rows.sort((a,b)=>b.day-a.day);

  let box=document.getElementById('rpActionCenter');
  if(!box){
    box=document.createElement('div');
    box.id='rpActionCenter';
    box.className='card';
    const criticalCard=source.closest('.card');
    if(criticalCard&&criticalCard.parentNode){
      criticalCard.parentNode.insertBefore(box,criticalCard.nextSibling);
    }else{
      dashboard.appendChild(box);
    }
  }

  const esc=s=>String(s||'')
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;')
    .replace(/'/g,'&#039;');

  const list=rows.slice(0,6).map(x=>{
    const critical=x.day>=91;
    return '<div class="rp-action-row '+(critical?'critical':'high')+'">'+
      '<div class="rp-action-icon">'+(critical?'🚨':'⚠️')+'</div>'+
      '<div class="rp-action-main">'+
        '<b>'+esc(x.plate)+(x.vehicle?' • '+esc(x.vehicle):'')+'</b>'+
        '<small>'+(critical?'Kritik stok süresi. Satış/fiyat aksiyonu değerlendir.':'Kritik sınıra yaklaşıyor. Stok aksiyonunu takip et.')+
        (x.profit?' • Tahmini Kâr: '+esc(x.profit):'')+'</small>'+
      '</div>'+
      '<div class="rp-action-day">'+Math.round(x.day)+' Gün</div>'+
    '</div>';
  }).join('');

  box.innerHTML=
    '<div class="cardhead">'+
      '<div><h3>🚦 Aksiyon Gereken Araçlar</h3><p class="hint">61 gün üzerindeki stokların yönetici özeti.</p></div>'+
      '<button class="btn small" onclick="page(\'stocks\')">Tüm Stoğu Aç</button>'+
    '</div>'+
    (list||'<div style="padding:14px;color:#738397;font-size:10px">61+ gün aksiyon gerektiren araç yok.</div>');
}

function enhance(){
  try{
    decorateKpis();
    decorateCriticalStock();
    decorateRiskBar();
    decorateProfitBar();
    buildActionCenter();
  }catch(e){
    console.warn('RENEW Dashboard V3',e);
  }
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded',enhance);
}else{
  enhance();
}

document.addEventListener('DOMContentLoaded',()=>{
  const dash=document.getElementById('dashboard');
  if(!dash) return;

  let timer=null;
  const obs=new MutationObserver(()=>{
    clearTimeout(timer);
    timer=setTimeout(enhance,180);
  });

  if(dash&&dash.nodeType===1){
    try{obs.observe(dash,{childList:true,subtree:true})}catch(e){console.warn('Dashboard observer devre dışı:',e.message)}
  }
});

setInterval(enhance,4000);
})();

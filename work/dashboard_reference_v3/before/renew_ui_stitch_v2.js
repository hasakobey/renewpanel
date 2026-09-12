/* RENEW shared presentation. No API writes or financial calculations. */
(()=>{'use strict';
const paths={car:'M3 14l2-6h14l2 6v5h-3v-2H6v2H3zM7 13h10M8 8l1-3h6l1 3',money:'M3 6h18v12H3zM14 12a2 2 0 1 1-4 0 2 2 0 0 1 4 0M6 9h.01M18 15h.01',chart:'M4 4v16h17M7 15l5-5 4 3 5-8',clock:'M12 8v5l3 2M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0',target:'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0M17 12a5 5 0 1 1-10 0 5 5 0 0 1 10 0M12 12h.01',calc:'M6 3h12v18H6zM9 7h6M9 11h1m4 0h1m-6 4h1m4 0h1',tag:'M3 3h8l10 10-8 8L3 11zM7 7h.01',plus:'M12 4v16M4 12h16',check:'M5 12l4 4L19 6',file:'M5 3h10l4 4v14H5zM14 3v5h5M8 12h8M8 16h6',camera:'M3 7h4l2-3h6l2 3h4v13H3zM16 13a4 4 0 1 1-8 0 4 4 0 0 1 8 0',down:'M12 3v12m-5-5 5 5 5-5M4 17v4h16v-4',edit:'M14 4l6 6M4 20l5-1L21 7l-6-6L3 13z',trash:'M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7',search:'M20 20l-5-5M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0',refresh:'M20 7a9 9 0 1 0 1 8M20 3v5h-5',video:'M3 5h13v14H3zM16 10l5-3v10l-5-3',shield:'M12 3l8 3v6c0 5-8 9-8 9s-8-4-8-9V6zM8 12l3 3 5-6'};
const svg=k=>`<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="${paths[k]||paths.chart}"/></svg>`;
const keyFor=s=>{s=s.toLocaleLowerCase('tr-TR');return s.includes('sil')?'trash':s.includes('düzenle')?'edit':s.includes('foto')?'camera':s.includes('indir')?'down':s.includes('yenile')?'refresh':s.includes('rapor')||s.includes('excel')?'file':s.includes('kaydet')?'check':s.includes('sks')?'clock':s.includes('hedef')||s.includes('performans')?'target':s.includes('maliyet')||s.includes('masraf')?'calc':s.includes('ciro')||s.includes('gelir')?'money':s.includes('kâr')?'chart':s.includes('stok')||s.includes('alınan')?'car':'tag'};
function addIcon(el,key){if(el.querySelector(':scope > .ui-icon'))return;const span=document.createElement('span');span.className='ui-icon';span.innerHTML=svg(key);el.prepend(span)}
const seen=new Map();let lastTrend=null,trendKey='revenue';
function trendData(){return typeof RENEW_DASH_DATA!=='undefined'?RENEW_DASH_DATA:null}
function chart(force=false){const host=document.getElementById('uiTrend');if(!host)return;const d=trendData(),rows=d?.monthly_trend||[],fingerprint=JSON.stringify(rows)+trendKey;if(!force&&lastTrend===fingerprint)return;lastTrend=fingerprint;
 const values=rows.map(r=>Number(r[trendKey])||0),max=Math.max(1,...values.map(Math.abs));
 const body=host.querySelector('.ui-trend-bars');body.replaceChildren();
 if(!rows.length){const empty=document.createElement('p');empty.className='ui-empty';empty.textContent='Bu görünüm için dönemsel satış verisi bulunmuyor.';body.append(empty);return}
 rows.forEach((r,i)=>{const cell=document.createElement('div');cell.className='ui-trend-column';const bar=document.createElement('button');bar.type='button';bar.className='ui-trend-bar';bar.style.setProperty('--bar-height',Math.max(0,Math.abs(values[i])/max*100)+'%');bar.classList.toggle('negative',values[i]<0);const value=trendKey==='sales_count'?values[i]+' araç':money(values[i]);bar.setAttribute('aria-label',`${r.month}: ${value}`);bar.title=`${r.month}: ${value}`;const date=document.createElement('small');date.textContent=String(r.month).slice(5);bar.addEventListener('focus',()=>{host.querySelector('.ui-chart-value').textContent=`${r.month} • ${value}`});bar.addEventListener('mouseenter',()=>{host.querySelector('.ui-chart-value').textContent=`${r.month} • ${value}`});cell.append(bar,date);body.append(cell)});
 host.querySelector('.ui-chart-value').textContent='Sütuna dokunarak dönem tutarını görün';
}
function decorate(){
 document.querySelectorAll('.page.active .rt-kpi,.page.active .kpis>.kpi').forEach((card,i)=>{if(!card.closest('#dashKpis')){let icon=card.querySelector('.rt-kpi-icon,.gw-kpi-icon');if(icon&&!icon.dataset.uiIcon){icon.innerHTML=svg(keyFor(card.querySelector('label')?.textContent||''));icon.dataset.uiIcon='1'}}
  const value=card.querySelector(':scope > strong'),label=card.querySelector('label')?.textContent;if(value&&!value.dataset.uiSeen){value.dataset.uiSeen='1';const key=(card.closest('.page')?.id||'')+label,old=seen.get(key);if(old&&old!==value.textContent&&!matchMedia('(prefers-reduced-motion: reduce)').matches)value.animate([{opacity:.35,transform:'translateY(4px)'},{opacity:1,transform:'none'}],{duration:320,easing:'ease-out'});seen.set(key,value.textContent)}
 });
 document.querySelectorAll('.page.active .rt-inline-actions button').forEach(b=>{if(!b.dataset.uiIcon){b.innerHTML=svg(keyFor(b.getAttribute('aria-label')||b.title||''));b.dataset.uiIcon='1'}});
 document.querySelectorAll('#photoStudio .photo-slot.empty>b').forEach(b=>{if(!b.dataset.uiIcon){b.innerHTML=svg('camera');b.dataset.uiIcon='1'}});
 document.querySelectorAll('.page.active .hero .btn,.page.active .cardhead>.btn').forEach(b=>addIcon(b,keyFor(b.textContent)));
 document.querySelectorAll('#renewMobileNav button').forEach((b,i)=>{if(b.dataset.uiIcon)return;[...b.childNodes].filter(n=>n.nodeType===3).forEach(n=>n.textContent='');addIcon(b,['chart','search','car','car','shield'][i]);b.dataset.uiIcon='1'});
 chart();
}
function boot(){document.documentElement.classList.add('renew-stitch-ui');const dashboard=document.getElementById('dashboard');if(dashboard){
 const grid=dashboard.querySelector('.ds-main-grid'),quick=grid?.querySelector('[data-ds-panel=quick]'),pulse=grid?.querySelector('[data-ds-panel=salesTrendChart]');if(quick&&pulse)pulse.after(quick);
 if(pulse){const el=document.createElement('section');el.id='uiTrend';el.setAttribute('aria-label','Dönemsel satış hareketi');el.innerHTML='<div class="ui-trend-head"><h4>Satış Hareketi</h4><div role="group" aria-label="Grafik metriği"><button type="button" data-trend="revenue" aria-pressed="true">Ciro</button><button type="button" data-trend="sales_count" aria-pressed="false">Adet</button><button type="button" data-trend="profit" aria-pressed="false">Kâr</button></div></div><div class="ui-trend-bars"></div><p class="ui-chart-value" aria-live="polite"></p>';pulse.append(el);el.addEventListener('click',e=>{const b=e.target.closest('[data-trend]');if(!b)return;trendKey=b.dataset.trend;el.querySelectorAll('[data-trend]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));chart(true)})}
 }
 decorate();let pending=false;new MutationObserver(()=>{if(pending)return;pending=true;requestAnimationFrame(()=>{pending=false;decorate()})}).observe(document.querySelector('.app'),{childList:true,subtree:true});
 document.getElementById('globalMonth')?.addEventListener('change',()=>requestAnimationFrame(decorate));
 const previousPage=window.page;if(typeof previousPage==='function')window.page=function(...args){const result=previousPage.apply(this,args);requestAnimationFrame(decorate);return result};
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();

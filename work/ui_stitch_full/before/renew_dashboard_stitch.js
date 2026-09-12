/* Presentation only: retains the application's renderers, records and actions. */
(()=>{'use strict';
const paths={car:'M3 14l2-6h14l2 6v5h-3v-2H6v2H3zM7 13h10M8 8l1-3h6l1 3',cart:'M3 4h2l3 12h11l2-8H6M9 20h.01M18 20h.01',calc:'M6 3h12v18H6zM9 7h6M9 11h1m4 0h1m-6 4h1m4 0h1',tag:'M3 3h8l10 10-8 8L3 11zM7 7h.01',chart:'M4 4v16h17M7 15l5-5 4 3 5-8',clock:'M12 8v5l3 2M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0',check:'M5 12l4 4L19 6',money:'M3 6h18v12H3zM14 12a2 2 0 1 1-4 0 2 2 0 0 1 4 0M6 9h.01M18 15h.01',target:'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0M17 12a5 5 0 1 1-10 0 5 5 0 0 1 10 0M12 12h.01',bars:'M5 20V10h3v10m3 0V4h3v16m3 0v-7h3v7',warning:'M12 3L2 21h20zM12 9v5m0 3v1',users:'M8 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8M2 21v-3a6 6 0 0 1 12 0v3M16 4a4 4 0 0 1 0 8m1 2a5 5 0 0 1 5 5',file:'M5 3h10l4 4v14H5zM14 3v5h5M8 12h8M8 16h6',plus:'M12 4v16M4 12h16'};
const icon=k=>`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${'<path d="'+(paths[k]||paths.chart)+'"/>'}</svg>`;
function badge(el,key){if(!el||el.querySelector(':scope > .ds-icon'))return;const i=document.createElement('span');i.className='ds-icon';i.innerHTML=icon(key);el.prepend(i)}
let root;
function decorate(){
 const cards=root.querySelectorAll('#dashKpis > .kpi');cards.forEach((card,i)=>{badge(card,['car','cart','calc','tag','chart','clock','check','money','money','target','bars','clock'][i]);card.style.setProperty('--ds-delay',`${i%6*25}ms`)});
 root.querySelectorAll('table').forEach(table=>{const heads=[...table.querySelectorAll('thead th')].map(x=>x.textContent);table.querySelectorAll('tbody tr').forEach(row=>[...row.cells].forEach((cell,i)=>{if(cell.colSpan===1)cell.dataset.dsLabel=heads[i]||''}))});
 root.querySelectorAll('.dash-alert').forEach(x=>badge(x,x.classList.contains('critical')?'warning':x.classList.contains('success')?'check':'clock'));
 const split=root.querySelector('#profitSplit'),good=Number(split?.querySelector('.g b')?.textContent||0),bad=Number(split?.querySelector('.r b')?.textContent||0);if(split){let bar=split.querySelector('.ds-profit-bar');if(!bar){bar=document.createElement('div');bar.className='ds-profit-bar';bar.innerHTML='<i></i><i></i>';split.append(bar)}bar.children[0].style.width=(good+bad?good/(good+bad)*100:0)+'%';bar.children[1].style.width=(good+bad?bad/(good+bad)*100:0)+'%';bar.title=`Kârlı / başabaş: ${good} • Zararlı: ${bad}`;}
 const picker=document.getElementById('globalMonth');const tag=root.querySelector('.ds-period');if(tag&&picker&&tag.textContent!==picker.value)tag.textContent=picker.value;
}
function boot(){root=document.getElementById('dashboard');if(!root)return;root.classList.add('ds');
 const hero=root.querySelector('.hero');if(hero){hero.querySelector('h2').textContent='Genel Dashboard';hero.querySelector('p').textContent='Seçili dönemin stok, satış ve kârlılık özeti.';const label=document.createElement('span');label.className='ds-period';hero.querySelector('h2').append(label);}
 const kpis=root.querySelector('#dashKpis');if(kpis){kpis.dataset.stockLabel='Stok ve Sermaye Özeti';kpis.dataset.salesLabel='Satış ve Kârlılık';}
 const grid=document.createElement('div');grid.className='ds-main-grid';root.append(grid);
 const ids=['salesTrendChart','risk','profitSplit','dashConsultants','brandDist','topSales','lossSales','criticalStock','dashAcquisitions','expertiseSummary','recentActivity'];
 ids.forEach((id,i)=>{const node=document.getElementById(id),card=node?.closest('.card');if(!card)return;card.classList.add('ds-panel');card.dataset.dsPanel=id;badge(card.querySelector('h3'),['chart','clock','chart','users','bars','chart','warning','car','cart','check','clock'][i]);grid.append(card)});
 // Preserve every quick action; only move the existing card out of the old wrapper.
 const quick=root.querySelector('.quick-card');if(quick){quick.classList.add('ds-panel');quick.dataset.dsPanel='quick';grid.append(quick);quick.querySelectorAll('button').forEach((x,i)=>badge(x,['plus','money','cart','file','file','check'][i]))}
 root.querySelectorAll(':scope > .grid2,:scope > .grid3,:scope > .dash-command-grid').forEach(x=>{if(!x.children.length)x.remove()});
 let scheduled=false;new MutationObserver(()=>{if(scheduled)return;scheduled=true;requestAnimationFrame(()=>{scheduled=false;decorate()})}).observe(root,{childList:true,subtree:true});decorate();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();

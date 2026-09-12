(()=>{'use strict';
const icons={dashAcquisitions:'🚘',brandDist:'▥',dashConsultants:'◎',topSales:'▲',lossSales:'!',expertiseSummary:'⌕'};
function decorate(){for(const [id,icon] of Object.entries(icons)){const el=document.getElementById(id),card=el?.closest('.card'),h=card?.querySelector(':scope>h3');if(h)h.dataset.dpIcon=icon}
 const rows=[...document.querySelectorAll('#dashConsultants tbody tr')],values=rows.map(r=>Number((r.children[1]?.textContent||'').replace(/[^0-9.-]/g,''))||0),max=Math.max(...values,1);rows.forEach((r,i)=>{const c=r.children[1];if(c){c.classList.add('dp-sales-cell');c.style.setProperty('--dp-ratio',String(values[i]/max*100))}});
}
let busy=false;function schedule(){if(busy)return;busy=true;requestAnimationFrame(()=>{busy=false;decorate()})}
document.addEventListener('DOMContentLoaded',()=>{decorate();new MutationObserver(schedule).observe(document.getElementById('dashboard')||document.body,{childList:true,subtree:true})});
})();

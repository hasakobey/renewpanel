/* One SVG set shared by navigation, actions, KPI cards and forms. */
(()=>{'use strict';
const paths={
 grid:'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z',
 car:'M3 12l3-7h12l3 7v6H3zM3 12h18M6 18v3m12-3v3M6 15h2m8 0h2',
 cart:'M2 3h3l3 13h11l3-10H6M9 21h.01M18 21h.01',
 money:'M2 5h20v14H2zM15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0M5 8h1m12 8h1',
 chart:'M3 3v18h18M7 16l5-7 4 4 5-8',bars:'M4 20V11h3v9m4 0V4h3v16m4 0v-6h3v6',
 clock:'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0M12 7v5l3 2',
 check:'M5 12l4 4L19 6',shield:'M12 2l8 4v6c0 5-8 10-8 10S4 17 4 12V6zM8 12l3 3 5-6',
 tag:'M3 3h8l10 10-8 8L3 11zM7 7h.01',calc:'M5 3h14v18H5zM8 7h8M8 11h1m6 0h1m-8 4h1m6 0h1m-8 3h1m6 0h1',
 camera:'M3 7h4l2-3h6l2 3h4v14H3zM16 13a4 4 0 1 1-8 0 4 4 0 0 1 8 0',
 video:'M3 5h12v14H3zM15 9l6-3v12l-6-3',orbit:'M20 5l1 5-5-1M21 10a9 9 0 1 0-1 7M8 10l4-2 4 2v5l-4 2-4-2zM8 10l4 2 4-2m-4 2v5',
 tool:'M14 3a6 6 0 0 0-7 8L2 16a3 3 0 0 0 4 4l6-6a6 6 0 0 0 8-7l-4 4-3-3z',
 target:'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0M17 12a5 5 0 1 1-10 0 5 5 0 0 1 10 0M12 12h.01',
 file:'M5 3h9l5 5v13H5zM14 3v6h5M8 13h8M8 17h6',download:'M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5',upload:'M12 16V4m-5 5 5-5 5 5M4 16v5h16v-5',
 settings:'M9 3h6l1 3 3 1 2 5-2 5-3 1-1 3H9l-1-3-3-1-2-5 2-5 3-1zM15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0',
 bell:'M5 17h14l-2-3V9a5 5 0 0 0-10 0v5zM10 21h4',user:'M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0M4 21v-3a8 8 0 0 1 16 0v3',
 users:'M10 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0M1 21v-3a6 6 0 0 1 12 0v3M16 3a4 4 0 0 1 0 8m1 3a5 5 0 0 1 5 5v2',
 search:'M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0m-2 5 6 6',plus:'M12 4v16M4 12h16',refresh:'M20 4v6h-6M4 20v-6h6M4 9a8 8 0 0 1 14-5l2 6M4 14l2 6a8 8 0 0 0 14-5',
 save:'M3 3h14l4 4v14H3zM7 3v6h9V3M7 21v-8h10v8',edit:'M14 4l6 6M3 21l2-7L17 2l5 5L10 19z',trash:'M3 6h18M8 6V3h8v3M6 6l1 15h10l1-15M10 10v7m4-7v7',
 arrow:'M4 12h16m-6-6 6 6-6 6',back:'M20 12H4m6-6-6 6 6 6',menu:'M3 6h18M3 12h18M3 18h18',close:'M5 5l14 14M19 5 5 19',
 warning:'M12 3L2 21h20zM12 9v5m0 3v1',sort:'M7 3v18m-4-4 4 4 4-4M17 21V3m-4 4 4-4 4 4',mail:'M3 5h18v14H3zM3 5l9 8 9-8',copy:'M8 8h13v13H8zM16 8V3H3v13h5',logout:'M9 3H3v18h6M9 12h12m-5-5 5 5-5 5'
};
const svg=(key,size=18)=>`<svg class="rn-icon" width="${size}" height="${size}" viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[key]||paths.file}"/></svg>`;
const nameFor=text=>{const s=String(text||'').toLocaleLowerCase('tr-TR');for(const [keys,name] of [[['360'],'orbit'],[['fotoğraf','kamera','galeri'],'camera'],[['video'],'video'],[['kopyala'],'copy'],[['sil','çıkar'],'trash'],[['düzenle'],'edit'],[['kaydet'],'save'],[['indir','excel'],'download'],[['yükle','aktar'],'upload'],[['rapor','pdf'],'file'],[['bildirim'],'bell'],[['yenile','önbellek'],'refresh'],[['sırala'],'sort'],[['arama','ara'],'search'],[['alım','alış'],'cart'],[['satış','ciro','gelir'],'money'],[['maliyet','masraf'],'calc'],[['kâr','performans','hedef'],'chart'],[['stok'],'car'],[['sks','süre'],'clock'],[['vazgeç','geri'],'back'],[['ekle','yeni'],'plus'],[['mail','ödeme'],'mail']])if(keys.some(k=>s.includes(k)))return name;return 'file'};
function apply(root=document){
 if(!root.querySelectorAll)return;
 const nodes=[...(root.matches?.('.btn')?[root]:[]),...root.querySelectorAll('.btn')];
 for(const n of nodes){if(n.dataset.rnIcon||n.querySelector('svg,.rfs-icon'))continue;n.dataset.rnIcon='1';const label=n.textContent.trim();if(!label)continue;const first=[...n.childNodes].find(x=>x.nodeType===3&&x.textContent.trim());if(first)first.textContent=first.textContent.replace(/^[\s＋+✓✔↻⇩⇅⇄▤◆↑↓↗📷💾✏🧹↪]+/u,'').trimStart();n.insertAdjacentHTML('afterbegin',svg(nameFor(label)))}
}
window.renewIcons={svg,apply,nameFor};
function boot(){
 const context=document.querySelector('.topbar #pageTitle')?.parentElement;context?.classList.add('rn-top-context');
 const map={dashboard:'grid',stocks:'car',sales:'money',acquisitions:'cart',photos:'camera','video-studio':'video',vehicle360:'orbit',expertise:'tool',performance:'chart',master:'file','stock-import':'upload','sales-import':'download',settings:'settings',reports:'bars',notifications:'bell',profile:'user',audit:'clock',users:'users'};
 document.querySelectorAll('.app>aside .nav').forEach(n=>{const i=n.querySelector('i');if(i)i.innerHTML=svg(map[n.dataset.page]);n.title=n.querySelector('b')?.textContent||''});
 const menu=document.getElementById('mobileMenuBtn');if(menu){menu.innerHTML=svg('menu');menu.setAttribute('aria-label','Menüyü aç');}
 const search=document.querySelector('#renewCommand>button>span');if(search)search.innerHTML=svg('search');
 const actions=document.querySelector('.top-actions');if(actions&&!actions.querySelector('.rn-header-notifications')){const btn=document.createElement('button');btn.className='rn-header-notifications';btn.type='button';btn.title='Bildirim Merkezi';btn.setAttribute('aria-label','Bildirim Merkezi');btn.innerHTML=svg('bell');btn.onclick=()=>page('notifications');actions.append(btn);if(typeof hasPerm==='function'&&!hasPerm('notifications.view'))btn.hidden=true;}
 const bottom=document.getElementById('renewMobileNav');if(bottom){const routes=[['dashboard','grid','Dashboard'],['stocks','car','Stok'],['sales','money','Satılanlar'],['acquisitions','cart','Alımlar'],['photos','camera','Fotoğraflar']];bottom.querySelectorAll('button').forEach((btn,i)=>{const [id,key,label]=routes[i];btn.innerHTML=svg(key)+`<small>${label}</small>`;btn.dataset.mobilePage=id;btn.setAttribute('aria-label',label);btn.onclick=()=>page(id)})}
 apply();
 const priorPage=window.page;window.page=function(id){const result=priorPage.apply(this,arguments);const actual=document.querySelector('.page.active')?.id;document.querySelectorAll('#renewMobileNav button').forEach(b=>b.classList.toggle('active',b.dataset.mobilePage===actual));document.body.classList.remove('mobile-nav-open');return result;};
 let scheduled=false;const pending=new Set();new MutationObserver(changes=>{for(const change of changes)for(const node of change.addedNodes)if(node.nodeType===1&&!node.closest('svg'))pending.add(node);if(scheduled||!pending.size)return;scheduled=true;requestAnimationFrame(()=>{scheduled=false;for(const node of pending)if(node.isConnected)apply(node);pending.clear()})}).observe(document.querySelector('.app'),{childList:true,subtree:true});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();

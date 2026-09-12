/* RENEW PRO 8.0 — dashboard, profile and media UX layer. Core Excel maths stay in calc.py. */
let RENEW_DASH_DATA=null,RENEW_PROFILE=null;

function renewNum(v){return Number(v||0)}
function renewCompactMoney(v){return new Intl.NumberFormat('tr-TR',{notation:'compact',maximumFractionDigits:1}).format(renewNum(v))+' ₺'}
function renewMonthLabel(v){const [y,m]=String(v).split('-');return new Date(Number(y),Number(m)-1,1).toLocaleDateString('tr-TR',{month:'short',year:'2-digit'})}

function renderRenewAlerts(d){
 const box=document.getElementById('dashAlerts');if(!box)return;
 const items=[];
 (d.critical_stock||[]).filter(x=>renewNum(x.sks)>=60).forEach(x=>items.push({level:renewNum(x.sks)>=90?'critical':'warning',icon:renewNum(x.sks)>=90?'!':'◷',title:`${x.plate} • ${x.vehicle||'Araç'}`,desc:`${Math.round(renewNum(x.sks))} gündür stokta`,badge:`${Math.round(renewNum(x.sks))} gün`,target:'stocks',filter:x.plate}));
 (d.loss_sales||[]).forEach(x=>items.push({level:'critical',icon:'↘',title:`${x.plate} • ${x.vehicle_info||'Satış'}`,desc:`Zararına satış • ${x.consultant||'Danışman belirtilmemiş'}`,badge:money(Math.abs(renewNum(x.profit))),target:'sales',filter:x.plate}));
 (PERF||[]).filter(x=>renewNum(x.target_sales)>0&&renewNum(x.sales_target_rate)<1).forEach(x=>{const rate=Math.round(renewNum(x.sales_target_rate)*100);items.push({level:'warning',icon:'◎',title:x.name||'Danışman',desc:`Aylık satış hedefinin altında • ${x.sales_count}/${x.target_sales} satış`,badge:`%${rate}`,target:'performance',filter:x.name})});
 const count=document.getElementById('dashAlertCount');if(count)count.textContent=`${items.length} kayıt`;
 box.innerHTML=items.length?items.map(x=>`<button class="dash-alert ${x.level}" onclick="openRenewAlert('${esc(x.target)}','${esc(x.filter||'')}')"><span class="dash-alert-icon">${x.icon}</span><div><b>${esc(x.title)}</b><small>${esc(x.desc)}</small></div><strong>${esc(x.badge)}</strong></button>`).join(''):'<div class="dash-alert success"><span class="dash-alert-icon">✓</span><div><b>Kontroller temiz</b><small>Seçili dönemde dikkat gerektiren kayıt bulunmuyor.</small></div><strong>0</strong></div>';
}
function openRenewAlert(target,filter){
 page(target);
 if(target==='stocks'){
  const q=document.getElementById('stockSearch');if(q)q.value=filter;
  renderStocks();
 }
 if(target==='sales'){const q=document.getElementById('salesSearch');if(q)q.value=filter;renderSales()}
}
function renewInitials(name){return String(name||'?').trim().split(/\s+/).slice(0,2).map(x=>x.charAt(0)).join('').toLocaleUpperCase('tr-TR')}
function renderRenewConsultants(){
 const host=document.getElementById('dashConsultants');if(!host)return;
 const salesBy=new Map();(SALES||[]).forEach(s=>{const key=String(s.consultant||'').trim().toLocaleUpperCase('tr-TR'),v=salesBy.get(key)||0;salesBy.set(key,v+renewNum(s.calc?.net_profit))});
 const rows=(PERF||[]).map(x=>{const rate=renewNum(x.sales_target_rate)*100,tone=rate>=100?'good':rate>=60?'warn':'bad',net=salesBy.get(String(x.name||'').trim().toLocaleUpperCase('tr-TR'))||0;return `<tr><td><div class="consultant-person"><span class="consultant-avatar ${tone}">${esc(renewInitials(x.name))}</span><b>${esc(x.name)}</b></div></td><td><b>${x.sales_count}</b></td><td class="${net<0?'loss':'profit'}"><b>${money(net)}</b></td><td><div class="target-cell ${tone}"><span><b>%${Math.round(rate)}</b><small>${x.sales_count}/${x.target_sales||0} satış</small></span><i><em style="width:${Math.min(100,Math.max(0,rate))}%"></em></i></div></td></tr>`});
 host.innerHTML=`<div class="consultant-table-scroll">${table(['Danışman','Satış Adedi','Net Kâr','Hedef Gerçekleşme'],rows)}</div>`;
}
function renderRenewTrend(d){
 const box=document.getElementById('salesTrendChart');if(!box)return;const rows=d.monthly_trend||[];
 const active=rows.filter(x=>x.sales_count||x.revenue||x.profit),recent=active.slice(-6),salesTarget=(SETTINGS.consultants||[]).filter(x=>x.active).reduce((a,x)=>a+renewNum(x.target_sales),0),profitTarget=(SETTINGS.consultants||[]).filter(x=>x.active).reduce((a,x)=>a+renewNum(x.target_profit),0);
 const salesPct=salesTarget?Math.min(100,d.sales_count/salesTarget*100):0,profitPct=profitTarget?Math.min(100,Math.max(0,d.sales_performance_profit)/profitTarget*100):0;
 const delta=(kind,label,now,prev,format,help)=>`<div class="pulse-compare ${kind}" title="${esc(help)}"><div class="metric-head"><span class="metric-icon"></span><small>${esc(label)}</small></div><div class="metric-values"><span><small>BU AY</small><b>${format(now)}</b></span><i class="${now>=prev?'up':'down'}">${now>=prev?'↗':'↘'} ${prev?Math.abs((now-prev)/prev*100).toFixed(0):now?'Yeni':'0'}${prev?'%':''}</i><span><small>GEÇEN AY</small><b>${format(prev)}</b></span></div></div>`;
 box.innerHTML=`<div class="pulse-comparisons">${delta('sales','Satış Adedi',d.sales_count,d.previous_sales_count,v=>v+' araç','Seçili ayda satılan toplam araç sayısı.')}${delta('revenue','Satış Cirosu',d.sales_revenue,d.previous_revenue,v=>renewCompactMoney(v),'Seçili ayın toplam araç satış bedeli.')}${delta('profit','Performans Kârı',d.sales_performance_profit,d.previous_performance_profit,v=>renewCompactMoney(v),'Excel matematiğine göre hesaplanan performans kârı.')}</div><div class="pulse-goals"><div class="goal-sales"><span><b>Satış Hedefi</b><small>${salesTarget?`${d.sales_count} satış yapıldı, hedef ${salesTarget} araç.`:'Danışman ayarlarından aylık satış hedefi belirleyebilirsiniz.'}</small></span><strong>${salesTarget?Math.round(salesPct)+'%':'Hedef yok'}</strong><i><em style="width:${salesPct}%"></em></i></div><div class="goal-profit"><span><b>Kâr Hedefi</b><small>${profitTarget?`${money(d.sales_performance_profit)} gerçekleşti, hedef ${money(profitTarget)}.`:'Danışman ayarlarından aylık kâr hedefi belirleyebilirsiniz.'}</small></span><strong>${profitTarget?Math.round(profitPct)+'%':'Hedef yok'}</strong><i><em class="yellow" style="width:${profitPct}%"></em></i></div></div><div class="pulse-efficiency"><div class="eff-profit"><small>Araç Başı Kâr</small><b>${money(d.avg_sale_profit)}</b><em>Satış başına ortalama performans kârı</em></div><div class="eff-margin"><small>Kâr Marjı</small><b>${pct(d.avg_margin)}</b><em>Ciro içindeki performans kârı oranı</em></div><div class="eff-sks"><small>Ortalama SKS</small><b>${renewNum(d.avg_sale_sks).toFixed(1)} gün</b><em>Satılan araçların ortalama stok süresi</em></div></div><div class="pulse-history"><span>İşlem bulunan aylar</span><div>${recent.length?recent.map(x=>`<button title="${money(x.revenue)} ciro • ${money(x.profit)} kâr"><small>${renewMonthLabel(x.month)}</small><b>${x.sales_count} satış</b></button>`).join(''):'<small>Henüz dönemsel satış verisi bulunmuyor.</small>'}</div></div>`;
}
function renderRenewSourceValue(d){
 const host=document.getElementById('purchaseTypes');if(!host)return;const rows=d.acquisition_sources||[];
 if(!rows.length)return;
 host.innerHTML='<div class="source-value-list">'+rows.slice(0,6).map(x=>`<div><span><b>${esc(x.name)}</b><small>${x.count} araç</small></span><strong>${renewCompactMoney(x.value)}</strong></div>`).join('')+'</div>';
}
const _renewOriginalRenderDashboard=renderDashboard;
renderDashboard=function(d){RENEW_DASH_DATA=d;_renewOriginalRenderDashboard(d);renderRenewAlerts(d);renderRenewConsultants();renderRenewTrend(d);renderRenewSourceValue(d)};

async function loadProfile(){
 const box=document.getElementById('profileActions');if(!box)return;box.innerHTML='<div class="empty">Profil yükleniyor…</div>';
 try{RENEW_PROFILE=await api('/api/profile');renderProfile()}catch(e){box.innerHTML=`<div class="error-box">${esc(e.message)}</div>`}
}
function entityName(v){return ({stock:'Stok',sale:'Satış',acquisition:'Alım',expertise:'Ekspertiz',settings:'Ayarlar',user:'Kullanıcı',auth:'Oturum',media:'Medya',import:'Excel Aktarımı'})[v]||v||'Diğer'}
function renderProfile(){
 const d=RENEW_PROFILE;if(!d)return;const u=d.user||{},s=d.summary||{};
 safe('#profileName',esc(u.full_name||u.username||'Profilim'));safe('#profileRole',`${esc(roleLabel(u.role))} • @${esc(u.username||'')}`);safe('#profileAvatar',esc((u.full_name||u.username||'R').charAt(0).toUpperCase()));
 kpis('#profileKpis',[['Toplam İşlem',renewNum(s.total_actions)+' kayıt','good','Son 100 hareket'],['Son İşlem',esc(s.last_action||'—'),'',''],['Rol',esc(roleLabel(u.role)),'',''],['Yetki',u.role==='administrator'?'Tüm Yetkiler':renewNum((u.permissions||[]).length)+' yetki','','']]);
 safe('#profileEntitySummary',Object.entries(s.by_entity||{}).sort((a,b)=>b[1]-a[1]).map(([k,v])=>`<div><span>${esc(entityName(k))}</span><b>${v}</b></div>`).join('')||'<div class="empty">Henüz işlem yok.</div>');
 safe('#profileDetails',`<div><span>Ad Soyad</span><b>${esc(u.full_name||'—')}</b></div><div><span>Kullanıcı Adı</span><b>${esc(u.username||'—')}</b></div><div><span>Rol</span><b>${esc(roleLabel(u.role))}</b></div><div><span>Durum</span><b>${u.active===false?'Pasif':'Aktif'}</b></div>`);renderProfileActions();
}
function renderProfileActions(){
 const box=document.getElementById('profileActions');if(!box||!RENEW_PROFILE)return;const q=(document.getElementById('profileActionSearch')?.value||'').toLocaleLowerCase('tr-TR');const rows=(RENEW_PROFILE.actions||[]).filter(x=>JSON.stringify(x).toLocaleLowerCase('tr-TR').includes(q));
 safe('#profileActions',table(['Tarih','Alan','İşlem','Detay'],rows.map(x=>`<tr><td>${esc(x.created_at||'')}</td><td><span class="profile-entity">${esc(entityName(x.entity))}</span></td><td><b>${esc(x.action||'')}</b></td><td>${esc(x.details||'')}</td></tr>`)));
}

function enhanceMediaCenter(){
 const gallery=document.getElementById('mediaGallery');if(!gallery||document.getElementById('mediaSmartTools'))return;
 const tools=document.createElement('div');tools.id='mediaSmartTools';tools.className='media-smart-tools';tools.innerHTML='<div><b>Medya Kontrolü</b><small>Dosyaları hızla bulun, görüntüleyin ve düzenleyin.</small></div><input id="mediaSearch" placeholder="Dosya adında ara…" oninput="applyMediaSmartFilter()"><select id="mediaSmartFilter" onchange="applyMediaSmartFilter()"><option value="all">Tüm kayıtlar</option><option value="images">Sadece görseller</option><option value="cover">Kapak fotoğrafı</option></select><button class="btn ghost small" onclick="toggleMediaDensity()">Görünümü Değiştir</button>';
 gallery.parentElement.insertBefore(tools,gallery);
 gallery.addEventListener('click',e=>{const img=e.target.closest('.media-card img');if(img)openMediaPreview(img.src,img.closest('.media-card')?.dataset.name||'Fotoğraf')});
}
function applyMediaSmartFilter(){const q=(document.getElementById('mediaSearch')?.value||'').toLocaleLowerCase('tr-TR'),f=document.getElementById('mediaSmartFilter')?.value||'all';document.querySelectorAll('#mediaGallery .media-card').forEach(x=>{const name=(x.dataset.name||'').toLocaleLowerCase('tr-TR'),isImg=!!x.querySelector('img'),isCover=!!x.querySelector('.cover-badge');x.style.display=(!q||name.includes(q))&&(f==='all'||f==='images'&&isImg||f==='cover'&&isCover)?'':'none'})}
function toggleMediaDensity(){document.getElementById('mediaGallery')?.classList.toggle('compact')}
function openMediaPreview(src,name){let x=document.getElementById('mediaPreviewModal');if(!x){x=document.createElement('div');x.id='mediaPreviewModal';x.className='media-preview-modal';x.onclick=e=>{if(e.target===x)x.classList.remove('show')};document.body.appendChild(x)}x.innerHTML=`<button onclick="document.getElementById('mediaPreviewModal').classList.remove('show')">×</button><img src="${src}" alt="${esc(name)}"><b>${esc(name)}</b>`;x.classList.add('show')}
const _renewRenderMediaGallery=renderMediaGallery;
renderMediaGallery=function(){_renewRenderMediaGallery();enhanceMediaCenter();applyMediaSmartFilter();const n=document.getElementById('mediaCount');if(n&&CURRENT_MEDIA)n.textContent=`${((CURRENT_MEDIA.folders||{})[CURRENT_MEDIA_TAB]||[]).length} kayıt • ${esc(CURRENT_MEDIA.plate||mediaPlate())}`};

const _renewPage=page;
page=function(id){if(id==='payment-center'||id==='mail-templates')id='dashboard';_renewPage(id);if(id==='profile')loadProfile();if(id==='photos')setTimeout(enhanceMediaCenter,0)};
const RENEW_NAV_ICONS={
 dashboard:'<path d="M4 13h6V4H4zM14 20h6V11h-6zM4 20h6v-3H4zM14 7h6V4h-6z"/>',
 stocks:'<path d="M3 13l2-5h14l2 5v6h-3v-2H6v2H3zM7 13h10M7 8l2-3h6l2 3"/>',
 sales:'<path d="M12 3v18M16 7.5c0-1.7-1.8-3-4-3s-4 1.3-4 3 1.8 2.5 4 3 4 1.3 4 3-1.8 3-4 3-4-1.3-4-3"/>',
 acquisitions:'<path d="M4 7h16l-1.5 12h-13zM8 7a4 4 0 018 0M9 11v4M15 11v4"/>',
 photos:'<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 15l-5-4-7 7"/>',
 vehicle360:'<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/>',
 expertise:'<path d="M4 20V7l8-4 8 4v13M8 20v-7h8v7M9 9h6"/>',
 performance:'<path d="M4 19V9M10 19V5M16 19v-8M22 19H2"/>',
 master:'<path d="M4 4h16v16H4zM8 4v16M4 9h16M4 14h16"/>',
 'stock-import':'<path d="M12 3v12M7 10l5 5 5-5M4 21h16"/>',
 'sales-import':'<path d="M7 7h12l-3-3M17 17H5l3 3M19 7l-3 3M5 17l3-3"/>',
 settings:'<circle cx="12" cy="12" r="3"/><path d="M19 12l2-1-2-4-2 1-2-2V3h-6v3L7 8 5 7l-2 4 2 1v3l-2 1 2 4 2-1 2 2h6v-3l2-2 2 1 2-4-2-1z"/>',
 reports:'<path d="M5 3h14v18H5zM8 8h8M8 12h8M8 16h5"/>',
 profile:'<circle cx="12" cy="8" r="4"/><path d="M4 21c1-5 4-7 8-7s7 2 8 7"/>',
 audit:'<path d="M3 12a9 9 0 109-9 9 9 0 00-7 3L3 8M3 3v5h5M12 7v5l3 2"/>',
 users:'<path d="M9 11a4 4 0 100-8 4 4 0 000 8M2 21c0-5 3-8 7-8s7 3 7 8M17 11a3 3 0 100-6M18 13c3 .5 4 3 4 6"/>'
};
function applyRenewNavIcons(){document.querySelectorAll('.nav[data-page]').forEach(n=>{const i=n.querySelector('i'),p=RENEW_NAV_ICONS[n.dataset.page];if(i&&p)i.innerHTML=`<svg viewBox="0 0 24 24" aria-hidden="true">${p}</svg>`})}
document.addEventListener('DOMContentLoaded',()=>{enhanceMediaCenter();applyRenewNavIcons();document.documentElement.classList.add('renew-v8')});

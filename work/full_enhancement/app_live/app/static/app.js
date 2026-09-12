const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
let STOCKS=[],SALES=[],EXPERTISE=[],PERF=[],SETTINGS={},stockImport=[],salesImport=[],MASTER=null,currentSettingsTab='expenses';
const trMoney=new Intl.NumberFormat('tr-TR',{style:'currency',currency:'TRY',maximumFractionDigits:0});
const money=v=>trMoney.format(Number(v||0)), pct=v=>'%'+(Number(v||0)*100).toFixed(1).replace('.',','), esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
const MONEY_KEYS=new Set(['purchase_price','list_price','target_profit','sale_price','extra_expense','insurance_income','credit_income','warranty_income','target_profit']);
function parseMoney(v){
 let s=String(v??'').trim().replace(/\s/g,'').replace(/TL|₺/gi,'');
 if(!s)return 0;
 // Türkçe görüntü: 1.280.000 veya 1.280.000,50. Sade 1280000 da kabul edilir.
 if(s.includes(',') && s.includes('.')) s=s.replace(/\./g,'').replace(',','.');
 else if(s.includes(',')) s=s.replace(',','.');
 else if((s.match(/\./g)||[]).length>=1 && /^-?\d{1,3}(\.\d{3})+$/.test(s)) s=s.replace(/\./g,'');
 s=s.replace(/[^0-9.-]/g,''); let n=Number(s); return Number.isFinite(n)?n:0;
}
function formatAmount(v){let n=parseMoney(v);return n?new Intl.NumberFormat('tr-TR',{maximumFractionDigits:2}).format(n):''}
function normalizeTR(v){return String(v??'').trim().toLocaleUpperCase('tr-TR').replace(/İ/g,'I').replace(/Ş/g,'S').replace(/Ğ/g,'G').replace(/Ü/g,'U').replace(/Ö/g,'O').replace(/Ç/g,'C').replace(/\s+/g,' ')}
function canonicalFrom(value,items,key='name'){
 let n=normalizeTR(value);if(!n)return '';
 let hit=(items||[]).find(x=>normalizeTR(typeof x==='string'?x:x[key])===n);
 return hit?(typeof hit==='string'?hit:hit[key]):'';
}
function activePurchaseTypes(){return (SETTINGS.rules||[]).filter(x=>x.active).map(x=>x.name)}
function activeSaleTypes(){return (SETTINGS.sale_types||[]).filter(x=>x.active).map(x=>x.name)}
function activeConsultants(){return (SETTINGS.consultants||[]).filter(x=>x.active).map(x=>x.name)}
function requiredSelect(options,value,onchange,label){let opts=['<option value="">— SEÇİM ZORUNLU —</option>',...options.map(x=>`<option value="${esc(x)}" ${x===value?'selected':''}>${esc(x)}</option>`)].join('');return `<select class="import-edit required-select ${value?'':'needs-choice'}" onchange="${onchange}">${opts}</select>`}
function validateStockRows(rows){let bad=rows.filter(r=>!canonicalFrom(r.purchase_type,activePurchaseTypes()));if(bad.length){alert(`${bad.length} stok kaydında Alım Türü seçilmemiş/eşleşmemiş. Kırmızı alanlardan seçim yapmadan aktarım yapılamaz.`);return false}return true}
function validateSalesRows(rows){let bad=rows.filter(r=>!canonicalFrom(r.purchase_type,activePurchaseTypes())||!canonicalFrom(r.sale_type,activeSaleTypes())||!canonicalFrom(r.consultant,activeConsultants()));if(bad.length){alert(`${bad.length} satış kaydında Alım Türü, Satış Türü veya Danışman seçimi eksik. Kırmızı alanları tamamlamadan aktarım yapılamaz.`);return false}return true}

async function api(url,opt={}){let r=await fetch(url,{cache:'no-store',...opt});let ct=r.headers.get('content-type')||'';if(!r.ok){let msg='';try{if(ct.includes('json')){let j=await r.json();msg=j.detail||j.message||JSON.stringify(j)}else msg=await r.text()}catch(e){msg=r.statusText}throw new Error(msg||('HTTP '+r.status))}return ct.includes('json')?r.json():r}
function safe(id,html){let n=$(id);if(n)n.innerHTML=html}
function month(){return $('#globalMonth').value}
function table(heads,rows){return `<div class="tablewrap"><table><thead><tr>${heads.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${rows.join('')||`<tr><td colspan="${heads.length}" class="empty">Kayıt yok</td></tr>`}</tbody></table></div>`}
function kpis(id,a){safe(id,a.map(x=>`<div class="kpi ${x[2]||''}"><label>${x[0]}</label><strong>${x[1]}</strong><small>${x[3]||''}</small></div>`).join(''))}
function page(id){$$('.page').forEach(x=>x.classList.toggle('active',x.id===id));$$('.nav').forEach(x=>x.classList.toggle('active',x.dataset.page===id));let n=$(`.nav[data-page="${id}"] b`);$('#pageTitle').textContent=n?n.textContent:'RENEW PRO';localStorage.setItem('renew_v6_page',id);if(id==='audit')loadAudit();if(id==='master')loadImportHistory()}
$$('.nav').forEach(b=>b.onclick=()=>page(b.dataset.page));
function setStatus(s){$('#status').textContent=s}
function trend(v){return `<span class="${v>=0?'up':'down'}">${v>=0?'▲':'▼'} ${Math.abs(v*100).toFixed(1).replace('.',',')}%</span>`}
function bars(items){let max=Math.max(1,...(items||[]).map(x=>x.count));return `<div class="bars">${(items||[]).map(x=>`<div class="bar"><span>${esc(x.name)}</span><div class="track"><div class="fill" style="width:${x.count/max*100}%"></div></div><b>${x.count}</b></div>`).join('')||'<div class="empty">Veri yok</div>'}</div>`}

async function refreshAll(){
 setStatus('Veriler güncelleniyor...');
 try{
  let m=month();let [d,st,sa,se,pf,ex,ac,acs]=await Promise.all([api('/api/dashboard?month='+m),api('/api/stocks'),api('/api/sales?month='+m),api('/api/settings'),api('/api/performance?month='+m),api('/api/expertise?month='+m),api('/api/acquisitions?month='+m),api('/api/acquisitions/summary?month='+m)]);
  STOCKS=st;SALES=sa;SETTINGS=se;PERF=pf;EXPERTISE=ex;ACQUISITIONS=ac;ACQSUMMARY=acs;
  renderDashboard(d);renderStocks();renderSales();renderAcquisitions();renderDashAcquisitions();renderExpertise();renderPerformance();renderSettings();updateReportLinks();setStatus(`Canlı veri • ${m}`);
 }catch(e){console.error(e);setStatus('Hata: '+e.message)}
}
function renderDashboard(d){
 kpis('#dashKpis',[['Güncel Stok',d.stock_count+' Adet','good','Aktif'],['Stok Alış',money(d.stock_purchase_total),'','Alış toplamı'],['Stok Maliyeti',money(d.stock_cost_total),'','Gider + SKS'],['Stok Satış',money(d.stock_sale_value),'','Liste toplamı'],['Tahmini Stok Kârı',money(d.stock_estimated_profit),d.stock_estimated_profit<0?'bad':'good',''],['SKS Finansman',money(d.stock_sks_finance),'warn',''],
 ['Aylık Satış',d.sales_count+' Adet','good',''],['Aylık Ciro',money(d.sales_revenue),'',''],['Net Kâr',money(d.sales_net_profit),d.sales_net_profit<0?'bad':'good',''],['Performans Kârı',money(d.sales_performance_profit),d.sales_performance_profit<0?'bad':'good',''],['Ort. Satış Kârı',money(d.avg_sale_profit),'',''],['Ort. Satış SKS',d.avg_sale_sks.toFixed(1)+' Gün','','']]);
 safe('#monthCompare',`<div class="compare"><span>SATIŞ ADEDİ</span><b>${d.sales_count} Adet</b>Geçen ay ${d.previous_sales_count} · ${trend(d.sales_count_change)}</div><div class="compare"><span>CİRO</span><b>${money(d.sales_revenue)}</b>Geçen ay ${money(d.previous_revenue)} · ${trend(d.revenue_change)}</div><div class="compare"><span>PERFORMANS KÂRI</span><b class="${d.sales_performance_profit<0?'loss':'profit'}">${money(d.sales_performance_profit)}</b>Geçen ay ${money(d.previous_performance_profit)} · ${trend(d.profit_change)}</div>`);
 safe('#risk',`<div class="r1">0–30 Gün<br><b>${d.stock_risk['0_30']}</b></div><div class="r2">31–60 Gün<br><b>${d.stock_risk['31_60']}</b></div><div class="r3">61–90 Gün<br><b>${d.stock_risk['61_90']}</b></div><div class="r4">90+ Kritik<br><b>${d.stock_risk['90_plus']}</b></div>`);safe('#riskSummary',`<p class="hint">Ortalama stok SKS: <b>${d.stock_avg_sks.toFixed(1)} gün</b> • Kritik: <b>${d.stock_critical_count}</b></p>`);
 safe('#profitSplit',`<div class="split"><div class="g">Kârlı / Başabaş<b>${d.profitable_sales}</b></div><div class="r">Zararlı<b>${d.losing_sales}</b></div></div><p class="hint">Ortalama performans marjı: <b>${pct(d.avg_margin)}</b></p>`);
 safe('#purchaseMonth',`<div class="split"><div class="g">Bu Ay Alınan<b>${d.purchased_count}</b></div><div class="g">Alım Değeri<b style="font-size:15px">${money(d.purchased_value)}</b></div></div>`);safe('#purchaseTypes',bars(d.purchase_type_distribution));
 safe('#brandDist',bars(d.brand_distribution));
 safe('#dashConsultants',table(['Danışman','Satış','Ciro','Perf. Kâr','Ort. SKS'],(d.consultant_summary||[]).map(x=>`<tr><td><b>${esc(x.name)}</b></td><td>${x.sales_count}</td><td>${money(x.revenue)}</td><td class="${x.profit<0?'loss':'profit'}">${money(x.profit)}</td><td>${x.avg_sks.toFixed(1)}</td></tr>`)));
 safe('#topSales',table(['Plaka','Araç','Danışman','SKS','Kâr'],(d.top_sales||[]).map(x=>`<tr><td><b>${esc(x.plate)}</b></td><td>${esc(x.vehicle_info)}</td><td>${esc(x.consultant)}</td><td>${x.sks}</td><td class="profit">${money(x.profit)}</td></tr>`)));
 safe('#lossSales',table(['Plaka','Araç','Danışman','SKS','Zarar'],(d.loss_sales||[]).map(x=>`<tr class="lossrow"><td><b>${esc(x.plate)}</b></td><td>${esc(x.vehicle_info)}</td><td>${esc(x.consultant)}</td><td>${x.sks}</td><td class="loss">${money(x.profit)}</td></tr>`)));
 safe('#criticalStock',table(['Plaka','Araç','SKS','Alış','Satış','Finansman','Maliyet','Tahmini Kâr'],(d.critical_stock||[]).map(x=>`<tr class="${x.profit<0?'lossrow':''}"><td><b>${esc(x.plate)}</b></td><td>${esc(x.vehicle)}</td><td>${x.sks}</td><td>${money(x.purchase_price)}</td><td>${money(x.list_price)}</td><td>${money(x.finance)}</td><td>${money(x.total_cost)}</td><td class="${x.profit<0?'loss':'profit'}">${money(x.profit)}</td></tr>`)));
 safe('#expertiseSummary',`<div class="split"><div class="g">Yapılan Ekspertiz<b>${d.expertise_done}</b></div><div class="g">Alıma Dönüşen<b>${d.expertise_converted}</b></div></div><p class="hint">Dönüşüm: <b>${pct(d.expertise_rate)}</b></p>`);
 safe('#recentActivity',(d.recent_activity||[]).map(x=>`<div class="activity"><b>${esc(x.action)} • ${esc(x.entity)}</b><small>${esc(x.details||'')} • ${esc(x.created_at)}</small></div>`).join('')||'<div class="empty">İşlem yok</div>');
}
function sksBadge(d){let c=d<=30?'sks-ok':d<=60?'sks-watch':d<=90?'sks-action':'sks-critical';return `<span class="sksbadge ${c}">${d} Gün</span>`}
function syncFilterOptions(){
 let b=$('#stockBrand'),sc=$('#salesConsultant'),pt=$('#salesPurchaseType');
 if(b){let v=b.value;b.innerHTML='<option value="">Tüm Markalar</option>'+[...new Set(STOCKS.map(x=>x.brand).filter(Boolean))].sort().map(x=>`<option>${esc(x)}</option>`).join('');b.value=v}
 if(sc){let v=sc.value;sc.innerHTML='<option value="">Tüm Danışmanlar</option>'+[...new Set(SALES.map(x=>x.consultant).filter(Boolean))].sort().map(x=>`<option>${esc(x)}</option>`).join('');sc.value=v}
 if(pt){let v=pt.value;pt.innerHTML='<option value="">Tüm Alım Türleri</option>'+[...new Set(SALES.map(x=>x.purchase_type).filter(Boolean))].sort().map(x=>`<option>${esc(x)}</option>`).join('');pt.value=v}
}
function sksMatch(d,v){return !v||(v==='0_30'&&d<=30)||(v==='31_60'&&d>=31&&d<=60)||(v==='61_90'&&d>=61&&d<=90)||(v==='90_plus'&&d>90)}
function renderStocks(){
 syncFilterOptions();let q=($('#stockSearch')?.value||'').toLocaleUpperCase('tr-TR'),brand=$('#stockBrand')?.value||'',sv=$('#stockSks')?.value||'',sort=$('#stockSort')?.value||'sks_desc';
 let rows=STOCKS.filter(r=>(!q||JSON.stringify(r).toLocaleUpperCase('tr-TR').includes(q))&&(!brand||r.brand===brand)&&sksMatch(r.calc.sks_days,sv));
 rows=[...rows].sort((a,b)=>sort==='sks_asc'?a.calc.sks_days-b.calc.sks_days:sort==='brand'?String(a.brand).localeCompare(String(b.brand),'tr'):sort==='price_desc'?b.list_price-a.list_price:sort==='profit_desc'?b.calc.estimated_profit-a.calc.estimated_profit:b.calc.sks_days-a.calc.sks_days);
 let profit=rows.reduce((a,r)=>a+r.calc.estimated_profit,0);kpis('#stockKpis',[['Stok',rows.length+' Adet','good','Filtrelenen'],['Alış Toplamı',money(rows.reduce((a,r)=>a+r.purchase_price,0)),'',''],['Satış Değeri',money(rows.reduce((a,r)=>a+r.list_price,0)),'',''],['SKS Finansman',money(rows.reduce((a,r)=>a+r.calc.sks_finance,0)),'warn','Alım türü kuralına göre'],['Stok Maliyeti',money(rows.reduce((a,r)=>a+r.calc.total_cost,0)),'',''],['Tahmini Net Kâr',money(profit),profit<0?'bad':'good','']]);
 let heads=['Sıra','Plaka','Model Yılı','KM','Marka','Model','Versiyon','Renk','Alış Tarihi','SKS Süresi','Yakıt','Vites','Alım Türü','Alış Fiyatı','Satış Fiyatı','Hedef Kazanç','Sabit Masraflar','SKS Finansman','Masraflar Dahil Toplam Alış','Tahmini Net Kâr','İşlem'];
 safe('#stockTable',table(heads,rows.map((r,i)=>`<tr class="${r.calc.estimated_profit<0?'lossrow':''}"><td>${i+1}</td><td><b>${esc(r.plate)}</b></td><td>${r.model_year||''}</td><td>${r.km||0}</td><td>${esc(r.brand)}</td><td>${esc(r.model)}</td><td>${esc(r.version)}</td><td>${esc(r.color)}</td><td>${r.purchase_date||''}</td><td>${sksBadge(r.calc.sks_days)}</td><td>${esc(r.fuel)}</td><td>${esc(r.transmission)}</td><td><b>${esc(r.purchase_type||'')}</b></td><td>${money(r.purchase_price)}</td><td>${money(r.list_price)}</td><td>${money(r.target_profit)}</td><td>${money(r.calc.fixed_expense)}</td><td class="finance">${money(r.calc.sks_finance)}</td><td>${money(r.calc.total_cost)}</td><td class="${r.calc.estimated_profit<0?'loss':'profit'}">${money(r.calc.estimated_profit)}</td><td><button class="btn primary small" onclick="openVehicleCard('${esc(r.plate)}')">360°</button> <button class="btn dark small" onclick="openVehiclePhotos('${esc(r.plate)}')">📷</button> <button class="btn small" onclick="openStock(${r.id})">Düzenle</button> <button class="btn success small" onclick="openSell(${r.id})">Satıldı</button> <button class="btn danger small" onclick="delStock(${r.id})">Sil</button></td></tr>`)));
}
function renderSales(){
 syncFilterOptions();let q=($('#salesSearch')?.value||'').toLocaleUpperCase('tr-TR'),co=$('#salesConsultant')?.value||'',pt=$('#salesPurchaseType')?.value||'',sv=$('#salesSks')?.value||'',pv=$('#salesProfit')?.value||'';
 let rows=SALES.filter(r=>(!q||JSON.stringify(r).toLocaleUpperCase('tr-TR').includes(q))&&(!co||r.consultant===co)&&(!pt||r.purchase_type===pt)&&sksMatch(r.calc.sks_days,sv)&&(!pv||(pv==='profit'?r.calc.performance_profit>=0:r.calc.performance_profit<0)));let perf=rows.reduce((a,r)=>a+r.calc.performance_profit,0);
 kpis('#salesKpis',[['Satılan',rows.length+' Adet','good','Filtrelenen'],['Ciro',money(rows.reduce((a,r)=>a+r.sale_price,0)),'',''],['Net Kâr',money(rows.reduce((a,r)=>a+r.calc.net_profit,0)),perf<0?'bad':'good',''],['Performans Kârı',money(perf),perf<0?'bad':'good',''],['Ort. Kâr',money(rows.length?perf/rows.length:0),'',''],['Zararlı Satış',rows.filter(r=>r.calc.performance_profit<0).length+' Adet','bad','']]);
 let heads=['Sayı','Otomobil Bilgileri','M.Yılı','Plaka','Alım Türü','Alış Bedeli','Alış Tarihi','Satış Tarihi','SKS Gün','Noter','Ekspertiz','150 Nokta','Sigorta Gideri','Ek Masraf','SKS Finansman','Toplam Gider','Toplam Maliyet','Müşteri Bilgileri','Satış Türü','Satış Bedeli','Brüt Kâr','Net Kâr','Net Kârlılık','Stok Durumu','Satış Danışmanı','Sigorta-Kasko Geliri','Kredi Geliri','Uzatılmış Garanti Geliri','Toplam Ek Gelir','Performans Net Kârı','İşlem'];
 safe('#salesTable',table(heads,rows.map((r,i)=>{let c=r.calc;return `<tr class="${c.performance_profit<0?'lossrow':''}"><td>${i+1}</td><td>${esc(r.vehicle_info)}</td><td>${r.model_year||''}</td><td><b>${esc(r.plate)}</b></td><td>${esc(r.purchase_type)}</td><td>${money(r.purchase_price)}</td><td>${r.purchase_date||''}</td><td>${r.sale_date||''}</td><td>${sksBadge(c.sks_days)}</td><td>${money(c.notary)}</td><td>${money(c.expertise)}</td><td>${money(c.control150)}</td><td>${money(c.insurance)}</td><td>${money(r.extra_expense)}</td><td class="finance">${money(c.sks_finance)}</td><td>${money(c.total_expense)}</td><td>${money(c.total_cost)}</td><td>${esc(r.customer)}</td><td>${esc(r.sale_type)}</td><td>${money(r.sale_price)}</td><td class="${c.gross_profit<0?'loss':'profit'}">${money(c.gross_profit)}</td><td class="${c.net_profit<0?'loss':'profit'}">${money(c.net_profit)}</td><td class="${c.net_margin<0?'loss':'profit'}">${pct(c.net_margin)}</td><td>${c.stock_status}</td><td>${esc(r.consultant)}</td><td>${money(r.insurance_income)}</td><td>${money(r.credit_income)}</td><td>${money(r.warranty_income)}</td><td>${money(c.extra_income)}</td><td class="${c.performance_profit<0?'loss':'profit'}">${money(c.performance_profit)}</td><td><button class="btn primary small" onclick="openVehicleCard('${esc(r.plate)}')">360°</button> <button class="btn dark small" onclick="openVehiclePhotos('${esc(r.plate)}')">📷</button> <button class="btn small" onclick="openSale(${r.id})">Düzenle</button> <button class="btn danger small" onclick="delSale(${r.id})">Sil</button></td></tr>`})));
}
function renderExpertise(){
 let total=EXPERTISE.reduce((a,r)=>a+Number(r.done_count||0),0),conv=EXPERTISE.reduce((a,r)=>a+Number(r.converted_count||0),0),cost=Number(SETTINGS.settings?.expertise_expense||0);
 kpis('#expertiseKpis',[['Personel',EXPERTISE.length+' Kişi','good','Excel EXPERTİZ TAKİP'],['Ekspertiz',total+' Adet','',''],['Alıma Dönüşen',conv+' Adet','',''],['Dönüşüm',pct(total?conv/total:0),'',''],['Toplam Maliyet',money(total*cost),'warn',''],['Alım Başı Maliyet',money(conv?total*cost/conv:0),'','']]);
 let rows=EXPERTISE.map((r,i)=>`<tr><td><b>${esc(r.consultant)}</b></td><td><input id="exd_${i}" type="number" min="0" value="${Number(r.done_count||0)}"></td><td><input id="exc_${i}" type="number" min="0" value="${Number(r.converted_count||0)}"></td><td>${pct(Number(r.done_count)?Number(r.converted_count)/Number(r.done_count):0)}</td><td>${money(Number(r.done_count||0)*cost)}</td><td>${money(Number(r.converted_count)?Number(r.done_count||0)*cost/Number(r.converted_count):0)}</td><td><button class="btn danger small" onclick="removeExpertisePerson(${i})">Çıkar</button></td></tr>`);
 safe('#expertiseTable',`<div class="expertise-table">${table(['Personel','Yapılan Ekspertiz','Alıma Dönüşen','Dönüşüm','Ekspertiz Maliyeti','Alım Başı Maliyet','İşlem'],rows)}</div>`);
}
function renderPerformance(){
 let perf=PERF.reduce((a,r)=>a+r.performance_profit,0),sales=PERF.reduce((a,r)=>a+r.sales_count,0);
 kpis('#perfKpis',[['Aktif Danışman',PERF.length+' Kişi','good',''],['Satış',sales+' Adet','',''],['Ciro',money(PERF.reduce((a,r)=>a+r.revenue,0)),'',''],['Performans Kârı',money(perf),perf<0?'bad':'good',''],['Araç Başı Kâr',money(sales?perf/sales:0),'',''],['Ort. SKS',(PERF.length?PERF.reduce((a,r)=>a+r.avg_sks,0)/PERF.length:0).toFixed(1)+' Gün','','']]);
 safe('#perfTable',table(['Danışman','Satış','Ciro','Performans Kârı','Araç Başı Kâr','Ort. SKS','Hedef Satış','Hedef Net Kâr','Satış Hedef Gerçekleşme'],PERF.map(r=>`<tr><td><b>${esc(r.name)}</b></td><td>${r.sales_count}</td><td>${money(r.revenue)}</td><td class="${r.performance_profit<0?'loss':'profit'}">${money(r.performance_profit)}</td><td>${money(r.avg_profit)}</td><td>${r.avg_sks.toFixed(1)}</td><td>${r.target_sales}</td><td>${money(r.target_profit)}</td><td>${pct(r.sales_target_rate)}</td></tr>`)));
}
function renderSettings(){
 let s=SETTINGS.settings||{};
 safe('#set_expenses',`<h3>Gider & SKS Ayarları</h3><p class="hint">Excel GİDER AYARLARI ile birebir.</p><div class="settings-grid">
 ${[['notary_expense','Noter Masrafı'],['expertise_expense','Ekspertiz Masrafı'],['control150_expense','150 Nokta Kontrol'],['insurance_expense','Sigorta Gideri'],['sks_monthly_rate','SKS Aylık Finansman Oranı']].map(([k,l])=>`<div class="settingbox"><div class="field"><label>${l}</label><input id="set_${k}" type="number" step="0.001" value="${s[k]??0}"></div></div>`).join('')}
 <div class="settingbox"><div class="field"><label>Excel Uyumluluk Modu</label><select id="set_excel_compatibility_mode"><option value="1" ${Number(s.excel_compatibility_mode??1)?'selected':''}>AÇIK — Excel formülü birebir</option><option value="0" ${!Number(s.excel_compatibility_mode??1)?'selected':''}>GELİŞMİŞ — Sabit gider kuralını uygula</option></select></div></div></div><div class="notice">Önerilen: <b>AÇIK</b>. Böylece panel matematiği mevcut Excel formülleriyle birebir çalışır; ALIM AYARLARI'nda bulunmayan alım türlerinde SKS 0 olur.</div>`);
 safe('#set_purchase',`<div class="cardhead"><h3>Alım Türü Ayarları</h3><button class="btn primary small" onclick="addRule()">+ Alım Türü</button></div>${table(['Alım Türü','SKS Uygula','Sabit Gider Uygula','Aktif','İşlem'],(SETTINGS.rules||[]).map((r,i)=>`<tr><td><input id="pr_name_${i}" value="${esc(r.name)}"></td><td><input id="pr_sks_${i}" type="checkbox" ${r.apply_sks?'checked':''}></td><td><input id="pr_fixed_${i}" type="checkbox" ${r.apply_fixed?'checked':''}></td><td><input id="pr_active_${i}" type="checkbox" ${r.active?'checked':''}></td><td><button class="btn danger small" onclick="SETTINGS.rules.splice(${i},1);renderSettings()">Çıkar</button></td></tr>`))}`);
 safe('#set_sale',`<div class="cardhead"><h3>Satış Türleri</h3><button class="btn primary small" onclick="addSaleType()">+ Satış Türü</button></div>${table(['Satış Türü','Aktif','İşlem'],(SETTINGS.sale_types||[]).map((r,i)=>`<tr><td><input id="st_name_${i}" value="${esc(r.name)}"></td><td><input id="st_active_${i}" type="checkbox" ${r.active?'checked':''}></td><td><button class="btn danger small" onclick="SETTINGS.sale_types.splice(${i},1);renderSettings()">Çıkar</button></td></tr>`))}`);
 safe('#set_income',`<div class="cardhead"><h3>Ek Gelir Türleri</h3><button class="btn primary small" onclick="addIncomeType()">+ Gelir Türü</button></div>${table(['Gelir Türü','Aktif','Açıklama','İşlem'],(SETTINGS.income_types||[]).map((r,i)=>`<tr><td><input id="it_name_${i}" value="${esc(r.name)}"></td><td><input id="it_active_${i}" type="checkbox" ${r.active?'checked':''}></td><td><input id="it_desc_${i}" value="${esc(r.description||'')}"></td><td><button class="btn danger small" onclick="SETTINGS.income_types.splice(${i},1);renderSettings()">Çıkar</button></td></tr>`))}`);
 safe('#set_consultants',`<div class="cardhead"><h3>Danışman Ayarları</h3><button class="btn primary small" onclick="addConsultant()">+ Danışman</button></div>${table(['Danışman','Aktif','Hedef Satış Adedi','Hedef Net Kâr'],(SETTINGS.consultants||[]).map((r,i)=>`<tr><td><input id="co_name_${i}" value="${esc(r.name)}"></td><td><input id="co_active_${i}" type="checkbox" ${r.active?'checked':''}></td><td><input id="co_sales_${i}" type="number" value="${r.target_sales||0}"></td><td><input id="co_profit_${i}" type="number" value="${r.target_profit||0}"></td></tr>`))}`);
}
function settingsTab(t){currentSettingsTab=t;$$('.settings-pane').forEach(x=>x.classList.toggle('active',x.id==='set_'+t));$$('.settings-tabs button').forEach((x,i)=>x.classList.toggle('active',['expenses','purchase','sale','income','consultants'][i]===t))}
function addRule(){SETTINGS.rules.push({name:'YENİ ALIM TÜRÜ',apply_sks:0,apply_fixed:1,active:1});renderSettings();settingsTab('purchase')} function addSaleType(){SETTINGS.sale_types.push({name:'YENİ SATIŞ TÜRÜ',active:1});renderSettings();settingsTab('sale')} function addIncomeType(){SETTINGS.income_types.push({name:'YENİ GELİR',active:1,description:''});renderSettings();settingsTab('income')} function addConsultant(){SETTINGS.consultants.push({name:'YENİ DANIŞMAN',active:1,target_sales:0,target_profit:0});renderSettings();settingsTab('consultants')}
async function saveSettings(){
 let st={};['notary_expense','expertise_expense','control150_expense','insurance_expense','sks_monthly_rate','excel_compatibility_mode'].forEach(k=>st[k]=Number($('#set_'+k)?.value||0));
 let rules=(SETTINGS.rules||[]).map((r,i)=>({name:$('#pr_name_'+i)?.value||r.name,apply_sks:$('#pr_sks_'+i)?.checked??r.apply_sks,apply_fixed:$('#pr_fixed_'+i)?.checked??r.apply_fixed,active:$('#pr_active_'+i)?.checked??r.active}));
 let sale_types=(SETTINGS.sale_types||[]).map((r,i)=>({name:$('#st_name_'+i)?.value||r.name,active:$('#st_active_'+i)?.checked??r.active}));
 let income_types=(SETTINGS.income_types||[]).map((r,i)=>({name:$('#it_name_'+i)?.value||r.name,active:$('#it_active_'+i)?.checked??r.active,description:$('#it_desc_'+i)?.value||''}));
 let consultants=(SETTINGS.consultants||[]).map((r,i)=>({name:$('#co_name_'+i)?.value||r.name,active:$('#co_active_'+i)?.checked??r.active,target_sales:Number($('#co_sales_'+i)?.value||0),target_profit:Number($('#co_profit_'+i)?.value||0)}));
 await api('/api/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({settings:st,rules,sale_types,income_types,consultants})});alert('Parametreler kaydedildi. Excel/PDF/Dashboard aynı ayarları kullanacak.');await refreshAll()
}
function formFields(o,fields){return `<div class="formgrid">${fields.map(([k,l,t='text',opts])=>{let isMoney=MONEY_KEYS.has(k);let val=isMoney?formatAmount(o[k]):(o[k]??'');return `<div class="field"><label>${l}</label>${opts?`<select id="f_${k}">${opts.map(x=>`<option ${String(o[k]||'')===x?'selected':''}>${x}</option>`).join('')}</select>`:`<input id="f_${k}" type="${isMoney?'text':t}" ${isMoney?'inputmode="decimal" class="money-input"':''} value="${esc(val)}" ${isMoney?'onfocus="this.value=this.value.replace(/\./g,\'\')" onblur="this.value=formatAmount(this.value)"':''}>`}</div>`}).join('')}</div>`}
function showModal(t,h){$('#modalTitle').textContent=t;$('#modalBody').innerHTML=h;$('#modal').classList.add('show')} function closeModal(){$('#modal').classList.remove('show')}
function activePurchaseTypes(){return (SETTINGS.rules||[]).filter(x=>x.active).map(x=>x.name)} function activeSaleTypes(){return (SETTINGS.sale_types||[]).filter(x=>x.active).map(x=>x.name)} function activeConsultants(){return (SETTINGS.consultants||[]).filter(x=>x.active).map(x=>x.name)}
function stockFieldsNow(){return [['plate','Plaka'],['model_year','Model Yılı','number'],['km','KM','number'],['brand','Marka'],['model','Model'],['version','Versiyon'],['color','Renk'],['purchase_date','Alış Tarihi','date'],['fuel','Yakıt','text',['BENZİN','DİZEL','BENZİN/LPG','ELEKTRİK','HİBRİT']],['transmission','Vites','text',['MANUEL','OTOMATİK']],['purchase_type','Alım Türü','text',activePurchaseTypes()],['purchase_price','Alış Fiyatı','number'],['list_price','Satış Fiyatı','number'],['target_profit','Hedef Kazanç','number']]}
const stockFields=stockFieldsNow();
function openStock(id){let r=id?STOCKS.find(x=>x.id===id):{};let fields=stockFieldsNow();showModal(id?'Stok Düzenle':'Yeni Stok',formFields(r,fields)+`<div class="actions"><button class="btn success" onclick="saveStock(${id||0})">Kaydet</button></div>`)}
async function saveStock(id){let o={};stockFieldsNow().forEach(([k,l,t])=>{let v=$('#f_'+k).value;o[k]=t==='number'?(MONEY_KEYS.has(k)?parseMoney(v):Number(v||0)):v});await api(id?'/api/stocks/'+id:'/api/stocks',{method:id?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(o)});closeModal();await refreshAll()}
async function delStock(id){if(confirm('Araç stoktan silinsin mi?')){await api('/api/stocks/'+id,{method:'DELETE'});await refreshAll()}}
function saleFieldsNow(){return [['plate','Plaka'],['vehicle_info','Otomobil Bilgileri'],['model_year','Model Yılı','number'],['purchase_type','Alım Türü','text',activePurchaseTypes()],['purchase_price','Alış Bedeli','number'],['purchase_date','Alış Tarihi','date'],['sale_date','Satış Tarihi','date'],['extra_expense','Ek Masraf','number'],['customer','Müşteri Bilgileri'],['sale_type','Satış Türü','text',activeSaleTypes()],['sale_price','Satış Bedeli','number'],['consultant','Satış Danışmanı','text',activeConsultants()],['insurance_income','Sigorta-Kasko Geliri','number'],['credit_income','Kredi Geliri','number'],['warranty_income','Uzatılmış Garanti Geliri','number']]}
const saleFields=saleFieldsNow();
function openSale(id){let r=id?SALES.find(x=>x.id===id):{sale_date:new Date().toISOString().slice(0,10)};showModal(id?'Satış Düzenle':'Yeni Satış',formFields(r,saleFieldsNow())+`<div class="actions"><button class="btn success" onclick="saveSale(${id||0})">Kaydet</button></div>`)}
async function saveSale(id){let o={};saleFieldsNow().forEach(([k,l,t])=>{let v=$('#f_'+k).value;o[k]=t==='number'?(MONEY_KEYS.has(k)?parseMoney(v):Number(v||0)):v});await api(id?'/api/sales/'+id:'/api/sales',{method:id?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(o)});closeModal();await refreshAll()} async function delSale(id){if(confirm('Satış silinsin mi?')){await api('/api/sales/'+id,{method:'DELETE'});await refreshAll()}}
function openSell(id){let v=STOCKS.find(x=>x.id===id);let r={plate:v.plate,vehicle_info:`${v.brand} ${v.model} ${v.version}`.trim(),model_year:v.model_year,purchase_type:v.purchase_type||'NAKİT',purchase_price:v.purchase_price,purchase_date:v.purchase_date,sale_date:new Date().toISOString().slice(0,10),extra_expense:0,customer:'',sale_type:'NAKİT',sale_price:v.list_price,consultant:'',insurance_income:0,credit_income:0,warranty_income:0};showModal('Stoktaki Aracı Sat',formFields(r,saleFieldsNow())+`<div class="actions"><button class="btn success" onclick="finishSell(${id})">Satışı Tamamla & Stoktan Düş</button></div>`)}
async function finishSell(id){let o={};saleFieldsNow().forEach(([k,l,t])=>{let v=$('#f_'+k).value;o[k]=t==='number'?(MONEY_KEYS.has(k)?parseMoney(v):Number(v||0)):v});await api('/api/stocks/'+id+'/sell',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(o)});closeModal();await refreshAll()}
async function addExpertisePerson(){let name=prompt('Ekspertiz personeli adı:');if(!name)return;await api('/api/expertise/person',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,month:month()})});await refreshAll()}
async function removeExpertisePerson(i){let r=EXPERTISE[i];if(confirm(r.consultant+' çıkarılsın mı?')){await api('/api/expertise/person?name='+encodeURIComponent(r.consultant)+'&month='+encodeURIComponent(r.month||month()),{method:'DELETE'});await refreshAll()}}
async function saveExpertise(){let rows=EXPERTISE.map((r,i)=>({consultant:r.consultant,done_count:Number($('#exd_'+i).value||0),converted_count:Number($('#exc_'+i).value||0)}));await api('/api/expertise',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({month:month(),rows})});alert('Ekspertiz verileri kaydedildi.');await refreshAll()}
async function previewStockImport(){
 let f=$('#stockFile').files[0];if(!f)return alert('Stok Excel dosyası seçin.');safe('#stockImportStatus','⏳ Dosya okunuyor...');
 try{let fd=new FormData();fd.append('file',f);let res=await api('/api/import/stock/preview',{method:'POST',body:fd});stockImport=(res.rows||[]).map(x=>{let pt=canonicalFrom(x.purchase_type,activePurchaseTypes());return {...x,purchase_type:pt,_raw_purchase_type:x.purchase_type||'',_sel:true,_dirty:false,_needsChoice:!pt}});safe('#stockImportStatus',`✓ ${res.file_name}: ${stockImport.length} araç okundu.`);renderStockImport()}catch(e){safe('#stockImportStatus','❌ '+esc(e.message));}
}
function selectStockImport(v){stockImport.forEach(x=>x._sel=v);renderStockImport()}
function importInput(kind,i,key,value,cls=''){
 let isMoney=cls.includes('money'),type=isMoney?'text':kind==='number'?'number':kind==='date'?'date':'text',shown=isMoney?formatAmount(value):value;
 let assign=isMoney?'parseMoney(this.value)':kind==='number'?'Number(this.value||0)':'this.value';
 return `<input class="import-edit ${cls}" type="${type}" ${isMoney?'inputmode="decimal"':''} value="${esc(shown??'')}" onchange="stockImport[${i}]['${key}']=${assign};stockImport[${i}]._dirty=true;${isMoney?'this.value=formatAmount(this.value);':''}renderStockImport()">`;
}
function renderStockImport(){
 let selected=stockImport.filter(x=>x._sel),buy=selected.reduce((a,r)=>a+Number(r.purchase_price||0),0),sell=selected.reduce((a,r)=>a+Number(r.list_price||0),0);
 kpis('#stockImportKpis',[['Okunan',stockImport.length+' Araç','good',''],['Seçili',selected.length+' Araç','',''],['Seçili Alış',money(buy),'',''],['Seçili Satış',money(sell),'','']]);
 let rows=stockImport.map((r,i)=>`<tr><td><input type="checkbox" ${r._sel?'checked':''} onchange="stockImport[${i}]._sel=this.checked;renderStockImport()"></td>
 <td>${importInput('text',i,'plate',r.plate)}</td><td>${importInput('number',i,'model_year',r.model_year)}</td><td>${importInput('number',i,'km',r.km)}</td>
 <td>${importInput('text',i,'brand',r.brand)}</td><td>${importInput('text',i,'model',r.model)}</td><td>${importInput('text',i,'version',r.version,'wide')}</td><td>${importInput('text',i,'color',r.color)}</td>
 <td>${importInput('date',i,'purchase_date',r.purchase_date,'date')}</td><td>${importInput('text',i,'fuel',r.fuel)}</td><td>${importInput('text',i,'transmission',r.transmission)}</td><td>${requiredSelect(activePurchaseTypes(),r.purchase_type,`stockImport[${i}].purchase_type=this.value;stockImport[${i}]._dirty=true;stockImport[${i}]._needsChoice=!this.value;renderStockImport()`,'Alım Türü')} ${!r.purchase_type&&r._raw_purchase_type?`<small class="raw-read">Okunan: ${esc(r._raw_purchase_type)}</small>`:''}</td>
 <td>${importInput('number',i,'purchase_price',r.purchase_price,'money')}</td><td>${importInput('number',i,'list_price',r.list_price,'money')}</td><td class="sticky-action"><button class="btn ${r._dirty?'success':'ghost'} small" onclick="applyOneStockImport(${i})">${r._dirty?'Düzenleneni Aktar':'Tek Aktar'}</button></td></tr>`);
 safe('#stockImportTable',table(['Seç','Plaka','Yıl','KM','Marka','Model','Versiyon','Renk','Alış Tarihi','Yakıt','Vites','Alım Türü','Alış Fiyatı','Satış Fiyatı','Aktar'],rows));
}

function cleanStockImportRow(r){let x={...r};Object.keys(x).filter(k=>k.startsWith('_')).forEach(k=>delete x[k]);return x}
function cleanSalesImportRow(r){let x={...r};Object.keys(x).filter(k=>k.startsWith('_')).forEach(k=>delete x[k]);return x}
async function applyStockImport(mode='merge'){
 let rows=stockImport.filter(x=>x._sel).map(cleanStockImportRow);if(!rows.length)return alert('Araç seçin.');if(!validateStockRows(rows))return;
 if(mode==='replace'&&!confirm('Mevcut GÜNCEL STOK kayıtları silinecek ve sadece seçili araçlar stokta kalacak. Devam edilsin mi?'))return;
 try{let r=await api('/api/import/stock/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({rows,mode})});alert(`${r.count} araç aktarıldı.${mode==='replace'?' Eski güncel stok temizlendi.':''}`);stockImport=[];renderStockImport();await refreshAll();}catch(e){safe('#stockImportStatus','❌ '+esc(e.message));}
}
async function applyOneStockImport(i){
 let r=stockImport[i]; if(!r)return; let row=cleanStockImportRow(r);if(!validateStockRows([row]))return;
 try{let x=await api('/api/import/stock/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({rows:[row],mode:'merge'})});r._dirty=false;r._sel=false;safe('#stockImportStatus',`✓ ${r.plate||''} tek kayıt olarak aktarıldı.`);renderStockImport();await refreshAll()}catch(e){safe('#stockImportStatus','❌ '+esc(e.message))}
}
async function applyDirtyStockImport(){
 let rows=stockImport.filter(x=>x._dirty).map(cleanStockImportRow);if(!rows.length)return alert('Henüz düzenlenmiş kayıt yok.');if(!validateStockRows(rows))return;
 try{let r=await api('/api/import/stock/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({rows,mode:'merge'})});stockImport.forEach(x=>{if(x._dirty){x._dirty=false;x._sel=false}});safe('#stockImportStatus',`✓ Düzenlenen ${r.count} araç aktarıldı.`);renderStockImport();await refreshAll()}catch(e){safe('#stockImportStatus','❌ '+esc(e.message))}
}
async function previewSalesImport(){
 let f=$('#salesFile').files[0],m=$('#salesImportMonth').value||month();if(!f)return alert('Satış Excel dosyası seçin.');if(!m)return alert('Aktarılacak ayı seçin.');safe('#salesImportStatus','⏳ Satış Excel okunuyor...');
 try{let fd=new FormData();fd.append('month',m);fd.append('file',f);let res=await api('/api/import/sales/preview',{method:'POST',body:fd});salesImport=(res.rows||[]).map(x=>{let pt=canonicalFrom(x.purchase_type,activePurchaseTypes()),st=canonicalFrom(x.sale_type,activeSaleTypes()),co=canonicalFrom(x.consultant,activeConsultants());return {...x,purchase_type:pt,sale_type:st,consultant:co,_raw_purchase_type:x.purchase_type||'',_raw_sale_type:x.sale_type||'',_raw_consultant:x.consultant||'',_sel:true,_dirty:false,_needsChoice:(!pt||!st||!co)}});safe('#salesImportStatus',`✓ ${res.file_name}: ${salesImport.length} satış okundu (${m}).`);renderSalesImport()}catch(e){safe('#salesImportStatus','❌ '+esc(e.message));salesImport=[];renderSalesImport()}
}
function selectSalesImport(v){salesImport.forEach(x=>x._sel=v);renderSalesImport()}
function salesImportInput(kind,i,key,value,cls=''){
 let isMoney=cls.includes('money'),type=isMoney?'text':kind==='number'?'number':kind==='date'?'date':'text',shown=isMoney?formatAmount(value):value;
 let assign=isMoney?'parseMoney(this.value)':kind==='number'?'Number(this.value||0)':'this.value';
 return `<input class="import-edit ${cls}" type="${type}" ${isMoney?'inputmode="decimal"':''} value="${esc(shown??'')}" onchange="salesImport[${i}]['${key}']=${assign};salesImport[${i}]._dirty=true;${isMoney?'this.value=formatAmount(this.value);':''}renderSalesImport()">`;
}
function renderSalesImport(){
 let selected=salesImport.filter(x=>x._sel),buy=selected.reduce((a,r)=>a+Number(r.purchase_price||0),0),sell=selected.reduce((a,r)=>a+Number(r.sale_price||0),0);
 kpis('#salesImportKpis',[['Okunan',salesImport.length+' Satış','good',''],['Seçili',selected.length+' Satış','',''],['Seçili Alış',money(buy),'',''],['Seçili Satış',money(sell),'','']]);
 let rows=salesImport.map((r,i)=>`<tr><td><input type="checkbox" ${r._sel?'checked':''} onchange="salesImport[${i}]._sel=this.checked;renderSalesImport()"></td>
 <td>${salesImportInput('date',i,'sale_date',r.sale_date,'date')}</td><td>${salesImportInput('text',i,'plate',r.plate)}</td><td>${salesImportInput('text',i,'vehicle_info',r.vehicle_info,'wide')}</td><td>${salesImportInput('number',i,'model_year',r.model_year)}</td>
 <td>${requiredSelect(activePurchaseTypes(),r.purchase_type,`salesImport[${i}].purchase_type=this.value;salesImport[${i}]._dirty=true;renderSalesImport()`,'Alım Türü')} ${!r.purchase_type&&r._raw_purchase_type?`<small class="raw-read">Okunan: ${esc(r._raw_purchase_type)}</small>`:''}</td><td>${salesImportInput('number',i,'purchase_price',r.purchase_price,'money')}</td><td>${salesImportInput('date',i,'purchase_date',r.purchase_date,'date')}</td>
 <td>${salesImportInput('number',i,'extra_expense',r.extra_expense,'money')}</td><td>${salesImportInput('text',i,'customer',r.customer,'wide')}</td><td>${requiredSelect(activeSaleTypes(),r.sale_type,`salesImport[${i}].sale_type=this.value;salesImport[${i}]._dirty=true;renderSalesImport()`,'Satış Türü')} ${!r.sale_type&&r._raw_sale_type?`<small class="raw-read">Okunan: ${esc(r._raw_sale_type)}</small>`:''}</td><td>${salesImportInput('number',i,'sale_price',r.sale_price,'money')}</td><td>${requiredSelect(activeConsultants(),r.consultant,`salesImport[${i}].consultant=this.value;salesImport[${i}]._dirty=true;renderSalesImport()`,'Danışman')} ${!r.consultant&&r._raw_consultant?`<small class="raw-read">Okunan: ${esc(r._raw_consultant)}</small>`:''}</td><td class="sticky-action"><button class="btn ${r._dirty?'success':'ghost'} small" onclick="applyOneSalesImport(${i})">${r._dirty?'Düzenleneni Aktar':'Tek Aktar'}</button></td></tr>`);
 safe('#salesImportTable',table(['Seç','Satış Tarihi','Plaka','Araç','Yıl','Alım Türü','Alış Bedeli','Alış Tarihi','Ek Masraf','Müşteri','Satış Türü','Satış Bedeli','Danışman','Aktar'],rows));
}
async function applyOneSalesImport(i){
 let r=salesImport[i],m=$('#salesImportMonth').value||month();if(!r)return;let row=cleanSalesImportRow(r);if(!validateSalesRows([row]))return;
 try{let x=await api('/api/import/sales/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({rows:[row],mode:'merge',month:m})});r._dirty=false;r._sel=false;safe('#salesImportStatus',`✓ ${r.plate||''} tek satış olarak aktarıldı.`);renderSalesImport();await refreshAll()}catch(e){safe('#salesImportStatus','❌ '+esc(e.message))}
}
async function applyDirtySalesImport(){
 let m=$('#salesImportMonth').value||month(),rows=salesImport.filter(x=>x._dirty).map(cleanSalesImportRow);if(!rows.length)return alert('Henüz düzenlenmiş satış kaydı yok.');if(!validateSalesRows(rows))return;
 try{let r=await api('/api/import/sales/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({rows,mode:'merge',month:m})});salesImport.forEach(x=>{if(x._dirty){x._dirty=false;x._sel=false}});safe('#salesImportStatus',`✓ Düzenlenen ${r.count} satış aktarıldı.`);renderSalesImport();await refreshAll()}catch(e){safe('#salesImportStatus','❌ '+esc(e.message))}
}
async function applySalesImport(mode='merge'){
 let rows=salesImport.filter(x=>x._sel).map(cleanSalesImportRow),m=$('#salesImportMonth').value;if(!rows.length)return alert('Satış seçin.');if(!validateSalesRows(rows))return;
 if(mode==='replace_month'&&!confirm(`${m} ayındaki mevcut satış kayıtları silinecek ve sadece seçili satışlar kalacak. Devam edilsin mi?`))return;
 try{let r=await api('/api/import/sales/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({rows,mode,month:m})});alert(`${r.count} satış aktarıldı.${mode==='replace_month'?' Seçili ay yeniden oluşturuldu.':''}`);salesImport=[];renderSalesImport();await refreshAll();}catch(e){safe('#salesImportStatus','❌ '+esc(e.message));}
}
async function previewMaster(){let f=$('#masterFile').files[0];if(!f)return alert('Ana Excel seçin.');safe('#masterStatus','⏳ Excel analiz ediliyor...');let fd=new FormData();fd.append('file',f);try{MASTER=await api('/api/master/preview',{method:'POST',body:fd});$('#masterReplace').disabled=false;$('#masterMerge').disabled=false;let s=MASTER.summary;safe('#masterStatus',`✓ ${s.sales_count} satış, ${s.stock_count} stok, ${s.consultant_count} danışman ve ${s.expertise_people} ekspertiz personeli bulundu.`);kpis('#masterSummary',[['Satış',s.sales_count+' Adet','good',''],['Stok',s.stock_count+' Adet','good',''],['Danışman',s.consultant_count+' Kişi','',''],['Ekspertiz',s.expertise_people+' Kişi','',''],['Ciro',money(s.sales_revenue),'',''],['Stok Alış',money(s.stock_purchase_total),'','']]);safe('#masterSamples',`<div class="grid2"><div class="card"><h3>Satış Önizleme</h3>${table(['Plaka','Araç','Tarih','Satış'],(MASTER.sample_sales||[]).map(x=>`<tr><td>${esc(x.plate)}</td><td>${esc(x.vehicle_info)}</td><td>${x.sale_date}</td><td>${money(x.sale_price)}</td></tr>`))}</div><div class="card"><h3>Stok Önizleme</h3>${table(['Plaka','Araç','Alış','Satış'],(MASTER.sample_stocks||[]).map(x=>`<tr><td>${esc(x.plate)}</td><td>${esc(x.brand+' '+x.model+' '+x.version)}</td><td>${money(x.purchase_price)}</td><td>${money(x.list_price)}</td></tr>`))}</div></div>`)}catch(e){safe('#masterStatus','❌ '+esc(e.message))}}
async function applyMaster(mode){if(!MASTER)return; if(!confirm(mode==='replace'?'Mevcut veritabanı yedeklenip Excel ile tamamen yenilensin mi?':'Excel mevcut veriye birleştirilsin mi?'))return;let r=await api('/api/master/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:MASTER.token,file_name:MASTER.file_name,mode})});alert('Ana Excel aktarıldı.');MASTER=null;$('#masterReplace').disabled=true;$('#masterMerge').disabled=true;await refreshAll();await loadImportHistory()}
async function loadImportHistory(){try{let a=await api('/api/import-history');safe('#importHistory',table(['Tarih','Dosya','Mod','Satış','Stok','Ekspertiz','Danışman'],a.map(r=>`<tr><td>${r.created_at}</td><td>${esc(r.file_name)}</td><td>${r.mode}</td><td>${r.sales_count}</td><td>${r.stock_count}</td><td>${r.expertise_count}</td><td>${r.consultant_count}</td></tr>`)))}catch(e){}}
function updateReportLinks(){let m=$('#reportMonth').value||month();$('#reportMonth').value=m;$('#rManagement').href='/api/report/management?month='+m;$('#rSales').href='/api/report/sales?month='+m;$('#rPurchase').href='/api/report/purchases?month='+m;$('#rConsultant').href='/api/report/consultants?month='+m;$('#rExpertise').href='/api/report/expertise?month='+m;$('#rProfit').href='/api/report/profit-loss?month='+m;$('#rExcel').href='javascript:void(0)';$('#rExcel').onclick=downloadExcel;$('#excelDownload').href='javascript:void(0)';$('#excelDownload').onclick=downloadExcel}
async function backup(){let r=await api('/api/backup',{method:'POST'});alert(r.ok?'Yedek alındı: '+r.file:'Yedek alınamadı')} async function loadAudit(){let a=await api('/api/audit');safe('#auditTable',table(['Tarih','Alan','ID','İşlem','Detay'],a.map(r=>`<tr><td>${r.created_at}</td><td>${r.entity}</td><td>${r.entity_id||''}</td><td>${r.action}</td><td>${esc(r.details)}</td></tr>`)))}
function clearBrowserCache(){localStorage.removeItem('renew_v6_page');sessionStorage.clear();alert('Arayüz hafızası temizlendi. Veritabanındaki araç/satış kayıtları silinmedi. Sayfa yenilenecek.');location.reload(true)}
window.addEventListener('DOMContentLoaded',()=>{let m=new Date().toISOString().slice(0,7);$('#globalMonth').value=m;$('#salesImportMonth').value=m;$('#reportMonth').value=m;$('#globalMonth').onchange=refreshAll;$('#reportMonth').onchange=updateReportLinks;page(localStorage.getItem('renew_v6_page')||'dashboard')});

async function downloadExcel(){
 try{
  let m=month(),r=await fetch('/api/export/excel?month='+encodeURIComponent(m),{cache:'no-store'});
  if(!r.ok)throw new Error(await r.text());
  let b=await r.blob(),u=URL.createObjectURL(b),a=document.createElement('a');a.href=u;a.download=`RENEW_GUNCEL_${m}.xlsx`;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),2000);
 }catch(e){alert('Excel indirilemedi: '+e.message)}
}

/* ================= V7.5 REQUIRED SELECTION FIX ================= */
function normText(s){
 return String(s??'').trim().toLocaleUpperCase('tr-TR')
   .normalize('NFD').replace(/[\u0300-\u036f]/g,'')
   .replace(/İ/g,'I').replace(/Ş/g,'S').replace(/Ğ/g,'G').replace(/Ü/g,'U').replace(/Ö/g,'O').replace(/Ç/g,'C')
   .replace(/\s+/g,' ');
}
function getActiveRules(){ return (SETTINGS.rules||[]).filter(x=>Number(x.active)!==0); }
function getActiveConsultants(){ return (SETTINGS.consultants||[]).filter(x=>Number(x.active)!==0); }
function getActiveSaleTypes(){ return (SETTINGS.sale_types||[]).filter(x=>Number(x.active)!==0); }

function matchByNorm(raw, list, key='name'){
 const n=normText(raw);
 if(!n) return '';
 const found=list.find(x=>normText(x[key])===n);
 return found?found[key]:'';
}

function purchaseTypeSelectHtml(raw, idx, target){
 const opts=getActiveRules();
 const matched=matchByNorm(raw,opts,'name');
 const cls=matched?'':' required-select';
 const current=matched||'';
 const unknown=raw && !matched ? `<small class="unmatched-note">Excel: ${esc(raw)}</small>`:'';
 return `<select class="${cls}" onchange="${target}[${idx}].purchase_type=this.value;${target}[${idx}]._dirty=true;this.classList.toggle('required-select',!this.value)">
   <option value="">— ALIM TÜRÜ SEÇ —</option>
   ${opts.map(x=>`<option value="${esc(x.name)}" ${current===x.name?'selected':''}>${esc(x.name)}</option>`).join('')}
 </select>${unknown}`;
}
function consultantSelectHtml(raw, idx){
 const opts=getActiveConsultants();
 const matched=matchByNorm(raw,opts,'name');
 const current=matched||'';
 const unknown=raw && !matched ? `<small class="unmatched-note">Excel: ${esc(raw)}</small>`:'';
 return `<select class="${matched?'':' required-select'}" onchange="salesImport[${idx}].consultant=this.value;salesImport[${idx}]._dirty=true;this.classList.toggle('required-select',!this.value)">
  <option value="">— DANIŞMAN SEÇ —</option>
  ${opts.map(x=>`<option value="${esc(x.name)}" ${current===x.name?'selected':''}>${esc(x.name)}</option>`).join('')}
 </select>${unknown}`;
}
function saleTypeSelectHtml(raw, idx){
 const opts=getActiveSaleTypes();
 const matched=matchByNorm(raw,opts,'name');
 const current=matched||'';
 const unknown=raw && !matched ? `<small class="unmatched-note">Excel: ${esc(raw)}</small>`:'';
 return `<select class="${matched?'':' required-select'}" onchange="salesImport[${idx}].sale_type=this.value;salesImport[${idx}]._dirty=true;this.classList.toggle('required-select',!this.value)">
  <option value="">— SATIŞ TÜRÜ SEÇ —</option>
  ${opts.map(x=>`<option value="${esc(x.name)}" ${current===x.name?'selected':''}>${esc(x.name)}</option>`).join('')}
 </select>${unknown}`;
}

function normalizeStockImportRows(rows){
 return (rows||[]).map(r=>{
   const matched=matchByNorm(r.purchase_type,getActiveRules(),'name');
   return {...r,purchase_type:matched,_original_purchase_type:r.purchase_type||'',_sel:true,_dirty:false};
 });
}
function normalizeSalesImportRows(rows){
 return (rows||[]).map(r=>{
   const p=matchByNorm(r.purchase_type,getActiveRules(),'name');
   const c=matchByNorm(r.consultant,getActiveConsultants(),'name');
   const s=matchByNorm(r.sale_type,getActiveSaleTypes(),'name');
   return {...r,purchase_type:p,consultant:c,sale_type:s,
     _original_purchase_type:r.purchase_type||'',_original_consultant:r.consultant||'',_original_sale_type:r.sale_type||'',
     _sel:true,_dirty:false};
 });
}
function validateStockRows(rows){
 const bad=rows.filter(r=>!String(r.purchase_type||'').trim());
 if(bad.length){
   alert(`Aktarım durduruldu.\n${bad.length} araçta Alım Türü seçilmemiş.\nKırmızı alanlardan Alım Türü seçmeden aktarım yapılamaz.`);
   return false;
 }
 return true;
}
function validateSalesRows(rows){
 const badP=rows.filter(r=>!String(r.purchase_type||'').trim());
 const badS=rows.filter(r=>!String(r.sale_type||'').trim());
 const badC=rows.filter(r=>!String(r.consultant||'').trim());
 if(badP.length||badS.length||badC.length){
   alert(`Aktarım durduruldu.\nAlım Türü eksik: ${badP.length}\nSatış Türü eksik: ${badS.length}\nDanışman eksik: ${badC.length}\n\nKırmızı seçim alanlarını doldurmadan aktarım yapılamaz.`);
   return false;
 }
 return true;
}

/* Override preview functions to normalize required fields immediately */
const _v74_previewStockImport = previewStockImport;
previewStockImport = async function(){
 let f=$('#stockFile').files[0];if(!f)return alert('Stok Excel dosyası seçin.');
 safe('#stockImportStatus','⏳ Dosya okunuyor...');
 try{
   let fd=new FormData();fd.append('file',f);
   let res=await api('/api/import/stock/preview',{method:'POST',body:fd});
   stockImport=normalizeStockImportRows(res.rows||[]);
   safe('#stockImportStatus',`✓ ${res.file_name}: ${stockImport.length} araç okundu. Alım Türü eşleşmeyen kayıtlar kırmızı ve zorunludur.`);
   renderStockImport();
 }catch(e){safe('#stockImportStatus','❌ '+esc(e.message));}
}

const _v74_previewSalesImport = previewSalesImport;
previewSalesImport = async function(){
 let f=$('#salesFile').files[0],m=$('#salesImportMonth').value;
 if(!f||!m)return alert('Ay ve satış dosyası seçin.');
 safe('#salesImportStatus','⏳ Dosya okunuyor...');
 try{
   let fd=new FormData();fd.append('month',m);fd.append('file',f);
   let res=await api('/api/import/sales/preview',{method:'POST',body:fd});
   salesImport=normalizeSalesImportRows(res.rows||[]);
   safe('#salesImportStatus',`✓ ${res.file_name}: ${m} için ${salesImport.length} satış okundu. Alım Türü / Satış Türü / Danışman eşleşmeyen kayıtlar zorunlu seçimdir.`);
   renderSalesImport();
 }catch(e){safe('#salesImportStatus','❌ '+esc(e.message));}
}

/* Override import tables with required dropdowns */
renderStockImport = function(){
 kpis('#stockImportKpis',[
   ['Okunan',stockImport.length+' Araç','good',''],
   ['Seçili',stockImport.filter(x=>x._sel).length+' Araç','',''],
   ['Alım Türü Eksik',stockImport.filter(x=>!x.purchase_type).length+' Araç',stockImport.some(x=>!x.purchase_type)?'bad':'good','Zorunlu'],
   ['Toplam Alış',money(stockImport.reduce((a,r)=>a+Number(r.purchase_price||0),0)),'',''],
   ['Toplam Satış',money(stockImport.reduce((a,r)=>a+Number(r.list_price||0),0)),'','']
 ]);
 safe('#stockImportTable',table(
  ['Seç','Plaka','Yıl','KM','Marka','Model','Versiyon','Renk','Alış Tarihi','Yakıt','Vites','Alım Türü','Alış Fiyatı','Satış Fiyatı','İşlem'],
  stockImport.map((r,i)=>`<tr class="${!r.purchase_type?'lossrow':''}">
    <td><input type="checkbox" ${r._sel?'checked':''} onchange="stockImport[${i}]._sel=this.checked"></td>
    <td><input value="${esc(r.plate)}" onchange="stockImport[${i}].plate=this.value;stockImport[${i}]._dirty=true"></td>
    <td><input value="${r.model_year||''}" onchange="stockImport[${i}].model_year=Number(this.value||0);stockImport[${i}]._dirty=true"></td>
    <td><input value="${r.km||0}" onchange="stockImport[${i}].km=Number(this.value||0);stockImport[${i}]._dirty=true"></td>
    <td><input value="${esc(r.brand)}" onchange="stockImport[${i}].brand=this.value;stockImport[${i}]._dirty=true"></td>
    <td><input value="${esc(r.model)}" onchange="stockImport[${i}].model=this.value;stockImport[${i}]._dirty=true"></td>
    <td><input value="${esc(r.version)}" onchange="stockImport[${i}].version=this.value;stockImport[${i}]._dirty=true"></td>
    <td><input value="${esc(r.color)}" onchange="stockImport[${i}].color=this.value;stockImport[${i}]._dirty=true"></td>
    <td><input type="date" value="${r.purchase_date||''}" onchange="stockImport[${i}].purchase_date=this.value;stockImport[${i}]._dirty=true"></td>
    <td><input value="${esc(r.fuel)}" onchange="stockImport[${i}].fuel=this.value;stockImport[${i}]._dirty=true"></td>
    <td><input value="${esc(r.transmission)}" onchange="stockImport[${i}].transmission=this.value;stockImport[${i}]._dirty=true"></td>
    <td>${purchaseTypeSelectHtml(r._original_purchase_type||r.purchase_type,i,'stockImport')}</td>
    <td><input value="${Number(r.purchase_price||0).toLocaleString('tr-TR')}" onchange="stockImport[${i}].purchase_price=parseMoneyInput(this.value);this.value=stockImport[${i}].purchase_price.toLocaleString('tr-TR');stockImport[${i}]._dirty=true"></td>
    <td><input value="${Number(r.list_price||0).toLocaleString('tr-TR')}" onchange="stockImport[${i}].list_price=parseMoneyInput(this.value);this.value=stockImport[${i}].list_price.toLocaleString('tr-TR');stockImport[${i}]._dirty=true"></td>
    <td><button class="btn success small" onclick="importOneStock(${i})">Tek Aktar</button></td>
  </tr>`)
 ));
}

renderSalesImport = function(){
 kpis('#salesImportKpis',[
   ['Okunan',salesImport.length+' Satış','good',''],
   ['Seçili',salesImport.filter(x=>x._sel).length+' Satış','',''],
   ['Alım Türü Eksik',salesImport.filter(x=>!x.purchase_type).length+'','','Zorunlu'],
   ['Satış Türü Eksik',salesImport.filter(x=>!x.sale_type).length+'','','Zorunlu'],
   ['Danışman Eksik',salesImport.filter(x=>!x.consultant).length+'','','Zorunlu']
 ]);
 safe('#salesImportTable',table(
 ['Seç','Satış Tarihi','Plaka','Araç','Yıl','Alım Türü','Alış Bedeli','Alış Tarihi','Müşteri','Satış Türü','Satış Bedeli','Danışman','İşlem'],
 salesImport.map((r,i)=>`<tr class="${(!r.purchase_type||!r.sale_type||!r.consultant)?'lossrow':''}">
  <td><input type="checkbox" ${r._sel?'checked':''} onchange="salesImport[${i}]._sel=this.checked"></td>
  <td><input type="date" value="${r.sale_date||''}" onchange="salesImport[${i}].sale_date=this.value;salesImport[${i}]._dirty=true"></td>
  <td><input value="${esc(r.plate)}" onchange="salesImport[${i}].plate=this.value;salesImport[${i}]._dirty=true"></td>
  <td><input value="${esc(r.vehicle_info)}" onchange="salesImport[${i}].vehicle_info=this.value;salesImport[${i}]._dirty=true"></td>
  <td><input value="${r.model_year||''}" onchange="salesImport[${i}].model_year=Number(this.value||0);salesImport[${i}]._dirty=true"></td>
  <td>${purchaseTypeSelectHtml(r._original_purchase_type||r.purchase_type,i,'salesImport')}</td>
  <td><input value="${Number(r.purchase_price||0).toLocaleString('tr-TR')}" onchange="salesImport[${i}].purchase_price=parseMoneyInput(this.value);this.value=salesImport[${i}].purchase_price.toLocaleString('tr-TR');salesImport[${i}]._dirty=true"></td>
  <td><input type="date" value="${r.purchase_date||''}" onchange="salesImport[${i}].purchase_date=this.value;salesImport[${i}]._dirty=true"></td>
  <td><input value="${esc(r.customer||'')}" onchange="salesImport[${i}].customer=this.value;salesImport[${i}]._dirty=true"></td>
  <td>${saleTypeSelectHtml(r._original_sale_type||r.sale_type,i)}</td>
  <td><input value="${Number(r.sale_price||0).toLocaleString('tr-TR')}" onchange="salesImport[${i}].sale_price=parseMoneyInput(this.value);this.value=salesImport[${i}].sale_price.toLocaleString('tr-TR');salesImport[${i}]._dirty=true"></td>
  <td>${consultantSelectHtml(r._original_consultant||r.consultant,i)}</td>
  <td><button class="btn success small" onclick="importOneSale(${i})">Tek Aktar</button></td>
 </tr>`)
 ));
}

/* hard validation before every import path */
async function importOneStock(i){
 const r=stockImport[i];
 if(!validateStockRows([r]))return;
 const {_sel,_dirty,_original_purchase_type,...row}=r;
 await api('/api/import/stock/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify([row])});
 alert('1 araç aktarıldı.');stockImport.splice(i,1);renderStockImport();await refreshAll();
}
async function importOneSale(i){
 const r=salesImport[i];
 if(!validateSalesRows([r]))return;
 const {_sel,_dirty,_original_purchase_type,_original_consultant,_original_sale_type,...row}=r;
 await api('/api/import/sales/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify([row])});
 alert('1 satış aktarıldı.');salesImport.splice(i,1);renderSalesImport();await refreshAll();
}

applyStockImport = async function(){
 let rows=stockImport.filter(x=>x._sel);
 if(!rows.length)return alert('Araç seçin.');
 if(!validateStockRows(rows))return;
 rows=rows.map(({_sel,_dirty,_original_purchase_type,...x})=>x);
 let r=await api('/api/import/stock/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(rows)});
 alert(r.count+' araç stoğa aktarıldı.');stockImport=[];renderStockImport();await refreshAll();
}
applySalesImport = async function(){
 let rows=salesImport.filter(x=>x._sel);
 if(!rows.length)return alert('Satış seçin.');
 if(!validateSalesRows(rows))return;
 rows=rows.map(({_sel,_dirty,_original_purchase_type,_original_consultant,_original_sale_type,...x})=>x);
 let r=await api('/api/import/sales/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(rows)});
 alert(r.count+' satış aktarıldı.');salesImport=[];renderSalesImport();await refreshAll();
}

/* If V7.4 has edited-only/bulk-replace helpers, validate them too by overriding common names when present */
if(typeof applyEditedStockImport==='function'){
 const _old=applyEditedStockImport;
 applyEditedStockImport=async function(){
   let rows=stockImport.filter(x=>x._dirty);
   if(!rows.length)return alert('Düzenlenmiş stok kaydı yok.');
   if(!validateStockRows(rows))return;
   return _old();
 }
}
if(typeof applyEditedSalesImport==='function'){
 const _old=applyEditedSalesImport;
 applyEditedSalesImport=async function(){
   let rows=salesImport.filter(x=>x._dirty);
   if(!rows.length)return alert('Düzenlenmiş satış kaydı yok.');
   if(!validateSalesRows(rows))return;
   return _old();
 }
}
if(typeof replaceStockImport==='function'){
 const _old=replaceStockImport;
 replaceStockImport=async function(){let rows=stockImport.filter(x=>x._sel);if(!validateStockRows(rows))return;return _old();}
}
if(typeof replaceSalesImport==='function'){
 const _old=replaceSalesImport;
 replaceSalesImport=async function(){let rows=salesImport.filter(x=>x._sel);if(!validateSalesRows(rows))return;return _old();}
}
/* ================= /V7.5 REQUIRED SELECTION FIX ================= */

/* ================= V7.6 IMPORT CHAIN FIX ================= */
async function apiV76(url,opt={}){
 const r=await fetch(url,{cache:'no-store',...opt});
 const ct=r.headers.get('content-type')||'';
 if(!r.ok){
   let msg='';
   try{
     if(ct.includes('json')){
       const j=await r.json();
       if(typeof j.detail==='string') msg=j.detail;
       else if(j.detail?.message){
         msg=j.detail.message;
         if(Array.isArray(j.detail.errors) && j.detail.errors.length){
           msg += '\n' + j.detail.errors.map(x=>`Satır ${x.row} ${x.plate||''}: ${typeof x.error==='string'?x.error:JSON.stringify(x.error)}`).join('\n');
         }
       } else msg=JSON.stringify(j.detail||j);
     }else msg=await r.text();
   }catch(e){msg=`HTTP ${r.status}`}
   throw new Error(msg||`HTTP ${r.status}`);
 }
 return ct.includes('json')?r.json():r;
}
api = apiV76;

function cleanImportRow(r){
 const o={};
 for(const [k,v] of Object.entries(r||{})){
   if(String(k).startsWith('_')) continue;
   o[k]=v;
 }
 return o;
}
function sanitizeStockRow(r){
 const o=cleanImportRow(r);
 o.plate=String(o.plate||'').trim();
 o.model_year=o.model_year?Number(o.model_year):null;
 o.km=Number(String(o.km??0).replace(/[^\d-]/g,''))||0;
 o.purchase_price=Number(o.purchase_price)||0;
 o.list_price=Number(o.list_price)||0;
 o.target_profit=Number(o.target_profit)||0;
 o.purchase_type=String(o.purchase_type||'').trim();
 o.purchase_date=String(o.purchase_date||'').slice(0,10);
 return o;
}
function sanitizeSaleRow(r){
 const o=cleanImportRow(r);
 o.plate=String(o.plate||'').trim();
 o.model_year=o.model_year?Number(o.model_year):null;
 o.purchase_price=Number(o.purchase_price)||0;
 o.sale_price=Number(o.sale_price)||0;
 o.extra_expense=Number(o.extra_expense)||0;
 o.insurance_income=Number(o.insurance_income)||0;
 o.credit_income=Number(o.credit_income)||0;
 o.warranty_income=Number(o.warranty_income)||0;
 o.purchase_type=String(o.purchase_type||'').trim();
 o.sale_type=String(o.sale_type||'').trim();
 o.consultant=String(o.consultant||'').trim();
 o.purchase_date=String(o.purchase_date||'').slice(0,10);
 o.sale_date=String(o.sale_date||'').slice(0,10);
 return o;
}

async function postStockRows(rows,successText){
 const clean=rows.map(sanitizeStockRow);
 if(!validateStockRows(clean)) return false;
 try{
   safe('#stockImportStatus','⏳ Aktarım yapılıyor...');
   const r=await api('/api/import/stock/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({rows:clean})});
   safe('#stockImportStatus',`✓ ${r.count} araç başarıyla aktarıldı.`);
   alert(successText||`${r.count} araç aktarıldı.`);
   await refreshAll();
   return true;
 }catch(e){
   safe('#stockImportStatus','❌ '+esc(e.message));
   alert('Stok aktarımı başarısız:\n'+e.message);
   return false;
 }
}
async function postSaleRows(rows,successText){
 const clean=rows.map(sanitizeSaleRow);
 if(!validateSalesRows(clean)) return false;
 try{
   safe('#salesImportStatus','⏳ Aktarım yapılıyor...');
   const r=await api('/api/import/sales/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({rows:clean})});
   safe('#salesImportStatus',`✓ ${r.count} satış başarıyla aktarıldı.`);
   alert(successText||`${r.count} satış aktarıldı.`);
   await refreshAll();
   return true;
 }catch(e){
   safe('#salesImportStatus','❌ '+esc(e.message));
   alert('Satış aktarımı başarısız:\n'+e.message);
   return false;
 }
}

importOneStock = async function(i){
 const r=stockImport[i];
 if(await postStockRows([r],'1 araç aktarıldı.')){
   stockImport.splice(i,1); renderStockImport();
 }
}
importOneSale = async function(i){
 const r=salesImport[i];
 if(await postSaleRows([r],'1 satış aktarıldı.')){
   salesImport.splice(i,1); renderSalesImport();
 }
}
applyStockImport = async function(){
 const rows=stockImport.filter(x=>x._sel);
 if(!rows.length) return alert('Aktarılacak araç seçin.');
 if(await postStockRows(rows)){
   const keys=new Set(rows.map(x=>x));
   stockImport=stockImport.filter(x=>!keys.has(x));
   renderStockImport();
 }
}
applySalesImport = async function(){
 const rows=salesImport.filter(x=>x._sel);
 if(!rows.length) return alert('Aktarılacak satış seçin.');
 if(await postSaleRows(rows)){
   const keys=new Set(rows.map(x=>x));
   salesImport=salesImport.filter(x=>!keys.has(x));
   renderSalesImport();
 }
}

/* Düzenlenenleri aktar butonları varsa bunları da aynı güvenli zincire bağla */
if(typeof applyEditedStockImport==='function'){
 applyEditedStockImport=async function(){
   const rows=stockImport.filter(x=>x._dirty);
   if(!rows.length)return alert('Düzenlenmiş stok kaydı yok.');
   if(await postStockRows(rows,'Düzenlenen stok kayıtları aktarıldı.')){
     rows.forEach(x=>x._dirty=false);renderStockImport();
   }
 }
}
if(typeof applyEditedSalesImport==='function'){
 applyEditedSalesImport=async function(){
   const rows=salesImport.filter(x=>x._dirty);
   if(!rows.length)return alert('Düzenlenmiş satış kaydı yok.');
   if(await postSaleRows(rows,'Düzenlenen satış kayıtları aktarıldı.')){
     rows.forEach(x=>x._dirty=false);renderSalesImport();
   }
 }
}
/* ================= /V7.6 IMPORT CHAIN FIX ================= */

/* =====================================================================
   V7.7 FINAL IMPORT CONTROLLER
   Bu blok dosyanın EN SONUNDA bulunur ve HTML butonlarının tamamını
   tek, güvenli aktarım akışına bağlar.
   ===================================================================== */
function v77ErrText(e){ return (e && e.message) ? e.message : String(e||'Bilinmeyen hata'); }

async function v77FetchJson(url,opt={}){
  const r=await fetch(url,{cache:'no-store',...opt});
  const ct=r.headers.get('content-type')||'';
  let body=null;
  try{ body=ct.includes('json') ? await r.json() : await r.text(); }catch(e){}
  if(!r.ok){
    let msg=`HTTP ${r.status}`;
    if(body){
      if(typeof body==='string') msg=body;
      else if(typeof body.detail==='string') msg=body.detail;
      else if(body.detail?.message){
        msg=body.detail.message;
        if(Array.isArray(body.detail.errors)){
          msg += '\n'+body.detail.errors.map(x=>`Satır ${x.row}${x.plate?' • '+x.plate:''}: ${typeof x.error==='string'?x.error:JSON.stringify(x.error)}`).join('\n');
        }
      } else msg=JSON.stringify(body.detail||body);
    }
    throw new Error(msg);
  }
  return body;
}

function v77CleanStock(r){
  return {
    plate:String(r.plate||'').trim(),
    model_year:r.model_year?Number(r.model_year):null,
    km:Number(r.km||0),
    brand:String(r.brand||'').trim(),
    model:String(r.model||'').trim(),
    version:String(r.version||'').trim(),
    color:String(r.color||'').trim(),
    fuel:String(r.fuel||'').trim(),
    transmission:String(r.transmission||'').trim(),
    purchase_date:String(r.purchase_date||'').slice(0,10),
    purchase_type:String(r.purchase_type||'').trim(),
    purchase_price:Number(r.purchase_price||0),
    list_price:Number(r.list_price||0),
    target_profit:Number(r.target_profit||0)
  };
}
function v77CleanSale(r){
  return {
    plate:String(r.plate||'').trim(),
    vehicle_info:String(r.vehicle_info||'').trim(),
    model_year:r.model_year?Number(r.model_year):null,
    purchase_type:String(r.purchase_type||'').trim(),
    purchase_price:Number(r.purchase_price||0),
    purchase_date:String(r.purchase_date||'').slice(0,10),
    sale_date:String(r.sale_date||'').slice(0,10),
    extra_expense:Number(r.extra_expense||0),
    customer:String(r.customer||'').trim(),
    sale_type:String(r.sale_type||'').trim(),
    sale_price:Number(r.sale_price||0),
    consultant:String(r.consultant||'').trim(),
    insurance_income:Number(r.insurance_income||0),
    credit_income:Number(r.credit_income||0),
    warranty_income:Number(r.warranty_income||0)
  };
}
function v77ValidateStock(rows){
  const bad=rows.filter(x=>!x.purchase_type);
  if(bad.length){
    alert(`Aktarım yapılamadı.\n${bad.length} araçta Alım Türü seçilmemiş.`);
    return false;
  }
  return true;
}
function v77ValidateSales(rows){
  const p=rows.filter(x=>!x.purchase_type), s=rows.filter(x=>!x.sale_type), c=rows.filter(x=>!x.consultant);
  if(p.length||s.length||c.length){
    alert(`Aktarım yapılamadı.\nAlım Türü eksik: ${p.length}\nSatış Türü eksik: ${s.length}\nDanışman eksik: ${c.length}`);
    return false;
  }
  return true;
}

async function v77PostStock(rows,mode='merge'){
  const clean=rows.map(v77CleanStock);
  if(!clean.length){ alert('Aktarılacak araç yok.'); return false; }
  if(!v77ValidateStock(clean)) return false;
  if(mode==='replace' && !confirm('Mevcut GÜNCEL STOK silinip yalnızca seçili araçlar mı kalsın?')) return false;
  safe('#stockImportStatus',`⏳ ${clean.length} araç aktarılıyor...`);
  try{
    const r=await v77FetchJson('/api/import/stock/apply',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({rows:clean,mode})
    });
    safe('#stockImportStatus',`✓ ${r.count} araç başarıyla aktarıldı.`);
    alert(`${r.count} araç başarıyla aktarıldı.`);
    await refreshAll();
    return true;
  }catch(e){
    const msg=v77ErrText(e);
    safe('#stockImportStatus','❌ '+esc(msg));
    alert('STOK AKTARIM HATASI:\n'+msg);
    return false;
  }
}
async function v77PostSales(rows,mode='merge'){
  const clean=rows.map(v77CleanSale);
  if(!clean.length){ alert('Aktarılacak satış yok.'); return false; }
  if(!v77ValidateSales(clean)) return false;
  const m=$('#salesImportMonth')?.value||month();
  if(mode==='replace_month' && !confirm(`${m} ayındaki mevcut satışlar silinip yalnızca seçili satışlar mı kalsın?`)) return false;
  safe('#salesImportStatus',`⏳ ${clean.length} satış aktarılıyor...`);
  try{
    const r=await v77FetchJson('/api/import/sales/apply',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({rows:clean,mode,month:m})
    });
    safe('#salesImportStatus',`✓ ${r.count} satış başarıyla aktarıldı.`);
    alert(`${r.count} satış başarıyla aktarıldı.`);
    await refreshAll();
    return true;
  }catch(e){
    const msg=v77ErrText(e);
    safe('#salesImportStatus','❌ '+esc(msg));
    alert('SATIŞ AKTARIM HATASI:\n'+msg);
    return false;
  }
}

/* HTML'deki buton adlarıyla BİREBİR */
applyStockImport = async function(mode='merge'){
  const rows=stockImport.filter(x=>x._sel);
  if(await v77PostStock(rows,mode)){
    if(mode==='replace') stockImport=[];
    else stockImport=stockImport.filter(x=>!x._sel);
    renderStockImport();
  }
};
applyDirtyStockImport = async function(){
  const rows=stockImport.filter(x=>x._dirty);
  if(!rows.length){ alert('Henüz düzenlenmiş stok kaydı yok.'); return; }
  if(await v77PostStock(rows,'merge')){
    rows.forEach(x=>{x._dirty=false;x._sel=false;});
    renderStockImport();
  }
};
applyOneStockImport = async function(i){
  const r=stockImport[i]; if(!r) return;
  if(await v77PostStock([r],'merge')){
    r._dirty=false;r._sel=false;
    renderStockImport();
  }
};
/* V7.5'te render edilmiş eski Tek Aktar adı da desteklenir */
importOneStock = applyOneStockImport;

applySalesImport = async function(mode='merge'){
  const rows=salesImport.filter(x=>x._sel);
  if(await v77PostSales(rows,mode)){
    if(mode==='replace_month') salesImport=[];
    else salesImport=salesImport.filter(x=>!x._sel);
    renderSalesImport();
  }
};
applyDirtySalesImport = async function(){
  const rows=salesImport.filter(x=>x._dirty);
  if(!rows.length){ alert('Henüz düzenlenmiş satış kaydı yok.'); return; }
  if(await v77PostSales(rows,'merge')){
    rows.forEach(x=>{x._dirty=false;x._sel=false;});
    renderSalesImport();
  }
};
applyOneSalesImport = async function(i){
  const r=salesImport[i]; if(!r) return;
  if(await v77PostSales([r],'merge')){
    r._dirty=false;r._sel=false;
    renderSalesImport();
  }
};
applyOneSaleImport = applyOneSalesImport;
importOneSale = applyOneSalesImport;

/* para inputlarında önceki yama ismini kullanan satırlar için */
if(typeof parseMoneyInput==='undefined'){
  window.parseMoneyInput=function(v){ return parseMoney(v); };
}

console.log('RENEW V7.7 FINAL IMPORT CONTROLLER ACTIVE');
/* =============================== /V7.7 =============================== */

function renderAcquisitions(){const s=ACQSUMMARY||{};kpis('#acqKpis',[['Bu Ay Alınan',`${s.count||0} Adet`,'good',''],['Toplam Alış',money(s.purchase_total||0),'',''],['Toplam Masraf',money(s.expense_total||0),'warn',''],['Toplam Maliyet',money(s.total_cost||0),'','']]);safe('#acqPeople',table(['Alınan Kişi / Ekspertiz','Araç','Alış Toplamı','Masraf','Toplam'],(s.by_person||[]).map(x=>`<tr><td><b>${esc(x.name)}</b></td><td>${x.count}</td><td>${money(x.purchase_total)}</td><td>${money(x.expense_total)}</td><td><b>${money(x.total_cost)}</b></td></tr>`)));safe('#acqTypes',bars(s.by_type||[]));safe('#acqTable',table(['#','Tarih','Plaka','Yıl','KM','Marka','Model','Versiyon','Alım Türü','Alınan Kişi','Alış','Masraf','Toplam','İşlem'],ACQUISITIONS.map((x,i)=>`<tr><td>${i+1}</td><td>${esc(x.purchase_date)}</td><td><b>${esc(x.plate)}</b></td><td>${x.model_year||''}</td><td>${Number(x.km||0).toLocaleString('tr-TR')}</td><td>${esc(x.brand)}</td><td>${esc(x.model)}</td><td>${esc(x.version)}</td><td>${esc(x.purchase_type)}</td><td><b>${esc(x.acquired_by)}</b></td><td>${money(x.purchase_price)}</td><td>${money(x.expense)}</td><td><b>${money(Number(x.purchase_price)+Number(x.expense))}</b></td><td><button class="btn small" onclick="openAcquisition(${x.id})">Düzenle</button> <button class="btn danger small" onclick="deleteAcquisition(${x.id})">Sil</button></td></tr>`)));let m=month();['#acqXlsx','#rAcqXlsx'].forEach(q=>{let n=$(q);if(n)n.href='/api/export/acquisitions.xlsx?month='+m});['#acqPdf','#rAcq'].forEach(q=>{let n=$(q);if(n)n.href='/api/report/acquisitions?month='+m});}
function acqPeopleOptions(sel=''){let names=[...new Set((EXPERTISE||[]).map(x=>x.consultant).filter(Boolean))];if(!names.length)names=(SETTINGS.consultants||[]).filter(x=>x.active).map(x=>x.name);return names.map(n=>`<option ${norm(n)==norm(sel)?'selected':''}>${esc(n)}</option>`).join('')}
function acqPurchaseOptions(sel=''){return (SETTINGS.rules||[]).filter(x=>x.active).map(x=>`<option ${norm(x.name)==norm(sel)?'selected':''}>${esc(x.name)}</option>`).join('')}
function openAcquisition(id=null){let x=id?ACQUISITIONS.find(a=>a.id===id):null;$('#modalTitle').textContent=x?'Aylık Alımı Düzenle':'Yeni Aylık Alım';$('#modalBody').innerHTML=`<form id="acqForm" class="formgrid"><label>Alım Tarihi<input name="purchase_date" type="date" required value="${esc(x?.purchase_date||new Date().toISOString().slice(0,10))}"></label><label>Plaka<input name="plate" required value="${esc(x?.plate||'')}"></label><label>Model Yılı<input name="model_year" type="number" value="${x?.model_year||''}"></label><label>KM<input name="km" type="number" value="${x?.km||0}"></label><label>Marka<input name="brand" value="${esc(x?.brand||'')}"></label><label>Model<input name="model" value="${esc(x?.model||'')}"></label><label>Versiyon<input name="version" value="${esc(x?.version||'')}"></label><label>Renk<input name="color" value="${esc(x?.color||'')}"></label><label>Yakıt<input name="fuel" value="${esc(x?.fuel||'')}"></label><label>Vites<input name="transmission" value="${esc(x?.transmission||'')}"></label><label>Alım Türü<select name="purchase_type" required><option value="">Seçiniz</option>${acqPurchaseOptions(x?.purchase_type)}</select></label><label>Alınan Kişi / Ekspertiz<select name="acquired_by" required><option value="">Seçiniz</option>${acqPeopleOptions(x?.acquired_by)}</select></label><label>Alış Fiyatı<input name="purchase_price" type="number" value="${x?.purchase_price||0}"></label><label>Masraf<input name="expense" type="number" value="${x?.expense||0}"></label><div class="actions full"><button type="submit" class="btn success">Kaydet</button></div></form>`;$('#modal').classList.add('show');$('#acqForm').onsubmit=async e=>{e.preventDefault();let o=Object.fromEntries(new FormData(e.target).entries());['model_year','km','purchase_price','expense'].forEach(k=>o[k]=Number(o[k]||0));try{await api(id?'/api/acquisitions/'+id:'/api/acquisitions',{method:id?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(o)});closeModal();await refreshAll()}catch(err){alert('Alım kaydedilemedi:\n'+err.message)}}}
async function deleteAcquisition(id){if(!confirm('Bu aylık alım kaydı silinsin mi?'))return;await api('/api/acquisitions/'+id,{method:'DELETE'});await refreshAll()}
console.log('RENEW V7.8 AYLIK ALIM MODÜLÜ ACTIVE');

/* ===== V7.9 AYLIK ALIM UI / IMPORT ===== */
function renderDashAcquisitions(){
  const s=ACQSUMMARY||{};
  safe('#dashAcquisitions',`<div class="split"><div class="g">Bu Ay Alınan<b>${s.count||0}</b></div><div class="g">Toplam Maliyet<b style="font-size:15px">${money(s.total_cost||0)}</b></div></div>
  ${table(['Alınan Kişi','Araç','Alış','Masraf'],(s.by_person||[]).slice(0,6).map(x=>`<tr><td><b>${esc(x.name)}</b></td><td>${x.count}</td><td>${money(x.purchase_total)}</td><td>${money(x.expense_total)}</td></tr>`))}`);
  const m=month(); const top=$('#topAcqXlsx'); if(top) top.href='/api/export/acquisitions.xlsx?month='+m;
}
const _v79_renderAcquisitions = typeof renderAcquisitions==='function' ? renderAcquisitions : null;
if(_v79_renderAcquisitions){
  renderAcquisitions=function(){ _v79_renderAcquisitions(); renderDashAcquisitions(); };
}
let ACQIMPORT=[];
async function previewAcquisitionImport(file){
 if(!file)return;
 const m=month();
 const status=$('#acqImportStatus'); if(status){status.style.display='block';status.textContent='⏳ Aylık alım Excel okunuyor...';}
 try{
   const fd=new FormData();fd.append('month',m);fd.append('file',file);
   const r=await api('/api/import/acquisitions/preview',{method:'POST',body:fd});
   ACQIMPORT=r.rows||[];
   if(status){status.innerHTML=`✓ <b>${esc(r.file_name)}</b>: ${ACQIMPORT.length} alım kaydı okundu. <button class="btn success small" onclick="applyAcquisitionImport('merge')">Seçili Aya Ekle</button> <button class="btn danger small" onclick="applyAcquisitionImport('replace_month')">Bu Ayı Sil + Yeniden Aktar</button>`;}
   if(ACQIMPORT.length){
     page('acquisitions');
     safe('#acqTable',table(['#','Tarih','Plaka','Marka','Model','Versiyon','Alım Türü','Alınan Kişi','Alış','Masraf','Durum'],ACQIMPORT.map((x,i)=>`<tr><td>${i+1}</td><td>${esc(x.purchase_date)}</td><td><b>${esc(x.plate)}</b></td><td>${esc(x.brand)}</td><td>${esc(x.model)}</td><td>${esc(x.version)}</td><td>${esc(x.purchase_type||'')}</td><td>${esc(x.acquired_by||'')}</td><td>${money(x.purchase_price)}</td><td>${money(x.expense)}</td><td>${(!x.purchase_type||!x.acquired_by)?'<span class="loss">SEÇİM EKSİK</span>':'Hazır'}</td></tr>`)));
   }
 }catch(e){if(status){status.style.display='block';status.textContent='❌ '+e.message;}alert('Aylık alım Excel okunamadı:\n'+e.message);}
}
async function applyAcquisitionImport(mode='merge'){
 if(!ACQIMPORT.length)return alert('Önce aylık alım Excel dosyası yükleyin.');
 const bad=ACQIMPORT.filter(x=>!x.purchase_type||!x.acquired_by);
 if(bad.length)return alert(`${bad.length} kayıtta Alım Türü veya Alınan Kişi eksik. Önce Excel'de doldurun veya panelden tek tek ekleyin.`);
 if(mode==='replace_month'&&!confirm(`${month()} ayındaki mevcut aylık alım kayıtları silinip bu Excel ile yeniden oluşturulsun mu?`))return;
 try{
   const r=await api('/api/import/acquisitions/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({rows:ACQIMPORT,month:month(),mode})});
   alert(`${r.count} aylık alım kaydı aktarıldı.`);ACQIMPORT=[];await refreshAll();page('acquisitions');
 }catch(e){alert('Aylık alım aktarımı başarısız:\n'+e.message)}
}
console.log('RENEW V7.9 AYLIK ALIM UI FIX ACTIVE');

/* ================= V7.10 YENİ ALIM FINAL CONTROLLER ================= */
function acqNorm(v){
  return String(v??'').trim().toLocaleUpperCase('tr-TR')
    .normalize('NFD').replace(/[\u0300-\u036f]/g,'')
    .replace(/İ/g,'I').replace(/Ş/g,'S').replace(/Ğ/g,'G').replace(/Ü/g,'U').replace(/Ö/g,'O').replace(/Ç/g,'C')
    .replace(/\s+/g,' ');
}
function acqActivePeople(){
  let names=[];
  (EXPERTISE||[]).forEach(x=>{if(x && x.consultant) names.push(x.consultant)});
  (SETTINGS.consultants||[]).forEach(x=>{if(Number(x.active)!==0 && x.name) names.push(x.name)});
  const seen=new Set(), out=[];
  names.forEach(n=>{const k=acqNorm(n);if(k&&!seen.has(k)){seen.add(k);out.push(n)}});
  return out;
}
function acqActivePurchaseTypes(){
  return (SETTINGS.rules||[]).filter(x=>Number(x.active)!==0 && x.name).map(x=>x.name);
}
function acqOptionList(list,selected){
  return list.map(v=>`<option value="${esc(v)}" ${acqNorm(v)===acqNorm(selected)?'selected':''}>${esc(v)}</option>`).join('');
}
function acqMoneyDisplay(v){
  return Number(v||0).toLocaleString('tr-TR');
}
function acqMoneyParse(v){
  let s=String(v||'').replace(/\s/g,'').replace(/TL|₺/gi,'');
  if((s.match(/\./g)||[]).length && !s.includes(',')) s=s.replace(/\./g,'');
  else s=s.replace(/\./g,'').replace(',','.');
  s=s.replace(/[^0-9.-]/g,'');
  let n=Number(s);return Number.isFinite(n)?n:0;
}

openAcquisition = function(id=null){
  try{
    const x=id ? (ACQUISITIONS||[]).find(a=>Number(a.id)===Number(id)) : null;
    const modal=document.getElementById('modal'), title=document.getElementById('modalTitle'), body=document.getElementById('modalBody');
    if(!modal||!title||!body){
      alert('Yeni Alım formu açılamadı: modal alanı bulunamadı.');
      return;
    }
    const people=acqActivePeople(), purchaseTypes=acqActivePurchaseTypes();
    title.textContent=x?'Aylık Alımı Düzenle':'Yeni Aylık Alım';
    body.innerHTML=`
      <form id="acqFormV710" class="acq-form">
        <div class="acq-grid">
          <label><span>Alım Tarihi *</span><input name="purchase_date" type="date" required value="${esc(x?.purchase_date||new Date().toISOString().slice(0,10))}"></label>
          <label><span>Plaka *</span><input name="plate" required value="${esc(x?.plate||'')}"></label>
          <label><span>Model Yılı</span><input name="model_year" type="number" value="${x?.model_year||''}"></label>
          <label><span>KM</span><input name="km" type="number" value="${x?.km||0}"></label>
          <label><span>Marka</span><input name="brand" value="${esc(x?.brand||'')}"></label>
          <label><span>Model</span><input name="model" value="${esc(x?.model||'')}"></label>
          <label class="wide"><span>Versiyon</span><input name="version" value="${esc(x?.version||'')}"></label>
          <label><span>Renk</span><input name="color" value="${esc(x?.color||'')}"></label>
          <label><span>Yakıt</span><input name="fuel" value="${esc(x?.fuel||'')}"></label>
          <label><span>Vites</span><input name="transmission" value="${esc(x?.transmission||'')}"></label>
          <label><span>Alım Türü *</span>
            <select name="purchase_type" required>
              <option value="">— Seçiniz —</option>${acqOptionList(purchaseTypes,x?.purchase_type||'')}
            </select>
          </label>
          <label><span>Alınan Kişi / Ekspertiz *</span>
            <select name="acquired_by" required>
              <option value="">— Seçiniz —</option>${acqOptionList(people,x?.acquired_by||'')}
            </select>
          </label>
          <label><span>Alış Fiyatı</span><input name="purchase_price" inputmode="numeric" value="${acqMoneyDisplay(x?.purchase_price||0)}"></label>
          <label><span>Masraf</span><input name="expense" inputmode="numeric" value="${acqMoneyDisplay(x?.expense||0)}"></label>
        </div>
        <div class="acq-help">
          ${people.length?`Ekspertiz/Alım personeli: ${people.length} kişi aktif.`:'<b>Uyarı:</b> Aktif ekspertiz/personel bulunamadı. Önce Ekspertiz Takip veya Danışman Ayarları bölümüne kişi ekleyin.'}
        </div>
        <div class="actions">
          <button type="button" class="btn ghost" onclick="closeModal()">Vazgeç</button>
          <button type="submit" class="btn success">Kaydet</button>
        </div>
      </form>`;
    modal.classList.add('show');

    const form=document.getElementById('acqFormV710');
    form.addEventListener('submit',async function(e){
      e.preventDefault();
      const f=new FormData(form);
      const o=Object.fromEntries(f.entries());
      o.model_year=o.model_year?Number(o.model_year):null;
      o.km=Number(o.km||0);
      o.purchase_price=acqMoneyParse(o.purchase_price);
      o.expense=acqMoneyParse(o.expense);
      if(!o.purchase_type){alert('Alım Türü seçmek zorunlu.');return;}
      if(!o.acquired_by){alert('Alınan Kişi / Ekspertiz seçmek zorunlu.');return;}
      const submit=form.querySelector('button[type="submit"]');
      submit.disabled=true;submit.textContent='Kaydediliyor...';
      try{
        await api(id?'/api/acquisitions/'+id:'/api/acquisitions',{
          method:id?'PUT':'POST',
          headers:{'Content-Type':'application/json'},
          body:JSON.stringify(o)
        });
        closeModal();
        await refreshAll();
        page('acquisitions');
      }catch(err){
        alert('Yeni alım kaydedilemedi:\n'+(err.message||err));
      }finally{
        submit.disabled=false;submit.textContent='Kaydet';
      }
    });
  }catch(err){
    console.error('openAcquisition V7.10 error',err);
    alert('Yeni Alım ekranı açılırken hata oluştu:\n'+(err.message||err));
  }
};
console.log('RENEW V7.10 YENİ ALIM CONTROLLER ACTIVE');
/* ================= /V7.10 ================= */

function photoPlate(){return String(document.getElementById('photoPlate')?.value||'').trim().toUpperCase().replace(/\s+/g,'');}
function photoCard(plate,kind,x){return `<div class="photo-card"><img src="${x.url}" loading="lazy"><div class="photo-meta"><small>${esc(x.name)}</small><div class="photo-actions">${kind==='original'?`<button class="btn small" onclick="copyPhotoToProcessed('${plate}','${encodeURIComponent(x.name)}')">İşlenmişe Kopyala</button>`:''}<button class="btn danger small" onclick="deleteVehiclePhoto('${plate}','${kind}','${encodeURIComponent(x.name)}')">Sil</button></div></div></div>`;}
async function loadVehiclePhotos(){const p=photoPlate();if(!p)return alert('Önce plaka girin.');try{const r=await api('/api/photos/'+encodeURIComponent(p));safe('#originalGallery',(r.original||[]).map(x=>photoCard(p,'original',x)).join('')||'<div class="empty">Orijinal fotoğraf yok.</div>');safe('#processedGallery',(r.processed||[]).map(x=>photoCard(p,'processed',x)).join('')||'<div class="empty">İşlenmiş fotoğraf yok.</div>');safe('#originalCount',`${(r.original||[]).length} fotoğraf`);safe('#processedCount',`${(r.processed||[]).length} fotoğraf`);}catch(e){alert('Fotoğraflar yüklenemedi:\n'+e.message);}}
async function uploadVehiclePhotos(){const p=photoPlate(),input=document.getElementById('photoFiles');if(!p)return alert('Plaka zorunlu.');if(!input?.files?.length)return alert('En az bir fotoğraf seçin.');const fd=new FormData();fd.append('plate',p);[...input.files].forEach(f=>fd.append('files',f));document.getElementById('photoStatus').style.display='block';safe('#photoStatus','⏳ Fotoğraflar yükleniyor...');try{const r=await api('/api/photos/upload',{method:'POST',body:fd});safe('#photoStatus',`✓ ${r.count} fotoğraf ${p} klasörüne kaydedildi.`);input.value='';await loadVehiclePhotos();}catch(e){safe('#photoStatus','❌ '+esc(e.message));}}
async function deleteVehiclePhoto(plate,kind,name){if(!confirm('Bu fotoğraf silinsin mi?'))return;await api(`/api/photos/${encodeURIComponent(plate)}/${kind}/${name}`,{method:'DELETE'});await loadVehiclePhotos();}
async function copyPhotoToProcessed(plate,name){await api(`/api/photos/${encodeURIComponent(plate)}/copy-to-processed/${name}`,{method:'POST'});await loadVehiclePhotos();}
function downloadPhotoZip(kind){const p=photoPlate();if(!p)return alert('Plaka zorunlu.');window.location.href=`/api/photos/download-zip/${encodeURIComponent(p)}/${kind}`;}
console.log('RENEW V7.11 PHOTO ARCHIVE ACTIVE');

function vehicleCatalog(){
 const all=[];
 (STOCKS||[]).forEach(x=>all.push({plate:x.plate,label:`${x.plate} • ${x.brand||''} ${x.model||''} ${x.version||''} • STOKTA`}));
 (SALES||[]).forEach(x=>all.push({plate:x.plate,label:`${x.plate} • ${x.vehicle_info||''} • SATILDI`}));
 const seen=new Set(),out=[];
 all.forEach(x=>{let k=String(x.plate||'').replace(/\s/g,'').toUpperCase();if(k&&!seen.has(k)){seen.add(k);out.push(x)}});
 return out;
}
function refreshVehicleSelectors(){
 const opts='<option value="">— Araç Seç —</option>'+vehicleCatalog().map(x=>`<option value="${esc(x.plate)}">${esc(x.label)}</option>`).join('');
 const p=$('#photoVehicleSelect'),v=$('#vehicle360Select'); if(p)p.innerHTML=opts;if(v)v.innerHTML=opts;
}
function selectPhotoVehicle(plate){if(!plate)return;const p=$('#photoPlate');if(p)p.value=plate;loadVehiclePhotos();}
function openVehiclePhotos(plate){page('photos');setTimeout(()=>{refreshVehicleSelectors();const p=$('#photoPlate');if(p)p.value=plate;const s=$('#photoVehicleSelect');if(s)s.value=plate;loadVehiclePhotos();},20);}
function v360StatusBadge(status){const c=status==='SATILDI'?'v360-sold':status==='STOKTA'?'v360-stock':'';return `<span class="v360-status ${c}">${esc(status||'')}</span>`;}
async function openVehicleCard(plate,inPage=false){
 try{
   const d=await api('/api/vehicle-card/'+encodeURIComponent(plate));
   const st=d.stock||{},sl=d.sale||{},aq=d.acquisition||{},c=d.calc||{};const sold=d.status==='SATILDI';
   const purchase=Number((sl.purchase_price??st.purchase_price)||0),sale=Number(sl.sale_price||st.list_price||0),totalCost=Number(c.total_cost||0),profit=Number((sold?c.performance_profit:c.estimated_profit)||0),sks=Number(c.sks_days||0);
   const body=`<div class="v360-wrap">
    <div class="v360-hero"><div><div class="v360-plate">${esc(d.plate)}</div><h2>${esc(d.vehicle_info||'Araç')}</h2><div>${v360StatusBadge(d.status)} ${sksBadge(sks)}</div></div><div><button class="btn dark" onclick="openVehiclePhotos('${esc(d.plate)}')">📷 Fotoğraflar (${d.photos.original+d.photos.processed})</button></div></div>
    <div class="v360-kpis"><div><span>Alış</span><b>${money(purchase)}</b></div><div><span>Toplam Maliyet</span><b>${money(totalCost)}</b></div><div><span>${sold?'Satış Bedeli':'Liste Satış'}</span><b>${money(sale)}</b></div><div class="${profit<0?'negative':'positive'}"><span>${sold?'Performans Kârı':'Tahmini Kâr'}</span><b>${money(profit)}</b></div><div><span>SKS</span><b>${sks} Gün</b></div><div><span>SKS Finansman</span><b>${money(c.sks_finance||0)}</b></div></div>
    <div class="grid2"><div class="card"><h3>Araç & Alım Bilgileri</h3><div class="v360-info"><span>Model Yılı<b>${st.model_year||sl.model_year||''}</b></span><span>KM<b>${Number(st.km||0).toLocaleString('tr-TR')}</b></span><span>Alım Tarihi<b>${st.purchase_date||sl.purchase_date||aq.purchase_date||''}</b></span><span>Alım Türü<b>${st.purchase_type||sl.purchase_type||aq.purchase_type||''}</b></span><span>Alınan Kişi / Kaynak<b>${aq.acquired_by||'—'}</b></span><span>Renk<b>${st.color||aq.color||'—'}</b></span><span>Yakıt<b>${st.fuel||aq.fuel||'—'}</b></span><span>Vites<b>${st.transmission||aq.transmission||'—'}</b></span></div></div>
    <div class="card"><h3>Fotoğraf Arşivi</h3><div class="v360-photo-summary"><div><b>${d.photos.original}</b><span>Orijinal</span></div><div><b>${d.photos.processed}</b><span>İşlenmiş</span></div></div><button class="btn primary" onclick="openVehiclePhotos('${esc(d.plate)}')">Fotoğraf Galerisini Aç</button></div></div>
    ${sold?`<div class="card"><h3>Satış Bilgileri</h3><div class="v360-info"><span>Satış Tarihi<b>${sl.sale_date||''}</b></span><span>Satış Türü<b>${esc(sl.sale_type||'')}</b></span><span>Danışman<b>${esc(sl.consultant||'')}</b></span><span>Müşteri<b>${esc(sl.customer||'')}</b></span><span>Net Kâr<b class="${Number(c.net_profit||0)<0?'loss':'profit'}">${money(c.net_profit||0)}</b></span><span>Ek Gelir<b>${money(c.extra_income||0)}</b></span></div></div>`:''}
    <div class="card"><h3>Süreç</h3><div class="v360-timeline"><div class="done">ALINDI</div><div class="done">EKSPERTİZ</div><div class="${sold?'done':'active'}">STOKTA</div><div class="${sold?'done':''}">SATILDI</div></div></div></div>`;
   if(inPage){page('vehicle360');safe('#vehicle360Content',body);const s=$('#vehicle360Select');if(s)s.value=plate;}else{showModal(`Araç 360° • ${plate}`,body);}
 }catch(e){alert('Araç kartı açılamadı:\n'+e.message)}
}
const _refreshAllV712=refreshAll;
refreshAll=async function(){const x=await _refreshAllV712();setTimeout(refreshVehicleSelectors,0);return x;}
window.addEventListener('DOMContentLoaded',()=>setTimeout(refreshVehicleSelectors,500));
console.log('RENEW V7.12 VEHICLE 360 ACTIVE');
/* ================= V7.14 MEDYA MERKEZİ ================= */
let MEDIA_SOURCES={stocks:[],sales:[],acquisitions:[]},CURRENT_MEDIA=null,CURRENT_MEDIA_TAB='original';
async function loadMediaSources(){try{MEDIA_SOURCES=await api('/api/vehicle-sources');refreshMediaVehicleSelect();refresh360GroupedSelect();}catch(e){}}
function mediaSourceLabel(k){return k==='stocks'?'GÜNCEL STOK':k==='sales'?'SATILAN ARAÇ':'ALINAN ARAÇ'}
function mediaItemLabel(k,x){if(k==='stocks')return `${x.plate} • ${x.brand||''} ${x.model||''} ${x.version||''}`;if(k==='sales')return `${x.plate} • ${x.vehicle_info||''}`;return `${x.plate} • ${x.brand||''} ${x.model||''} ${x.version||''} • ${x.acquired_by||''}`}
function refreshMediaVehicleSelect(){const k=$('#mediaSourceFilter')?.value||'stocks',sel=$('#mediaVehicleSelect');if(!sel)return;const rows=MEDIA_SOURCES[k]||[];sel.innerHTML='<option value="">— Araç Seç —</option>'+rows.map(x=>`<option value="${esc(x.plate)}">${esc(mediaItemLabel(k,x))}</option>`).join('')}
async function selectMediaVehicle(plate){if(!plate)return;$('#mediaPlate').value=plate;const k=$('#mediaSourceFilter').value;const x=(MEDIA_SOURCES[k]||[]).find(v=>String(v.plate).replace(/\s/g,'').toUpperCase()===String(plate).replace(/\s/g,'').toUpperCase());const info=$('#mediaVehicleInfo');if(info){info.style.display='block';info.innerHTML=`<b>${esc(plate)}</b> • ${esc(mediaSourceLabel(k))} • ${esc(mediaItemLabel(k,x||{}).replace(plate,'').replace('•','').trim())}`;}await loadMediaCenter()}
function mediaPlate(){return String($('#mediaPlate')?.value||'').replace(/\s/g,'').toUpperCase()}
function mediaTab(kind,btn){CURRENT_MEDIA_TAB=kind;document.querySelectorAll('.media-tabs button').forEach(x=>x.classList.remove('active'));if(btn)btn.classList.add('active');const titles={original:'Araç Fotoğrafları',listing:'İlan Fotoğrafları',documents:'Belgeler',archive:'Arşiv'};$('#mediaSectionTitle').textContent=titles[kind];const lab=$('#mediaUploadLabel');if(lab)lab.childNodes[0].nodeValue=(kind==='documents'?'Belge Yükle':'Fotoğraf Yükle');const f=$('#mediaFiles');if(f)f.accept=kind==='documents'?'.pdf,.jpg,.jpeg,.png,.webp,.doc,.docx,.xls,.xlsx,.txt':'.jpg,.jpeg,.png,.webp';$('#listingZipBtn').style.display=kind==='listing'?'inline-flex':'none';$('#saveOrderBtn').style.display=kind==='listing'?'inline-flex':'none';renderMediaGallery()}
async function loadMediaCenter(){const p=mediaPlate();if(!p)return;try{CURRENT_MEDIA=await api('/api/media/'+encodeURIComponent(p));renderMediaGallery()}catch(e){safe('#mediaStatus','❌ '+esc(e.message));$('#mediaStatus').style.display='block'}}
function mediaThumb(x){const ext=(x.name.split('.').pop()||'').toLowerCase(),img=['jpg','jpeg','png','webp'].includes(ext);return img?`<img src="${x.url}" loading="lazy">`:`<div class="doc-icon">📄<b>${esc(ext.toUpperCase())}</b></div>`}
function renderMediaGallery(){if(!CURRENT_MEDIA){safe('#mediaGallery','<div class="empty">Araç seçin.</div>');return}const arr=(CURRENT_MEDIA.folders||{})[CURRENT_MEDIA_TAB]||[];safe('#mediaCount',`${arr.length} kayıt`);const isListing=CURRENT_MEDIA_TAB==='listing';safe('#mediaGallery',arr.map((x,i)=>`<div class="media-card" draggable="${isListing?'true':'false'}" data-name="${esc(x.name)}"><div class="media-top">${isListing?`<span class="order-badge">${i+1}</span>`:''}${x.is_cover?'<span class="cover-badge">⭐ KAPAK</span>':''}</div>${mediaThumb(x)}<div class="media-body"><input class="media-rename" value="${esc(x.name.replace(/\.[^.]+$/,''))}" title="Dosya adı"><div class="media-row"><button class="btn small" onclick="renameMedia('${CURRENT_MEDIA_TAB}','${encodeURIComponent(x.name)}',this)">İsmi Değiştir</button>${CURRENT_MEDIA_TAB!=='documents'?`<button class="btn small" onclick="setMediaCover('${CURRENT_MEDIA_TAB}','${encodeURIComponent(x.name)}')">⭐ Kapak</button>`:''}</div><div class="media-row">${CURRENT_MEDIA_TAB==='original'?`<button class="btn success small" onclick="moveMedia('original','listing','${encodeURIComponent(x.name)}')">→ İlana</button><button class="btn ghost small" onclick="moveMedia('original','archive','${encodeURIComponent(x.name)}')">Arşivle</button>`:''}${CURRENT_MEDIA_TAB==='listing'?`<button class="btn ghost small" onclick="moveMedia('listing','archive','${encodeURIComponent(x.name)}')">Arşivle</button>`:''}${CURRENT_MEDIA_TAB==='archive'?`<button class="btn success small" onclick="moveMedia('archive','original','${encodeURIComponent(x.name)}')">Geri Al</button>`:''}<button class="btn danger small" onclick="deleteMedia('${CURRENT_MEDIA_TAB}','${encodeURIComponent(x.name)}')">Sil</button></div>${CURRENT_MEDIA_TAB==='documents'?`<input class="media-label" value="${esc(x.label||'')}" placeholder="Örn: Ruhsat Bilgisi" onchange="setMediaLabel('documents','${encodeURIComponent(x.name)}',this.value)">`:''}</div></div>`).join('')||'<div class="empty">Bu bölümde kayıt yok.</div>');if(isListing)enableListingDrag()}
async function uploadMediaFiles(){const p=mediaPlate(),f=$('#mediaFiles');if(!p)return alert('Araç seçin.');if(!f?.files?.length)return alert('Dosya seçin.');const fd=new FormData();fd.append('plate',p);fd.append('kind',CURRENT_MEDIA_TAB);[...f.files].forEach(x=>fd.append('files',x));$('#mediaStatus').style.display='block';safe('#mediaStatus','⏳ Dosyalar yükleniyor...');try{const r=await api('/api/media/upload',{method:'POST',body:fd});safe('#mediaStatus',`✓ ${r.count} dosya yüklendi.`);f.value='';await loadMediaCenter()}catch(e){safe('#mediaStatus','❌ '+esc(e.message))}}
async function renameMedia(kind,name,btn){const card=btn.closest('.media-card'),input=card.querySelector('.media-rename'),new_name=input.value.trim();if(!new_name)return;try{await api(`/api/media/${encodeURIComponent(mediaPlate())}/rename`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({kind,name:decodeURIComponent(name),new_name})});await loadMediaCenter()}catch(e){alert(e.message)}}
async function moveMedia(from,to,name){await api(`/api/media/${encodeURIComponent(mediaPlate())}/move`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({from,to,name:decodeURIComponent(name)})});await loadMediaCenter()}
async function setMediaCover(kind,name){await api(`/api/media/${encodeURIComponent(mediaPlate())}/cover`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({kind,name:decodeURIComponent(name)})});await loadMediaCenter()}
async function setMediaLabel(kind,name,label){await api(`/api/media/${encodeURIComponent(mediaPlate())}/label`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({kind,name:decodeURIComponent(name),label})});await loadMediaCenter()}
async function deleteMedia(kind,name){if(!confirm('Bu dosya silinsin mi?'))return;await api(`/api/media/${encodeURIComponent(mediaPlate())}/${kind}/${name}`,{method:'DELETE'});await loadMediaCenter()}
function downloadVehicleMediaBackup(){const p=mediaPlate();if(!p)return alert('Araç seçin.');window.location.href=`/api/media/${encodeURIComponent(p)}/backup`}
function downloadListingZip(){const p=mediaPlate();if(!p)return alert('Araç seçin.');window.location.href=`/api/media/${encodeURIComponent(p)}/listing-zip`}
async function openCurrentMediaFolder(){const p=mediaPlate();if(!p)return alert('Araç seçin.');const r=await api(`/api/media/${encodeURIComponent(p)}/open-folder`,{method:'POST'});if(!r.ok)alert('Klasör yolu:\n'+r.path)}
let dragEl=null;function enableListingDrag(){document.querySelectorAll('#mediaGallery .media-card').forEach(card=>{card.ondragstart=()=>{dragEl=card;card.classList.add('dragging')};card.ondragend=()=>{card.classList.remove('dragging');dragEl=null};card.ondragover=e=>{e.preventDefault();const box=card.getBoundingClientRect();const before=e.clientY<box.top+box.height/2;const parent=card.parentNode;if(dragEl&&dragEl!==card)parent.insertBefore(dragEl,before?card:card.nextSibling)}})}
async function saveListingOrder(){const names=[...document.querySelectorAll('#mediaGallery .media-card')].map(x=>x.dataset.name);await api(`/api/media/${encodeURIComponent(mediaPlate())}/listing-order`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({names})});await loadMediaCenter();alert('İlan fotoğraf sırası kaydedildi.')}
function refresh360GroupedSelect(){const s=$('#vehicle360Select');if(!s)return;const group=(label,rows,k)=>`<optgroup label="${label}">${(rows||[]).map(x=>`<option value="${esc(x.plate)}">${esc(mediaItemLabel(k,x))}</option>`).join('')}</optgroup>`;s.innerHTML='<option value="">— Araç Seç —</option>'+group('GÜNCEL STOK',MEDIA_SOURCES.stocks,'stocks')+group('SATILAN ARAÇLAR',MEDIA_SOURCES.sales,'sales')+group('ALINAN ARAÇLAR',MEDIA_SOURCES.acquisitions,'acquisitions')}
const _v714Refresh=refreshAll;refreshAll=async function(){const r=await _v714Refresh();setTimeout(loadMediaSources,0);return r};window.addEventListener('DOMContentLoaded',()=>setTimeout(loadMediaSources,700));console.log('RENEW V7.14 MEDIA CENTER ACTIVE');
/* ================= /V7.14 ================= */

/* ================= V7.15 KULLANICI / YETKİ / LOG ================= */
let CURRENT_USER=null,USER_META=null,USERS=[];

function hasPerm(p){return CURRENT_USER&&(CURRENT_USER.role==='administrator'||(CURRENT_USER.permissions||[]).includes(p))}
function applyPermissions(){
 const map={
  dashboard:'dashboard.view',stocks:'stocks.view',sales:'sales.view',acquisitions:'acquisitions.view',
  expertise:'expertise.view',performance:'performance.view',settings:'settings.view',master:'imports.use',
  'stock-import':'imports.use','sales-import':'imports.use',reports:'reports.view',audit:'audit.view',
  photos:'media.view',vehicle360:'dashboard.view',users:'users.manage'
 };
 document.querySelectorAll('.nav[data-page]').forEach(n=>{const p=map[n.dataset.page];n.style.display=(!p||hasPerm(p))?'':'none'});
 document.querySelectorAll('.admin-only').forEach(n=>n.style.display=hasPerm('users.manage')?'':'none');
 const box=$('#currentUserBox');if(box&&CURRENT_USER)box.innerHTML=`<b>${esc(CURRENT_USER.full_name)}</b><small>${esc(CURRENT_USER.role)}</small>`;
}
async function checkAuth(){
 try{
  CURRENT_USER=await api('/api/auth/me');
  $('#loginOverlay').classList.add('hidden');applyPermissions();
  if(CURRENT_USER.must_change_password)setTimeout(()=>openPasswordChange(true),200);
  await refreshAll();
 }catch(e){
  CURRENT_USER=null;$('#loginOverlay').classList.remove('hidden');
 }
}
$('#loginForm').onsubmit=async e=>{
 e.preventDefault();const u=$('#loginUsername').value.trim(),p=$('#loginPassword').value;
 try{
  const r=await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});
  const j=await r.json();if(!r.ok)throw new Error(j.detail||'Giriş başarısız');
  CURRENT_USER=j;$('#loginOverlay').classList.add('hidden');applyPermissions();$('#loginMessage').textContent='';
  await refreshAll();if(CURRENT_USER.must_change_password)setTimeout(()=>openPasswordChange(true),200);
 }catch(err){$('#loginMessage').textContent='❌ '+err.message;}
};
async function logoutUser(){
 try{await api('/api/auth/logout',{method:'POST'})}catch(e){}
 location.reload();
}
function openPasswordChange(force=false){
 showModal('Şifre Değiştir',`<form id="pwForm" class="formgrid">
   ${force?'':'<label>Mevcut Şifre<input name="old_password" type="password"></label>'}
   <label>Yeni Şifre<input name="new_password" type="password" minlength="6" required></label>
   <label>Yeni Şifre Tekrar<input name="again" type="password" minlength="6" required></label>
   <div class="actions full"><button class="btn success" type="submit">Şifreyi Kaydet</button></div></form>`);
 $('#pwForm').onsubmit=async e=>{e.preventDefault();const f=new FormData(e.target);if(f.get('new_password')!==f.get('again'))return alert('Yeni şifreler aynı değil.');await api('/api/auth/change-password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({old_password:f.get('old_password')||'',new_password:f.get('new_password')})});closeModal();CURRENT_USER=await api('/api/auth/me');applyPermissions();alert('Şifre değiştirildi.');};
}
async function loadUsers(){
 if(!hasPerm('users.manage'))return;
 [USERS,USER_META]=await Promise.all([api('/api/users'),api('/api/users/meta')]);
 safe('#usersTable',table(['Kullanıcı','Ad Soyad','Rol','Durum','Yetki','İşlem'],USERS.map(u=>`<tr>
  <td><b>${esc(u.username)}</b></td><td>${esc(u.full_name)}</td><td>${esc(u.role)}</td>
  <td>${u.active?'<span class="badge good">AKTİF</span>':'<span class="badge">PASİF</span>'}</td>
  <td>${u.role==='administrator'?'TÜM YETKİLER':`${(u.permissions||[]).length} yetki`}</td>
  <td><button class="btn small" onclick="openUserEditor(${u.id})">Düzenle</button>${u.id!==CURRENT_USER.id?` <button class="btn danger small" onclick="deleteUser(${u.id})">Sil</button>`:''}</td>
 </tr>`)));
}
function roleDefaults(role){return (USER_META?.roles?.[role]||[])}
function permissionsHtml(selected,role){
 const all=USER_META?.permissions||{},set=new Set(selected||[]);
 return `<div class="perm-grid">${Object.entries(all).map(([k,label])=>`<label class="perm-item"><input type="checkbox" name="perm" value="${esc(k)}" ${role==='administrator'||set.has(k)?'checked':''} ${role==='administrator'?'disabled':''}><span>${esc(label)}</span></label>`).join('')}</div>`;
}
async function openUserEditor(id=null){
 if(!USER_META){[USERS,USER_META]=await Promise.all([api('/api/users'),api('/api/users/meta')])}
 const u=id?USERS.find(x=>x.id===id):null,role=u?.role||'viewer',perms=u?.permissions||roleDefaults(role);
 showModal(u?'Kullanıcı Düzenle':'Yeni Kullanıcı',`<form id="userForm" class="formgrid">
  <label>Kullanıcı Adı<input name="username" required value="${esc(u?.username||'')}"></label>
  <label>Ad Soyad<input name="full_name" required value="${esc(u?.full_name||'')}"></label>
  <label>Rol<select name="role" onchange="refreshPermissionEditor(this.value)">${Object.keys(USER_META.roles).map(r=>`<option ${r===role?'selected':''}>${r}</option>`).join('')}</select></label>
  <label>${u?'Yeni Şifre (boş bırakılabilir)':'İlk Şifre'}<input name="password" type="password" ${u?'':'required'} minlength="6"></label>
  <label>Durum<select name="active"><option value="true" ${u?.active!==false?'selected':''}>Aktif</option><option value="false" ${u?.active===false?'selected':''}>Pasif</option></select></label>
  <label>İlk Girişte Şifre Değiştir<select name="must_change_password"><option value="false">Hayır</option><option value="true" ${u?.must_change_password?'selected':''}>Evet</option></select></label>
  <div class="full"><h3>Yetkiler</h3><div id="permissionEditor">${permissionsHtml(perms,role)}</div></div>
  <div class="actions full"><button class="btn success" type="submit">Kaydet</button></div>
 </form>`);
 $('#userForm').dataset.editId=id||'';
 $('#userForm').onsubmit=saveUserForm;
}
function refreshPermissionEditor(role){
 const f=$('#userForm'),id=Number(f?.dataset.editId||0),u=id?USERS.find(x=>x.id===id):null;
 $('#permissionEditor').innerHTML=permissionsHtml(role===u?.role?u.permissions:roleDefaults(role),role);
}
async function saveUserForm(e){
 e.preventDefault();const f=new FormData(e.target),id=Number(e.target.dataset.editId||0);
 const payload={username:f.get('username').trim(),full_name:f.get('full_name').trim(),password:f.get('password')||'',role:f.get('role'),
  permissions:[...document.querySelectorAll('#permissionEditor input[name="perm"]:checked')].map(x=>x.value),
  active:f.get('active')==='true',must_change_password:f.get('must_change_password')==='true'};
 await api(id?'/api/users/'+id:'/api/users',{method:id?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
 closeModal();await loadUsers();alert('Kullanıcı kaydedildi.');
}
async function deleteUser(id){if(!confirm('Bu kullanıcı silinsin mi?'))return;await api('/api/users/'+id,{method:'DELETE'});await loadUsers();}
async function loadAudit(){
 if(!hasPerm('audit.view'))return;
 const q=encodeURIComponent($('#auditSearch')?.value||''),u=encodeURIComponent($('#auditUser')?.value||''),e=encodeURIComponent($('#auditEntity')?.value||'');
 const a=await api(`/api/audit?q=${q}&username=${u}&entity=${e}`);
 const users=[...new Set(a.map(x=>x.username).filter(Boolean))].sort(),entities=[...new Set(a.map(x=>x.entity).filter(Boolean))].sort();
 const us=$('#auditUser'),es=$('#auditEntity');if(us&&us.options.length<=1)us.innerHTML='<option value="">Tüm Kullanıcılar</option>'+users.map(x=>`<option>${esc(x)}</option>`).join('');if(es&&es.options.length<=1)es.innerHTML='<option value="">Tüm Alanlar</option>'+entities.map(x=>`<option>${esc(x)}</option>`).join('');
 safe('#auditTable',table(['Tarih','Kullanıcı','Alan','ID','İşlem','Detay','Eski','Yeni'],a.map(r=>`<tr><td>${esc(r.created_at)}</td><td><b>${esc(r.username||'SYSTEM')}</b></td><td>${esc(r.entity)}</td><td>${esc(r.entity_id||'')}</td><td>${esc(r.action)}</td><td>${esc(r.details||'')}</td><td class="audit-value">${esc(r.old_value||'')}</td><td class="audit-value">${esc(r.new_value||'')}</td></tr>`)));
}
const _pageV715=page;
page=function(id){if(id==='users'&&!hasPerm('users.manage'))return alert('Bu bölüm için yetkiniz yok.');_pageV715(id);if(id==='users')loadUsers();if(id==='audit')loadAudit();}

window.addEventListener('DOMContentLoaded',()=>setTimeout(checkAuth,100));
console.log('RENEW V7.15 AUTH LOG ACTIVE');
/* ================= /V7.15 ================= */

/* ================= V7.16 LAN ACCESS ================= */
async function showLanInfo(){
  try{
    const n=await api('/api/network-info');
    let box=document.getElementById('lanInfoBox');
    if(!box){
      box=document.createElement('div');
      box.id='lanInfoBox';
      box.className='lan-info-box';
      const top=document.querySelector('.top-actions');
      if(top)top.insertBefore(box,top.firstChild);
    }
    if(box)box.innerHTML=`<b>LAN</b><small>${esc(n.lan_url)}</small>`;
  }catch(e){}
}
console.log('RENEW V7.16 LAN ACCESS ACTIVE');
/* ================= /V7.16 ================= */

let CSRF_TOKEN='';
function renewCookie(name){const m=document.cookie.match(new RegExp('(?:^|; )'+name+'=([^;]*)'));return m?decodeURIComponent(m[1]):'';}
const _apiSec=api;
api=async function(url,opt={}){
 const method=(opt.method||'GET').toUpperCase();
 const headers=new Headers(opt.headers||{});
 if(['POST','PUT','PATCH','DELETE'].includes(method)){const t=CSRF_TOKEN||renewCookie('renew_csrf');if(t)headers.set('X-CSRF-Token',t);}
 return _apiSec(url,{...opt,headers});
};
if(document.getElementById('loginForm')){
 document.getElementById('loginForm').onsubmit=async e=>{
  e.preventDefault();const u=document.getElementById('loginUsername').value.trim(),p=document.getElementById('loginPassword').value;
  try{const r=await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});const x=await r.json();if(!r.ok)throw new Error(x.detail||'Giriş başarısız');CURRENT_USER=x;CSRF_TOKEN=x.csrf_token||renewCookie('renew_csrf');document.getElementById('loginOverlay').classList.add('hidden');applyPermissions();await refreshAll();}catch(err){document.getElementById('loginMessage').textContent='❌ '+err.message;}
 };
}
function toggleMobileMenu(){document.body.classList.toggle('mobile-nav-open')}
function closeMobileMenu(){document.body.classList.remove('mobile-nav-open')}
document.addEventListener('click',e=>{if(e.target.closest?.('.nav[data-page]')&&window.innerWidth<=900)closeMobileMenu()});

async function usersRequest(url,opt={}){
 const method=(opt.method||'GET').toUpperCase(),headers=new Headers(opt.headers||{});
 if(['POST','PUT','PATCH','DELETE'].includes(method)){const t=CSRF_TOKEN||renewCookie('renew_csrf');if(t)headers.set('X-CSRF-Token',t);}
 const r=await fetch(url,{...opt,headers,credentials:'same-origin'});let d={};try{d=await r.json()}catch{}
 if(!r.ok)throw new Error(d.detail||`HTTP ${r.status}`);return d;
}
function roleLabel(r){return ({administrator:'Administrator',manager:'Yönetici',editor:'Veri Girişi',viewer:'Görüntüleme'})[r]||r}
function roleBadge(r){return `<span class="role-badge role-${esc(r)}">${esc(roleLabel(r))}</span>`}
async function loadUsers(){if(!hasPerm('users.manage'))return;try{[USERS,USER_META]=await Promise.all([usersRequest('/api/users'),usersRequest('/api/users/meta')]);renderUsersClean()}catch(e){safe('#usersTable',`<div class="error-box">${esc(e.message)}</div>`)}}
function renderUsersClean(){
 const q=String($('#userSearch')?.value||'').toLocaleUpperCase('tr-TR'),rf=$('#userRoleFilter')?.value||'',sf=$('#userStatusFilter')?.value||'';
 const rows=(USERS||[]).filter(u=>{const t=`${u.username} ${u.full_name}`.toLocaleUpperCase('tr-TR');return(!q||t.includes(q))&&(!rf||u.role===rf)&&(!sf||(sf==='active'?u.active:!u.active))});
 const active=(USERS||[]).filter(x=>x.active).length,admins=(USERS||[]).filter(x=>x.active&&x.role==='administrator').length;
 kpis('#usersSummary',[['Toplam Kullanıcı',`${USERS.length} Adet`,'',''],['Aktif',`${active} Adet`,'good',''],['Administrator',`${admins} Adet`,'warn',''],['Pasif',`${USERS.length-active} Adet`,'','']]);
 safe('#usersTable',table(['Kullanıcı','Ad Soyad','Rol','Durum','Yetki','İşlem'],rows.map(u=>`<tr><td><div class="user-cell"><span class="user-avatar">${esc((u.full_name||u.username||'?').charAt(0).toUpperCase())}</span><div><b>${esc(u.username)}</b><small>#${u.id}</small></div></div></td><td><b>${esc(u.full_name)}</b></td><td>${roleBadge(u.role)}</td><td>${u.active?'<span class="status-pill active">● AKTİF</span>':'<span class="status-pill passive">● PASİF</span>'}</td><td>${u.role==='administrator'?'<b>Tüm Yetkiler</b>':`<b>${(u.permissions||[]).length}</b> yetki`}</td><td><div class="row-actions"><button class="btn small" onclick="openUserEditor(${u.id})">✏ Düzenle</button>${u.id!==CURRENT_USER?.id?`<button class="btn danger small" onclick="deleteUser(${u.id})">Sil</button>`:''}</div></td></tr>`)));
}
function permissionsGroupedHtml(selected,role){const g=USER_META?.groups||{},l=USER_META?.permissions||{},s=new Set(selected||[]);return Object.entries(g).map(([name,keys])=>`<div class="perm-group"><div class="perm-group-title"><b>${esc(name)}</b><button type="button" class="mini-link" onclick="togglePermissionGroup(this,true)">Tümünü Seç</button><button type="button" class="mini-link" onclick="togglePermissionGroup(this,false)">Temizle</button></div><div class="perm-grid">${keys.map(k=>`<label class="perm-item"><input type="checkbox" name="perm" value="${esc(k)}" ${role==='administrator'||s.has(k)?'checked':''} ${role==='administrator'?'disabled':''}><span>${esc(l[k]||k)}</span></label>`).join('')}</div></div>`).join('')}
function togglePermissionGroup(btn,v){btn.closest('.perm-group')?.querySelectorAll('input[name="perm"]:not(:disabled)').forEach(x=>x.checked=v)}
async function openUserEditor(id=null){
 try{
  if(!USER_META){[USERS,USER_META]=await Promise.all([usersRequest('/api/users'),usersRequest('/api/users/meta')])}
  const u=id?USERS.find(x=>Number(x.id)===Number(id)):null,role=u?.role||'viewer',perms=u?.permissions||USER_META.roles?.[role]||[];
  showModal(u?'Kullanıcı Düzenle':'Yeni Kullanıcı',`<form id="userFormFinal" class="user-editor"><div class="user-editor-grid"><label><span>Kullanıcı Adı *</span><input name="username" required value="${esc(u?.username||'')}"></label><label><span>Ad Soyad *</span><input name="full_name" required value="${esc(u?.full_name||'')}"></label><label><span>Rol *</span><select name="role" onchange="refreshPermissionEditorFinal(this.value)">${Object.keys(USER_META.roles||{}).map(r=>`<option value="${r}" ${r===role?'selected':''}>${esc(roleLabel(r))}</option>`).join('')}</select></label><label><span>${u?'Yeni Şifre':'İlk Şifre *'}</span><input name="password" type="password" ${u?'':'required'} placeholder="${u?'Değiştirmeyeceksen boş bırak':'En az 10 karakter'}"></label><label><span>Durum</span><select name="active"><option value="true" ${u?.active!==false?'selected':''}>Aktif</option><option value="false" ${u?.active===false?'selected':''}>Pasif</option></select></label><label><span>İlk Girişte Şifre Değiştir</span><select name="must_change_password"><option value="false">Hayır</option><option value="true" ${u?.must_change_password?'selected':''}>Evet</option></select></label></div><div class="permission-box"><div class="permission-head"><div><h3>Yetkiler</h3><p>Kullanıcının erişebileceği bölümleri seçin.</p></div><span id="permRoleNote">${role==='administrator'?'Administrator tüm yetkilere sahiptir.':''}</span></div><div id="permissionEditorFinal">${permissionsGroupedHtml(perms,role)}</div></div><div id="userFormError" class="error-box" style="display:none"></div><div class="actions"><button type="button" class="btn ghost" onclick="closeModal()">Vazgeç</button><button id="userSaveBtn" type="submit" class="btn success">💾 Kaydet</button></div></form>`);
  const f=$('#userFormFinal');f.dataset.editId=id||'';f.addEventListener('submit',saveUserFormFinal)
 }catch(e){alert('Kullanıcı ekranı açılamadı:\n'+e.message)}
}
function refreshPermissionEditorFinal(role){const f=$('#userFormFinal'),id=Number(f?.dataset.editId||0),u=id?USERS.find(x=>Number(x.id)===id):null;const s=(u&&u.role===role)?u.permissions:(USER_META.roles?.[role]||[]);$('#permissionEditorFinal').innerHTML=permissionsGroupedHtml(s,role);$('#permRoleNote').textContent=role==='administrator'?'Administrator tüm yetkilere sahiptir.':''}
async function saveUserFormFinal(e){
 e.preventDefault();const f=new FormData(e.currentTarget),id=Number(e.currentTarget.dataset.editId||0),role=f.get('role'),err=$('#userFormError'),btn=$('#userSaveBtn');
 const payload={username:String(f.get('username')||'').trim(),full_name:String(f.get('full_name')||'').trim(),password:String(f.get('password')||''),role,permissions:role==='administrator'?(USER_META.roles?.administrator||[]):[...e.currentTarget.querySelectorAll('input[name="perm"]:checked')].map(x=>x.value),active:f.get('active')==='true',must_change_password:f.get('must_change_password')==='true'};
 btn.disabled=true;btn.textContent='Kaydediliyor...';err.style.display='none';
 try{await usersRequest(id?`/api/users/${id}`:'/api/users',{method:id?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});closeModal();await loadUsers()}catch(ex){err.style.display='block';err.textContent='❌ '+ex.message}finally{btn.disabled=false;btn.textContent='💾 Kaydet'}
}
async function deleteUser(id){const u=USERS.find(x=>Number(x.id)===Number(id));if(!confirm(`${u?.full_name||'Bu kullanıcı'} silinsin mi?`))return;try{await usersRequest(`/api/users/${id}`,{method:'DELETE'});await loadUsers()}catch(e){alert(e.message)}}


/* ================= V7.19.1 CSRF IMPORT FIX ================= */
const _nativeFetchV7191 = window.fetch.bind(window);
window.fetch = async function(input, init={}){
  try{
    const url = typeof input === 'string' ? input : (input && input.url ? input.url : '');
    const method = String(init.method || 'GET').toUpperCase();
    if(url.startsWith('/api/') && !url.startsWith('/api/auth/login') && ['POST','PUT','PATCH','DELETE'].includes(method)){
      const headers = new Headers(init.headers || {});
      const token = (typeof CSRF_TOKEN!=='undefined' && CSRF_TOKEN) ? CSRF_TOKEN :
                    (typeof renewCookie==='function' ? renewCookie('renew_csrf') : '');
      if(token && !headers.has('X-CSRF-Token')) headers.set('X-CSRF-Token', token);
      init = {...init, headers, credentials: init.credentials || 'same-origin'};
    }
  }catch(e){}
  return _nativeFetchV7191(input, init);
};
console.log('RENEW V7.19.1 CSRF IMPORT FIX ACTIVE');
/* ================= /V7.19.1 ================= */

/* V7.20 — ÖDEME MERKEZİ */
function reloadPaymentCenter(){
  const f=document.getElementById('paymentCenterFrame');
  if(f) f.src='/static/payment_center.html?v=7.20.0&t='+Date.now();
}
function openPaymentCenterNewTab(){
  window.open('/static/payment_center.html?v=7.20.0','_blank','noopener,noreferrer');
}

/* ================= V7.21 MAIL TEMPLATE CENTER ================= */
const MAIL_TPL_KEY='renewpro_mail_templates_v721';
const MAIL_TPL_DEFAULTS=[
 {id:'tahsilat',name:'Kredi Kartı Tahsilat Maili',type:'tahsilat',active:true,subject:'Kredi Kartı Tahsilat Hk.',to:'seval.avseven@cayan.com.tr;muhasebe@cayan.com.tr;tahsilatsorgu@cayan.com.tr',cc:'emirhan.cayan.cayan@ys.renault.com.tr;denizhan.cayan.cayan@ys.renault.com.tr',body:`Merhaba,

Aşağıda bilgileri bulunan müşterimizin kredi kartı tahsilat işlemi için desteğinizi rica ederim.

MÜŞTERİ BİLGİLERİ

Alıcı Adı Soyadı: {alici}
T.C. Kimlik No: {tc}
Cep Telefonu: {cep}

ÖDEME BİLGİLERİ

Çekilecek Tutar: {tutar}
Kredi Kartı Kullanımı: {kart_tipi}

İlgili tutarın belirtilen kredi kartı/kartları üzerinden tahsilat işleminin gerçekleştirilmesini rica ederim.

İyi çalışmalar.`},
 {id:'odeme',name:'Ödeme Bildirimi',type:'odeme',active:true,subject:'{isim} - {tutar} - {banka}',to:'seval.avseven@cayan.com.tr;muhasebe@cayan.com.tr;tahsilatsorgu@cayan.com.tr',cc:'emirhan.cayan.cayan@ys.renault.com.tr;denizhan.cayan.cayan@ys.renault.com.tr',body:`Merhaba,

{isim} isimli müşterimiz tarafından {banka} hesabımıza {tutar} tutarında ödeme gönderimi sağlanmıştır.

Kontrolünü sağlayabilir miyiz?

İyi çalışmalar.`},
 {id:'sigorta',name:'Sigorta İptali',type:'sigorta',active:true,subject:'{plaka} - Sigorta İptali Hk.',to:'muhasebe@cayan.com.tr;Sezen.Tanrisever@kocstellantissigorta.com.tr',cc:'',body:`Merhaba,

{plaka} plakalı aracın sigorta iptal işlemini gerçekleştirebilir misiniz?

İyi çalışmalar,
Saygılarımla.`},
 {id:'devir',name:'Devir İşlemi Maili',type:'devir',active:true,subject:'Çayan Devir Hk.',to:'g.n.d@hotmail.com',cc:'',body:`Merhaba, Çayan Otomotiv adına {yetkili} imza yetkilisidir. Araç bedeli {tutar}'dir. Araç {km}'dedir. {plaka_durumu} İyi çalışmalar.`}
];
const MAIL_TPL_VARS={tahsilat:['alici','tc','cep','tutar','kart_tipi'],odeme:['isim','tutar','banka'],sigorta:['plaka'],devir:['yetkili','tutar','km','plaka_durumu'],custom:['isim','plaka','tutar','banka','tarih']};
let mailTemplates=[],selectedMailTplId=null;
function loadMailTemplates(){
 try{mailTemplates=JSON.parse(localStorage.getItem(MAIL_TPL_KEY)||'null')||structuredClone(MAIL_TPL_DEFAULTS)}catch(e){mailTemplates=JSON.parse(JSON.stringify(MAIL_TPL_DEFAULTS))}
 renderMailTemplateList();
}
function persistMailTemplates(){localStorage.setItem(MAIL_TPL_KEY,JSON.stringify(mailTemplates));}
function renderMailTemplateList(){
 const box=document.getElementById('mailTplList'); if(!box)return;
 const q=(document.getElementById('mailTplSearch')?.value||'').toLocaleLowerCase('tr-TR');
 const arr=mailTemplates.filter(x=>(x.name+' '+x.type).toLocaleLowerCase('tr-TR').includes(q));
 document.getElementById('mailTplCount').textContent=mailTemplates.length;
 box.innerHTML=arr.map(x=>`<button class="mailtpl-item ${x.id===selectedMailTplId?'active':''}" onclick="selectMailTemplate('${x.id}')"><span><b>${esc(x.name)}</b><small>${x.active?'Aktif':'Pasif'} • ${esc(x.subject||'Konu yok')}</small></span><span class="mailtpl-kind">${esc(x.type)}</span></button>`).join('')||'<div class="empty-state" style="padding:35px 10px">Şablon bulunamadı.</div>';
}
function selectMailTemplate(id){
 selectedMailTplId=id; const x=mailTemplates.find(t=>t.id===id); if(!x)return;
 document.getElementById('mailTplEmpty').style.display='none';document.getElementById('mailTplForm').style.display='';
 document.getElementById('mailTplName').value=x.name||'';document.getElementById('mailTplType').value=x.type||'custom';document.getElementById('mailTplSubject').value=x.subject||'';
 document.getElementById('mailTplTo').value=x.to||'';document.getElementById('mailTplCc').value=x.cc||'';document.getElementById('mailTplActive').value=String(x.active!==false);document.getElementById('mailTplBody').value=x.body||'';
 document.getElementById('mailTplEditorTitle').textContent=x.name||'Şablon Düzenle';renderMailTplVars();renderMailTplPreview();renderMailTemplateList();
}
function updateMailTemplateDraft(){
 const x=mailTemplates.find(t=>t.id===selectedMailTplId);if(!x)return;
 x.name=document.getElementById('mailTplName').value;x.type=document.getElementById('mailTplType').value;x.subject=document.getElementById('mailTplSubject').value;x.to=document.getElementById('mailTplTo').value;x.cc=document.getElementById('mailTplCc').value;x.active=document.getElementById('mailTplActive').value==='true';x.body=document.getElementById('mailTplBody').value;
 document.getElementById('mailTplEditorTitle').textContent=x.name||'Şablon Düzenle';renderMailTplVars();renderMailTplPreview();renderMailTemplateList();
}
function newMailTemplate(){const id='custom_'+Date.now();mailTemplates.push({id,name:'Yeni Mail Şablonu',type:'custom',active:true,subject:'',to:'',cc:'',body:'Merhaba,\\n\\n{isim}\\n\\nİyi çalışmalar.'});selectMailTemplate(id)}
function deleteMailTemplate(){const x=mailTemplates.find(t=>t.id===selectedMailTplId);if(!x)return;if(['tahsilat','odeme','sigorta','devir'].includes(x.id)){alert('Sistem şablonu silinemez. İsterseniz Pasif yapabilir veya içeriğini değiştirebilirsiniz.');return}if(!confirm('Bu şablon silinsin mi?'))return;mailTemplates=mailTemplates.filter(t=>t.id!==selectedMailTplId);selectedMailTplId=null;persistMailTemplates();document.getElementById('mailTplForm').style.display='none';document.getElementById('mailTplEmpty').style.display='';renderMailTemplateList()}
function saveMailTemplates(){updateMailTemplateDraft();persistMailTemplates();const f=document.getElementById('paymentCenterFrame');if(f)f.contentWindow?.postMessage({type:'renew-mail-templates-updated'},location.origin);alert('Mail şablonları kaydedildi. Ödeme Merkezi anında güncellendi.')}
function resetMailTemplates(){if(!confirm('Mail şablonları varsayılan metinlere dönsün mü?'))return;mailTemplates=JSON.parse(JSON.stringify(MAIL_TPL_DEFAULTS));persistMailTemplates();selectedMailTplId='tahsilat';selectMailTemplate('tahsilat')}
function renderMailTplVars(){const x=mailTemplates.find(t=>t.id===selectedMailTplId);if(!x)return;const vars=MAIL_TPL_VARS[x.type]||MAIL_TPL_VARS.custom;document.getElementById('mailTplVars').innerHTML=vars.map(v=>`<button onclick="insertMailTplVar('${v}')">{${v}}</button>`).join('')}
function insertMailTplVar(v){const a=document.getElementById('mailTplBody');const s=a.selectionStart||0,e=a.selectionEnd||0;a.value=a.value.slice(0,s)+'{'+v+'}'+a.value.slice(e);a.focus();a.selectionStart=a.selectionEnd=s+v.length+2;updateMailTemplateDraft()}
function mailTplSampleVars(){return{alici:'Hasan Hüseyin Sürmeli',tc:'12345678901',cep:'0549 000 00 00',tutar:'1.250.000 TL',kart_tipi:'Tek Kredi Kartı',isim:'Örnek Müşteri',banka:'T.C. Ziraat Bankası A.Ş.',plaka:'33 ABC 123',yetkili:'Onur İpek',km:'35.000 KM',plaka_durumu:'Plaka aynı kalacaktır.',tarih:new Date().toLocaleDateString('tr-TR')}}
function applyMailTplText(t,vars){return String(t||'').replace(/\{([a-zA-Z0-9_]+)\}/g,(m,k)=>vars[k]??m)}
function renderMailTplPreview(){const x=mailTemplates.find(t=>t.id===selectedMailTplId);if(!x)return;document.getElementById('mailTplPreview').textContent='KONU: '+applyMailTplText(x.subject,mailTplSampleVars())+'\\nALICI: '+(x.to||'-')+'\\nCC: '+(x.cc||'-')+'\\n\\n'+applyMailTplText(x.body,mailTplSampleVars())}
function copyMailTemplatePreview(){navigator.clipboard.writeText(document.getElementById('mailTplPreview').textContent)}
document.addEventListener('DOMContentLoaded',loadMailTemplates);
/* ================= /V7.21 ================= */

function syncPaymentFrameHeight(){
  const f=document.getElementById('paymentCenterFrame');if(!f)return;
  try{const d=f.contentDocument||f.contentWindow?.document;if(!d)return;const h=Math.max(d.body?.scrollHeight||0,d.documentElement?.scrollHeight||0,680);f.style.height=Math.min(Math.max(h+8,680),1400)+'px'}catch(e){}
}
document.addEventListener('DOMContentLoaded',()=>{const f=document.getElementById('paymentCenterFrame');if(f)f.addEventListener('load',()=>{syncPaymentFrameHeight();setTimeout(syncPaymentFrameHeight,300);setTimeout(syncPaymentFrameHeight,900)})});
window.addEventListener('resize',syncPaymentFrameHeight);

/* ================= V7.23 PRO MAIL STUDIO ================= */
const MAIL_CUSTOM_VAR_KEY='renewpro_mail_custom_vars_v723';
const MAIL_AUTHORITY_KEY='renewpro_devir_authorities_v723';
const MAIL_GLOBAL_VARS=[
 ['isim','Müşteri / kişi adı'],['alici','Alıcı adı soyadı'],['tc','T.C. kimlik no'],['cep','Cep telefonu'],
 ['plaka','Araç plakası'],['marka','Marka'],['model','Model'],['versiyon','Versiyon'],['model_yili','Model yılı'],
 ['km','Kilometre'],['sasi','Şasi no'],['renk','Renk'],['tutar','Tutar'],['banka','Banka'],['iban','IBAN'],
 ['kart_tipi','Kart kullanım tipi'],['taksit','Taksit'],['oran','Komisyon oranı'],['net_tutar','Net tutar'],
 ['tarih','Tarih'],['saat','Saat'],['yetkili','Yetkili adı'],['yetkili_unvan','Yetkili unvanı'],['yetkili_tel','Yetkili telefonu'],
 ['plaka_durumu','Plaka durumu'],['not','Not']
];
let customMailVars=[];
let authorityPeople=[];
function loadProMailStudioData(){
 try{customMailVars=JSON.parse(localStorage.getItem(MAIL_CUSTOM_VAR_KEY)||'[]')}catch(e){customMailVars=[]}
 try{authorityPeople=JSON.parse(localStorage.getItem(MAIL_AUTHORITY_KEY)||'null')||[
  {id:'onur',name:'Onur İpek',title:'İmza Yetkilisi',phone:''},
  {id:'hasan',name:'Hasan Hüseyin Sürmeli',title:'Yetkili Personel',phone:''}
 ]}catch(e){authorityPeople=[]}
}
function saveProMailStudioData(){localStorage.setItem(MAIL_CUSTOM_VAR_KEY,JSON.stringify(customMailVars));localStorage.setItem(MAIL_AUTHORITY_KEY,JSON.stringify(authorityPeople))}
function allVarsForCurrentTemplate(){
 const x=mailTemplates.find(t=>t.id===selectedMailTplId),type=x?.type||'custom';
 const typeKeys=MAIL_TPL_VARS[type]||[];
 const map=new Map(MAIL_GLOBAL_VARS.map(v=>[v[0],v[1]]));
 typeKeys.forEach(k=>{if(!map.has(k))map.set(k,k)});
 customMailVars.forEach(v=>map.set(v.key,v.label||v.key));
 return [...map.entries()];
}
function renderMailTplVars(){
 const box=document.getElementById('mailTplVars');if(!box)return;
 box.innerHTML=allVarsForCurrentTemplate().map(([k,l])=>`<button type="button" class="var-chip" title="${esc(l)}" onclick="insertMailTplVar('${esc(k)}')">{${esc(k)}}</button>`).join('');
 renderCustomVarRows();renderAuthorityManager();
}
function renderCustomVarRows(){
 const b=document.getElementById('mailTplCustomVars');if(!b)return;
 b.innerHTML=customMailVars.map((v,i)=>`<div class="custom-var-row"><input value="${esc(v.key)}" placeholder="degisken_adi" onchange="updateCustomMailVar(${i},'key',this.value)"><input value="${esc(v.label||'')}" placeholder="Açıklama" onchange="updateCustomMailVar(${i},'label',this.value)"><button type="button" class="btn danger small" onclick="removeCustomMailVar(${i})">Sil</button></div>`).join('');
}
function addCustomMailVariable(){customMailVars.push({key:'yeni_degisken',label:'Yeni değişken'});saveProMailStudioData();renderMailTplVars()}
function updateCustomMailVar(i,k,v){if(k==='key')v=String(v).trim().toLocaleLowerCase('tr-TR').replace(/\s+/g,'_').replace(/[^a-z0-9_ğüşöçıİ]/gi,'');customMailVars[i][k]=v;saveProMailStudioData();renderMailTplPreview()}
function removeCustomMailVar(i){customMailVars.splice(i,1);saveProMailStudioData();renderMailTplVars();renderMailTplPreview()}
function renderAuthorityManager(){
 const x=mailTemplates.find(t=>t.id===selectedMailTplId),box=document.getElementById('devirAuthorityBox');if(!box)return;
 const isDevir=x?.type==='devir';box.style.display=isDevir?'':'none';if(!isDevir)return;
 const list=document.getElementById('authorityPeopleList');
 list.innerHTML=authorityPeople.map((a,i)=>`<div class="authority-row"><input value="${esc(a.name||'')}" placeholder="Ad Soyad" onchange="updateAuthority(${i},'name',this.value)"><input class="authority-role" value="${esc(a.title||'')}" placeholder="Unvan / görev" onchange="updateAuthority(${i},'title',this.value)"><input value="${esc(a.phone||'')}" placeholder="Telefon" onchange="updateAuthority(${i},'phone',this.value)"><button type="button" class="btn danger small" onclick="removeAuthority(${i})">Sil</button></div>`).join('');
 const sel=document.getElementById('authorityPreviewSelect'),old=sel.value;
 sel.innerHTML=authorityPeople.map((a,i)=>`<option value="${i}">${esc(a.name||'İsimsiz Yetkili')} — ${esc(a.title||'')}</option>`).join('');
 if(old && sel.querySelector(`option[value="${old}"]`))sel.value=old;
}
function addAuthorityPerson(){authorityPeople.push({id:'auth_'+Date.now(),name:'Yeni Yetkili',title:'İmza Yetkilisi',phone:''});saveProMailStudioData();renderAuthorityManager();renderMailTplPreview()}
function updateAuthority(i,k,v){authorityPeople[i][k]=v;saveProMailStudioData();renderAuthorityManager();renderMailTplPreview()}
function removeAuthority(i){if(authorityPeople.length<=1){alert('En az bir yetkili kişi kalmalıdır.');return}authorityPeople.splice(i,1);saveProMailStudioData();renderAuthorityManager();renderMailTplPreview()}
function mailTplSampleVars(){
 const now=new Date(),idx=Number(document.getElementById('authorityPreviewSelect')?.value||0),a=authorityPeople[idx]||authorityPeople[0]||{};
 const v={alici:'Hasan Hüseyin Sürmeli',tc:'12345678901',cep:'0549 000 00 00',tutar:'1.250.000 TL',kart_tipi:'Tek Kredi Kartı',
 isim:'Örnek Müşteri',banka:'T.C. Ziraat Bankası A.Ş.',iban:'TR00 0000 0000 0000 0000 0000 00',plaka:'33 ABC 123',
 marka:'Renault',model:'Megane Sedan',versiyon:'Touch 1.3 TCe EDC',model_yili:'2025',km:'35.000 KM',sasi:'VF1XXXXXXXXXXXXXX',
 renk:'Beyaz',taksit:'6 Taksit',oran:'%7,5',net_tutar:'1.343.750 TL',yetkili:a.name||'Yetkili Personel',
 yetkili_unvan:a.title||'İmza Yetkilisi',yetkili_tel:a.phone||'05XX XXX XX XX',plaka_durumu:'Plaka aynı kalacaktır.',
 tarih:now.toLocaleDateString('tr-TR'),saat:now.toLocaleTimeString('tr-TR',{hour:'2-digit',minute:'2-digit'}),not:'Örnek açıklama'};
 customMailVars.forEach(x=>v[x.key]='['+(x.label||x.key)+']');return v;
}
function renderMailTplPreview(){
 const x=mailTemplates.find(t=>t.id===selectedMailTplId);if(!x)return;
 const v=mailTplSampleVars();
 const subject=applyMailTplText(x.subject,v),body=applyMailTplText(x.body,v);
 document.getElementById('mailTplPreview').textContent=`KONU: ${subject}\nALICI: ${x.to||'-'}\nCC: ${x.cc||'-'}\n\n${body}`.replace(/\r\n/g,'\n').replace(/[ \t]+\n/g,'\n');
}
function updateMailTemplateDraft(){
 const x=mailTemplates.find(t=>t.id===selectedMailTplId);if(!x)return;
 x.name=document.getElementById('mailTplName').value;
 x.type=(document.getElementById('mailTplType').value||'custom').trim();
 x.subject=document.getElementById('mailTplSubject').value;x.to=document.getElementById('mailTplTo').value;x.cc=document.getElementById('mailTplCc').value;x.active=document.getElementById('mailTplActive').value==='true';x.body=document.getElementById('mailTplBody').value;
 document.getElementById('mailTplEditorTitle').textContent=x.name||'Şablon Düzenle';renderMailTplVars();renderMailTplPreview();renderMailTemplateList();
}
document.addEventListener('DOMContentLoaded',()=>{loadProMailStudioData();setTimeout(()=>{if(selectedMailTplId)renderMailTplVars()},50)});
/* ================= /V7.23 ================= */

/* ================= V7.25 CENTRAL MAIL CONFIG ================= */
let MAIL_CONFIG={templates:[],custom_vars:[],authorities:[]};
let mailSaveTimer=null;
async function mailConfigRequest(url,opt={}){
 const method=(opt.method||'GET').toUpperCase(),headers=new Headers(opt.headers||{});
 if(['POST','PUT','PATCH','DELETE'].includes(method)){const t=CSRF_TOKEN||renewCookie('renew_csrf');if(t)headers.set('X-CSRF-Token',t)}
 const r=await fetch(url,{...opt,headers,credentials:'same-origin'});let d={};try{d=await r.json()}catch{}
 if(!r.ok)throw new Error(d.detail||`HTTP ${r.status}`);return d
}
async function loadMailTemplates(){
 try{
   MAIL_CONFIG=await mailConfigRequest('/api/mail-config');
   mailTemplates=MAIL_CONFIG.templates||[];customMailVars=MAIL_CONFIG.custom_vars||[];authorityPeople=MAIL_CONFIG.authorities||[];
   renderMailTemplateList();if(selectedMailTplId&&mailTemplates.some(x=>x.id===selectedMailTplId))selectMailTemplate(selectedMailTplId);
   setMailSaveState('Kayıtlı','');
 }catch(e){setMailSaveState('Yüklenemedi','error')}
}
function setMailSaveState(t,c){const x=document.getElementById('mailSaveState');if(x){x.textContent=t;x.className='save-state '+(c||'')}}
function scheduleMailConfigSave(){
 setMailSaveState('Kaydediliyor…','saving');clearTimeout(mailSaveTimer);mailSaveTimer=setTimeout(()=>saveMailTemplates(false),450)
}
async function saveMailTemplates(showMessage=false){
 try{
   updateMailTemplateDraft(false);
   MAIL_CONFIG={templates:mailTemplates,custom_vars:customMailVars,authorities:authorityPeople};
   MAIL_CONFIG=await mailConfigRequest('/api/mail-config',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(MAIL_CONFIG)});
   mailTemplates=MAIL_CONFIG.templates||[];customMailVars=MAIL_CONFIG.custom_vars||[];authorityPeople=MAIL_CONFIG.authorities||[];
   setMailSaveState('Kayıtlı','');
   const f=document.getElementById('paymentCenterFrame');if(f?.contentWindow)f.contentWindow.postMessage({type:'renew-mail-config-updated'},location.origin);
   if(showMessage)alert('Mail Studio kaydedildi ve Ödeme Merkezi güncellendi.');
 }catch(e){setMailSaveState('Kayıt Hatası','error');if(showMessage)alert('Kaydedilemedi:\n'+e.message)}
}
async function resetMailTemplates(){
 if(!confirm('Tüm mail şablonları ve devir yetkilileri varsayılanlara dönsün mü?'))return;
 try{MAIL_CONFIG=await mailConfigRequest('/api/mail-config/reset',{method:'POST'});mailTemplates=MAIL_CONFIG.templates;customMailVars=MAIL_CONFIG.custom_vars;authorityPeople=MAIL_CONFIG.authorities;selectedMailTplId=mailTemplates[0]?.id||null;renderMailTemplateList();if(selectedMailTplId)selectMailTemplate(selectedMailTplId);setMailSaveState('Kayıtlı','');const f=document.getElementById('paymentCenterFrame');f?.contentWindow?.postMessage({type:'renew-mail-config-updated'},location.origin)}catch(e){alert(e.message)}
}
function renderMailTemplateList(){
 const box=document.getElementById('mailTplList');if(!box)return;
 const q=(document.getElementById('mailTplSearch')?.value||'').toLocaleLowerCase('tr-TR'),mf=document.getElementById('mailModuleFilter')?.value||'';
 const arr=(mailTemplates||[]).filter(x=>(!mf||x.module===mf)&&((x.name+' '+x.type+' '+x.module).toLocaleLowerCase('tr-TR').includes(q)));
 document.getElementById('mailTplCount').textContent=mailTemplates.length;
 const ml={tahsilat:'Kredi Kartı',odeme:'Ödeme',sigorta:'Sigorta',devir:'Devir',general:'Genel'};
 box.innerHTML=arr.map(x=>`<button class="mailtpl-item ${x.id===selectedMailTplId?'active':''}" onclick="selectMailTemplate('${x.id}')"><span><b>${esc(x.name)}</b><small>${esc(x.type||'Etiketsiz')} • ${x.active?'Aktif':'Pasif'}</small></span><span class="mailtpl-kind">${esc(ml[x.module]||x.module||'Genel')}</span></button>`).join('')||'<div class="empty-state" style="padding:35px 10px">Şablon bulunamadı.</div>'
}
function selectMailTemplate(id){
 selectedMailTplId=id;const x=mailTemplates.find(t=>t.id===id);if(!x)return;
 document.getElementById('mailTplEmpty').style.display='none';document.getElementById('mailTplForm').style.display='';
 document.getElementById('mailTplName').value=x.name||'';document.getElementById('mailTplModule').value=x.module||'general';document.getElementById('mailTplType').value=x.type||'';
 document.getElementById('mailTplSubject').value=x.subject||'';document.getElementById('mailTplTo').value=x.to||'';document.getElementById('mailTplCc').value=x.cc||'';document.getElementById('mailTplActive').value=String(x.active!==false);document.getElementById('mailTplBody').value=x.body||'';
 renderMailTplVars();renderMailTplPreview();renderMailTemplateList()
}
function updateMailTemplateDraft(doSave=true){
 const x=mailTemplates.find(t=>t.id===selectedMailTplId);if(!x)return;
 x.name=document.getElementById('mailTplName')?.value||x.name;x.module=document.getElementById('mailTplModule')?.value||x.module||'general';x.type=(document.getElementById('mailTplType')?.value||'').trim();
 x.subject=document.getElementById('mailTplSubject')?.value||'';x.to=document.getElementById('mailTplTo')?.value||'';x.cc=document.getElementById('mailTplCc')?.value||'';x.active=document.getElementById('mailTplActive')?.value==='true';x.body=document.getElementById('mailTplBody')?.value||'';
 renderMailTplVars();renderMailTplPreview();renderMailTemplateList();if(doSave)scheduleMailConfigSave()
}
function newMailTemplate(){
 const id='tpl_'+Date.now();mailTemplates.push({id,name:'Yeni Mail Şablonu',module:'general',type:'Özel Şablon',active:true,subject:'',to:'',cc:'',body:'Merhaba,\n\n{isim}\n\nİyi çalışmalar.'});selectMailTemplate(id);scheduleMailConfigSave()
}
function deleteMailTemplate(){
 const x=mailTemplates.find(t=>t.id===selectedMailTplId);if(!x)return;
 if(!confirm(`"${x.name}" şablonu silinsin mi?`))return;
 mailTemplates=mailTemplates.filter(t=>t.id!==selectedMailTplId);selectedMailTplId=null;document.getElementById('mailTplForm').style.display='none';document.getElementById('mailTplEmpty').style.display='';renderMailTemplateList();scheduleMailConfigSave()
}
function addCustomMailVariable(){customMailVars.push({key:'yeni_degisken',label:'Yeni değişken'});renderMailTplVars();scheduleMailConfigSave()}
function updateCustomMailVar(i,k,v){if(k==='key')v=String(v).trim().toLocaleLowerCase('tr-TR').replace(/\s+/g,'_').replace(/[^a-z0-9_ğüşöçıİ]/gi,'');customMailVars[i][k]=v;renderMailTplVars();renderMailTplPreview();scheduleMailConfigSave()}
function removeCustomMailVar(i){customMailVars.splice(i,1);renderMailTplVars();renderMailTplPreview();scheduleMailConfigSave()}
function renderAuthorityManager(){
 const x=mailTemplates.find(t=>t.id===selectedMailTplId),box=document.getElementById('devirAuthorityBox');if(!box)return;
 const show=x?.module==='devir';box.style.display=show?'':'none';if(!show)return;
 document.getElementById('authorityPeopleList').innerHTML=authorityPeople.map((a,i)=>`<div class="authority-row"><input value="${esc(a.name||'')}" placeholder="Ad Soyad" oninput="updateAuthority(${i},'name',this.value)"><input value="${esc(a.title||'')}" placeholder="Unvan / Görev" oninput="updateAuthority(${i},'title',this.value)"><input value="${esc(a.phone||'')}" placeholder="Telefon" oninput="updateAuthority(${i},'phone',this.value)"><button type="button" class="btn danger small" onclick="removeAuthority(${i})">Sil</button></div>`).join('');
 const s=document.getElementById('authorityPreviewSelect'),old=s.value;s.innerHTML=authorityPeople.map((a,i)=>`<option value="${i}">${esc(a.name||'İsimsiz')} — ${esc(a.title||'')}</option>`).join('');if([...s.options].some(o=>o.value===old))s.value=old
}
function addAuthorityPerson(){authorityPeople.push({id:'auth_'+Date.now(),name:'Yeni Yetkili',title:'İmza Yetkilisi',phone:''});renderAuthorityManager();renderMailTplPreview();scheduleMailConfigSave()}
function updateAuthority(i,k,v){authorityPeople[i][k]=v;renderMailTplPreview();scheduleMailConfigSave()}
function removeAuthority(i){if(authorityPeople.length<=1)return alert('En az bir yetkili kalmalıdır.');authorityPeople.splice(i,1);renderAuthorityManager();renderMailTplPreview();scheduleMailConfigSave()}
function allVarsForCurrentTemplate(){
 const x=mailTemplates.find(t=>t.id===selectedMailTplId),module=x?.module||'general';
 const moduleMap={tahsilat:['alici','tc','cep','tutar','kart_tipi','taksit','oran','net_tutar'],odeme:['isim','tutar','banka','iban'],sigorta:['plaka','marka','model'],devir:['yetkili','yetkili_unvan','yetkili_tel','tutar','km','plaka_durumu','plaka','marka','model'],general:[]};
 const map=new Map(MAIL_GLOBAL_VARS.map(v=>[v[0],v[1]]));(moduleMap[module]||[]).forEach(k=>{if(!map.has(k))map.set(k,k)});customMailVars.forEach(v=>map.set(v.key,v.label||v.key));return [...map.entries()]
}
document.addEventListener('DOMContentLoaded',()=>setTimeout(()=>{if(CURRENT_USER)loadMailTemplates()},150));
/* ================= /V7.24 ================= */

/* V7.24 payment center fixed viewport: prevents layout jumps */
syncPaymentFrameHeight=function(){};
const _pageV724=page;
page=function(id){_pageV724(id);if(id==='payment-center'){const f=document.getElementById('paymentCenterFrame');if(f){f.style.height='calc(100vh - 215px)';setTimeout(()=>{try{f.contentWindow?.postMessage({type:'renew-mail-config-updated'},location.origin)}catch(e){}},150)}}};

/* ================= V7.25 MAIL STUDIO RELIABILITY ================= */
async function loadMailTemplatesV725(){
 const state=document.getElementById('mailSaveState');
 try{
   if(state){state.textContent='Yükleniyor…';state.className='save-state saving'}
   const cfg=await mailConfigRequest('/api/mail-config');
   MAIL_CONFIG=cfg;mailTemplates=cfg.templates||[];customMailVars=cfg.custom_vars||[];authorityPeople=cfg.authorities||[];
   renderMailTemplateList();
   if(!selectedMailTplId && mailTemplates.length) selectedMailTplId=mailTemplates[0].id;
   if(selectedMailTplId && mailTemplates.some(x=>x.id===selectedMailTplId)) selectMailTemplate(selectedMailTplId);
   setMailSaveState('Kayıtlı','');
 }catch(e){
   console.error('Mail Studio:',e);
   setMailSaveState('Yüklenemedi','error');
   const empty=document.getElementById('mailTplEmpty');
   if(empty){empty.style.display='';empty.innerHTML='<b>Mail Studio yüklenemedi</b><p>'+esc(e.message||'Sunucu bağlantısı kurulamadı.')+'</p><button class="btn primary" onclick="loadMailTemplatesV725()">Tekrar Dene</button>'}
 }
}
loadMailTemplates=loadMailTemplatesV725;
async function saveMailTemplatesV725(showMessage=false){
 try{
   updateMailTemplateDraft(false);
   MAIL_CONFIG=await mailConfigRequest('/api/mail-config',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({templates:mailTemplates,custom_vars:customMailVars,authorities:authorityPeople})});
   mailTemplates=MAIL_CONFIG.templates||[];customMailVars=MAIL_CONFIG.custom_vars||[];authorityPeople=MAIL_CONFIG.authorities||[];
   setMailSaveState('Kayıtlı','');
   const f=document.getElementById('paymentCenterFrame');
   if(f?.contentWindow)f.contentWindow.postMessage({type:'renew-mail-config-updated'},location.origin);
   if(showMessage)alert('Kaydedildi. Ödeme Merkezi mail seçenekleri güncellendi.');
 }catch(e){setMailSaveState('Kayıt Hatası','error');if(showMessage)alert('Kaydedilemedi:\n'+e.message)}
}
saveMailTemplates=saveMailTemplatesV725;
const _pageV725=page;
page=function(id){
 _pageV725(id);
 if(id==='mail-templates'&&CURRENT_USER)loadMailTemplatesV725();
};
document.addEventListener('DOMContentLoaded',()=>setTimeout(()=>{
 if(CURRENT_USER&&document.getElementById('mail-templates')?.classList.contains('active'))loadMailTemplatesV725();
},300));
/* ================= /V7.25 ================= */

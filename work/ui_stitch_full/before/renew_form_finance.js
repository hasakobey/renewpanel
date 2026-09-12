/* Live presentation; all stock/sale amounts come from the existing server calculator. */
(()=>{'use strict';const format=n=>Number(n||0).toLocaleString('tr-TR',{style:'currency',currency:'TRY',maximumFractionDigits:2});
let active=null;
function mount(){const body=document.getElementById('modalBody');if(!body)return;
 if(active&&!body.contains(active.panel)){active.controller?.abort();clearTimeout(active.timer);active.dispose?.();active=null}
 if(active)return;
 const acq=body.querySelector('#acqFormV710'),sections=body.querySelectorAll('.rfs-section');if(!sections.length)return;
 const section=sections[sections.length-1],grid=section.querySelector('.renew-form-grid,.acq-cost-grid');if(!grid)return;
 const kind=acq?'acquisition':body.querySelector('#f_sale_price')?'sale':'stock';
 const wrap=document.createElement('div');wrap.className='rff-layout';grid.before(wrap);const left=document.createElement('div');left.className='rff-inputs';left.append(grid);wrap.append(left);
 const panel=document.createElement('div');panel.className='rff-panel';panel.setAttribute('role','region');panel.setAttribute('aria-label','Canlı finansal analiz');
 panel.innerHTML='<div class="rff-heading"><b>▥ Canlı Finansal Analiz</b><span>ÖNİZLEME</span></div><p class="rff-status" role="status"></p><div class="rff-results" hidden><div class="rff-total"><span>Toplam Maliyet</span><strong data-value="total"></strong></div><dl></dl><div class="rff-profit"><span></span><strong></strong><small></small><div class="rff-meter" aria-hidden="true"><i></i></div></div><p class="rff-footnote"></p></div>';
 wrap.append(panel);const breakdown=document.createElement('div');breakdown.className='rff-fixed';left.append(breakdown);
 const rule=document.createElement('p');rule.className='rff-rule';left.append(rule);
 active={panel,controller:null,timer:null,version:0};const session=active;
 const status=panel.querySelector('.rff-status'),results=panel.querySelector('.rff-results'),dl=panel.querySelector('dl'),profitBox=panel.querySelector('.rff-profit');
 function rows(items){dl.replaceChildren();items.forEach(([label,value])=>{const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=label;dd.textContent=value;dl.append(dt,dd)})}
 function ready(){status.textContent='Güncel form değerleri • Kaydedilmedi';results.hidden=false;panel.classList.remove('rff-pending');}
 if(acq){
  breakdown.hidden=true;rule.textContent='Aylık alım maliyeti, mevcut kayıt mantığıyla alış fiyatı + girilen masraftır. Stok/satış giderleri bu toplama otomatik eklenmez.';
  const total=acq.querySelector('#acqLiveTotal');
  function acquisition(){if(active!==session||!total)return;ready();panel.querySelector('[data-value=total]').textContent=total.textContent;rows([['Alış Fiyatı',format(acqMoneyParse(acq.elements.purchase_price.value))],['Ek Masraf',format(acqMoneyParse(acq.elements.expense.value))]]);profitBox.hidden=true;panel.querySelector('.rff-footnote').textContent='Seçili ayın alım kaydı • Satış fiyatı olmadığı için kâr hesaplanmaz.'}
  const observer=new MutationObserver(acquisition);observer.observe(total,{childList:true,characterData:true,subtree:true});acq.addEventListener('input',acquisition);session.dispose=()=>{observer.disconnect();acq.removeEventListener('input',acquisition)};acquisition();return;
 }
 const field=key=>body.querySelector('#f_'+key)?.value||'';
 function queue(){if(active!==session)return;session.controller?.abort();clearTimeout(session.timer);session.version++;panel.classList.add('rff-pending');results.hidden=true;breakdown.replaceChildren();rule.textContent='';status.textContent='Hesaplanıyor…';const version=session.version;
  session.timer=setTimeout(()=>update(version),280);
 }
 async function update(version){
  if(active!==session||!panel.isConnected)return;
  const payload=kind==='sale'?renewSalePayload():Object.fromEntries(stockFieldsNow().map(([key,,type])=>[key,type==='number'?(MONEY_KEYS.has(key)?parseMoney(field(key)):Number(field(key)||0)):field(key)]));
  payload.month=month();
  if(!payload.purchase_type||!payload.purchase_date||!payload.purchase_price||(kind==='sale'&&!payload.sale_date)){status.textContent='Alış bedeli, alım türü ve tarihleri girin; analiz burada güncellenecek.';return}
  session.controller=new AbortController();
  try{
   const response=await api('/api/'+(kind==='sale'?'sales':'stocks')+'/financial-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal:session.controller.signal});
   if(active!==session||version!==session.version||!panel.isConnected)return;
   ready();const c=response.calc;panel.querySelector('[data-value=total]').textContent=format(c.total_cost);
   rows([['Alış Bedeli',format(payload.purchase_price)],['Sabit Giderler',format(response.fixed_expense)],...(kind==='sale'?[['Ek Masraf',format(c.extra_expense)]]:[]),['SKS',c.sks_days+' gün'],['SKS Finansman',format(c.sks_finance)],['Günlük SKS Etkisi',format(response.daily_finance)]]);
   if(kind==='sale'){rows([['Alış Bedeli',format(payload.purchase_price)],['Sabit Giderler',format(response.fixed_expense)],['Ek Masraf',format(c.extra_expense)],['SKS Finansman ('+c.sks_days+' gün)',format(c.sks_finance)],['Brüt Kâr',format(c.gross_profit)],['Ek Gelirler',format(c.extra_income)],['Performans Kârı',format(c.performance_profit)]]);}
   const selling=kind==='sale'?payload.sale_price:payload.list_price;profitBox.hidden=!selling;
   profitBox.querySelector('span').textContent=kind==='sale'?'Net Kâr':'Tahmini Net Kâr';profitBox.querySelector('strong').textContent=format(response.profit);
   profitBox.querySelector('small').textContent=response.margin===null?'':'Net marj: %'+(response.margin*100).toLocaleString('tr-TR',{maximumFractionDigits:2});
   profitBox.classList.toggle('rff-loss',response.profit<0);profitBox.querySelector('i').style.width=Math.min(100,Math.abs((response.margin||0)*100))+'%';
   panel.querySelector('.rff-footnote').textContent='Hesap tarihi: '+response.as_of+' • Kayıt ve Excel ile aynı hesaplama motoru.';
   breakdown.replaceChildren();const heading=document.createElement('div');heading.className='rff-fixed-heading';const title=document.createElement('b'),sum=document.createElement('strong');title.textContent='Sabit Gider Dökümü';sum.textContent=format(response.fixed_expense);heading.append(title,sum);breakdown.append(heading);
   const tiles=document.createElement('div');tiles.className='rff-expenses';[['notary','Noter'],['expertise','Ekspertiz'],['control150','150 Nokta'],['insurance','Sigorta']].forEach(([key,label])=>{const tile=document.createElement('div'),name=document.createElement('span'),value=document.createElement('b');name.textContent=label;value.textContent=format(response.expenses[key]);tile.append(name,value);tiles.append(tile)});breakdown.append(tiles);
   rule.textContent=(response.apply_fixed?'Noter ve sigorta, bu alım türünün kuralına göre uygulanır.':'Bu alım türünde noter ve sigorta uygulanmaz.')+' '+(response.apply_sks?'SKS finansmanı mevcut oranla hesaplanır.':'Bu alım türünde SKS finansmanı uygulanmaz.');
  }catch(error){if(active!==session||version!==session.version||error.name==='AbortError')return;status.textContent='Önizleme alınamadı. '+error.message;results.hidden=true;}
 }
 body.addEventListener('input',queue);body.addEventListener('change',queue);session.dispose=()=>{body.removeEventListener('input',queue);body.removeEventListener('change',queue)};queue();
}
function init(){let pending=false;new MutationObserver(()=>{if(pending)return;pending=true;queueMicrotask(()=>{pending=false;mount()})}).observe(document.getElementById('modalBody'),{childList:true,subtree:true});mount()}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();

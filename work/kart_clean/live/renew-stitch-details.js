/* Reference-design decoration only: original values, controls and handlers stay authoritative. */
(()=>{function init(){
 const card=document.getElementById('finansKartPanel');if(!card)return;
 const paths={
 calculator:'<rect x="5" y="2" width="14" height="20" rx="2"/><path d="M8 6h8M8 10h2m4 0h2M8 14h2m4 0h2M8 18h2m4 0h2"/>',
 chart:'<path d="M5 20V10m7 10V4m7 16V7" stroke-width="3"/>',
 history:'<path d="M3 4v5h5M3 9a9 9 0 1 1 0 6M12 7v5l3 2"/>',
 save:'<path d="M4 3h13l3 3v15H4zM8 3v6h8V3M8 21v-8h8v8"/>',
 sheet:'<path d="M14 3H4v18h16V9h-6zM14 3l6 6M7 12h10M7 16h10M11 12v8"/>',
 copy:'<rect x="8" y="8" width="12" height="13" rx="2"/><path d="M15 8V3H3v13h5"/>',
 pdf:'<path d="M14 3H4v18h16V9h-6zM14 3l6 6M7 16h10M7 12h5"/>',
 chat:'<path d="M4 3h16v14H9l-5 4zM8 7h8M8 11h6"/>',
 money:'<rect x="3" y="6" width="18" height="12" rx="2"/><circle cx="12" cy="12" r="3"/><path d="M3 10l4-4m10 12 4-4M1 10v11h17"/>',
 shield:'<path d="M12 2l8 4v6c0 5-8 10-8 10S4 17 4 12V6zM8 11l3 3 5-6"/>',
 bank:'<path d="M2 8l10-5 10 5zM5 10v8m7-8v8m7-8v8M2 21h20M3 18h18"/>',
 user:'<circle cx="12" cy="7" r="4"/><path d="M4 21v-3a8 8 0 0 1 16 0v3z"/>',
 car:'<path d="M3 17V9l3-5h12l3 5v8zM3 9h18M6 13h2m8 0h2M5 17v3m14-3v3"/>',
 card:'<rect x="2" y="4" width="20" height="16" rx="3"/><path d="M2 9h20M6 15h4"/>'};
 function icon(name){const span=document.createElement('span');span.className='rst-icon';span.setAttribute('aria-hidden','true');span.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'+paths[name]+'</svg>';return span}
 function decorate(el,name){if(!el||el.querySelector(':scope > .rst-icon'))return;
  // Remove only the old decorative prefix; retain the original wording and nodes.
  const walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);const first=walker.nextNode();
  if(first)first.textContent=first.textContent.replace(/^[^\p{L}\p{N}]+/u,'');
  el.prepend(icon(name));el.classList.add('rst-icon-label');
 }
 decorate(card.querySelector('.brand h2'),'calculator');
 card.querySelectorAll('.rc-section-head b').forEach((el,i)=>decorate(el,i?'history':'chart'));
 [['.rc-mini-actions button:first-child','save'],['.rc-mini-actions button:last-child','sheet'],['#copyBtn','copy'],['#wpBtn','chat'],['#pdfBtn','pdf']].forEach(([sel,key])=>decorate(card.querySelector(sel),key));
 const actions=card.querySelector('.rst-actions');new MutationObserver(()=>{[['#copyBtn','copy'],['#wpBtn','chat'],['#pdfBtn','pdf']].forEach(([sel,key])=>decorate(card.querySelector(sel),key))}).observe(actions,{childList:true,subtree:true});
 document.querySelectorAll('.finans-mod-btn').forEach((el,i)=>decorate(el,['card','bank','car'][i]));
 decorate(document.querySelector('.side-panel .toggle-section span'),'user');decorate(document.querySelector('.rst-bank-panel .toggle-section span'),'bank');
 decorate(document.querySelector('.mail-panel-toggle>span'),'chat');
 document.querySelectorAll('.bank-copy-btn').forEach(btn=>{
  const originalLabel=btn.textContent;btn.setAttribute('title',originalLabel);btn.setAttribute('aria-label',originalLabel+' — '+btn.closest('.bank-card').querySelector('.bank-name').textContent);
  function add(){if(!btn.querySelector('.rst-icon'))btn.append(icon('copy'))}add();new MutationObserver(add).observe(btn,{childList:true});
 });
 const total=document.getElementById('toplamGeriOdeme').closest('.result-item');const cash=icon('money');cash.classList.add('rst-cash-icon');total.append(cash);
 const monthly=document.getElementById('aylikTaksitTutari').closest('.result-item'),badge=document.createElement('small');badge.className='rst-monthly-badge';badge.textContent='Her Ay Ödenecek';monthly.append(badge);
 const trust=card.querySelector('.rc-trust b');if(trust){trust.textContent='';trust.append(icon('shield'))}
 const input=document.getElementById('tutar'),field=document.createElement('div');field.className='rst-currency-field';input.before(field);field.append(input);const currency=document.createElement('span');currency.className='rst-currency-symbol';currency.textContent='₺';currency.setAttribute('aria-hidden','true');field.prepend(currency);
 document.querySelectorAll('.taksit-btn').forEach(btn=>{const term=parseInt(btn.textContent);btn.textContent='';const n=document.createElement('b'),label=document.createElement('small');n.textContent=term;label.textContent=' Taksit';btn.append(n,label)});
 const labels=document.querySelector('.kc-slider-labels'),selected=document.createElement('span');selected.className='rst-slider-selected';labels.firstElementChild.after(selected);
 function sliderLabel(){selected.textContent=(input.value||'0')+' ₺ (Seçili)'}input.addEventListener('input',sliderLabel);sliderLabel();
 const bars=card.querySelector('.kc-bars'),money=n=>n.toLocaleString('tr-TR',{minimumFractionDigits:2,maximumFractionDigits:2})+' ₺';
 function details(){
  sliderLabel();bars.querySelectorAll('.kc-bar-row').forEach(row=>{
   const term=parseInt(row.querySelector('.kc-bar-opt b').textContent);
   if(!row.querySelector('.rst-term')){
    const number=document.createElement('span');number.className='rst-term';number.textContent=term;row.prepend(number);
    const state=document.createElement('span');state.className='rst-current';state.textContent='Mevcut Seçim';row.querySelector('.kc-bar-opt').append(state);
    const track=row.querySelector('.kc-track'),group=document.createElement('span');group.className='rst-cost';track.before(group);const line=document.createElement('span');line.className='rst-cost-head';line.innerHTML='<span>Maliyet Yükü</span><b></b>';group.append(line,track);
    const amounts=row.querySelector('.kc-bar-values');amounts.classList.add('rst-labeled-values');
   }
   // Call the existing central calculation, never introduce another formula or rate table.
   const calculation=window.renewKartTotals(window.hamTutarAl(),term);
   row.querySelector('.rst-cost-head b').textContent=money(calculation.commission)+' Komisyon';
  });
 }
 new MutationObserver(details).observe(document.getElementById('rcCompareBody'),{childList:true});details();
 const history=document.getElementById('rcHistory');function historyIcons(){history.querySelectorAll('.rc-history-item').forEach(row=>{if(!row.querySelector('.rst-recall')){const glyph=icon('history');glyph.classList.add('rst-recall');row.append(glyph);row.title='Bu hesaplamayı geri çağır'}})}
 new MutationObserver(historyIcons).observe(history,{childList:true});historyIcons();
}if(document.readyState==='complete')init();else window.addEventListener('load',init)})();

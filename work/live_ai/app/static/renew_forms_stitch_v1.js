/* RENEW PRO — Precision Automotive form system: Stok / Satış / Aylık Alım.
   Sadece mevcut openStock/openSale/openSell/openAcquisition fonksiyonlarını
   zincirler; alan id/name, submit ve API akışı hiç değişmez.
   Canlı Finansal Analiz paneli calc.py'deki stock_calc/sale_calc ile
   BİREBİR AYNI formülü kullanır (backend'e ek istek atmadan, mevcut
   SETTINGS/rules global verisinden). */
(function(){
  'use strict';

  function norm(v){return String(v||'').trim().toLocaleUpperCase('tr-TR')}
  function findRule(purchaseType){
    const rules=(typeof SETTINGS!=='undefined'&&SETTINGS.rules)||[];
    const hit=rules.find(r=>norm(r.name)===norm(purchaseType));
    return hit||{apply_sks:0,apply_fixed:0};
  }
  function settingsNums(){return (typeof SETTINGS!=='undefined'&&SETTINGS.settings)||{}}
  function num(id){const el=document.getElementById(id);if(!el)return 0;return typeof parseMoney==='function'?parseMoney(el.value):(Number(el.value)||0)}
  function val(id){const el=document.getElementById(id);return el?el.value:''}
  function fmt(n){return typeof money==='function'?money(n):('₺'+Math.round(n||0).toLocaleString('tr-TR'))}
  function daysBetween(startStr,endStr){
    const s=startStr?new Date(startStr+'T00:00:00'):null;
    const e=endStr?new Date(endStr+'T00:00:00'):new Date();
    if(!s||isNaN(s))return 0;
    const diff=Math.floor((e-s)/86400000);
    return Math.max(0,diff);
  }

  /* ---------- panel markup ---------- */
  function panelSkeletonStock(){
    return `
      <div class="pa-fp-head">
        <div class="pa-fp-head-top"><span class="pa-fp-dot"></span><h4>Canlı Finansal Analiz</h4></div>
        <p>Ayarlar merkezindeki gider/SKS oranlarıyla anlık hesap</p>
      </div>
      <div class="pa-fp-body">
        <div class="pa-fp-highlights">
          <div class="pa-fp-card neutral">
            <span class="pa-fp-label">Toplam Araç Maliyeti</span>
            <div class="pa-fp-value" id="pfStockCost">₺0</div>
            <span class="pa-fp-sub">Alış + Sabit Gider + SKS Dahil</span>
          </div>
          <div class="pa-fp-card" id="pfStockProfitBox">
            <span class="pa-fp-label">Tahmini Net Kâr (Beklenen)</span>
            <div class="pa-fp-value" id="pfStockProfit">₺0</div>
            <span class="pa-fp-margin" id="pfStockMargin">%0</span>
          </div>
        </div>
        <div class="pa-fp-detail">
          <div class="pa-fp-row"><span>Stokta Bekleme (SKS)</span><span class="pa-fp-sks-pill" id="pfStockSksDays">0 Gün</span></div>
          <div class="pa-fp-row pa-fp-danger"><span>SKS Finansman Faizi</span><b id="pfStockSksFin">₺0</b></div>
          <div class="pa-fp-row"><span>Ham Alış Bedeli</span><b id="pfStockRaw">₺0</b></div>
          <div class="pa-fp-row"><span>Sabit Giderler Toplamı</span><b id="pfStockFixed">₺0</b></div>
          <div class="pa-fp-row total"><span>Hedef / Alış Farkı</span><b id="pfStockDiff">₺0</b></div>
        </div>
      </div>
      <div class="pa-fp-state"><span>Formül Motoru: <b>Hazır &amp; Senkronize</b></span><span>Excel ile birebir</span></div>`;
  }
  function panelSkeletonSale(){
    return `
      <div class="pa-fp-head">
        <div class="pa-fp-head-top"><span class="pa-fp-dot"></span><h4>Canlı Finansal Analiz</h4></div>
        <p>Ayarlar merkezindeki gider/SKS oranlarıyla anlık hesap</p>
      </div>
      <div class="pa-fp-body">
        <div class="pa-fp-highlights">
          <div class="pa-fp-card neutral">
            <span class="pa-fp-label">Toplam Maliyet</span>
            <div class="pa-fp-value" id="pfSaleCost">₺0</div>
            <span class="pa-fp-sub">Alış + Giderler + SKS Dahil</span>
          </div>
          <div class="pa-fp-card" id="pfSaleProfitBox">
            <span class="pa-fp-label">Gerçekleşen Net Kâr</span>
            <div class="pa-fp-value" id="pfSaleProfit">₺0</div>
            <span class="pa-fp-margin" id="pfSaleMargin">%0</span>
          </div>
        </div>
        <div class="pa-fp-detail">
          <div class="pa-fp-row"><span>Stokta Bekleme (SKS)</span><span class="pa-fp-sks-pill" id="pfSaleSksDays">0 Gün</span></div>
          <div class="pa-fp-row pa-fp-danger"><span>SKS Finansman Faizi</span><b id="pfSaleSksFin">₺0</b></div>
          <div class="pa-fp-row"><span>Noter + Ekspertiz + 150 Nokta + Sigorta</span><b id="pfSaleFixed">₺0</b></div>
          <div class="pa-fp-row"><span>Ek Masraf</span><b id="pfSaleExtra">₺0</b></div>
          <div class="pa-fp-row"><span>Ek Gelir (Sigorta/Kredi/Garanti)</span><b id="pfSaleExtraIncome">₺0</b></div>
          <div class="pa-fp-row total"><span>Performans Kârı</span><b id="pfSalePerf">₺0</b></div>
        </div>
      </div>
      <div class="pa-fp-state"><span>Formül Motoru: <b>Hazır &amp; Senkronize</b></span><span>Excel ile birebir</span></div>`;
  }

  function attachFinancePanel(kind){
    const body=document.getElementById('modalBody');
    const layout=body&&body.querySelector('.renew-form-layout');
    if(!body||!layout)return;
    const shell=document.createElement('div');shell.className='pa-form-shell';
    const main=document.createElement('div');main.className='pa-form-main';
    const aside=document.createElement('div');aside.className='pa-finance-panel';
    aside.innerHTML=kind==='stock'?panelSkeletonStock():panelSkeletonSale();
    layout.parentNode.insertBefore(shell,layout);
    main.appendChild(layout);
    shell.appendChild(main);
    shell.appendChild(aside);

    const recompute=kind==='stock'?computeStock:computeSale;
    const watchIds=kind==='stock'
      ?['f_purchase_price','f_list_price','f_purchase_date','f_purchase_type']
      :['f_purchase_price','f_sale_price','f_purchase_date','f_sale_date','f_purchase_type','f_extra_expense','f_insurance_income','f_credit_income','f_warranty_income'];
    watchIds.forEach(id=>{
      const el=document.getElementById(id);
      if(!el)return;
      el.addEventListener('input',recompute);
      el.addEventListener('change',recompute);
      el.addEventListener('blur',recompute);
    });
    recompute();
  }

  /* ---------- stok: calc.py stock_calc ile birebir ---------- */
  function computeStock(){
    const s=settingsNums();
    const buy=num('f_purchase_price');
    const sell=num('f_list_price');
    const rule=findRule(val('f_purchase_type'));
    const sks=daysBetween(val('f_purchase_date'));

    let fixed=buy?(Number(s.expertise_expense||0)+Number(s.control150_expense||0)):0;
    if(buy&&rule.apply_fixed) fixed+=Number(s.notary_expense||0)+Number(s.insurance_expense||0);
    const fin=(buy&&rule.apply_sks)?buy*Number(s.sks_monthly_rate||0)*sks/30:0;
    const total=buy?buy+fixed+fin:0;
    const profit=(sell&&buy)?sell-total:0;

    setText('pfStockRaw',fmt(buy));
    setText('pfStockFixed',fmt(fixed));
    setText('pfStockSksFin',fmt(fin));
    setText('pfStockCost',fmt(total));
    setText('pfStockDiff',fmt(sell-buy));
    const sksPill=document.getElementById('pfStockSksDays');
    if(sksPill){sksPill.textContent=sks+' Gün';sksPill.classList.toggle('crit',sks>=60)}

    const box=document.getElementById('pfStockProfitBox');
    const val_=document.getElementById('pfStockProfit');
    const margin=document.getElementById('pfStockMargin');
    if(box&&val_&&margin){
      const pct=sell>0?(profit/sell*100):0;
      if(profit>=0){
        box.className='pa-fp-card profit';
        val_.textContent='+'+fmt(profit);
        margin.textContent='%'+pct.toLocaleString('tr-TR',{maximumFractionDigits:1})+' Net Marj';
      }else{
        box.className='pa-fp-card loss';
        val_.textContent='-'+fmt(Math.abs(profit));
        margin.textContent='%'+pct.toLocaleString('tr-TR',{maximumFractionDigits:1})+' Zarar Marjı';
      }
    }
  }

  /* ---------- satış: calc.py sale_calc ile birebir ---------- */
  function computeSale(){
    const s=settingsNums();
    const buy=num('f_purchase_price');
    const sell=num('f_sale_price');
    const rule=findRule(val('f_purchase_type'));
    const sks=daysBetween(val('f_purchase_date'),val('f_sale_date'));
    const extra=num('f_extra_expense');

    const fixedOn=!!rule.apply_fixed;
    const notary=(buy&&fixedOn)?Number(s.notary_expense||0):0;
    const expertise=buy?Number(s.expertise_expense||0):0;
    const control=buy?Number(s.control150_expense||0):0;
    const insurance=(buy&&fixedOn)?Number(s.insurance_expense||0):0;
    const fin=(buy&&rule.apply_sks)?buy*Number(s.sks_monthly_rate||0)*sks/30:0;
    const totalExpense=notary+expertise+control+insurance+extra+fin;
    const totalCost=buy?buy+totalExpense:0;
    const net=sell?sell-totalCost:0;
    const extraIncome=num('f_insurance_income')+num('f_credit_income')+num('f_warranty_income');
    const perf=net+extraIncome;

    setText('pfSaleFixed',fmt(notary+expertise+control+insurance));
    setText('pfSaleExtra',fmt(extra));
    setText('pfSaleSksFin',fmt(fin));
    setText('pfSaleCost',fmt(totalCost));
    setText('pfSaleExtraIncome',fmt(extraIncome));
    setText('pfSalePerf',fmt(perf));
    const sksPill=document.getElementById('pfSaleSksDays');
    if(sksPill){sksPill.textContent=sks+' Gün';sksPill.classList.toggle('crit',sks>=60)}

    const box=document.getElementById('pfSaleProfitBox');
    const val_=document.getElementById('pfSaleProfit');
    const margin=document.getElementById('pfSaleMargin');
    if(box&&val_&&margin){
      const pct=sell>0?(net/sell*100):0;
      if(net>=0){
        box.className='pa-fp-card profit';
        val_.textContent='+'+fmt(net);
        margin.textContent='%'+pct.toLocaleString('tr-TR',{maximumFractionDigits:1})+' Net Marj';
      }else{
        box.className='pa-fp-card loss';
        val_.textContent='-'+fmt(Math.abs(net));
        margin.textContent='%'+pct.toLocaleString('tr-TR',{maximumFractionDigits:1})+' Zarar Marjı';
      }
    }
  }

  function setText(id,txt){const el=document.getElementById(id);if(el)el.textContent=txt}

  /* ---------- mevcut fonksiyonları zincirle (renew_forms_v1.js'ten SONRA çalışır) ---------- */
  const chainedStock=window.openStock,chainedSale=window.openSale,chainedSell=window.openSell;
  if(typeof chainedStock==='function'){
    window.openStock=function(id){chainedStock(id);attachFinancePanel('stock')};
  }
  if(typeof chainedSale==='function'){
    window.openSale=function(id){chainedSale(id);attachFinancePanel('sale')};
  }
  if(typeof chainedSell==='function'){
    window.openSell=function(id){chainedSell(id);attachFinancePanel('sale')};
  }
})();


function rpToast(message){
  let el=document.getElementById('rpToast');
  if(!el){el=document.createElement('div');el.id='rpToast';el.className='rp-toast';document.body.appendChild(el)}
  el.textContent=message;el.classList.add('show');clearTimeout(window.rpToastTimer);window.rpToastTimer=setTimeout(()=>el.classList.remove('show'),1800);
}
function finOdemePlaniMetni(){
  const body=document.getElementById('finPlanBody');
  if(!body||!body.children.length)return '';
  const tip=typeof finTip!=='undefined'&&finTip==='kurumsal'?'Kurumsal':'Bireysel';
  const lines=[
    'RENEW • Kredi Aylık Ödeme Planı',
    'Müşteri Tipi: '+tip,
    'Araç / Kasko Değeri: '+(document.getElementById('finAracBedeli')?.value||'')+' TL',
    'Kredi Tutarı: '+(document.getElementById('finOKredi')?.textContent||''),
    'Vade: '+(document.getElementById('finVade')?.value||'')+' Ay',
    'Aylık Faiz: %'+(document.getElementById('finFaiz')?.value||''),
    'Aylık Taksit: '+(document.getElementById('finOTaksit')?.textContent||''),
    'Toplam Ödeme: '+(document.getElementById('finOToplam')?.textContent||''),
    'Toplam Faiz: '+(document.getElementById('finOFaiz')?.textContent||''),'',
    'Ay | Taksit | Faiz | Anapara | Kalan'
  ];
  body.querySelectorAll('tr').forEach(tr=>lines.push([...tr.querySelectorAll('td')].map(td=>td.textContent.trim()).join(' | ')));
  lines.push('','Not: Bankanın nihai koşulları farklılık gösterebilir.');
  return lines.join('\n');
}
function finOdemePlaniKopyala(btn){
  const text=finOdemePlaniMetni();if(!text)return alert('Önce ödeme planını hesaplayın.');
  const done=()=>{rpToast('Ödeme planı kopyalandı');if(btn){const old=btn.textContent;btn.textContent='✅ Kopyalandı';setTimeout(()=>btn.textContent=old,1600)}};
  if(navigator.clipboard?.writeText)navigator.clipboard.writeText(text).then(done).catch(()=>rpEskiKopyala(text,done));else rpEskiKopyala(text,done);
}
function rpEskiKopyala(text,done){const t=document.createElement('textarea');t.value=text;t.style.position='fixed';t.style.opacity='0';document.body.appendChild(t);t.select();document.execCommand('copy');t.remove();done()}
document.addEventListener('DOMContentLoaded',function(){
  const notes={finansKartPanel:'Tutarı ve taksiti seçin; komisyon, aylık ödeme ve toplam geri ödeme aynı matematik kaynağından hesaplanır.',finansKrediPanel:'Araç değerine göre azami limiti kontrol edin; oluşturulan tablo, kopyalama ve PDF aynı ödeme planını kullanır.',finansKaskoPanel:'TSB değerini girin; bireysel ve kurumsal limitleri görün, seçiminizi kredi hesabına aktarın.'};
  Object.keys(notes).forEach(id=>{const panel=document.getElementById(id),brand=panel?.querySelector('.brand');if(panel&&brand&&!panel.querySelector('.rp-helper')){const p=document.createElement('p');p.className='rp-helper';p.innerHTML='<strong>Nasıl kullanılır:</strong> '+notes[id];brand.insertAdjacentElement('afterend',p)}});
  document.querySelectorAll('.bank-copy-btn').forEach(b=>b.setAttribute('aria-label','Banka ve IBAN bilgisini kopyala'));
});

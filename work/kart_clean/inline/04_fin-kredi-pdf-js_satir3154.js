
function finPdfEsc(v){
  return String(v ?? '').replace(/[&<>"']/g,function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
  });
}

function finOdemePlaniPdf(){
  const planBody=document.getElementById('finPlanBody');
  if(!planBody || !planBody.children.length){
    alert('Önce ödeme planını hesaplayın.');
    return;
  }

  const aracBedeli=document.getElementById('finAracBedeli')?.value || '';
  const kredi=document.getElementById('finKrediTutari')?.value || '';
  const vade=document.getElementById('finVade')?.value || '';
  const faiz=document.getElementById('finFaiz')?.value || '';
  const tip=typeof finTip!=='undefined' && finTip==='kurumsal' ? 'Kurumsal' : 'Bireysel';
  const limit=document.getElementById('finLimit')?.textContent || '';
  const aylik=document.getElementById('finOTaksit')?.textContent || '';
  const toplam=document.getElementById('finOToplam')?.textContent || '';
  const toplamFaiz=document.getElementById('finOFaiz')?.textContent || '';

  const rows=[...planBody.querySelectorAll('tr')].map(function(tr){
    const tds=[...tr.querySelectorAll('td')].map(td=>finPdfEsc(td.textContent.trim()));
    if(tds.length!==5)return '';
    return `<tr>
      <td>${tds[0]}</td><td>${tds[1]}</td><td>${tds[2]}</td>
      <td>${tds[3]}</td><td>${tds[4]}</td>
    </tr>`;
  }).join('');

  const w=window.open('','_blank','width=1000,height=800');
  if(!w){
    alert('PDF penceresi açılamadı. Tarayıcı açılır pencere iznini kontrol edin.');
    return;
  }

  w.document.open();
  w.document.write(`<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<title>Kredi Ödeme Planı</title>
<style>
@page{size:A4;margin:10mm}
*{box-sizing:border-box}
body{font-family:Arial,"Segoe UI",sans-serif;color:#111827;margin:0;background:#fff}
.header{border:2px solid #111827;border-radius:12px;padding:15px 17px;margin-bottom:12px;position:relative}
.header:before{content:"";position:absolute;left:0;top:0;bottom:0;width:6px;background:#f7d117;border-radius:10px 0 0 10px}
.header h1{margin:0 0 4px;font-size:19px}
.header p{margin:0;color:#64748b;font-size:10px;font-weight:700;letter-spacing:.7px}
.meta{display:grid;grid-template-columns:repeat(3,1fr);gap:7px;margin-bottom:10px}
.meta div,.summary div{border:1px solid #dbe3ec;border-radius:8px;padding:8px 9px;background:#f8fafc}
.meta span,.summary span{display:block;color:#64748b;font-size:8px;font-weight:800;text-transform:uppercase;letter-spacing:.45px}
.meta strong,.summary strong{display:block;margin-top:3px;font-size:11px}
.summary{display:grid;grid-template-columns:repeat(4,1fr);gap:7px;margin-bottom:11px}
.summary div:last-child{border-bottom:3px solid #f7d117}
table{width:100%;border-collapse:collapse;font-size:9px}
th{background:#0b1220;color:#fff;padding:7px 5px;text-align:right}
th:first-child{text-align:center}
td{padding:6px 5px;border-bottom:1px solid #e5e7eb;text-align:right}
td:first-child{text-align:center;font-weight:700}
tr:nth-child(even) td{background:#f8fafc}
.footer{margin-top:10px;border-top:1px solid #dbe3ec;padding-top:7px;color:#64748b;font-size:8px;text-align:center}
@media print{
  body{-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .no-print{display:none!important}
  thead{display:table-header-group}
  tr{page-break-inside:avoid}
}
</style>
</head>
<body>
<div class="header">
  <h1>RENEW • Kredi Aylık Ödeme Planı</h1>
  <p>ÇAYAN OTOMOTİV • FİNANSMAN HESAPLAMA</p>
</div>

<div class="meta">
  <div><span>Müşteri Tipi</span><strong>${finPdfEsc(tip)}</strong></div>
  <div><span>Araç / Kasko Değeri</span><strong>${finPdfEsc(aracBedeli)} TL</strong></div>
  <div><span>Azami Kredi Limiti</span><strong>${finPdfEsc(limit)}</strong></div>
  <div><span>Kredi Tutarı</span><strong>${finPdfEsc(kredi)} TL</strong></div>
  <div><span>Vade</span><strong>${finPdfEsc(vade)} Ay</strong></div>
  <div><span>Aylık Faiz</span><strong>%${finPdfEsc(faiz)}</strong></div>
</div>

<div class="summary">
  <div><span>Aylık Taksit</span><strong>${finPdfEsc(aylik)}</strong></div>
  <div><span>Toplam Ödeme</span><strong>${finPdfEsc(toplam)}</strong></div>
  <div><span>Toplam Faiz</span><strong>${finPdfEsc(toplamFaiz)}</strong></div>
  <div><span>Vade</span><strong>${finPdfEsc(vade)} Ay</strong></div>
</div>

<table>
<thead><tr><th>Ay</th><th>Taksit</th><th>Faiz</th><th>Anapara</th><th>Kalan Borç</th></tr></thead>
<tbody>${rows}</tbody>
</table>

<div class="footer">
Bu belge hesaplama amaçlı hazırlanmıştır. Banka nihai kredi koşulları ve ödeme planı farklılık gösterebilir.
</div>

<script>
window.onload=function(){
  setTimeout(function(){window.print();},300);
};
<\/script>

</body>
</html>`);
  w.document.close();
}

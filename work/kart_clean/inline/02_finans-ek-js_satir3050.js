
let finTip='bireysel';

function finansModAc(mod){
  const map={kart:'finansKartPanel',kredi:'finansKrediPanel',kasko:'finansKaskoPanel'};
  Object.keys(map).forEach(function(k){
    const el=document.getElementById(map[k]);
    if(el) el.style.display=(k===mod)?'':'none';
  });
  document.querySelectorAll('.finans-mod-btn').forEach(function(b){
    b.classList.toggle('active',b.dataset.finans===mod);
  });
  if(mod==='kredi') finLimitGuncelle();
  if(mod==='kasko') finKaskoGuncelle();
}
function finNum(v){return Number(String(v||'').replace(/\D/g,''))||0}
function finTL(v){return '₺'+Math.round(Number(v)||0).toLocaleString('tr-TR')}
function finPara(el){
  const d=String(el.value||'').replace(/\D/g,'');
  el.value=d?parseInt(d,10).toLocaleString('tr-TR'):'';
}
function finKrediTipSec(t){
  finTip=t==='kurumsal'?'kurumsal':'bireysel';
  document.getElementById('finBireysel').classList.toggle('active',finTip==='bireysel');
  document.getElementById('finKurumsal').classList.toggle('active',finTip==='kurumsal');
  document.getElementById('finOran').textContent=finTip==='bireysel'?'%20':'%80';
  finLimitGuncelle();
}
function finLimitDegeri(){
  const bedel=finNum(document.getElementById('finAracBedeli').value);
  return bedel*(finTip==='bireysel'?0.20:0.80);
}
function finLimitGuncelle(){
  document.getElementById('finLimit').textContent=finTL(finLimitDegeri());
  finLimitKontrol();
}
function finLimitKontrol(){
  const input=document.getElementById('finKrediTutari');
  if(!input)return;
  const kredi=finNum(input.value), limit=finLimitDegeri();
  input.style.borderColor=(limit>0&&kredi>limit)?'#b91c1c':'';
}
function finOdemePlani(){
  const bedel=finNum(document.getElementById('finAracBedeli').value);
  const P=finNum(document.getElementById('finKrediTutari').value);
  const n=parseInt(document.getElementById('finVade').value,10)||0;
  const r=(Number(document.getElementById('finFaiz').value)||0)/100;
  const limit=finLimitDegeri();
  if(!bedel)return alert('Araç bedeli / kasko değerini girin.');
  if(!P)return alert('Çekmek istediğiniz kredi tutarını girin.');
  if(P>limit)return alert('Kredi tutarı azami limiti aşıyor: '+finTL(limit));
  if(n<1)return alert('Geçerli vade girin.');

  let taksit=r===0?P/n:P*(r*Math.pow(1+r,n))/(Math.pow(1+r,n)-1);
  let kalan=P, toplam=0, rows='';
  for(let ay=1;ay<=n;ay++){
    let faiz=kalan*r, anapara=taksit-faiz, odeme=taksit;
    if(ay===n){anapara=kalan;odeme=anapara+faiz}
    kalan=Math.max(0,kalan-anapara); toplam+=odeme;
    rows+=`<tr><td>${ay}</td><td>${finTL(odeme)}</td><td>${finTL(faiz)}</td><td>${finTL(anapara)}</td><td>${finTL(kalan)}</td></tr>`;
  }
  document.getElementById('finOKredi').textContent=finTL(P);
  document.getElementById('finOTaksit').textContent=finTL(taksit);
  document.getElementById('finOToplam').textContent=finTL(toplam);
  document.getElementById('finOFaiz').textContent=finTL(toplam-P);
  document.getElementById('finPlanBody').innerHTML=rows;
  document.getElementById('finOzet').style.display='grid';
  document.getElementById('finPlan').style.display='block';
  document.getElementById('finKrediActions').style.display='flex';
}
function finKaskoGuncelle(){
  const d=finNum(document.getElementById('finKaskoDegeri').value);
  document.getElementById('finKaskoOzet').textContent=finTL(d);
  document.getElementById('finKasko20').textContent=finTL(d*.20);
  document.getElementById('finKasko80').textContent=finTL(d*.80);
}
document.addEventListener('DOMContentLoaded',function(){finansModAc('kart');finKrediTipSec('bireysel')});

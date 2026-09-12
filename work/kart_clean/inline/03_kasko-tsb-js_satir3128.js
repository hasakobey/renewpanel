
let finKaskoTipi='bireysel';
function finTsbAc(){
  window.open('https://www.tsb.org.tr/tr/kasko-deger-listesi?pageID=500','_blank','noopener,noreferrer');
}
function finKaskoTemizle(){
  const el=document.getElementById('finKaskoDegeri');
  if(el){el.value='';finKaskoGuncelle();el.focus();}
}
function finKaskoTipSec(t){
  finKaskoTipi=t==='kurumsal'?'kurumsal':'bireysel';
  document.getElementById('kaskoBireyselSec')?.classList.toggle('active',finKaskoTipi==='bireysel');
  document.getElementById('kaskoKurumsalSec')?.classList.toggle('active',finKaskoTipi==='kurumsal');
}
function finKaskoyuAktar(){
  const d=finNum(document.getElementById('finKaskoDegeri')?.value);
  if(!d)return alert('Önce TSB kasko değerini girin.');
  const input=document.getElementById('finAracBedeli');
  if(input) input.value=Math.round(d).toLocaleString('tr-TR');
  finKrediTipSec(finKaskoTipi);
  finansModAc('kredi');
  finLimitGuncelle();
}
document.addEventListener('DOMContentLoaded',function(){finKaskoTipSec('bireysel')});

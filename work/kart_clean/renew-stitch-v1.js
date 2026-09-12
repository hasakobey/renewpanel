/* Visual composition only. Existing controls and handlers are moved, never cloned. */
(()=>{function init(){const card=document.getElementById('finansKartPanel'),tabs=document.getElementById('finansModSecici');if(!card||!tabs)return;document.body.classList.add('rst-v1');
const header=document.createElement('header');header.className='rst-header';const inner=document.createElement('div');inner.className='rst-header-inner';const brand=document.createElement('div');brand.className='rst-brand';brand.innerHTML='<b aria-hidden="true">R</b><span><strong>RENEW</strong><small>ÇAYAN TARSUS OTOMOTİV</small></span>';inner.append(brand,tabs);header.append(inner);document.querySelector('.wrapper').before(header);
const work=card.querySelector('.rc-workspace'),actions=document.createElement('div');actions.className='rst-actions';const main=card.querySelector('.rc-mini-actions'),secondary=card.querySelector('.btn-container');if(work&&main&&secondary){actions.append(main,secondary);work.after(actions)}
// Separate the existing customer and IBAN controls without replacing their handlers.
const bank=document.getElementById('bankContent'),bankToggle=bank.previousElementSibling;
const bankPanel=document.createElement('section');bankPanel.className='rst-bank-panel';
bank.parentElement.after(bankPanel);bankPanel.append(bankToggle,bank);
if(matchMedia('(min-width:851px)').matches){
 if(getComputedStyle(bank).display==='none')window.bankaAlaniniAcKapat();
 const customer=document.getElementById('musteriContent');
 if(getComputedStyle(customer).display==='none')window.musteriAlaniniAcKapat();
}
const reduced=matchMedia('(prefers-reduced-motion:reduce)'),running=new WeakMap();
function motion(el,frames,options={}){if(!el||reduced.matches)return;running.get(el)?.cancel();running.set(el,el.animate(frames,{duration:350,easing:'cubic-bezier(.16,1,.3,1)',...options}))}
const metrics=[...card.querySelectorAll('#sonuc .result-item strong')],previous=new Map(metrics.map(el=>[el,el.textContent]));
let frame;
new MutationObserver(()=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>{
 metrics.forEach(el=>{if(previous.get(el)===el.textContent)return;previous.set(el,el.textContent);
  motion(el,[{transform:'translateY(3px) scale(.985)',filter:'brightness(1.18)'},{transform:'translateY(0) scale(1)',filter:'brightness(1)'}]);
  const green=el.id==='toplamGeriOdeme',color=green?'#16653435':'#0051d52b';
  motion(el.closest('.result-item'),[{boxShadow:'0 0 0 0 '+color},{boxShadow:'0 0 0 5px transparent'}],{duration:550});
 });
})}).observe(document.getElementById('sonuc'),{subtree:true,childList:true,characterData:true});
document.getElementById('taksit').addEventListener('change',()=>requestAnimationFrame(()=>{
 motion(card.querySelector('.taksit-btn.active'),[{transform:'scale(.96)'},{transform:'scale(1.025)'},{transform:'scale(1)'}]);
 card.querySelectorAll('.kc-fill').forEach((el,i)=>motion(el,[{transform:'scaleX(.4)'},{transform:'scaleX(1)'}],{duration:550,delay:i*45}));
}));
document.querySelectorAll('.bank-copy-btn').forEach(btn=>{
 new MutationObserver(()=>{if(/✓|✅|Kopyalandı/i.test(btn.textContent))motion(btn.closest('.bank-card'),[{boxShadow:'0 0 0 2px #16a34a65',background:'#dcfce7'},{boxShadow:'0 0 0 5px transparent',background:'#f0f5fa'}],{duration:650})}).observe(btn,{childList:true,subtree:true,characterData:true});
});
[document.querySelector('.side-panel'),bankPanel,card,...card.querySelectorAll('.rc-section')].forEach((el,i)=>motion(el,[{opacity:.5,transform:'translateY(10px)'},{opacity:1,transform:'translateY(0)'}],{duration:450,delay:Math.min(i*50,200)}));
}if(document.readyState==='complete')init();else document.addEventListener('DOMContentLoaded',init)})();

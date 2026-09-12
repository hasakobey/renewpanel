/* Presentation layer only. Existing fields, generated text and actions are retained. */
(()=>{'use strict';
function init(){
 const panel=document.querySelector('.mail-panel'),content=document.getElementById('mailPanelContent');if(!panel||!content||document.getElementById('mailStudio'))return;
 const items=[['tahsilatBolum','Kredi Kartı Tahsilatı','Kart tahsilatı için destek maili','mailOnizleme','✉'],['odemeBolum','Ödeme Bildirimi','Gönderilen ödemeyi bildirin','odemeOnizleme','↗'],['sigortaBolum','Sigorta İşlemleri','Sigorta talebi ve iptal işlemi','sigortaOnizleme','◇'],['devirBolum','Devir İşlemi','Alış ve devir yazışmaları','devirOnizleme','⇄'],['nakitBolum','Nakit / Takas Talebi','Araç bedeli ödeme talebi','nakitOnizleme','₺']];
 const dialog=document.createElement('dialog');dialog.id='mailStudio';dialog.setAttribute('aria-labelledby','msTitle');
 dialog.innerHTML='<header class="ms-top"><div><span>RENEW / YAZIŞMA ATÖLYESİ</span><h2 id="msTitle">Mail & Ödeme Stüdyosu</h2></div><button class="ms-close" type="button" aria-label="Şablon stüdyosunu kapat">×</button></header><div class="ms-layout"><nav class="ms-rail" aria-label="Mail şablonları"><div class="ms-rail-head"><div><small>ŞABLONLAR</small><h3>Mail Merkezi</h3></div><span>5</span></div><div class="ms-nav"></div><p>Bilgileri doldurun, metni kontrol edin ve kopyalayın ya da Outlook’ta açın. Buradan e-posta gönderilmez.</p></nav><main class="ms-paper"><header class="ms-letterhead"><div class="ms-brand"><b>R</b><div><strong>RENEW</strong><small>Çayan Tarsus Otomotiv</small></div></div><div class="ms-date"><time></time><span>Taslak önizleme</span></div></header><div class="ms-documents"></div></main></div>';
 document.body.append(dialog);let active=items[0][0],trigger=panel.querySelector('.mail-panel-toggle');
 const font=document.createElement('link');font.rel='stylesheet';font.href='https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Newsreader:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap';document.head.append(font);
 const toast=document.createElement('div');toast.className='ms-toast';toast.setAttribute('role','status');toast.hidden=true;dialog.append(toast);let toastTimer;
 const copyObserver=new MutationObserver(records=>{if(records.some(r=>r.target.parentElement?.closest('.mail-copy-btn')?.textContent.includes('Kopyalandı')||r.target.closest?.('.mail-copy-btn')?.textContent.includes('Kopyalandı'))){toast.textContent='Metin kopyalandı';toast.hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>toast.hidden=true,2200)}});
 const side=document.querySelector('.side-panel');
 if(side){const left=document.createElement('div');left.className='ms-left-column';side.before(left);left.append(side,panel);document.body.classList.add('ms-ready')}
 items.forEach(([id,title,desc,preview,icon])=>{
   const body=document.getElementById(id),section=body.closest('.mail-section'),oldTitle=section.querySelector('.mail-section-title');
   oldTitle.hidden=true;oldTitle.removeAttribute('onclick');body.classList.add('show');
   dialog.querySelector('.ms-documents').append(section);section.dataset.msId=id;
   const nav=document.createElement('button');nav.type='button';nav.className='ms-tile';nav.dataset.target=id;nav.setAttribute('aria-controls',id);
   const ic=document.createElement('span');ic.className='ms-icon';ic.textContent=icon;const text=document.createElement('span');text.innerHTML='<b></b><small></small>';text.querySelector('b').textContent=title;text.querySelector('small').textContent=desc;nav.append(ic,text);nav.addEventListener('click',()=>select(id));dialog.querySelector('.ms-nav').append(nav);
   const area=document.getElementById(preview),group=area.parentElement;group.classList.add('ms-message');
   const subject=document.createElement('div');subject.className='ms-subject';subject.textContent=title;const rich=document.createElement('div');rich.className='ms-letter';rich.dataset.source=preview;rich.setAttribute('aria-label',title+' metin önizlemesi');
   area.before(subject,rich);area.classList.add('ms-raw');
   const rawToggle=document.createElement('button');rawToggle.type='button';rawToggle.className='ms-raw-toggle';rawToggle.textContent='Düz metni göster';rawToggle.setAttribute('aria-expanded','false');rawToggle.addEventListener('click',()=>{const show=area.classList.toggle('ms-raw-visible');rawToggle.textContent=show?'Düz metni gizle':'Düz metni göster';rawToggle.setAttribute('aria-expanded',String(show))});area.after(rawToggle);
   const actions=document.createElement('div');actions.className='ms-actions';group.append(actions);group.querySelectorAll('.mail-copy-btn,.mail-outlook-btn').forEach(b=>actions.append(b));
   actions.querySelectorAll('.mail-copy-btn').forEach(b=>copyObserver.observe(b,{childList:true,subtree:true,characterData:true}));
   body.querySelectorAll('input,select,textarea').forEach(el=>{const label=el.parentElement.querySelector('label');if(label&&el.id&&!label.htmlFor)label.htmlFor=el.id});
   body.querySelectorAll('.mail-choice').forEach(el=>el.parentElement.classList.add('mail-full'));
 });
 function refresh(){dialog.querySelectorAll('.ms-letter').forEach(el=>{const value=document.getElementById(el.dataset.source).value;if(el.dataset.current===value)return;el.dataset.current=value;el.replaceChildren();value.split(/\n\s*\n/).forEach(block=>{
   if(block.split('\n').every(line=>/^[^:]{2,65}:/.test(line))){block.split('\n').forEach(line=>{const row=document.createElement('div');row.className='ms-detail-row';const key=document.createElement('span'),val=document.createElement('span');const at=line.indexOf(':');key.textContent=line.slice(0,at);val.textContent=line.slice(at+1).trim();val.className='ms-value';row.append(key,val);el.append(row)});return}
   const p=document.createElement('p');block.split(/(\[[^\]]+\])/).forEach(part=>{if(/^\[.*\]$/.test(part)){const mark=document.createElement('span');mark.className='ms-value';mark.textContent=part;p.append(mark)}else p.append(document.createTextNode(part))});if(block===block.toLocaleUpperCase('tr-TR')&&/[A-ZÇĞİÖŞÜ]/.test(block))p.className='ms-block-label';el.append(p)
 })});const current=document.getElementById(items.find(i=>i[0]===active)[3]).value;dialog.querySelector('.ms-date>span').textContent=/\[[^\]]+\]/.test(current)?'Bilgileri tamamlayın':'Taslak önizleme'}
 function select(id){active=id;dialog.querySelectorAll('[data-ms-id]').forEach(s=>s.hidden=s.dataset.msId!==id);dialog.querySelectorAll('.ms-tile').forEach(b=>{const on=b.dataset.target===id;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on))});refresh()}
 function close(){dialog.close()}
 trigger.removeAttribute('onclick');trigger.setAttribute('aria-haspopup','dialog');trigger.setAttribute('aria-controls','mailStudio');trigger.setAttribute('aria-expanded','false');
 trigger.addEventListener('click',()=>{if(dialog.open)return;dialog.querySelector('time').textContent=new Date().toLocaleDateString('tr-TR',{day:'2-digit',month:'long',year:'numeric'});select(active);dialog.showModal();document.body.classList.add('ms-open');trigger.setAttribute('aria-expanded','true')});
 dialog.querySelector('.ms-close').addEventListener('click',close);dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)close()}});
 dialog.addEventListener('close',()=>{document.body.classList.remove('ms-open');trigger.setAttribute('aria-expanded','false');trigger.focus()});
 ['input','change','click'].forEach(type=>document.addEventListener(type,()=>{if(dialog.open)queueMicrotask(refresh)}));
 content.hidden=true;select(active);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();

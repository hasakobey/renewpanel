/* Shared stock / sale / acquisition presentation. No payload or business-rule changes. */
(()=>{'use strict';
const shapes={car:'<path d="M3 17V9l3-5h12l3 5v8zM3 9h18M6 13h2m8 0h2M5 17v3m14-3v3"/>',source:'<path d="M4 21V5h9v16M13 10h7v11M7 8h3M7 12h3M7 16h3M16 13h1M16 17h1M2 21h20"/>',money:'<rect x="2" y="5" width="20" height="14" rx="2"/><circle cx="12" cy="12" r="3"/><path d="M5 9h1m12 6h1"/>',save:'<path d="M4 3h13l3 3v15H4zM8 3v6h8V3M8 21v-8h8v8"/>',back:'<path d="M9 6l-6 6 6 6M3 12h18"/>',plus:'<circle cx="12" cy="12" r="9"/><path d="M12 7v10M7 12h10"/>'};
function icon(key){const n=document.createElement('span');n.className='rfs-icon';n.setAttribute('aria-hidden','true');n.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'+shapes[key]+'</svg>';return n}
function decorate(){const modal=document.getElementById('modal'),body=document.getElementById('modalBody');if(!modal||!body)return;
 const form=body.querySelector('#acqFormV710'),layout=body.querySelector('.renew-form-layout');
 if(!form&&!layout){modal.classList.remove('rfs-modal');return}
 modal.classList.add('rfs-modal');if(body.querySelector('.rfs-scroll'))return;
 const host=form||body,actions=host.querySelector('.actions');if(!actions)return;
 // Keep the actions in their original form/body ancestry: save handlers depend on it.
 const scroll=document.createElement('div');scroll.className='rfs-scroll';
 [...host.children].filter(n=>n!==actions).forEach(n=>scroll.append(n));host.prepend(scroll);actions.classList.add('rfs-actions');
 const sections=scroll.querySelectorAll('.renew-form-section,.acq-section');
 sections.forEach((section,i)=>{section.classList.add('rfs-section');section.style.setProperty('--rfs-order',i);
  const head=section.querySelector('.renew-form-section-head,.acq-section-head');if(head){const old=head.querySelector(':scope>span,:scope>i');if(old)old.replaceWith(icon(['car','source','money'][i]||'car'));else head.prepend(icon('car'))}
 });
 const intro=scroll.querySelector('.renew-form-icon,.acq-intro-icon');if(intro){intro.textContent='';intro.append(icon(form?'source':'plus'))}
 actions.querySelectorAll('button').forEach(btn=>{
  const success=btn.classList.contains('success');btn.classList.add('rfs-button');
  const line=btn.querySelector('span')||btn;
  if(line.firstChild?.nodeType===Node.TEXT_NODE)line.firstChild.textContent=line.firstChild.textContent.replace(/^[✓✔✅]\s*/,'');
  line.prepend(icon(success?'save':'back'));
 });
 scroll.querySelectorAll('.field').forEach(field=>{const control=field.querySelector('input,select,textarea'),label=field.querySelector('label');if(control?.id&&label&&!label.htmlFor)label.htmlFor=control.id});
}
function init(){let scheduled=false;const queue=()=>{if(scheduled)return;scheduled=true;queueMicrotask(()=>{scheduled=false;decorate()})};new MutationObserver(queue).observe(document.getElementById('modalBody'),{childList:true,subtree:true});decorate()}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();

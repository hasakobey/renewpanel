(()=>{'use strict';
 function syncMobileNav(pageId){document.querySelectorAll('#renewMobileNav button[data-mobile-page]').forEach(b=>b.classList.toggle('active',b.dataset.mobilePage===pageId))}
 function upgradeNav(){const n=document.getElementById('renewMobileNav');if(!n)return;n.querySelectorAll('button').forEach((b,i)=>{const ids=['dashboard','search','stock','vehicle360','profile'];b.type='button';b.dataset.mobilePage=ids[i]||'';b.setAttribute('aria-label',(b.querySelector('small')?.textContent||'Menü').trim())});const active=document.querySelector('.page.active')?.id;syncMobileNav(active==='stocks'?'stock':active)}
 const previous=self.page;self.page=function(id){if(typeof previous==='function')previous(id);syncMobileNav(id);if(innerWidth<=900)requestAnimationFrame(()=>scrollTo({top:0,behavior:'smooth'}))};
 document.addEventListener('click',e=>{const b=e.target.closest?.('#renewMobileNav button');if(!b)return;if(b.dataset.mobilePage==='search')syncMobileNav('search');else if(b.dataset.mobilePage==='stock')syncMobileNav('stock')});
 const modalObserver=new MutationObserver(()=>document.body.classList.toggle('renew-modal-open',!!document.querySelector('.modal.show,.renew-command-modal.show')));
 document.addEventListener('DOMContentLoaded',()=>{upgradeNav();const modal=document.getElementById('modal');if(modal)modalObserver.observe(modal,{attributes:true,attributeFilter:['class']});const command=document.getElementById('renewCommandModal');if(command)modalObserver.observe(command,{attributes:true,attributeFilter:['class']})},{once:true});
 addEventListener('orientationchange',()=>setTimeout(()=>{document.documentElement.style.setProperty('--renew-vh',innerHeight+'px')},180));
})();

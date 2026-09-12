/* Layout only: retain existing inputs, calculation functions, values and actions. */
(()=>{function init(){const card=document.getElementById('finansKartPanel'),work=card?.querySelector('.rc-workspace');if(!work)return;card.classList.add('kc-console');let anchor=work;card.querySelectorAll('.rc-summary-pane>.rc-section,.rc-summary-pane>.rc-trust').forEach(el=>{anchor.after(el);anchor=el});
}if(document.readyState!=='complete')window.addEventListener('load',init);else init()})();

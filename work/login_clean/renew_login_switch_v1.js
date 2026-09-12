(function(){
  function initLoginSwitch(){
    var overlay = document.getElementById('loginOverlay');
    if(!overlay) return;

    // --- Basarili giris gecisi ---
    // Mevcut auth akisina (app.js / user_admin_v2.js icindeki calisan submit
    // handler) HIC dokunmuyoruz. Onlar basari halinde overlay'e '.hidden'
    // class'i ekliyor. Biz sadece bu class eklemesini gozlemleyip araya bir
    // mavi gecis animasyonu sokuyoruz, sonra dogal gizlemeye izin veriyoruz.
    var transitionEl = null;
    function ensureTransitionEl(){
      if(transitionEl) return transitionEl;
      transitionEl = document.createElement('div');
      transitionEl.className = 'renew-login-transition';
      transitionEl.innerHTML = '<div class="renew-login-transition-ring"></div>';
      document.body.appendChild(transitionEl);
      return transitionEl;
    }

    var playing = false;
    var observer = new MutationObserver(function(){
      if(playing) return;
      var justHidden = overlay.classList.contains('hidden');
      if(!justHidden) return;
      playing = true;
      overlay.classList.remove('hidden');
      var el = ensureTransitionEl();
      // eslint-disable-next-line no-unused-expressions
      el.offsetHeight; // gecisi tetiklemek icin zorla reflow
      // NOT: requestAnimationFrame BURADA KULLANILMAZ - arka plan/gizli
      // sekmede hic calismiyor (kart.renewpanel.xyz duzeltmesinde de ayni
      // sorun cikmisti, bkz. CLAUDE.md). setTimeout her durumda calisir.
      setTimeout(function(){ el.classList.add('is-active'); }, 20);
      setTimeout(function(){
        var ring = el.querySelector('.renew-login-transition-ring');
        if(ring) ring.outerHTML = '<div class="renew-login-transition-check">✓</div>';
      }, 480);
      setTimeout(function(){
        overlay.classList.add('hidden');
        el.classList.remove('is-active');
        setTimeout(function(){ if(el && el.parentNode) el.parentNode.removeChild(el); transitionEl = null; playing = false; }, 350);
      }, 950);
    });
    observer.observe(overlay, { attributes: true, attributeFilter: ['class'] });
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', initLoginSwitch);
  } else {
    initLoginSwitch();
  }
})();

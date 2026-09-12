(function(){
  'use strict';

  /*
    F5 sırasında eski sayfa çok erken açılıp CURRENT_USER henüz
    yüklenmeden permission kontrolüne girmesin.
  */
  try{
    const saved = localStorage.getItem('renew_v6_page') || 'dashboard';
    sessionStorage.setItem('renew_pending_page', saved);
    localStorage.setItem('renew_v6_page', 'dashboard');
  }catch(e){}

  window.RENEW_AUTH_BOOTING = true;

  /*
    Sadece başlangıç sırasında görülen yanlış permission uyarısını bastır.
    Diğer alert'lere dokunmaz.
  */
  const nativeAlert = window.alert.bind(window);
  window.__renewNativeAlert = nativeAlert;

  window.alert = function(message){
    const text = String(message || '');
    if(
      window.RENEW_AUTH_BOOTING &&
      text.includes('Bu bölüm için yetkiniz yok')
    ){
      return;
    }
    return nativeAlert(message);
  };
})();

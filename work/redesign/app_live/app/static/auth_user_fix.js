(function(){
'use strict';

const FIX_VERSION = 'AUTH-USER-FIX-1.0.0';

function cookie(name){
  const m = document.cookie.match(
    new RegExp('(?:^|; )'+name.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'=([^;]*)')
  );
  return m ? decodeURIComponent(m[1]) : '';
}

async function requestJSON(url,opt={}){
  const method = String(opt.method || 'GET').toUpperCase();
  const headers = new Headers(opt.headers || {});

  if(['POST','PUT','PATCH','DELETE'].includes(method)){
    let token = '';

    try{
      if(typeof CSRF_TOKEN !== 'undefined' && CSRF_TOKEN){
        token = CSRF_TOKEN;
      }
    }catch(e){}

    token = token || cookie('renew_csrf');

    if(token && !headers.has('X-CSRF-Token')){
      headers.set('X-CSRF-Token',token);
    }
  }

  const r = await fetch(url,{
    ...opt,
    headers,
    credentials:'same-origin',
    cache:'no-store'
  });

  let data = null;
  const ct = r.headers.get('content-type') || '';

  try{
    data = ct.includes('application/json')
      ? await r.json()
      : await r.text();
  }catch(e){
    data = null;
  }

  if(!r.ok){
    let message = '';

    if(data && typeof data === 'object'){
      message = data.detail || data.message || JSON.stringify(data);
    }else{
      message = String(data || '');
    }

    throw new Error(message || ('HTTP '+r.status));
  }

  return data;
}

function currentHas(permission){
  try{
    return !!CURRENT_USER && (
      CURRENT_USER.role === 'administrator' ||
      (CURRENT_USER.permissions || []).includes(permission)
    );
  }catch(e){
    return false;
  }
}

function showLogin(){
  const overlay = document.getElementById('loginOverlay');
  if(overlay) overlay.classList.remove('hidden');
}

function hideLogin(){
  const overlay = document.getElementById('loginOverlay');
  if(overlay) overlay.classList.add('hidden');
}

function savedTarget(){
  try{
    return sessionStorage.getItem('renew_pending_page') || 'dashboard';
  }catch(e){
    return 'dashboard';
  }
}

function clearPending(){
  try{
    sessionStorage.removeItem('renew_pending_page');
  }catch(e){}
}

function safePage(target){
  let pageId = target || 'dashboard';

  if(pageId === 'users' && !currentHas('users.manage')){
    pageId = 'dashboard';
  }

  try{
    if(typeof page === 'function'){
      page(pageId);
    }
  }catch(e){
    console.warn('safePage:',e);
  }

  try{
    localStorage.setItem('renew_v6_page',pageId);
  }catch(e){}
}

async function restoreAuth(){
  const target = savedTarget();

  try{
    const me = await requestJSON('/api/auth/me');

    try{
      CURRENT_USER = me;
    }catch(e){}

    try{
      if(typeof CSRF_TOKEN !== 'undefined'){
        CSRF_TOKEN = me?.csrf_token || cookie('renew_csrf') || CSRF_TOKEN || '';
      }
    }catch(e){}

    hideLogin();

    try{
      if(typeof applyPermissions === 'function'){
        applyPermissions();
      }
    }catch(e){}

    /*
      app.js içindeki veri yüklemeleri auth oluşmadan başlamış olabilir.
      Kullanıcı belli olduktan sonra bir defa güvenli yenile.
    */
    try{
      if(typeof refreshAll === 'function'){
        await refreshAll();
      }
    }catch(e){
      console.warn('refreshAll after auth:',e);
    }

    window.RENEW_AUTH_BOOTING = false;
    safePage(target);
    clearPending();

    /*
      Eğer users sayfası açıldıysa listeyi kesin olarak yenile.
    */
    if(target === 'users' && currentHas('users.manage')){
      try{
        await window.loadUsers();
      }catch(e){}
    }

    console.log('RENEW',FIX_VERSION,'AUTH RESTORED');
    return true;

  }catch(err){
    window.RENEW_AUTH_BOOTING = false;

    try{
      CURRENT_USER = null;
    }catch(e){}

    showLogin();
    safePage('dashboard');
    clearPending();

    console.log('RENEW',FIX_VERSION,'NO SESSION');
    return false;
  }
}

/*
  app.js bittikten sonra PAGE fonksiyonunu güvenli hale getir.
  Auth yüklenirken kullanıcı sayfası istenirse sıraya alır.
*/
function installSafePage(){
  if(typeof window.page !== 'function' && typeof page !== 'function'){
    return;
  }

  const originalPage = window.page || page;

  const fixedPage = function(id){
    if(window.RENEW_AUTH_BOOTING){
      try{
        sessionStorage.setItem('renew_pending_page',id || 'dashboard');
      }catch(e){}
      return;
    }

    if(id === 'users' && !currentHas('users.manage')){
      const nativeAlert = window.__renewNativeAlert || window.alert;
      nativeAlert('Bu bölüm için yetkiniz yok.');
      return;
    }

    return originalPage(id);
  };

  try{ window.page = fixedPage; }catch(e){}
  try{ page = fixedPage; }catch(e){}
}

/*
  Kullanıcı listesini her çağrıda doğrudan sunucudan getir.
*/
window.loadUsers = async function(){
  if(!currentHas('users.manage')){
    return;
  }

  const tableBox = document.getElementById('usersTable');

  try{
    const result = await Promise.all([
      requestJSON('/api/users'),
      requestJSON('/api/users/meta')
    ]);

    try{ USERS = result[0] || []; }catch(e){}
    try{ USER_META = result[1] || {}; }catch(e){}

    if(typeof renderUsersClean === 'function'){
      renderUsersClean();
    }

  }catch(err){
    if(tableBox){
      tableBox.innerHTML =
        '<div class="error-box">❌ '+escapeHtml(err.message)+'</div>';
    }
    throw err;
  }
};

function escapeHtml(v){
  return String(v || '')
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;')
    .replace(/'/g,'&#039;');
}

async function freshUsers(){
  const users = await requestJSON('/api/users');
  try{ USERS = users || []; }catch(e){}
  return users || [];
}

async function saveUserFormPatched(e){
  e.preventDefault();

  const form = e.currentTarget;
  const fd = new FormData(form);
  const id = Number(form.dataset.editId || 0);
  const role = String(fd.get('role') || 'viewer');

  const err =
    document.getElementById('userFormError') ||
    document.getElementById('userFormErrorFinal');

  const btn =
    document.getElementById('userSaveBtn') ||
    form.querySelector('button[type="submit"]');

  const permissionInputs = form.querySelectorAll(
    'input[name="perm"]:checked'
  );

  let allAdminPermissions = [];

  try{
    allAdminPermissions =
      (USER_META && USER_META.roles && USER_META.roles.administrator)
      ? USER_META.roles.administrator
      : [];
  }catch(e){}

  const payload = {
    username:String(fd.get('username') || '').trim(),
    full_name:String(fd.get('full_name') || '').trim(),
    password:String(fd.get('password') || ''),
    role:role,
    permissions:
      role === 'administrator'
        ? allAdminPermissions
        : [...permissionInputs].map(x=>x.value),
    active:String(fd.get('active')) === 'true',
    must_change_password:
      String(fd.get('must_change_password')) === 'true'
  };

  function showError(msg){
    if(err){
      err.style.display='block';
      err.textContent='❌ '+msg;
    }else{
      (window.__renewNativeAlert || window.alert)('❌ '+msg);
    }
  }

  if(!payload.username){
    showError('Kullanıcı adı boş olamaz.');
    return;
  }

  if(!payload.full_name){
    showError('Ad Soyad boş olamaz.');
    return;
  }

  /*
    Yeni kullanıcıda şifre zorunlu.
    Mevcut kullanıcının şifresi boş bırakılabilir.
  */
  if(!id && !payload.password){
    showError('Yeni kullanıcı için ilk şifre zorunludur.');
    return;
  }

  if(btn){
    btn.disabled=true;
    btn.textContent='Kaydediliyor...';
  }

  if(err){
    err.style.display='none';
    err.textContent='';
  }

  try{
    let targetId = id;

    /*
      Loglarda POST /api/users -> 400 görülüyor.
      En yaygın sebep aynı kullanıcı adının zaten mevcut olması.
      Yeni kayıt formunda aynı kullanıcı varsa POST yerine o kullanıcıyı
      güncelleyerek yetki değişikliğinin kaybolmasını önlüyoruz.
    */
    if(!targetId){
      const users = await freshUsers();

      const existing = users.find(u=>
        String(u.username || '').trim().toLocaleLowerCase('tr-TR') ===
        payload.username.toLocaleLowerCase('tr-TR')
      );

      if(existing){
        targetId = Number(existing.id);

        /*
          Var olan kullanıcı güncellenirken formda şifre verilmediyse
          boş şifre gönderilir; backend mevcut şifreyi koruyor.
        */
      }
    }

    const url = targetId
      ? '/api/users/'+targetId
      : '/api/users';

    const method = targetId ? 'PUT' : 'POST';

    await requestJSON(url,{
      method,
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(payload)
    });

    /*
      Yetkiler gerçekten DB'den geri okunana kadar listeyi sunucudan yenile.
    */
    await window.loadUsers();

    /*
      Kendimizi düzenlediysek CURRENT_USER'ı da hemen tazele.
    */
    try{
      if(
        targetId &&
        CURRENT_USER &&
        Number(CURRENT_USER.id) === Number(targetId)
      ){
        const me = await requestJSON('/api/auth/me');
        CURRENT_USER = me;

        if(typeof CSRF_TOKEN !== 'undefined'){
          CSRF_TOKEN = me?.csrf_token || cookie('renew_csrf') || CSRF_TOKEN || '';
        }

        if(typeof applyPermissions === 'function'){
          applyPermissions();
        }
      }
    }catch(e){}

    if(typeof closeModal === 'function'){
      closeModal();
    }

    if(currentHas('users.manage')){
      safePage('users');
      await window.loadUsers();
    }

    (window.__renewNativeAlert || window.alert)(
      targetId && !id
        ? 'Kullanıcı zaten vardı; bilgileri ve yetkileri güncellendi.'
        : 'Kullanıcı ve yetkileri kaydedildi.'
    );

  }catch(ex){
    showError(ex.message || String(ex));
  }finally{
    if(btn){
      btn.disabled=false;
      btn.textContent='💾 Kaydet';
    }
  }
}

/*
  app.js içinde hem eski hem final kullanıcı editörü bulunduğu için
  ikisini de aynı sağlam kayıt fonksiyonuna bağla.
*/
try{ window.saveUserFormFinal = saveUserFormPatched; }catch(e){}
try{ saveUserFormFinal = saveUserFormPatched; }catch(e){}
try{ window.saveUserForm = saveUserFormPatched; }catch(e){}
try{ saveUserForm = saveUserFormPatched; }catch(e){}

/*
  Modal her açıldığında submit listener eski fonksiyonu referanslamış
  olabilir. Capture aşamasında userForm/userFormFinal submit'ini
  tek kayıt fonksiyonuna yönlendir.
*/
document.addEventListener('submit',function(e){
  const form = e.target;

  if(
    form &&
    (form.id === 'userFormFinal' || form.id === 'userForm')
  ){
    e.preventDefault();
    e.stopImmediatePropagation();
    saveUserFormPatched(e);
  }
},true);

/*
  Login başarılı olduğunda auth boot state kapansın.
*/
document.addEventListener('DOMContentLoaded',function(){
  installSafePage();

  /*
    app.js kendi checkAuth çağrılarını yapıyor; bunun yanında
    tek ve deterministik restore akışı çalıştırıyoruz.
  */
  setTimeout(restoreAuth,50);
});

window.RENEW_AUTH_FIX = {
  version:FIX_VERSION,
  restoreAuth,
  requestJSON
};

})();

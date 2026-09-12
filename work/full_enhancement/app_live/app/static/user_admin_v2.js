(function(){
'use strict';

const VERSION='2.0.0';
let AUTH_READY=false;
let USERS_V2=[];
let META_V2=null;

function $(s){return document.querySelector(s)}
function esc(v){
  return String(v??'')
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;')
    .replace(/'/g,'&#039;');
}
function cookie(name){
  const m=document.cookie.match(new RegExp('(?:^|; )'+name.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'=([^;]*)'));
  return m?decodeURIComponent(m[1]):'';
}
function csrf(){
  try{
    if(typeof CSRF_TOKEN!=='undefined' && CSRF_TOKEN) return CSRF_TOKEN;
  }catch(e){}
  return cookie('renew_csrf');
}
function normalizePerms(arr){return [...new Set((arr||[]).map(String))].sort()}
function sameArray(a,b){
  a=normalizePerms(a); b=normalizePerms(b);
  return a.length===b.length && a.every((x,i)=>x===b[i]);
}
async function req(url,opt={}){
  const method=String(opt.method||'GET').toUpperCase();
  const headers=new Headers(opt.headers||{});
  if(['POST','PUT','PATCH','DELETE'].includes(method)){
    const t=csrf();
    if(t) headers.set('X-CSRF-Token',t);
  }
  const r=await fetch(url,{...opt,headers,credentials:'same-origin',cache:'no-store'});
  const ct=r.headers.get('content-type')||'';
  let data=null;
  try{data=ct.includes('json')?await r.json():await r.text()}catch(e){data=null}
  if(!r.ok){
    let msg='';
    if(data && typeof data==='object'){
      if(Array.isArray(data.detail)) msg=data.detail.map(x=>x.msg||JSON.stringify(x)).join(' • ');
      else msg=data.detail||data.message||JSON.stringify(data);
    }else msg=String(data||'');
    const err=new Error(msg||`HTTP ${r.status}`);
    err.status=r.status;
    err.payload=data;
    throw err;
  }
  return data;
}
function has(permission){
  try{
    return !!CURRENT_USER && (
      CURRENT_USER.role==='administrator' ||
      (CURRENT_USER.permissions||[]).includes(permission)
    );
  }catch(e){return false}
}
function setCurrentUser(u){
  try{CURRENT_USER=u}catch(e){}
  try{
    if(typeof CSRF_TOKEN!=='undefined') CSRF_TOKEN=u?.csrf_token||cookie('renew_csrf')||'';
  }catch(e){}
}
function loginVisible(show){
  const el=$('#loginOverlay');
  if(!el)return;
  el.classList.toggle('hidden',!show);
  el.style.visibility=show?'visible':'hidden';
  el.style.opacity=show?'1':'0';
}
function finishAuthVisual(){document.documentElement.classList.remove('renew-auth-pending')}
function getSavedPage(){
  try{return sessionStorage.getItem('renew_auth_target')||localStorage.getItem('renew_v6_page')||'dashboard'}
  catch(e){return 'dashboard'}
}
function rememberTarget(){
  try{sessionStorage.setItem('renew_auth_target',localStorage.getItem('renew_v6_page')||'dashboard')}catch(e){}
}
function clearTarget(){try{sessionStorage.removeItem('renew_auth_target')}catch(e){}}
function safeOriginalPage(id){
  const fn=window.__renewOriginalPageV2;
  if(typeof fn==='function') return fn(id||'dashboard');
}
function gotoAfterAuth(){
  let target=getSavedPage();
  if(target==='users' && !has('users.manage')) target='dashboard';
  if(!document.getElementById(target)) target='dashboard';
  safeOriginalPage(target);
  clearTarget();
}
async function refreshAppOnce(){
  try{if(typeof refreshAll==='function') await refreshAll()}
  catch(e){console.warn('RENEW USER ADMIN V2 refreshAll:',e)}
}
async function restoreSession(){
  rememberTarget();
  try{
    const me=await req('/api/auth/me');
    setCurrentUser(me);
    try{if(typeof applyPermissions==='function')applyPermissions()}catch(e){}
    loginVisible(false);
    AUTH_READY=true;
    finishAuthVisual();
    await refreshAppOnce();
    gotoAfterAuth();
    console.log('[RENEW USER ADMIN V2] Session restored',VERSION);
    return true;
  }catch(e){
    setCurrentUser(null);
    AUTH_READY=true;
    finishAuthVisual();
    loginVisible(true);
    try{safeOriginalPage('dashboard')}catch(_){}
    console.log('[RENEW USER ADMIN V2] No active session');
    return false;
  }
}

function installPageGuard(){
  if(!window.__renewOriginalPageV2) window.__renewOriginalPageV2=window.page;
  window.page=function(id){
    if(!AUTH_READY){
      try{sessionStorage.setItem('renew_auth_target',id||'dashboard')}catch(e){}
      return;
    }
    if(id==='users' && !has('users.manage')){
      alert('Bu bölüm için yetkiniz yok.');
      return;
    }
    const r=safeOriginalPage(id);
    if(id==='users' && has('users.manage')) window.loadUsers();
    return r;
  };
  try{page=window.page}catch(e){}
}

async function loginSubmit(e){
  e.preventDefault();
  const msg=$('#loginMessage');
  if(msg)msg.textContent='';
  const username=String($('#loginUsername')?.value||'').trim();
  const password=String($('#loginPassword')?.value||'');
  if(!username||!password){
    if(msg)msg.textContent='❌ Kullanıcı adı ve şifre gerekli.';
    return;
  }
  try{
    const user=await req('/api/auth/login',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({username,password})
    });
    setCurrentUser(user);
    AUTH_READY=true;
    try{if(typeof applyPermissions==='function')applyPermissions()}catch(e){}
    loginVisible(false);
    finishAuthVisual();
    await refreshAppOnce();
    gotoAfterAuth();
    if(user.must_change_password && typeof openPasswordChange==='function'){
      setTimeout(()=>openPasswordChange(true),250);
    }
  }catch(err){
    if(msg)msg.textContent='❌ '+err.message;
  }
}

async function loadUsersV2(){
  if(!has('users.manage')) return;
  try{
    [USERS_V2,META_V2]=await Promise.all([req('/api/users'),req('/api/users/meta')]);
    try{USERS=USERS_V2}catch(e){}
    try{USER_META=META_V2}catch(e){}
    renderUsersV2();
  }catch(err){
    const box=$('#usersTable');
    if(box)box.innerHTML='<div class="error-box">❌ '+esc(err.message)+'</div>';
  }
}

function roleLabel(r){
  return ({administrator:'Administrator',manager:'Yönetici',editor:'Veri Girişi',viewer:'Görüntüleme'})[r]||r;
}
function roleBadge(r){return `<span class="role-badge role-${esc(r)}">${esc(roleLabel(r))}</span>`}
function renderUsersV2(){
  const box=$('#usersTable');
  if(!box)return;
  const q=String($('#userSearch')?.value||'').toLocaleUpperCase('tr-TR');
  const rf=$('#userRoleFilter')?.value||'';
  const sf=$('#userStatusFilter')?.value||'';
  const rows=(USERS_V2||[]).filter(u=>{
    const t=`${u.username||''} ${u.full_name||''}`.toLocaleUpperCase('tr-TR');
    return (!q||t.includes(q))&&(!rf||u.role===rf)&&(!sf||(sf==='active'?!!u.active:!u.active));
  });
  const tbody=rows.map(u=>`
    <tr>
      <td><div class="user-cell"><span class="user-avatar">${esc((u.full_name||u.username||'?').charAt(0).toUpperCase())}</span><div><b>${esc(u.username)}</b><small>#${esc(u.id)}</small></div></div></td>
      <td><b>${esc(u.full_name)}</b></td>
      <td>${roleBadge(u.role)}</td>
      <td>${u.active?'<span class="status-pill active">● AKTİF</span>':'<span class="status-pill passive">● PASİF</span>'}</td>
      <td>${u.role==='administrator'?'<b>Tüm Yetkiler</b>':`<b>${(u.permissions||[]).length}</b> yetki`}</td>
      <td><div class="row-actions"><button class="btn small" onclick="openUserEditor(${Number(u.id)})">✏ Düzenle</button>${Number(u.id)!==Number((window.CURRENT_USER||{}).id)?`<button class="btn danger small" onclick="deleteUser(${Number(u.id)})">Sil</button>`:''}</div></td>
    </tr>`).join('');
  box.innerHTML=`<div class="tablewrap"><table><thead><tr><th>Kullanıcı</th><th>Ad Soyad</th><th>Rol</th><th>Durum</th><th>Yetki</th><th>İşlem</th></tr></thead><tbody>${tbody||'<tr><td colspan="6">Kullanıcı bulunamadı.</td></tr>'}</tbody></table></div>`;
}

function permissionsHtml(selected,role){
  const meta=META_V2||{},groups=meta.groups||{},labels=meta.permissions||{},chosen=new Set(selected||[]);
  const disabled=role==='administrator';
  if(Object.keys(groups).length){
    return Object.entries(groups).map(([title,keys])=>`
      <div class="perm-group">
        <div class="perm-group-title">
          <b>${esc(title)}</b>
          ${disabled?'':`<button type="button" class="mini-link" data-perm-all="1">Tümünü Seç</button><button type="button" class="mini-link" data-perm-clear="1">Temizle</button>`}
        </div>
        <div class="perm-grid">${(keys||[]).map(k=>`<label class="perm-item"><input type="checkbox" name="perm" value="${esc(k)}" ${disabled||chosen.has(k)?'checked':''} ${disabled?'disabled':''}><span>${esc(labels[k]||k)}</span></label>`).join('')}</div>
      </div>`).join('');
  }
  return `<div class="perm-grid">${Object.entries(labels).map(([k,label])=>`<label class="perm-item"><input type="checkbox" name="perm" value="${esc(k)}" ${disabled||chosen.has(k)?'checked':''} ${disabled?'disabled':''}><span>${esc(label)}</span></label>`).join('')}</div>`;
}

async function openEditorV2(id=null){
  if(!has('users.manage')) return alert('Bu bölüm için yetkiniz yok.');
  if(!META_V2) await loadUsersV2();
  const uid=id==null?null:Number(id);
  const u=uid?USERS_V2.find(x=>Number(x.id)===uid):null;
  const role=u?.role||'viewer';
  const defaults=(META_V2?.roles||{})[role]||[];
  const perms=u?.permissions||defaults;
  if(typeof showModal!=='function') return alert('Modal sistemi bulunamadı.');

  showModal(u?'Kullanıcı Düzenle':'Yeni Kullanıcı',`
    <form id="userAdminV2Form" class="user-editor" novalidate>
      <div class="user-editor-grid">
        <label><span>Kullanıcı Adı *</span><input name="username" required autocomplete="off" value="${esc(u?.username||'')}"></label>
        <label><span>Ad Soyad *</span><input name="full_name" required value="${esc(u?.full_name||'')}"></label>
        <label><span>Rol *</span><select name="role">${Object.keys(META_V2?.roles||{}).map(r=>`<option value="${esc(r)}" ${r===role?'selected':''}>${esc(roleLabel(r))}</option>`).join('')}</select></label>
        <label><span>${u?'Yeni Şifre':'İlk Şifre *'}</span><input name="password" type="password" ${u?'':'required minlength="10"'} placeholder="${u?'Değiştirmeyeceksen boş bırak':'En az 10 karakter'}"></label>
        <label><span>Durum</span><select name="active"><option value="true" ${u?.active!==false?'selected':''}>Aktif</option><option value="false" ${u?.active===false?'selected':''}>Pasif</option></select></label>
        <label><span>İlk Girişte Şifre Değiştir</span><select name="must_change_password"><option value="false" ${!u?.must_change_password?'selected':''}>Hayır</option><option value="true" ${u?.must_change_password?'selected':''}>Evet</option></select></label>
      </div>
      <div class="permission-box">
        <div class="permission-head"><div><h3>Yetkiler</h3><p>Kullanıcının erişebileceği bölümleri seçin.</p></div><span id="userAdminV2RoleNote"></span></div>
        <div id="userAdminV2Permissions">${permissionsHtml(perms,role)}</div>
      </div>
      <div id="userAdminV2Error" class="error-box" style="display:none"></div>
      <div class="actions"><button type="button" class="btn ghost" onclick="closeModal()">Vazgeç</button><button id="userAdminV2Save" type="submit" class="btn success">💾 Kaydet</button></div>
    </form>`);

  const form=$('#userAdminV2Form');
  form.dataset.editId=u?String(u.id):'';
  form.elements.role.addEventListener('change',()=>{
    const r=form.elements.role.value;
    const existing=(u&&u.role===r)?u.permissions:((META_V2?.roles||{})[r]||[]);
    $('#userAdminV2Permissions').innerHTML=permissionsHtml(existing,r);
    bindPermissionButtons();
    updateRoleNote(r);
  });
  form.addEventListener('submit',saveUserV2);
  bindPermissionButtons();
  updateRoleNote(role);
}
function updateRoleNote(role){
  const n=$('#userAdminV2RoleNote');
  if(n)n.textContent=role==='administrator'?'Administrator tüm yetkilere sahiptir.':'';
}
function bindPermissionButtons(){
  document.querySelectorAll('#userAdminV2Permissions [data-perm-all]').forEach(b=>{
    b.onclick=()=>b.closest('.perm-group')?.querySelectorAll('input[name="perm"]').forEach(x=>x.checked=true);
  });
  document.querySelectorAll('#userAdminV2Permissions [data-perm-clear]').forEach(b=>{
    b.onclick=()=>b.closest('.perm-group')?.querySelectorAll('input[name="perm"]').forEach(x=>x.checked=false);
  });
}

async function saveUserV2(e){
  e.preventDefault();
  const form=e.currentTarget;
  const id=Number(form.dataset.editId||0);
  const fd=new FormData(form);
  const role=String(fd.get('role')||'viewer');
  const err=$('#userAdminV2Error');
  const btn=$('#userAdminV2Save');

  const payload={
    username:String(fd.get('username')||'').trim(),
    full_name:String(fd.get('full_name')||'').trim(),
    password:String(fd.get('password')||''),
    role,
    permissions:role==='administrator'
      ? normalizePerms((META_V2?.roles||{}).administrator||[])
      : normalizePerms([...form.querySelectorAll('input[name="perm"]:checked')].map(x=>x.value)),
    active:String(fd.get('active'))==='true',
    must_change_password:String(fd.get('must_change_password'))==='true'
  };

  function fail(msg){err.style.display='block';err.textContent='❌ '+msg}
  err.style.display='none';

  if(!payload.username)return fail('Kullanıcı adı zorunludur.');
  if(!payload.full_name)return fail('Ad Soyad zorunludur.');
  if(!id && payload.password.length<10)return fail('Yeni kullanıcı şifresi en az 10 karakter olmalıdır.');

  if(!id){
    const exists=USERS_V2.find(x=>String(x.username||'').trim().toLocaleLowerCase('tr-TR')===payload.username.toLocaleLowerCase('tr-TR'));
    if(exists)return fail(`"${payload.username}" kullanıcı adı zaten mevcut. Mevcut kullanıcıyı Düzenle ile açın.`);
  }

  btn.disabled=true;
  btn.textContent='Kaydediliyor...';

  try{
    await req(id?`/api/users/${id}`:'/api/users',{
      method:id?'PUT':'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(payload)
    });

    const fresh=await req('/api/users');
    const saved=id
      ? fresh.find(x=>Number(x.id)===id)
      : fresh.find(x=>String(x.username||'').toLocaleLowerCase('tr-TR')===payload.username.toLocaleLowerCase('tr-TR'));

    if(!saved)throw new Error('Sunucu başarılı yanıt verdi ancak kullanıcı geri okunamadı.');

    if(saved.username!==payload.username || saved.full_name!==payload.full_name || saved.role!==payload.role || Boolean(saved.active)!==Boolean(payload.active)){
      throw new Error('Kullanıcı kaydı doğrulaması başarısız: sunucudaki kayıt gönderilen bilgiyle eşleşmiyor.');
    }
    if(payload.role!=='administrator' && !sameArray(saved.permissions,payload.permissions)){
      throw new Error('Yetki kaydı doğrulaması başarısız: seçilen yetkiler veritabanına tam yansımadı.');
    }

    USERS_V2=fresh;
    try{USERS=fresh}catch(e){}

    try{
      if(id && Number(CURRENT_USER?.id)===id){
        const me=await req('/api/auth/me');
        setCurrentUser(me);
        if(typeof applyPermissions==='function')applyPermissions();
      }
    }catch(e){}

    if(typeof closeModal==='function')closeModal();
    renderUsersV2();
    alert(id?'Kullanıcı ve yetkileri güncellendi.':'Yeni kullanıcı oluşturuldu.');
  }catch(ex){
    fail(ex.message||String(ex));
  }finally{
    btn.disabled=false;
    btn.textContent='💾 Kaydet';
  }
}

async function deleteUserV2(id){
  if(!has('users.manage'))return alert('Bu bölüm için yetkiniz yok.');
  id=Number(id);
  if(Number(CURRENT_USER?.id)===id)return alert('Aktif kullanıcı kendi hesabını silemez.');
  if(!confirm('Bu kullanıcı silinsin mi?'))return;
  try{
    await req(`/api/users/${id}`,{method:'DELETE'});
    await loadUsersV2();
  }catch(e){
    alert('Silme başarısız: '+e.message);
  }
}

function installOverrides(){
  window.loadUsers=loadUsersV2;
  window.openUserEditor=openEditorV2;
  window.deleteUser=deleteUserV2;
  try{loadUsers=loadUsersV2}catch(e){}
  try{openUserEditor=openEditorV2}catch(e){}
  try{deleteUser=deleteUserV2}catch(e){}
  const lf=$('#loginForm');
  if(lf)lf.onsubmit=loginSubmit;
  installPageGuard();
  ['userSearch','userRoleFilter','userStatusFilter'].forEach(id=>{
    const el=$('#'+id);
    if(el)el.addEventListener(id==='userSearch'?'input':'change',renderUsersV2);
  });
}

async function boot(){
  installOverrides();
  await restoreSession();
  installOverrides();
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded',()=>setTimeout(boot,0),{once:true});
}else{
  setTimeout(boot,0);
}

window.RENEW_USER_ADMIN_V2={version:VERSION,restoreSession,loadUsers:loadUsersV2};
})();

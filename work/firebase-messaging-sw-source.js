import {initializeApp} from 'firebase/app';
import {getMessaging,onBackgroundMessage} from 'firebase/messaging/sw';

const app=initializeApp({
  apiKey:'AIzaSyC0dSWVPNfT9str9wo-BLro5xoMyQnvC6s',
  authDomain:'renew-43298.firebaseapp.com',
  projectId:'renew-43298',
  storageBucket:'renew-43298.firebasestorage.app',
  messagingSenderId:'343449047493',
  appId:'1:343449047493:web:3f28664b43242b00ce3bac'
});

const messaging=getMessaging(app);
onBackgroundMessage(messaging,payload=>{
  const notification=payload.notification||{};
  const data=payload.data||{};
  self.registration.showNotification(notification.title||data.title||'RENEW PRO',{
    body:notification.body||data.body||'',
    icon:'/static/renew-pro-favicon-white.png',
    badge:'/static/renew-pro-favicon-white.png',
    data:{url:data.url||'/?page=notifications'}
  });
});

self.addEventListener('notificationclick',event=>{
  event.notification.close();
  event.waitUntil(clients.openWindow(event.notification.data?.url||'/?page=notifications'));
});

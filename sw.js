/* 땡큐와인 앱(홈 화면에 추가) 서비스 워커: 알림 받기·알림 누르면 열기.
   화면은 늘 인터넷에서 새로 받아요(오래된 가격이 남지 않게). 인터넷이 끊겼을 때만 안내 문구를 보여 줘요. */
const OFFLINE = '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>땡큐와인</title>'
  + '<body style="font-family:system-ui,sans-serif;text-align:center;padding:80px 24px;color:#1a1a1a">'
  + '<p style="color:#7a1f33;font-weight:700;font-size:20px">땡큐와인</p><p>인터넷에 연결되면 다시 열어 주세요.</p>'
  + '<p><a href="/" style="color:#7a1f33">다시 시도</a></p></body>';

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));

self.addEventListener('fetch', e => {
  if (e.request.mode !== 'navigate') return;
  e.respondWith(fetch(e.request).catch(() => new Response(OFFLINE, { headers: { 'content-type': 'text/html; charset=utf-8' } })));
});

self.addEventListener('push', e => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (_) { d = { body: e.data ? e.data.text() : '' }; }
  const opt = {
    body: d.body || '',
    icon: '/assets/app/icon-192.png',
    badge: '/assets/app/badge-96.png',
    tag: d.tag || 'ty',
    data: { url: d.url || '/' },
  };
  if (d.image) opt.image = d.image;
  e.waitUntil(self.registration.showNotification(d.title || '땡큐와인', opt));
});

self.addEventListener('notificationclick', e => {
  e.notification.close();
  let url = '/';
  try { const u = new URL((e.notification.data && e.notification.data.url) || '/', self.location.origin); if (u.origin === self.location.origin) url = u.href; } catch (_) {}
  e.waitUntil((async () => {
    const list = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    for (const c of list) {
      if (new URL(c.url).origin === self.location.origin && 'focus' in c) { await c.focus(); if ('navigate' in c) return c.navigate(url); return; }
    }
    return self.clients.openWindow(url);
  })());
});

// 브라우저가 알림 주소를 바꾸면 새 주소로 다시 등록해요.
self.addEventListener('pushsubscriptionchange', e => {
  e.waitUntil((async () => {
    try {
      const old = e.oldSubscription;
      const SB = 'https://bgkignhdshaclcgxrsbp.supabase.co', KEY = 'sb_publishable_Ep0Axlpg3mvLQuA1a4BFzw_orvuNKob';
      const h = { apikey: KEY, 'content-type': 'application/json' };
      let topics = ['sale', 'new'];
      if (old) {
        const r = await fetch(SB + '/rest/v1/rpc/ty_push_status', { method: 'POST', headers: h, body: JSON.stringify({ p_endpoint: old.endpoint }) });
        const j = r.ok ? await r.json() : []; if (j && j[0] && j[0].topics) topics = j[0].topics; else return;
      }
      const sub = e.newSubscription || await self.registration.pushManager.subscribe(old ? old.options : { userVisibleOnly: true });
      const k = sub.toJSON().keys || {};
      await fetch(SB + '/rest/v1/rpc/ty_push_subscribe', { method: 'POST', headers: h, body: JSON.stringify({ p_endpoint: sub.endpoint, p_p256dh: k.p256dh, p_auth: k.auth, p_topics: topics, p_ua: 'renew' }) });
      if (old) await fetch(SB + '/rest/v1/rpc/ty_push_unsubscribe', { method: 'POST', headers: h, body: JSON.stringify({ p_endpoint: old.endpoint }) });
    } catch (_) {}
  })());
});

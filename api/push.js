// 땡큐와인 앱 알림 보내기 (Vercel Serverless Function)
// 관리자 화면(/admin/)에서 로그인한 관리자가 누를 때만 동작해요.
//  1) 브라우저가 보낸 로그인 토큰으로 Supabase 에 '관리자 맞나요?'(is_admin)를 물어요. 아니면 거절.
//  2) 같은 토큰으로 알림 서명 키(ty_push_config)와 받는 기기 목록(ty_push_subs)을 읽어요. (관리자만 읽을 수 있는 표)
//  3) 기기마다 알림을 보내고, 없어진 기기(404·410)는 목록에서 지워요. 결과를 ty_push_log 에 남겨요.
// 광고성 정보 규칙(정보통신망법 제50조): 제목 앞 '(광고)', 끝에 수신거부 방법, 밤 9시~아침 8시(한국 시간)엔 손님에게 보내지 않아요.
const webpush = require('web-push');

const SB = 'https://bgkignhdshaclcgxrsbp.supabase.co';
const KEY = 'sb_publishable_Ep0Axlpg3mvLQuA1a4BFzw_orvuNKob'; // 공개돼도 되는 키
const SITE = 'https://thankyouwine.com';
const TOPICS = { sale: '특가', new: '신규 입고' };
const OPTOUT = '수신거부: 땡큐와인 앱 › 알림 설정';

const clip = (s, n) => String(s || '').replace(/\s+/g, ' ').trim().slice(0, n);
const kstHour = () => (new Date().getUTCHours() + 9) % 24;
const isNight = () => { const h = kstHour(); return h >= 21 || h < 8; };

async function sb(path, token, opt = {}) {
  const r = await fetch(SB + path, {
    ...opt,
    headers: { apikey: KEY, authorization: 'Bearer ' + token, 'content-type': 'application/json', ...(opt.headers || {}) },
  });
  const text = await r.text();
  let data = null; try { data = text ? JSON.parse(text) : null; } catch { data = text; }
  if (!r.ok) throw new Error(`supabase ${r.status} ${typeof data === 'string' ? data : JSON.stringify(data)}`.slice(0, 300));
  return data;
}

// 손님이 받는 제목·내용 모양(관리자 화면 미리보기와 같은 규칙)
function shape({ topic, title, body }) {
  return {
    title: '(광고) ' + clip(title, 40),
    body: (clip(body, 120) + '\n' + OPTOUT).trim(),
  };
}

module.exports = async (req, res) => {
  res.setHeader('cache-control', 'no-store');
  if (req.method !== 'POST') { res.status(405).json({ ok: false, reason: 'method' }); return; }
  const token = String(req.headers.authorization || '').replace(/^Bearer\s+/i, '');
  if (!token) { res.status(401).json({ ok: false, reason: 'login' }); return; }

  let b = req.body;
  if (typeof b === 'string') { try { b = JSON.parse(b); } catch { b = null; } }
  if (!b || typeof b !== 'object') { res.status(400).json({ ok: false, reason: 'bad-json' }); return; }
  const topic = String(b.topic || '');
  if (!TOPICS[topic]) { res.status(400).json({ ok: false, reason: 'topic' }); return; }
  if (!clip(b.title, 40)) { res.status(400).json({ ok: false, reason: 'title' }); return; }
  const test = !!b.test;
  let url = String(b.url || '/');
  try { const u = new URL(url, SITE); url = u.origin === SITE ? u.pathname + u.search + u.hash : '/'; } catch { url = '/'; }
  let image = '';
  try { if (b.image) { const u = new URL(String(b.image), SITE); if (u.origin === SITE) image = u.href; } } catch {}

  try {
    const ok = await sb('/rest/v1/rpc/is_admin', token, { method: 'POST', body: '{}' });
    if (ok !== true) { res.status(403).json({ ok: false, reason: 'not-admin' }); return; }
    if (!test && isNight()) { res.status(400).json({ ok: false, reason: 'night' }); return; }

    const user = await sb('/auth/v1/user', token);
    const cfg = (await sb('/rest/v1/ty_push_config?select=public_key,private_key&id=eq.1', token))[0];
    if (!cfg) { res.status(400).json({ ok: false, reason: 'no-key' }); return; }

    // 보낼 기기: 시험이면 관리자 본인 기기(로그인한 계정으로 켠 기기 + 지금 이 브라우저)만
    let subs;
    if (test) {
      const mine = await sb(`/rest/v1/ty_push_subs?select=endpoint,p256dh,auth&user_id=eq.${encodeURIComponent(user.id)}`, token);
      const here = b.endpoint ? await sb(`/rest/v1/ty_push_subs?select=endpoint,p256dh,auth&endpoint=eq.${encodeURIComponent(String(b.endpoint))}`, token) : [];
      const m = new Map(); [...mine, ...here].forEach(s => m.set(s.endpoint, s)); subs = [...m.values()];
    } else {
      subs = await sb(`/rest/v1/ty_push_subs?select=endpoint,p256dh,auth&topics=cs.%7B${topic}%7D&limit=10000`, token);
    }
    if (!subs.length) { res.status(200).json({ ok: true, sent: 0, failed: 0, removed: 0, total: 0 }); return; }

    const s = shape({ topic, title: b.title, body: b.body });
    const payload = JSON.stringify({ title: s.title, body: s.body, url, image, tag: 'ty-' + topic + '-' + Date.now() });
    webpush.setVapidDetails('mailto:thankyouwine@gmail.com', cfg.public_key, cfg.private_key);

    let sent = 0, failed = 0; const gone = [];
    const queue = subs.slice();
    async function worker() {
      while (queue.length) {
        const x = queue.shift();
        try {
          await webpush.sendNotification({ endpoint: x.endpoint, keys: { p256dh: x.p256dh, auth: x.auth } }, payload, { TTL: 60 * 60 * 24, urgency: 'normal' });
          sent++;
        } catch (e) {
          failed++;
          if (e && (e.statusCode === 404 || e.statusCode === 410)) gone.push(x.endpoint);
        }
      }
    }
    await Promise.all(Array.from({ length: Math.min(20, queue.length) }, worker));

    for (let i = 0; i < gone.length; i += 50) {
      const list = gone.slice(i, i + 50).map(e => '"' + e.replace(/"/g, '\\"') + '"').join(',');
      await sb(`/rest/v1/ty_push_subs?endpoint=in.(${encodeURIComponent(list)})`, token, { method: 'DELETE' }).catch(() => {});
    }
    await sb('/rest/v1/ty_push_log', token, {
      method: 'POST', headers: { prefer: 'return=minimal' },
      body: JSON.stringify({ topic, title: s.title, body: clip(b.body, 120), url, test, sent, failed, removed: gone.length, by_email: user.email || '' }),
    }).catch(() => {});
    res.status(200).json({ ok: true, sent, failed, removed: gone.length, total: subs.length });
  } catch (e) {
    res.status(500).json({ ok: false, reason: 'server', detail: String(e && e.message || e).slice(0, 200) });
  }
};

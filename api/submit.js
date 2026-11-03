// 땡큐와인 접수 API (Vercel Serverless Function, Node 18+)
// 폼(모임 견적·선물 문의·일반 문의)을 받아 SUBMIT_WEBHOOK_URL(구글 앱스 스크립트 → 스프레드시트+메일)로 넘기고,
// RESEND_API_KEY + NOTIFY_EMAIL 이 있으면 이메일 알림도 보냅니다. 둘 다 없으면 503 → 사이트는 '복사해서 보내기' 안내로 전환.
const KINDS = { party: '모임·행사 와인 견적', gift: '기업·명절 선물 문의', ask: '일반 문의' };
const MAX_FIELDS = 40, MAX_LEN = 2000;

module.exports = async (req, res) => {
  res.setHeader('cache-control', 'no-store');
  if (req.method !== 'POST') { res.status(405).json({ ok: false, reason: 'method' }); return; }

  let body = req.body;
  if (typeof body === 'string') { try { body = JSON.parse(body); } catch { body = null; } }
  if (!body || typeof body !== 'object') { res.status(400).json({ ok: false, reason: 'bad-json' }); return; }

  const kind = String(body.kind || '');
  if (!KINDS[kind]) { res.status(400).json({ ok: false, reason: 'kind' }); return; }
  if (body.website) { res.status(200).json({ ok: true }); return; } // 봇이 채우는 숨은 칸: 조용히 무시

  const fields = {};
  const src = body.fields && typeof body.fields === 'object' ? body.fields : {};
  for (const [k, v] of Object.entries(src).slice(0, MAX_FIELDS)) {
    const key = String(k).slice(0, 60), val = String(v ?? '').replace(/\s+$/g, '').slice(0, MAX_LEN);
    if (key && val) fields[key] = val;
  }
  if (!Object.keys(fields).length) { res.status(400).json({ ok: false, reason: 'empty' }); return; }

  const record = {
    kind, kindLabel: KINDS[kind], fields,
    receivedAt: new Date().toISOString(),
    page: String(body.page || '').slice(0, 200),
    ua: String(req.headers['user-agent'] || '').slice(0, 200),
    ip: String(req.headers['x-forwarded-for'] || '').split(',')[0].trim(),
  };

  const hook = process.env.SUBMIT_WEBHOOK_URL;
  const resendKey = process.env.RESEND_API_KEY, notify = process.env.NOTIFY_EMAIL;
  if (!hook && !(resendKey && notify)) { res.status(503).json({ ok: false, reason: 'not-configured' }); return; }

  const errors = [];
  if (hook) {
    try {
      const r = await fetch(hook, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(record), redirect: 'follow' });
      if (!r.ok) errors.push('webhook-' + r.status);
    } catch (e) { errors.push('webhook-fail'); }
  }
  if (resendKey && notify) {
    const lines = Object.entries(fields).map(([k, v]) => `${k}: ${v}`).join('\n');
    try {
      const r = await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: { 'content-type': 'application/json', authorization: 'Bearer ' + resendKey },
        body: JSON.stringify({
          from: process.env.NOTIFY_FROM || 'Thank You Wine <onboarding@resend.dev>',
          to: [notify],
          subject: `[땡큐와인] ${KINDS[kind]} 접수`,
          text: `${KINDS[kind]}\n접수 ${record.receivedAt}\n\n${lines}\n\n(페이지 ${record.page})`,
        }),
      });
      if (!r.ok) errors.push('mail-' + r.status);
    } catch (e) { errors.push('mail-fail'); }
  }

  const sent = (hook ? 1 : 0) + (resendKey && notify ? 1 : 0);
  if (errors.length >= sent) { res.status(502).json({ ok: false, reason: errors.join(',') }); return; }
  res.status(200).json({ ok: true });
};

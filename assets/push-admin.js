/* 관리자 화면(/admin/) '앱 알림 보내기' (2026-11-25)
   - 관리자 계정일 때만 보여요(is_admin). 알림 서명 키가 없으면 '처음 켜기'로 이 브라우저에서 만들어 저장해요.
   - 보내기는 /api/push 가 해요. 손님에게 보내기 전에 '내 폰으로 먼저 받아 보기'로 확인해요. */
(function(){
  'use strict';
  const box=document.querySelector('[data-push-admin]'); if(!box) return;
  const $=s=>box.querySelector(s);
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const OPTOUT='수신거부: 땡큐와인 앱 › 알림 설정';
  const TOPIC={sale:'특가',new:'신규 입고'};
  let WINES=[]; try{WINES=JSON.parse((document.getElementById('push-wines')||{}).textContent||'[]')}catch(e){}
  const el={setup:$('[data-pa-setup]'),form:$('[data-pa-form]'),count:$('[data-pa-count]'),topic:$('[data-pa-topic]'),wine:$('[data-pa-wine]'),
    title:$('[data-pa-title]'),body:$('[data-pa-body]'),url:$('[data-pa-url]'),preview:$('[data-pa-preview]'),msg:$('[data-pa-msg]'),log:$('[data-pa-log]'),
    tlen:$('[data-pa-tlen]'),blen:$('[data-pa-blen]')};
  let image='', COUNTS={sale:0,new:0,all:0};
  box.hidden=true;
  WINES.forEach((w,i)=>{const o=document.createElement('option');o.value=i;o.textContent=w.k;el.wine.appendChild(o)});

  const kstHour=()=>(new Date().getUTCHours()+9)%24;
  const night=()=>{const h=kstHour();return h>=21||h<8};
  const fmt=t=>{const d=new Date(t);return `${d.getMonth()+1}/${d.getDate()} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`};
  const b64u=buf=>btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');

  function preview(){
    const t=el.title.value.trim()||'제목', b=el.body.value.trim();
    el.preview.innerHTML=`<img src="/assets/app/icon-192.png" alt=""><div><b>(광고) ${esc(t)}</b><span>${esc((b?b+'\n':'')+OPTOUT)}</span>${image?`<img src="${esc(image)}" alt="" style="width:auto;height:90px;margin-top:8px;border-radius:8px">`:''}</div>`;
    el.tlen.textContent=`${el.title.value.length}/40`; el.blen.textContent=`${el.body.value.length}/120`;
    const n=COUNTS[el.topic.value]||0;
    $('[data-pa-send]').textContent=`손님 ${n}명에게 보내기`;
    $('[data-pa-send]').disabled=!n;
  }
  ['input','change'].forEach(ev=>box.addEventListener(ev,e=>{ if(e.target.closest('[data-pa-title],[data-pa-body],[data-pa-topic],[data-pa-url]')) preview(); }));
  el.wine.addEventListener('change',()=>{
    const w=WINES[+el.wine.value];
    if(!w){image='';el.url.value='/wines/';preview();return}
    el.url.value=w.u; image=w.i||'';
    if(!el.title.value.trim()) el.title.value=w.k.slice(0,40);
    preview();
  });

  async function client(){ return window.TYMembers&&window.TYMembers.client; }
  async function load(){
    const c=await client(); if(!c) return;
    const {data:adm}=await c.rpc('is_admin'); if(adm!==true){box.hidden=true;return}
    box.hidden=false;
    const {data:key}=await c.rpc('ty_push_public_key');
    el.setup.hidden=!!key; el.form.hidden=!key;
    const {data:subs}=await c.from('ty_push_subs').select('topics').limit(10000);
    COUNTS={sale:0,new:0,all:(subs||[]).length};
    (subs||[]).forEach(s=>(s.topics||[]).forEach(t=>{if(t in COUNTS)COUNTS[t]++}));
    el.count.textContent=`알림 켠 기기 ${COUNTS.all}대 · 특가 ${COUNTS.sale} · 신규 입고 ${COUNTS.new}`;
    const {data:log}=await c.from('ty_push_log').select('*').order('sent_at',{ascending:false}).limit(10);
    el.log.innerHTML=(log||[]).map(l=>`<li><b>${esc(l.title)}</b> <span class="muted small">· ${TOPIC[l.topic]||l.topic} · ${fmt(l.sent_at)} · ${l.test?'내 폰 시험':'손님'} ${l.sent}대 보냄${l.failed?` · 실패 ${l.failed}`:''}${l.removed?` (지운 기기 ${l.removed})`:''}</span></li>`).join('')||'<li class="muted">아직 보낸 알림이 없어요.</li>';
    preview();
  }

  $('[data-pa-genkey]').addEventListener('click',async e=>{
    const b=e.target; b.disabled=true;
    try{
      const c=await client();
      const kp=await crypto.subtle.generateKey({name:'ECDSA',namedCurve:'P-256'},true,['sign','verify']);
      const pub=b64u(await crypto.subtle.exportKey('raw',kp.publicKey));
      const jwk=await crypto.subtle.exportKey('jwk',kp.privateKey);
      const {error}=await c.from('ty_push_config').insert({id:1,public_key:pub,private_key:jwk.d});
      if(error) throw error;
      el.msg.textContent='알림 기능을 켰어요. 이제 손님이 /app/ 에서 알림을 켤 수 있어요.';
      load();
    }catch(err){ el.msg.textContent='만들지 못했어요: '+(err.message||err); b.disabled=false; }
  });

  async function send(test){
    const title=el.title.value.trim(), body=el.body.value.trim(), topic=el.topic.value;
    if(!title){el.msg.textContent='제목을 적어 주세요.';el.title.focus();return}
    if(!test){
      if(night()){el.msg.textContent='밤 9시~아침 8시(한국 시간)엔 손님에게 보낼 수 없어요(광고성 정보 야간 전송 제한). 아침 8시 이후에 보내 주세요.';return}
      const n=COUNTS[topic]||0;
      if(!confirm(`${TOPIC[topic]} 소식을 손님 ${n}명에게 보낼까요?\n\n(광고) ${title}\n${body}\n\n보내면 되돌릴 수 없어요.`)) return;
    }
    const c=await client(); const {data}=await c.auth.getSession(); const tk=data&&data.session&&data.session.access_token;
    if(!tk){el.msg.textContent='다시 로그인해 주세요.';return}
    let endpoint='';
    try{ const r=await navigator.serviceWorker.getRegistration('/'); const s=r&&await r.pushManager.getSubscription(); endpoint=s?s.endpoint:''; }catch(e){}
    const btns=[...box.querySelectorAll('[data-pa-test],[data-pa-send]')]; btns.forEach(b=>b.disabled=true);
    el.msg.textContent=test?'내 폰으로 보내는 중…':'손님에게 보내는 중…';
    try{
      const r=await fetch('/api/push',{method:'POST',headers:{authorization:'Bearer '+tk,'content-type':'application/json'},
        body:JSON.stringify({topic,title,body,url:el.url.value.trim()||'/',image,test,endpoint})});
      const j=await r.json().catch(()=>({}));
      if(!r.ok||!j.ok){
        const why={night:'밤 9시~아침 8시엔 손님에게 보낼 수 없어요.','not-admin':'관리자 계정이 아니에요.','no-key':'알림 기능을 먼저 켜 주세요.',login:'다시 로그인해 주세요.'}[j.reason];
        el.msg.textContent='보내지 못했어요. '+(why||j.detail||('오류 '+r.status));
      }else if(!j.total){
        el.msg.textContent=test?'받을 내 기기가 없어요. 이 휴대폰에서 관리자 계정으로 로그인한 채 /app/ 에서 알림을 먼저 켜 주세요.':'보낼 손님이 없어요.';
      }else{
        el.msg.textContent=`${test?'내 기기':'손님'} ${j.sent}대에 보냈어요.`+(j.failed?` ${j.failed}대는 실패(그중 ${j.removed}대는 알림을 끈 기기라 목록에서 지웠어요).`:'');
      }
    }catch(e){ el.msg.textContent='보내지 못했어요. 인터넷 연결을 확인해 주세요.'; }
    finally{ btns.forEach(b=>b.disabled=false); load(); }
  }
  $('[data-pa-test]').addEventListener('click',()=>send(true));
  $('[data-pa-send]').addEventListener('click',()=>send(false));

  const start=()=>{ if(!window.TYMembers){setTimeout(start,200);return} window.TYMembers.onAuth(u=>{ if(u) load(); else box.hidden=true; }); if(window.TYMembers.user) load(); };
  start();
})();

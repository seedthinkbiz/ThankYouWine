/* 땡큐와인 앱(홈 화면에 추가)·알림 (2026-11-25)
   - 모든 페이지: 서비스 워커 등록, 휴대폰에서 '앱 받기'/'알림 켜기' 작은 안내(닫으면 2주 동안 안 보임)
   - /app/ : 기기별 설치 방법, 알림 켜기·끄기·받을 소식 고르기(특가·신규 입고)
   알림 주소는 Supabase 함수(ty_push_subscribe 등)로만 넣고 빼요. 목록은 관리자만 봐요(docs/supabase-push.sql). */
(function(){
  'use strict';
  const SB='https://bgkignhdshaclcgxrsbp.supabase.co', KEY='sb_publishable_Ep0Axlpg3mvLQuA1a4BFzw_orvuNKob';
  const $=(s,r)=>(r||document).querySelector(s);
  const $$=(s,r)=>[...(r||document).querySelectorAll(s)];
  const store={get(k){try{return JSON.parse(localStorage.getItem(k)||'null')}catch(e){return null}},
    set(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}};
  const REL=document.documentElement.dataset.rel||'';
  const ua=navigator.userAgent||'';
  const isIOS=/iPad|iPhone|iPod/.test(ua)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1);
  const isAndroid=/Android/i.test(ua);
  const isKakao=/KAKAOTALK/i.test(ua);
  const inApp=isKakao||/NAVER\(inapp|Instagram|FBAN|FBAV|FB_IAB|Line\/|DaumApps|BAND\/|everytimeApp|; wv\)/i.test(ua);
  const standalone=()=>(window.matchMedia&&matchMedia('(display-mode: standalone)').matches)||navigator.standalone===true;
  const mobile=isIOS||isAndroid;
  const pushOK=('serviceWorker' in navigator)&&('PushManager' in window)&&('Notification' in window)&&window.isSecureContext;
  const kdate=t=>{const d=t?new Date(t):new Date();return `${d.getFullYear()}년 ${d.getMonth()+1}월 ${d.getDate()}일`};

  /* ---------- 서비스 워커 ---------- */
  let regP=null;
  if(('serviceWorker' in navigator)&&window.isSecureContext&&!document.documentElement.hasAttribute('data-preview')){
    regP=navigator.serviceWorker.register('/sw.js',{scope:'/'}).catch(()=>null);
  }

  /* ---------- 설치 버튼(안드로이드 크롬·PC) ---------- */
  let deferred=null;
  window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();deferred=e;renderInstall()});
  window.addEventListener('appinstalled',()=>{deferred=null;store.set('ty-app-installed',Date.now());renderInstall()});

  /* ---------- 서버(Supabase 함수) ---------- */
  function token(){ // 로그인해 있으면 회원 계정으로 같이 저장(관리자 '내 폰으로 먼저 받아 보기'에 씀)
    try{const s=JSON.parse(localStorage.getItem('sb-bgkignhdshaclcgxrsbp-auth-token')||'null');
      if(s&&s.access_token&&(!s.expires_at||s.expires_at*1000>Date.now()+60000)) return s.access_token;}catch(e){}
    return '';
  }
  async function rpc(name,args,auth){
    const h={apikey:KEY,'content-type':'application/json'};
    const t=auth&&token(); if(t) h.authorization='Bearer '+t;
    let r=await fetch(SB+'/rest/v1/rpc/'+name,{method:'POST',headers:h,body:JSON.stringify(args||{})});
    if(r.status===401&&t){delete h.authorization; r=await fetch(SB+'/rest/v1/rpc/'+name,{method:'POST',headers:h,body:JSON.stringify(args||{})});}
    if(!r.ok) throw new Error('rpc '+name+' '+r.status);
    const x=await r.text(); return x?JSON.parse(x):null;
  }
  const b64u=s=>{s=String(s).replace(/-/g,'+').replace(/_/g,'/');while(s.length%4)s+='=';const b=atob(s);return Uint8Array.from(b,c=>c.charCodeAt(0))};
  async function reg(){ if(!regP) return null; await regP; return navigator.serviceWorker.ready; }
  async function currentSub(){ const r=await reg(); return r?r.pushManager.getSubscription():null; }
  async function serverStatus(sub){ if(!sub) return null; const j=await rpc('ty_push_status',{p_endpoint:sub.endpoint}); return j&&j[0]?j[0]:null; }

  /* ---------- 작은 안내 바(휴대폰) ---------- */
  const HIDE_KEY='ty-appbar-hide', HIDE_DAYS=14;
  const page=location.pathname;
  function appbar(){
    if(!mobile||/^\/(app|admin|login)\//.test(page)) return;
    const h=store.get(HIDE_KEY); if(h&&Date.now()-h<HIDE_DAYS*864e5) return;
    let text='', btn='', href=REL+'app/';
    if(!standalone()){ text='땡큐와인 앱으로 특가·신규 입고 소식을 먼저 받아 보세요'; btn='앱 받기'; }
    else if(pushOK&&Notification.permission==='default'){ text='알림을 켜 두면 특가·신규 입고 소식을 보내 드려요'; btn='알림 켜기'; href+='#alarm'; }
    else return;
    const el=document.createElement('div'); el.className='appbar'; el.setAttribute('role','region'); el.setAttribute('aria-label','땡큐와인 앱');
    el.innerHTML=`<img src="/assets/app/icon-192.png" alt="" width="40" height="40"><p>${text}</p><a class="btn wine sm" href="${href}">${btn}</a><button class="x" type="button" aria-label="닫기">×</button>`;
    el.querySelector('.x').addEventListener('click',()=>{store.set(HIDE_KEY,Date.now());el.remove()});
    el.querySelector('a').addEventListener('click',()=>store.set(HIDE_KEY,Date.now()));
    document.body.appendChild(el);
  }
  setTimeout(appbar,4000);

  /* ---------- /app/ 페이지 ---------- */
  const ap=$('[data-app-page]');
  function renderInstall(){
    if(!ap) return;
    const sa=standalone();
    $('[data-app-installed]',ap).hidden=!sa;
    $('[data-app-inapp]',ap).hidden=sa||!inApp;
    $('[data-app-prompt]',ap).hidden=sa||inApp||!deferred;
    $('[data-app-how]',ap).hidden=sa;
  }
  if(ap){
    const plat=isIOS?'ios':isAndroid?'android':'pc';
    const d=$(`[data-how="${plat}"]`,ap); if(d) d.open=true;
    const ext=$('[data-app-open-external]',ap), here='https://thankyouwine.com/app/';
    if(isKakao) ext.href='kakaotalk://web/openExternal?url='+encodeURIComponent(here);
    else if(isAndroid) ext.href='intent://thankyouwine.com/app/#Intent;scheme=https;end';
    else ext.hidden=true;
    $('[data-app-install-btn]',ap).addEventListener('click',async()=>{
      if(!deferred) return; deferred.prompt(); try{await deferred.userChoice}catch(e){} deferred=null; renderInstall();
    });
    renderInstall();
    initPush();
  }

  async function initPush(){
    const box=$('[data-app-push]',ap), form=$('[data-push-form]',box), un=$('[data-push-unsupported]',box), msg=$('[data-push-msg]',box);
    const on=$('[data-push-on]',box), save=$('[data-push-save]',box), off=$('[data-push-off]',box), consent=$('[data-push-consent]',box);
    const topics=()=>$$('[data-push-topic]',box).filter(b=>b.checked).map(b=>b.value);
    const say=(t,ok)=>{msg.textContent=t;msg.classList.toggle('ok',!!ok)};
    const unsupported=t=>{un.textContent=t;un.hidden=false;form.hidden=true};
    if(inApp) return unsupported('카카오톡 같은 앱 안의 화면에서는 알림을 켤 수 없어요. 위 1번처럼 기본 브라우저로 열어 주세요.');
    if(isIOS&&!standalone()) return unsupported('아이폰은 위 1번처럼 홈 화면에 추가한 다음, 홈 화면의 땡큐와인 앱을 열어 여기서 알림을 켜 주세요.');
    if(!pushOK) return unsupported('이 브라우저는 알림을 지원하지 않아요. 크롬이나 삼성 인터넷, 아이폰은 홈 화면에 추가한 땡큐와인 앱에서 열어 주세요.');
    form.hidden=false;
    const mode=(subscribed,st)=>{
      on.hidden=subscribed; save.hidden=!subscribed; off.hidden=!subscribed; consent.hidden=subscribed;
      if(subscribed&&st){ $$('[data-push-topic]',box).forEach(b=>b.checked=(st.topics||[]).includes(b.value));
        say(`알림을 받고 있어요. (${kdate(st.agreed_at)} 수신 동의)`,true); }
    };
    if(Notification.permission==='denied'){
      say('이 기기에서 땡큐와인 알림이 차단돼 있어요. 휴대폰 설정 › 알림(또는 브라우저의 사이트 설정)에서 땡큐와인 알림을 허용한 뒤 다시 눌러 주세요.');
    }
    try{ const sub=await currentSub(); const st=Notification.permission==='granted'?await serverStatus(sub):null; mode(!!st,st); }
    catch(e){ mode(false); }

    on.addEventListener('click',async()=>{
      const t=topics(); if(!t.length){say('받을 소식을 하나 이상 골라 주세요.');return}
      on.disabled=true; say('알림을 켜는 중이에요…');
      try{
        const perm=await Notification.requestPermission();   // 버튼을 누른 바로 그때 물어야 해요(아이폰)
        if(perm!=='granted'){ say(perm==='denied'?'알림이 차단됐어요. 휴대폰 설정 › 알림에서 땡큐와인을 허용한 뒤 다시 눌러 주세요.':'알림 허용을 눌러 주셔야 소식을 보낼 수 있어요.'); return; }
        const key=await rpc('ty_push_public_key');
        if(!key){ say('알림 기능을 준비하고 있어요. 조금 뒤에 다시 눌러 주세요.'); return; }
        const r=await reg(); if(!r) throw new Error('sw');
        let sub=await r.pushManager.getSubscription();
        if(!sub) sub=await r.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:b64u(key)});
        const k=sub.toJSON().keys||{};
        const at=await rpc('ty_push_subscribe',{p_endpoint:sub.endpoint,p_p256dh:k.p256dh,p_auth:k.auth,p_topics:t,p_ua:ua.slice(0,300)},true);
        mode(true,null);
        say(`${kdate(at)}, 땡큐와인(한낮의밤)의 ${t.map(x=>x==='sale'?'특가':'신규 입고').join('·')} 소식(광고성 정보) 수신에 동의하셨어요. 좋은 소식이 생기면 알려 드릴게요.`,true);
      }catch(e){ say('알림을 켜지 못했어요. 잠시 뒤 다시 눌러 주세요. 계속 안 되면 카톡으로 알려 주세요.'); }
      finally{ on.disabled=false; }
    });
    save.addEventListener('click',async()=>{
      const t=topics(); if(!t.length){off.click();return}
      save.disabled=true;
      try{ const sub=await currentSub(); const k=sub.toJSON().keys||{};
        await rpc('ty_push_subscribe',{p_endpoint:sub.endpoint,p_p256dh:k.p256dh,p_auth:k.auth,p_topics:t,p_ua:ua.slice(0,300)},true);
        say(`저장했어요. 앞으로 ${t.map(x=>x==='sale'?'특가':'신규 입고').join('·')} 소식만 보내 드려요.`,true);
      }catch(e){ say('저장하지 못했어요. 잠시 뒤 다시 눌러 주세요.'); }
      finally{ save.disabled=false; }
    });
    off.addEventListener('click',async()=>{
      off.disabled=true;
      try{ const sub=await currentSub(); if(sub){ await rpc('ty_push_unsubscribe',{p_endpoint:sub.endpoint}); await sub.unsubscribe().catch(()=>{}); }
        mode(false); $$('[data-push-topic]',box).forEach(b=>b.checked=true);
        say(`${kdate()}, 땡큐와인 소식 수신 거부가 처리됐어요. 알림을 더 보내지 않아요.`,true);
      }catch(e){ say('끄지 못했어요. 잠시 뒤 다시 눌러 주세요.'); }
      finally{ off.disabled=false; }
    });
  }
})();

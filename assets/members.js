/* 땡큐와인 회원: 로그인(login/), 내 와인(me/), 관리자 연결·장부 반영(admin/)
   - 코르크매치·비노나루와 같은 Supabase 회원(카카오·구글). 아래 두 값은 공개돼도 되는 값이에요.
   - 내가 산 와인은 매장 장부와 '연결'된 회원에게만 보여요. 연결은 관리자가 휴대폰 번호를 확인하고 해요.
   - 별점·한 줄 메모는 산 와인에만 남길 수 있어요(서버 규칙으로도 막혀 있어요). 가격은 어디에도 없어요. */
(function(){
  'use strict';
  const CFG={url:'https://bgkignhdshaclcgxrsbp.supabase.co',key:'sb_publishable_Ep0Axlpg3mvLQuA1a4BFzw_orvuNKob'};
  const $=(s,r)=>(r||document).querySelector(s);
  const $$=(s,r)=>[...(r||document).querySelectorAll(s)];
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const REL=document.documentElement.dataset.rel||'';
  const AGREE_KEY='ty-agree';
  const store={get(k){try{return JSON.parse(localStorage.getItem(k)||'null')}catch(e){return null}},
    set(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}},del(k){try{localStorage.removeItem(k)}catch(e){}}};
  const digits=s=>String(s||'').replace(/\D/g,'');
  const fmtPhone=s=>{const d=digits(s);return d.length===11?`${d.slice(0,3)}-${d.slice(3,7)}-${d.slice(7)}`:d.length===10?`${d.slice(0,3)}-${d.slice(3,6)}-${d.slice(6)}`:String(s||'').trim()};
  const fmtD=t=>{if(!t)return'';const [y,m,d]=String(t).slice(0,10).split('-');return `${y}.${+m}.${+d}`};
  const safeNext=n=>n&&n.startsWith('/')&&!n.startsWith('//')?n:'';

  let client=null, user=null, profile=null;
  try{ if(window.supabase&&window.supabase.createClient)
    client=window.supabase.createClient(CFG.url,CFG.key,{auth:{persistSession:true,autoRefreshToken:true,detectSessionInUrl:true,flowType:'pkce'}});
  }catch(e){client=null}
  const meta=u=>(u&&u.user_metadata)||{};
  const nameOf=u=>u?((profile&&profile.name)||meta(u).full_name||meta(u).name||meta(u).nickname||(u.email||'').split('@')[0]||'회원'):'';
  const providerOf=u=>{const p=u&&u.app_metadata&&u.app_metadata.provider;return p==='kakao'?'카카오':p==='google'?'구글':p==='email'?'이메일':(p||'')};

  /* 켜져 있는 로그인 수단만 보여요 (둘 다 꺼져 있으면 '곧 열려요') */
  const root=document.documentElement;
  root.classList.add('no-google','no-kakao','no-social');
  if(client) fetch(CFG.url+'/auth/v1/settings',{headers:{apikey:CFG.key}}).then(r=>r.ok?r.json():null).then(j=>{
    const ex=(j&&j.external)||{};
    root.classList.toggle('no-google',!ex.google); root.classList.toggle('no-kakao',!ex.kakao);
    root.classList.toggle('no-social',!ex.google&&!ex.kakao);
  }).catch(()=>{});

  async function login(provider,back){
    if(!client){alert('지금은 로그인을 쓸 수 없어요. 잠시 뒤 다시 해 주세요.');return}
    const opts={redirectTo:back};
    if(provider==='kakao') opts.scopes='profile_nickname profile_image account_email';
    const {error}=await client.auth.signInWithOAuth({provider,options:opts});
    if(error) alert('로그인 연결이 아직 준비 중이에요. 카톡으로 문의해 주세요.');
  }
  async function loadProfile(){
    profile=null; if(!client||!user) return null;
    const {data,error}=await client.from('ty_profiles').select('*').eq('id',user.id).maybeSingle();
    if(!error) profile=data||null; return profile;
  }
  async function saveProfile(d){
    if(!client||!user) return false;
    const row={id:user.id,name:(profile&&profile.name)||'',phone:(profile&&profile.phone)||'',agreed_at:(profile&&profile.agreed_at)||null,...d,email:user.email||'',updated_at:new Date().toISOString()};
    const {error}=await client.from('ty_profiles').upsert(row);
    if(error){console.warn('profile',error.message);return false}
    profile={...(profile||{}),...row}; return true;
  }
  const subs=[];
  let lastId='';
  async function setUser(u){ user=u; if((u&&u.id)!==lastId){lastId=u&&u.id; await loadProfile();} subs.forEach(f=>f(user)); }
  const onAuth=f=>{subs.push(f); if(!client) f(null)};
  if(client){
    client.auth.getSession().then(({data})=>setUser(data&&data.session?data.session.user:null));
    client.auth.onAuthStateChange((_e,s)=>{setTimeout(()=>setUser(s?s.user:null),0)});
  }

  document.addEventListener('click',e=>{
    const pb=e.target.closest('[data-login-provider]');
    if(!pb) return; e.preventDefault(); if(pb.disabled) return;
    if(pb.closest('[data-admin-login]')){ login(pb.dataset.loginProvider,location.href.split('#')[0]); return; }
    const back=new URL(REL+'me/',location.href); const n=safeNext(new URLSearchParams(location.search).get('next')||''); if(n) back.searchParams.set('next',n);
    login(pb.dataset.loginProvider,back.href);
  });
  document.addEventListener('click',async e=>{
    if(!e.target.closest('[data-logout]')) return; e.preventDefault();
    if(client) await client.auth.signOut().catch(()=>{}); location.href=REL||'./';
  });

  /* 사이트 와인 목록(키 → 이름·사진·스타일·나라·소개 글) */
  let WI={}; try{WI=JSON.parse(($('#wine-index')||{}).textContent||'{}')}catch(e){}

  /* ---------- 로그인·가입 ---------- */
  const lp=$('[data-login-page]');
  if(lp){
    const req=$$('[data-agree][required]',lp), all=$('[data-agree-all]',lp), boxes=$$('[data-agree]',lp);
    const sync=()=>{const ok=req.every(b=>b.checked);
      $$('[data-login-provider]',lp).forEach(b=>b.disabled=!ok);
      $('[data-login-hint]',lp).hidden=ok; all.checked=boxes.every(b=>b.checked);
      if(ok) store.set(AGREE_KEY,{at:new Date().toISOString()});};
    all.addEventListener('change',()=>{boxes.forEach(b=>b.checked=all.checked);sync()});
    boxes.forEach(b=>b.addEventListener('change',sync)); sync();
    onAuth(u=>{ if(u&&profile&&profile.agreed_at) location.replace(safeNext(new URLSearchParams(location.search).get('next')||'')||REL+'me/'); });
  }

  /* ---------- 내 와인 ---------- */
  const mp=$('[data-me-page]');
  if(mp){
    const out=$('[data-me-out]',mp), inn=$('[data-me-in]',mp), form=$('[data-me-form]',mp), msg=$('[data-me-msg]',mp);
    const consent=$('[data-me-consent]',mp), wait=$('[data-me-wait]',mp), box=$('[data-me-wines]',mp), list=$('[data-me-list]',mp);
    const tabs=$('[data-me-tabs]',mp), sum=$('[data-me-sum]',mp);
    let WINES=[], REV={}, TAB='all';

    function group(rows){
      const m=new Map();
      rows.forEach(r=>{const g=m.get(r.wine_key)||{key:r.wine_key,wine:r.wine,times:0,qty:0,last:'',first:''};
        g.times++; g.qty+=r.qty||0; if(!g.last||(r.date||'')>g.last) g.last=r.date||''; if(!g.first||(r.date||'')<g.first) g.first=r.date||'';
        m.set(r.wine_key,g)});
      return [...m.values()].sort((a,b)=>(b.last||'').localeCompare(a.last||''));
    }
    const STAR='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.8l2.8 5.9 6.4.8-4.7 4.4 1.2 6.4L12 17.2l-5.7 3.1 1.2-6.4-4.7-4.4 6.4-.8z"/></svg>';
    function stars(key,v){
      return `<div class="stars" role="radiogroup" aria-label="별점">${[1,2,3,4,5].map(n=>`<button type="button" class="st${v>=n?' on':''}" role="radio" aria-checked="${v===n}" aria-label="${n}점" data-star="${n}" data-key="${esc(key)}">${STAR}</button>`).join('')}</div>`;
    }
    function card(g){
      const w=WI[g.key]||null, r=REV[g.key]||{};
      const pic=w&&w.i?`<div class="wimg"><img src="${REL}${esc(w.i)}" alt="" loading="lazy" width="300" height="480"></div>`:`<div class="wimg none" aria-hidden="true">${$('.logo .mark')?$('.logo .mark').outerHTML:''}</div>`;
      const metaLine=[w&&w.s,w&&w.c].filter(Boolean).join(' · ');
      const post=w&&w.p?(w.p.startsWith('http')?`<a class="textlink" href="${esc(w.p)}" target="_blank" rel="noopener">소개 글 →</a>`:`<a class="textlink" href="${REL}${esc(w.p)}">소개 글 →</a>`):'';
      const bought=g.times>1?`${fmtD(g.last)} 외 ${g.times-1}번 더 샀어요`:`${fmtD(g.last)}에 샀어요`;
      return `<li class="wine mywine" data-key="${esc(g.key)}">${pic}<div class="wbody">
        ${metaLine?`<div class="wtop"><span class="wstyle">${esc(metaLine)}</span></div>`:''}
        <h3>${esc(w?w.k:g.wine)}</h3>
        <p class="wmeta bought">${esc(bought)}</p>
        ${stars(g.key,+r.stars||0)}
        <label class="memo"><span class="sr">한 줄 메모</span><input type="text" maxlength="100" placeholder="한 줄 메모 (예: 고기랑 최고, 다음엔 두 병)" value="${esc(r.note||'')}" data-note="${esc(g.key)}"></label>
        <p class="savemsg muted small" data-save-msg="${esc(g.key)}" aria-live="polite"></p>
        <div class="wacts"><button class="btn line sm" type="button" data-again="${esc(w?w.k:g.wine)}">다시 주문하기</button>${post}</div>
      </div></li>`;
    }
    function paint(){
      const rated=WINES.filter(g=>REV[g.key]&&REV[g.key].stars).length;
      sum.textContent=`산 와인 ${WINES.length}종 · 별점 ${rated}개`;
      $$('.chip',tabs).forEach(b=>{b.setAttribute('aria-pressed',b.dataset.tab===TAB);
        const n=b.dataset.tab==='todo'?WINES.length-rated:b.dataset.tab==='done'?rated:WINES.length; $('span',b).textContent=n;});
      const rows=WINES.filter(g=>TAB==='all'||(TAB==='done')===!!(REV[g.key]&&REV[g.key].stars));
      list.innerHTML=rows.map(card).join('')||`<p class="muted">${TAB==='todo'?'모든 와인에 별점을 남기셨어요. 고마워요!':'아직 별점을 남긴 와인이 없어요.'}</p>`;
    }
    async function saveReview(key,patch){
      const cur=REV[key]||{};
      const row={user_id:user.id,wine_key:key,stars:cur.stars??null,note:cur.note||'',...patch,updated_at:new Date().toISOString()};
      const m=$(`[data-save-msg="${CSS.escape(key)}"]`,list); if(m) m.textContent='저장하는 중…';
      const {error}=await client.from('ty_reviews').upsert(row);
      if(error){ if(m) m.textContent='저장하지 못했어요. 잠시 뒤 다시 해 주세요.'; return false }
      REV[key]={...cur,...row}; if(m) m.textContent='저장했어요'; return true;
    }
    list.addEventListener('click',async e=>{
      const s=e.target.closest('[data-star]');
      if(s){ const key=s.dataset.key, n=+s.dataset.star, cur=+((REV[key]||{}).stars||0);
        const v=cur===n?null:n;  // 같은 별을 다시 누르면 지워요
        $$(`[data-key="${CSS.escape(key)}"][data-star]`,list).forEach(b=>{b.classList.toggle('on',v>=+b.dataset.star);b.setAttribute('aria-checked',v===+b.dataset.star)});
        if(await saveReview(key,{stars:v})) sum.textContent=`산 와인 ${WINES.length}종 · 별점 ${WINES.filter(g=>REV[g.key]&&REV[g.key].stars).length}개`;
        return; }
      const a=e.target.closest('[data-again]');
      if(a){ const d=$('#contact'); if(!d) return;
        let p=$('.cdwine',d); if(!p){p=document.createElement('p');p.className='cdwine';$('.cdbody',d).prepend(p);
          d.addEventListener('close',()=>{p.hidden=true});}
        p.innerHTML=`다시 주문할 와인: <b>${esc(a.dataset.again)}</b> <button type="button" class="btn line sm" style="margin-left:8px">이름 복사</button>`;
        p.hidden=false; $('button',p).onclick=ev=>{try{navigator.clipboard.writeText(a.dataset.again+' 다시 주문하고 싶어요');ev.target.textContent='복사했어요'}catch(_){}};
        d.showModal(); }
    });
    list.addEventListener('change',e=>{const i=e.target.closest('[data-note]'); if(!i) return;
      const v=i.value.trim().slice(0,100); if(v===((REV[i.dataset.note]||{}).note||'')) return; saveReview(i.dataset.note,{note:v});});
    list.addEventListener('keydown',e=>{const i=e.target.closest('[data-note]'); if(i&&e.key==='Enter'){e.preventDefault();i.blur()}});
    tabs.addEventListener('click',e=>{const b=e.target.closest('[data-tab]'); if(!b) return; TAB=b.dataset.tab; paint();});

    async function loadWines(){
      // 관리자도 자기 구매만 보이게 연결된 장부 id로 꼭 거릅니다
      const {data:link}=await client.from('ty_links').select('ref,linked_at').eq('user_id',user.id).maybeSingle();
      const [{data:rows},{data:revs}]=await Promise.all([
        link?client.from('ty_purchases').select('id,date,wine_key,wine,qty').eq('ref',link.ref).order('date',{ascending:false}).limit(2000):Promise.resolve({data:[]}),
        client.from('ty_reviews').select('wine_key,stars,note,updated_at').eq('user_id',user.id)]);
      REV={}; (revs||[]).forEach(r=>REV[r.wine_key]=r);
      if(link){ const {data:pp}=await client.from('ty_prepaid').select('id,date,kind,amount,label').eq('ref',link.ref).order('date',{ascending:true}).limit(500); paintPrepaid(pp||[]); }
      else paintPrepaid([]);
      WINES=group(rows||[]);
      wait.hidden=!!link; box.hidden=!link;
      $('[data-me-wait-msg]',mp).textContent=profile&&profile.phone
        ?`${fmtPhone(profile.phone)} 번호로 매장 구매 기록을 찾아 연결해 드릴게요. 보통 하루 안에 연결되고, 연결되면 산 와인이 여기에 모여요.`
        :'휴대폰 번호를 남겨 주시면 매장에서 산 와인을 찾아 연결해 드려요.';
      if(link){ if(!WINES.length) list.innerHTML='<p class="muted">연결됐어요. 아직 기록된 구매가 없어요.</p>'; else paint(); }
    }
    const ppBox=$('[data-me-prepaid]',mp);
    const won=n=>Math.abs(n).toLocaleString('ko-KR')+'원';
    function paintPrepaid(rows){
      if(!ppBox) return;
      if(!rows.length){ppBox.hidden=true;return}
      const bal=rows.reduce((a,r)=>a+(r.amount||0),0);
      $('[data-pp-bal]',ppBox).textContent=won(bal);
      $('[data-pp-list]',ppBox).innerHTML=rows.slice().reverse().map(r=>`<li><span class="ppd">${fmtD(r.date)}</span><span class="ppl"><b>${esc(r.kind)}</b> ${esc(r.label||'')}</span><span class="ppa${r.amount<0?' out':''}">${r.amount<0?'−':'+'}${won(r.amount)}</span></li>`).join('');
      ppBox.hidden=false;
    }
    async function render(u){
      if(!u){out.hidden=false;inn.hidden=true;return}
      out.hidden=true; inn.hidden=false;
      if(!profile||!profile.agreed_at){
        const ag=store.get(AGREE_KEY);
        if(ag){ await saveProfile({name:nameOf(u),agreed_at:ag.at||new Date().toISOString()}); store.del(AGREE_KEY);
          $('[data-me-welcome]',mp).hidden=false;
          const n=safeNext(new URLSearchParams(location.search).get('next')||''); if(n&&n!==location.pathname){location.replace(n);return} }
      }
      const agreed=!!(profile&&profile.agreed_at);
      consent.hidden=agreed;
      $('[data-me-hello]',mp).textContent=`${nameOf(u)}님의 와인`;
      $('[data-me-sub]',mp).textContent=`${providerOf(u)} 계정으로 로그인했어요${u.email?' · '+u.email:''}`;
      form.name.value=(profile&&profile.name)||nameOf(u); form.phone.value=(profile&&profile.phone)||'';
      if(agreed) await loadWines(); else {wait.hidden=true; box.hidden=true}
    }
    form.addEventListener('submit',async e=>{e.preventDefault();
      const upd={};
      if(!profile||!profile.agreed_at){ if(!form.age.checked||!form.privacy.checked){msg.textContent='필수 항목에 동의해 주세요.';return} upd.agreed_at=new Date().toISOString(); }
      if(!form.name.value.trim()){msg.textContent='이름을 적어 주세요.';form.name.focus();return}
      const ph=digits(form.phone.value); if(ph&&!/^01\d{8,9}$/.test(ph)){msg.textContent='휴대폰 번호를 확인해 주세요.';form.phone.focus();return}
      Object.assign(upd,{name:form.name.value.trim().slice(0,50),phone:ph?fmtPhone(ph):''});
      msg.textContent='저장하는 중…';
      const ok=await saveProfile(upd);
      msg.textContent=ok?'저장했어요.':'저장하지 못했어요. 잠시 뒤 다시 해 주세요.';
      if(ok){consent.hidden=true; loadWines();}
    });
    $('[data-me-delete]',mp).addEventListener('click',async()=>{
      if(!confirm('탈퇴하면 땡큐와인 회원 정보와 별점·메모가 바로 지워져요. 매장 장부의 구매 기록(세금·영수증용)은 그대로 남아요. 탈퇴할까요?')) return;
      const {error}=await client.rpc('ty_leave');
      if(error){alert('탈퇴하지 못했어요. 010-8078-7493으로 문자 주시면 바로 처리할게요.');return}
      await client.auth.signOut().catch(()=>{}); alert('탈퇴했어요. 그동안 고마웠어요.'); location.href=REL||'./';
    });
    let chain=Promise.resolve();
    if(!client){out.hidden=false}
    onAuth(u=>{ if(client) chain=chain.then(()=>render(u)).catch(err=>console.warn(err)) });
  }

  /* ---------- 관리자: 회원 ↔ 장부 손님 연결, 구매 내역 반영 ---------- */
  const ap=$('[data-admin-page]');
  if(ap){
    const bar=$('[data-admin-bar]',ap), st=$('[data-admin-status]',ap), pend=$('[data-admin-pending]',ap), linked=$('[data-admin-linked]',ap);
    const fileIn=$('[data-admin-file]',ap), fileMsg=$('[data-admin-file-msg]',ap);
    let LEDGER=null, PROFILES=[], LINKS=[];
    const custOf=ref=>LEDGER&&LEDGER.customers.find(c=>c.ref===ref);
    function render(){
      const linkedIds=new Set(LINKS.map(l=>l.user_id));
      const waiting=PROFILES.filter(p=>!linkedIds.has(p.id)&&p.agreed_at);
      const opts=LEDGER?LEDGER.customers.filter(c=>!LINKS.some(l=>l.ref===c.ref)).map(c=>`<option value="${esc(c.ref)}">${esc(c.name)}${c.phone?' · '+esc(c.phone):''}</option>`).join(''):'';
      pend.innerHTML=waiting.length?waiting.map(p=>{
        const hit=LEDGER&&p.phone?LEDGER.customers.filter(c=>digits(c.phone)&&digits(c.phone)===digits(p.phone)):[];
        const sel=hit.length===1?hit[0].ref:'';
        return `<article class="arow" data-uid="${esc(p.id)}"><div class="ahead2"><b>${esc(p.name||'(이름 없음)')}</b><span class="muted small">${esc(p.phone||'번호 없음')} · ${esc(p.email)} · ${fmtD(p.created_at)} 가입</span></div>
          ${LEDGER?`<div class="linkrow"><select data-ref aria-label="장부 손님"><option value="">장부 손님 고르기</option>${opts.replace(`value="${esc(sel)}"`,`value="${esc(sel)}" selected`)}</select>
          <button class="btn wine sm" type="button" data-link>연결</button>${hit.length===1?'<span class="okmark">번호 일치</span>':hit.length>1?'<span class="muted small">같은 번호 손님이 여럿이에요</span>':p.phone?'<span class="muted small">같은 번호 없음</span>':''}</div>`:'<p class="muted small">장부 파일을 열면 같은 번호 손님을 찾아 드려요.</p>'}
        </article>`}).join(''):'<p class="muted">연결을 기다리는 회원이 없어요.</p>';
      linked.innerHTML=LINKS.length?LINKS.map(l=>{const p=PROFILES.find(x=>x.id===l.user_id)||{}, c=custOf(l.ref);
        return `<article class="arow" data-uid="${esc(l.user_id)}"><div class="ahead2"><b>${esc(p.name||'')}</b><span class="muted small">${esc(p.phone||'')} → 장부 ${esc(c?c.name:l.ref)} · ${fmtD(l.linked_at)} 연결</span>
          <button class="btn line sm" type="button" data-unlink>연결 끊기</button></div></article>`}).join(''):'<p class="muted">연결된 회원이 아직 없어요.</p>';
    }
    async function load(){
      if(!client||!user){bar.hidden=true;return}
      const [{data:ps,error:e1},{data:ls}]=await Promise.all([
        client.from('ty_profiles').select('*').order('created_at',{ascending:false}).limit(2000),
        client.from('ty_links').select('*').limit(2000)]);
      if(e1){st.textContent='불러오지 못했어요: '+e1.message;bar.hidden=true;return}
      PROFILES=ps||[]; LINKS=ls||[];
      if(PROFILES.length<=1&&!LINKS.length&&!(PROFILES[0]&&PROFILES[0].id!==user.id)){
        st.textContent=PROFILES.length?'아직 다른 회원이 없거나, 관리자로 등록된 계정이 아니에요.':'보이는 회원이 없어요. 관리자로 등록된 계정이 아니면 비어 보여요.'; }
      else st.textContent=`회원 ${PROFILES.length}명 · 연결 ${LINKS.length}명`;
      bar.hidden=false; render();
    }
    function rowsFor(ref){ return LEDGER.purchases.filter(p=>p.ref===ref).map(p=>({id:p.id,ref:p.ref,date:p.date||null,wine_key:p.key,wine:String(p.wine).slice(0,120),qty:p.qty||null,updated_at:new Date().toISOString()})) }
    async function push(ref){  // 이 손님 구매 줄만 올리고, 장부에서 지워진 줄은 서버에서도 지워요
      const rows=rowsFor(ref);
      if(rows.length){ const {error}=await client.from('ty_purchases').upsert(rows); if(error) throw error; }
      const {data:have}=await client.from('ty_purchases').select('id').eq('ref',ref).limit(5000);
      const keep=new Set(rows.map(r=>r.id)), gone=(have||[]).map(r=>r.id).filter(id=>!keep.has(id));
      if(gone.length){ const {error}=await client.from('ty_purchases').delete().in('id',gone); if(error) throw error; }
      // 선불권(이 손님 것만)
      const pp=(LEDGER.prepaid||[]).filter(p=>p.ref===ref).map(p=>({id:p.id,ref,date:p.date||null,kind:p.kind,amount:p.amount,label:String(p.label||'').slice(0,120),updated_at:new Date().toISOString()}));
      if(pp.length){ const {error}=await client.from('ty_prepaid').upsert(pp); if(error) throw error; }
      const {data:havePP}=await client.from('ty_prepaid').select('id').eq('ref',ref).limit(2000);
      const keepPP=new Set(pp.map(r=>r.id)), gonePP=(havePP||[]).map(r=>r.id).filter(id=>!keepPP.has(id));
      if(gonePP.length){ const {error}=await client.from('ty_prepaid').delete().in('id',gonePP); if(error) throw error; }
      return rows.length;
    }
    fileIn.addEventListener('change',async()=>{
      const f=fileIn.files[0]; if(!f) return;
      try{ const j=JSON.parse(await f.text()); if(j.kind!=='thankyouwine-ledger'||!Array.isArray(j.customers)||!Array.isArray(j.purchases)) throw new Error('형식');
        LEDGER=j; fileMsg.textContent=`${f.name} · 손님 ${j.customers.length}명 · ${fmtD(j.made)} 만든 파일 (파일은 이 브라우저 안에서만 읽어요)`; render();
      }catch(e){ LEDGER=null; fileMsg.textContent='장부 파일이 아니에요. ledger_export.py 로 만든 파일을 골라 주세요.'; }
    });
    ap.addEventListener('click',async e=>{
      const lb=e.target.closest('[data-link]');
      if(lb){ const row=lb.closest('[data-uid]'), uid=row.dataset.uid, ref=$('[data-ref]',row).value;
        if(!ref){alert('장부 손님을 골라 주세요.');return}
        const p=PROFILES.find(x=>x.id===uid)||{}, c=custOf(ref)||{};
        if(digits(p.phone)!==digits(c.phone)&&!confirm(`회원 번호(${p.phone||'없음'})와 장부 번호(${c.phone||'없음'})가 달라요. 본인이 맞는지 확인하셨나요?`)) return;
        lb.disabled=true;
        try{ const {error}=await client.from('ty_links').insert({user_id:uid,ref}); if(error) throw error;
          const n=await push(ref); st.textContent=`${p.name||''}님 연결, 구매 ${n}줄 반영했어요.`; await load();
        }catch(err){ alert('연결하지 못했어요: '+(err.message||err)); lb.disabled=false; }
        return; }
      const ub=e.target.closest('[data-unlink]');
      if(ub){ const uid=ub.closest('[data-uid]').dataset.uid;
        if(!confirm('연결을 끊으면 이 회원에게 보이던 구매 내역이 서버에서 지워져요(별점·메모는 남아요). 끊을까요?')) return;
        const {error}=await client.from('ty_links').delete().eq('user_id',uid);
        if(error){alert('끊지 못했어요: '+error.message);return} await load(); return; }
      if(e.target.closest('[data-admin-sync]')){
        if(!LEDGER){alert('먼저 장부 파일을 열어 주세요.');return}
        const b=e.target.closest('[data-admin-sync]'); b.disabled=true; let n=0,miss=0;
        try{ for(const l of LINKS){ if(!custOf(l.ref)){miss++;continue} n+=await push(l.ref); }
          st.textContent=`연결된 ${LINKS.length-miss}명 구매 ${n}줄 반영했어요.`+(miss?` (장부 파일에 없는 손님 ${miss}명은 그대로 뒀어요)`:'');
        }catch(err){ st.textContent='반영하다 멈췄어요: '+(err.message||err); }
        b.disabled=false; return; }
      if(e.target.closest('[data-admin-reload]')) load();
    });
    onAuth(u=>{ $$('[data-admin-login] [data-login-provider]',ap).forEach(b=>b.hidden=!!u); $('[data-admin-who]',ap).textContent=u?`${nameOf(u)} · ${u.email||''}`:''; load(); });
  }

  /* ---------- 찜하기 · 평균 별점 · '많이 찜한/문의 많은 와인' (와인 목록·와인 페이지·내 와인) ---------- */
  const LOCAL_SAVES='ty-saves', NOTE_OFF='ty-save-note-off';
  const HEART='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20.5s-7.5-4.6-7.5-10.2A4.3 4.3 0 0 1 12 7.6a4.3 4.3 0 0 1 7.5 2.7c0 5.6-7.5 10.2-7.5 10.2z"/></svg>';
  let SAVED=new Set(store.get(LOCAL_SAVES)||[]), serverSaves=false;
  const hasSocial=()=>$('[data-save]')||$('[data-stats]')||$('[data-me-saved]');
  function paintSaves(){
    $$('[data-save]').forEach(b=>{const on=SAVED.has(b.dataset.save); b.setAttribute('aria-pressed',on); b.setAttribute('aria-label',on?'찜 해제':'찜하기');
      const l=$('[data-save-label]',b); if(l) l.textContent=on?'찜했어요':'찜하기';});
    paintSavedList();
  }
  function saveNote(){
    const n=$('[data-save-note]'); if(!n) return;
    if(user||store.get(NOTE_OFF)||!SAVED.size){n.hidden=true;return}
    n.innerHTML=`<b>이 기기에만 저장돼 있어요.</b> <a class="textlink" href="${REL}login/?next=${encodeURIComponent(location.pathname)}">로그인</a>하면 휴대폰·컴퓨터 어디서든 찜한 와인을 모아 볼 수 있어요. <button type="button" class="noteclose" aria-label="닫기">×</button>`;
    n.hidden=false; $('.noteclose',n).onclick=()=>{store.set(NOTE_OFF,1);n.hidden=true};
  }
  async function loadServerSaves(){
    if(!client||!user){serverSaves=false; SAVED=new Set(store.get(LOCAL_SAVES)||[]); return}
    const {data,error}=await client.from('ty_saves').select('wine_key').eq('user_id',user.id).limit(2000);
    if(error){serverSaves=false; return}
    serverSaves=true;
    const local=store.get(LOCAL_SAVES)||[], have=new Set((data||[]).map(r=>r.wine_key));
    const add=local.filter(k=>!have.has(k));   // 로그인 전에 이 기기에서 찜한 것을 계정으로 옮겨요
    if(add.length){ const {error:e2}=await client.from('ty_saves').upsert(add.map(k=>({user_id:user.id,wine_key:k}))); if(!e2){add.forEach(k=>have.add(k)); store.del(LOCAL_SAVES);} }
    else if(local.length) store.del(LOCAL_SAVES);
    SAVED=have;
  }
  document.addEventListener('click',async e=>{
    const b=e.target.closest('[data-save]'); if(!b) return; e.preventDefault();
    const k=b.dataset.save, on=!SAVED.has(k);
    if(on) SAVED.add(k); else SAVED.delete(k);
    paintSaves();
    if(serverSaves&&user){
      const q=on?client.from('ty_saves').upsert({user_id:user.id,wine_key:k}):client.from('ty_saves').delete().eq('user_id',user.id).eq('wine_key',k);
      const {error}=await q; if(error){ if(on) SAVED.delete(k); else SAVED.add(k); paintSaves(); alert('저장하지 못했어요. 잠시 뒤 다시 눌러 주세요.'); }
    } else { store.set(LOCAL_SAVES,[...SAVED].slice(0,500)); }
    saveNote();
  });
  /* 문의 버튼 누른 횟수(익명, 와인마다 한 브라우저에서 하루 한 번만) */
  document.addEventListener('click',e=>{
    const a=e.target.closest('[data-ask]'); if(!a||!client) return;
    const k=a.dataset.ask, day=new Date().toISOString().slice(0,10), mem=store.get('ty-asked')||{};
    if(mem[k]===day) return; mem[k]=day; store.set('ty-asked',mem);
    client.rpc('ty_ask',{k}).then(()=>{},()=>{});
  },true);
  /* 평균 별점·배지 */
  const starRow=v=>{let h='';for(let i=1;i<=5;i++){const f=Math.max(0,Math.min(1,v-i+1));h+=`<span class="s5" style="--f:${Math.round(f*100)}%"></span>`}return h};
  async function paintStats(){
    const slots=$$('[data-stats]'); if(!slots.length||!client) return;
    const {data,error}=await client.rpc('ty_wine_stats'); if(error||!data) return;
    const top=(f,min)=>new Set(data.filter(r=>r[f]>=min).sort((a,b)=>b[f]-a[f]).slice(0,10).map(r=>r.wine_key));
    const saved=top('saves_n',3), asked=top('asks_n',5), by={}; data.forEach(r=>by[r.wine_key]=r);
    slots.forEach(el=>{const r=by[el.dataset.stats]; if(!r) return;
      let h='';
      if(r.stars_avg) h+=`<span class="wstars" title="회원 ${r.stars_n}명 평균"><span class="s5row" aria-hidden="true">${starRow(+r.stars_avg)}</span><b>${(+r.stars_avg).toFixed(1)}</b><span class="muted small">(${r.stars_n})</span><span class="sr">회원 ${r.stars_n}명 평균 별점 ${r.stars_avg}점</span></span>`;
      const bs=[]; if(asked.has(r.wine_key)) bs.push('<span class="hb ask">문의 많은 와인</span>'); if(saved.has(r.wine_key)) bs.push('<span class="hb save">많이 찜한 와인</span>');
      if(bs.length) h+=`<span class="hbs">${bs.join('')}</span>`;
      if(h){el.innerHTML=h;el.hidden=false}});
  }
  /* 내 와인: 찜한 와인 */
  function paintSavedList(){
    const box=$('[data-me-saved]'); if(!box) return;
    const keys=[...SAVED].filter(k=>WI[k]);
    box.innerHTML=keys.length?keys.map(k=>{const w=WI[k];
      const pic=w.i?`<div class="wimg"><img src="${REL}${esc(w.i)}" alt="" loading="lazy" width="300" height="480"></div>`:`<div class="wimg none" aria-hidden="true">${$('.logo .mark')?$('.logo .mark').outerHTML:''}</div>`;
      return `<li class="wine mywine"><div class="wpicwrap">${pic}<button class="wsave" type="button" data-save="${esc(k)}" aria-pressed="true" aria-label="찜 해제">${HEART}</button></div><div class="wbody"><div class="wtop"><span class="wstyle">${esc([w.s,w.c].filter(Boolean).join(' · '))}</span></div><h3>${esc(w.k)}</h3><div class="wacts"><a class="btn line sm" href="${REL}wines/?q=${encodeURIComponent(w.k)}">와인 목록에서 보기</a></div></div></li>`}).join('')
      :`<p class="muted">아직 찜한 와인이 없어요. <a class="textlink" href="${REL}wines/">와인 목록</a>에서 하트를 눌러 보세요.</p>`;
  }
  if(hasSocial()){
    paintSaves(); saveNote(); paintStats();
    if(client) onAuth(async()=>{ await loadServerSaves(); paintSaves(); saveNote(); });
  }
})();

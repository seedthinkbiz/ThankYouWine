/* 땡큐와인 공통 스크립트: 메뉴, 문의 팝업, 블로그 분류 필터·네이버 새 글, 견적·문의 폼 */
(function(){
  'use strict';
  const REL=document.documentElement.getAttribute('data-rel')||'';
  const PAGE=document.documentElement.hasAttribute('data-preview')?'index.html':'';
  const CFG=window.TYW||{};
  const PHONE=CFG.phone||'010-8078-7493';
  const $=(s,r)=>(r||document).querySelector(s);
  const $$=(s,r)=>[...(r||document).querySelectorAll(s)];
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  /* ---------- 메뉴 ---------- */
  const navbtn=$('.navbtn'), nav=$('.nav');
  if(navbtn&&nav){
    navbtn.addEventListener('click',()=>{const open=nav.classList.toggle('open');navbtn.setAttribute('aria-expanded',String(open))});
    document.addEventListener('click',e=>{if(!nav.contains(e.target)&&!navbtn.contains(e.target)){nav.classList.remove('open');navbtn.setAttribute('aria-expanded','false')}});
  }
  $$('.year').forEach(el=>el.textContent=new Date().getFullYear());

  /* ---------- 복사 ---------- */
  async function copyText(btn,text){
    const old=btn.textContent;
    try{await navigator.clipboard.writeText(text);btn.textContent='복사됐어요'}
    catch(e){
      const ta=document.createElement('textarea');ta.value=text;ta.setAttribute('readonly','');ta.style.position='fixed';ta.style.left='-9999px';document.body.appendChild(ta);ta.select();
      let ok=false;try{ok=document.execCommand('copy')}catch(err){}
      document.body.removeChild(ta);btn.textContent=ok?'복사됐어요':'길게 눌러 복사해 주세요';
    }
    setTimeout(()=>{btn.textContent=old},1800);
  }
  document.addEventListener('click',e=>{
    const b=e.target.closest('[data-copy-text]'); if(!b) return;
    e.preventDefault(); copyText(b,b.getAttribute('data-copy-text'));
  });

  /* ---------- 문의 팝업 ---------- */
  const cd=$('#contact');
  if(cd){
    $$('[data-contact]').forEach(el=>el.addEventListener('click',e=>{e.preventDefault();if(!cd.open) cd.showModal();}));
    $('#cd-close').addEventListener('click',()=>cd.close());
    cd.addEventListener('click',e=>{if(e.target===cd) cd.close()});
    if(location.hash==='#contact'){try{cd.showModal()}catch(e){}}
  }

  /* ---------- 블로그 글 (목록은 HTML에 미리 들어 있어요. 여기서는 분류 필터와 네이버 새 글만) ---------- */
  const splitTitle=t=>{const s=String(t||'');const i=s.indexOf('｜');return i>0?[s.slice(0,i).trim(),s.slice(i+1).trim()]:[s,'']};
  const all=$('#posts-all'), chips=$('#post-chips');
  if(all&&chips){
    chips.addEventListener('click',e=>{
      const b=e.target.closest('.chip'); if(!b) return;
      const cat=b.dataset.cat||'';
      $$('.chip',chips).forEach(x=>x.setAttribute('aria-pressed',String(x===b)));
      let n=0; $$('.post',all).forEach(a=>{const show=!cat||(a.dataset.cat||'')===cat;a.hidden=!show;if(show)n++});
      const empty=$('.postsempty',all); if(empty) empty.hidden=n>0;
    });
  }
  // 네이버에 새로 올라와서 아직 사이트에 없는 글은 RSS로 받아 맨 위에 끼워 넣어요
  if(all&&!PAGE&&/^https?:/.test(location.protocol)){
    const have=new Set(CFG.posts||[]);
    fetch(REL+'api/posts',{cache:'no-cache'}).then(r=>r.ok?r.json():null).then(j=>{
      if(!j||!j.ok||!Array.isArray(j.posts)) return;
      const fresh=j.posts.filter(p=>{const m=String(p.url||'').match(/(\d{9,})\s*$/);return m&&!have.has(m[1])});
      if(!fresh.length) return;
      all.insertAdjacentHTML('afterbegin',fresh.slice(0,6).map(p=>{const [a,b]=splitTitle(p.title);return `<a class="post ext" href="${esc(p.url)}" target="_blank" rel="noopener" data-cat="${esc(p.category||'')}"><span class="pcat">네이버 새 글 · ${esc(p.category||'블로그')}</span><h3>${esc(a)}</h3>${b?`<p class="psub">${esc(b)}</p>`:''}${p.lead?`<p class="plead">${esc(p.lead)}</p>`:''}<span class="pmeta"><span>${esc(p.date||'')}</span><i>네이버에서 읽기 →</i></span></a>`}).join(''));
    }).catch(()=>{});
  }

  /* ---------- 폼 ---------- */
  const LABELS={
    party:[['인원','p-people'],['날짜','p-date'],['장소','p-place'],['자리 성격','p-type'],['예산','p-budget'],['와인잔 대여','p-glass'],['함께 나올 음식','p-food'],['연락처','p-contact'],['남기실 말','p-note']],
    gift:[['회사·이름','g-name'],['수량','g-qty'],['1병 예산','g-budget'],['필요한 날','g-date'],['받는 분','g-to'],['세금계산서','g-tax'],['연락처','g-contact'],['남기실 말','g-note']],
  };
  const TITLE={party:'모임·행사 와인 견적 요청',gift:'기업·명절 선물 문의'};
  const DONE={
    party:'견적 요청이 접수됐어요. 인원과 예산에 맞춰 구성 두세 가지를 정리해 영업일 하루 안에 연락드릴게요.',
    gift:'선물 문의가 접수됐어요. 예산과 수량에 맞는 와인을 골라 영업일 하루 안에 연락드릴게요.',
  };
  async function submitRequest(payload){
    const r=await fetch(REL+'api/submit',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(payload)});
    let j=null; try{j=await r.json()}catch(e){}
    if(!r.ok||!j||!j.ok) throw new Error((j&&j.reason)||('http-'+r.status));
    return j;
  }
  function fallbackBox(title,text){
    const d=document.createElement('div');d.className='fallback';
    const why=PAGE?'미리보기 화면이라 자동 접수는 안 돼요. 실제 사이트에서는 바로 접수돼요. 지금은 아래 내용을 메일·문자·카카오톡('+esc(PHONE)+' 친구 추가)으로 보내 주시면 바로 봐 드릴게요.'
                  :'지금은 자동 접수가 잠시 안 돼요. 아래 내용을 메일·문자·카카오톡('+esc(PHONE)+' 친구 추가)으로 보내 주시면 바로 봐 드릴게요.';
    d.innerHTML=`<b>${esc(title)}</b>
      <p class="small muted">${why}</p>
      <pre></pre><div class="acts"><a class="btn wine sm" data-mail>메일로 보내기</a><a class="btn line sm" data-sms>문자로 보내기</a><button class="btn line sm" type="button" data-copy>내용 복사</button>${CFG.kakao?`<a class="btn line sm" href="${esc(CFG.kakao)}" target="_blank" rel="noopener">카카오톡 채널 열기</a>`:''}</div>`;
    d.querySelector('pre').textContent=text;
    d.querySelector('[data-copy]').onclick=function(){copyText(this,text)};
    d.querySelector('[data-sms]').href='sms:'+PHONE.replace(/-/g,'')+'?body='+encodeURIComponent(text);
    d.querySelector('[data-mail]').href='mailto:'+(CFG.email||'')+'?subject='+encodeURIComponent(title.replace(/ 내용을 직접 보내 주세요$/,''))+'&body='+encodeURIComponent(text);
    return d;
  }
  $$('form[data-kind]').forEach(f=>{
    const kind=f.dataset.kind; if(!LABELS[kind]) return;
    const done=f.parentElement.querySelector('.done')||(()=>{const d=document.createElement('div');d.className='done';d.hidden=true;d.setAttribute('role','status');f.after(d);return d})();
    f.addEventListener('submit',async e=>{
      e.preventDefault();
      if(!f.checkValidity()){f.reportValidity();return}
      const btn=f.querySelector('[type="submit"]'); btn.disabled=true; const old=btn.textContent; btn.textContent='보내는 중…';
      const fields={}; LABELS[kind].forEach(([l,id])=>{const el=document.getElementById(id); if(el&&el.value.trim()) fields[l]=el.value.trim()});
      const hp=f.querySelector('.hp input');
      const text='['+TITLE[kind]+']\n'+Object.entries(fields).map(([k,v])=>k+': '+v).join('\n');
      try{
        await submitRequest({kind,fields,website:hp?hp.value:'',page:location.pathname});
        f.hidden=true; done.innerHTML=`<b>접수 완료</b><p>${DONE[kind]}</p>`; done.hidden=false; done.scrollIntoView({behavior:'smooth',block:'center'});
      }catch(err){
        f.hidden=true; done.innerHTML=''; done.appendChild(fallbackBox(TITLE[kind]+' 내용을 직접 보내 주세요',text));
        const back=document.createElement('button');back.type='button';back.className='btn line sm';back.textContent='폼으로 돌아가기';back.onclick=()=>{done.hidden=true;f.hidden=false};
        done.querySelector('.acts').appendChild(back);
        done.hidden=false; done.scrollIntoView({behavior:'smooth',block:'center'});
      }finally{btn.disabled=false;btn.textContent=old}
    });
  });
})();

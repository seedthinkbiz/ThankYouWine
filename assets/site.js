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


  /* ---------- 와인 목록: 검색·나라·스타일·재고 필터, 가격 문의 때 와인 이름 보여 주기 ---------- */
  const wl=$('#wlist');
  if(wl){
    const q=$('#wq'), cs=$('#wcountry'), nw=$('#wnow'), wc=$('#wchips'), cnt=$('#wcount'), emp=$('#wempty');
    let style='';
    const norm=t=>String(t||'').toLowerCase().replace(/\s+/g,'');
    const run=()=>{
      const words=String(q.value||'').toLowerCase().split(/\s+/).filter(Boolean).map(norm);
      let n=0;
      $$('.wine',wl).forEach(li=>{
        const hay=norm(li.dataset.q);
        const ok=(!style||li.dataset.style===style)&&(!cs.value||li.dataset.country===cs.value)&&(!nw.checked||li.dataset.now==='1')&&words.every(w=>hay.includes(w));
        li.hidden=!ok; if(ok) n++;
      });
      cnt.textContent=n+'종'; emp.hidden=n>0;
    };
    q.addEventListener('input',run); const q0=new URLSearchParams(location.search).get('q'); if(q0){q.value=q0;run();} cs.addEventListener('change',run); nw.addEventListener('change',run);
    wc.addEventListener('click',e=>{const b=e.target.closest('.chip'); if(!b) return; style=b.dataset.style||''; $$('.chip',wc).forEach(x=>x.setAttribute('aria-pressed',String(x===b))); run();});
    const dlg=$('#contact');
    if(dlg){
      const box=document.createElement('p'); box.className='cdwine'; box.hidden=true;
      const t=document.createElement('span');
      const c=document.createElement('button'); c.type='button'; c.className='btn line sm'; c.style.marginLeft='8px';
      box.append(t,c); $('.cdbody',dlg).prepend(box);
      c.addEventListener('click',()=>{try{navigator.clipboard.writeText(c.dataset.copy);c.textContent='복사했어요'}catch(_){}});
      wl.addEventListener('click',e=>{
        const b=e.target.closest('[data-wine]'); if(!b) return;
        t.textContent='문의할 와인: '+b.dataset.wine; c.textContent='이름 복사'; c.dataset.copy=b.dataset.wine+' 가격 문의드려요'; box.hidden=false;
      },true);
      dlg.addEventListener('close',()=>{box.hidden=true});
    }
  }


  /* ---------- 와인 카드: 와인 이름·사진을 누르면 크게 보기 (11/25 도하) ---------- */
  if($('.wine [data-wcard]')||$('#wlist')){
    const wd=document.createElement('dialog'); wd.className='cd wcard'; wd.setAttribute('aria-label','와인 카드');
    document.body.appendChild(wd);
    let src=null;
    const open=li=>{
      src=li; const c=li.cloneNode(true); c.hidden=false; c.classList.add('big');
      $$('[data-wcard]',c).forEach(b=>{const h=document.createElement('span'); h.textContent=b.textContent; b.replaceWith(h);});
      $$('[id]',c).forEach(x=>x.removeAttribute('id'));
      if(li.dataset.page){ const a=document.createElement('a'); a.className='textlink'; a.href=li.dataset.page; a.textContent='가격·자세한 정보 보기 →'; const acts=$('.wacts',c); if(acts) acts.append(a); }
      wd.innerHTML='<button type="button" class="wclose" aria-label="닫기">×</button>'; wd.append(c);
      try{wd.showModal()}catch(_){wd.setAttribute('open','')}
    };
    document.addEventListener('click',e=>{
      if(wd.contains(e.target)) return;
      const t=e.target.closest('.wine [data-wcard], .wine .wimg'); if(!t) return;
      const li=t.closest('.wine'); if(!li||li.classList.contains('mywine')) return;
      e.preventDefault(); open(li);
    });
    wd.addEventListener('click',e=>{
      if(e.target===wd||e.target.closest('.wclose')){wd.close();return}
      const ct=e.target.closest('[data-contact]');
      if(ct){ e.preventDefault(); wd.close();
        const orig=src&&($('#wlist .wine[data-key="'+src.dataset.key+'"] [data-contact]')||$('[data-contact]',src));
        if(orig) orig.click(); else { const d=$('#contact'); if(d&&!d.open) d.showModal(); }
      }
    });
    const k0=new URLSearchParams(location.search).get('w');
    if(k0){ const li=$('#wlist .wine[data-key="'+k0.replace(/[^\w]/g,'')+'"]'); if(li) setTimeout(()=>open(li),50); }
  }


  /* ---------- 와인 추천기: 자리·음식·맛 세 가지로 매장 와인 3병 고르기 ---------- */
  const wp=$('#wpick'), wlist=$('#wlist');
  if(wp&&wlist){
    const sel={occ:null,food:null,taste:null};
    const msg=$('#wpickmsg'), out=$('#wpickout'), res=$('#wpickres');
    $$('.pq',wp).forEach(g=>g.addEventListener('click',e=>{
      const b=e.target.closest('.chip'); if(!b) return;
      sel[g.dataset.q]=b.dataset.v;
      $$('.chip',g).forEach(x=>x.setAttribute('aria-pressed',String(x===b)));
      msg.textContent='';
    }));
    const score=(li,np)=>{
      const [body,sw,food,flags='']=(li.dataset.tags||'').split(' ');
      const st=li.dataset.style, occ=sel.occ, f=sel.food, t=sel.taste;
      if(occ==='N'){ if(st!=='무알콜') return -99; } else if(st==='무알콜') return -99;
      if(t==='s'&&sw==='d') return -99;
      let s=0;
      if(occ==='G'&&flags.includes('G')) s+=4;
      if(occ==='P'&&flags.includes('P')) s+=4;
      if(occ==='H'&&!flags.includes('G')) s+=1.5;
      if(f){ if(food.includes(f)) s+=4; else s-=1; }
      const sweetOK=(t==='s')||(f==='D');
      if(t==='s'){ s+= sw==='s'?4: sw==='o'?2:-2; }
      else if(t){ const o='lmf', d=Math.abs(o.indexOf(body)-o.indexOf(t)); s+= d===0?3: d===1?1:-1; }
      if(sw==='s'&&!sweetOK) s-=4;
      if(f==='D'&&sw!=='s') s-=2;
      if(!np) s+=(+li.dataset.push||0)*1.75;
      if(li.querySelector('.wimg img')) s+=.5;
      return s+Math.random()*.6;
    };
    const go=()=>{
      if(!sel.occ||sel.food===null||sel.taste===null){ msg.textContent='세 가지 질문에 하나씩 골라 주세요.'; return; }
      const cand=$$('.wine[data-now="1"][data-tags]',wlist).map(li=>[score(li),li]).filter(x=>x[0]>-50).sort((a,b)=>b[0]-a[0]);
      const picked=[], seen=new Set();
      for(const [,li] of cand){ const k=(li.querySelector('h3').textContent||'').split(' ')[0]; if(seen.has(k)) continue; seen.add(k); picked.push(li); if(picked.length===3) break; }
      if(!picked.some(li=>li.dataset.push==='3')){
        const must=cand.filter(([,li])=>li.dataset.push==='3').map(([,li])=>[score(li,1),li]).filter(x=>x[0]>=2).sort((a,b)=>b[0]-a[0])[0];
        if(must){ picked.pop(); picked.unshift(must[1]); }
      }
      res.replaceChildren(...picked.map(li=>{ const c=li.cloneNode(true); c.hidden=false; return c; }));
      out.hidden=false; msg.textContent='';
      res.scrollIntoView({behavior:'smooth',block:'start'});
    };
    $('#wpickbtn').addEventListener('click',go);
    $('#wpickagain').addEventListener('click',()=>{ out.hidden=true; Object.keys(sel).forEach(k=>{sel[k]=null}); $$('.chip',wp).forEach(x=>x.setAttribute('aria-pressed','false')); wp.scrollIntoView({behavior:'smooth',block:'start'}); });
    res.addEventListener('click',e=>{
      const b=e.target.closest('[data-contact]'); if(!b) return;
      e.preventDefault();
      const o=$$('[data-wine]',wlist).find(x=>x.dataset.wine===b.dataset.wine); if(o) o.click();
    });
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
      const fresh=j.posts.filter(p=>{const m=String(p.url||'').match(/\/(\d{9,})(?:[?#/]|$)/);return m&&!have.has(m[1])}).map(p=>({...p,url:String(p.url).split('?')[0]}));
      if(!fresh.length) return;
      all.insertAdjacentHTML('afterbegin',fresh.slice(0,30).map(p=>{const [a,b]=splitTitle(p.title);return `<a class="post ext" href="${esc(p.url)}" target="_blank" rel="noopener" data-cat="${esc(p.category||'')}"><span class="pcat">네이버 새 글 · ${esc(p.category||'블로그')}</span><h3>${esc(a)}</h3>${b?`<p class="psub">${esc(b)}</p>`:''}${p.lead?`<p class="plead">${esc(p.lead)}</p>`:''}<span class="pmeta"><span>${esc(p.date||'')}</span><i>네이버에서 읽기 →</i></span></a>`}).join(''));
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

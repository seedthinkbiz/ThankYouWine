# -*- coding: utf-8 -*-
"""땡큐와인 정적 사이트 생성기.
python3 tools/build.py            → 저장소 루트(사이트 폴더)에 HTML 생성 (Vercel이 그대로 배포)
python3 tools/build.py --preview  → tools/preview/ 에 아티팩트 미리보기용 HTML 생성
문구·주소·영업시간은 아래 SITE 블록만 고치고 다시 실행하면 돼요."""
import os, json, datetime, re as _re, shutil
from urllib.parse import quote

HERE=os.path.dirname(os.path.abspath(__file__))   # tools/
SITEDIR=os.path.dirname(HERE)                   # 저장소 루트 = 사이트 폴더
ROOT=SITEDIR
TODAY=datetime.date(2026,11,3)
PRIVACY_DATE=datetime.date(2026,11,24)   # 개인정보처리방침 내용을 바꿀 때만 고쳐요(11/24 회원 '내 와인' 추가)

# ───────────────── 여기만 고치면 돼요 ─────────────────
SITE=dict(
  name='땡큐와인', en='THANK YOU WINE',
  base='https://thankyouwine.vercel.app',          # 실제 주소가 정해지면 바꾸기
  phone='010-8078-7493',
  email='thankyouwine@gmail.com',
  address='서울 성동구 성덕정길 109 2층',
  hours='',                                          # 예: '화~일 12:00~21:00 · 월요일 휴무'  (비워 두면 안 보임)
  naver_place='',                                    # 네이버 플레이스 링크 (비워 두면 주소 검색 링크로 대신)
  kakao='',                                          # 카카오톡 채널 링크 pf.kakao.com/... (비워 두면 '번호로 친구 추가' 안내)
  blog='https://blog.naver.com/middaynight109',
  insta='https://www.instagram.com/thankyouwine/',
  insta_id='thankyouwine',
  corkmatch='https://corkmatch.com/',
  owner='한낮의밤', ceo='이도하', regno='482-11-01565', mailorder='제2024-서울성동-0327호',
)
# 회원 '내 와인'(로그인·산 와인 모아 보기·별점). Supabase 설정(docs/members.md)을 마친 뒤 True 로 두면 메뉴에 '내 와인'이 보여요.
MEMBERS_OPEN=True
SUPABASE_REGION='미국'  # 회원 저장 서버(Supabase) 국가. 코르크매치 build.py 와 같은 값으로(대시보드 → Project Settings → General → Region)
# ──────────────────────────────────────────────────

BASE=SITE['base']
PHONE=SITE['phone']
MAP_NAVER=SITE['naver_place'] or 'https://map.naver.com/p/search/'+quote(SITE['address'])
MAP_KAKAO='https://map.kakao.com/?q='+quote(SITE['address'])

import hashlib as _hl
def _asset_v():
    h=_hl.md5()
    for f in ('site.css','site.js'):
        try: h.update(open(os.path.join(SITEDIR,'assets',f),'rb').read())
        except OSError: pass
    return h.hexdigest()[:8]
ASSET_V=_asset_v()   # 캐시 무효화용(css/js 바뀌면 값이 바뀜)
GLASS_SVG='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.6 2.5h10.8l-.7 6.6a4.7 4.7 0 0 1-9.4 0L6.6 2.5z" fill="#7a1f33"/><path d="M12 13.8v5.6M8.2 20.6h7.6" stroke="#7a1f33" stroke-width="1.9" stroke-linecap="round"/></svg>'
# 하트 와인잔 마크(로고_1116/AC세트/ac.html의 #heart 심볼과 동일)
HEART_PATHS=('<path d="M75 118 C 30 88 14 62 22 38 C 30 14 62 12 75 36 C 88 12 120 14 128 38 C 136 62 120 88 75 118 Z" fill="none" stroke="#7A1F33" stroke-width="7" stroke-linejoin="round"/>'
             '<path d="M30 64 C 50 70 100 70 120 64 C 112 82 96 98 75 112 C 54 98 38 82 30 64 Z" fill="#7A1F33"/>'
             '<line x1="75" y1="118" x2="75" y2="170" stroke="#1a1a1a" stroke-width="6"/>'
             '<line x1="48" y1="174" x2="102" y2="174" stroke="#1a1a1a" stroke-width="6" stroke-linecap="round"/>')
HEART_SVG='<svg class="mark" viewBox="10 8 130 172" aria-hidden="true">'+HEART_PATHS+'</svg>'
WORDMARK='<span class="wordmark"><span class="en">THANK YOU WINE</span><span class="ko">땡큐와인</span></span>'
# 검색엔진 소유 확인 태그 (구글 서치콘솔 2026-11-19; 네이버 서치어드바이저는 등록 시 추가)
VERIFY_META=['<meta name="google-site-verification" content="AcdmXdyKv493Pcbqy103hmzLdd3vwIC6El_rb6pzydE">']
GOOGLE_VERIFY_FILE='google14be0bc5848b85b8.html'
MENU_SVG='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>'

PAGES={
 'index':     dict(path='',           title='땡큐와인 · 성수동 와인 토탈 서비스, 모임·행사 와인과 기업 선물', desc='성수동의 와인 토탈 서비스 땡큐와인. 집에서 마실 한 병부터 송년회 와인, 거래처 명절 선물까지 인원과 예산에 맞춰 골라 드려요. 와인잔 대여, 와인 강의·시음회.'),
 'gathering': dict(path='gathering/', title='모임·행사 와인 견적 · 땡큐와인', desc='송년회, 동호회, 회사 모임 와인. 인원과 예산에 맞춘 구성, 와인잔 대여와 배송·수거까지. 가입 없이 견적을 요청하세요.'),
 'gift':      dict(path='gift/',      title='기업·명절 선물 와인 · 땡큐와인', desc='거래처 명절 선물, 임직원 선물, 감사 인사 한 병. 보르도 5대 샤토부터 데일리 와인까지 예산에 맞춰 고르고 세금계산서를 발행해 드려요.'),
 'wines':     dict(path='wines/',     title='와인 목록 · 땡큐와인이 소개하고 판매한 와인 찾기', desc='땡큐와인에서 지금 만날 수 있는 와인과 지금까지 소개·판매한 와인 목록. 이름·나라·스타일로 찾고, 와인별 가격도 확인하세요.'),
 'shop':      dict(path='shop/',      title='매장 안내 · 땡큐와인', desc='서울 성동구 성덕정길 109 2층. 매장 픽업, 멤버 시음회·모임 안내.'),
 'about':     dict(path='about/',     title='소개 · 땡큐와인과 와인 컨설턴트 이도하', desc='땡큐와인은 모임·행사·기업 선물 와인부터 와인 강의·시음회까지 맡는 성수동의 와인 토탈 서비스예요. 운영하는 와인 컨설턴트 이도하 소개.'),
 'blog':      dict(path='blog/',      title='블로그 · 땡큐와인', desc='땡큐와인이 네이버 블로그에 올린 와인 소개·와인 이야기·모임·선물 글을 사이트에서 그대로 읽어요. 글마다 한 줄 요약부터.'),
 'occasions': dict(path='occasions/', title='상황별 와인 고르기 · 송년회·거래처 선물·고기·해산물 와인 | 땡큐와인', desc='회사 송년회 몇 병, 거래처 명절 선물 예산, 고기 굽는 날 레드, 해산물 화이트, 생빈티지 선물까지. 땡큐와인의 와인 컨설턴트가 상황별 고르는 기준을 정리했어요.'),
 'faq':       dict(path='faq/',       title='자주 묻는 질문 · 땡큐와인', desc='가격, 모임 와인 병 수, 와인잔 대여, 세금계산서, 멤버에 대해 자주 묻는 질문.'),
 'privacy':   dict(path='privacy/',   title='개인정보처리방침 · 땡큐와인', desc='땡큐와인 개인정보처리방침'),
 'login':     dict(path='login/',     title='로그인 · 땡큐와인', desc='카카오·구글로 로그인하고 내가 산 와인을 모아 보세요.'),
 'me':        dict(path='me/',        title='내 와인 · 땡큐와인', desc='땡큐와인에서 산 와인을 모아 보고 별점과 한 줄 메모를 남겨요.'),
 'admin':     dict(path='admin/',     title='회원 연결 · 땡큐와인', desc='관리자 전용'),
 '404':       dict(path='404.html',   title='페이지를 찾을 수 없어요 · 땡큐와인', desc='땡큐와인'),
}

MEMBER_PAGES=('login','me','admin')   # 검색에 안 나오고 사이트맵·llms.txt 에도 안 넣어요
def rel_for(path):
    return '../'*path.count('/')

ORG_ID=BASE+'/#org'; PERSON_ID=BASE+'/about/#person'; SITE_ID=BASE+'/#website'
KNOWS=["와인","와인 추천","모임 와인","송년회 와인","기업 선물 와인","명절 선물 와인","샴페인","부르고뉴 와인","보르도 와인","나파밸리 와인","와인 페어링","와인잔 대여"]

def ld_org():
    same=[SITE['blog'],SITE['insta']]+([SITE['naver_place']] if SITE['naver_place'] else [])
    return {"@context":"https://schema.org","@type":["LiquorStore","LocalBusiness"],"@id":ORG_ID,"name":"땡큐와인","alternateName":["Thank You Wine"],
      "url":BASE+'/',"logo":BASE+'/assets/logo.png',"image":[BASE+'/assets/og.png',BASE+'/assets/logo.png'],
      "description":"서울 성수동의 와인 토탈 서비스. 모임·행사 와인과 기업·명절 선물 와인을 인원과 예산에 맞춰 구성하고, 와인잔 대여와 와인 강의·시음회까지 해 드려요. 와인 컨설턴트 이도하가 운영해요.",
      "telephone":"+82-"+PHONE[1:],"email":SITE['email'],"priceRange":"₩₩",
      "address":{"@type":"PostalAddress","streetAddress":"성덕정길 109 2층","addressLocality":"성동구","addressRegion":"서울","addressCountry":"KR"},
      "areaServed":{"@type":"City","name":"서울"},"founder":{"@id":PERSON_ID},"knowsAbout":KNOWS,"sameAs":same,
      "makesOffer":[{"@type":"Offer","itemOffered":{"@type":"Service","name":"모임·행사 와인 구성과 견적","url":BASE+'/gathering/',"description":"인원과 예산에 맞춘 와인 구성, 와인잔 대여, 행사장 배송과 수거"}},
                    {"@type":"Offer","itemOffered":{"@type":"Service","name":"기업·명절 선물 와인","url":BASE+'/gift/',"description":"거래처·임직원 선물 와인 선정과 포장, 예산에 맞춘 제안"}}]}
def ld_website():
    return {"@context":"https://schema.org","@type":"WebSite","@id":SITE_ID,"url":BASE+'/',"name":"땡큐와인","alternateName":"Thank You Wine","inLanguage":"ko-KR","publisher":{"@id":ORG_ID}}
def ld_person():
    return {"@context":"https://schema.org","@type":"Person","@id":PERSON_ID,"name":"이도하","alternateName":"Doha Lee","jobTitle":"와인 컨설턴트","url":BASE+'/about/',"image":BASE+'/assets/img/doha.webp',
      "description":"성수동의 와인 토탈 서비스 땡큐와인을 운영하는 와인 컨설턴트. 모임·행사·기업 선물 와인 구성과 견적, 와인 매너·와인 인문학 강의와 시음회 진행, 와인 수입사 선샤인와인 운영.",
      "worksFor":{"@id":ORG_ID},"knowsAbout":KNOWS,"sameAs":[SITE['blog'],SITE['insta'],SITE['corkmatch']]}
def ld_faq(items):
    return {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in items]}
def ld_breadcrumb(items):
    return {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":i+1,"name":n,"item":u} for i,(n,u) in enumerate(items)]}
def ld_service(name,path,desc,stype):
    return {"@context":"https://schema.org","@type":"Service","@id":BASE+'/'+path+'#service',"name":name,"serviceType":stype,"url":BASE+'/'+path,"description":desc,
            "provider":{"@id":ORG_ID},"areaServed":{"@type":"City","name":"서울"},"availableChannel":{"@type":"ServiceChannel","serviceUrl":BASE+'/'+path,"servicePhone":{"@type":"ContactPoint","telephone":PHONE,"contactType":"상담"}}}
def ld_page(key):
    """모임·선물·매장·소개·FAQ 페이지 구조화 데이터 (AI 검색이 '누가 무엇을 하는지'를 바로 읽도록)."""
    p=PAGES.get(key); 
    if not p or key in ('index','404','privacy'): return None
    bc=ld_breadcrumb([('홈',BASE+'/'),(p['title'].split(' · ')[0],BASE+'/'+p['path'])])
    if key=='gathering':
        return [ld_service('모임·행사 와인 구성과 견적','gathering/',p['desc'],'모임·행사 와인 케이터링'),ld_faq(FAQ_GATHERING),bc]
    if key=='gift':
        return [ld_service('기업·명절 선물 와인','gift/',p['desc'],'기업 선물 와인'),ld_faq(FAQ_GIFT),bc]
    if key=='shop':
        return [ld_org(),bc]
    return [bc]
def ld_script(objs):
    return ''.join('<script type="application/ld+json">'+json.dumps(o,ensure_ascii=False)+'</script>\n' for o in objs if o)

def head(key, rel, page=None, ld=None, og=None):
    p=page or PAGES[key]
    canon=BASE+'/'+(p['path'] if p['path']!='404.html' else '')
    lds=list(ld or [])
    if key=='index': lds=[ld_org(),ld_website()]+lds
    elif key=='about': lds=[ld_org(),ld_person()]+lds
    elif key=='faq': lds=[ld_faq(FAQ_ALL)]+lds
    og=og or {}
    img=og.get('image') or BASE+'/assets/og.png'
    extra=''
    if og.get('type')=='article':
        extra=''.join(f'<meta property="article:{k}" content="{v}">\n' for k,v in (('published_time',og.get('published')),('modified_time',og.get('modified')),('author',BASE+'/about/'),('section',og.get('section'))) if v)
        extra+=''.join(f'<meta property="article:tag" content="{esc(t)}">\n' for t in og.get('tags',[])[:10])
        extra+='<meta name="author" content="이도하">\n'
    cfg=json.dumps({"phone":PHONE,"kakao":SITE['kakao'],"email":SITE['email'],"insta":SITE['insta'],"posts":[x['logNo'] for x in POSTS]},ensure_ascii=False)
    title=esc(p['title']); desc=esc(p['desc'])
    return f'''<!doctype html>
<html lang="ko" data-rel="{rel}"{" data-preview" if PREVIEW else ""}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="{'noindex,nofollow' if key in MEMBER_PAGES else 'index,follow,max-snippet:-1,max-image-preview:large,max-video-preview:-1'}">
<link rel="canonical" href="{canon}">
<meta property="og:type" content="{og.get('type','website')}">
<meta property="og:site_name" content="땡큐와인">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{img}">
<meta property="og:locale" content="ko_KR">
{extra}<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#ffffff">
{"".join(VERIFY_META)}
<link rel="icon" href="{rel}favicon.svg" type="image/svg+xml">
<link rel="alternate" type="application/rss+xml" title="땡큐와인 블로그" href="{BASE}/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600&family=Noto+Sans+KR:wght@400;500;700&family=Noto+Serif+KR:wght@600;700&display=swap">
<link rel="stylesheet" href="{rel}assets/site.css?v={ASSET_V}">
<script>window.TYW={cfg}</script>
{MEMBER_SCRIPTS.format(rel=rel,v=ASSET_V) if (key in MEMBER_PAGES or (MEMBERS_OPEN and key in ('wines','wine'))) else ''}
{ld_script(lds)}</head>
<body>
'''

MEMBER_SCRIPTS='<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.min.js" defer></script>\n<script src="{rel}assets/members.js?v={v}" defer></script>'
def header(rel, current):
    def a(href,label,k):
        cur=' aria-current="page"' if k==current else ''
        return f'<a href="{href}"{cur}>{label}</a>'
    home=rel if rel else './'
    return f'''<header class="top">
  <div class="wrap wide">
    <a class="logo" href="{home}" aria-label="땡큐와인 홈">{HEART_SVG}{WORDMARK}</a>
    <button class="navbtn" type="button" aria-expanded="false" aria-controls="nav" aria-label="메뉴">{MENU_SVG}</button>
    <nav class="nav" id="nav" aria-label="주요 메뉴">
      {a(rel+'gathering/','모임·행사 와인','gathering')}
      {a(rel+'gift/','기업·명절 선물','gift')}
      {a(rel+'wines/','와인 목록','wines')}
      {a(rel+'shop/','매장 안내','shop')}
      {a(rel+'blog/','블로그','blog')}
      {a(rel+'about/','소개','about')}
      {a(rel+'me/','내 와인','me') if MEMBERS_OPEN else ''}
      <a class="btn wine sm" href="#contact" data-contact>문의하기</a>
    </nav>
  </div>
</header>
'''

def contact_dialog():
    kakao_row = (f'''<div class="ch"><div><b>카카오톡</b><span>채널에서 1:1로 대화해요</span></div><div class="acts"><a class="btn wine sm" href="{SITE['kakao']}" target="_blank" rel="noopener">채널 열기</a></div></div>'''
                 if SITE['kakao'] else
                 f'''<div class="ch"><div><b>카카오톡</b><span>카카오톡에서 {PHONE} 을 친구로 추가하고 메시지 주세요</span></div><div class="acts"><button class="btn wine sm" type="button" data-copy-text="{PHONE}">번호 복사</button></div></div>''')
    return f'''<dialog class="cd" id="contact" aria-labelledby="cd-title">
  <div class="cdhead"><span id="cd-title">문의하기</span><button class="cdclose" type="button" id="cd-close" aria-label="닫기">×</button></div>
  <div class="cdbody">
    <p class="cdlead">카톡이나 문자로 편하게 남겨 주세요. 어떤 자리인지, 무엇과 드실지, 편한 가격대만 알려 주시면 돼요.</p>
    {kakao_row}
    <div class="ch"><div><b>문자 · 전화</b><span>{PHONE}</span></div><div class="acts"><a class="btn line sm" href="sms:{PHONE.replace('-','')}">문자 보내기</a><a class="btn line sm" href="tel:{PHONE.replace('-','')}">전화</a><button class="btn line sm" type="button" data-copy-text="{PHONE}">복사</button></div></div>
    <div class="ch"><div><b>이메일</b><span>{SITE['email']}</span></div><div class="acts"><a class="btn line sm" href="mailto:{SITE['email']}">메일 쓰기</a><button class="btn line sm" type="button" data-copy-text="{SITE['email']}">복사</button></div></div>
    <div class="ch"><div><b>인스타그램</b><span>@{SITE['insta_id']}</span></div><div class="acts"><a class="btn line sm" href="{SITE['insta']}" target="_blank" rel="noopener">DM 보내기</a></div></div>
  </div>
</dialog>
'''

def footer(rel):
    return f'''<footer>
  <div class="wrap">
    <p class="fname"><span class="logo">{HEART_SVG}{WORDMARK}</span></p>
    <p class="warn">지나친 음주는 뇌졸중, 기억력 손상이나 치매를 유발합니다. 임신 중 음주는 기형아 출생 위험을 높입니다.</p>
    <p>땡큐와인은 만 19세 이상만 이용할 수 있어요. 와인 가격은 와인 목록에 적힌 것 말고는 카카오톡으로 1:1 안내해 드려요.</p>
    <p>상호 {SITE['owner']} · 대표 {SITE['ceo']} · 사업자등록번호 {SITE['regno']} · 통신판매업 신고번호 {SITE['mailorder']}<br>{SITE['address']} · {PHONE} · {SITE['email']}</p>
    <p class="frow"><a href="{rel}gathering/">모임·행사 와인</a><a href="{rel}gift/">기업·명절 선물</a><a href="{rel}wines/">와인 목록</a><a href="{rel}shop/">매장 안내</a><a href="{rel}occasions/">상황별 와인 고르기</a><a href="{rel}faq/">자주 묻는 질문</a><a href="{rel}privacy/">개인정보처리방침</a><a href="{SITE['blog']}" target="_blank" rel="noopener">블로그</a><a href="{SITE['insta']}" target="_blank" rel="noopener">인스타그램</a><a href="{SITE['corkmatch']}" target="_blank" rel="noopener">코르크매치</a></p>
    <p>© <span class="year">2026</span> 땡큐와인</p>
  </div>
</footer>
{contact_dialog()}
<script src="{rel}assets/site.js?v={ASSET_V}" defer></script>
</body>
</html>
'''

FAQ_ALL=[
 ('블로그에 소개한 와인을 사고 싶은데 어디서 살 수 있나요?','서울 성수동 땡큐와인 매장(성동구 성덕정길 109 2층)에서 살 수 있어요. 블로그에 소개한 와인은 대부분 매장에 있거나 주문할 수 있으니, 카카오톡으로 와인 이름을 보내 주시면 입고 상황과 가격을 바로 알려 드려요. 매장에서 바로 가져가시거나 미리 주문해 두실 수 있어요.'),
 ('와인 가격은 어디서 보나요?','최근 수입사에서 받은 가격이 확실한 와인은 와인 목록과 와인별 페이지에 가격을 적어 두었어요. 나머지는 수입사 행사와 입고 시기에 따라 자주 바뀌어서 카카오톡으로 1:1 안내해 드려요. 어떤 자리인지, 무엇과 드실지, 편한 가격대만 알려 주시면 맞는 와인을 골라 가격과 함께 보내 드릴게요.'),
 ('모임 와인은 몇 병을 준비하면 될까요?','한 병(750ml)은 보통 5~6잔이 나와요. 식사 중심으로 건배와 한두 잔이면 2~3명에 1병, 식사와 대화가 길어지는 자리면 2명에 1병, 와인이 주인공인 모임이면 1명에 1병을 추천해요. 인원만 알려 주시면 1인 1병과 2인 1병 두 가지로 나란히 견적을 드려요.'),
 ('와인잔도 빌릴 수 있나요?','네. 인원만큼 와인잔을 준비해 드리고 행사가 끝나면 수거해요. 잔 포함과 잔 미포함으로 견적을 따로 드리니 비교해 보고 정하시면 돼요. 배송과 수거 방법은 견적 때 함께 안내드려요.'),
 ('세금계산서가 발행되나요?','네. 사업자(회사·단체·개인사업자)라면 세금계산서를 발행해 드려요. 사업자등록번호를 알려 주시면 되고, 결제는 계좌이체가 기본이에요. 개인 구매는 요청하시면 현금영수증을 발행해 드려요.'),
 ('와인을 잘 몰라도 괜찮나요?','그럼요. 세 가지만 알려 주세요. 어떤 자리인지, 어떤 음식과 함께인지, 어느 가격대가 편하신지. 이 세 가지만 알면 만족도가 가장 높은 와인을 찾아 드릴 수 있어요. 단 와인이 싫다거나 묵직한 레드가 좋다 같은 취향도 알려 주시면 더 좋아요.'),
 ('멤버는 어떻게 되나요?','가입비 없이, 10만원 이상 구매하시면 땡큐와인 멤버로 등록돼요. 멤버에게는 좋은 와인이 들어올 때와 시음회·모임을 열 때 카카오톡으로 먼저 알려 드리고, 멤버 가격은 카톡으로 1:1 안내해 드려요.'),
 ('매장에서 마셔 볼 수 있나요?','멤버 시음회와 모임을 매장에서 열어요. 15명까지 앉을 수 있어요. 일정은 카카오톡과 인스타그램으로 알려 드리고, 멤버에게 먼저 초대를 드려요.'),
 ('미리 주문하고 찾아갈 수 있나요?','네. 카톡으로 미리 주문해 두면 매장에서 바로 가져가실 수 있어요. 모임·행사 와인은 행사장으로 배송하고, 잔을 빌리셨으면 수거까지 해 드려요.'),
 ('미성년자도 살 수 있나요?','아니요. 땡큐와인은 만 19세 이상만 이용할 수 있어요. 모임과 시음회 참석자도 모두 만 19세 이상이어야 해요.'),
]
FAQ_GATHERING=[
 ('송년회 와인은 몇 병 준비하면 되나요?','한 병(750ml)은 5~6잔이 나와요. 식사 중심으로 건배와 한두 잔이면 2~3명에 1병, 식사와 대화가 길어지는 자리면 2명에 1병, 와인이 주인공인 모임이면 1명에 1병으로 잡아요. 땡큐와인 구성 예시로는 25명 송년회에 10병, 40명 송년회에 16병을 준비해요.'),
 ('모임 와인은 어떤 순서로 내면 좋나요?','건배는 스파클링으로 시작해서 화이트로 가볍게 이어가다가, 메인 요리가 나올 때 레드로 마무리하는 흐름이 가장 무난해요. 단 와인이 싫다, 묵직한 레드가 좋다 같은 취향을 알려 주시면 구성에 반영해요.'),
 ('행사 때 와인잔도 빌릴 수 있나요?','네. 인원만큼 와인잔을 빌려 드리고 행사가 끝나면 수거해요. 잔 포함과 잔 미포함 견적을 나란히 드리니 비교해 보고 정하시면 돼요.'),
 ('행사장으로 와인을 배송해 주나요?','네. 행사장으로 배송해 드리고, 성수동 매장 픽업도 돼요. 원하시면 자리에서 와인을 짧게 소개해 드리고, 와인 매너 미니 클래스도 할 수 있어요.'),
 ('견적은 어떻게 받나요?','가입 없이 견적 요청 폼이나 카카오톡으로 인원, 날짜, 장소, 예산을 알려 주세요. 영업일 하루 안에 1인 1병과 2인 1병처럼 구성 두세 가지와 견적을 보내 드려요. 회사·단체는 세금계산서를 발행해 드려요.'),
]
FAQ_GIFT=[
 ('거래처 명절 선물 와인은 어떻게 고르나요?','1병 예산, 수량, 받는 분, 필요한 날을 알려 주세요. 같은 예산이라도 이름이 알려진 와인과 숨은 보석 같은 와인은 느낌이 달라서, 받는 분들의 성향을 듣고 예산 안에서 두세 가지를 골라 와인마다 고른 이유와 함께 카카오톡으로 보내 드려요.'),
 ('VIP나 대표님께 드릴 와인은 무엇이 좋나요?','보르도 5대 샤토, 나파밸리, 빈티지 샴페인처럼 받자마자 알아보는 와인을 많이 찾으세요. 태어난 해 빈티지처럼 이야기가 있는 와인도 찾아 드려요.'),
 ('와인을 잘 모르는 분께 선물해도 괜찮을까요?','네. 와인마다 산지와 맛, 어울리는 음식을 적은 소개 카드를 함께 넣어 드려서, 받는 분이 와인을 잘 몰라도 편하게 드실 수 있어요.'),
 ('기업 선물 와인도 세금계산서가 되나요?','네. 계좌이체로 결제하시면 세금계산서를 발행해 드려요.'),
 ('선물 와인은 어떻게 전달되나요?','매장 픽업, 사무실 배송으로 전달하고, 수량이 많으면 수입사에서 바로 배송해 드릴 수 있어요.'),
]
def faq_html(items):
    return '<div class="faq">'+''.join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q,a in items)+'</div>'

PRIVACY_SNIPPET='''<details class="policy"><summary>내용 보기</summary>
            <p><b>수집 항목</b> {items}<br><b>이용 목적</b> 문의 확인, 견적·추천 상담 및 연락<br><b>보유 기간</b> 상담 종료 후 1년, 요청 시 즉시 삭제<br>동의하지 않을 수 있지만, 이 경우 폼으로는 접수할 수 없어요. <a class="textlink" href="{rel}privacy/" target="_blank" rel="noopener">개인정보처리방침</a></p>
          </details>'''

def bottle(rel, key, caption):
    return f'<figure><img src="{rel}assets/img/{key}.jpg" alt="{caption}" loading="lazy"><figcaption>{caption}</figcaption></figure>'

HERO_BOTTLES=[('sedici','세디치 브뤼 스푸만테'),('airen','라스 쿠아트로 에스타시오네스 아이렌'),('colombard','바롱 드 보삭 콜롱바르 소비뇽'),('beauvillage','샤또 보빌라쥬 메독'),('seguin-vv','조나단 세갱 부르고뉴 VV')]
SET_BOTTLES=[('pinfleur','바론 도베른 · 그랑 크뤼 샴페인'),('macon','피에르 아르망 · 부르고뉴 화이트'),('seguin-vv','조나단 세갱 · 부르고뉴 피노 누아'),('loufrejau','루 프레조 · 샤토뇌프 뒤 파프'),('papillon','오린 스위프트 파피용 · 나파 밸리')]
GIFT_BOTTLES=[('pinfleur','그랑 크뤼 샴페인'),('1865','칠레 까베르네 소비뇽'),('seguin-clos','부르고뉴 피노 누아'),('tarapaca','그란 리제르바 레드'),('auslese','독일 스위트 와인')]

def members_section(rel):
    return f'''<section class="sec band" id="members">
  <div class="wrap">
    <div class="head">
      <span class="kicker">멤버</span>
      <h2>10만원 이상 구매하시면<br>땡큐와인 멤버예요</h2>
      <p>가입비는 따로 없어요. 10만원 이상 구매하시면 멤버로 등록되고, 좋은 와인이 들어올 때와 시음회·모임을 열 때 카카오톡으로 먼저 알려 드려요. 멤버 가격은 카톡으로 1:1 안내해 드려요.</p>
    </div>
    <div class="ctas" style="margin-top:0"><a class="btn wine" href="#contact" data-contact>카톡으로 물어보기</a><a class="btn line" href="{rel}faq/">자주 묻는 질문</a></div>
  </div>
</section>'''

def hours_html():
    return f'<p class="hours">{SITE["hours"]}</p>' if SITE['hours'] else ''

# ---------------- 홈 ----------------
# ── 다가오는 행사(홈 첫 화면·관련 글에 신청 링크. until이 지나면 다음 빌드에서 자동으로 빠짐. 11/19 도하: 와인 인문학 강의는 코르크매치 행사 페이지로) ──
EVENTS=[dict(id='wine-humanities-1127',title='와인 인문학 강의 · 역사와 문화로 읽는 와인의 세계',when='11월 27일(금) 19:00~21:30',where='강남역 라임스퀘어',
             who='박찬준 대표님(아시아 와인 트로피 아시아 디렉터)',url='https://corkmatch.com/events/wine-humanities-1127/',until='2026-11-27',
             posts=('224466864886','224479046305'),cta='코르크매치에서 보고 신청하기')]
def live_events():
    t=datetime.date.today()
    return [e for e in EVENTS if datetime.date.fromisoformat(e['until'])>=t]
def eventbar_html():
    return ''.join(f'<a class="eventbar" href="{e["url"]}" target="_blank" rel="noopener"><span class="ev-k">행사</span><span class="ev-t"><b>{esc(e["title"])}</b><span>{esc(e["when"])} · {esc(e["where"])} · {esc(e["who"])}</span></span><span class="ev-c">{esc(e["cta"])} →</span></a>' for e in live_events())
def eventbox_html(p):
    return ''.join(f'<aside class="eventbox"><b>신청은 코르크매치 행사 페이지에서</b><p>{esc(e["title"])}<br>{esc(e["when"])} · {esc(e["where"])} · {esc(e["who"])}</p><a class="btn wine" href="{e["url"]}" target="_blank" rel="noopener">{esc(e["cta"])}</a></aside>' for e in live_events() if p['logNo'] in e.get('posts',()))
def page_index(rel):
    return f'''
<section class="hero">
  <div class="wrap wide">
    <div class="herogrid">
      <div>
        <h1>오늘 자리에 맞는 와인,<br>함께 골라 드려요</h1>
        <p class="lead">집에서 마실 한 병부터 30명 송년회, 거래처 명절 선물까지. <b>인원과 예산, 자리의 분위기</b>만 알려 주시면 와인 구성부터 잔 준비까지 땡큐와인이 맞춰 드려요.</p>
        <div class="ctas">
          <a class="btn wine" href="{rel}gathering/">모임 와인 견적 받기</a>
          <a class="btn line" href="{rel}gift/">기업·명절 선물 문의</a>
          <a class="textlink" href="{rel}blog/">블로그에서 와인 둘러보기 →</a>
        </div>
        {eventbar_html()}
      </div>
      <div>
        <div class="bottles">{''.join(bottle(rel,k,c) for k,c in HERO_BOTTLES)}</div>
        <p class="bottlenote">요즘 모임에서 가장 많이 찾으시는 와인들이에요.</p>
      </div>
    </div>
  </div>
</section>

<section class="sec" id="services">
  <div class="wrap">
    <div class="head">
      <span class="kicker">이런 자리에</span>
      <h2>와인이 필요한 자리마다<br>맞는 방법이 있어요</h2>
    </div>
    <div class="doors">
      <a class="door" href="{rel}gathering/"><h3>모임·행사 와인</h3><p>송년회, 동호회 정모, 회사 모임. 인원과 예산에 맞춰 스파클링·화이트·레드를 짜고, 와인잔 대여와 배송·수거까지 한 번에 준비해요.</p><span class="more">견적 받기 →</span></a>
      <a class="door" href="{rel}gift/"><h3>기업·명절 선물</h3><p>거래처 명절 선물부터 임직원 선물까지. 보르도 5대 샤토부터 데일리 와인까지 예산에 맞춰 고르고, 세금계산서를 발행해 드려요.</p><span class="more">선물 문의 →</span></a>
      <a class="door" href="{rel}shop/"><h3>오늘 마실 한 병</h3><p>성수동 매장에서 어떤 자리인지, 무엇과 드실지 듣고 한 병을 골라 드려요. 카톡으로 미리 주문해 두고 들러 가셔도 돼요.</p><span class="more">매장 안내 →</span></a>
    </div>
  </div>
</section>

<section class="sec" id="how">
  <div class="wrap">
    <div class="head">
      <span class="kicker">진행 방법</span>
      <h2>세 가지만 알려 주시면 돼요</h2>
    </div>
    <div class="steps">
      <div class="step"><span class="n">1</span><h3>자리를 알려 주세요</h3><p>인원, 날짜, 예산, 그리고 어떤 자리인지. 식사가 중심인지, 와인이 주인공인지에 따라 병 수와 구성이 달라져요.</p></div>
      <div class="step"><span class="n">2</span><h3>구성과 견적을 받아 보세요</h3><p>1인 1병과 2인 1병, 잔 포함과 잔 미포함처럼 두세 가지를 나란히 비교할 수 있게 정리해 드려요.</p></div>
      <div class="step"><span class="n">3</span><h3>받으시는 방법을 정해요</h3><p>매장 픽업, 행사장 배송, 잔 대여 시 수거까지. 기업·단체는 세금계산서를 발행해 드려요.</p></div>
    </div>
  </div>
</section>

<section class="sec" id="price">
  <div class="wrap">
    <div class="head">
      <span class="kicker">가격</span>
      <h2>예산을 말씀해 주시면<br>그 안에서 가장 좋은 구성을 찾아요</h2>
      <p>가격이 확실한 와인은 <a href="{rel}wines/">와인 목록</a>에 적어 두었어요. 나머지는 수입사 행사와 입고 시기에 따라 자주 바뀌어서 1:1 카카오톡으로 안내드려요.</p>
    </div>
    <dl class="ranges">
      <div><dt>데일리</dt><dd><b>여러 병 쓰는 모임</b><span>집에서 편하게, 모임에서 여러 병 쓰기 좋은 와인</span></dd></div>
      <div><dt>모임 · 선물</dt><dd><b>한 병도 손색없는 와인</b><span>호텔에 납품되는 와인, 선물로 건네도 좋은 한 병</span></dd></div>
      <div><dt>특별한 날</dt><dd><b>샴페인 · 부르고뉴 · 나파밸리</b><span>기념일, 특별한 손님이 오는 자리</span></dd></div>
      <div><dt>프리미엄</dt><dd><b>보르도 5대 샤토 · 빈티지 샴페인</b><span>VIP 선물, 이야기가 있는 한 병</span></dd></div>
    </dl>
    <div class="ctas"><a class="btn wine" href="#contact" data-contact>카톡으로 가격 물어보기</a></div>
  </div>
</section>

<section class="sec" id="blog">
  <div class="wrap">
    <div class="head">
      <span class="kicker">블로그</span>
      <h2>요즘 매장에 있는 와인,<br>글로 먼저 만나 보세요</h2>
      <p>와인 소개와 와인 이야기를 블로그에 꾸준히 올려요. 발행한 글은 사이트에서도 그대로 읽을 수 있어요.</p>
    </div>
    <div class="posts" id="posts-home">{posts_cards(rel,POSTS[:6])}</div>
    <div class="morerow"><a class="btn line" href="{rel}blog/">글 전체 보기</a><a class="textlink" href="{SITE['blog']}" target="_blank" rel="noopener">네이버 블로그로 가기 →</a></div>
  </div>
</section>

<section class="sec" id="shop">
  <div class="wrap">
    <div class="shopgrid">
      <div>
        <span class="kicker">매장</span>
        <h2>성수동에서 뵐게요</h2>
        <p class="addr">{SITE['address']}</p>
        {hours_html()}
        <div class="ctas"><a class="btn line" href="{MAP_NAVER}" target="_blank" rel="noopener">네이버 지도</a><a class="btn line" href="{MAP_KAKAO}" target="_blank" rel="noopener">카카오맵</a><a class="textlink" href="{rel}shop/">매장 안내 →</a></div>
      </div>
      <ul class="shoplist">
        <li><b>매장 픽업</b><span>카톡으로 미리 주문해 두고 들러 가세요. 취향을 말씀해 주시면 자리에서 골라 드려요.</span></li>
        <li><b>시음회 · 모임</b><span>멤버 시음회와 모임을 매장에서 열어요. 15명까지 앉을 수 있어요.</span></li>
      </ul>
    </div>
  </div>
</section>

{members_section(rel)}

<section class="sec" id="faq">
  <div class="wrap">
    <div class="head">
      <span class="kicker">자주 묻는 질문</span>
      <h2>궁금한 점</h2>
    </div>
    {faq_html(FAQ_ALL[:4])}
    <div class="morerow"><a class="textlink" href="{rel}faq/">질문 전체 보기 →</a></div>
  </div>
</section>

<section class="sec">
  <div class="wrap">
    <div class="final">
      <h2>와인은 취하려고가 아니라<br>대화를 풍성하게 하려고 마시는 거니까요</h2>
      <p>필요하실 때 함께 고민해 드릴게요. 언제든 편하게 연락 주세요.</p>
      <div class="ctas"><a class="btn wine" href="#contact" data-contact>문의하기</a><a class="btn line" href="{rel}gathering/">모임 와인 견적 받기</a></div>
    </div>
  </div>
</section>'''

# ---------------- 모임·행사 와인 ----------------
def page_gathering(rel):
    pol=PRIVACY_SNIPPET.format(items='연락처, 인원, 날짜, 장소, 예산, 요청 내용',rel=rel)
    return f'''
<section class="sec tight" id="gathering">
  <div class="wrap">
    <div class="head">
      <span class="kicker">모임·행사 와인</span>
      <h1>인원과 예산만 알려 주세요.<br>와인부터 잔까지 맞춰 드릴게요</h1>
      <p>송년회, 동호회 정모, 회사 워크숍, 비즈니스 모임. 몇 병이 필요한지, 예산 안에서 어떤 와인을 고를지, 잔은 어떻게 할지까지 한 번에 정리해 드려요.</p>
    </div>
    <div class="ctas" style="margin-top:0"><a class="btn wine" href="#quote">견적 요청하기</a><a class="btn line" href="#contact" data-contact>카톡으로 바로 문의</a></div>
  </div>
</section>

<section class="sec" id="howmany">
  <div class="wrap">
    <div class="head">
      <span class="kicker">몇 병이 필요할까</span>
      <h2>한 병은 5~6잔,<br>자리에 따라 이렇게 잡아요</h2>
    </div>
    <div class="tablebox">
      <table>
        <thead><tr><th>자리</th><th>추천 비율</th><th>20명이면</th></tr></thead>
        <tbody>
          <tr><td>식사 중심, 건배와 한두 잔</td><td class="us">2~3명에 1병</td><td>7~10병</td></tr>
          <tr><td>식사와 대화가 길어지는 자리</td><td class="us">2명에 1병</td><td>10병</td></tr>
          <tr><td>와인이 주인공인 모임·파티</td><td class="us">1명에 1병</td><td>20병</td></tr>
        </tbody>
      </table>
    </div>
    <p class="postsnote">건배는 스파클링으로 시작해서 화이트로 가볍게 이어가다가, 메인 요리가 나올 때 레드로 마무리하는 흐름이 가장 무난해요.</p>
  </div>
</section>

<section class="sec" id="sets">
  <div class="wrap">
    <div class="head">
      <span class="kicker">구성 예시</span>
      <h2>인원별로 이렇게 짜 드려요</h2>
      <p>모임 성격에 맞춰 짠 예시예요. 가격은 카톡으로 안내드리고, 잔 대여는 따로 안내드려요. 예산과 취향, 음식에 따라 구성은 얼마든지 바꿔 드려요.</p>
    </div>
    <div class="sets">
      <div class="set"><span class="who">10명 홈파티</span><span class="range">6병</span><ul><li>마리 드메 뀌베 19세기 샴페인<b>1</b></li><li>피에르 아르망 마콩 빌라주<b>2</b></li><li>조나단 세갱 부르고뉴 피노 누아 VV<b>2</b></li><li>그랜드 바로사 까베르네 소비뇽<b>1</b></li></ul></div>
      <div class="set"><span class="who">25명 송년회</span><span class="range">10병</span><ul><li>세디치 브뤼 스푸만테<b>2</b></li><li>샤또 드 말리니 샤블리<b>3</b></li><li>타라파카 그란 레세르바 까베르네 소비뇽<b>3</b></li><li>그랜드 바로사 까베르네 소비뇽<b>2</b></li></ul></div>
      <div class="set"><span class="who">30명 기업 송년회</span><span class="range">12병</span><ul><li>바론 도베른 그랑 크뤼 샴페인<b>3</b></li><li>샤또 드 말리니 샤블리<b>3</b></li><li>루 프레조 샤토뇌프 뒤 파프<b>3</b></li><li>오베하 네그라 그란 레세르바<b>3</b></li></ul></div>
      <div class="set"><span class="who">40명 VIP·비즈니스 모임</span><span class="range">16병</span><ul><li>바론 도베른 그랑 크뤼 샴페인<b>4</b></li><li>피에르 아르망 마콩 빌라주<b>4</b></li><li>프로두토리 델 바르바레스코<b>4</b></li><li>오린 스위프트 파피용<b>4</b></li></ul></div>
    </div>
    <div class="setbottles">{''.join(bottle(rel,k,c) for k,c in SET_BOTTLES)}</div>
    <p class="postsnote">부담 없는 데일리 와인으로 인원을 넉넉히 맞추거나, 보르도 그랑 크뤼·빈티지 샴페인으로 더 특별하게 짜는 것도 돼요. 예산만 알려 주세요. <a class="textlink" href="{rel}wines/">와인 목록 보기 →</a></p>
  </div>
</section>

<section class="sec" id="with">
  <div class="wrap">
    <div class="head">
      <span class="kicker">함께 준비해 드리는 것</span>
      <h2>와인만이 아니라 자리 전체를</h2>
    </div>
    <ul class="checks">
      <li>인원만큼 와인잔을 빌려 드리고, 행사가 끝나면 수거해요. 플라스틱 컵에 마시는 와인은 그 맛이 안 나니까요.</li>
      <li>1인 1병과 2인 1병, 잔 포함과 잔 미포함처럼 두세 가지 견적을 나란히 드려요.</li>
      <li>행사장으로 배송해 드리고, 매장 픽업도 돼요.</li>
      <li>원하시면 자리에서 와인을 짧게 소개해 드려요. 와인 매너 미니 클래스도 가능해요.</li>
      <li>회사·단체는 세금계산서를 발행해 드려요.</li>
      <li>단 와인이 싫다, 묵직한 레드가 좋다 같은 취향을 알려 주시면 구성에 반영해요.</li>
    </ul>
  </div>
</section>

<section class="sec" id="faq">
  <div class="wrap">
    <div class="head">
      <span class="kicker">자주 묻는 질문</span>
      <h2>많이 물어보시는 것</h2>
    </div>
    {faq_html(FAQ_GATHERING)}
  </div>
</section>
<section class="sec" id="quote">
  <div class="wrap">
    <div class="head">
      <span class="kicker">견적 요청</span>
      <h2>가입 없이 남겨 주세요</h2>
      <p>영업일 하루 안에 구성 두세 가지와 견적을 보내 드려요. 받아 보고 정하셔도 돼요.</p>
    </div>
    <div class="formbox">
      <form id="f-party" data-kind="party" novalidate="">
        <div class="row">
          <label>인원<input id="p-people" type="number" min="2" inputmode="numeric" placeholder="예: 25" required></label>
          <label>날짜<input id="p-date" type="text" placeholder="예: 12월 12일 금요일 저녁"></label>
        </div>
        <div class="row">
          <label>장소<input id="p-place" type="text" placeholder="예: 성수동 레스토랑, 회사 회의실"></label>
          <label>자리 성격<select id="p-type"><option>식사 중심 (건배와 한두 잔)</option><option selected>식사와 대화가 길어지는 자리</option><option>와인이 주인공인 모임·파티</option></select></label>
        </div>
        <div class="row">
          <label>예산<input id="p-budget" type="text" placeholder="예: 총 30만원, 또는 1인 2만원"></label>
          <label>와인잔 대여<select id="p-glass"><option>필요해요</option><option>필요 없어요</option><option selected>아직 모르겠어요</option></select></label>
        </div>
        <label>함께 나올 음식<input id="p-food" type="text" placeholder="예: 한식 코스, 치킨·피자, 핑거푸드"></label>
        <label>연락처<input id="p-contact" type="text" placeholder="이름, 휴대폰 번호 또는 카카오톡 ID" required autocomplete="tel"></label>
        <label>남기실 말<textarea id="p-note" placeholder="예: 단 와인 싫어하는 분이 많아요, 잔 수거는 다음 날 오전에 가능해요"></textarea></label>
        <div class="hp" aria-hidden="true"><label>홈페이지<input type="text" name="website" tabindex="-1" autocomplete="off"></label></div>
        <div class="consent">
          <label class="check"><input id="p-privacy" type="checkbox" required><span>[필수] 개인정보 수집·이용에 동의해요.</span></label>
          {pol}
        </div>
        <button class="btn wine" type="submit">견적 요청하기</button>
      </form>
      <div class="done" hidden role="status"></div>
    </div>
    <p class="formalt">폼이 번거로우시면 카톡으로 인원·날짜·예산만 보내 주셔도 돼요. <a class="textlink" href="#contact" data-contact>문의하기</a></p>
  </div>
</section>'''

# ---------------- 기업·명절 선물 ----------------
def page_gift(rel):
    pol=PRIVACY_SNIPPET.format(items='회사·이름, 연락처, 수량, 예산, 요청 내용',rel=rel)
    return f'''
<section class="sec tight" id="gift">
  <div class="wrap">
    <div class="head">
      <span class="kicker">기업·명절 선물</span>
      <h1>보르도 5대 샤토부터 데일리까지,<br>예산에 맞춰 골라 드려요</h1>
      <p>거래처 명절 선물, 임직원 선물, 감사 인사 한 병. 받는 분과 예산을 알려 주시면 두세 가지로 추려 제안드리고, 세금계산서도 발행해 드려요.</p>
    </div>
    <div class="ctas" style="margin-top:0"><a class="btn wine" href="#ask">선물 문의하기</a><a class="btn line" href="#contact" data-contact>카톡으로 바로 문의</a></div>
  </div>
</section>

<section class="sec" id="kinds">
  <div class="wrap">
    <div class="head">
      <span class="kicker">이런 선물</span>
      <h2>받는 분에 따라 다르게 골라요</h2>
    </div>
    <div class="gifts">
      <div class="gift"><span class="tag">명절 · 연말</span><h3>거래처 선물</h3><p>같은 예산이라도 이름이 알려진 와인과 숨은 보석 같은 와인은 느낌이 달라요. 받는 분들의 성향을 듣고 골라요. 수량이 많으면 수입사에서 바로 배송해 드릴 수 있어요.</p></div>
      <div class="gift"><span class="tag">임직원 · VIP</span><h3>특별한 한 병</h3><p>보르도 5대 샤토, 나파밸리, 빈티지 샴페인처럼 받자마자 알아보는 와인. 태어난 해 빈티지처럼 이야기가 있는 와인도 찾아 드려요.</p></div>
      <div class="gift"><span class="tag">감사 · 축하</span><h3>마음을 담은 한 병</h3><p>와인마다 산지와 맛, 어울리는 음식을 적은 소개 카드를 함께 넣어 드려요. 받는 분이 와인을 잘 몰라도 편하게 드실 수 있게요.</p></div>
    </div>
  </div>
</section>

<section class="sec" id="range">
  <div class="wrap">
    <div class="head">
      <span class="kicker">예산별 제안</span>
      <h2>예산을 말씀해 주시면<br>그 안에서 가장 좋은 걸 찾아요</h2>
      <p>정확한 가격은 카카오톡으로 안내드려요. 수량이 많으면 수량에 맞춰 다시 맞춰 드려요.</p>
    </div>
    <dl class="ranges">
      <div><dt>부담 없는 선물</dt><dd><b>여러 분께 드리는 명절 선물</b><span>데일리로 즐기기 좋은 와인</span></dd></div>
      <div><dt>기본 선물</dt><dd><b>호텔에 납품되는 와인</b><span>선물로 건네도 손색없는 한 병</span></dd></div>
      <div><dt>특별한 분께</dt><dd><b>그랑 크뤼 샴페인 · 부르고뉴 · 나파밸리</b><span>이름만 들어도 아는 산지</span></dd></div>
      <div><dt>프리미엄</dt><dd><b>보르도 5대 샤토 · 빈티지 샴페인</b><span>VIP·대표님께 드리는 한 병</span></dd></div>
    </dl>
    <div class="setbottles">{''.join(bottle(rel,k,c) for k,c in GIFT_BOTTLES)}</div>
  </div>
</section>

<section class="sec" id="flow">
  <div class="wrap">
    <div class="head">
      <span class="kicker">진행 순서</span>
      <h2>문의부터 받으실 때까지</h2>
    </div>
    <div class="steps">
      <div class="step"><span class="n">1</span><h3>예산과 수량, 받는 분</h3><p>1병 예산, 몇 병인지, 누가 받으시는지 알려 주세요. 필요한 날짜도요.</p></div>
      <div class="step"><span class="n">2</span><h3>두세 가지 제안</h3><p>예산 안에서 두세 가지를 골라 가격과 함께 카톡으로 보내 드려요. 와인마다 왜 골랐는지도 적어 드려요.</p></div>
      <div class="step"><span class="n">3</span><h3>세금계산서와 전달</h3><p>계좌이체로 결제하시면 세금계산서를 발행해 드려요. 매장 픽업, 사무실 배송, 수량이 많으면 수입사 직접 배송으로 전달해요.</p></div>
    </div>
  </div>
</section>

<section class="sec" id="faq">
  <div class="wrap">
    <div class="head">
      <span class="kicker">자주 묻는 질문</span>
      <h2>많이 물어보시는 것</h2>
    </div>
    {faq_html(FAQ_GIFT)}
  </div>
</section>
<section class="sec" id="ask">
  <div class="wrap">
    <div class="head">
      <span class="kicker">선물 문의</span>
      <h2>가입 없이 남겨 주세요</h2>
      <p>영업일 하루 안에 제안을 보내 드려요.</p>
    </div>
    <div class="formbox">
      <form id="f-gift" data-kind="gift" novalidate="">
        <div class="row">
          <label>회사·이름<input id="g-name" type="text" placeholder="예: OO주식회사 김OO" required autocomplete="organization"></label>
          <label>수량<input id="g-qty" type="text" placeholder="예: 12병, 30세트" required></label>
        </div>
        <div class="row">
          <label>1병 예산<input id="g-budget" type="text" placeholder="예: 1병 5만원, 또는 총 100만원"></label>
          <label>필요한 날<input id="g-date" type="text" placeholder="예: 설 일주일 전, 12월 20일"></label>
        </div>
        <label>받는 분<input id="g-to" type="text" placeholder="예: 거래처 대표님들, 임직원, 와인 좋아하는 분"></label>
        <div class="row">
          <label>세금계산서<select id="g-tax"><option selected>필요해요</option><option>필요 없어요</option></select></label>
          <label>연락처<input id="g-contact" type="text" placeholder="휴대폰 번호 또는 이메일" required autocomplete="tel"></label>
        </div>
        <label>남기실 말<textarea id="g-note" placeholder="예: 선물 포장이 필요해요, 받는 분이 단 와인을 좋아해요"></textarea></label>
        <div class="hp" aria-hidden="true"><label>홈페이지<input type="text" name="website" tabindex="-1" autocomplete="off"></label></div>
        <div class="consent">
          <label class="check"><input id="g-privacy" type="checkbox" required><span>[필수] 개인정보 수집·이용에 동의해요.</span></label>
          {pol}
        </div>
        <button class="btn wine" type="submit">선물 문의하기</button>
      </form>
      <div class="done" hidden role="status"></div>
    </div>
    <p class="formalt">폼이 번거로우시면 카톡으로 예산·수량만 보내 주셔도 돼요. <a class="textlink" href="#contact" data-contact>문의하기</a></p>
  </div>
</section>'''

# ---------------- 매장 안내 ----------------
def page_shop(rel):
    return f'''
<section class="sec tight" id="shop">
  <div class="wrap">
    <div class="shopgrid">
      <div>
        <span class="kicker">매장 안내</span>
        <h1>성수동 땡큐와인</h1>
        <p class="addr">{SITE['address']}</p>
        {hours_html()}
        <p class="muted small" style="margin-top:10px">연락처 {PHONE}</p>
        <div class="ctas"><a class="btn wine" href="{MAP_NAVER}" target="_blank" rel="noopener">네이버 지도에서 보기</a><a class="btn line" href="{MAP_KAKAO}" target="_blank" rel="noopener">카카오맵</a><button class="btn line" type="button" data-copy-text="{SITE['address']}">주소 복사</button></div>
      </div>
      <ul class="shoplist">
        <li><b>한 병 고르기</b><span>어떤 자리인지, 무엇과 드실지, 편한 가격대. 세 가지만 말씀해 주시면 자리에서 골라 드려요.</span></li>
        <li><b>매장 픽업</b><span>카톡으로 미리 주문해 두면 들르셔서 바로 가져가실 수 있어요.</span></li>
        <li><b>시음회 · 모임</b><span>멤버 시음회와 모임을 매장에서 열어요. 15명까지 앉을 수 있어요. 일정은 카카오톡과 인스타그램으로 알려 드려요.</span></li>
        <li><b>모임·선물 상담</b><span>모임 와인과 기업 선물은 매장에 오시지 않아도 카톡으로 상담부터 전달까지 돼요.</span></li>
      </ul>
    </div>
  </div>
</section>

{members_section(rel)}

<section class="sec" id="follow">
  <div class="wrap">
    <div class="head">
      <span class="kicker">소식</span>
      <h2>새 와인과 행사 소식은 여기서</h2>
    </div>
    <div class="ctas" style="margin-top:0"><a class="btn line" href="{SITE['blog']}" target="_blank" rel="noopener">네이버 블로그</a><a class="btn line" href="{SITE['insta']}" target="_blank" rel="noopener">인스타그램 @{SITE['insta_id']}</a><a class="btn line" href="{rel}blog/">사이트에서 글 보기</a></div>
  </div>
</section>'''

# ---------------- 소개 ----------------
def page_about(rel):
    return f'''
<section class="sec tight" id="about">
  <div class="wrap">
    <div class="head">
      <span class="kicker">땡큐와인 소개</span>
      <h1>와인을 고르는 일부터<br>자리를 준비하는 일까지</h1>
      <p>땡큐와인은 서울 성수동에서 와인을 파는 데서 그치지 않고, 모임과 행사에 맞는 와인 구성, 기업·명절 선물, 와인잔 대여, 와인 강의와 시음회까지 한 사람이 끝까지 맡는 <b>와인 토탈 서비스</b>예요. 집에서 마실 한 병을 고르는 손님부터 30명 송년회, 거래처 여러 곳에 보내는 명절 선물까지 같은 방식으로 챙겨요.</p>
    </div>
    <ul class="checks">
      <li>모임·행사 와인 구성과 견적, 와인잔 대여, 행사장 배송·수거</li>
      <li>기업·명절 선물 와인 구성과 제안</li>
      <li>매장 구매와 미리 주문(성동구 성덕정길 109 2층), 와인 목록에 없는 가격은 카카오톡 1:1 안내</li>
      <li>와인 매너·와인 인문학 강의, 시음회 진행</li>
      <li>멤버 시음회·모임(10만원 이상 구매하시면 멤버)</li>
      <li><span>와인 수입사 <b>선샤인와인</b>, 와인 강사·인플루언서 매칭 <a class="textlink" href="{SITE['corkmatch']}" target="_blank" rel="noopener">코르크매치</a>와 함께</span></li>
    </ul>
    <div class="ctas"><a class="btn wine" href="{rel}gathering/">모임 와인 견적 받기</a><a class="btn line" href="{rel}gift/">기업·명절 선물 문의</a><a class="btn line" href="{rel}shop/">매장 안내</a></div>
  </div>
</section>
<section class="sec" id="doha">
  <div class="wrap">
    <div class="aboutgrid">
      <figure class="portrait"><img src="{rel}assets/img/doha.webp" alt="와인잔을 든 와인 컨설턴트 이도하" width="760" height="1168"><figcaption>와인 컨설턴트 이도하 · Wine Consultant</figcaption></figure>
      <div class="abouttext">
        <span class="kicker">대표 소개</span>
        <h2 class="big">와인은 취하려고가 아니라<br>대화를 풍성하게 하려고<br>마시는 거예요</h2>
        <p>안녕하세요, 땡큐와인을 운영하는 와인 컨설턴트 이도하입니다. 와인바로 시작했다가, 한자리에 머물기보다 사람들을 만나 그 자리에 맞는 와인을 골라 드리는 일이 더 맞는다는 걸 알고 지금의 땡큐와인으로 바꿨어요. 지금은 모임과 회사, 대표님들의 와인을 담당하고 있어요.</p>
        <p>땡큐와인에서는 세 가지만 여쭤봐요. 어떤 자리인지, 무엇과 함께 드실지, 어느 정도 예산이 편하신지. 이 세 가지만 알면 만족도가 가장 높은 와인을 찾아 드릴 수 있거든요. 와인을 잘 몰라도 괜찮아요. 아는 척하지 않아도 되는 자리를 만드는 게 제 일이에요.</p>
        <h3>하는 일</h3>
        <ul class="checks one">
          <li>땡큐와인 운영, 모임·행사·기업 선물 와인 컨설팅</li>
          <li>와인 매너, 와인 인문학 강의와 시음회 진행</li>
          <li>와인 수입사 선샤인와인 운영</li>
          <li><span>와인 강사·인플루언서 매칭 <a class="textlink" href="{SITE['corkmatch']}" target="_blank" rel="noopener">코르크매치</a> 운영</span></li>
        </ul>
        <h3>2027년 6월, 와이너리 크루즈</h3>
        <p>땡큐와인 멤버들과 크루즈를 타고 와이너리를 둘러보는 여행을 준비하고 있어요. 각자 예약하고 같이 떠나는 모임이에요. 궁금하시면 카톡으로 물어봐 주세요.</p>
        <div class="ctas"><a class="btn wine" href="#contact" data-contact>문의하기</a><a class="btn line" href="{SITE['blog']}" target="_blank" rel="noopener">블로그</a><a class="btn line" href="{SITE['insta']}" target="_blank" rel="noopener">인스타그램</a></div>
      </div>
    </div>
  </div>
</section>'''

# ---------------- 블로그 글 (posts_raw/ → /posts/<slug>/) ----------------
import html as _html
POSTS=[]
POSTS_RAW=os.path.join(HERE,'posts_raw')
SERVICE={'gathering':('모임 와인 견적 받기','gathering/','모임에 이 와인을 쓰고 싶으시면 인원과 예산만 알려 주세요. 구성과 가격은 카톡으로 1:1 안내해 드려요.'),
         'gift':('선물 와인 문의하기','gift/','선물로 생각하신다면 수량과 예산만 알려 주세요. 가격은 카톡으로 1:1 안내해 드려요.'),
         'shop':('매장 안내 보기','shop/','이 와인이 궁금하시면 카톡으로 물어봐 주세요. 가격은 1:1로 안내해 드려요.')}
PRICE_RE=_re.compile(r'\d{1,3}(?:,\d{3})+\s*원|\d+\s*만\s*\d*\s*천?\s*원(?!대)')
WARNINGS=[]

# ── 글 속 금액 정리 (사이트 원칙: 가격은 가격대만, 택배 안내 없음) ──
# PRICE_MODE  'none' = 금액·가격대가 든 문장을 통째로 삭제, 택배 문장도 삭제 (기본. 2026-11-15 도하: 블로그·인스타엔
#                      와인 가격도 '몇만원대' 같은 가격대도 쓰지 않음. 시음회·강의 참가비, 멤버 등록 기준 문장은 남김)
#             'band' = 1만원 이상 금액을 '8만원대'처럼 가격대로 바꾸고 택배 문장은 삭제 (11/3~11/15 방식)
#             'wine' = 1만5천원 이상(와인값으로 보이는 금액)만 가격대로, 택배비·콜키지는 그대로
#             'keep' = 네이버 글 그대로
PRICE_MODE='none'
_ANY_AMT=_re.compile(r'\d{1,3}(?:,\d{3})+\s*원|\d{4,}\s*원|\d+\s*만\s*\d*\s*천?\s*원|\d+\s*천\s*원|만원대|천원대|원대')
_FEE_KEEP=_re.compile(r'참가비|회비|수강료|강의료|강의|클래스|세미나|워크숍|멤버')
def sanitize_title(t):
    if PRICE_MODE!='none' or not t: return sanitize_text(t)
    t=t.replace('와인 디렉터','와인 컨설턴트').replace('와인디렉터','와인 컨설턴트')
    for a,b in WORD_RULES: t=t.replace(a,b)
    t=_re.sub(r'(?:\d[\d,]*\s*[~∼〜\-–]\s*)?\d[\d,]*\s*(?:만\s*\d*\s*천?\s*|천\s*)?원대?\s*(?:이하|이상|미만|이내|안팎|내외|정도|선|대)?\s*(?:의|짜리|에)?','',t)
    return _re.sub(r'\s{2,}',' ',t).strip(' ,·|-~')
SANITIZE_STATS={'amounts':0,'parcel':0}
_AMT=r'(\d{1,3}(?:,\d{3})+|\d{4,})'
_MAN=r'(\d+)\s*만\s*(\d)?\s*천?'
_KEEP=r'(?!\s*(?:대|이상|이하|미만|이내|초과|안팎|내외|정도|선에|선으로|부터|까지|쯤|가량|넘))'   # 이미 범위 표현이면 그대로
def _won(s): return int(s.replace(',',''))
def _band(won): return f'{won//10000}만원대'
def sanitize_text(t,mode=None):
    mode=mode or PRICE_MODE
    if not t: return t
    t=t.replace('와인 디렉터','와인 컨설턴트').replace('와인디렉터','와인 컨설턴트').replace('Wine Director','Wine Consultant')   # 직함은 와인 컨설턴트(11/2 도하)
    for a,b in WORD_RULES: t=t.replace(a,b)
    if mode=='keep': return t
    thr=10000 if mode=='band' else 15000
    out=[]
    if mode=='none':
        for ln in t.split('\n'):
            kept=[]
            for x in _re.split(r'(?<=[.!?。])\s+',ln):
                if _PARCEL.search(x): SANITIZE_STATS['parcel']+=1; continue
                if _ANY_AMT.search(x) and (not _FEE_KEEP.search(x) or '가입비' in x): SANITIZE_STATS['amounts']+=1; continue
                kept.append(x)
            ln=' '.join(kept).strip()
            if ln: out.append(ln)
        return '\n'.join(out)
    for ln in t.split('\n'):
        if mode=='band' and '택배' in ln:
            sents=_re.split(r'(?<=[.!?。])\s+',ln)
            kept=[x for x in sents if '택배' not in x]
            SANITIZE_STATS['parcel']+=len(sents)-len(kept)
            ln=' '.join(kept).strip()
            if not ln: continue
        def rng(m):
            a,b=_won(m.group(1)),_won(m.group(2))
            if a<thr or b<thr: return m.group(0)
            SANITIZE_STATS['amounts']+=1; return f'{a//10000}만~{b//10000}만원대'
        ln=_re.sub(_AMT+r'\s*[~∼〜\-–]\s*'+_AMT+r'\s*원'+_KEEP,rng,ln)
        def one(m):
            w=_won(m.group(1))
            if w<thr: return m.group(0)
            SANITIZE_STATS['amounts']+=1; return _band(w)
        ln=_re.sub(_AMT+r'\s*원'+_KEEP,one,ln)
        def man(m):
            w=int(m.group(1))*10000+(int(m.group(2))*1000 if m.group(2) else 0)
            if w<thr: return m.group(0)
            SANITIZE_STATS['amounts']+=1; return _band(w)
        ln=_re.sub(_MAN+r'\s*원'+_KEEP,man,ln)
        out.append(ln)
    return '\n'.join(out)
def sanitize_blocks(blocks):
    res=[]
    for b in blocks:
        b=dict(b)
        for k in ('text','caption','alt'):
            if isinstance(b.get(k),str): b[k]=sanitize_text(b[k])
        if b.get('type') in ('p','quote','h2') and not (b.get('text') or '').strip(): continue   # 택배 문장만 있던 문단은 통째로 제거
        if b.get('type') in ('p','quote') and _OLD_LINES.match(strip_md(b.get('text') or '').strip()): continue   # 옛 꼬리 안내 줄 제거
        res.append(b)
    return res

def esc(s): return _html.escape(str(s if s is not None else ''),quote=True)
def short(t,n=150):
    t=(t or '').strip()
    if len(t)<=n+5: return t
    cut=t[:n]; i=max(cut.rfind('. '),cut.rfind('요. '),cut.rfind('다. '))
    return (cut[:i+1] if i>40 else cut.rstrip()+'…')
def strip_md(t): return _re.sub(r'\*\*|==','',t or '')
def inline(t):
    t=esc(t)
    t=_re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',t,flags=_re.S)
    t=_re.sub(r'==(.+?)==',r'<mark>\1</mark>',t,flags=_re.S)
    return t
def parse_date(s):
    m=_re.search(r'(\d{4})\D+(\d{1,2})\D+(\d{1,2})',str(s or ''))
    return f'{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}' if m else ''
def kdate(iso):
    if not iso: return ''
    y,m,d=iso.split('-'); return f'{int(y)}년 {int(m)}월 {int(d)}일'
def split_title(t):
    t=_re.sub(r'\s*:\s*네이버 블로그\s*$','',str(t or '')).strip()
    i=t.find('｜')
    if i<0: i=t.find('|')
    return (t[:i].strip(),t[i+1:].strip()) if i>0 else (t,'')
BULLET=_re.compile(r'^[•·▪◦‣\-–]\s*(.+)$')
def para_html(text):
    out=[];buf=[];ul=[]
    def flush_p():
        if buf: out.append('<p>'+'<br>'.join(inline(x) for x in buf)+'</p>'); buf.clear()
    def flush_ul():
        if ul: out.append('<ul>'+''.join('<li>'+inline(x)+'</li>' for x in ul)+'</ul>'); ul.clear()
    for ln in (text or '').split('\n'):
        s=ln.strip()
        if not s: continue
        m=BULLET.match(s)
        if m: flush_p(); ul.append(m.group(1))
        else: flush_ul(); buf.append(s)
    flush_p(); flush_ul()
    return ''.join(out)
def facts_from(texts):
    rows=[]
    for text in texts:
        for ln in text.split('\n'):
            s=strip_md(ln.strip()); s=BULLET.sub(r'\1',s)
            m=_re.match(r'^([^:：]{1,14})\s*[:：]\s*(.+)$',s)
            if m: rows.append((m.group(1).strip(),m.group(2).strip()))
    return rows
def faq_from(texts):
    pairs=[]; q=None; a=[]
    for text in texts:
        for ln in text.split('\n'):
            s=ln.strip()
            if not s: continue
            isq=(s.startswith('**') and s.endswith('**')) or (s.endswith('?') and len(s)<80 and q is None) or (s.endswith('?') and a)
            if isq:
                if q and a: pairs.append((strip_md(q),' '.join(a)))
                q=strip_md(s).strip(); a=[]
            elif q: a.append(strip_md(s))
    if q and a: pairs.append((q,' '.join(a)))
    return pairs

# ── 네이버 글 정리: 공통 꼬리말(연락처·배송 안내) 제거, 해시태그 → 태그, 관련 글 링크 정리 ──
FOOTER_MARKS=('🥂 와인으로 연결되는 사람과 경험','와인으로 연결되는 사람과 경험','방문 픽업 및 배송 방법 안내','방문 픽업 및 택배·퀵 배송 안내','✔ 택배& 퀵 배송 안내','✔ 업장 방문하여 결제 또는 픽업 필수','📩 상담 · 문의','🍷땡큐와인 멤버십 가입','땡큐와인 멤버십 가입')
BAN_TAG=('택배','배송','답례품','웨딩','결혼','배달','원대','만원','가격','와인샵')          # 사이트 원칙: 택배·배달 안내 없음, 웨딩 답례품 언급 없음
EXCLUDE_TITLE=_re.compile(r'택배|배송 안내|배송 방법')
HASHTAG_LINE=_re.compile(r'^(#\S+\s*)+$')
URL_ONLY=_re.compile(r'^https?://\S+$')
NAVER_CATS={'멤버십 와인 커뮤니티 땡큐와인'}
_NOT_HEAD=_re.compile(r'^[\d@+]|[●○★☆]|^\d{2,3}-\d{3,4}-\d{4}$')
# 옛 글 표현 정리(2026-11-19 도하 OK): 땡큐와인을 가리키는 '와인샵'은 땡큐와인/매장으로, 답례품은 선물로. 일반적인 뜻의 '와인샵'(에노테카 뜻풀이, '일반 와인샵')은 그대로
WORD_RULES=[('땡큐와인(성수동 와인샵)','땡큐와인(성수동 매장)'),('서울숲 와인샵 땡큐와인','서울숲 땡큐와인'),('와인샵 땡큐와인','땡큐와인'),
 ('성수동 와인샵&바 한낮의밤','성수동 땡큐와인 · 한낮의밤'),('성수동 와인샵,','성수동 땡큐와인,'),('성수동 와인샵','성수동 땡큐와인'),('와인샵 겸 바 한낮의밤','와인 매장 겸 바 한낮의밤'),
 ('작은 와인샵이에요','작은 와인 매장이에요'),('와인샵이라 와인은','와인 매장이라 와인은'),('와인샵 공간이라','와인을 파는 공간이라'),('요즘 와인샵에서','요즘 매장에서'),
 ('와인샵에서 가장 자주 듣는','매장에서 가장 자주 듣는'),('막상 와인샵에 가면','막상 매장에 오시면'),('단순한 와인샵을 넘어','단순히 와인을 파는 곳을 넘어'),
 (', 결혼식 답례품',''),('결혼식 답례품','기념 선물'),('웨딩 답례품','기념 선물'),('기업 답례품','기업 선물'),('비즈니스 답례품','비즈니스 선물'),('선물이나 답례품으로','선물이나 행사 기념품으로'),('답례품','선물'),
 ('인스타그램 @middaynight109','인스타그램 @thankyouwine')]
# 옛 글(한낮의밤 시절) 꼬리 안내 줄: 옛 영업시간·휴무, 택배 안내, 옛 서명 줄은 사이트에 싣지 않음(영업시간은 사이트에 안 넣기로, 11/19 도하)
_OLD_LINES=_re.compile(r'^(와인 재고 확인 & 가격 문의|010-8078-7493|영업시간\s*:?|오후 5시 ~ 12시|정기휴무\s*:?|매주 화요일|예약 및 문의\s*:?|매장 방문 결제시 전국 배송 가능.*|6병 이상 구매시 서울 전지역 퀵\s?배송비 무료)$')
_PARCEL=_re.compile(r'택배|전국 ?배송|무료 ?배송|무료로 배송|비대면 배송')
_SENT_END=_re.compile(r'[.,。!…:]$|(?:요|다|죠|까|네|니다|세요|어요|아요|해요|예요|에요|습니다)$')
def _bold_line(b):
    raw=(b.get('text') or '').strip()
    return b.get('type')=='p' and raw.startswith('**') and raw.endswith('**') and raw.count('**')==2 and '\n' not in raw
def clean_blocks(blocks):
    cut=len(blocks)
    for i,b in enumerate(blocks):
        t=strip_md(b.get('text') or '').strip()
        if b.get('type') in ('h2','p') and t and any(t.startswith(m) or m in t[:40] for m in FOOTER_MARKS): cut=i; break
    blocks=list(blocks[:cut])
    while blocks and blocks[-1].get('type')=='hr': blocks.pop()
    out=[]; tags=[]
    for i,b in enumerate(blocks):
        if b.get('type')=='p':
            sline=strip_md(b.get('text') or '').strip()
            if HASHTAG_LINE.match(sline):
                tags+=[w.lstrip('#') for w in sline.split()]; continue
            if URL_ONLY.match(sline):
                nxt=blocks[i+1] if i+1<len(blocks) else None
                if not (nxt and nxt.get('type')=='link' and nxt.get('href')): out.append({'type':'link','href':sline})
                continue
            if sline.startswith('▲ 관련 글') and any(x.get('type')=='link' or URL_ONLY.match(strip_md(x.get('text') or '').strip()) for x in blocks[i+1:i+3]): continue
            raw=(b.get('text') or '').strip()
            if _bold_line(b) and 2<len(sline)<=60 and not sline.endswith('?') and not _SENT_END.search(sline) and not _NOT_HEAD.search(sline):
                nxt=next((x for x in blocks[i+1:i+4] if x.get('type') in ('p','quote','li','h2')),None)
                if len(sline)<=24 or not (nxt and _bold_line(nxt)):      # 굵은 문장이 줄줄이 이어지면 강조 본문이지 소제목이 아님
                    b=dict(b); b['type']='h2'; b['text']=sline
        if b.get('type')=='h2':
            sline=strip_md(b.get('text') or '').strip()
            if len(sline)>45 or (len(sline)>24 and _SENT_END.search(sline)) or _NOT_HEAD.search(sline):   # 긴 문장·연락처·평점 줄은 소제목이 아니라 강조 본문
                b=dict(b); b['type']='p'; b['text']='**'+sline+'**'
        out.append(b)
    tags=[x for x in dict.fromkeys(tags) if x and not any(bw in x for bw in BAN_TAG)]
    return out,tags
def _has_batchim(ch):
    o=ord(ch)
    if 0xAC00<=o<=0xD7A3: return (o-0xAC00)%28!=0
    if ch.isdigit(): return ch in '013678'
    return False
def eun_neun(w): return '은' if w and _has_batchim(w[-1]) else '는'
def ieyo(w): return '이에요' if w and _has_batchim(w[-1]) else '예요'
def point_summary(main,blocks):
    for i,b in enumerate(blocks[:-1]):
        t=strip_md(b.get('text') or '').strip()
        if t.startswith('무엇보다 중요한 포인트는 바로') and blocks[i+1].get('type') in ('p','h2'):
            pt=strip_md(blocks[i+1].get('text') or '').strip().rstrip('.')
            pt=_re.sub(r'(이)?라는\s*(것|점)$','',pt).strip()
            if not pt: return ''
            if _re.search(r'(다|요)$',pt): return f'{main}{eun_neun(main)} {pt}.'
            return f'{main}{eun_neun(main)} {pt}{ieyo(pt)}.'
    return ''
def guess_category(main,title):
    t=title
    if any(k in t for k in ('선물','답례품','기업','행사','모임','송년회','명절','연말','납품','특판','단체','파티','시음회')): return '모임·선물'
    if '｜' not in title and '|' not in title and any(k in main for k in ('이야기','방법','차이','뜻','기초','용어','고르','읽는','보관','온도','디캔팅','페어링','추천','이유','역사')): return '와인 이야기'
    return '와인 소개'

def _meta_all():
    fn=os.path.join(HERE,'posts_meta.json')
    if not os.path.exists(fn): return {}
    return {k:v for k,v in json.load(open(fn,encoding='utf-8')).items() if not k.startswith('_')}
def _find_meta(meta,logNo,title):
    if logNo in meta: return meta[logNo]
    for k,v in meta.items():
        if v.get('match') and v['match'] in title: return v
    return {}

def _first_sentence(blocks):
    # 첫 문단(20자 넘는 p)부터 문장이 끝날 때까지 줄을 이어 붙여 한 줄 요약으로
    texts=[(b['type'],strip_md(b.get('text') or '').split('\n')[0].strip()) for b in blocks if b.get('type') in ('p','quote','li','h2')]
    start=next((i for i,(t,x) in enumerate(texts) if t=='p' and len(x)>20),None)
    if start is None: start=next((i for i,(t,x) in enumerate(texts) if len(x)>15),None)
    if start is None: return ''
    acc=''
    for t,x in texts[start:start+4]:
        if not x: break
        acc=(acc+' '+x).strip()
        if _re.search(r'[.!?。…]$|(?:요|다|죠|까|니다)$',x) or len(acc)>=120: break
    return acc
HIDE_LOGNOS={'224240070422','224100251200','224240112168'}   # 웨딩·답례품이 주제인 옛 글은 사이트에 싣지 않음(11/19 도하). vercel.json에서 /blog/로 넘김
def load_posts():
    idx=os.path.join(POSTS_RAW,'index.json')
    if not os.path.exists(idx): return []
    meta=_meta_all(); posts=[]; seen_slug=set()
    for it in json.load(open(idx,encoding='utf-8'))['posts']:
        fn=os.path.join(POSTS_RAW,it['logNo']+'.json')
        if not os.path.exists(fn): continue
        d=json.load(open(fn,encoding='utf-8'))
        title=sanitize_title((d.get('title') or it.get('title') or '').strip())
        main,sub=split_title(title)
        m=_find_meta(meta,d['logNo'],title)
        raw,htags=clean_blocks(d.get('blocks') or [])
        blocks=sanitize_blocks(raw)
        first=_first_sentence(blocks) or f'{main} 소개'
        desc=sanitize_text((d.get('desc') or '').strip())
        if len(desc)<30 or desc.endswith(('...','…')) or any(bw in desc for bw in BAN_TAG): desc=''
        pointsum=point_summary(main,blocks)
        slug=m.get('slug') or 'n'+d['logNo']
        if slug in seen_slug: slug=slug+'-'+d['logNo']
        seen_slug.add(slug)
        words=sum(len(strip_md(b.get('text','')).split()) for b in blocks)
        if d['logNo'] in HIDE_LOGNOS:
            WARNINGS.append(f"숨김(웨딩·답례품 글, 11/19 도하): {title[:40]}"); continue
        if EXCLUDE_TITLE.search(title) or words<40:
            WARNINGS.append(f"제외(안내 글이거나 너무 짧음): {title[:40]} · {words}단어"); continue
        ncat=d.get('category') or it.get('category') or ''
        if ncat in NAVER_CATS: ncat=''
        ntags=[t for t in (d.get('tags') or []) if t and not any(bw in t for bw in BAN_TAG)]
        p=dict(logNo=d['logNo'],naver=d.get('url') or f"{SITE['blog']}/{d['logNo']}",title=main+(' | '+sub if sub else ''),main=main,sub=sub,
               date=parse_date(d.get('date') or it.get('date') or d.get('addDate')) or TODAY.isoformat(),
               category=m.get('category') or ncat or guess_category(main,title),
               tags=(ntags or htags)[:12],blocks=blocks,slug=slug,path='posts/'+slug+'/',
               summary=sanitize_text(m.get('summary') or '') or pointsum or desc or first,service=m.get('service') or 'shop',standin=bool(d.get('standin')),words=words)
        for b in blocks:
            if b['type'] in ('p','quote'):
                for hit in PRICE_RE.findall(strip_md(b['text'])): WARNINGS.append(f"가격 표현 확인: {p['slug']} → '{hit}'")
        posts.append(p)
    posts.sort(key=lambda x:(x['date'],x['logNo']),reverse=True)
    if PRICE_MODE!='keep' and (SANITIZE_STATS['amounts'] or SANITIZE_STATS['parcel']):
        print(f"금액 정리({PRICE_MODE}): 금액 문장 {SANITIZE_STATS['amounts']}곳 {'삭제' if PRICE_MODE=='none' else '→ 가격대'}, 택배 문장 {SANITIZE_STATS['parcel']}개 삭제")
    return posts

def prepare_images(posts):
    dst_dir=os.path.join(SITEDIR,'assets','posts'); os.makedirs(dst_dir,exist_ok=True)
    try: from PIL import Image, ImageOps
    except ImportError: Image=None
    for p in posts:
        for b in p['blocks']:
            if b['type']!='img' or not b.get('file'): continue
            src=os.path.join(POSTS_RAW,*b['file'].split('/'))
            stem,ext=os.path.splitext(os.path.basename(src)); ext=ext.lower()
            out_ext='.gif' if ext=='.gif' else '.jpg'
            dst=os.path.join(dst_dir,stem+out_ext); w=h=None
            if not os.path.exists(src):
                if not os.path.exists(dst): continue          # 원본도 변환본도 없으면 사진 없이
                try:
                    if Image and out_ext=='.jpg':
                        with Image.open(dst) as im: w,h=im.size
                except Exception: pass
                b['web']='assets/posts/'+stem+out_ext; b['w']=w; b['h']=h; continue
            try:
                if not os.path.exists(dst) or os.path.getmtime(dst)<os.path.getmtime(src):
                    if Image and out_ext=='.jpg':
                        im=Image.open(src); im=ImageOps.exif_transpose(im)
                        if im.mode!='RGB': im=im.convert('RGB')
                        if im.width>1200: im=im.resize((1200,round(im.height*1200/im.width)),Image.LANCZOS)
                        im.save(dst,'JPEG',quality=82,optimize=True,progressive=True); w,h=im.size
                    else: shutil.copyfile(src,dst)
                elif Image:
                    with Image.open(dst) as im: w,h=im.size
            except Exception as e:
                WARNINGS.append(f'이미지 변환 실패 {src}: {e}'); continue
            b['web']='assets/posts/'+stem+out_ext; b['w']=w; b['h']=h

def post_card(rel,p,ext=False):
    img=next((b for b in p['blocks'] if b.get('web')),None)
    thumb=f'<span class="thumb"><img src="{rel}{img["web"]}" alt="" loading="lazy" decoding="async"></span>' if img else ''
    sub=f'<p class="psub">{esc(p["sub"])}</p>' if p['sub'] else ''
    lead=esc(p['summary'][:120])
    return (f'<a class="post" href="{rel}{p["path"]}" data-cat="{esc(p["category"])}">{thumb}<span class="pcat">{esc(p["category"])}</span>'
            f'<h3>{esc(p["main"])}</h3>{sub}<p class="plead">{lead}</p><span class="pmeta"><span>{p["date"]}</span><i>읽기 →</i></span></a>')
def posts_cards(rel,posts):
    return ''.join(post_card(rel,p) for p in posts) if posts else '<p class="postsempty">아직 올린 글이 없어요.</p>'

def render_body(p,rel):
    by_logno={x['logNo']:x for x in POSTS}
    sections=[]; cur=(None,[])
    for b in p['blocks']:
        if b['type']=='hr': continue
        if b['type']=='h2':
            if cur[0] is not None or cur[1]: sections.append(cur)
            cur=(strip_md(b['text']).strip(),[])
        else: cur[1].append(b)
    if cur[0] is not None or cur[1]: sections.append(cur)
    out=[]; facts=[]; faq=[]; nimg=0
    for title,blocks in sections:
        texts=[b['text'] for b in blocks if b['type']=='p']
        if title and title.startswith('한눈에') and facts_from(texts):
            facts=facts_from(texts)
            if buyable(p): facts=facts+[('구매처','성수동 땡큐와인 매장 · 카톡으로 입고·가격 1:1 안내')]
            out.append(f'<section class="facts"><h2>{esc(title)}</h2><dl>'+''.join(f'<div><dt>{esc(k)}</dt><dd>{inline(v)}</dd></div>' for k,v in facts)+'</dl></section>')
            continue
        if title and '자주 묻는 질문' in title and faq_from(texts):
            faq=faq_from(texts)
            out.append(f'<h2>{esc(title)}</h2>'+faq_html([(esc(q),inline(a)) for q,a in faq]))
            continue
        if title: out.append(f'<h2>{esc(title)}</h2>')
        for b in blocks:
            t=b['type']
            if t=='p': out.append(para_html(b['text']))
            elif t=='quote': out.append('<blockquote>'+para_html(b['text'])+'</blockquote>')
            elif t=='img' and b.get('web'):
                nimg+=1; alt=esc(b.get('alt') or f"{p['main']} 사진 {nimg}")
                dims=f' width="{b["w"]}" height="{b["h"]}"' if b.get('w') and b.get('h') else ''
                load='' if nimg==1 else ' loading="lazy"'
                out.append(f'<figure class="aimg"><img src="{rel}{b["web"]}" alt="{alt}"{dims}{load} decoding="async"></figure>')
            elif t=='link' and b.get('href'):
                href=b['href']; m=_re.search(r'blog\.naver\.com/(?:PostView\.naver\?[^"]*logNo=|middaynight109/)(\d{9,})',href)
                if m and m.group(1) in by_logno:
                    x=by_logno[m.group(1)]; out.append(f'<p class="plink"><a href="{rel}{x["path"]}">→ {esc(x["main"])}</a></p>')
                else:
                    out.append(f'<p class="plink"><a href="{esc(href)}" target="_blank" rel="noopener">{esc(href)}</a></p>')
    return ''.join(out),facts,faq

def ld_post(p,faq):
    url=BASE+'/'+p['path']
    imgs=[BASE+'/'+b['web'] for b in p['blocks'] if b.get('web')][:4]
    art={"@context":"https://schema.org","@type":"BlogPosting","@id":url+'#article',"url":url,"mainEntityOfPage":url,
         "headline":p['main'][:110],"alternativeHeadline":p['sub'],"name":p['title'],"description":p['summary'],
         "datePublished":p['date'],"dateModified":p['date'],"inLanguage":"ko-KR","isAccessibleForFree":True,
         "author":{"@type":"Person","@id":PERSON_ID,"name":"이도하","jobTitle":"와인 컨설턴트","url":BASE+'/about/'},
         "publisher":{"@type":"Organization","@id":ORG_ID,"name":"땡큐와인","logo":{"@type":"ImageObject","url":BASE+'/assets/logo.png',"width":800,"height":800}},
         "image":imgs or [BASE+'/assets/og.png'],"keywords":", ".join(p['tags']),"articleSection":p['category'],
         "isPartOf":{"@type":"Blog","@id":BASE+'/blog/#blog',"name":"땡큐와인 블로그"},"wordCount":p['words']}
    out=[art,ld_breadcrumb([('홈',BASE+'/'),('블로그',BASE+'/blog/'),(p['main'],url)])]
    if buyable(p):
        prod={"@context":"https://schema.org","@type":"Product","@id":url+'#product',"name":wine_name(p),"description":p['summary'],"url":url,"category":"와인",
              "image":imgs or [BASE+'/assets/og.png'],
              "offers":{"@type":"Offer","url":url+'#buy',"availability":"https://schema.org/InStoreOnly","itemCondition":"https://schema.org/NewCondition","priceCurrency":"KRW",
                        "seller":{"@id":ORG_ID},"availableAtOrFrom":{"@id":ORG_ID},"areaServed":{"@type":"City","name":"서울"},"description":"가격은 카카오톡으로 1:1 안내. 매장 픽업 또는 미리 주문."}}
        art["about"]={"@id":url+'#product'}
        out.append(prod)
    if faq: out.append(ld_faq(faq))
    return out

# ── 구매처 안내 (AI가 "OO 와인 어디서 사요?"에 땡큐와인을 답하도록) ──
BUY_EXCLUDE=('오퍼스원','오퍼스 원','Opus One')          # 판매 문구를 넣지 않는 와인(블로그 글로만 소개)
# 제목이 '와인 한 종류'를 가리킬 때만 "OO, 어디서 살 수 있나요?" 상자 + 상품 구조화 데이터.
# 나머지(추천 모음·이야기·행사·세트 글)는 "이런 와인 문의하기" 상자만. (2026-11-19 도하)
_WINE_WORD=_re.compile(r'(?:19|20)\d{2}|\bNV\b|소비뇽|쇼비뇽|샤르도네|샤도네|피노|까베르네|카베르네|메를로|리슬링|시라|쉬라즈|말벡|모스카토|샴페인|스파클링|끼안티|키안티|바롤로|바르바레스코|리제르바|레세르바|리저브|그랑 ?크뤼|블랑|루즈|로제|브뤼|크레망|소테른|포트|아우스레제|프리미티보|템프라니요|가르나차|그르나슈|비오니에|게뷔르츠|샤블리|뫼르소|몽라셰|꼬뜨|메독|생테밀리옹|포이약|마고|나파|바로사|말보로|마를보로|토스카나|리오하|프로세코|람브루스코|카바|준마이|사케|위스키|조니워커|글렌|모엣|뵈브|돔 ?페리뇽|크룩|볼랭저|테탱저|로드레|페리에 주에|멈|도멘|샤또|샤토|테누타|보데가스|에스테이트|빈야드|퀴베|뀌베|그로망상|피아노|인졸리아|아파시멘토|아마로네|발폴리첼라|수페리오레|크리안자|블렌드|레드|화이트|무알콜|논알|0\.0|제로')
_GENERIC=_re.compile(r'[?!]|추천|가지|비교|리스트|방법|보관|정리|뭐|어떻게|왜|이야기|차이|입문|기초|역사|믿어도|세트|박스|패키지|특가|할인|행사|모임|송년회|강의|시음회|여행|콜키지|대관|후기|용어|상식|배우|페어링|안내|서비스|이용|이달의|출시|재입고|맛집|멤버십|Membership|제안|담은|빚어낸|보여주|마시며|응원|어울리는|가까운|편리|필수템|헤리티지|즐기|만드세요|유혹|여름날|시원|년생|정보|×|BEST|TOP|타닌감|묵직|화사한|탐구|극찬|열정|우아함|울림|\[')
_EMOJI=_re.compile('[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B50\u2B55\uFE0F]')
def wine_name(p):
    n=_EMOJI.sub('',p['main']); n=_re.sub(r'^\s*[\[(][^\])]*[\])]\s*','',n); n=_re.sub(r'\s{2,}',' ',n).strip(' ,·|')
    return n or p['main']
def buyable(p):
    """특정 와인 한 종류를 소개한 글인가(구매 상자·FAQ·Product 데이터 대상)"""
    m=p['main']
    return (p['category']=='와인 소개' and bool(_WINE_WORD.search(m)) and not _GENERIC.search(m)
            and not any(x in m for x in BUY_EXCLUDE))
def askable(p):
    """와인 한 종류는 아니지만 와인 글이라 '이런 와인 문의하기' 상자를 붙일 글"""
    return (not buyable(p)) and p['category'] in ('와인 소개','모임·선물','와인 이야기') and not any(x in p['main'] for x in BUY_EXCLUDE) and not _NOTICE.search(p['main'])
_NOTICE=_re.compile(r'강의|시음회|대관|예약|행사|안내|서비스|이용|멤버십|Membership|제로페이|주소|인문학|클래스|모집|오픈|마감')
def askbox_html(rel,p):
    return ('<aside class="buybox" id="buy"><h2>이런 와인, 땡큐와인에 문의하기</h2>'
            '<p>글에 나온 와인이나 비슷한 와인이 궁금하시면 카카오톡으로 편하게 물어보세요. 서울 성수동 <strong>땡큐와인</strong> 매장(성동구 성덕정길 109 2층)에서 바로 구매하시거나 미리 주문해 두실 수 있고, 모임·선물용 수량 주문과 세금계산서 발행도 돼요.</p>'
            f'<div class="ctas"><a class="btn wine" href="#contact" data-contact>카톡으로 문의하기</a><a class="btn line" href="{rel}shop/">매장 위치 보기</a></div></aside>')
def buy_faq(p):
    n=wine_name(p)
    return [(f'{n}{eun_neun(n)} 어디서 살 수 있나요?', f'서울 성수동 땡큐와인 매장(성동구 성덕정길 109 2층)에서 구매할 수 있어요. 카카오톡으로 와인 이름을 보내 주시면 입고 상황과 가격을 1:1로 알려 드리고, 매장에서 바로 가져가시거나 미리 주문해 두실 수 있어요.'),
            (f'{n} 가격은 얼마인가요?', '수입사 행사와 입고 시기에 따라 가격이 자주 바뀌어서 사이트에는 적지 않고, 카카오톡으로 1:1 안내해 드려요. 모임·선물용 수량 주문은 세금계산서 발행도 돼요.')]
def buybox_html(rel,p):
    n=esc(wine_name(p))
    return (f'<aside class="buybox" id="buy"><h2>{n}, 어디서 살 수 있나요?</h2>'
            f'<p><strong>{n}</strong>{eun_neun(wine_name(p))} 서울 성수동 <strong>땡큐와인</strong> 매장(성동구 성덕정길 109 2층)에서 구매할 수 있어요. 카카오톡으로 와인 이름을 보내 주시면 입고 상황과 가격을 1:1로 알려 드리고, 매장에서 바로 가져가시거나 미리 주문해 두실 수 있어요. 모임·선물용 수량 주문과 세금계산서 발행도 돼요.</p>'
            f'<div class="ctas"><a class="btn wine" href="#contact" data-contact>카톡으로 입고·가격 묻기</a><a class="btn line" href="{rel}shop/">매장 위치 보기</a></div></aside>')

def page_post(rel,p):
    body,facts,faq=render_body(p,rel)
    buy=buyable(p)
    p['_faq']=faq+(buy_faq(p) if buy else [])
    buybox=(buybox_html(rel,p)+'<section class="buyfaq"><h2>구매 전에 자주 묻는 질문</h2>'+faq_html([(esc(q),esc(a)) for q,a in buy_faq(p)])+'</section>') if buy else (askbox_html(rel,p) if askable(p) else '')
    svc=SERVICE.get(p['service'],SERVICE['shop'])
    related=[x for x in POSTS if x['logNo']!=p['logNo'] and x['category']==p['category']][:3]
    if len(related)<3: related+=[x for x in POSTS if x['logNo']!=p['logNo'] and x not in related][:3-len(related)]
    tags=''.join(f'<span class="tag">#{esc(t)}</span>' for t in p['tags'][:10])
    sub=f'<p class="asub">{esc(p["sub"])}</p>' if p['sub'] else ''
    return f'''
<section class="sec tight">
  <div class="wrap">
    <article class="article">
      <nav class="crumbs" aria-label="현재 위치"><a href="{rel}">홈</a><span>›</span><a href="{rel}blog/">블로그</a><span>›</span><span>{esc(p['category'])}</span></nav>
      <header class="ahead">
        <span class="kicker">{esc(p['category'])}</span>
        <h1>{esc(p['main'])}</h1>
        {sub}
        <p class="ameta"><a href="{rel}about/">이도하 · 와인 컨설턴트</a> · <time datetime="{p['date']}">{kdate(p['date'])}</time></p>
      </header>
      {('<div class="summary"><b>한 줄 요약</b><p>'+esc(p['summary'])+'</p></div>') if p['summary'] else ''}
      {eventbox_html(p)}
      <div class="abody">{body}</div>
      {buybox}
      <aside class="acta"><p>{svc[2]}</p><div class="ctas"><a class="btn wine" href="#contact" data-contact>카톡으로 물어보기</a><a class="btn line" href="{rel}{svc[1]}">{svc[0]}</a></div></aside>
      <p class="aorig">이 글은 <a href="{p['naver']}" target="_blank" rel="noopener">땡큐와인 네이버 블로그</a>에 먼저 올린 글이에요.</p>
      {f'<div class="tags">{tags}</div>' if tags else ''}
    </article>
  </div>
</section>
<section class="sec related">
  <div class="wrap">
    <div class="head"><span class="kicker">함께 읽기</span><h2>이어서 읽으면 좋은 글</h2></div>
    <div class="posts">{posts_cards(rel,related)}</div>
    <div class="morerow"><a class="btn line" href="{rel}blog/">글 전체 보기</a><a class="textlink" href="{SITE['blog']}" target="_blank" rel="noopener">네이버 블로그로 가기 →</a></div>
  </div>
</section>'''

def write_posts_json(posts):
    data={'updated':TODAY.isoformat(),'note':'사이트에 올린 블로그 글 목록(build.py가 만들어요). 사이트는 이 목록을 HTML에 미리 넣고, /api/posts(네이버 RSS)로 아직 사이트에 없는 새 글만 덧붙여요.',
          'posts':[{'logNo':p['logNo'],'title':p['title'],'path':p['path'],'url':BASE+'/'+p['path'],'naver':p['naver'],'date':p['date'],'category':p['category'],'lead':p['summary'][:140],
                    'image':next((b['web'] for b in p['blocks'] if b.get('web')),'')} for p in posts]}
    os.makedirs(os.path.join(SITEDIR,'data'),exist_ok=True)
    with open(os.path.join(SITEDIR,'data','posts.json'),'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=1)

def blocks_markdown(p):
    out=[]
    for b in p['blocks']:
        t=b['type']
        if t=='h2': out.append('## '+strip_md(b['text']))
        elif t=='p': out.append(b['text'].replace('==',''))
        elif t=='quote': out.append('\n'.join('> '+l for l in b['text'].split('\n')))
        elif t=='img' and b.get('web'): out.append(f"![{b.get('alt') or p['main']}]({BASE}/{b['web']})")
        elif t=='link' and b.get('href'): out.append(b['href'])
    return '\n\n'.join(out)

# ---------------- 블로그 목록 ----------------
def page_blog(rel):
    cats=[]
    for p in POSTS:
        if p['category'] not in cats: cats.append(p['category'])
    chips=''.join(f'<button class="chip" type="button" data-cat="{esc(c)}" aria-pressed="false">{esc(c)}</button>' for c in cats)
    return f'''
<section class="sec tight" id="blog">
  <div class="wrap">
    <div class="head">
      <span class="kicker">블로그</span>
      <h1>와인 소개와 와인 이야기</h1>
      <p>네이버 블로그에 올린 글 {len(POSTS)}편을 사이트에서도 읽을 수 있어요. 글마다 한 줄 요약을 먼저 두었어요.</p>
    </div>
    <div class="chips" id="post-chips" role="group" aria-label="글 분류"><button class="chip" type="button" data-cat="" aria-pressed="true">전체</button>{chips}</div>
    <div class="posts" id="posts-all">{posts_cards(rel,POSTS)}<p class="postsempty" hidden>이 분류의 글이 아직 없어요.</p></div>
    <div class="morerow"><a class="btn line" href="{SITE['blog']}" target="_blank" rel="noopener">네이버 블로그로 가기</a><a class="textlink" href="{SITE['insta']}" target="_blank" rel="noopener">인스타그램 @{SITE['insta_id']} →</a></div>
  </div>
</section>'''
def ld_blog():
    return [{"@context":"https://schema.org","@type":"Blog","@id":BASE+'/blog/#blog',"url":BASE+'/blog/',"name":"땡큐와인 블로그","inLanguage":"ko-KR","publisher":{"@id":ORG_ID},
             "blogPost":[{"@type":"BlogPosting","headline":p['main'],"url":BASE+'/'+p['path'],"datePublished":p['date']} for p in POSTS]}]

# ---------------- 상황별 와인 고르기 (CEP 페이지, 2026-11-03 GEO 반영) ----------------
# 손님이 AI에게 묻는 '상황' 하나당 한 블록. 질문 → 바로 답 → 고르는 기준 → 가격대 → 이어지는 글·서비스.
# 새 상황은 여기에 한 줄씩 추가하면 사이트·llms.txt·구조화 데이터에 같이 들어가요.
OCCASIONS=[
 dict(id='year-end-company', q='회사 송년회 와인, 20~30명이면 몇 병을 어떻게 준비하나요?',
   a='식사 중심 송년회면 2~3명에 1병, 대화가 길어지면 2명에 1병으로 잡아요. 20명이면 7~10병, 30명이면 10~15병이에요. 건배용 스파클링 → 가벼운 화이트 → 메인 요리와 레드 순서로 구성하고, 와인잔 대여와 행사장 배송·수거까지 한 번에 준비해 드려요. 회사 주문은 세금계산서를 발행해요.',
   rows=[('인원','2~3명에 1병(식사 중심) / 2명에 1병(긴 자리)'),('구성','스파클링·화이트·레드를 1:1:2 정도'),('잔','인원만큼 대여, 끝나면 수거'),('서류','세금계산서 발행')],
   service='gathering', posts=['year-end-party-wine','how-to-choose-party-wine']),
 dict(id='club-meetup', q='동호회 정모나 소모임에 가져갈 와인, 와인 모르는 사람이 많으면 뭘 고르나요?',
   a='처음 마시는 분이 많으면 산뜻한 스파클링과 살짝 달콤하거나 상큼한 화이트를 먼저 두고, 레드는 타닌이 부드러운 메를로나 과실감 있는 레드로 고르면 실패가 적어요. 1인 1병과 2인 1병 견적을 나란히 드려서 회비에 맞춰 고를 수 있어요.',
   rows=[('입문자 많을 때','스파클링, 상큼한 화이트, 부드러운 레드'),('견적','1인 1병 / 2인 1병, 잔 포함 / 잔 미포함'),('장소','행사장 배송 또는 매장 픽업')],
   service='gathering', posts=['domaine-haut-brande-merlot-2022','baron-de-baussac-colombard-sauvignon-2023','7-deadly-red']),
 dict(id='client-holiday-gift', q='거래처 명절 선물로 와인을 보내려면 예산별로 뭘 고르나요?',
   a='거래처 여러 곳에 같은 선물을 보낼 때는 이름이 알려진 산지(보르도·부르고뉴·나파밸리)의 와인을 고르면 받는 분이 부담 없이 반가워해요. 특별히 챙길 분께는 샴페인이나 부르고뉴, VIP께는 보르도 5대 샤토까지 예산에 맞춰 골라 드려요. 기업 주문은 세금계산서를 발행해요.',
   rows=[('여러 곳에 같은 선물','이름이 알려진 산지의 와인'),('특별히 챙길 분','샴페인·부르고뉴·나파밸리'),('VIP·대표님','보르도 5대 샤토·빈티지 샴페인'),('서류','세금계산서 발행')],
   service='gift', posts=['caymus-napa-cabernet-sauvignon','baron-dauvergne-fine-fleur-champagne','jonathan-seguin-bourgogne-pinot-noir-vv-2024']),
 dict(id='vip-thanks', q='대표님이나 VIP께 감사 인사로 드릴 고급 와인은 어떻게 고르나요?',
   a='받는 분이 와인을 즐기시면 이야기가 있는 와인이 좋아요. 보르도 5대 샤토, 나파밸리 대표 와인, 좋은 해의 빈티지 샴페인처럼 이름만 들어도 아는 와인이나, 그 해에 의미가 있는 빈티지를 골라 드려요. 어떤 분께 어떤 자리에서 드리는지 알려 주시면 맞춰 드려요.',
   rows=[('기준','이름이 알려진 와인 또는 의미 있는 빈티지'),('함께 전할 것','와인 소개 한 줄(원하시면 정리해 드림)')],
   service='gift', posts=['opus-one-2022','charles-gardet-millesime-2008','great-vintages-for-wine-gifts']),
 dict(id='birth-year-vintage', q='태어난 해 와인(생빈티지)을 선물하고 싶어요. 어떻게 찾나요?',
   a='태어난 해가 좋은 해(그레이트 빈티지)라면 보르도, 샴페인, 바롤로처럼 오래 두고 마시는 와인에서 찾을 수 있어요. 예를 들어 2008년생 성인 기념이라면 2008 빈티지 샴페인을 추천해요. 연도와 예산을 알려 주시면 구할 수 있는 와인을 찾아 드려요.',
   rows=[('잘 남아 있는 와인','보르도 레드, 빈티지 샴페인, 바롤로·브루넬로'),('필요한 정보','태어난 해, 예산, 드릴 날짜')],
   service='gift', posts=['great-vintages-for-wine-gifts','charles-gardet-millesime-2008']),
 dict(id='bbq-red', q='고기 굽는 날 편하게 딸 레드 와인은 뭐가 좋아요?',
   a='삼겹살·목살처럼 기름진 고기에는 타닌이 적당하고 과실감 있는 까베르네 소비뇽이나 메를로가 잘 맞아요. 칠레·호주 까베르네 소비뇽, 보르도 메를로처럼 데일리로 따기 좋은 레드를 골라 드려요.',
   rows=[('기름진 고기','칠레·호주 까베르네 소비뇽'),('부드럽게','보르도 메를로'),('여럿이 편하게','과실감 있는 미국 레드 블렌드')],
   service='gathering', posts=['tarapaca-gran-reserva-cabernet-sauvignon-2023','grand-barossa-cabernet-sauvignon-2020','7-deadly-red']),
 dict(id='seafood-white', q='굴이나 회, 해산물과 같이 마실 화이트 와인은요?',
   a='해산물에는 오크 없이 산뜻하고 산도가 살아 있는 화이트가 잘 맞아요. 상큼한 뉴질랜드 소비뇽 블랑, 미네랄이 느껴지는 부르고뉴 마콩 샤르도네, 가볍게 마시는 남프랑스 화이트를 상황에 따라 골라 드려요.',
   rows=[('굴·회','소비뇽 블랑, 오크 없는 샤르도네'),('가볍게 여럿이','남프랑스 데일리 화이트'),('온도','차갑게(8~10도)')],
   service='gathering', posts=['kim-crawford-sauvignon-blanc','pierre-armand-macon-villages-2024','baron-de-baussac-colombard-sauvignon-2023']),
 dict(id='special-day-champagne', q='기념일·특별한 날 열 샴페인은 어떻게 고르나요?',
   a='샴페인은 포도 품종과 마을로 맛이 달라져요. 과실감과 구조감을 원하면 피노 누아로 만든 블랑 드 누아, 섬세하고 산뜻한 맛을 원하면 샤르도네 중심을 골라요. 의미를 더하고 싶으면 기념하는 해의 빈티지 샴페인도 있어요.',
   rows=[('깊고 과실감 있게','블랑 드 누아(피노 누아)'),('섬세하게','샤르도네 중심'),('의미 있게','빈티지 샴페인')],
   service='gift', posts=['baron-dauvergne-fine-fleur-champagne','charles-gardet-millesime-2008']),
 dict(id='sweet-beginner', q='와인을 처음 마시는 사람에게 단 와인을 주고 싶어요. 어떤 게 있나요?',
   a='단 와인은 만드는 방법에 따라 늦수확, 귀부, 아이스와인, 주정강화 와인으로 나뉘어요. 처음이라면 도수가 낮고 상큼하게 단 독일 리슬링이나 살짝 달콤한 화이트부터 권해요. 디저트와 함께라면 더 진한 스위트 와인도 좋아요.',
   rows=[('처음 마시는 분','살짝 달콤한 화이트, 독일 리슬링'),('디저트와','귀부·아이스와인'),('식후 한 잔','포트 같은 주정강화 와인')],
   service='gift', posts=['sweet-wine-types']),
]

def _occ_posts(rel,slugs):
    by={p['path'].strip('/').split('/')[-1]:p for p in POSTS}
    out=[by[s] for s in slugs if s in by]
    return out

def page_occasions(rel):
    toc=''.join(f'<li><a class="textlink" href="#{o["id"]}">{esc(o["q"])}</a></li>' for o in OCCASIONS)
    blocks=[]
    for o in OCCASIONS:
        rows=''.join(f'<tr><td>{esc(k)}</td><td>{esc(v)}</td></tr>' for k,v in o['rows'])
        ps=_occ_posts(rel,o['posts'])
        plinks=''.join(f'<li><a class="textlink" href="{rel}{p["path"]}">{esc(p["main"])}</a></li>' for p in ps)
        svc=SERVICE.get(o['service'])
        cta=f'<a class="btn wine sm" href="{rel}{svc[1]}">{svc[0]}</a>' if svc else ''
        blocks.append(f'''
<section class="sec" id="{o['id']}">
  <div class="wrap">
    <div class="head"><h2>{esc(o['q'])}</h2></div>
    <p><b>{esc(o['a'])}</b></p>
    <div class="tablebox"><table><thead><tr><th>고르는 기준</th><th>추천</th></tr></thead><tbody>{rows}<tr><td>가격</td><td>카카오톡 1:1 안내 (예산을 알려 주시면 그 안에서 제안)</td></tr></tbody></table></div>
    {('<p class="postsnote">이어서 읽어 보세요</p><ul>'+plinks+'</ul>') if plinks else ''}
    <div class="ctas">{cta}<a class="btn line sm" href="#contact" data-contact>카톡으로 물어보기</a></div>
  </div>
</section>''')
    return f'''
<section class="sec tight" id="occasions">
  <div class="wrap">
    <div class="head">
      <span class="kicker">상황별 와인 고르기</span>
      <h1>이런 자리엔<br>이런 와인을 골라요</h1>
      <p>와인 컨설턴트 이도하가 손님들께 가장 많이 받는 질문을 상황별로 정리했어요. 어떤 자리인지, 무엇과 드실지, 편한 가격대만 알려 주시면 맞는 와인을 골라 드려요.</p>
    </div>
    <ol>{toc}</ol>
  </div>
</section>'''+''.join(blocks)

def ld_occasions():
    faq=ld_faq([(o['q'],o['a']) for o in OCCASIONS])
    lst={"@context":"https://schema.org","@type":"ItemList","name":"상황별 와인 고르기 · 땡큐와인","itemListElement":[{"@type":"ListItem","position":i+1,"name":o['q'],"url":BASE+'/occasions/#'+o['id']} for i,o in enumerate(OCCASIONS)]}
    bc=ld_breadcrumb([('홈',BASE+'/'),('상황별 와인 고르기',BASE+'/occasions/')])
    return [faq,lst,bc]


# ---------------- FAQ ----------------
def page_faq(rel):
    return f'''
<section class="sec tight" id="faq">
  <div class="wrap">
    <div class="head">
      <span class="kicker">자주 묻는 질문</span>
      <h1>궁금한 점</h1>
      <p>여기 없는 질문은 카톡이나 문자로 편하게 물어봐 주세요.</p>
    </div>
    {faq_html(FAQ_ALL)}
    <div class="ctas"><a class="btn wine" href="#contact" data-contact>문의하기</a><a class="btn line" href="{rel}gathering/">모임 와인 견적 받기</a></div>
  </div>
</section>'''

# ---------------- 개인정보처리방침 ----------------
def page_privacy(rel):
    return f'''
<section class="sec tight">
  <div class="wrap doc">
    <h1>개인정보처리방침</h1>
    <p class="date">시행일 {PRIVACY_DATE.year}년 {PRIVACY_DATE.month}월 {PRIVACY_DATE.day}일</p>
    <p>땡큐와인(운영 {SITE['owner']}, 이하 "땡큐와인")은 개인정보 보호법에 따라 이용자의 개인정보를 보호하고, 이와 관련한 고충을 신속하게 처리하기 위해 다음과 같이 개인정보처리방침을 둡니다.</p>
    <h2>1. 수집하는 개인정보와 수집 방법</h2>
    <p>땡큐와인은 이용자가 직접 입력한 정보만 수집하며, 서비스별로 다음 항목을 수집합니다.</p>
    <div class="tablebox"><table>
      <thead><tr><th>구분</th><th>수집 항목</th><th>수집 시점</th></tr></thead>
      <tbody>
        <tr><td>모임·행사 와인 견적</td><td>연락처(이름, 휴대폰 번호 또는 카카오톡 ID), 인원, 날짜, 장소, 자리 성격, 예산, 음식, 요청 내용</td><td>견적 요청 폼 작성 시</td></tr>
        <tr><td>기업·명절 선물 문의</td><td>회사·이름, 연락처(휴대폰 번호 또는 이메일), 수량, 예산, 받는 분, 필요한 날, 세금계산서 필요 여부, 요청 내용</td><td>선물 문의 폼 작성 시</td></tr>
        <tr><td>멤버 등록</td><td>이름, 연락처(휴대폰 번호 또는 카카오톡 ID), 구매 내역</td><td>10만원 이상 구매로 멤버 등록 시</td></tr>
        <tr id="member"><td>회원 가입(내 와인)</td><td>이름, 이메일(카카오·구글 계정 정보), 휴대폰 번호, 매장 구매 기록 중 와인 이름·구매 날짜·병 수, 선불권 충전·사용 내역과 잔액(선불권이 있는 경우), 별점·한 줄 메모</td><td>카카오·구글로 가입하고 내 정보를 저장할 때, 관리자가 구매 기록을 연결할 때</td></tr>
        <tr><td>자동 수집</td><td>접속 IP, 브라우저 정보, 접수 시각</td><td>폼 접수 시 자동 기록</td></tr>
      </tbody>
    </table></div>
    <h2>2. 개인정보의 이용 목적</h2>
    <ul>
      <li>견적·문의 확인과 와인 추천, 결과 안내, 연락</li>
      <li>주문 확인, 결제 안내, 세금계산서·현금영수증 발행, 전달</li>
      <li>멤버에게 입고 소식과 시음회·모임 안내 (원하지 않으면 언제든 중단)</li>
      <li>회원이 산 와인을 모아 보여 주고, 산 와인에 별점·메모를 남기게 함 (구매 가격은 보여 주지 않음)</li>
      <li>부정 이용 방지, 서비스 개선</li>
    </ul>
    <h2>3. 보유와 이용 기간</h2>
    <ul>
      <li>견적·문의 정보: 상담 종료 후 1년. 이용자가 삭제를 요청하면 즉시 삭제합니다.</li>
      <li>멤버 정보: 탈퇴 또는 삭제 요청 시 즉시 삭제합니다.</li>
      <li>회원(내 와인) 정보: 탈퇴하면 회원 정보·구매 기록 연결·별점·메모를 즉시 삭제합니다. 같은 로그인으로 코르크매치를 쓰지 않으면 로그인 계정도 함께 삭제합니다.</li>
      <li>계약·결제 기록: 전자상거래 등에서의 소비자보호에 관한 법률에 따라 5년, 세법에 따른 거래 증빙은 5년 보관합니다.</li>
      <li>접속 기록: 통신비밀보호법에 따라 3개월 보관합니다.</li>
    </ul>
    <h2>4. 개인정보의 제3자 제공</h2>
    <p>법령에 따른 요청이 있을 때만 제공합니다. 배송이 필요한 주문은 전달에 필요한 범위에서 수입사·배송업체에 받는 분의 이름, 연락처, 주소를 전달합니다.</p>
    <h2>5. 개인정보 처리 위탁과 국외 이전</h2>
    <p>원활한 서비스 운영을 위해 다음 업체에 처리를 위탁하며, 서버가 국외에 있어 개인정보가 국외로 이전됩니다.</p>
    <div class="tablebox"><table>
      <thead><tr><th>수탁 업체</th><th>위탁 업무</th><th>이전 국가</th></tr></thead>
      <tbody>
        <tr><td>Vercel Inc.</td><td>웹사이트 호스팅, 폼 접수 처리</td><td>미국</td></tr>
        <tr><td>Google LLC</td><td>접수 내용 저장(스프레드시트), 메일 알림</td><td>미국</td></tr>
        <tr><td>Supabase Inc.</td><td>회원 계정, 내 와인(구매 기록 연결·별점·메모) 저장</td><td>{SUPABASE_REGION}</td></tr>
      </tbody>
    </table></div>
    <h2>6. 이용자의 권리</h2>
    <p>이용자는 언제든지 자신의 개인정보를 열람·정정·삭제하거나 처리 정지를 요청할 수 있습니다. 아래 연락처로 요청하시면 영업일 3일 안에 처리하고 결과를 알려 드립니다.</p>
    <h2>7. 개인정보의 파기</h2>
    <p>보유 기간이 지나거나 처리 목적이 달성되면 지체 없이 파기합니다. 전자 파일은 복구할 수 없는 방법으로 삭제하고, 종이 문서는 분쇄합니다.</p>
    <h2>8. 안전성 확보 조치</h2>
    <ul>
      <li>개인정보는 운영자만 접근할 수 있는 계정에 보관하고, 접근 권한을 최소화합니다.</li>
      <li>웹사이트는 HTTPS로 암호화해 전송합니다.</li>
    </ul>
    <h2>9. 개인정보 보호책임자</h2>
    <ul>
      <li>책임자: {SITE['ceo']} (땡큐와인 운영)</li>
      <li>연락처: {PHONE} (문자·전화), {SITE['email']}</li>
    </ul>
    <p>개인정보 침해에 대한 신고나 상담은 개인정보침해신고센터(privacy.kisa.or.kr, 국번 없이 118)에서도 할 수 있습니다.</p>
    <h2>10. 방침의 변경</h2>
    <p>이 방침을 변경할 때는 시행 7일 전부터 웹사이트에 공지합니다.</p>
  </div>
</section>'''

def page_404(rel):
    return f'''
<section class="notfound">
  <div class="wrap">
    <h1>이 페이지는 비어 있어요</h1>
    <p class="muted">주소가 바뀌었거나 잘못 입력됐어요.</p>
    <div class="ctas" style="justify-content:center"><a class="btn wine" href="{rel}">홈으로</a><a class="btn line" href="{rel}gathering/">모임 와인 견적</a></div>
  </div>
</section>'''

def preview_links(html,rel,key):
    # 미리보기(아티팩트)용: 폴더 링크를 index.html 로 바꾸고, 바깥 태그를 떼어냄
    def fix(m):
        href=m.group(1)
        if href.startswith(('http','#','mailto','sms','tel')): return m.group(0)
        if href in ('','./'): return 'href="index.html"'
        if href=='../': return 'href="../index.html"'
        base,sep,tail=href.partition('?')
        a,h,frag=base.partition('#')
        if a.endswith('/'): a+='index.html'
        return 'href="'+a+(h+frag if h else '')+(sep+tail if sep else '')+'"'
    html=_re.sub(r'href="([^"]*)"',fix,html)
    if key=='index':
        html=html.split('<body>\n',1)[1] if '<body>\n' in html else html
        html=html.replace('</body>\n</html>\n','')
        headpart=_re.search(r'<title>.*?</title>',html,_re.S)
        html='<meta name="claude:viewport-fit-sides" content="cover">\n<script>document.documentElement.setAttribute("data-rel","");document.documentElement.setAttribute("data-preview","")</script>\n'+html
    return html

def preview_head_inline(html):
    # 미리보기 index: 아티팩트 스켈레톤이 head/body를 감싸므로 head 안 내용만 본문 앞에 둠
    html=html[html.index('<head>'):]
    m=_re.search(r'<head>\n(.*?)</head>\n<body>\n',html,_re.S)
    if not m: return html
    headinner=m.group(1).replace('<meta charset="utf-8">\n','').replace('<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n','')
    body=html[m.end():].replace('</body>\n</html>\n','')
    return headinner+body


# ---------------- 와인 목록 (2026-11-23 도하: 판매 중·판매했던 와인 전부, 검색, 가격은 문의) ----------------
# 목록은 tools/wines.json 한 곳에서 고쳐요. now=true 면 '지금 매장에', order=true 면 '주문 가능'(수입사 주문), 아니면 '재입고 문의'. 가격 칸은 일부러 없어요.
STYLE_ORDER=['레드','화이트','로제','스파클링','스위트','포트·셰리','무알콜','기타']
def load_wines():
    fn=os.path.join(HERE,'wines.json')
    if not os.path.exists(fn): return []
    W=json.load(open(fn,encoding='utf-8'))['wines']
    W.sort(key=lambda w:(not w['now'],not w.get('order'),not w.get('img'),STYLE_ORDER.index(w['style']) if w['style'] in STYLE_ORDER else 99,w['ko']))
    return W
def wine_card(rel,w):
    where=' '.join(x for x in (w['country'],w['region']) if x)
    meta=' · '.join(x for x in (w['vintage'],where,w['grape']) if x)
    hay=' '.join([w['ko'],w['en'],w['vintage'],w['country'],w['region'],w['grape'],w['style']]).lower()
    status=('<span class="wbadge now">지금 매장에</span>' if w['now'] else '<span class="wbadge order">주문 가능</span>' if w.get('order') else '<span class="wbadge">재입고 문의</span>')
    purl=w.get('post') or ''
    post=(f'<a class="textlink" href="{purl}" target="_blank" rel="noopener">소개 글 →</a>' if purl.startswith('http')
          else f'<a class="textlink" href="{rel}{purl}">소개 글 →</a>' if purl else '')
    pic=(f'<div class="wimg"><img src="{rel}{w["img"]}" alt="{esc(w["ko"])} 바틀" loading="lazy" width="300" height="480"></div>' if w.get('img')
         else f'<div class="wimg none" aria-hidden="true">{HEART_SVG}</div>')
    return (f'<li class="wine" data-style="{esc(w["style"])}" data-country="{esc(w["country"])}" data-now="{1 if w["now"] else 0}"'+(f' data-tags="{esc(w["tags"])}"' if w.get('tags') else '')+(f' data-push="{w["push"]}"' if w.get('push') else '')+f' data-q="{esc(hay)}">'
            f'<div class="wpicwrap">{pic}'+(f'<button class="wsave" type="button" data-save="{wine_key(w["ko"])}" aria-pressed="false" aria-label="찜하기"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20.5s-7.5-4.6-7.5-10.2A4.3 4.3 0 0 1 12 7.6a4.3 4.3 0 0 1 7.5 2.7c0 5.6-7.5 10.2-7.5 10.2z"/></svg></button>' if MEMBERS_OPEN else '')+'</div>'+f'<div class="wbody"><div class="wtop"><span class="wstyle">{esc(w["style"])}</span>{status}</div>'+
            (f'<h3><a href="{rel}{wine_path(w)}">{esc(w["ko"])}</a></h3>' if w.get('price') else f'<h3>{esc(w["ko"])}</h3>')+(f'<p class="wen" lang="en">{esc(w["en"])}</p>' if w['en'] else '')+
            (f'<p class="wmeta">{esc(meta)}</p>' if meta else '')+
            (f'<div class="wsocial" data-stats="{wine_key(w["ko"])}" hidden></div>' if MEMBERS_OPEN else '')+
            (price_html(w,link=rel+wine_path(w)) if w.get('price') else '')+
            f'<div class="wacts"><a class="btn line sm" href="#contact" data-contact data-wine="{esc(w["ko"])}" data-ask="{wine_key(w["ko"])}">{"주문 문의" if w.get("price") else "가격 문의"}</a>{post}</div></div></li>')
# ── 가격 공개 와인 개별 페이지 (2026-11-24 도하: 1개월 내 받은 단가 + 데일리샷 최저가 비교, 마진 30% 이상만) ──
def wine_slug(w):
    import unicodedata
    en=unicodedata.normalize('NFKD',w.get('en') or '').encode('ascii','ignore').decode()
    base=_re.sub(r'[^a-z0-9]+','-',en.lower().replace("'",'')).strip('-')
    if w.get('vintage') and w['vintage'] not in base: base=(base+'-'+w['vintage']).strip('-')
    return base or 'w'+_hl.md5(w['ko'].encode()).hexdigest()[:8]
def wine_path(w): return 'wines/'+wine_slug(w)+'/'
def price_html(w,cls='wprice',link=None):
    """가격 표시: 최대 정가 대비 할인율(2026-11-24 도하: 가격 노출 땐 항상 최대 정가 대비 할인율)."""
    p=w['price']; lp=w.get('list_price') or 0
    inner=f'{p:,}원'
    if lp>p:
        pct=int((lp-p)*100/lp)
        inner=f'<s class="wlist">정가 {lp:,}원</s> <b class="woff">{pct}%</b> {p:,}원'
    if link: inner=f'<a href="{link}">{inner}</a>'
    return f'<p class="{cls}">{inner}</p>'

def price_date():
    fn=os.path.join(HERE,'wines.json')
    d=json.load(open(fn,encoding='utf-8')).get('price_date')
    return datetime.date.fromisoformat(d) if d else datetime.date.today()
def ld_wine(w):
    url=BASE+'/'+wine_path(w)
    img=BASE+'/'+w['img'] if w.get('img') else BASE+'/assets/og.png'
    valid=(price_date()+datetime.timedelta(days=30)).isoformat()
    prod={"@context":"https://schema.org","@type":"Product","@id":url+'#product',"name":w['ko'],"alternateName":w.get('en') or None,"url":url,"image":[img],"category":"와인",
          "description":wine_desc(w),"brand":None,
          "offers":{"@type":"Offer","url":url,"price":w['price'],"priceCurrency":"KRW","priceValidUntil":valid,
                    "availability":"https://schema.org/InStock" if w['now'] else "https://schema.org/BackOrder","itemCondition":"https://schema.org/NewCondition",
                    "seller":{"@id":ORG_ID},"availableAtOrFrom":{"@id":ORG_ID},"areaServed":{"@type":"City","name":"서울"}}}
    prod={k:v for k,v in prod.items() if v is not None}
    return [prod,ld_breadcrumb([('홈',BASE+'/'),('와인 목록',BASE+'/wines/'),(w['ko'],url)])]
def wine_desc(w):
    where=' '.join(x for x in (w['country'],w['region']) if x)
    bits=[x for x in (where,w.get('grape'),w.get('style')) if x]
    st='성수동 땡큐와인 매장에 있어요' if w['now'] else '주문하면 받아 드려요'
    return f"{w['ko']}{' '+w['vintage'] if w.get('vintage') and w['vintage'] not in w['ko'] else ''}" + (f" ({', '.join(bits)})" if bits else '') + (f". 정가 {w['list_price']:,}원에서 {int((w['list_price']-w['price'])*100/w['list_price'])}% 할인된 땡큐와인 가격 {w['price']:,}원, {st}." if (w.get('list_price') or 0)>w['price'] else f". 땡큐와인 가격 {w['price']:,}원, {st}.")
def page_wine(rel,w):
    where=' '.join(x for x in (w['country'],w['region']) if x)
    rows=''.join(f'<tr><th>{k}</th><td>{esc(v)}</td></tr>' for k,v in (('빈티지',w.get('vintage')),('나라·지역',where),('품종',w.get('grape')),('스타일',w.get('style'))) if v)
    purl=w.get('post') or ''
    post=(f'<a class="textlink" href="{purl}" target="_blank" rel="noopener">소개 글 →</a>' if purl.startswith('http') else f'<a class="textlink" href="{rel}{purl}">소개 글 →</a>' if purl else '')
    pic=(f'<div class="wimg big"><img src="{rel}{w["img"]}" alt="{esc(w["ko"])} 바틀" width="300" height="480"></div>' if w.get('img') else f'<div class="wimg big none" aria-hidden="true">{HEART_SVG}</div>')
    st='<span class="wbadge now">지금 매장에</span>' if w['now'] else '<span class="wbadge order">주문 가능</span>'
    return f"""
<section class="sec tight" id="wine">
  <div class="wrap">
    <p class="crumb"><a href="{rel}wines/">와인 목록</a> › {esc(w['ko'])}</p>
    <div class="wdetail">{pic}
      <div class="wbody">
        <div class="wtop"><span class="wstyle">{esc(w['style'])}</span>{st}</div>
        <h1>{esc(w['ko'])}</h1>{f'<p class="wen" lang="en">{esc(w["en"])}</p>' if w.get('en') else ''}
        {f'<div class="wsocial big" data-stats="{wine_key(w["ko"])}" hidden></div>' if MEMBERS_OPEN else ''}
        {price_html(w,cls='wprice big')}
        <table class="wfacts">{rows}</table>
        <p>{esc(wine_desc(w))} 매장에서 바로 사거나, 카톡·문자로 이름만 보내 주시면 준비해 둘게요. 6병 이상이면 서울 퀵 배송비가 무료예요.</p>
        <div class="wacts"><a class="btn sm" href="#contact" data-contact data-wine="{esc(w['ko'])}" data-ask="{wine_key(w['ko'])}">주문 문의</a>{(f'<button class="wsave inline" type="button" data-save="{wine_key(w["ko"])}" aria-pressed="false" aria-label="찜하기"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20.5s-7.5-4.6-7.5-10.2A4.3 4.3 0 0 1 12 7.6a4.3 4.3 0 0 1 7.5 2.7c0 5.6-7.5 10.2-7.5 10.2z"/></svg><span data-save-label>찜하기</span></button>' if MEMBERS_OPEN else '')}{post}</div>
        <p class="savenote" data-save-note hidden></p>
        <p class="note">가격은 {price_date().month}월 {price_date().day}일 기준이에요. 수입사 가격이 바뀌면 달라질 수 있어요.</p>
      </div>
    </div>
  </div>
</section>"""
def page_wines(rel):
    W=WINES
    styles=[s for s in STYLE_ORDER if any(w['style']==s for w in W)]
    countries=sorted({w['country'] for w in W if w['country']},key=lambda c:-sum(1 for w in W if w['country']==c))
    chips=''.join(f'<button class="chip" type="button" data-style="{esc(s)}" aria-pressed="false">{esc(s)}</button>' for s in styles)
    opts=''.join(f'<option value="{esc(c)}">{esc(c)}</option>' for c in countries)
    now_n=sum(1 for w in W if w['now'])
    return f"""
<section class="sec tight" id="wines">
  <div class="wrap wide">
    <div class="head">
      <span class="kicker">와인 목록</span>
      <h1>땡큐와인이 소개하고 판매한 와인</h1>
      <p>지금 매장에 있는 와인 {now_n}종, 주문해서 받아 드릴 수 있는 와인 {sum(1 for w in W if w.get('order') and not w['now'])}종, 지금까지 소개하고 판매한 와인까지 모두 {len(W)}종이에요. 최근 수입사에서 받은 가격이 확실한 와인은 가격을 적어 두었고, 나머지는 입고 시기에 따라 자주 바뀌어서 <b>가격 문의</b>로 남겨 두었어요. 카톡이나 문자로 이름만 보내 주세요. 다 나간 와인도 다시 구해 드릴 수 있는지 알아봐 드려요.</p>
    </div>
    <div class="wpick" id="wpick">
      <h2>뭘 골라야 할지 모르겠다면</h2>
      <p class="wpicklead">세 가지만 눌러 주세요. 지금 매장에 있는 와인 중에서 세 병을 골라 드려요.</p>
      <div class="pq" data-q="occ"><b>어떤 자리예요?</b><div class="chips"><button class="chip" type="button" data-v="G" aria-pressed="false">선물</button><button class="chip" type="button" data-v="P" aria-pressed="false">여럿이 모임·건배</button><button class="chip" type="button" data-v="H" aria-pressed="false">집에서 편하게</button><button class="chip" type="button" data-v="N" aria-pressed="false">술을 안 드시는 분</button></div></div>
      <div class="pq" data-q="food"><b>무엇과 함께 드세요?</b><div class="chips"><button class="chip" type="button" data-v="M" aria-pressed="false">고기</button><button class="chip" type="button" data-v="S" aria-pressed="false">회·해산물</button><button class="chip" type="button" data-v="K" aria-pressed="false">한식·매운 음식</button><button class="chip" type="button" data-v="C" aria-pressed="false">치즈·가벼운 안주</button><button class="chip" type="button" data-v="D" aria-pressed="false">디저트</button><button class="chip" type="button" data-v="" aria-pressed="false">와인만</button></div></div>
      <div class="pq" data-q="taste"><b>어떤 맛이 좋으세요?</b><div class="chips"><button class="chip" type="button" data-v="l" aria-pressed="false">가볍고 산뜻하게</button><button class="chip" type="button" data-v="m" aria-pressed="false">적당히</button><button class="chip" type="button" data-v="f" aria-pressed="false">진하고 묵직하게</button><button class="chip" type="button" data-v="s" aria-pressed="false">달콤하게</button><button class="chip" type="button" data-v="" aria-pressed="false">잘 모르겠어요</button></div></div>
      <div class="wpickgo"><button class="btn wine" type="button" id="wpickbtn">추천 받기</button><span class="wpickmsg" id="wpickmsg" aria-live="polite"></span></div>
      <div id="wpickout" hidden>
        <ul class="wines wpickres" id="wpickres"></ul>
        <p class="wpicknote">맛과 음식 궁합을 기준으로 고른 참고용 추천이에요. 예산이나 받는 분 취향을 알려 주시면 더 잘 맞춰 드려요. <button class="textlink" type="button" id="wpickagain">다시 고르기</button></p>
      </div>
    </div>
    <div class="wfind" role="search">
      <label class="wsearch"><span class="sr">와인 검색</span><input id="wq" type="search" placeholder="와인 이름, 품종, 지역으로 찾기 (예: 피노 누아, 보르도, Chablis)" autocomplete="off"></label>
      <div class="wsel">
        <label><span class="sr">나라</span><select id="wcountry"><option value="">모든 나라</option>{opts}</select></label>
        <label class="wnow"><input id="wnow" type="checkbox"> 지금 매장에 있는 와인만</label>
      </div>
      <div class="chips" id="wchips" role="group" aria-label="스타일"><button class="chip" type="button" data-style="" aria-pressed="true">전체</button>{chips}</div>
      <p class="wcount" id="wcount" aria-live="polite">{len(W)}종</p>
    </div>
    {'<p class="savenote" data-save-note hidden></p>' if MEMBERS_OPEN else ''}
    <ul class="wines" id="wlist">{''.join(wine_card(rel,w) for w in W)}</ul>
    <p class="wempty" id="wempty" hidden>찾는 와인이 목록에 없어도 구해 드릴 수 있어요. <a class="textlink" href="#contact" data-contact>카톡으로 물어보기 →</a></p>
    <p class="muted small" style="margin-top:28px">'지금 매장에'는 매장 재고 기준이라 그사이 다 나갔을 수 있어요. 가져가시기 전에 카톡으로 한 번 확인해 주세요.</p>
  </div>
</section>"""


# ---------------- 회원: 로그인 · 내 와인 · 관리자 연결 (2026-11-24 도하: 산 와인 모아 보기, 산 와인에만 별점·메모) ----------------
# 회원은 코르크매치·비노나루와 같은 Supabase(카카오·구글). 구매 내역은 장부에서 관리자가 '연결'한 회원 것만 올라가요. 가격은 어디에도 없어요.
import hashlib as _hashlib
def wine_key(ko): return 'w'+_hashlib.md5(ko.encode('utf-8')).hexdigest()[:10]   # tools/ledger_export.py 와 같은 규칙
def wine_index_json():
    idx={wine_key(w['ko']):{k:v for k,v in (('k',w['ko']),('i',w.get('img','')),('s',w['style']),('c',w['country']),('p',w.get('post',''))) if v} for w in WINES}
    return json.dumps(idx,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
KAKAO_BTN='<button class="btn social kakao" type="button" data-login-provider="kakao">카카오로 시작하기</button>'
GOOGLE_BTN='<button class="btn social google" type="button" data-login-provider="google">구글로 시작하기</button>'
def page_login(rel):
    return f"""
<section class="sec tight">
  <div class="wrap narrow" data-login-page>
    <span class="kicker">내 와인</span>
    <h1>산 와인을 모아 보고<br>별점을 남겨 보세요</h1>
    <p class="lead2">땡큐와인에서 산 와인이 한곳에 모이고, 마셔 본 와인에 별점과 한 줄 메모를 남길 수 있어요. 다음에 무엇을 고를지, 지난번 그 와인이 뭐였는지 바로 찾을 수 있어요.</p>
    <ul class="checks one" style="margin:18px 0 24px">
      <li>매장에서 산 와인이 자동으로 모여요 (따로 입력할 것 없어요)</li>
      <li>찜한 와인을 휴대폰·컴퓨터 어디서든 모아 볼 수 있어요</li>
      <li>선불권이 있으면 남은 금액과 사용 내역도 볼 수 있어요</li>
      <li>별점·메모는 직접 산 와인에만 남길 수 있고, 나만 봐요</li>
      <li>가입비 없고, 언제든 탈퇴할 수 있어요</li>
    </ul>
    <div class="consentbox">
      <label class="check all"><input type="checkbox" data-agree-all><span><b>모두 동의해요</b></span></label>
      <label class="check"><input type="checkbox" data-agree="age" required><span>[필수] 만 19세 이상이에요.</span></label>
      <label class="check"><input type="checkbox" data-agree="privacy" required><span>[필수] 개인정보 수집·이용에 동의해요. <a class="textlink" href="{rel}privacy/#member" target="_blank" rel="noopener">내용 보기</a></span></label>
      <p class="muted small">수집: 이름, 이메일(카카오·구글 계정), 휴대폰 번호, 매장 구매 기록(와인 이름·날짜), 선불권 내역(있는 경우), 별점·메모 · 목적: 산 와인 모아 보기와 기록 · 보유: 탈퇴할 때까지</p>
    </div>
    <div class="socials">{KAKAO_BTN}{GOOGLE_BTN}</div>
    <p class="muted small" data-login-hint>필수 항목에 동의하면 버튼이 눌려요.</p>
    <p class="soon">회원 기능은 곧 열려요. 그동안 산 와인이 궁금하시면 카톡으로 물어봐 주세요.</p>
  </div>
</section>"""
def page_me(rel):
    return f"""
<section class="sec tight">
  <div class="wrap" data-me-page>
    <div data-me-out hidden>
      <span class="kicker">내 와인</span>
      <h1>로그인하면 산 와인이 모여요</h1>
      <p class="lead2">땡큐와인에서 산 와인을 한곳에서 보고, 마셔 본 와인에 별점과 한 줄 메모를 남겨 보세요.</p>
      <div class="ctas"><a class="btn wine" href="{rel}login/">로그인 · 가입</a><a class="btn line" href="{rel}wines/">와인 목록 보기</a></div>
    </div>
    <div data-me-in hidden>
      <p class="welcome" data-me-welcome hidden>가입을 마쳤어요. 반가워요!</p>
      <span class="kicker">내 와인</span>
      <h1 data-me-hello>내 와인</h1>
      <p class="muted small" data-me-sub></p>
      <div class="mewait" data-me-wait hidden>
        <b>매장 구매 기록과 연결하는 중이에요</b>
        <p data-me-wait-msg></p>
      </div>
      <div class="prepaid" data-me-prepaid hidden>
        <div class="pphead"><span>선불권 잔액</span><b data-pp-bal></b></div>
        <details><summary>충전·사용 내역</summary><ul class="pplist" data-pp-list></ul></details>
        <p class="muted small">매장 장부 기준이에요. 다르게 보이면 카톡으로 알려 주세요.</p>
      </div>
      <div data-me-wines hidden>
        <div class="metabs"><p class="mesum" data-me-sum></p>
          <div class="chips" data-me-tabs role="group" aria-label="보기"><button class="chip" type="button" data-tab="all" aria-pressed="true">전체 <span></span></button><button class="chip" type="button" data-tab="todo" aria-pressed="false">별점 남길 와인 <span></span></button><button class="chip" type="button" data-tab="done" aria-pressed="false">별점 남긴 와인 <span></span></button></div>
        </div>
        <ul class="wines mywines" data-me-list></ul>
        <p class="muted small" style="margin-top:20px">별점과 메모는 나만 봐요. 같은 별을 한 번 더 누르면 지워져요. 목록에 없는 구매가 있으면 카톡으로 알려 주세요.</p>
      </div>
      <div class="mesaved" data-me-saved-box>
        <h2>찜한 와인</h2>
        <ul class="wines mywines" data-me-saved></ul>
      </div>
      <form class="formbox meform" data-me-form novalidate>
        <h2>내 정보</h2>
        <div class="consentbox" data-me-consent hidden>
          <label class="check"><input type="checkbox" name="age"><span>[필수] 만 19세 이상이에요.</span></label>
          <label class="check"><input type="checkbox" name="privacy"><span>[필수] 개인정보 수집·이용에 동의해요. <a class="textlink" href="{rel}privacy/#member" target="_blank" rel="noopener">내용 보기</a></span></label>
        </div>
        <div class="row"><label>이름<input name="name" maxlength="50" autocomplete="name"></label>
          <label>휴대폰 번호<input name="phone" inputmode="tel" maxlength="20" placeholder="010-0000-0000" autocomplete="tel"></label></div>
        <p class="muted small">매장에서 구매할 때 쓰신 번호를 남겨 주세요. 이 번호로 구매 기록을 찾아 연결해 드려요.</p>
        <div class="ctas" style="margin-top:12px"><button class="btn wine" type="submit">저장</button><span class="muted small" data-me-msg aria-live="polite"></span></div>
        <p class="meout"><button class="textlink" type="button" data-logout>로그아웃</button> · <button class="textlink" type="button" data-me-delete>회원 탈퇴</button></p>
      </form>
    </div>
  </div>
  <script type="application/json" id="wine-index">{wine_index_json()}</script>
</section>"""
def page_admin(rel):
    return f"""
<section class="sec tight">
  <div class="wrap" data-admin-page>
    <span class="kicker">관리자</span>
    <h1>회원 연결 · 구매 내역 반영</h1>
    <div class="adminlogin" data-admin-login><span class="muted small" data-admin-who></span>{KAKAO_BTN}{GOOGLE_BTN}</div>
    <div data-admin-bar hidden>
      <div class="formbox">
        <h2>1. 장부 파일 열기</h2>
        <p class="muted small">비서실에 '땡큐와인 회원 장부 파일 만들어 줘'라고 하면 만들어 드려요. 파일은 이 브라우저 안에서만 읽고, 연결한 회원의 구매 줄(와인 이름·날짜·병 수)과 그 회원의 선불권 내역만 올라가요. 와인 가격은 올라가지 않아요.</p>
        <input type="file" accept=".json,application/json" data-admin-file>
        <p class="small" data-admin-file-msg></p>
        <div class="ctas"><button class="btn line sm" type="button" data-admin-sync>연결된 회원 구매 내역 새로 반영</button><button class="btn line sm" type="button" data-admin-reload>새로고침</button></div>
      </div>
      <p class="adminstat" data-admin-status aria-live="polite"></p>
      <h2>2. 연결 기다리는 회원</h2>
      <p class="muted small">회원이 남긴 번호와 장부 번호가 같으면 미리 골라 둬요. 본인이 맞는지 보고 '연결'을 눌러 주세요.</p>
      <div data-admin-pending></div>
      <h2 style="margin-top:32px">연결된 회원</h2>
      <div data-admin-linked></div>
    </div>
  </div>
</section>"""

BUILDERS={'login':page_login,'me':page_me,'admin':page_admin,'index':page_index,'wines':page_wines,'gathering':page_gathering,'gift':page_gift,'shop':page_shop,'about':page_about,'blog':page_blog,'faq':page_faq,'occasions':page_occasions,'privacy':page_privacy,'404':page_404}

PREVIEW=False
AI_BOTS=['GPTBot','OAI-SearchBot','ChatGPT-User','ClaudeBot','Claude-SearchBot','Claude-User','anthropic-ai','Google-Extended','Googlebot','Bingbot','PerplexityBot','Perplexity-User','Yeti','Applebot','Applebot-Extended','DuckAssistBot','meta-externalagent','Amazonbot','CCBot']
def write_text(path,text):
    text=text.replace('http://www.instagram.com','https://www.instagram.com')
    os.makedirs(os.path.dirname(path),exist_ok=True)
    with open(path,'w',encoding='utf-8') as f: f.write(text)
def indexnow_key():
    fn=os.path.join(HERE,'indexnow_key.txt')
    if not os.path.exists(fn):
        import secrets; write_text(fn,secrets.token_hex(16))
    return open(fn,encoding='utf-8').read().strip()
def rfc822(iso):
    return datetime.datetime.strptime(iso,'%Y-%m-%d').replace(hour=9).strftime('%a, %d %b %Y %H:%M:%S +0900')

def write_extras():
    pages=[(BASE+'/'+p['path'],TODAY.isoformat()) for k,p in PAGES.items() if p['path']!='404.html' and k not in MEMBER_PAGES]
    posts=[(BASE+'/'+p['path'],p['date']) for p in POSTS]
    posts+=[(BASE+'/'+wine_path(w),price_date().isoformat()) for w in WINES if w.get('price')]
    sm='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join(f'  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>\n' for u,d in pages+posts)+'</urlset>\n'
    write_text(os.path.join(ROOT,'sitemap.xml'),sm)
    NO='Disallow: /api/\nDisallow: /tools/\nDisallow: /docs/\nDisallow: /login/\nDisallow: /me/\nDisallow: /admin/\n'
    rb='# 땡큐와인 — 검색엔진과 AI 어시스턴트 크롤러 모두 환영해요. 가격이 확실한 와인은 와인 페이지에 적고, 나머지는 카카오톡으로 1:1 안내해요.\n\nUser-agent: *\nAllow: /\n'+NO+'\n'
    rb+=''.join(f'User-agent: {b}\nAllow: /\n'+NO+'\n' for b in AI_BOTS)
    rb+=f'Sitemap: {BASE}/sitemap.xml\n'
    write_text(os.path.join(ROOT,'robots.txt'),rb)
    key=indexnow_key(); write_text(os.path.join(ROOT,key+'.txt'),key)
    # llms.txt (llmstxt.org 형식)
    L=['# 땡큐와인 (Thank You Wine)','',
       '> 서울 성수동의 와인 토탈 서비스. 와인 컨설턴트 이도하가 모임·행사 와인과 기업·명절 선물 와인을 인원과 예산에 맞춰 골라 드리고, 와인잔 대여·와인 강의·시음회까지 해 드려요. 와인은 성수동 매장에서 구매하거나 미리 주문할 수 있고, 가격이 확실한 와인은 와인 목록에 적고, 나머지는 카카오톡으로 1:1 안내해요.','',
       '## 기본 정보','',f"- 주소: {SITE['address']}",f"- 연락: {PHONE} (문자·전화·카카오톡 친구 추가), {SITE['email']}",
       f"- 네이버 블로그: {SITE['blog']}",f"- 인스타그램: {SITE['insta']}",
       '- 운영: 상호 한낮의밤, 대표 이도하(와인 컨설턴트).',
       '- 멤버: 가입비 없음. 10만원 이상 구매하면 멤버로 등록되고 입고 소식·시음회·모임 안내를 카카오톡으로 먼저 받아요.']+[f"- 다가오는 행사: {e['title']} · {e['when']} · {e['where']} · {e['who']} · 안내와 신청: {e['url']}" for e in live_events()]+['',
       '## 주요 페이지','']
    for k,p in PAGES.items():
        if p['path'] in ('404.html','privacy/') or k in MEMBER_PAGES: continue
        L.append(f"- [{p['title'].split(' · ')[0]}]({BASE}/{p['path']}): {p['desc']}")
    L+=['','## 블로그 글 (와인 소개·와인 이야기·모임·선물)','']
    for p in POSTS: L.append(f"- [{p['title']}]({BASE}/{p['path']}): {p['summary']}")
    L+=['','## 자주 묻는 질문','']
    for q,a in FAQ_ALL: L.append(f'- {q} {a}')
    L+=['','## 모임·행사 와인 질문','']+[f'- {q} {a}' for q,a in FAQ_GATHERING]
    L+=['','## 기업·명절 선물 와인 질문','']+[f'- {q} {a}' for q,a in FAQ_GIFT]
    L+=['','## Optional','',f'- [전체 본문(llms-full.txt)]({BASE}/llms-full.txt)',f'- [RSS]({BASE}/feed.xml)',f'- [사이트맵]({BASE}/sitemap.xml)','']
    write_text(os.path.join(ROOT,'llms.txt'),'\n'.join(L))
    F=['# 땡큐와인 전체 본문','',L[2],'',f"주소 {SITE['address']} · 연락 {PHONE} · {SITE['email']} · 블로그 {SITE['blog']} · 인스타그램 {SITE['insta']}",'',
       '## 하는 일','',
       '- 모임·행사 와인: 송년회, 동호회 정모, 회사 모임, 비즈니스 모임. 인원과 예산에 맞춰 스파클링·화이트·레드를 짜고, 와인잔 대여와 행사장 배송·수거까지 준비. 1인 1병과 2인 1병, 잔 포함과 잔 미포함으로 견적을 나란히 비교.',
       '- 기업·명절 선물: 거래처 명절 선물, 임직원 선물, 감사 인사 한 병. 보르도 5대 샤토부터 데일리 와인까지 예산에 맞춰 고르고 세금계산서 발행.',
       '- 오늘 마실 한 병: 성수동 매장에서 어떤 자리인지, 무엇과 드실지 듣고 골라 드림. 매장 픽업.',
       '- 멤버 시음회·모임을 매장에서 진행(15명까지).','',
       '## 병 수 가이드','','한 병(750ml)은 5~6잔. 식사 중심이면 2~3명에 1병, 식사와 대화가 길면 2명에 1병, 와인이 주인공인 모임이면 1명에 1병.','',
       '## 가격','','가격이 확실한 와인은 와인 목록(/wines/)과 와인별 페이지에 원화 가격을 적음. 나머지는 카카오톡 1:1로 안내하고, 예산을 알려 주면 그 안에서 제안(데일리 / 모임·선물용 호텔 납품 와인 / 샴페인·부르고뉴·나파밸리 / 보르도 5대 샤토·빈티지 샴페인).','',
       '## 상황별 와인 고르기','']
    for o in OCCASIONS: F+=['### '+o['q'],'',o['a'],'']+[f'- {k}: {v}' for k,v in o['rows']]+['- 가격: 카카오톡 1:1 안내','']
    F+=['## 자주 묻는 질문','']
    for q,a in FAQ_ALL: F+=['### '+q,'',a,'']
    for q,a in FAQ_GATHERING+FAQ_GIFT: F+=['### '+q,'',a,'']
    for p in POSTS:
        F+=['','---','',f"# {p['title']}",'',f"- 주소: {BASE}/{p['path']}",f"- 날짜: {p['date']} · 분류: {p['category']} · 글쓴이: 이도하(와인 컨설턴트)",f"- 네이버 원문: {p['naver']}"]+([f"- 구매처: 서울 성수동 땡큐와인 매장(성덕정길 109 2층) 구매·카톡 주문, 가격은 카톡 1:1 안내"] if buyable(p) else [])+['',f"**한 줄 요약:** {p['summary']}",'',blocks_markdown(p),'']
    write_text(os.path.join(ROOT,'llms-full.txt'),'\n'.join(F))
    items=''.join(f'  <item>\n    <title>{esc(p["title"])}</title>\n    <link>{BASE}/{p["path"]}</link>\n    <guid isPermaLink="true">{BASE}/{p["path"]}</guid>\n    <pubDate>{rfc822(p["date"])}</pubDate>\n    <category>{esc(p["category"])}</category>\n    <description>{esc(p["summary"])}</description>\n  </item>\n' for p in POSTS)
    feed=f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n<channel>\n  <title>땡큐와인 블로그</title>\n  <link>{BASE}/blog/</link>\n  <atom:link href="{BASE}/feed.xml" rel="self" type="application/rss+xml"/>\n  <description>성수동 와인 토탈 서비스 땡큐와인의 와인 소개와 와인 이야기</description>\n  <language>ko-kr</language>\n{items}</channel>\n</rss>\n'
    write_text(os.path.join(ROOT,'feed.xml'),feed)

def build(preview=False):
    global PREVIEW, ROOT, POSTS
    PREVIEW=preview; ROOT=SITEDIR
    POSTS=load_posts()
    global WINES; WINES=load_wines()
    prepare_images(POSTS)
    write_posts_json(POSTS)
    if preview:
        ROOT=os.path.join(HERE,'preview')
        os.makedirs(ROOT,exist_ok=True)
        for d in ('assets','data'):
            dst=os.path.join(ROOT,d)
            if os.path.isdir(dst): shutil.rmtree(dst)
            shutil.copytree(os.path.join(SITEDIR,d),dst)
    def emit(out,html,key):
        if PREVIEW:
            if key=='index':
                html=preview_head_inline(html)
                html='<meta name="claude:viewport-fit-sides" content="cover">\n<script>document.documentElement.setAttribute("data-rel","");document.documentElement.setAttribute("data-preview","")</script>\n'+html
            html=_re.sub(r'href="([^"]*)"',lambda m:_fixhref(m.group(1)),html)
        os.makedirs(os.path.dirname(out),exist_ok=True)
        write_text(out,html)
    for key,p in PAGES.items():
        if p['path']=='404.html': out=os.path.join(ROOT,'404.html'); rel=''
        else: out=os.path.join(ROOT,p['path'],'index.html'); rel=rel_for(p['path'])
        cur=key if key!='index' else 'home'
        ld=ld_blog() if key=='blog' else (ld_occasions() if key=='occasions' else (None if key in MEMBER_PAGES else ld_page(key)))
        html=head(key,rel,ld=ld)+header(rel,cur)+'<main>'+BUILDERS[key](rel)+'</main>\n'+footer(rel)
        emit(out,html,key)
    for p in POSTS:
        rel='../../'; out=os.path.join(ROOT,p['path'],'index.html')
        body=page_post(rel,p)
        page=dict(path=p['path'],title=f"{p['main']} · 땡큐와인",desc=short(p['summary'],150))
        img=next((BASE+'/'+b['web'] for b in p['blocks'] if b.get('web')),None)
        html=head('post',rel,page=page,ld=ld_post(p,p.get('_faq')),og=dict(type='article',image=img,published=p['date'],modified=p['date'],section=p['category'],tags=p['tags']))+header(rel,'blog')+'<main>'+body+'</main>\n'+footer(rel)
        emit(out,html,'post')
    for w in WINES:
        if not w.get('price'): continue
        path=wine_path(w); rel=rel_for(path); out=os.path.join(ROOT,path,'index.html')
        page=dict(path=path,title=f"{w['ko']} 가격 {w['price']:,}원 · 성수 땡큐와인",desc=short(wine_desc(w),150))
        html=head('wine',rel,page=page,ld=ld_wine(w),og=dict(image=(BASE+'/'+w['img']) if w.get('img') else None))+header(rel,'wines')+'<main>'+page_wine(rel,w)+'</main>\n'+footer(rel)
        emit(out,html,'wine')
    print(f'pages {len(PAGES)} + posts {len(POSTS)} → {os.path.relpath(ROOT,SITEDIR) or "(루트)"}/')
    with open(os.path.join(ROOT,'favicon.svg'),'w',encoding='utf-8') as f:
        f.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="-16 4 182 182"><rect x="-16" y="4" width="182" height="182" rx="40" fill="#fff"/>'+HEART_PATHS+'</svg>')
    with open(os.path.join(ROOT,GOOGLE_VERIFY_FILE),'w',encoding='utf-8') as f: f.write('google-site-verification: '+GOOGLE_VERIFY_FILE)
    if not PREVIEW: write_extras()
    for w in WARNINGS: print('!!',w)

def _fixhref(href):
    if href.startswith(('http','#','mailto','sms','tel')): return f'href="{href}"'
    if href in ('','./'): return 'href="index.html"'
    if href=='../': return 'href="../index.html"'
    base,sep,tail=href.partition('?')
    a,h,frag=base.partition('#')
    if a.endswith('/'): a+='index.html'
    return 'href="'+a+(h+frag if h else '')+(sep+tail if sep else '')+'"'

if __name__=='__main__':
    import sys
    build(preview='--preview' in sys.argv)

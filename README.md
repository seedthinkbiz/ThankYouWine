# 땡큐와인 웹사이트

성수동 와인샵 **땡큐와인** 웹사이트 소스입니다. 빌드 도구 없이 정적 HTML + Vercel 서버리스 함수 두 개로 돌아갑니다.

## 구성

| 경로 | 내용 |
|---|---|
| `index.html` | 홈 (이런 자리에 · 진행 방법 · 가격대 · 블로그 최신 글 · 매장 · 멤버 · FAQ) |
| `gathering/` | 모임·행사 와인 (병 수 가이드, 구성 예시, 견적 요청 폼) |
| `gift/` | 기업·명절 선물 (선물 종류, 가격대, 선물 문의 폼) |
| `shop/` | 매장 안내 (주소·지도·멤버) |
| `about/` | 소개 (와인 컨설턴트 이도하) |
| `blog/` | 블로그 글 목록 (사이트에 올린 글 전부, 분류 필터) |
| `posts/<slug>/` | 블로그 글 본문 페이지 (한 줄 요약 · 한눈에 보기 · 본문 · 사진 · FAQ · 네이버 원문 링크) |
| `faq/` `privacy/` `404.html` | 자주 묻는 질문, 개인정보처리방침, 404 |
| `assets/site.css` `assets/site.js` `assets/img/` | 공통 스타일·스크립트, 바틀 사진·프로필·OG 이미지 |
| `api/posts.js` | 블로그 글 API (네이버 RSS → JSON, 30분 캐시) |
| `api/submit.js` | 폼 접수 API (Vercel Serverless Function) |
| `data/posts.json` | 사이트에 올린 글 목록 (build.py가 생성) |
| `robots.txt` `llms.txt` `llms-full.txt` `sitemap.xml` `feed.xml` | 검색엔진·AI 크롤러용 (build.py가 생성, 손대지 않아도 됨) |
| `<32자>.txt` | IndexNow 키 파일 (`tools/build.py`가 씀, `tools/indexnow.py`가 사용) |
| `docs/apps-script.gs` | 접수 → 구글 스프레드시트 + 메일 알림 스크립트 |
| `vercel.json` | 주소 끝 슬래시, 보안 헤더, 캐시 |
| `tools/build.py` | 사이트 생성기 (템플릿·문구·SITE 설정). 실행하면 루트에 HTML을 다시 씀 |
| `tools/scrape_naver.py` `tools/posts_raw/` `tools/posts_meta.json` | 네이버 블로그 글 긁기, 긁은 원문, 글별 주소·한 줄 요약 |
| `tools/indexnow.py` `tools/indexnow_key.txt` | 배포 후 빙·네이버에 새 주소 알리기 |
| `tools/preview/` | 아티팩트 미리보기용 출력 (git에 안 올라감) |

HTML 페이지는 `tools/build.py`(템플릿)로 만들었습니다. 블로그 글은 `tools/posts_raw/`(네이버에서 긁은 글, `tools/scrape_naver.py`)와 `tools/posts_meta.json`(글별 주소·한 줄 요약)을 읽어 `posts/` 아래에 만듭니다. **주소·영업시간·카카오톡 채널·네이버 플레이스 링크는 `tools/build.py` 맨 위 `SITE` 블록**만 고치고 저장소 루트에서 `python3 tools/build.py`를 실행하면 루트의 HTML이 다시 만들어집니다. HTML을 직접 고쳐도 되지만, 다음 빌드 때 덮어쓰이니 `build.py`를 고치는 쪽이 안전합니다.

## 사이트 원칙

- 가격은 적지 않고 가격대만 (정확한 가격은 카카오톡 1:1).
- 하는 일만 씁니다. 안 하는 일은 적지 않습니다. 배달앱(배민·쿠팡이츠) 이야기는 넣지 않습니다(2026-11-03 도하).
- 직함은 '와인 컨설턴트'.
- 흰 배경, 검정, 버건디(#7a1f33).

## 배포 (Vercel)

1. 이 저장소(GitHub `seedthinkbiz/ThankYouWine`, `main`)를 Vercel 프로젝트로 Import 합니다. (Framework Preset: Other, Build Command·Output Directory·Root Directory 모두 비움) 이후에는 `main`에 push 할 때마다 자동 배포됩니다.
2. 또는 Vercel CLI: `npx vercel --prod` 를 저장소 루트에서 실행합니다.
3. 주소가 정해지면 `tools/build.py`의 `base`를 바꾸고 다시 빌드합니다 (robots·사이트맵·llms.txt·feed.xml이 같이 바뀝니다).

## 블로그 글 올리기 (새 글을 발행했을 때)

1. 저장소 루트에서 `python3 tools/scrape_naver.py` 실행 → 네이버 블로그 발행 글 전체를 `tools/posts_raw/`에 받습니다 (이미 받은 글은 건너뜀). 네이버는 PC에서만 열리니 PC에서 실행합니다.
2. `tools/posts_meta.json`에 새 글의 logNo로 `slug`(영문 주소)와 `summary`(한 줄 요약, 답부터 쓰기)를 적습니다. 안 적으면 주소는 `n<logNo>`, 요약은 첫 문단이 됩니다.
3. `python3 tools/build.py` → `posts/<slug>/`, 블로그 목록, 홈 최신 글, 사이트맵, llms.txt, feed.xml이 다시 만들어집니다.
4. `git add -A && git commit -m "블로그 글 추가" && git push` → Vercel이 자동으로 배포합니다.
5. 배포된 뒤 `python3 tools/indexnow.py` → 빙·네이버에 새 주소를 바로 알립니다.

그 사이에는 `/api/posts`(네이버 RSS)가 아직 사이트에 없는 새 글을 블로그 목록 맨 위에 '네이버 새 글'로 끼워 넣어 줍니다.

## AI 검색·검색엔진에 잘 잡히게 해 둔 것

- 글마다 `BlogPosting`(글쓴이 이도하·와인 컨설턴트, 날짜, 사진), `BreadcrumbList`, 글 안 FAQ는 `FAQPage` 구조화 데이터. 홈은 `LiquorStore`+`WebSite`, 소개는 `Person`, FAQ 페이지는 `FAQPage`, 블로그 목록은 `Blog`.
- 글 맨 위 '한 줄 요약'과 '한눈에 보는' 표: AI가 답을 뽑아 가기 쉬운 형태.
- `robots.txt`: GPTBot·OAI-SearchBot·ClaudeBot·Claude-SearchBot·Google-Extended·PerplexityBot·Bingbot·Yeti(네이버) 등 전부 허용, `/api/`만 제외.
- `llms.txt`(사이트 안내)·`llms-full.txt`(전체 본문), `sitemap.xml`, `feed.xml`(RSS), IndexNow 키.
- 사이트 주소가 바뀌면 `build.py`의 `base`만 바꾸고 다시 빌드하면 전부 따라 바뀝니다.

## 폼 접수 연결 (한 번만)

폼은 `/api/submit` 으로 보내고, 접수 API는 환경 변수가 있을 때만 동작합니다. 없으면 사이트가 "내용 복사해서 카톡·문자로 보내기" 안내로 바뀝니다.

### 방법 A. 구글 스프레드시트 + 메일 (추천, 무료)
1. 구글 드라이브에서 새 스프레드시트를 만들고 **확장 프로그램 > Apps Script** 를 엽니다.
2. `docs/apps-script.gs` 내용을 붙여넣고, 맨 위 `NOTIFY_EMAIL` 을 알림 받을 메일로 바꿉니다.
3. **배포 > 새 배포 > 웹 앱**, 실행 사용자 '나', 액세스 '모든 사용자' 로 배포하고 웹 앱 URL을 복사합니다.
4. Vercel 프로젝트 **Settings > Environment Variables** 에 `SUBMIT_WEBHOOK_URL` = (웹 앱 URL) 을 넣고 다시 배포합니다.

접수가 오면 시트에 종류별 탭('모임·행사 와인 견적', '기업·명절 선물 문의')으로 쌓이고 메일이 옵니다.

### 방법 B. 이메일만 (Resend)
`RESEND_API_KEY` 와 `NOTIFY_EMAIL` 을 환경 변수로 넣으면 메일로만 받습니다. A와 같이 써도 됩니다.

## 로컬 확인

```
python3 -m http.server 8000   # 저장소 루트에서
```
브라우저에서 http://localhost:8000 을 엽니다. 로컬에서는 `/api/*` 가 없어 폼은 '복사해서 보내기' 안내로, 블로그 글은 `data/posts.json` 사본으로 나옵니다.

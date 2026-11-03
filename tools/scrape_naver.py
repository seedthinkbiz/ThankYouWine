# -*- coding: utf-8 -*-
"""네이버 블로그 발행 글 전체 긁기 (표준 라이브러리만 사용, Windows/맥 모두 OK)
사용: python scrape_naver.py [blogId]        기본 blogId = middaynight109 (땡큐와인)
결과: posts_raw/index.json (목록), posts_raw/<logNo>.json (글별 본문 블록), posts_raw/img/ (글당 이미지 최대 8장), posts_raw.zip
"""
import sys, os, re, json, time, html, zipfile, urllib.request, urllib.parse
from html.parser import HTMLParser
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass

BLOG = sys.argv[1] if len(sys.argv) > 1 else 'middaynight109'
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'posts_raw'); IMG = os.path.join(OUT, 'img')
os.makedirs(IMG, exist_ok=True)
MAX_IMG = 12
UA_PC = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
UA_M = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'

def get(url, ua=UA_PC, referer=None, binary=False, tries=3):
    err = None
    for i in range(tries):
        try:
            h = {'User-Agent': ua, 'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.5'}
            if referer: h['Referer'] = referer
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=40) as r:
                data = r.read()
                return data if binary else data.decode('utf-8', 'replace')
        except Exception as e:
            err = e; time.sleep(1.5 * (i + 1))
    print('  !! GET 실패', url, err)
    return None

# ---------- 1) 글 목록 ----------
def list_posts():
    posts = []; page = 1; total = None
    while True:
        u = f'https://blog.naver.com/PostTitleListAsync.naver?blogId={BLOG}&viewdate=&currentPage={page}&categoryNo=0&parentCategoryNo=&countPerPage=30'
        t = get(u, referer=f'https://blog.naver.com/{BLOG}')
        if not t: break
        j = None
        for cand in (t, t.replace("\\'", "'")):
            try: j = json.loads(cand); break
            except Exception: pass
        if j is None:
            print('목록 JSON 파싱 실패:', t[:300]); break
        pl = j.get('postList') or []
        for p in pl:
            posts.append({'logNo': str(p.get('logNo')),
                          'title': html.unescape(urllib.parse.unquote_plus(str(p.get('title', '')))),
                          'addDate': urllib.parse.unquote_plus(str(p.get('addDate', ''))),
                          'categoryNo': str(p.get('categoryNo', ''))})
        total = int(j.get('totalCount') or 0)
        print(f'목록 {page}쪽: {len(pl)}개 (누적 {len(posts)}/{total})')
        if not pl or len(posts) >= total: break
        page += 1; time.sleep(0.4)
    seen = set(); out = []
    for p in posts:
        if p['logNo'] in seen: continue
        seen.add(p['logNo']); out.append(p)
    return out

# ---------- 2) 본문 파서 (스마트에디터 ONE) ----------
class SEParser(HTMLParser):
    VOID = {'img', 'br', 'hr', 'meta', 'link', 'input', 'source', 'wbr', 'area', 'base', 'col', 'embed', 'param', 'track'}
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []; self.depth = 0; self.main = None; self.ctx = []; self.cur = None; self.bold = 0; self.link = None
    def handle_starttag(self, tag, attrs):
        a = dict(attrs); c = a.get('class') or ''
        if tag not in self.VOID: self.depth += 1
        if self.main is None:
            if 'se-main-container' in c: self.main = self.depth
            return
        if self.main == -1: return
        if 'se-section-quotation' in c: self.ctx.append((self.depth, 'quote'))
        elif 'se-section-sectionTitle' in c: self.ctx.append((self.depth, 'h2'))
        elif 'se-section-oglink' in c: self.ctx.append((self.depth, 'oglink'))
        elif 'se-section-placesMap' in c: self.ctx.append((self.depth, 'place'))
        elif 'se-section-horizontalLine' in c: self.blocks.append({'type': 'hr'})
        if tag == 'p' and 'se-text-paragraph' in c:
            kind = self.ctx[-1][1] if self.ctx else 'p'
            if kind in ('oglink', 'place'): kind = 'p'
            self.cur = {'type': kind, 'text': ''}
        elif tag == 'img':
            src = a.get('data-lazy-src') or a.get('src') or ''
            if 'se-image-resource' in c and src and not src.startswith('data:'):
                self.blocks.append({'type': 'img', 'src': src, 'alt': a.get('alt') or ''})
        elif tag == 'br' and self.cur is not None: self.cur['text'] += '\n'
        elif tag in ('b', 'strong'): self.bold += 1
        elif tag == 'a' and self.ctx and self.ctx[-1][1] == 'oglink' and a.get('href'): self.link = a.get('href')
    def handle_endtag(self, tag):
        if tag in self.VOID: return
        if self.main not in (None, -1):
            if tag == 'p' and self.cur is not None:
                t = self.cur['text'].replace('​', '').strip()
                if t: self.blocks.append({'type': self.cur['type'], 'text': t})
                self.cur = None
            if tag in ('b', 'strong'): self.bold = max(0, self.bold - 1)
            while self.ctx and self.ctx[-1][0] >= self.depth:
                popped = self.ctx.pop()
                if popped[1] == 'oglink' and self.link:
                    self.blocks.append({'type': 'link', 'href': self.link}); self.link = None
            if self.depth == self.main: self.main = -1
        self.depth -= 1
    def handle_data(self, data):
        if self.cur is not None and self.main not in (None, -1):
            d = data.replace('​', '')
            if not d: return
            self.cur['text'] += ('**' + d + '**') if self.bold and d.strip() else d

def clean_text(t):
    t = t.replace('****', '')
    t = re.sub(r'[ \t]+\n', '\n', t)
    t = re.sub(r'\n{3,}', '\n\n', t)
    return t.strip()

def parse_old(page):
    """옛 에디터(postViewArea) 대비"""
    m = re.search(r'<div[^>]+id="postViewArea"[^>]*>(.*?)<div[^>]+class="(?:post_footer|post-btn|blog_footer)', page, re.S)
    seg = m.group(1) if m else ''
    if not seg: return []
    blocks = []
    parts = re.split(r'(<img[^>]+>)', seg)
    for part in parts:
        if part.startswith('<img'):
            s = re.search(r'src="([^"]+)"', part)
            if s and not s.group(1).startswith('data:'): blocks.append({'type': 'img', 'src': html.unescape(s.group(1)), 'alt': ''})
            continue
        txt = re.sub(r'<br\s*/?>|</p>|</div>|</li>', '\n', part)
        txt = re.sub(r'<[^>]+>', '', txt)
        txt = html.unescape(txt).replace('​', '')
        for para in re.split(r'\n\s*\n', txt):
            para = para.strip()
            if para: blocks.append({'type': 'p', 'text': para})
    return blocks

def meta(page, prop):
    m = re.search(r'<meta[^>]+property="%s"[^>]+content="([^"]*)"' % re.escape(prop), page) or re.search(r'<meta[^>]+content="([^"]*)"[^>]+property="%s"' % re.escape(prop), page)
    return html.unescape(m.group(1)) if m else ''

def fetch_post(logNo):
    url = f'https://m.blog.naver.com/PostView.naver?blogId={BLOG}&logNo={logNo}'
    page = get(url, ua=UA_M, referer=f'https://m.blog.naver.com/{BLOG}')
    if not page: return None
    p = SEParser()
    try: p.feed(page)
    except Exception as e: print('  파서 오류', logNo, e)
    blocks = [b for b in p.blocks]
    if not any(b['type'] != 'img' for b in blocks):
        blocks = parse_old(page) or blocks
    for b in blocks:
        if 'text' in b: b['text'] = clean_text(b['text'])
    blocks = [b for b in blocks if b.get('type') != 'p' or b.get('text')]
    title = meta(page, 'og:title') or ''
    desc = meta(page, 'og:description') or ''
    date = ''
    for pat in (r'class="blog_date"[^>]*>\s*([^<]+?)\s*<', r'se_publishDate[^>]*>\s*([^<]+?)\s*<', r'class="date"[^>]*>\s*([^<]+?)\s*<'):
        m = re.search(pat, page)
        if m: date = html.unescape(m.group(1)).strip(); break
    cat = ''
    for pat in (r'class="blog_category"[^>]*>\s*(?:<[^>]+>\s*)*([^<]+?)\s*<', r'class="category_name"[^>]*>\s*([^<]+?)\s*<', r'categoryName["\']?\s*[:=]\s*["\']([^"\']+)'):
        m = re.search(pat, page)
        if m: cat = html.unescape(m.group(1)).strip(); break
    tags = re.findall(r'class="[^"]*tag_item[^"]*"[^>]*>\s*#?([^<#]+?)\s*<', page)
    return {'logNo': str(logNo), 'url': f'https://blog.naver.com/{BLOG}/{logNo}', 'title': title, 'desc': desc, 'date': date, 'category': cat,
            'tags': [t.strip() for t in tags][:20], 'blocks': blocks}

def download_images(post):
    n = 0
    for b in post['blocks']:
        if b['type'] != 'img' or n >= MAX_IMG: continue
        src = b['src']
        base = src.split('?')[0]
        u = base + '?type=w773'
        ext = os.path.splitext(urllib.parse.urlparse(base).path)[1].lower() or '.jpg'
        if ext not in ('.jpg', '.jpeg', '.png', '.gif', '.webp'): ext = '.jpg'
        fn = f"{post['logNo']}_{n+1}{ext}"
        path = os.path.join(IMG, fn)
        if not os.path.exists(path):
            data = get(u, referer='https://blog.naver.com/', binary=True) or get(src, referer='https://blog.naver.com/', binary=True)
            if not data: continue
            with open(path, 'wb') as f: f.write(data)
            time.sleep(0.15)
        b['file'] = 'img/' + fn; n += 1

def main():
    posts = list_posts()
    print('총', len(posts), '개 글')
    index = []; fails = []
    for i, p in enumerate(posts, 1):
        fn = os.path.join(OUT, p['logNo'] + '.json')
        d = json.load(open(fn, encoding='utf-8')) if os.path.exists(fn) else None
        if d and d.get('standin'): d = None   # 임시(스튜디오 원고) 파일은 다시 긁기
        if d is None:
            d = fetch_post(p['logNo'])
            if not d or not d['blocks']:
                fails.append(p['logNo']); print(f'{i}/{len(posts)} 실패', p['logNo'], p['title']); continue
            d['listTitle'] = p['title']; d['addDate'] = p['addDate']; d['categoryNo'] = p['categoryNo']
            download_images(d)
            with open(fn, 'w', encoding='utf-8') as f: json.dump(d, f, ensure_ascii=False, indent=1)
            time.sleep(0.5)
        nimg = sum(1 for b in d['blocks'] if b['type'] == 'img')
        index.append({'logNo': d['logNo'], 'title': d.get('title') or p['title'], 'date': d.get('date') or p['addDate'], 'category': d.get('category', ''), 'categoryNo': p['categoryNo'], 'blocks': len(d['blocks']), 'images': nimg})
        print(f"{i}/{len(posts)} OK {d['logNo']} {index[-1]['date']} [{index[-1]['category']}] {index[-1]['title'][:40]} ({len(d['blocks'])}블록/{nimg}장)")
    with open(os.path.join(OUT, 'index.json'), 'w', encoding='utf-8') as f:
        json.dump({'blogId': BLOG, 'count': len(index), 'fails': fails, 'posts': index}, f, ensure_ascii=False, indent=1)
    zp = os.path.join(HERE, 'posts_raw.zip')
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(OUT):
            for fn in files:
                full = os.path.join(root, fn); z.write(full, os.path.relpath(full, HERE))
    print('완료:', len(index), '개 저장, 실패', len(fails), fails, '| zip', os.path.getsize(zp) // 1024, 'KB')

if __name__ == '__main__':
    main()

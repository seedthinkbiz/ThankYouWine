# -*- coding: utf-8 -*-
"""장부 → 사이트 회원 '내 와인'용 파일 만들기 (2026-11-24)

장부(아티팩트 db)의 members·sales 를 JSON 파일로 내려받은 폴더를 읽어서,
관리자 페이지(/admin/ → '장부 파일 열기')에 넣을 파일 하나를 만들어요.

  python3 tools/ledger_export.py <내려받은 폴더> <만들 파일.json>

  <내려받은 폴더>/members/*.json, <내려받은 폴더>/sales/*.json  (ArtifactData list → out_dir 모양)

들어가는 것: 손님(장부 id·이름·휴대폰), 구매 줄(날짜·와인 이름·병 수).
빠지는 것: 가격·원가·결제·주소·메모. 와인 이름 괄호 속 메모(선물 받는 분 이름 등)도 지워요.
만든 파일에는 손님 연락처가 들어 있으니 저장소(공개)에 절대 올리지 말고 프로젝트 파일 폴더에만 두세요.
관리자 페이지는 파일을 브라우저 안에서만 읽고, '연결'한 회원의 구매 줄만 서버에 올려요.
"""
import os, sys, json, glob, re, hashlib, difflib, datetime

HERE = os.path.dirname(os.path.abspath(__file__))

# 와인이 아닌 줄(선불권·칵테일 믹스·도구·서비스 요금)은 '내 와인'에 넣지 않아요.
SKIP = re.compile(r'선불권|칵테일 ?믹스|셰이커|잔 ?대여|와인잔|퀵|배송|수거|할인|쿠폰|포장|케이스|아이스|칠링|보냉|쇼핑백')

# 표기 흔들림 맞추기 (비교용으로만 쓰고 화면엔 원래 이름을 보여요)
SAME = [('쇼비뇽', '소비뇽'), ('카베르네', '까베르네'), ('까쇼', '까베르네소비뇽'), ('카쇼', '까베르네소비뇽'), ('샤도네이', '샤르도네'),
        ('샤도네', '샤르도네'), ('브륏', '브뤼'), ('브룻', '브뤼'), ('샤르무와', '샤르무아'), ('리저르바', '리제르바'), ('리제르파', '리제르바'),
        ('그랑리저브', '그랑리제르바'), ('콜롬바드', '콜롱바르'), ('샤또', '샤토'), ('끼안티', '키안티'), ('쉬라즈', '시라즈'), ('피노누와', '피노누아'),
        ('페어히즈', '페어허즈'), ('매그넘', ''), ('선물세트', ''), ('슈퍼픽션에디션', '')]

def wine_key(ko):
    return 'w' + hashlib.md5(ko.encode('utf-8')).hexdigest()[:10]

def other_key(name):
    return 'x' + hashlib.md5(norm(name).encode('utf-8')).hexdigest()[:10]

def clean(name):
    """화면에 보일 이름: 괄호 속 메모를 지우고 공백 정리."""
    n = re.sub(r'\([^)]*\)|\[[^\]]*\]', ' ', name or '')
    return re.sub(r'\s+', ' ', n).strip(' ,·-')

def norm(name):
    n = clean(name).lower()
    n = re.sub(r'\b(19|20)\d{2}\b|\bnv\b', ' ', n)
    n = re.sub(r'[^0-9a-z가-힣]', '', n)
    for a, b in SAME: n = n.replace(a, b)
    return n

def load_wines():
    W = json.load(open(os.path.join(HERE, 'wines.json'), encoding='utf-8'))['wines']
    return [(w['ko'], norm(w['ko']), norm(w.get('en', ''))) for w in W]

def load_alias():
    fn = os.path.join(HERE, 'ledger_alias.json')
    if not os.path.exists(fn): return {}
    return {norm(k): v for k, v in json.load(open(fn, encoding='utf-8')).items() if not k.startswith('_')}

def match(name, W, alias):
    """장부 와인 이름 → 사이트 와인 목록 이름. 확실하지 않으면 None(목록에 없는 와인으로 따로 보여요)."""
    n = norm(name)
    if not n: return None
    if n in alias: return alias[n] or None
    exact = [ko for ko, k, e in W if n == k]
    if exact: return exact[0]
    inside = [ko for ko, k, e in W if len(n) >= 4 and (n in k or (len(k) >= 4 and k in n))]
    if len(inside) == 1: return inside[0]
    if len(inside) > 1:
        best = sorted(inside, key=lambda ko: -difflib.SequenceMatcher(None, n, norm(ko)).ratio())
        r0 = difflib.SequenceMatcher(None, n, norm(best[0])).ratio()
        r1 = difflib.SequenceMatcher(None, n, norm(best[1])).ratio()
        return best[0] if r0 >= 0.8 and r0 - r1 >= 0.1 else None
    best, r = None, 0
    for ko, k, e in W:
        x = difflib.SequenceMatcher(None, n, k).ratio()
        if x > r: best, r = ko, x
    return best if r >= 0.86 else None

def phone(p):
    d = re.sub(r'\D', '', p or '')
    return f'{d[:3]}-{d[3:-4]}-{d[-4:]}' if len(d) in (10, 11) else (p or '').strip()

def main(src, out):
    W, alias = load_wines(), load_alias()
    rd = lambda f: json.load(open(f, encoding='utf-8'))
    members = {os.path.basename(f)[:-5]: rd(f) for f in glob.glob(os.path.join(src, 'members', '*.json'))}
    sales = {os.path.basename(f)[:-5]: rd(f) for f in glob.glob(os.path.join(src, 'sales', '*.json'))}
    customers = [dict(ref=ref, name=(m.get('name') or '').strip(), phone=phone(m.get('phone')))
                 for ref, m in sorted(members.items(), key=lambda x: (x[1].get('name') or ''))]
    purchases, unmatched = [], {}
    for sid, s in sales.items():
        ref = s.get('memberId') or ''
        if ref not in members: continue
        if (s.get('status') or '') in ('취소', '환불'): continue
        for i, it in enumerate(s.get('items') or []):
            raw = it.get('name') or ''
            if not raw or SKIP.search(raw): continue
            qty = it.get('qty') or 0
            if qty <= 0: continue
            ko = match(raw, W, alias)
            shown = ko or clean(raw)
            if not shown: continue
            if not ko: unmatched[clean(raw)] = unmatched.get(clean(raw), 0) + 1
            purchases.append(dict(id=f'{sid}:{i}', ref=ref, date=s.get('date') or None,
                                  key=wine_key(ko) if ko else other_key(raw), wine=shown[:120], qty=int(qty)))
    purchases.sort(key=lambda p: (p['ref'], p['date'] or '', p['id']))
    doc = dict(kind='thankyouwine-ledger', made=datetime.datetime.now().isoformat(timespec='minutes'),
               note='손님 연락처가 들어 있어요. 저장소에 올리지 마세요. 가격은 들어 있지 않아요.',
               customers=customers, purchases=purchases)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    json.dump(doc, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(f'손님 {len(customers)}명 · 구매 줄 {len(purchases)}개 → {out}')
    if unmatched:
        print(f'사이트 와인 목록과 못 맞춘 이름 {len(unmatched)}개 (그대로 보여요. 맞추려면 tools/ledger_alias.json 에 "장부 이름": "목록 이름"):')
        for k, v in sorted(unmatched.items(), key=lambda x: -x[1]): print(f'  {v}  {k}')

if __name__ == '__main__':
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])

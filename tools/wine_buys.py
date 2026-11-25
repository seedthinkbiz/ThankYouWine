"""장부 판매 기록 → 와인별 '산 손님 수'·'팔린 병 수'·'다시 산 손님 있음' (tools/wine_buys.json)

  python3 tools/wine_buys.py <내려받은 장부 폴더>      (ledger_export.py 와 같은 폴더: members/, sales/)

회원이 아닌 손님(행사 주문, 엑스포 현장 판매 등)도 셉니다. 나오는 파일엔 와인 키와 숫자만 있어요
(손님 이름·번호·날짜·가격 없음). 그래서 저장소에 넣어도 돼요.
사이트 표시(2026-11-25 도하):
  - '최근 3개월간 N병 팔렸어요': 최근 90일 판매 병 수(행사·현장 판매 포함), 1병 이상이면 표시 (도하 11/25: 손님 수 표시는 뺌)
  - '많이 팔린 와인': 최근 90일 판매 병 수 상위 10개(12병 이상) (도하 11/25)
  - '다시 찾는 와인': 같은 손님이 다른 날 또 산 와인
"""
import sys, os, json, glob, re, collections, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ledger_export import SKIP, load_wines, load_alias, match, wine_key

DROP = ('취소', '환불', '견적 발송 대기')
def buyer(sid, s):
    if s.get('memberId'): return 'm:' + s['memberId']
    g = re.split(r'[—(]', s.get('guestName') or '')[0].strip()
    if not g or '현장' in (s.get('guestName') or '') or '손님' in g: return 's:' + sid   # 이름 없는 손님은 판매마다 다른 사람
    return 'g:' + re.sub(r'\s+', '', g)

def main(src):
    W, alias = load_wines(), load_alias()
    who = collections.defaultdict(lambda: collections.defaultdict(set)); bottles = collections.Counter()
    recent = collections.Counter(); since = (datetime.date.today() - datetime.timedelta(days=90)).isoformat()
    sales_of = collections.defaultdict(set)   # 도하(11/25): 판매 한 건 = 손님 한 명
    for f in glob.glob(os.path.join(src, 'sales', '*.json')):
        sid = os.path.basename(f)[:-5]; s = json.load(open(f, encoding='utf-8')); s = s.get('data', s)
        if (s.get('status') or '') in DROP: continue
        b = buyer(sid, s)
        for it in s.get('items') or []:
            raw = it.get('name') or ''; qty = it.get('qty') or 0
            if not raw or SKIP.search(raw) or qty <= 0: continue
            ko = match(raw, W, alias)
            if not ko: continue
            k = wine_key(ko); who[k][b].add(s.get('date') or sid); bottles[k] += int(qty); sales_of[k].add(sid)
            if (s.get('date') or '') >= since: recent[k] += int(qty)
    out = {}
    for k, v in who.items():
        n = len(sales_of[k]); again = any(len(d) > 1 for d in v.values()); bt = bottles[k]
        if recent[k] > 0 or again:
            out[k] = {'n': n, 'bottles': bt, 'b90': recent[k], 'again': again}
    fn = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wine_buys.json')
    json.dump({'made': datetime.date.today().isoformat(), 'wines': out}, open(fn, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
    print(f'{len(out)}종 → {fn}')

if __name__ == '__main__':
    main(sys.argv[1])

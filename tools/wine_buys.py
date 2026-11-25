"""장부 구매 기록 → 와인별 '산 손님 수'·'다시 산 손님 있음' (tools/wine_buys.json)

  python3 tools/wine_buys.py <ledger_export.py 로 만든 파일.json>

나오는 파일엔 와인 키와 숫자만 있어요(손님 이름·번호·날짜·가격 없음). 그래서 저장소에 넣어도 돼요.
사이트 표시(2026-11-25 도하):
  - '손님 N명이 샀어요': 산 손님이 3명 이상인 와인만
  - '많이 팔린 와인': 산 손님 3명 이상 중 상위 10개
  - '다시 찾는 와인': 같은 손님이 다른 날 또 산 와인
"""
import sys, json, os, collections, datetime
src = sys.argv[1]
j = json.load(open(src, encoding='utf-8'))
by = collections.defaultdict(lambda: collections.defaultdict(set))
for p in j['purchases']:
    if p.get('ref') and str(p.get('key', '')).startswith('w'):
        by[p['key']][p['ref']].add(p.get('date') or p['id'])
out = {}
for k, v in by.items():
    n = len(v); again = any(len(d) > 1 for d in v.values())
    if n >= 3 or again:
        out[k] = {'n': n, 'again': again}
fn = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wine_buys.json')
json.dump({'made': j.get('made') or datetime.date.today().isoformat(), 'wines': out}, open(fn, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
print(f'{len(out)}종 → {fn}')

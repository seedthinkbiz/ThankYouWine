"""와인 심리테스트 결과 카드 이미지 (2026-11-26 도하: 다들 캡처해서 공유하니 이미지 공유도 쉽게).
유형마다 1080x1350 PNG → assets/taste/<유형>.png. 결과 화면 '이미지로 저장·공유' 버튼과 공유 링크 미리보기(og:image)에 써요.
사용: 루트에서 python3 tools/taste_cards.py  (추천 와인·문구가 바뀌면 다시 돌린 뒤 build.py)"""
import os,sys,json,subprocess,tempfile,html
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
sys.path.insert(0,HERE)
import build as B
B.WINES=B.load_wines()
OUT=os.path.join(ROOT,'assets','taste'); os.makedirs(OUT,exist_ok=True)
e=lambda t:html.escape(str(t))
HEART=B.HEART_PATHS.replace('#7A1F33','#ffffff').replace('#7a1f33','#ffffff')
CSS='''*{box-sizing:border-box;margin:0}
body{width:1080px;height:1350px;background:#7a1f33;color:#fff;font-family:"Noto Sans KR",sans-serif;padding:70px 76px 60px;display:flex;flex-direction:column}
.top{display:flex;align-items:center;gap:16px;opacity:.95}
.top svg{width:54px;height:70px}
.top .en{font-family:"Cormorant Garamond",serif;font-weight:600;font-size:34px;letter-spacing:.16em}
.top .ko{font-size:17px;letter-spacing:.5em;opacity:.8;margin-top:2px}
.k{margin-top:52px;font-size:32px;opacity:.85}
h1{font-family:"Noto Serif KR",serif;font-weight:700;font-size:104px;line-height:1.15;margin-top:10px;letter-spacing:-.01em}
.line{font-size:40px;font-weight:700;margin-top:14px}
.desc{font-size:31px;line-height:1.6;margin-top:22px;opacity:.95}
.facts{margin-top:34px;background:rgba(255,255,255,.11);border-radius:24px;padding:26px 32px;display:grid;gap:14px}
.facts div{display:grid;grid-template-columns:190px 1fr;gap:16px;font-size:29px;line-height:1.45}
.facts dt{opacity:.75}
.facts dd{font-weight:500}
.wines{margin-top:auto;background:#fff;border-radius:28px;padding:22px 30px 18px;display:flex;align-items:flex-end;justify-content:space-around;gap:10px}
.wines img{height:250px;width:auto}
.foot{margin-top:26px;display:flex;justify-content:space-between;align-items:center;font-size:30px}
.foot b{font-weight:700}
.foot span{opacity:.85}
'''
def card(k):
    name,line,desc,wine,food,*_=B.TASTE_T[k]
    picks=[w for w in B.taste_picks(k) if w.get('img')]
    imgs=''.join(f'<img src="file://{os.path.join(ROOT,w["img"].split("?")[0])}">' for w in picks)
    rows=[('잘 맞는 와인',wine),('어울리는 음식',food),('찰떡궁합',B.TASTE_T[B.TASTE_MATE[k]][0]),('티격태격',B.TASTE_T[B.TASTE_RIVAL[k]][0])]
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600&family=Noto+Sans+KR:wght@400;500;700&family=Noto+Serif+KR:wght@700&display=swap">
<style>{CSS}</style></head><body>
<div class="top"><svg viewBox="10 8 130 172">{HEART}</svg><div><div class="en">THANK YOU WINE</div><div class="ko">땡큐와인</div></div></div>
<p class="k">나와 닮은 와인 유형은</p><h1>{e(name)}</h1><p class="line">{e(line)}</p><p class="desc">{e(desc)}</p>
<dl class="facts">{''.join(f'<div><dt>{a}</dt><dd>{e(b)}</dd></div>' for a,b in rows)}</dl>
{f'<div class="wines">{imgs}</div>' if imgs else ''}
<div class="foot"><span>나도 해 보기 · 친구와 궁합 보기</span><b>thankyouwine.com/taste</b></div>
</body></html>'''
tmp=tempfile.mkdtemp()
jobs=[]
for k in B.TASTE_ORDER:
    fn=os.path.join(tmp,k+'.html'); open(fn,'w',encoding='utf-8').write(card(k)); jobs.append([fn,os.path.join(OUT,k+'.png')])
js='''const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await (await b.newContext({viewport:{width:1080,height:1350},deviceScaleFactor:1})).newPage();
for(const [src,out] of JSON.parse(process.argv[1])){await p.goto('file://'+src,{waitUntil:'networkidle'});await p.evaluate(()=>document.fonts.ready);await p.screenshot({path:out});console.log(out)}await b.close()})()'''
subprocess.run(['node','-e',js,json.dumps(jobs)],check=True)
# PNG는 무거우니 jpg로도 (공유·미리보기용)
from PIL import Image
for _,out in jobs:
    Image.open(out).convert('RGB').save(out[:-4]+'.jpg',quality=88); os.remove(out)
print('done',OUT)

"""병 사진 → 사이트용 300x480 흰 배경 jpg + 왼쪽 위 땡큐와인 로고(도하 11/25: 에이와인처럼 로고 넣기).
사용: python3 tools/bottle_img.py <원본 이미지> "<wines.json ko 이름>" [--erase x0,y0,x1,y1]
--erase: 원본에서 지울 영역(다른 사이트 배지 등)을 흰색으로 덮음."""
import sys,json,hashlib,os
from PIL import Image,ImageChops
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
W,H=300,480
def stamp():
    lg=Image.open(os.path.join(ROOT,'assets/logo-wide.png')).convert('RGB')
    bb=ImageChops.invert(lg.convert('L')).point(lambda v:255 if v>10 else 0).getbbox()
    lg=lg.crop(bb); s=150/lg.width
    return lg.resize((150,int(lg.height*s)),Image.LANCZOS)
def make(src,ko,erase=None):
    im=Image.open(src).convert('RGBA')
    a=im.split()[3]
    if a.getextrema()[0]<255:  # 투명 배경 사진: 반투명 그림자 지움
        im.putalpha(a.point(lambda v:0 if v<200 else 255))
    bg0=Image.new('RGBA',im.size,(255,255,255,255)); bg0.alpha_composite(im); im=bg0.convert('RGB')
    if erase: im.paste((255,255,255),erase)
    # 거의 흰 배경(연회색 카드 등)은 완전 흰색으로
    m=im.convert('L').point(lambda v:255 if v>=236 else 0); im.paste((255,255,255),mask=m)
    g=ImageChops.invert(im.convert('L')).point(lambda v:255 if v>18 else 0)
    b=im.crop(g.getbbox())
    s=min(250/b.width,430/b.height); b=b.resize((max(1,int(b.width*s)),int(b.height*s)),Image.LANCZOS)
    out=Image.new('RGB',(W,H),'white'); out.paste(b,((W-b.width)//2,H-b.height-18))
    out.paste(stamp(),(10,12))
    fn='assets/wines/w'+hashlib.md5(ko.encode()).hexdigest()[:8]+'.jpg'
    out.save(os.path.join(ROOT,fn),quality=88)
    p=os.path.join(HERE,'wines.json'); w=json.load(open(p))
    hit=[x for x in w['wines'] if x['ko']==ko]
    if not hit: sys.exit('wines.json에 없는 이름: '+ko)
    hit[0]['img']=fn
    open(p,'w').write(json.dumps(w,ensure_ascii=False,indent=1)+'\n')
    print(ko,'→',fn)
if __name__=='__main__':
    a=sys.argv[1:]; er=None
    if '--erase' in a:
        i=a.index('--erase'); er=tuple(int(v) for v in a[i+1].split(',')); del a[i:i+2]
    make(a[0],a[1],er)

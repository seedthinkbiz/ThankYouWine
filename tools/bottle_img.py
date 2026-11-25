"""병 사진 → 사이트용 300x480 흰 배경 jpg + 병 아래쪽 유리 위에 땡큐와인 로고(도하 11/25: 에이와인처럼 병 위에 얹어 도용 방지).
사용: python3 tools/bottle_img.py <원본 이미지> "<wines.json ko 이름>" [--erase x0,y0,x1,y1]
--erase: 원본에서 지울 영역(다른 사이트 배지 등)을 흰색으로 덮음."""
import sys,json,hashlib,os
from PIL import Image,ImageChops
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
W,H=300,480
def stamp(w):
    """땡큐와인 로고 마스크: 하트 와인잔(꼭 들어감, 도하 11/25) 위 + THANK YOU WINE 아래, 폭 w."""
    from PIL import ImageFilter
    lg=Image.open(os.path.join(ROOT,'assets/logo-wide.png')).convert('L')
    def mask(box,boost):
        m=ImageChops.invert(lg.crop(box)).point(lambda v:min(255,v*boost))
        return m.crop(m.point(lambda v:255 if v>30 else 0).getbbox())
    heart=mask((110,80,260,260),3)
    text=mask((290,100,1100,175),3).filter(ImageFilter.MaxFilter(5))
    tw=w; text=text.resize((tw,max(1,int(text.height*tw/text.width))),Image.LANCZOS)
    hh=int(w*0.30); heart=heart.resize((max(1,int(heart.width*hh/heart.height)),hh),Image.LANCZOS)
    gap=max(2,w//40)
    m=Image.new('L',(w,hh+gap+text.height),0)
    m.paste(heart,((w-heart.width)//2,0)); m.paste(text,(0,hh+gap))
    return m
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
    s=min(250/b.width,440/b.height); b=b.resize((max(1,int(b.width*s)),int(b.height*s)),Image.LANCZOS)
    from PIL import ImageFilter
    out=Image.new('RGB',(W,H),'white'); out.paste(b,((W-b.width)//2,H-b.height-20))
    # 로고를 병 아래쪽 유리 위에 얹음(흰 글자+옅은 그림자, 밝은 병에서도 보이게)
    from PIL import ImageFilter
    bx=(W-b.width)//2; by=H-b.height-20
    m=stamp(max(70,min(int(b.width*0.74),140)))
    # 병 몸통 아래쪽(병 높이 91% 지점)에 흰 로고+어두운 테두리: 어느 병·라벨 위에서도 보이고 잘라내기 어렵게
    x=(W-m.width)//2; y=by+int(b.height*0.91)-m.height//2
    edge=m.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.8)).point(lambda v:int(v*0.7))
    out.paste((25,25,25),(x,y),edge)
    out.paste((255,255,255),(x,y),m)
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

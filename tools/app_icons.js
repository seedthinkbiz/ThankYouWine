// 땡큐와인 앱 아이콘 만들기 (하트 와인잔 마크). 저장소 루트에서: node tools/app_icons.js
// 결과: assets/app/icon-192.png · icon-512.png · maskable-512.png · apple-touch-icon.png · badge-96.png
const path=require('path');
const {chromium}=require('playwright');
const HEART=`<path d="M75 118 C 30 88 14 62 22 38 C 30 14 62 12 75 36 C 88 12 120 14 128 38 C 136 62 120 88 75 118 Z" fill="none" stroke="#7A1F33" stroke-width="7" stroke-linejoin="round"/><path d="M30 64 C 50 70 100 70 120 64 C 112 82 96 98 75 112 C 54 98 38 82 30 64 Z" fill="#7A1F33"/><line x1="75" y1="118" x2="75" y2="170" stroke="#1a1a1a" stroke-width="6"/><line x1="48" y1="174" x2="102" y2="174" stroke="#1a1a1a" stroke-width="6" stroke-linecap="round"/>`;
// 마크 중심(75,95), 높이 약 166. pad = 마크 높이가 아이콘에서 차지하는 비율
const svg=(size,ratio,{bg='#fff',mono=false}={})=>{
  const s=size*ratio/166, tx=size/2-75*s, ty=size/2-95*s;
  let g=HEART; if(mono) g=g.replace(/#7A1F33|#1a1a1a/g,'#fff');
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">${bg?`<rect width="${size}" height="${size}" fill="${bg}"/>`:''}<g transform="translate(${tx} ${ty}) scale(${s})">${g}</g></svg>`;
};
const OUT=[
  ['icon-192.png',192,.72],['icon-512.png',512,.72],['apple-touch-icon.png',180,.70],
  ['maskable-512.png',512,.56],['badge-96.png',96,.86,{bg:'',mono:true}],
];
(async()=>{
  const b=await chromium.launch(); const p=await b.newPage();
  for(const [name,size,ratio,opt] of OUT){
    await p.setViewportSize({width:size,height:size});
    await p.setContent(`<html><body style="margin:0;background:transparent">${svg(size,ratio,opt)}</body></html>`);
    await p.locator('svg').screenshot({path:path.join(__dirname,'..','assets','app',name),omitBackground:true});
    console.log(name);
  }
  await b.close();
})();

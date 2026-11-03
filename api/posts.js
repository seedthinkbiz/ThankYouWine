// 땡큐와인 블로그 최신 글 API (Vercel Serverless Function, Node 18+)
// 네이버 블로그 RSS(middaynight109)를 읽어 제목·링크·날짜·카테고리·요약을 JSON으로 돌려줍니다.
// 30분 캐시. RSS를 못 읽으면 502 → 사이트는 data/posts.json 사본을 보여줍니다.
const RSS = 'https://rss.blog.naver.com/middaynight109.xml';

const strip = (s) => String(s || '')
  .replace(/<!\[CDATA\[|\]\]>/g, '')
  .replace(/<[^>]+>/g, ' ')
  .replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
  .replace(/&quot;/g, '"').replace(/&#39;|&apos;/g, "'")
  .replace(/\s+/g, ' ').trim();
const tag = (it, k) => { const m = it.match(new RegExp('<' + k + '>([\\s\\S]*?)</' + k + '>')); return m ? strip(m[1]) : ''; };

module.exports = async (req, res) => {
  res.setHeader('cache-control', 'public, s-maxage=1800, stale-while-revalidate=86400');
  try {
    const r = await fetch(RSS, { headers: { 'user-agent': 'Mozilla/5.0 (thankyouwine.site)' } });
    if (!r.ok) throw new Error('rss-' + r.status);
    const xml = await r.text();
    const items = [...xml.matchAll(/<item>([\s\S]*?)<\/item>/g)].map((m) => m[1]);
    const posts = items.slice(0, 40).map((it) => {
      const date = tag(it, 'pubDate');
      let iso = '';
      if (date) { const d = new Date(date); if (!isNaN(d)) iso = d.toISOString().slice(0, 10); }
      return { title: tag(it, 'title'), url: tag(it, 'link'), date: iso, category: tag(it, 'category'), lead: tag(it, 'description').slice(0, 140) };
    }).filter((p) => p.title && p.url);
    if (!posts.length) throw new Error('empty');
    res.status(200).json({ ok: true, source: 'rss', posts });
  } catch (e) {
    res.status(502).json({ ok: false, reason: String((e && e.message) || e) });
  }
};

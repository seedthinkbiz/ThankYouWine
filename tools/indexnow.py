# -*- coding: utf-8 -*-
"""배포한 뒤 한 번 실행: 사이트맵의 주소 전부를 IndexNow(빙·네이버·얀덱스 공용)에 알려요.
사용: python3 tools/indexnow.py      (루트의 sitemap.xml 과 tools/indexnow_key.txt 를 읽어요)
키 파일은 build.py 가 루트에 <키>.txt 로 같이 만들어 두니, 배포된 상태여야 해요."""
import os, re, json, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
key = open(os.path.join(HERE, 'indexnow_key.txt'), encoding='utf-8').read().strip()
sm = open(os.path.join(os.path.dirname(HERE), 'sitemap.xml'), encoding='utf-8').read()
urls = re.findall(r'<loc>(.*?)</loc>', sm)
host = re.sub(r'^https?://', '', urls[0]).split('/')[0]
body = json.dumps({'host': host, 'key': key, 'keyLocation': f'https://{host}/{key}.txt', 'urlList': urls}).encode()
req = urllib.request.Request('https://api.indexnow.org/indexnow', data=body, headers={'Content-Type': 'application/json; charset=utf-8'})
with urllib.request.urlopen(req, timeout=30) as r:
    print('IndexNow 응답', r.status, '| 주소', len(urls), '개 전송 (200/202면 성공)')

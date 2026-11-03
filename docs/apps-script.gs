/**
 * 땡큐와인 접수 → 구글 스프레드시트 + 메일 알림 (Google Apps Script)
 *
 * 설치 (한 번만, 5분):
 *  1. 구글 드라이브에서 새 스프레드시트 만들기 (예: "땡큐와인 접수")
 *  2. 확장 프로그램 > Apps Script 열고, 이 파일 내용을 붙여넣기
 *  3. 아래 NOTIFY_EMAIL 을 알림 받을 주소로 바꾸기
 *  4. 배포 > 새 배포 > 유형 '웹 앱' > 실행 사용자 '나', 액세스 권한 '모든 사용자' > 배포
 *  5. 나온 웹 앱 URL 을 Vercel 프로젝트의 환경 변수 SUBMIT_WEBHOOK_URL 에 넣고 다시 배포
 *
 * 시트는 종류별로 자동 생성됩니다: '모임·행사 와인 견적', '기업·명절 선물 문의', '일반 문의'
 */
var NOTIFY_EMAIL = 'seedthink.biz@gmail.com';

function doPost(e) {
  var data = JSON.parse(e.postData.contents);
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var name = data.kindLabel || data.kind || '접수';
  var sheet = ss.getSheetByName(name) || ss.insertSheet(name);
  var fields = data.fields || {};
  var keys = Object.keys(fields);

  // 머리글: 접수시각, 상태, 필드들…, 페이지
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(['접수시각', '상태'].concat(keys, ['페이지']));
    sheet.setFrozenRows(1);
  } else {
    var header = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
    keys.forEach(function (k) { if (header.indexOf(k) < 0) { sheet.getRange(1, header.length + 1).setValue(k); header.push(k); } });
  }
  var header2 = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  var row = header2.map(function (h) {
    if (h === '접수시각') return new Date(data.receivedAt || new Date());
    if (h === '상태') return '접수';
    if (h === '페이지') return data.page || '';
    return fields[h] || '';
  });
  sheet.appendRow(row);

  var body = keys.map(function (k) { return k + ': ' + fields[k]; }).join('\n');
  MailApp.sendEmail({
    to: NOTIFY_EMAIL,
    subject: '[땡큐와인] ' + name + ' 접수',
    body: name + '\n\n' + body + '\n\n시트: ' + ss.getUrl()
  });
  return ContentService.createTextOutput(JSON.stringify({ ok: true })).setMimeType(ContentService.MimeType.JSON);
}

function doGet() {
  return ContentService.createTextOutput('thankyouwine webhook ok');
}

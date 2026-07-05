/**
 * お金のカルテ — 共通リード受信レシーバ（Google Apps Script）★全診断の共通の受け皿
 * ---------------------------------------------------------------------------
 * 役割：
 *   1) どの診断（自社株評価・家計・相続…）の相談フォームからのPOSTも受信
 *   2) Cloudflare Turnstile をサーバー側で検証（任意）＋ honeypot ＋ 送信元ホスト検査
 *   3) 1枚のスプレッドシートに「診断名」付きで1行追記（診断が増えても混ざらない）
 *   4) info@ 等へメール通知
 *
 * ★セットアップ（方法B＝スプレッドシートの中から作る／SHEET_ID不要）：
 *   1. Googleスプレッドシートを新規作成（名前は「お金のカルテ_リード」など）
 *   2. そのシートの上メニュー「拡張機能 → Apps Script」を開く
 *   3. このコードを丸ごと貼り付けて保存
 *   4. 「プロジェクトの設定 → スクリプト プロパティ」に登録：
 *        NOTIFY_TO        … 通知先メール（例 info@livmakers.co.jp）※これだけは必須
 *        ALLOWED_HOSTS    … okane-carte.jp,www.okane-carte.jp（任意・推奨）
 *        TURNSTILE_SECRET … Turnstileを使うときのみ（後日でも可）
 *      ※ SHEET_ID は不要（このシート自身に書き込む）。別シートに書きたいときだけ設定。
 *   5. 「デプロイ → 新しいデプロイ → ウェブアプリ」／実行=自分・アクセス=全員
 *   6. 発行された /exec URL を各サイトの config.json（gas.endpoint）に設定
 *
 * このスクリプトは外部の生成AI(LLM)を一切呼ばない（継続課金ゼロ）。
 */

var SHEET_NAME = 'leads';
/* 固定の主要列。診断ごとの数値は「診断サマリー」＋「詳細(JSON)」に集約するので、
   新しい診断が増えても列を増やさず同じ1枚で運用できる。 */
var HEADERS = [
  '受信日時','診断','会社名','ご担当者','メール','電話',
  '診断サマリー','ご相談内容','詳細','送信元ホスト','UA'
];
/* サマリー/詳細から除外する（＝主要列やシステム項目）キー */
var CORE_KEYS = {
  website:1, company:1, name:1, email:1, tel:1, message:1,
  formName:1, summary:1, pageHost:1, ua:1
};
CORE_KEYS['cf-turnstile-response'] = 1;

/* ===== エントリポイント ===== */
function doPost(e){
  try{
    var p = (e && e.parameter) ? e.parameter : {};
    var props = PropertiesService.getScriptProperties();

    // 1) honeypot
    if (p.website && String(p.website).trim() !== ''){
      return json_({ ok:true, skipped:'honeypot' });
    }

    // 2) 送信元ホストの許可チェック（未設定なら素通し）
    var allowed = String(props.getProperty('ALLOWED_HOSTS') || '').split(',')
      .map(function(s){ return s.trim().toLowerCase(); }).filter(String);
    var host = String(p.pageHost || '').trim().toLowerCase();
    if (allowed.length && host && allowed.indexOf(host) === -1){
      return json_({ ok:false, error:'host_not_allowed' });
    }

    // 3) Turnstile 検証（SECRET設定時のみ）
    var secret = props.getProperty('TURNSTILE_SECRET');
    if (secret){
      var token = p['cf-turnstile-response'] || '';
      if (!token || !verifyTurnstile_(secret, token)){
        return json_({ ok:false, error:'turnstile_failed' });
      }
    }

    // 4) 必須項目
    var company = clean_(p.company), name = clean_(p.name), email = clean_(p.email);
    if (!company || !name || !email){
      return json_({ ok:false, error:'missing_required' });
    }

    // 5) 診断名・サマリー・詳細（診断が増えても列を増やさず1枚に集約）
    var formName = clean_(p.formName) || '（診断名なし）';
    var summary  = clean_(p.summary);
    var extra = {};
    for (var k in p){
      if (p.hasOwnProperty(k) && !CORE_KEYS[k]){ extra[k] = clean_(p[k]); }
    }
    var detail = '';
    try{ detail = JSON.stringify(extra); }catch(e2){ detail = ''; }

    var row = [
      new Date(), formName, company, name, email, clean_(p.tel),
      summary, cleanMulti_(p.message), detail, host, clean_(p.ua)
    ];
    appendRow_(row);

    // 6) 通知
    notify_(props.getProperty('NOTIFY_TO'), formName, summary, p);

    return json_({ ok:true });
  }catch(err){
    return json_({ ok:false, error:String(err) });
  }
}

/* ヘルスチェック */
function doGet(){ return json_({ ok:true, service:'okane-carte-shared-receiver' }); }

/* ===== ヘルパ ===== */
function verifyTurnstile_(secret, token){
  try{
    var res = UrlFetchApp.fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
      method:'post', payload:{ secret:secret, response:token }, muteHttpExceptions:true
    });
    return (JSON.parse(res.getContentText() || '{}').success === true);
  }catch(e){ return false; }
}

function getSheet_(){
  var props = PropertiesService.getScriptProperties();
  var id = props.getProperty('SHEET_ID');
  // ★方法B：SHEET_ID未設定なら、このスクリプトが属するシート自身に書き込む
  var ss = id ? SpreadsheetApp.openById(id) : SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(SHEET_NAME);
  if (!sh){ sh = ss.insertSheet(SHEET_NAME); }
  if (sh.getLastRow() === 0){ sh.appendRow(HEADERS); }
  return sh;
}
function appendRow_(row){ getSheet_().appendRow(row); }

function notify_(to, formName, summary, p){
  if (!to) return;
  var subject = '【お金のカルテ】' + formName + ' リード' + (summary ? '（' + summary + '）' : '') + (p.company ? '／' + clean_(p.company) : '');
  var body = [
    formName + ' の相談フォームからリードが届きました。',
    '',
    '■ 診断サマリー：' + (summary || '—'),
    '',
    '── 連絡先 ──',
    '会社名　：' + clean_(p.company),
    'ご担当者：' + clean_(p.name),
    'メール　：' + clean_(p.email),
    '電話　　：' + (clean_(p.tel) || '—'),
    'ご相談　：' + (cleanMulti_(p.message) || '（記入なし）'),
    '',
    '送信元ホスト：' + (p.pageHost || '—')
  ].join('\n');
  try{ MailApp.sendEmail(to, subject, body); }catch(e){}
}

/* ヘッダインジェクション対策：改行・制御文字除去＋長さ制限 */
function clean_(v){ return String(v == null ? '' : v).replace(/[\r\n\t]+/g,' ').trim().slice(0, 300); }
function cleanMulti_(v){ return String(v == null ? '' : v).replace(/[\r\n]+/g,' / ').replace(/\t/g,' ').trim().slice(0, 1000); }

function json_(obj){
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

/**
 * お金のカルテ — 自社株評価診断 リード受信レシーバ (Google Apps Script)
 * ---------------------------------------------------------------------------
 * 役割：
 *   1) index.html の相談フォーム(FormData / POST)を受信
 *   2) Cloudflare Turnstile トークンをサーバー側で検証（bot/スパム除去）
 *   3) honeypot(website) と送信元ホスト(ALLOWED_HOSTS)を検査
 *   4) スプレッドシートに1行追記（連絡先＋診断で算出した概算評価額・会社規模・財務値）
 *   5) 管理者へメール通知（受け取るのは「自社株◯億円と算出済みの事業承継オーナー」）
 *
 * 秘密情報は一切コード内に書かない。すべて「スクリプトプロパティ」に隔離する。
 *   プロジェクトの設定 → スクリプト プロパティ に以下4つを登録：
 *     NOTIFY_TO        … 通知先メール（グループ共有アドレス。個人アドレス不可。例 info@example.co.jp）
 *     SHEET_ID         … 蓄積先スプレッドシートのID（URLの /d/ と /edit の間）
 *     TURNSTILE_SECRET … Cloudflare Turnstile のシークレットキー
 *     ALLOWED_HOSTS    … 送信を許可するホスト（カンマ区切り。例 okane-carte.jp,www.okane-carte.jp）
 *
 * デプロイ：「ウェブアプリ」／実行するユーザー=自分／アクセスできるユーザー=全員。
 *          発行された /exec URL を config.json の gas.endpoint に設定する。
 * このスクリプトは外部の生成AI(LLM)を一切呼ばない（継続課金ゼロ）。
 * 詳細手順は README.md を参照。
 */

var SHEET_NAME = 'leads';
var HEADERS = [
  '受信日時','会社名','ご担当者','メール','電話',
  '概算評価額(総額)','1株あたり','会社規模','斟酌率','業種',
  '配当','利益','簿価純資産','ご相談内容','送信元ホスト','UA'
];

/* ===== エントリポイント ===== */
function doPost(e){
  try{
    var p = (e && e.parameter) ? e.parameter : {};
    var props = PropertiesService.getScriptProperties();

    // 1) honeypot（不可視フィールドに値が入っていたら bot）
    if (p.website && String(p.website).trim() !== ''){
      return json_({ ok:true, skipped:'honeypot' });
    }

    // 2) 送信元ホストの許可チェック（ALLOWED_HOSTS 未設定なら素通し）
    var allowed = String(props.getProperty('ALLOWED_HOSTS') || '').split(',')
      .map(function(s){ return s.trim().toLowerCase(); }).filter(String);
    var host = String(p.pageHost || '').trim().toLowerCase();
    if (allowed.length && host && allowed.indexOf(host) === -1){
      return json_({ ok:false, error:'host_not_allowed' });
    }

    // 3) Turnstile 検証（SECRET 設定時のみ・未設定なら検証スキップ）
    var secret = props.getProperty('TURNSTILE_SECRET');
    if (secret){
      var token = p['cf-turnstile-response'] || '';
      if (!token || !verifyTurnstile_(secret, token)){
        return json_({ ok:false, error:'turnstile_failed' });
      }
    }

    // 4) 必須項目の最低限バリデーション＋ヘッダインジェクション対策
    var company = clean_(p.company), name = clean_(p.name), email = clean_(p.email);
    if (!company || !name || !email){
      return json_({ ok:false, error:'missing_required' });
    }

    // 5) スプレッドシートへ追記
    var row = [
      new Date(),
      company, name, email, clean_(p.tel),
      clean_(p.estTotal), clean_(p.estPerShare), clean_(p.companySize), clean_(p.shakushaku), clean_(p.industry),
      clean_(p.dividendMan), clean_(p.profitMan), clean_(p.netAssetMan),
      cleanMulti_(p.message), host, clean_(p.ua)
    ];
    appendRow_(row);

    // 6) 通知（全リードが「概算算出済み」の濃いリード）
    notify_(props.getProperty('NOTIFY_TO'), p);

    return json_({ ok:true });
  }catch(err){
    return json_({ ok:false, error:String(err) });
  }
}

/* ヘルスチェック（ブラウザで /exec を開いたとき用） */
function doGet(){
  return json_({ ok:true, service:'okane-carte-receiver' });
}

/* ===== ヘルパ ===== */
function verifyTurnstile_(secret, token){
  try{
    var res = UrlFetchApp.fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
      method:'post',
      payload:{ secret:secret, response:token },
      muteHttpExceptions:true
    });
    var data = JSON.parse(res.getContentText() || '{}');
    return data.success === true;
  }catch(e){ return false; }
}

function getSheet_(){
  var props = PropertiesService.getScriptProperties();
  var id = props.getProperty('SHEET_ID');
  var ss = id ? SpreadsheetApp.openById(id) : SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(SHEET_NAME);
  if (!sh){ sh = ss.insertSheet(SHEET_NAME); }
  if (sh.getLastRow() === 0){ sh.appendRow(HEADERS); }
  return sh;
}
function appendRow_(row){ getSheet_().appendRow(row); }

function notify_(to, p){
  if (!to) return;
  var subject = '【お金のカルテ】自社株評価リード（概算 ' + (p.estTotal || '—') + '）' + (p.company ? '／' + clean_(p.company) : '');
  var body = [
    '自社株評価シミュレーターから相談リードが届きました。',
    '（診断で概算評価額を算出済みの事業承継オーナーです）',
    '',
    '■ 概算評価額（総額）：' + (p.estTotal || '—'),
    '■ 1株あたり　　　　：' + (p.estPerShare || '—'),
    '■ 会社規模 / 斟酌率 ：' + (p.companySize || '—') + ' / ' + (p.shakushaku || '—'),
    '■ 業種　　　　　　　：' + (p.industry || '—'),
    '■ 配当 / 利益 / 純資産：' + (p.dividendMan||'—') + ' / ' + (p.profitMan||'—') + ' / ' + (p.netAssetMan||'—'),
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

/* ヘッダインジェクション対策：改行・制御文字を除去し長さ制限 */
function clean_(v){
  return String(v == null ? '' : v).replace(/[\r\n\t]+/g,' ').trim().slice(0, 200);
}
/* 複数行を許容する項目（相談内容）用：CR/LFのみ空白化しつつ長めに保持 */
function cleanMulti_(v){
  return String(v == null ? '' : v).replace(/[\r\n]+/g,' / ').replace(/\t/g,' ').trim().slice(0, 1000);
}

function json_(obj){
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

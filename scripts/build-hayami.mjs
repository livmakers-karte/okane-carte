#!/usr/bin/env node
/* =============================================================================
 * お金のカルテ ─ 相続税の概算早見表 pSEO ジェネレータ
 * -----------------------------------------------------------------------------
 * 実行: node scripts/build-hayami.mjs
 * 出力: okane-carte/hayami/ 配下に静的HTML一式 + sitemap-hayami.xml
 *
 * 依存ゼロ（Node.js標準ライブラリのみ・ESM）。外部API・外部CDNなし。
 *
 * 【計算ロジックの一致】
 * 本スクリプトの税額計算は okane-carte/sozoku/index.html の calc()/taxOn()/
 * heirsInfo() と完全に同じ式・同じ定数を用いる（config.json の constants を
 * そのまま踏襲）。早見表では「財産＝課税価格」とみなす単純化を行うため、
 * 生命保険の非課税枠（500万円×人数）は考慮しない（保険金という財産区分が
 * 早見表には存在しないため）。この単純化は各ページの免責欄に明記する。
 *
 * 【出典（design/tax-sources.md と同一・推測値なし）】
 *  - 基礎控除：国税庁 No.4152 https://www.nta.go.jp/taxes/shiraberu/taxanswer/sozoku/4152.htm
 *  - 相続税の速算表：国税庁 No.4155（令和7年4月1日現在法令等）
 *      https://www.nta.go.jp/taxes/shiraberu/taxanswer/sozoku/4155.htm
 *  - 生命保険金の非課税枠：国税庁 No.4114（本早見表では不使用・注記のみ）
 *      https://www.nta.go.jp/taxes/shiraberu/taxanswer/sozoku/4114.htm
 *  - 配偶者の税額軽減：国税庁 No.4158
 *      https://www.nta.go.jp/taxes/shiraberu/taxanswer/sozoku/4158.htm
 *  確認日：2026-07-07（design/tax-sources.md 参照）。
 * ========================================================================== */

import { mkdirSync, writeFileSync, rmSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const OUT_DIR = join(ROOT, 'hayami');
const SITE_ORIGIN = 'https://okane-carte.jp';
const SOURCE_NOTE_DATE = '2026-07-07';

/* ---------------------------------------------------------------------------
 * 1. 税制定数（sozoku/config.json の constants と完全一致。単位：円）
 * ------------------------------------------------------------------------- */
const CONST = {
  kisoBase: 30000000,        // 基礎控除の定額部分 3,000万円
  kisoPerHeir: 6000000,      // 基礎控除の加算 600万円 × 法定相続人の数
  spouseCreditFixed: 160000000, // 配偶者の税額軽減 定額 1億6,000万円（本早見表では「法定相続分まで軽減」の簡易モデルのため直接は未使用。出典明記のみ）
  taxTable: [
    { upTo: 10000000,  rate: 0.10, deduct: 0 },
    { upTo: 30000000,  rate: 0.15, deduct: 500000 },
    { upTo: 50000000,  rate: 0.20, deduct: 2000000 },
    { upTo: 100000000, rate: 0.30, deduct: 7000000 },
    { upTo: 200000000, rate: 0.40, deduct: 17000000 },
    { upTo: 300000000, rate: 0.45, deduct: 27000000 },
    { upTo: 600000000, rate: 0.50, deduct: 42000000 },
    { upTo: null,      rate: 0.55, deduct: 72000000 },
  ],
  sourceNote:
    '国税庁 No.4152（基礎控除・計算方法）／No.4155（速算表・令和7年4月1日現在法令等）／' +
    'No.4158（配偶者の税額軽減）。確認日 ' + SOURCE_NOTE_DATE + '。詳細は design/tax-sources.md。',
};

/* ---------------------------------------------------------------------------
 * 2. 速算表（sozoku/index.html taxOn() と同一ロジック）
 * ------------------------------------------------------------------------- */
function taxOn(yenAmt) {
  if (yenAmt <= 0) return 0;
  const t = CONST.taxTable;
  for (let i = 0; i < t.length; i++) {
    if (t[i].upTo === null || yenAmt <= t[i].upTo) {
      return yenAmt * t[i].rate - t[i].deduct;
    }
  }
  return 0;
}

/* ---------------------------------------------------------------------------
 * 3. 相続人構成の定義（早見表用に6構成を固定。sozoku heirsInfo() と同じ
 *    法定相続分ルールを、固定構成に適用する）
 * ------------------------------------------------------------------------- */
const COMPOSITIONS = [
  {
    id: 'haigusha-ko1',
    label: '配偶者＋子1人',
    shortLabel: '配偶者と子1人',
    n: 2, // 法定相続人の数
    shares: [
      { who: '配偶者', share: 0.5, spouse: true },
      { who: '子', share: 0.5 },
    ],
  },
  {
    id: 'haigusha-ko2',
    label: '配偶者＋子2人',
    shortLabel: '配偶者と子2人',
    n: 3,
    shares: [
      { who: '配偶者', share: 0.5, spouse: true },
      { who: '子', share: 0.25 },
      { who: '子', share: 0.25 },
    ],
  },
  {
    id: 'haigusha-ko3',
    label: '配偶者＋子3人',
    shortLabel: '配偶者と子3人',
    n: 4,
    shares: [
      { who: '配偶者', share: 0.5, spouse: true },
      { who: '子', share: 1 / 6 },
      { who: '子', share: 1 / 6 },
      { who: '子', share: 1 / 6 },
    ],
  },
  {
    id: 'ko2',
    label: '子のみ2人',
    shortLabel: '子2人のみ',
    n: 2,
    shares: [
      { who: '子', share: 0.5 },
      { who: '子', share: 0.5 },
    ],
  },
  {
    id: 'ko3',
    label: '子のみ3人',
    shortLabel: '子3人のみ',
    n: 3,
    shares: [
      { who: '子', share: 1 / 3 },
      { who: '子', share: 1 / 3 },
      { who: '子', share: 1 / 3 },
    ],
  },
  {
    id: 'haigusha-nomi',
    label: '配偶者のみ（子なし・親兄弟なし）',
    shortLabel: '配偶者のみ',
    n: 1,
    shares: [{ who: '配偶者', share: 1, spouse: true }],
  },
];

/* ---------------------------------------------------------------------------
 * 4. 遺産総額の刻み：3,000万〜3億円を1,000万円刻み（万円単位で保持）
 * ------------------------------------------------------------------------- */
const ASSET_STEPS_MAN = [];
for (let m = 3000; m <= 30000; m += 1000) ASSET_STEPS_MAN.push(m);
// 28通り（3000,4000,...,30000）

/* ---------------------------------------------------------------------------
 * 5. 本計算（sozoku calc() と同じ式。生命保険は早見表では非対象のため0扱い）
 *    assetMan: 遺産総額（万円） / comp: COMPOSITIONS の1要素
 * ------------------------------------------------------------------------- */
function calcHayami(assetMan, comp) {
  const assetYen = assetMan * 10000;
  const kiso = CONST.kisoBase + CONST.kisoPerHeir * comp.n;
  const netEstate = Math.max(0, assetYen - kiso); // 課税遺産総額

  let total = 0;
  const perHeir = comp.shares.map((s) => {
    const base = netEstate * s.share;
    const tax = taxOn(base);
    total += tax;
    return { ...s, base, tax };
  });
  total = Math.max(0, total);

  let spouseShare = 0;
  comp.shares.forEach((s) => { if (s.spouse) spouseShare += s.share; });
  let afterSpouse = total * (1 - spouseShare);
  if (afterSpouse < 0) afterSpouse = 0;

  return {
    assetMan, assetYen, kiso, netEstate, total, afterSpouse, spouseShare, perHeir, comp,
  };
}

/* ---------------------------------------------------------------------------
 * 6. 自己検算（要件の検算例）
 *    遺産5,000万円・配偶者+子2人
 *    → 基礎控除4,800万、課税遺産200万、
 *      配偶者100万×10%=10万 + 子50万×2×10%=10万 = 総額20万、
 *      配偶者軽減後（配偶者法定相続分1/2）= 20万×(1-1/2) = 10万
 * ------------------------------------------------------------------------- */
function runSelfCheck() {
  const comp = COMPOSITIONS.find((c) => c.id === 'haigusha-ko2');
  const r = calcHayami(5000, comp);
  const assertEq = (actual, expected, label) => {
    if (Math.round(actual) !== expected) {
      throw new Error(
        `[自己検算失敗] ${label}: expected=${expected} actual=${Math.round(actual)}`
      );
    }
  };
  assertEq(r.kiso, 48000000, '基礎控除（4,800万円）');
  assertEq(r.netEstate, 2000000, '課税遺産総額（200万円）');
  assertEq(r.total, 200000, '相続税の総額（20万円）');
  assertEq(r.afterSpouse, 100000, '配偶者軽減後（10万円）');
  return {
    assetMan: 5000,
    kiso: r.kiso / 10000,
    netEstate: r.netEstate / 10000,
    total: r.total / 10000,
    afterSpouse: r.afterSpouse / 10000,
  };
}

/* ---------------------------------------------------------------------------
 * 7. 表記ユーティリティ
 * ------------------------------------------------------------------------- */
function yen(n) { return Math.round(n).toLocaleString('ja-JP'); }
function manFromYen(y) { return Math.round(y / 10000); }
function jpMoney(y) {
  y = Math.round(y);
  if (y <= 0) return '0円';
  const oku = Math.floor(y / 100000000);
  const man = Math.floor((y % 100000000) / 10000);
  const rest = y % 10000;
  let s = '';
  if (oku) s += oku + '億';
  if (man) s += yen(man) + '万';
  if (!oku && !man) s += yen(rest);
  else if (rest) s += rest;
  return s + '円';
}
function manLabel(m) {
  // 万円単位の数値を「◯億◯,◯◯◯万円」表記に（早見表の遺産総額表示用）
  if (m >= 10000) {
    const oku = Math.floor(m / 10000);
    const rest = m % 10000;
    return rest ? `${oku}億${yen(rest)}万円` : `${oku}億円`;
  }
  return `${yen(m)}万円`;
}

/* ---------------------------------------------------------------------------
 * 8. 共通 head / header / footer パーツ
 * ------------------------------------------------------------------------- */
const CSP =
  "default-src 'self'; base-uri 'self'; object-src 'none'; img-src 'self' data:; " +
  "style-src 'self' 'unsafe-inline'; font-src 'self'; script-src 'self' 'unsafe-inline'; " +
  "frame-src 'none'; connect-src 'self'; form-action 'self'; frame-ancestors 'none';";

const FRAME_BUST_JS = `if (window.top !== window.self) { window.top.location = window.self.location; }`;

const STYLE = `
  @font-face{font-family:"Shippori Mincho";src:url("/assets/fonts/ShipporiMincho-Bold.subset.woff2") format("woff2");font-weight:700;font-display:swap}
  @font-face{font-family:"Marcellus";src:url("/assets/fonts/Marcellus-400.woff2") format("woff2");font-weight:400;font-display:swap}
  @font-face{font-family:"Cormorant";src:url("/assets/fonts/Cormorant-500.woff2") format("woff2");font-weight:500;font-display:swap}
  @font-face{font-family:"Cormorant";src:url("/assets/fonts/Cormorant-600.woff2") format("woff2");font-weight:600;font-display:swap}
  :root{
    --bg:#FAF6EE; --bg-2:#F1E8D9; --paper:#FFFDF8;
    --green:#22463C; --green-2:#5E7E6E;
    --shu:#A24B3C; --shu-2:#8B3E30;
    --gold:#C7A24E; --gold-2:#B0893A; --gold-hi:#E6D2A0; --gold-soft:#F4ECD7;
    --ink:#2C2A22; --muted:#6A6353; --line:#DDD2BE;
    --radius:14px; --radius-sm:9px;
    --shadow-card:0 10px 30px rgba(34,70,60,.08);
    --serif-jp:"Shippori Mincho","Yu Mincho","YuMincho","Hiragino Mincho ProN","Hiragino Mincho Pro",serif;
    --serif-en:"Marcellus",var(--serif-jp);
    --num:"Cormorant","Marcellus",Georgia,serif;
    --sans:system-ui,-apple-system,"Segoe UI","Hiragino Kaku Gothic ProN","Yu Gothic UI","Meiryo",sans-serif;
  }
  *{box-sizing:border-box}
  html{-webkit-text-size-adjust:100%}
  body{margin:0;font-family:var(--sans);color:var(--ink);line-height:1.8;letter-spacing:.01em;
    background:radial-gradient(1100px 520px at 86% -8%, rgba(199,162,78,.11), transparent 58%),
      radial-gradient(820px 460px at 0% 3%, rgba(34,70,60,.05), transparent 55%), var(--bg);
    min-height:100vh;display:flex;flex-direction:column}
  .wrap{max-width:880px;margin:0 auto;padding:0 22px;width:100%}
  h1,h2,h3{font-family:var(--serif-jp);color:var(--green);letter-spacing:.02em;line-height:1.5;font-weight:700}
  a{color:var(--green)}
  ::selection{background:var(--gold-soft)}
  :focus-visible{outline:2px solid var(--green);outline-offset:2px;border-radius:4px}
  header{padding:18px 0;border-bottom:1px solid var(--line)}
  header .wrap{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap}
  .brand{display:flex;align-items:center;gap:11px;color:var(--green);text-decoration:none}
  .brand .mark{font-family:var(--serif-jp);font-size:19px;letter-spacing:.06em;line-height:1.1;color:var(--green)}
  .brand .sub{font-size:11px;color:var(--muted);letter-spacing:.1em}
  .navlinks{display:flex;gap:14px;flex-wrap:wrap}
  .navlink{font-family:var(--serif-en);color:var(--green);text-decoration:none;font-size:12.5px;letter-spacing:.04em;white-space:nowrap}
  .navlink:hover{color:var(--gold-2)}
  main{flex:1}
  .crumbs{font-size:12px;color:var(--muted);margin:18px 0 6px}
  .crumbs a{color:var(--muted);text-decoration:underline;text-underline-offset:2px}
  .crumbs a:hover{color:var(--green)}
  .eyebrow{color:var(--gold-2);font-size:11.5px;letter-spacing:.16em;font-weight:700;margin:14px 0 12px;display:inline-flex;align-items:center;gap:9px}
  .eyebrow::before{content:"";width:24px;height:1px;background:linear-gradient(90deg,transparent,var(--gold))}
  h1{font-size:clamp(23px,4.6vw,34px);margin:0 0 14px}
  p.lead{color:var(--ink);font-size:clamp(14px,2.1vw,15.5px);max-width:42em;margin:0 0 18px}
  .answer{position:relative;background:var(--paper);border:1px solid var(--line);border-left:4px solid var(--gold);
    border-radius:var(--radius-sm);padding:16px 18px;margin:8px 0 22px}
  .answer .k{font-family:var(--serif-en);font-size:10.5px;letter-spacing:.14em;color:var(--gold-2);display:block;margin-bottom:5px}
  .answer p{margin:0;font-size:13.5px;color:var(--ink);line-height:1.75}
  .answer .src{display:block;margin-top:8px;font-size:11px;color:var(--muted)}
  section{padding:8px 0}
  .sec-sub{color:var(--muted);font-size:13px;margin:2px 0 16px}
  .orn{display:flex;align-items:center;gap:14px;color:var(--gold);margin:32px 0 18px}
  .orn .ln{flex:1;height:1px;background:linear-gradient(90deg,transparent,var(--gold),transparent)}
  .orn .lbl{font-family:var(--serif-en);font-size:11.5px;letter-spacing:.14em;color:var(--gold-2);white-space:nowrap}
  .card{background:var(--paper);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow-card)}
  .card-pad{padding:22px 22px 20px}
  table.hayami{width:100%;border-collapse:collapse;font-size:13.5px;margin:6px 0}
  table.hayami caption{text-align:left;font-size:12px;color:var(--muted);margin-bottom:8px}
  table.hayami th,table.hayami td{border-bottom:1px solid var(--line);padding:9px 8px;text-align:right;white-space:nowrap}
  table.hayami th:first-child,table.hayami td:first-child{text-align:left;color:var(--ink)}
  table.hayami thead th{color:var(--green);font-family:var(--serif-jp);font-weight:700;border-bottom:1px solid var(--gold-hi);background:var(--gold-soft)}
  table.hayami tbody tr:hover{background:var(--bg-2)}
  table.hayami tbody tr.hl{background:#FBF3E1}
  table.hayami tbody tr.hl td:first-child{font-weight:700;color:var(--green)}
  .num{font-family:var(--num);font-weight:600}
  .wrap-table{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:0 0 20px}
  .note-box{background:var(--gold-soft);border:1px solid var(--gold-hi);border-radius:var(--radius-sm);padding:13px 15px;font-size:12.5px;color:var(--ink);line-height:1.75;margin:16px 0}
  .note-box strong{color:var(--shu-2)}
  .explain{font-size:14px;line-height:1.85;margin:14px 0}
  .explain .stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:14px 0}
  .stat{background:var(--paper);border:1px solid var(--line);border-radius:var(--radius-sm);padding:12px 14px}
  .stat .l{font-size:11px;color:var(--muted);margin-bottom:4px}
  .stat .v{font-family:var(--num);font-weight:600;font-size:19px;color:var(--green)}
  .cta-band{display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between;
    background:linear-gradient(180deg,#2b5245,var(--green));border-radius:var(--radius);padding:22px 24px;color:#eef3ef;margin:26px 0}
  .cta-band h3{color:#fff;font-size:17px;margin:0 0 4px}
  .cta-band p{color:#cddbd3;font-size:12.5px;margin:0;max-width:36em}
  .btn{font-family:var(--sans);font-size:14.5px;font-weight:700;border:none;border-radius:var(--radius-sm);padding:12px 22px;cursor:pointer;
    transition:transform .12s,box-shadow .15s;text-decoration:none;display:inline-flex;align-items:center;justify-content:center;gap:8px;white-space:nowrap}
  .btn.gold{background:linear-gradient(120deg,var(--gold-hi),var(--gold),var(--gold-2));color:#3a2e0f}
  .btn.gold:hover{transform:translateY(-2px);box-shadow:0 8px 20px rgba(199,162,78,.32)}
  .btn.ghost{background:transparent;color:#eaf1ec;border:1px solid rgba(255,255,255,.4)}
  .btn.ghost:hover{border-color:#fff}
  .linklist{display:flex;flex-wrap:wrap;gap:8px 16px;margin:0 0 8px;font-size:13px}
  .linklist a{text-decoration:underline;text-underline-offset:2px}
  .crossgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px;margin:16px 0}
  .crosscard{display:block;background:var(--paper);border:1px solid var(--line);border-left:4px solid var(--green-2);border-radius:var(--radius-sm);
    padding:13px 15px;text-decoration:none;color:inherit;font-size:12.5px;transition:transform .12s,border-color .15s}
  .crosscard:hover{transform:translateY(-2px);border-color:var(--green)}
  .crosscard .t{font-family:var(--serif-jp);font-size:14px;color:var(--green);margin:0 0 4px}
  #faq{padding:26px 0}
  .faq details{border-bottom:1px solid var(--line)}
  .faq summary{cursor:pointer;padding:14px 26px 14px 4px;font-family:var(--serif-jp);font-size:14.5px;color:var(--green);position:relative;list-style:none}
  .faq summary::-webkit-details-marker{display:none}
  .faq summary::after{content:"＋";position:absolute;right:6px;top:13px;color:var(--gold-2);font-size:15px}
  .faq details[open] summary::after{content:"−"}
  .faq .a{padding:0 4px 16px;font-size:13px;color:var(--ink);line-height:1.85}
  .disclaimer-box{margin:18px 0;background:var(--gold-soft);border:1px solid var(--gold-hi);border-radius:var(--radius-sm);padding:14px 16px;font-size:12px;color:var(--ink);line-height:1.8}
  .disclaimer-box strong{color:var(--shu-2)}
  footer.site{position:relative;background:var(--green);color:#c9d6ce;padding:28px 0 24px;margin-top:32px;font-size:12px;line-height:1.85}
  footer.site a{color:#e6d2a0;text-decoration:none}
  footer.site a:hover{text-decoration:underline}
  .footlinks{display:flex;flex-wrap:wrap;gap:8px 18px;margin:0 0 12px;font-size:12.5px}
  .foot-discl{color:#9fb6a9;margin:6px 0 0}
  @media(max-width:640px){ table.hayami{font-size:12.5px} }
`;

function headBlock({ title, description, canonicalPath, ogType = 'article', indexable = false }) {
  const canonical = `${SITE_ORIGIN}${canonicalPath}`;
  const robots = indexable ? 'index, follow' : 'noindex, nofollow';
  return `<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta http-equiv="Content-Security-Policy" content="${CSP}">
<meta name="referrer" content="strict-origin-when-cross-origin">
<!-- 公開前は noindex。go-live 時に index, follow へ一括切替（オーケストレーター担当）。 -->
<meta name="robots" content="${robots}">
<title>${title}</title>
<meta name="description" content="${description}">
<link rel="canonical" href="${canonical}">
<meta property="og:type" content="${ogType}">
<meta property="og:site_name" content="お金のカルテ">
<meta property="og:title" content="${title}">
<meta property="og:description" content="${description}">
<meta property="og:url" content="${canonical}">
<meta property="og:image" content="${SITE_ORIGIN}/sozoku/assets/ogp.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="${title}">
<meta name="twitter:description" content="${description}">`;
}

function headerBlock() {
  return `<header>
  <div class="wrap">
    <a class="brand" href="/">
      <span><span class="mark">お金のカルテ</span><br><span class="sub">相続税の概算早見表</span></span>
    </a>
    <div class="navlinks">
      <a class="navlink" href="/sozoku/">相続税かんたん診断 →</a>
      <a class="navlink" href="/hayami/">早見表トップ</a>
    </div>
  </div>
</header>`;
}

function footerBlock() {
  return `<footer class="site">
  <div class="wrap">
    <div class="footlinks">
      <a href="/">お金のカルテ トップ</a>
      <a href="/sozoku/">相続税かんたん診断</a>
      <a href="/zoyo/">生前贈与診断</a>
      <a href="/fukuri/">複利シミュレーター</a>
      <a href="/jikabuka/">自社株評価診断</a>
      <a href="/hayami/">相続税の概算早見表</a>
    </div>
    <p class="foot-discl">本ページの数値は一般的な速算による概算の目安であり、個別の税務相談・税額計算の代行ではありません。土地建物の評価（路線価・小規模宅地等の特例）、生命保険の非課税枠、二次相続、実際の遺産分割の仕方などは反映していません。正確な税額計算・申告は税理士等の専門家にご確認ください。</p>
    <p class="foot-discl">出典：${CONST.sourceNote}</p>
    <p class="foot-discl">© <span id="year">${new Date().getFullYear()}</span> リブメーカーズ株式会社（LIVmakers Co., Ltd.）／ お金のカルテ ／ 本サイトは相続の一般的な情報提供および概算シミュレーションであり、税務・法務・投資に関する助言・代理を行うものではありません。</p>
  </div>
</footer>`;
}

function ctaBand() {
  return `<div class="cta-band">
  <div>
    <h3>あなたの財産で、正確に概算する</h3>
    <p>早見表は「区切りのよい金額」での目安です。ご自身の財産（不動産・現預金・有価証券・生命保険など）を入れて、5分・匿名・登録不要で「家族へのカルテ」を発行できます。</p>
  </div>
  <a class="btn gold" href="/sozoku/">あなたの相続税を概算する →</a>
</div>`;
}

function disclaimerBox(extra = '') {
  return `<div class="disclaimer-box">
  <strong>この早見表について：</strong> 本ページの金額は、遺産総額（課税価格）と相続人構成の代表的な組み合わせについて、
  基礎控除・相続税の速算表・配偶者の税額軽減のみを反映した<strong>簡易な概算</strong>です。
  生命保険金の非課税枠（500万円×法定相続人の数）は、早見表では財産区分を設けていないため反映していません
  （その分、実際の税額はここに示す概算より低くなる場合があります）。
  土地建物の個別評価・小規模宅地等の特例・二次相続・各種税額控除・実際の遺産分割の仕方は未反映です。
  ${extra}
  正確な相続税額の計算・申告は、必ず税理士等の専門家にご確認ください。
  出典：${CONST.sourceNote}
</div>`;
}

/* ---------------------------------------------------------------------------
 * 9. JSON-LD 生成
 * ------------------------------------------------------------------------- */
function breadcrumbLd(items) {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((it, i) => ({
      '@type': 'ListItem', position: i + 1, name: it.name, item: `${SITE_ORIGIN}${it.path}`,
    })),
  };
}
function faqLd(qas) {
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: qas.map((qa) => ({
      '@type': 'Question',
      name: qa.q,
      acceptedAnswer: { '@type': 'Answer', text: qa.a },
    })),
  };
}
function ldScript(obj) {
  return `<script type="application/ld+json">\n${JSON.stringify(obj, null, 2)}\n</script>`;
}

/* ---------------------------------------------------------------------------
 * 10. FAQ 生成（構成別・総額別で内容を変える＝固有性の担保）
 * ------------------------------------------------------------------------- */
function faqForComposition(comp) {
  const ex = calcHayami(10000, comp); // 1億円の例で具体を示す
  return [
    {
      q: `${comp.label}の場合、相続税の基礎控除はいくらですか？`,
      a: `法定相続人が${comp.n}人のため、基礎控除は3,000万円＋600万円×${comp.n}人＝${manLabel(manFromYen(comp_kiso(comp)))}です。財産の合計（課税価格）がこの金額以下なら、相続税はかかりません。出典：国税庁No.4152。`,
    },
    {
      q: `${comp.label}で遺産1億円のとき、相続税はいくらになりますか？`,
      a: `基礎控除${manLabel(manFromYen(ex.kiso))}を差し引いた課税遺産総額は${manLabel(manFromYen(ex.netEstate))}です。速算表の税率を適用した相続税の総額は約${manLabel(Math.round(manFromYen(ex.total)))}、${comp.shares.some((s) => s.spouse) ? '配偶者の税額軽減後は約' + manLabel(Math.round(manFromYen(ex.afterSpouse))) + 'が目安です。' : 'このケースには配偶者がいないため軽減はかかりません。'}出典：国税庁No.4155・No.4158。`,
    },
    {
      q: '生命保険金の非課税枠はこの早見表に反映されていますか？',
      a: '反映していません。早見表は財産区分を設けず「遺産総額（課税価格）」のみで一覧化しているため、生命保険金500万円×法定相続人の数の非課税枠は考慮していません。生命保険がある場合、実際の税額はこの早見表の概算よりやや低くなることがあります。正確な概算は診断ツールをご利用ください。',
    },
    {
      q: 'この早見表の数値をそのまま申告に使えますか？',
      a: '使えません。本早見表は基礎控除・速算表・配偶者の税額軽減の基本部分のみを反映した目安で、土地建物の評価（路線価・小規模宅地等の特例）や二次相続、実際の遺産分割の仕方などは反映していません。正確な税額計算・申告は税理士等の専門家にご確認ください。',
    },
  ];
}
function comp_kiso(comp) { return CONST.kisoBase + CONST.kisoPerHeir * comp.n; }

function faqForAsset(assetMan) {
  const compSpouse2 = COMPOSITIONS.find((c) => c.id === 'haigusha-ko2');
  const compKo2 = COMPOSITIONS.find((c) => c.id === 'ko2');
  const rSpouse2 = calcHayami(assetMan, compSpouse2);
  const rKo2 = calcHayami(assetMan, compKo2);
  return [
    {
      q: `遺産総額${manLabel(assetMan)}の場合、相続税はかかりますか？`,
      a: `相続人構成によって基礎控除が変わるため、税額の有無も変わります。例えば配偶者と子2人（法定相続人3人）なら基礎控除は4,800万円、子2人のみ（法定相続人2人）なら基礎控除は4,200万円です。財産合計がこの基礎控除以下であれば相続税はかかりません。出典：国税庁No.4152。`,
    },
    {
      q: `遺産${manLabel(assetMan)}・配偶者と子2人の場合、相続税の概算はいくらですか？`,
      a: `基礎控除4,800万円を差し引いた課税遺産総額は${manLabel(manFromYen(rSpouse2.netEstate))}です。相続税の総額は約${manLabel(Math.round(manFromYen(rSpouse2.total)))}、配偶者の税額軽減後は約${manLabel(Math.round(manFromYen(rSpouse2.afterSpouse)))}が目安です。出典：国税庁No.4155・No.4158。`,
    },
    {
      q: `遺産${manLabel(assetMan)}・子2人のみ（配偶者なし）の場合はどうなりますか？`,
      a: `基礎控除4,200万円を差し引いた課税遺産総額は${manLabel(manFromYen(rKo2.netEstate))}です。配偶者がいないため税額軽減は適用されず、相続税の総額（約${manLabel(Math.round(manFromYen(rKo2.total)))}）がそのまま家族全体の概算納付額の目安になります。出典：国税庁No.4155。`,
    },
    {
      q: 'この金額は正確な相続税額ですか？',
      a: '正確な税額ではありません。区切りのよい遺産総額と代表的な相続人構成についての概算です。土地建物の個別評価、小規模宅地等の特例、生命保険の非課税枠、二次相続、実際の遺産分割の仕方は反映していません。ご自身の財産で正確に近い概算を出すには、無料の相続税かんたん診断をご利用ください。',
    },
  ];
}

/* ---------------------------------------------------------------------------
 * 11. 直答ブロック生成（80〜120字目安・数値埋め込み）
 * ------------------------------------------------------------------------- */
function directAnswerForCompAsset(assetMan, comp, r) {
  const spouseNote = comp.shares.some((s) => s.spouse)
    ? `配偶者の税額軽減後は約${manLabel(Math.round(manFromYen(r.afterSpouse)))}`
    : `配偶者がいないため軽減はなく、総額約${manLabel(Math.round(manFromYen(r.total)))}がそのまま目安`;
  return `遺産${manLabel(assetMan)}・相続人が${comp.label}の場合、基礎控除${manLabel(manFromYen(r.kiso))}を差し引いた課税遺産${manLabel(manFromYen(r.netEstate))}に対する相続税の総額は約${manLabel(Math.round(manFromYen(r.total)))}、${spouseNote}が目安です。出典：国税庁No.4155・No.4152、${SOURCE_NOTE_DATE}確認。`;
}

/* ---------------------------------------------------------------------------
 * 12. 「構成別の一覧ページ」6枚
 * ------------------------------------------------------------------------- */
function buildCompositionPage(comp) {
  const path = `/hayami/${comp.id}/`;
  const rows = ASSET_STEPS_MAN.map((assetMan) => calcHayami(assetMan, comp));
  const title = `【早見表】${comp.label}の相続税はいくら？遺産3,000万〜3億円を一覧｜お金のカルテ`;
  const description = `相続人が${comp.label}の場合の相続税を、遺産総額3,000万円〜3億円まで1,000万円刻みで一覧表にした早見表。基礎控除・速算表・配偶者の税額軽減を反映した概算。出典：国税庁No.4152・4155・4158。`;

  // 直答（このページの代表：遺産1億円のケースを軸に）
  const repRow = rows.find((r) => r.assetMan === 10000);
  const directAnswer = directAnswerForCompAsset(10000, comp, repRow);

  const faqs = faqForComposition(comp);

  const tableRows = rows.map((r) => {
    const isRep = r.assetMan === 10000;
    return `        <tr${isRep ? ' class="hl"' : ''}>
          <td>${manLabel(r.assetMan)}</td>
          <td class="num">${manLabel(manFromYen(r.kiso))}</td>
          <td class="num">${manLabel(manFromYen(r.netEstate))}</td>
          <td class="num">${manLabel(Math.round(manFromYen(r.total)))}</td>
          <td class="num">${manLabel(Math.round(manFromYen(r.afterSpouse)))}</td>
          <td><a href="/hayami/isan-${r.assetMan}man/">総額${manLabel(r.assetMan)}の一覧 →</a></td>
        </tr>`;
  }).join('\n');

  const explain = `<div class="explain">
    <p>相続人が<strong>${comp.label}</strong>の場合、法定相続人の数は<strong>${comp.n}人</strong>です。
    基礎控除は「3,000万円＋600万円×${comp.n}人＝<strong>${manLabel(manFromYen(comp_kiso(comp)))}</strong>」となり、
    遺産総額がこれ以下であれば相続税はかかりません。
    ${comp.shares.some((s) => s.spouse)
      ? '配偶者がいるため、配偶者が取得した分は法定相続分（またはそれ以下）であれば大きく軽減されます（本表では配偶者は法定相続分どおりに取得したと仮定）。'
      : '配偶者がいないため、配偶者の税額軽減は適用されず、相続税の総額がそのまま家族全体の概算納付額になります。'}
    </p>
    <div class="stat-grid">
      <div class="stat"><div class="l">法定相続人の数</div><div class="v">${comp.n}人</div></div>
      <div class="stat"><div class="l">基礎控除</div><div class="v">${manLabel(manFromYen(comp_kiso(comp)))}</div></div>
      <div class="stat"><div class="l">配偶者の法定相続分</div><div class="v">${comp.shares.some((s) => s.spouse) ? (spouseShareLabel(comp)) : 'なし'}</div></div>
    </div>
  </div>`;

  const otherComps = COMPOSITIONS.filter((c) => c.id !== comp.id);
  const crossComps = otherComps.map((c) => `<a class="crosscard" href="/hayami/${c.id}/"><p class="t">${c.label} →</p><p>遺産3,000万〜3億円の相続税を一覧</p></a>`).join('\n      ');

  const bodyMain = `
  <div class="wrap">
    <p class="crumbs"><a href="/">お金のカルテ</a> ＞ <a href="/hayami/">相続税早見表</a> ＞ ${comp.label}</p>
    <p class="eyebrow">相続税の概算早見表</p>
    <h1>${comp.label}の相続税はいくら？<br>遺産3,000万〜3億円の早見表</h1>
    <p class="lead">相続人が${comp.label}（法定相続人${comp.n}人）の場合の相続税の概算を、遺産総額3,000万円〜3億円まで1,000万円刻みで一覧にしました。基礎控除・相続税の速算表・配偶者の税額軽減を反映しています。</p>
    <div class="answer">
      <span class="k">DIRECT ANSWER</span>
      <p>${directAnswer}</p>
    </div>
    ${explain}
  </div>

  <div class="wrap">
    <div class="wrap-table">
      <table class="hayami">
        <caption>相続人＝${comp.label}（法定相続人${comp.n}人・基礎控除${manLabel(manFromYen(comp_kiso(comp)))}）の相続税概算一覧</caption>
        <thead>
          <tr>
            <th>遺産総額<br>（課税価格）</th>
            <th>基礎控除</th>
            <th>課税遺産<br>総額</th>
            <th>相続税の<br>総額</th>
            <th>配偶者軽減後<br>（概算納付額）</th>
            <th>詳細</th>
          </tr>
        </thead>
        <tbody>
${tableRows}
        </tbody>
      </table>
    </div>
    ${disclaimerBox()}
    ${ctaBand()}
  </div>

  <div class="wrap"><div class="orn"><span class="ln"></span><span class="lbl">OTHER COMPOSITIONS</span><span class="ln"></span></div></div>

  <div class="wrap">
    <h2>他の相続人構成の早見表</h2>
    <p class="sec-sub">相続人構成が変わると、法定相続人の数と法定相続分が変わり、基礎控除と税額配分が変わります。</p>
    <div class="crossgrid">
      ${crossComps}
    </div>
  </div>

  <div class="wrap"><div class="orn"><span class="ln"></span><span class="lbl">FAQ</span><span class="ln"></span></div></div>

  <section id="faq">
    <div class="wrap">
      <h2>よくある質問</h2>
      <p class="sec-sub">${comp.label}の相続税について</p>
      <div class="faq">
${faqs.map((qa) => `        <details>
          <summary>${qa.q}</summary>
          <div class="a">${qa.a}</div>
        </details>`).join('\n')}
      </div>
    </div>
  </section>

  <div class="wrap">
    <div class="linklist">
      <a href="/sozoku/">相続税かんたん診断</a>
      <a href="/sozoku/index-definition/">相続準備指数の定義</a>
      <a href="/hayami/">早見表トップに戻る</a>
    </div>
  </div>
`;

  const html = renderPage({
    lang: 'ja',
    head: headBlock({ title, description, canonicalPath: path }),
    ld: [
      breadcrumbLd([
        { name: 'お金のカルテ', path: '/' },
        { name: '相続税早見表', path: '/hayami/' },
        { name: comp.label, path },
      ]),
      faqLd(faqs),
    ],
    body: bodyMain,
  });

  return { path, html };
}

function spouseShareLabel(comp) {
  const s = comp.shares.find((x) => x.spouse);
  if (!s) return 'なし';
  const frac = s.share;
  if (Math.abs(frac - 1) < 1e-9) return 'すべて（1/1）';
  if (Math.abs(frac - 0.5) < 1e-9) return '2分の1';
  if (Math.abs(frac - (2 / 3)) < 1e-6) return '3分の2';
  return `${(frac * 100).toFixed(1)}%`;
}

/* ---------------------------------------------------------------------------
 * 13. 「遺産総額別ページ」28枚
 * ------------------------------------------------------------------------- */
function buildAssetPage(assetMan) {
  const path = `/hayami/isan-${assetMan}man/`;
  const rows = COMPOSITIONS.map((comp) => calcHayami(assetMan, comp));
  const title = `遺産${manLabel(assetMan)}の相続税はいくら？相続人構成別の早見表｜お金のカルテ`;
  const description = `遺産総額${manLabel(assetMan)}の場合の相続税を、配偶者＋子・子のみなど代表的な相続人構成6パターンで一覧にした早見表。基礎控除・速算表・配偶者の税額軽減を反映した概算。出典：国税庁No.4152・4155・4158。`;

  const repRow = rows.find((r) => r.comp.id === 'haigusha-ko2');
  const directAnswer = directAnswerForCompAsset(assetMan, repRow.comp, repRow);
  const faqs = faqForAsset(assetMan);

  const tableRows = rows.map((r) => {
    const isRep = r.comp.id === 'haigusha-ko2';
    return `        <tr${isRep ? ' class="hl"' : ''}>
          <td>${r.comp.label}</td>
          <td class="num">${r.comp.n}人</td>
          <td class="num">${manLabel(manFromYen(r.kiso))}</td>
          <td class="num">${manLabel(manFromYen(r.netEstate))}</td>
          <td class="num">${manLabel(Math.round(manFromYen(r.total)))}</td>
          <td class="num">${manLabel(Math.round(manFromYen(r.afterSpouse)))}</td>
          <td><a href="/hayami/${r.comp.id}/">${r.comp.shortLabel}の一覧 →</a></td>
        </tr>`;
  }).join('\n');

  const idx = ASSET_STEPS_MAN.indexOf(assetMan);
  const prevMan = idx > 0 ? ASSET_STEPS_MAN[idx - 1] : null;
  const nextMan = idx < ASSET_STEPS_MAN.length - 1 ? ASSET_STEPS_MAN[idx + 1] : null;

  const kisoMin = Math.min(...COMPOSITIONS.map((c) => comp_kiso(c)));
  const kisoMax = Math.max(...COMPOSITIONS.map((c) => comp_kiso(c)));

  const explain = `<div class="explain">
    <p>遺産総額（課税価格）が<strong>${manLabel(assetMan)}</strong>の場合、相続税がかかるかどうか・いくらになるかは相続人構成によって大きく変わります。
    基礎控除は法定相続人の数によって「3,000万円＋600万円×人数」で決まり、本ページの6構成では
    <strong>${manLabel(manFromYen(kisoMin))}〜${manLabel(manFromYen(kisoMax))}</strong>の幅があります。
    配偶者がいる構成では配偶者の税額軽減（配偶者は法定相続分取得と仮定）により、家族全体の概算納付額が小さくなります。</p>
  </div>`;

  const crossAssets = [];
  if (prevMan) crossAssets.push(`<a class="crosscard" href="/hayami/isan-${prevMan}man/"><p class="t">遺産${manLabel(prevMan)}の早見表 →</p><p>1つ下の刻みの相続人構成別一覧</p></a>`);
  if (nextMan) crossAssets.push(`<a class="crosscard" href="/hayami/isan-${nextMan}man/"><p class="t">遺産${manLabel(nextMan)}の早見表 →</p><p>1つ上の刻みの相続人構成別一覧</p></a>`);
  // 3〜4件になるよう少し離れた総額も添える（3000万刻みで前後2つ）
  const farPrevMan = idx - 3 >= 0 ? ASSET_STEPS_MAN[idx - 3] : null;
  const farNextMan = idx + 3 < ASSET_STEPS_MAN.length ? ASSET_STEPS_MAN[idx + 3] : null;
  if (farPrevMan) crossAssets.push(`<a class="crosscard" href="/hayami/isan-${farPrevMan}man/"><p class="t">遺産${manLabel(farPrevMan)}の早見表 →</p><p>相続人構成別の相続税一覧</p></a>`);
  if (farNextMan) crossAssets.push(`<a class="crosscard" href="/hayami/isan-${farNextMan}man/"><p class="t">遺産${manLabel(farNextMan)}の早見表 →</p><p>相続人構成別の相続税一覧</p></a>`);

  const bodyMain = `
  <div class="wrap">
    <p class="crumbs"><a href="/">お金のカルテ</a> ＞ <a href="/hayami/">相続税早見表</a> ＞ 遺産${manLabel(assetMan)}</p>
    <p class="eyebrow">相続税の概算早見表</p>
    <h1>遺産${manLabel(assetMan)}の相続税はいくら？<br>相続人構成別の早見表</h1>
    <p class="lead">遺産総額（課税価格）${manLabel(assetMan)}の場合の相続税の概算を、配偶者＋子・子のみなど代表的な相続人構成6パターンで一覧にしました。基礎控除・相続税の速算表・配偶者の税額軽減を反映しています。</p>
    <div class="answer">
      <span class="k">DIRECT ANSWER</span>
      <p>${directAnswer}</p>
    </div>
    ${explain}
  </div>

  <div class="wrap">
    <div class="wrap-table">
      <table class="hayami">
        <caption>遺産総額 ${manLabel(assetMan)} の場合の相続人構成別・相続税概算一覧</caption>
        <thead>
          <tr>
            <th>相続人構成</th>
            <th>法定相続人</th>
            <th>基礎控除</th>
            <th>課税遺産<br>総額</th>
            <th>相続税の<br>総額</th>
            <th>配偶者軽減後<br>（概算納付額）</th>
            <th>詳細</th>
          </tr>
        </thead>
        <tbody>
${tableRows}
        </tbody>
      </table>
    </div>
    ${disclaimerBox()}
    ${ctaBand()}
  </div>

  <div class="wrap"><div class="orn"><span class="ln"></span><span class="lbl">OTHER AMOUNTS</span><span class="ln"></span></div></div>

  <div class="wrap">
    <h2>他の遺産総額の早見表</h2>
    <p class="sec-sub">遺産総額が変わると、基礎控除を超える金額（課税遺産総額）と税率区分が変わります。</p>
    <div class="crossgrid">
      ${crossAssets.join('\n      ')}
    </div>
  </div>

  <div class="wrap"><div class="orn"><span class="ln"></span><span class="lbl">FAQ</span><span class="ln"></span></div></div>

  <section id="faq">
    <div class="wrap">
      <h2>よくある質問</h2>
      <p class="sec-sub">遺産${manLabel(assetMan)}の相続税について</p>
      <div class="faq">
${faqs.map((qa) => `        <details>
          <summary>${qa.q}</summary>
          <div class="a">${qa.a}</div>
        </details>`).join('\n')}
      </div>
    </div>
  </section>

  <div class="wrap">
    <div class="linklist">
      <a href="/sozoku/">相続税かんたん診断</a>
      <a href="/sozoku/index-definition/">相続準備指数の定義</a>
      <a href="/hayami/">早見表トップに戻る</a>
    </div>
  </div>
`;

  const html = renderPage({
    lang: 'ja',
    head: headBlock({ title, description, canonicalPath: path }),
    ld: [
      breadcrumbLd([
        { name: 'お金のカルテ', path: '/' },
        { name: '相続税早見表', path: '/hayami/' },
        { name: `遺産${manLabel(assetMan)}`, path },
      ]),
      faqLd(faqs),
    ],
    body: bodyMain,
  });

  return { path, html };
}

/* ---------------------------------------------------------------------------
 * 14. 索引トップページ
 * ------------------------------------------------------------------------- */
function buildIndexPage() {
  const path = '/hayami/';
  const title = '相続税の概算早見表｜遺産総額・相続人構成でわかる目安一覧｜お金のカルテ';
  const description = '遺産総額3,000万円〜3億円×相続人構成6パターンの相続税を早見表で一覧化。基礎控除・速算表・配偶者の税額軽減を反映した概算。あなたの財産で正確に試算するなら相続税かんたん診断へ。';

  const compCards = COMPOSITIONS.map((c) => `<a class="crosscard" href="/hayami/${c.id}/"><p class="t">${c.label} →</p><p>遺産3,000万〜3億円の相続税を一覧（法定相続人${c.n}人・基礎控除${manLabel(manFromYen(comp_kiso(c)))}）</p></a>`).join('\n      ');

  const assetCards = ASSET_STEPS_MAN.map((m) => `<a class="crosscard" href="/hayami/isan-${m}man/"><p class="t">遺産${manLabel(m)} →</p><p>相続人構成6パターンの相続税を一覧</p></a>`).join('\n      ');

  const faqs = [
    {
      q: '相続税の早見表はどのように使えばいいですか？',
      a: 'まずお手元の財産のおおよその合計に近い「遺産総額別ページ」を開くと、配偶者の有無や子の人数による違いを一覧で比較できます。逆に相続人構成が決まっている場合は「構成別ページ」で金額の刻みごとの目安を確認できます。どちらも概算であり、正確な試算はご自身の財産を入力する診断ツールをご利用ください。',
    },
    {
      q: 'なぜ早見表と実際の申告額が違うことがあるのですか？',
      a: '早見表は基礎控除・速算表・配偶者の税額軽減という基本要素のみを反映した概算だからです。実際の相続税は、土地建物の評価方法（路線価や小規模宅地等の特例）、生命保険金の非課税枠、二次相続、実際の遺産分割の仕方などによって変動します。正確な金額は税理士等の専門家にご確認ください。',
    },
    {
      q: '相続人構成が早見表の6パターンに当てはまらない場合は？',
      a: '早見表は代表的な6パターン（配偶者＋子1〜3人、子のみ2〜3人、配偶者のみ）に絞っています。それ以外の構成（親や兄弟姉妹が相続人になる場合など）や、財産の内訳（不動産・現預金・生命保険など）を反映した概算は、無料の相続税かんたん診断でブラウザ内試算できます。',
    },
  ];

  const bodyMain = `
  <div class="wrap">
    <p class="crumbs"><a href="/">お金のカルテ</a> ＞ 相続税早見表</p>
    <p class="eyebrow">相続税の概算早見表</p>
    <h1>相続税の概算早見表<br>遺産総額 × 相続人構成で見る目安</h1>
    <p class="lead">遺産総額3,000万円〜3億円（1,000万円刻み・28通り）と、代表的な相続人構成6パターンを組み合わせ、相続税の概算を一覧にしました。基礎控除・相続税の速算表・配偶者の税額軽減を反映しています。</p>
    <div class="answer">
      <span class="k">DIRECT ANSWER</span>
      <p>相続税は「財産合計−基礎控除（3,000万円＋600万円×法定相続人の数）」を法定相続分で按分し、10〜55%の累進税率（速算表）を適用して合計し、配偶者の税額軽減を反映して求めます。本早見表は、この計算を遺産総額と相続人構成の代表的な組み合わせであらかじめ算出した一覧です。出典：国税庁No.4152・4155・4158、${SOURCE_NOTE_DATE}確認。</p>
    </div>
  </div>

  <div class="wrap">
    ${ctaBand()}
  </div>

  <div class="wrap"><div class="orn"><span class="ln"></span><span class="lbl">BY COMPOSITION</span><span class="ln"></span></div></div>

  <div class="wrap">
    <h2>相続人構成から探す</h2>
    <p class="sec-sub">構成ごとに、遺産総額3,000万〜3億円の相続税を一覧表示します。</p>
    <div class="crossgrid">
      ${compCards}
    </div>
  </div>

  <div class="wrap"><div class="orn"><span class="ln"></span><span class="lbl">BY AMOUNT</span><span class="ln"></span></div></div>

  <div class="wrap">
    <h2>遺産総額から探す</h2>
    <p class="sec-sub">3,000万円〜3億円まで1,000万円刻み・全28通り。各ページで相続人構成6パターンを比較できます。</p>
    <div class="crossgrid">
      ${assetCards}
    </div>
  </div>

  <div class="wrap">
    ${disclaimerBox()}
  </div>

  <div class="wrap"><div class="orn"><span class="ln"></span><span class="lbl">FAQ</span><span class="ln"></span></div></div>

  <section id="faq">
    <div class="wrap">
      <h2>よくある質問</h2>
      <p class="sec-sub">相続税の早見表について</p>
      <div class="faq">
${faqs.map((qa) => `        <details>
          <summary>${qa.q}</summary>
          <div class="a">${qa.a}</div>
        </details>`).join('\n')}
      </div>
    </div>
  </section>

  <div class="wrap">
    <div class="linklist">
      <a href="/sozoku/">相続税かんたん診断</a>
      <a href="/sozoku/index-definition/">相続準備指数の定義</a>
    </div>
  </div>
`;

  const html = renderPage({
    lang: 'ja',
    head: headBlock({ title, description, canonicalPath: path }),
    ld: [
      breadcrumbLd([
        { name: 'お金のカルテ', path: '/' },
        { name: '相続税早見表', path },
      ]),
      faqLd(faqs),
    ],
    body: bodyMain,
  });

  return { path, html };
}

/* ---------------------------------------------------------------------------
 * 15. ページ全体レンダリング
 * ------------------------------------------------------------------------- */
function renderPage({ lang, head, ld, body }) {
  const ldScripts = ld.map(ldScript).join('\n');
  return `<!DOCTYPE html>
<html lang="${lang}">
<head>
${head}
${ldScripts}
<style>${STYLE}</style>
<script>${FRAME_BUST_JS}</script>
</head>
<body>
${headerBlock()}
<main>
${body}
</main>
${footerBlock()}
</body>
</html>
`;
}

/* ---------------------------------------------------------------------------
 * 16. 書き出し
 * ------------------------------------------------------------------------- */
function writePage(pagePath, html) {
  // pagePath: "/hayami/xxx/" → hayami/xxx/index.html
  const rel = pagePath.replace(/^\/hayami\//, '').replace(/\/$/, '');
  const dir = rel === '' ? OUT_DIR : join(OUT_DIR, rel);
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, 'index.html'), html, 'utf8');
}

function buildSitemap(urls) {
  const lastmod = SOURCE_NOTE_DATE;
  const body = urls.map((u) => `  <url>
    <loc>${SITE_ORIGIN}${u}</loc>
    <lastmod>${lastmod}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>${u === '/hayami/' ? '0.7' : '0.5'}</priority>
  </url>`).join('\n');
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${body}\n</urlset>\n`;
}

/* ---------------------------------------------------------------------------
 * 17. メイン処理
 * ------------------------------------------------------------------------- */
function main() {
  console.log('=== お金のカルテ 相続税早見表 pSEO ビルド開始 ===');

  const check = runSelfCheck();
  console.log(
    `[自己検算OK] 遺産${check.assetMan}万円・配偶者+子2人 → 基礎控除${check.kiso}万円 / 課税遺産${check.netEstate}万円 / 総額${check.total}万円 / 配偶者軽減後${check.afterSpouse}万円`
  );

  if (existsSync(OUT_DIR)) {
    rmSync(OUT_DIR, { recursive: true, force: true });
  }
  mkdirSync(OUT_DIR, { recursive: true });

  const pages = [];

  // 索引トップ
  pages.push(buildIndexPage());

  // 構成別 6ページ
  for (const comp of COMPOSITIONS) {
    pages.push(buildCompositionPage(comp));
  }

  // 総額別 28ページ
  for (const assetMan of ASSET_STEPS_MAN) {
    pages.push(buildAssetPage(assetMan));
  }

  for (const p of pages) {
    writePage(p.path, p.html);
  }

  const urls = pages.map((p) => p.path);
  const sitemapXml = buildSitemap(urls);
  writeFileSync(join(OUT_DIR, 'sitemap-hayami.xml'), sitemapXml, 'utf8');

  console.log(`[生成完了] ページ数: ${pages.length}（索引1 + 構成別${COMPOSITIONS.length} + 総額別${ASSET_STEPS_MAN.length}）`);
  console.log(`[出力先] ${OUT_DIR}`);
  console.log(`[sitemap] ${join(OUT_DIR, 'sitemap-hayami.xml')}`);
  console.log('=== ビルド完了 ===');
}

main();

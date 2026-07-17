#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# お金のカルテ ─ 相続税の概算早見表 pSEO ジェネレータ（Python版）
# -----------------------------------------------------------------------------
# 実行: python scripts/build_hayami.py
# 出力: okane-carte/hayami/ 配下に静的HTML一式 + sitemap-hayami.xml
#
# 依存ゼロ（Python標準ライブラリのみ）。外部API・外部CDNなし。
# ※ 当初 scripts/build-hayami.mjs（Node）で実装したが、当環境にNode未導入のため
#    同一ロジック・同一出力をPythonへ移植した。計算式・定数・URL体系・
#    テンプレートは sozoku/index.html の calc()/taxOn()/heirsInfo() と完全一致。
#
# 【計算の一致】早見表では「財産＝課税価格」とみなす単純化を行い、生命保険の
#   非課税枠（500万円×人数）は考慮しない（保険という財産区分が早見表に無いため）。
#   この単純化は各ページの免責欄に明記する。
#
# 【出典（design/tax-sources.md と同一・推測値なし）】
#   基礎控除：国税庁 No.4152 ／ 速算表：No.4155（令和7年4月1日現在法令等）
#   生命保険非課税：No.4114（本表では不使用・注記のみ）／ 配偶者軽減：No.4158
#   確認日：2026-07-07。
# =============================================================================

import os
import json
import math
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, 'hayami')
SITE_ORIGIN = 'https://okane-carte.jp'
SOURCE_NOTE_DATE = '2026-07-07'
YEAR = 2026


def jsround(x):
    """JSの Math.round（正の数を四捨五入・半分は切り上げ）に一致。"""
    return int(math.floor(x + 0.5))


# --- 1. 税制定数（sozoku/config.json の constants と完全一致・単位:円） ---
KISO_BASE = 30000000
KISO_PER_HEIR = 6000000
TAX_TABLE = [
    {'upTo': 10000000,  'rate': 0.10, 'deduct': 0},
    {'upTo': 30000000,  'rate': 0.15, 'deduct': 500000},
    {'upTo': 50000000,  'rate': 0.20, 'deduct': 2000000},
    {'upTo': 100000000, 'rate': 0.30, 'deduct': 7000000},
    {'upTo': 200000000, 'rate': 0.40, 'deduct': 17000000},
    {'upTo': 300000000, 'rate': 0.45, 'deduct': 27000000},
    {'upTo': 600000000, 'rate': 0.50, 'deduct': 42000000},
    {'upTo': None,      'rate': 0.55, 'deduct': 72000000},
]
SOURCE_NOTE = (
    '国税庁 No.4152（基礎控除・計算方法）／No.4155（速算表・令和7年4月1日現在法令等）／'
    'No.4158（配偶者の税額軽減）。確認日 ' + SOURCE_NOTE_DATE + '。詳細は design/tax-sources.md。'
)


# --- 2. 速算表（sozoku taxOn() と同一） ---
def tax_on(yen_amt):
    if yen_amt <= 0:
        return 0
    for t in TAX_TABLE:
        if t['upTo'] is None or yen_amt <= t['upTo']:
            return yen_amt * t['rate'] - t['deduct']
    return 0


# --- 3. 相続人構成（6構成固定） ---
COMPOSITIONS = [
    {'id': 'haigusha-ko1', 'label': '配偶者＋子1人', 'shortLabel': '配偶者と子1人', 'n': 2,
     'shares': [{'who': '配偶者', 'share': 0.5, 'spouse': True}, {'who': '子', 'share': 0.5}]},
    {'id': 'haigusha-ko2', 'label': '配偶者＋子2人', 'shortLabel': '配偶者と子2人', 'n': 3,
     'shares': [{'who': '配偶者', 'share': 0.5, 'spouse': True}, {'who': '子', 'share': 0.25}, {'who': '子', 'share': 0.25}]},
    {'id': 'haigusha-ko3', 'label': '配偶者＋子3人', 'shortLabel': '配偶者と子3人', 'n': 4,
     'shares': [{'who': '配偶者', 'share': 0.5, 'spouse': True}, {'who': '子', 'share': 1/6}, {'who': '子', 'share': 1/6}, {'who': '子', 'share': 1/6}]},
    {'id': 'ko2', 'label': '子のみ2人', 'shortLabel': '子2人のみ', 'n': 2,
     'shares': [{'who': '子', 'share': 0.5}, {'who': '子', 'share': 0.5}]},
    {'id': 'ko3', 'label': '子のみ3人', 'shortLabel': '子3人のみ', 'n': 3,
     'shares': [{'who': '子', 'share': 1/3}, {'who': '子', 'share': 1/3}, {'who': '子', 'share': 1/3}]},
    {'id': 'haigusha-nomi', 'label': '配偶者のみ（子なし・親兄弟なし）', 'shortLabel': '配偶者のみ', 'n': 1,
     'shares': [{'who': '配偶者', 'share': 1, 'spouse': True}]},
]

# --- 4. 遺産総額の刻み：3,000万〜3億円を1,000万円刻み（万円単位）＝28通り ---
ASSET_STEPS_MAN = list(range(3000, 30001, 1000))


def has_spouse(comp):
    return any(s.get('spouse') for s in comp['shares'])


def comp_kiso(comp):
    return KISO_BASE + KISO_PER_HEIR * comp['n']


# --- 5. 本計算（sozoku calc() と同じ式） ---
def calc_hayami(asset_man, comp):
    asset_yen = asset_man * 10000
    kiso = KISO_BASE + KISO_PER_HEIR * comp['n']
    net_estate = max(0, asset_yen - kiso)
    total = 0.0
    per_heir = []
    for s in comp['shares']:
        base = net_estate * s['share']
        tax = tax_on(base)
        total += tax
        row = dict(s)
        row['base'] = base
        row['tax'] = tax
        per_heir.append(row)
    total = max(0, total)
    spouse_share = sum(s['share'] for s in comp['shares'] if s.get('spouse'))
    after_spouse = max(0, total * (1 - spouse_share))
    return {
        'assetMan': asset_man, 'assetYen': asset_yen, 'kiso': kiso, 'netEstate': net_estate,
        'total': total, 'afterSpouse': after_spouse, 'spouseShare': spouse_share,
        'perHeir': per_heir, 'comp': comp,
    }


# --- 6. 自己検算 ---
def run_self_check():
    comp = next(c for c in COMPOSITIONS if c['id'] == 'haigusha-ko2')
    r = calc_hayami(5000, comp)

    def assert_eq(actual, expected, label):
        if jsround(actual) != expected:
            raise SystemExit('[自己検算失敗] %s: expected=%d actual=%d' % (label, expected, jsround(actual)))

    assert_eq(r['kiso'], 48000000, '基礎控除（4,800万円）')
    assert_eq(r['netEstate'], 2000000, '課税遺産総額（200万円）')
    assert_eq(r['total'], 200000, '相続税の総額（20万円）')
    assert_eq(r['afterSpouse'], 100000, '配偶者軽減後（10万円）')
    return {'assetMan': 5000, 'kiso': r['kiso'] // 10000, 'netEstate': r['netEstate'] // 10000,
            'total': jsround(r['total']) // 10000, 'afterSpouse': jsround(r['afterSpouse']) // 10000}


# --- 7. 表記ユーティリティ ---
def yen(n):
    return '{:,}'.format(jsround(n))


def man_from_yen(y):
    return jsround(y / 10000)


def man_label(m):
    m = int(m)
    if m >= 10000:
        oku = m // 10000
        rest = m % 10000
        return ('%d億%s万円' % (oku, yen(rest))) if rest else ('%d億円' % oku)
    return '%s万円' % yen(m)


def spouse_share_label(comp):
    s = next((x for x in comp['shares'] if x.get('spouse')), None)
    if not s:
        return 'なし'
    frac = s['share']
    if abs(frac - 1) < 1e-9:
        return 'すべて（1/1）'
    if abs(frac - 0.5) < 1e-9:
        return '2分の1'
    if abs(frac - (2/3)) < 1e-6:
        return '3分の2'
    return '%.1f%%' % (frac * 100)


# --- 8. 共通パーツ ---
CSP = (
    "default-src 'self'; base-uri 'self'; object-src 'none'; img-src 'self' data:; "
    "style-src 'self' 'unsafe-inline'; font-src 'self'; script-src 'self' 'unsafe-inline'; "
    "frame-src 'none'; connect-src 'self'; form-action 'self'; frame-ancestors 'none';"
)
FRAME_BUST_JS = "if (window.top !== window.self) { window.top.location = window.self.location; }"

STYLE = r"""
  @font-face{font-family:"Shippori Mincho";src:url("/assets/fonts/ShipporiMincho-Bold.subset.woff2") format("woff2");font-weight:700;font-display:swap}
  @font-face{font-family:"Marcellus";src:url("/assets/fonts/Marcellus-400.woff2") format("woff2");font-weight:400;font-display:swap}
  @font-face{font-family:"Cormorant";src:url("/assets/fonts/Cormorant-500.woff2") format("woff2");font-weight:500;font-display:swap}
  @font-face{font-family:"Cormorant";src:url("/assets/fonts/Cormorant-600.woff2") format("woff2");font-weight:600;font-display:swap}
  :root{
    --bg:#FAF6EE; --bg-2:#F1E8D9; --paper:#FFFDF8;
    --green:#22463C; --green-2:#5E7E6E;
    --shu:#A24B3C; --shu-2:#8B3E30;
    --gold:#C7A24E; --gold-2:#8B6B28; --gold-hi:#E6D2A0; --gold-soft:#F4ECD7;
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
"""


def head_block(title, description, canonical_path, og_type='article', indexable=True):  # go-live: index
    canonical = SITE_ORIGIN + canonical_path
    robots = 'index, follow' if indexable else 'noindex, nofollow'
    return (
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<meta http-equiv="Content-Security-Policy" content="%s">\n'
        '<meta name="referrer" content="strict-origin-when-cross-origin">\n'
        '<!-- 公開前は noindex。go-live 時に index, follow へ一括切替（オーケストレーター担当）。 -->\n'
        '<meta name="robots" content="%s">\n'
        '<title>%s</title>\n'
        '<meta name="description" content="%s">\n'
        '<link rel="canonical" href="%s">\n'
        '<meta property="og:type" content="%s">\n'
        '<meta property="og:site_name" content="お金のカルテ">\n'
        '<meta property="og:title" content="%s">\n'
        '<meta property="og:description" content="%s">\n'
        '<meta property="og:url" content="%s">\n'
        '<meta property="og:image" content="%s/sozoku/assets/ogp.png">\n'
        '<meta name="twitter:card" content="summary_large_image">\n'
        '<meta name="twitter:title" content="%s">\n'
        '<meta name="twitter:description" content="%s">'
    ) % (CSP, robots, title, description, canonical, og_type, title, description, canonical,
         SITE_ORIGIN, title, description)


def header_block():
    return (
        '<header>\n'
        '  <div class="wrap">\n'
        '    <a class="brand" href="/">\n'
        '      <span><span class="mark">お金のカルテ</span><br><span class="sub">相続税の概算早見表</span></span>\n'
        '    </a>\n'
        '    <div class="navlinks">\n'
        '      <a class="navlink" href="/sozoku/">相続税かんたん診断 →</a>\n'
        '      <a class="navlink" href="/hayami/">早見表トップ</a>\n'
        '    </div>\n'
        '  </div>\n'
        '</header>'
    )


def footer_block():
    return (
        '<footer class="site">\n'
        '  <div class="wrap">\n'
        '    <div class="footlinks">\n'
        '      <a href="/">お金のカルテ トップ</a>\n'
        '      <a href="/sozoku/">相続税かんたん診断</a>\n'
        '      <a href="/zoyo/">生前贈与診断</a>\n'
        '      <a href="/fukuri/">複利シミュレーター</a>\n'
        '      <a href="/jikabuka/">自社株評価診断</a>\n'
        '      <a href="/hayami/">相続税の概算早見表</a>\n'
        '    </div>\n'
        '    <p class="foot-discl">本ページの数値は一般的な速算による概算の目安であり、個別の税務相談・税額計算の代行ではありません。土地建物の評価（路線価・小規模宅地等の特例）、生命保険の非課税枠、二次相続、実際の遺産分割の仕方などは反映していません。正確な税額計算・申告は税理士等の専門家にご確認ください。</p>\n'
        '    <p class="foot-discl">出典：%s</p>\n'
        '    <p class="foot-discl">© %d リブメーカーズ株式会社（LIVmakers Co., Ltd.）／ お金のカルテ ／ 本サイトは相続の一般的な情報提供および概算シミュレーションであり、税務・法務・投資に関する助言・代理を行うものではありません。</p>\n'
        '  </div>\n'
        '</footer>'
    ) % (SOURCE_NOTE, YEAR)


def cta_band():
    return (
        '<div class="cta-band">\n'
        '  <div>\n'
        '    <h3>あなたの財産で、正確に概算する</h3>\n'
        '    <p>早見表は「区切りのよい金額」での目安です。ご自身の財産（不動産・現預金・有価証券・生命保険など）を入れて、5分・匿名・登録不要で「家族へのカルテ」を発行できます。</p>\n'
        '  </div>\n'
        '  <a class="btn gold" href="/sozoku/">あなたの相続税を概算する →</a>\n'
        '</div>'
    )


def disclaimer_box(extra=''):
    return (
        '<div class="disclaimer-box">\n'
        '  <strong>この早見表について：</strong> 本ページの金額は、遺産総額（課税価格）と相続人構成の代表的な組み合わせについて、\n'
        '  基礎控除・相続税の速算表・配偶者の税額軽減のみを反映した<strong>簡易な概算</strong>です。\n'
        '  生命保険金の非課税枠（500万円×法定相続人の数）は、早見表では財産区分を設けていないため反映していません\n'
        '  （その分、実際の税額はここに示す概算より低くなる場合があります）。\n'
        '  土地建物の個別評価・小規模宅地等の特例・二次相続・各種税額控除・実際の遺産分割の仕方は未反映です。\n'
        '  %s\n'
        '  正確な相続税額の計算・申告は、必ず税理士等の専門家にご確認ください。\n'
        '  出典：%s\n'
        '</div>'
    ) % (extra, SOURCE_NOTE)


# --- 9. JSON-LD ---
def breadcrumb_ld(items):
    return {
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': it['name'], 'item': SITE_ORIGIN + it['path']}
            for i, it in enumerate(items)
        ],
    }


def faq_ld(qas):
    return {
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'mainEntity': [
            {'@type': 'Question', 'name': qa['q'], 'acceptedAnswer': {'@type': 'Answer', 'text': qa['a']}}
            for qa in qas
        ],
    }


def ld_script(obj):
    return '<script type="application/ld+json">\n%s\n</script>' % json.dumps(obj, ensure_ascii=False, indent=2)


# --- 10. FAQ 生成 ---
def faq_for_composition(comp):
    ex = calc_hayami(10000, comp)
    kiso_label = man_label(man_from_yen(comp_kiso(comp)))
    if has_spouse(comp):
        a2_tail = '配偶者の税額軽減後は約' + man_label(jsround(man_from_yen(ex['afterSpouse']))) + 'が目安です。'
    else:
        a2_tail = 'このケースには配偶者がいないため軽減はかかりません。'
    return [
        {'q': '%sの場合、相続税の基礎控除はいくらですか？' % comp['label'],
         'a': '法定相続人が%d人のため、基礎控除は3,000万円＋600万円×%d人＝%sです。財産の合計（課税価格）がこの金額以下なら、相続税はかかりません。出典：国税庁No.4152。' % (comp['n'], comp['n'], kiso_label)},
        {'q': '%sで遺産1億円のとき、相続税はいくらになりますか？' % comp['label'],
         'a': '基礎控除%sを差し引いた課税遺産総額は%sです。速算表の税率を適用した相続税の総額は約%s、%s出典：国税庁No.4155・No.4158。' % (
             man_label(man_from_yen(ex['kiso'])), man_label(man_from_yen(ex['netEstate'])), man_label(jsround(man_from_yen(ex['total']))), a2_tail)},
        {'q': '生命保険金の非課税枠はこの早見表に反映されていますか？',
         'a': '反映していません。早見表は財産区分を設けず「遺産総額（課税価格）」のみで一覧化しているため、生命保険金500万円×法定相続人の数の非課税枠は考慮していません。生命保険がある場合、実際の税額はこの早見表の概算よりやや低くなることがあります。正確な概算は診断ツールをご利用ください。'},
        {'q': 'この早見表の数値をそのまま申告に使えますか？',
         'a': '使えません。本早見表は基礎控除・速算表・配偶者の税額軽減の基本部分のみを反映した目安で、土地建物の評価（路線価・小規模宅地等の特例）や二次相続、実際の遺産分割の仕方などは反映していません。正確な税額計算・申告は税理士等の専門家にご確認ください。'},
    ]


def faq_for_asset(asset_man):
    comp_s2 = next(c for c in COMPOSITIONS if c['id'] == 'haigusha-ko2')
    comp_k2 = next(c for c in COMPOSITIONS if c['id'] == 'ko2')
    r_s2 = calc_hayami(asset_man, comp_s2)
    r_k2 = calc_hayami(asset_man, comp_k2)
    lbl = man_label(asset_man)
    return [
        {'q': '遺産総額%sの場合、相続税はかかりますか？' % lbl,
         'a': '相続人構成によって基礎控除が変わるため、税額の有無も変わります。例えば配偶者と子2人（法定相続人3人）なら基礎控除は4,800万円、子2人のみ（法定相続人2人）なら基礎控除は4,200万円です。財産合計がこの基礎控除以下であれば相続税はかかりません。出典：国税庁No.4152。'},
        {'q': '遺産%s・配偶者と子2人の場合、相続税の概算はいくらですか？' % lbl,
         'a': '基礎控除4,800万円を差し引いた課税遺産総額は%sです。相続税の総額は約%s、配偶者の税額軽減後は約%sが目安です。出典：国税庁No.4155・No.4158。' % (
             man_label(man_from_yen(r_s2['netEstate'])), man_label(jsround(man_from_yen(r_s2['total']))), man_label(jsround(man_from_yen(r_s2['afterSpouse']))))},
        {'q': '遺産%s・子2人のみ（配偶者なし）の場合はどうなりますか？' % lbl,
         'a': '基礎控除4,200万円を差し引いた課税遺産総額は%sです。配偶者がいないため税額軽減は適用されず、相続税の総額（約%s）がそのまま家族全体の概算納付額の目安になります。出典：国税庁No.4155。' % (
             man_label(man_from_yen(r_k2['netEstate'])), man_label(jsround(man_from_yen(r_k2['total']))))},
        {'q': 'この金額は正確な相続税額ですか？',
         'a': '正確な税額ではありません。区切りのよい遺産総額と代表的な相続人構成についての概算です。土地建物の個別評価、小規模宅地等の特例、生命保険の非課税枠、二次相続、実際の遺産分割の仕方は反映していません。ご自身の財産で正確に近い概算を出すには、無料の相続税かんたん診断をご利用ください。'},
    ]


# --- 11. 直答ブロック ---
def direct_answer_for_comp_asset(asset_man, comp, r):
    if has_spouse(comp):
        spouse_note = '配偶者の税額軽減後は約%s' % man_label(jsround(man_from_yen(r['afterSpouse'])))
    else:
        spouse_note = '配偶者がいないため軽減はなく、総額約%sがそのまま目安' % man_label(jsround(man_from_yen(r['total'])))
    return '遺産%s・相続人が%sの場合、基礎控除%sを差し引いた課税遺産%sに対する相続税の総額は約%s、%sが目安です。出典：国税庁No.4155・No.4152、%s確認。' % (
        man_label(asset_man), comp['label'], man_label(man_from_yen(r['kiso'])), man_label(man_from_yen(r['netEstate'])),
        man_label(jsround(man_from_yen(r['total']))), spouse_note, SOURCE_NOTE_DATE)


def faq_details_html(faqs):
    return '\n'.join(
        '        <details>\n          <summary>%s</summary>\n          <div class="a">%s</div>\n        </details>' % (qa['q'], qa['a'])
        for qa in faqs
    )


def render_page(head, ld, body):
    ld_scripts = '\n'.join(ld_script(o) for o in ld)
    return (
        '<!DOCTYPE html>\n<html lang="ja">\n<head>\n%s\n%s\n<style>%s</style>\n<script>%s</script>\n</head>\n<body>\n%s\n<main>\n%s\n</main>\n%s\n</body>\n</html>\n'
    ) % (head, ld_scripts, STYLE, FRAME_BUST_JS, header_block(), body, footer_block())


# --- 12. 構成別ページ ---
def build_composition_page(comp):
    path = '/hayami/%s/' % comp['id']
    rows = [calc_hayami(a, comp) for a in ASSET_STEPS_MAN]
    title = '【早見表】%sの相続税はいくら？遺産3,000万〜3億円を一覧｜お金のカルテ' % comp['label']
    description = '相続人が%sの場合の相続税を、遺産総額3,000万円〜3億円まで1,000万円刻みで一覧表にした早見表。基礎控除・速算表・配偶者の税額軽減を反映した概算。出典：国税庁No.4152・4155・4158。' % comp['label']
    rep_row = next(r for r in rows if r['assetMan'] == 10000)
    direct_answer = direct_answer_for_comp_asset(10000, comp, rep_row)
    faqs = faq_for_composition(comp)

    table_rows = '\n'.join(
        '        <tr%s>\n          <td>%s</td>\n          <td class="num">%s</td>\n          <td class="num">%s</td>\n          <td class="num">%s</td>\n          <td class="num">%s</td>\n          <td><a href="/hayami/isan-%dman/">総額%sの一覧 →</a></td>\n        </tr>' % (
            ' class="hl"' if r['assetMan'] == 10000 else '',
            man_label(r['assetMan']), man_label(man_from_yen(r['kiso'])), man_label(man_from_yen(r['netEstate'])),
            man_label(jsround(man_from_yen(r['total']))), man_label(jsround(man_from_yen(r['afterSpouse']))),
            r['assetMan'], man_label(r['assetMan']))
        for r in rows)

    if has_spouse(comp):
        spouse_explain = '配偶者がいるため、配偶者が取得した分は法定相続分（またはそれ以下）であれば大きく軽減されます（本表では配偶者は法定相続分どおりに取得したと仮定）。'
        spouse_stat = spouse_share_label(comp)
    else:
        spouse_explain = '配偶者がいないため、配偶者の税額軽減は適用されず、相続税の総額がそのまま家族全体の概算納付額になります。'
        spouse_stat = 'なし'

    explain = (
        '<div class="explain">\n'
        '    <p>相続人が<strong>%s</strong>の場合、法定相続人の数は<strong>%d人</strong>です。\n'
        '    基礎控除は「3,000万円＋600万円×%d人＝<strong>%s</strong>」となり、\n'
        '    遺産総額がこれ以下であれば相続税はかかりません。\n'
        '    %s</p>\n'
        '    <div class="stat-grid">\n'
        '      <div class="stat"><div class="l">法定相続人の数</div><div class="v">%d人</div></div>\n'
        '      <div class="stat"><div class="l">基礎控除</div><div class="v">%s</div></div>\n'
        '      <div class="stat"><div class="l">配偶者の法定相続分</div><div class="v">%s</div></div>\n'
        '    </div>\n'
        '  </div>'
    ) % (comp['label'], comp['n'], comp['n'], man_label(man_from_yen(comp_kiso(comp))), spouse_explain,
         comp['n'], man_label(man_from_yen(comp_kiso(comp))), spouse_stat)

    cross = '\n      '.join(
        '<a class="crosscard" href="/hayami/%s/"><p class="t">%s →</p><p>遺産3,000万〜3億円の相続税を一覧</p></a>' % (c['id'], c['label'])
        for c in COMPOSITIONS if c['id'] != comp['id'])

    body = (
        '\n  <div class="wrap">\n'
        '    <p class="crumbs"><a href="/">お金のカルテ</a> ＞ <a href="/hayami/">相続税早見表</a> ＞ %s</p>\n'
        '    <p class="eyebrow">相続税の概算早見表</p>\n'
        '    <h1>%sの相続税はいくら？<br>遺産3,000万〜3億円の早見表</h1>\n'
        '    <p class="lead">相続人が%s（法定相続人%d人）の場合の相続税の概算を、遺産総額3,000万円〜3億円まで1,000万円刻みで一覧にしました。基礎控除・相続税の速算表・配偶者の税額軽減を反映しています。</p>\n'
        '    <div class="answer">\n      <span class="k">DIRECT ANSWER</span>\n      <p>%s</p>\n    </div>\n'
        '    %s\n  </div>\n\n'
        '  <div class="wrap">\n    <div class="wrap-table" tabindex="0" role="region" aria-label="相続税概算一覧表（横スクロール可）">\n      <table class="hayami">\n'
        '        <caption>相続人＝%s（法定相続人%d人・基礎控除%s）の相続税概算一覧</caption>\n'
        '        <thead>\n          <tr>\n            <th>遺産総額<br>（課税価格）</th>\n            <th>基礎控除</th>\n            <th>課税遺産<br>総額</th>\n            <th>相続税の<br>総額</th>\n            <th>配偶者軽減後<br>（概算納付額）</th>\n            <th>詳細</th>\n          </tr>\n        </thead>\n        <tbody>\n%s\n        </tbody>\n      </table>\n    </div>\n    %s\n    %s\n  </div>\n\n'
        '  <div class="wrap"><div class="orn"><span class="ln"></span><span class="lbl">OTHER COMPOSITIONS</span><span class="ln"></span></div></div>\n\n'
        '  <div class="wrap">\n    <h2>他の相続人構成の早見表</h2>\n    <p class="sec-sub">相続人構成が変わると、法定相続人の数と法定相続分が変わり、基礎控除と税額配分が変わります。</p>\n    <div class="crossgrid">\n      %s\n    </div>\n  </div>\n\n'
        '  <div class="wrap"><div class="orn"><span class="ln"></span><span class="lbl">FAQ</span><span class="ln"></span></div></div>\n\n'
        '  <section id="faq">\n    <div class="wrap">\n      <h2>よくある質問</h2>\n      <p class="sec-sub">%sの相続税について</p>\n      <div class="faq">\n%s\n      </div>\n    </div>\n  </section>\n\n'
        '  <div class="wrap">\n    <div class="linklist">\n      <a href="/sozoku/">相続税かんたん診断</a>\n      <a href="/sozoku/index-definition/">相続準備指数の定義</a>\n      <a href="/hayami/">早見表トップに戻る</a>\n    </div>\n  </div>\n'
    ) % (comp['label'], comp['label'], comp['label'], comp['n'], direct_answer, explain,
         comp['label'], comp['n'], man_label(man_from_yen(comp_kiso(comp))), table_rows, disclaimer_box(), cta_band(),
         cross, comp['label'], faq_details_html(faqs))

    ld = [
        breadcrumb_ld([{'name': 'お金のカルテ', 'path': '/'}, {'name': '相続税早見表', 'path': '/hayami/'}, {'name': comp['label'], 'path': path}]),
        faq_ld(faqs),
    ]
    return {'path': path, 'html': render_page(head_block(title, description, path), ld, body)}


# --- 13. 遺産総額別ページ ---
def build_asset_page(asset_man):
    path = '/hayami/isan-%dman/' % asset_man
    rows = [calc_hayami(asset_man, comp) for comp in COMPOSITIONS]
    lbl = man_label(asset_man)
    title = '遺産%sの相続税はいくら？相続人構成別の早見表｜お金のカルテ' % lbl
    description = '遺産総額%sの場合の相続税を、配偶者＋子・子のみなど代表的な相続人構成6パターンで一覧にした早見表。基礎控除・速算表・配偶者の税額軽減を反映した概算。出典：国税庁No.4152・4155・4158。' % lbl
    rep_row = next(r for r in rows if r['comp']['id'] == 'haigusha-ko2')
    direct_answer = direct_answer_for_comp_asset(asset_man, rep_row['comp'], rep_row)
    faqs = faq_for_asset(asset_man)

    table_rows = '\n'.join(
        '        <tr%s>\n          <td>%s</td>\n          <td class="num">%d人</td>\n          <td class="num">%s</td>\n          <td class="num">%s</td>\n          <td class="num">%s</td>\n          <td class="num">%s</td>\n          <td><a href="/hayami/%s/">%sの一覧 →</a></td>\n        </tr>' % (
            ' class="hl"' if r['comp']['id'] == 'haigusha-ko2' else '',
            r['comp']['label'], r['comp']['n'], man_label(man_from_yen(r['kiso'])), man_label(man_from_yen(r['netEstate'])),
            man_label(jsround(man_from_yen(r['total']))), man_label(jsround(man_from_yen(r['afterSpouse']))),
            r['comp']['id'], r['comp']['shortLabel'])
        for r in rows)

    idx = ASSET_STEPS_MAN.index(asset_man)
    kiso_min = min(comp_kiso(c) for c in COMPOSITIONS)
    kiso_max = max(comp_kiso(c) for c in COMPOSITIONS)

    explain = (
        '<div class="explain">\n'
        '    <p>遺産総額（課税価格）が<strong>%s</strong>の場合、相続税がかかるかどうか・いくらになるかは相続人構成によって大きく変わります。\n'
        '    基礎控除は法定相続人の数によって「3,000万円＋600万円×人数」で決まり、本ページの6構成では\n'
        '    <strong>%s〜%s</strong>の幅があります。\n'
        '    配偶者がいる構成では配偶者の税額軽減（配偶者は法定相続分取得と仮定）により、家族全体の概算納付額が小さくなります。</p>\n'
        '  </div>'
    ) % (lbl, man_label(man_from_yen(kiso_min)), man_label(man_from_yen(kiso_max)))

    cross = []
    if idx > 0:
        p = ASSET_STEPS_MAN[idx - 1]
        cross.append('<a class="crosscard" href="/hayami/isan-%dman/"><p class="t">遺産%sの早見表 →</p><p>1つ下の刻みの相続人構成別一覧</p></a>' % (p, man_label(p)))
    if idx < len(ASSET_STEPS_MAN) - 1:
        p = ASSET_STEPS_MAN[idx + 1]
        cross.append('<a class="crosscard" href="/hayami/isan-%dman/"><p class="t">遺産%sの早見表 →</p><p>1つ上の刻みの相続人構成別一覧</p></a>' % (p, man_label(p)))
    if idx - 3 >= 0:
        p = ASSET_STEPS_MAN[idx - 3]
        cross.append('<a class="crosscard" href="/hayami/isan-%dman/"><p class="t">遺産%sの早見表 →</p><p>相続人構成別の相続税一覧</p></a>' % (p, man_label(p)))
    if idx + 3 < len(ASSET_STEPS_MAN):
        p = ASSET_STEPS_MAN[idx + 3]
        cross.append('<a class="crosscard" href="/hayami/isan-%dman/"><p class="t">遺産%sの早見表 →</p><p>相続人構成別の相続税一覧</p></a>' % (p, man_label(p)))

    body = (
        '\n  <div class="wrap">\n'
        '    <p class="crumbs"><a href="/">お金のカルテ</a> ＞ <a href="/hayami/">相続税早見表</a> ＞ 遺産%s</p>\n'
        '    <p class="eyebrow">相続税の概算早見表</p>\n'
        '    <h1>遺産%sの相続税はいくら？<br>相続人構成別の早見表</h1>\n'
        '    <p class="lead">遺産総額（課税価格）%sの場合の相続税の概算を、配偶者＋子・子のみなど代表的な相続人構成6パターンで一覧にしました。基礎控除・相続税の速算表・配偶者の税額軽減を反映しています。</p>\n'
        '    <div class="answer">\n      <span class="k">DIRECT ANSWER</span>\n      <p>%s</p>\n    </div>\n'
        '    %s\n  </div>\n\n'
        '  <div class="wrap">\n    <div class="wrap-table" tabindex="0" role="region" aria-label="相続税概算一覧表（横スクロール可）">\n      <table class="hayami">\n'
        '        <caption>遺産総額 %s の場合の相続人構成別・相続税概算一覧</caption>\n'
        '        <thead>\n          <tr>\n            <th>相続人構成</th>\n            <th>法定相続人</th>\n            <th>基礎控除</th>\n            <th>課税遺産<br>総額</th>\n            <th>相続税の<br>総額</th>\n            <th>配偶者軽減後<br>（概算納付額）</th>\n            <th>詳細</th>\n          </tr>\n        </thead>\n        <tbody>\n%s\n        </tbody>\n      </table>\n    </div>\n    %s\n    %s\n  </div>\n\n'
        '  <div class="wrap"><div class="orn"><span class="ln"></span><span class="lbl">OTHER AMOUNTS</span><span class="ln"></span></div></div>\n\n'
        '  <div class="wrap">\n    <h2>他の遺産総額の早見表</h2>\n    <p class="sec-sub">遺産総額が変わると、基礎控除を超える金額（課税遺産総額）と税率区分が変わります。</p>\n    <div class="crossgrid">\n      %s\n    </div>\n  </div>\n\n'
        '  <div class="wrap"><div class="orn"><span class="ln"></span><span class="lbl">FAQ</span><span class="ln"></span></div></div>\n\n'
        '  <section id="faq">\n    <div class="wrap">\n      <h2>よくある質問</h2>\n      <p class="sec-sub">遺産%sの相続税について</p>\n      <div class="faq">\n%s\n      </div>\n    </div>\n  </section>\n\n'
        '  <div class="wrap">\n    <div class="linklist">\n      <a href="/sozoku/">相続税かんたん診断</a>\n      <a href="/sozoku/index-definition/">相続準備指数の定義</a>\n      <a href="/hayami/">早見表トップに戻る</a>\n    </div>\n  </div>\n'
    ) % (lbl, lbl, lbl, direct_answer, explain, lbl, table_rows, disclaimer_box(), cta_band(),
         '\n      '.join(cross), lbl, faq_details_html(faqs))

    ld = [
        breadcrumb_ld([{'name': 'お金のカルテ', 'path': '/'}, {'name': '相続税早見表', 'path': '/hayami/'}, {'name': '遺産%s' % lbl, 'path': path}]),
        faq_ld(faqs),
    ]
    return {'path': path, 'html': render_page(head_block(title, description, path), ld, body)}


# --- 14. 索引トップページ ---
def build_index_page():
    path = '/hayami/'
    title = '相続税の概算早見表｜遺産総額・相続人構成でわかる目安一覧｜お金のカルテ'
    description = '遺産総額3,000万円〜3億円×相続人構成6パターンの相続税を早見表で一覧化。基礎控除・速算表・配偶者の税額軽減を反映した概算。あなたの財産で正確に試算するなら相続税かんたん診断へ。'

    comp_cards = '\n      '.join(
        '<a class="crosscard" href="/hayami/%s/"><p class="t">%s →</p><p>遺産3,000万〜3億円の相続税を一覧（法定相続人%d人・基礎控除%s）</p></a>' % (
            c['id'], c['label'], c['n'], man_label(man_from_yen(comp_kiso(c))))
        for c in COMPOSITIONS)
    asset_cards = '\n      '.join(
        '<a class="crosscard" href="/hayami/isan-%dman/"><p class="t">遺産%s →</p><p>相続人構成6パターンの相続税を一覧</p></a>' % (m, man_label(m))
        for m in ASSET_STEPS_MAN)

    faqs = [
        {'q': '相続税の早見表はどのように使えばいいですか？',
         'a': 'まずお手元の財産のおおよその合計に近い「遺産総額別ページ」を開くと、配偶者の有無や子の人数による違いを一覧で比較できます。逆に相続人構成が決まっている場合は「構成別ページ」で金額の刻みごとの目安を確認できます。どちらも概算であり、正確な試算はご自身の財産を入力する診断ツールをご利用ください。'},
        {'q': 'なぜ早見表と実際の申告額が違うことがあるのですか？',
         'a': '早見表は基礎控除・速算表・配偶者の税額軽減という基本要素のみを反映した概算だからです。実際の相続税は、土地建物の評価方法（路線価や小規模宅地等の特例）、生命保険金の非課税枠、二次相続、実際の遺産分割の仕方などによって変動します。正確な金額は税理士等の専門家にご確認ください。'},
        {'q': '相続人構成が早見表の6パターンに当てはまらない場合は？',
         'a': '早見表は代表的な6パターン（配偶者＋子1〜3人、子のみ2〜3人、配偶者のみ）に絞っています。それ以外の構成（親や兄弟姉妹が相続人になる場合など）や、財産の内訳（不動産・現預金・生命保険など）を反映した概算は、無料の相続税かんたん診断でブラウザ内試算できます。'},
    ]

    body = (
        '\n  <div class="wrap">\n'
        '    <p class="crumbs"><a href="/">お金のカルテ</a> ＞ 相続税早見表</p>\n'
        '    <p class="eyebrow">相続税の概算早見表</p>\n'
        '    <h1>相続税の概算早見表<br>遺産総額 × 相続人構成で見る目安</h1>\n'
        '    <p class="lead">遺産総額3,000万円〜3億円（1,000万円刻み・28通り）と、代表的な相続人構成6パターンを組み合わせ、相続税の概算を一覧にしました。基礎控除・相続税の速算表・配偶者の税額軽減を反映しています。</p>\n'
        '    <div class="answer">\n      <span class="k">DIRECT ANSWER</span>\n'
        '      <p>相続税は「財産合計−基礎控除（3,000万円＋600万円×法定相続人の数）」を法定相続分で按分し、10〜55%%の累進税率（速算表）を適用して合計し、配偶者の税額軽減を反映して求めます。本早見表は、この計算を遺産総額と相続人構成の代表的な組み合わせであらかじめ算出した一覧です。出典：国税庁No.4152・4155・4158、%s確認。</p>\n    </div>\n  </div>\n\n'
        '  <div class="wrap">\n    %s\n  </div>\n\n'
        '  <div class="wrap"><div class="orn"><span class="ln"></span><span class="lbl">BY COMPOSITION</span><span class="ln"></span></div></div>\n\n'
        '  <div class="wrap">\n    <h2>相続人構成から探す</h2>\n    <p class="sec-sub">構成ごとに、遺産総額3,000万〜3億円の相続税を一覧表示します。</p>\n    <div class="crossgrid">\n      %s\n    </div>\n  </div>\n\n'
        '  <div class="wrap"><div class="orn"><span class="ln"></span><span class="lbl">BY AMOUNT</span><span class="ln"></span></div></div>\n\n'
        '  <div class="wrap">\n    <h2>遺産総額から探す</h2>\n    <p class="sec-sub">3,000万円〜3億円まで1,000万円刻み・全28通り。各ページで相続人構成6パターンを比較できます。</p>\n    <div class="crossgrid">\n      %s\n    </div>\n  </div>\n\n'
        '  <div class="wrap">\n    %s\n  </div>\n\n'
        '  <div class="wrap"><div class="orn"><span class="ln"></span><span class="lbl">FAQ</span><span class="ln"></span></div></div>\n\n'
        '  <section id="faq">\n    <div class="wrap">\n      <h2>よくある質問</h2>\n      <p class="sec-sub">相続税の早見表について</p>\n      <div class="faq">\n%s\n      </div>\n    </div>\n  </section>\n\n'
        '  <div class="wrap">\n    <div class="linklist">\n      <a href="/sozoku/">相続税かんたん診断</a>\n      <a href="/sozoku/index-definition/">相続準備指数の定義</a>\n    </div>\n  </div>\n'
    ) % (SOURCE_NOTE_DATE, cta_band(), comp_cards, asset_cards, disclaimer_box(), faq_details_html(faqs))

    ld = [
        breadcrumb_ld([{'name': 'お金のカルテ', 'path': '/'}, {'name': '相続税早見表', 'path': path}]),
        faq_ld(faqs),
    ]
    return {'path': path, 'html': render_page(head_block(title, description, path, og_type='website'), ld, body)}


# --- 15. 書き出し ---
def write_page(page_path, html):
    rel = page_path[len('/hayami/'):].rstrip('/')
    d = OUT_DIR if rel == '' else os.path.join(OUT_DIR, *rel.split('/'))
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'index.html'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(html)


def build_sitemap(urls):
    body = '\n'.join(
        '  <url>\n    <loc>%s%s</loc>\n    <lastmod>%s</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>%s</priority>\n  </url>' % (
            SITE_ORIGIN, u, SOURCE_NOTE_DATE, '0.7' if u == '/hayami/' else '0.5')
        for u in urls)
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n' % body


def main():
    print('=== お金のカルテ 相続税早見表 pSEO ビルド開始（Python） ===')
    check = run_self_check()
    print('[自己検算OK] 遺産%d万円・配偶者+子2人 → 基礎控除%d万円 / 課税遺産%d万円 / 総額%d万円 / 配偶者軽減後%d万円' % (
        check['assetMan'], check['kiso'], check['netEstate'], check['total'], check['afterSpouse']))

    if os.path.isdir(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR, exist_ok=True)

    pages = [build_index_page()]
    for comp in COMPOSITIONS:
        pages.append(build_composition_page(comp))
    for asset_man in ASSET_STEPS_MAN:
        pages.append(build_asset_page(asset_man))

    for p in pages:
        write_page(p['path'], p['html'])

    urls = [p['path'] for p in pages]
    with open(os.path.join(OUT_DIR, 'sitemap-hayami.xml'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(build_sitemap(urls))

    print('[生成完了] ページ数: %d（索引1 + 構成別%d + 総額別%d）' % (len(pages), len(COMPOSITIONS), len(ASSET_STEPS_MAN)))
    print('[出力先] %s' % OUT_DIR)
    print('[sitemap] %s' % os.path.join(OUT_DIR, 'sitemap-hayami.xml'))
    print('=== ビルド完了 ===')


if __name__ == '__main__':
    main()

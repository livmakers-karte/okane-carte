#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
お金のカルテ /fudosan/ ─ pSEO（プログラマティックSEO）静的ページ量産ビルドスクリプト
=============================================================================
実行: python scripts/build_fudosan.py
     （カレントディレクトリ = リポジトリ直下 C:\\Users\\NOBU\\okane-carte を想定。
      ただしスクリプト自身の場所からの相対解決も併用するため、どこから実行しても動作する）

依存: Python3 標準ライブラリのみ（json, os, pathlib, datetime, hashlib）。外部API・外部CDNなし。

生成物:
  fudosan/p/assets/pseo.css              … 共有CSS（案Cトークン。全pSEOページがlinkする）
  fudosan/p/zanka/{structure}-{age}/index.html   … 24ページ（構造4 × 築年6区分）
  fudosan/p/zanka/index.html             … 残価率マトリクスのハブ
  fudosan/p/rimawari/{area}-{ageBand}/index.html … 20ページ（エリア5 × 築年帯4区分）
  fudosan/p/rimawari/index.html          … 利回りマトリクスのハブ
  fudosan/p/index.html                   … pSEO早見表トップ（両系統への導線）
  fudosan/p/_urls.txt                    … 生成した全URL一覧（1行1URL・絶対URL）

【単一の真実】
数値は必ず fudosan/config.json の data.* を読み込んで使う（ハードコピー禁止）。
このスクリプトが所有するのは scripts/build_fudosan.py と fudosan/p/ 配下のみ。
fudosan/index.html・fudosan/config.json・root の sitemap.xml/robots.txt/llms.txt/index.html は一切変更しない。
=============================================================================
"""

import json
import os
from pathlib import Path
from datetime import date

# ---------------------------------------------------------------------------
# 0. パス解決（スクリプト相対・リポジトリ相対の両対応）
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent  # scripts/ の親 = okane-carte 直下
FUDOSAN_DIR = REPO_ROOT / "fudosan"
CONFIG_PATH = FUDOSAN_DIR / "config.json"
P_DIR = FUDOSAN_DIR / "p"
SITE_ORIGIN = "https://okane-carte.jp"
BUILD_DATE = "2026-07-07"  # config.sources の確認日と統一

if not CONFIG_PATH.exists():
    raise SystemExit(f"[ERROR] config.json が見つかりません: {CONFIG_PATH}")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

D = CONFIG["data"]
STRUCTURES = D["structures"]           # list of {key,label,usefulLife,replacementCost[min,max],koteiRatio}
AGE_BANDS = D["ageBands"]              # list of {key,label,minY,maxY,liquidity}
AREAS = D["areas"]                     # list of {key,label,liquidity,landPrice[min,max],shakuchiKen}
CAP_RATES = D["capRates"]              # area -> income -> ageBandKey -> [min,max]
TAX_RULES = D["taxRules"]
SALVAGE_FLOOR = D["salvageFloor"]
OPEX_RATIO = D["opexRatio"]
SOURCES = CONFIG["sources"]
DISCLAIMER = CONFIG["disclaimer"]

STRUCT_BY_KEY = {s["key"]: s for s in STRUCTURES}
AREA_BY_KEY = {a["key"]: a for a in AREAS}
AGEBAND_BY_KEY = {b["key"]: b for b in AGE_BANDS}


# ---------------------------------------------------------------------------
# 1. ユーティリティ
# ---------------------------------------------------------------------------
def esc(s):
    """HTMLエスケープ（最小限）。"""
    if s is None:
        return ""
    s = str(s)
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def fmt_yen(v):
    """円 → 億/万 表記（億がある場合は「◯億 ◯,◯◯◯万円」、それ以外は「◯万円」「◯円」）。"""
    v = round(v)
    if v >= 1e8:
        oku = v // int(1e8)
        man = round((v - oku * int(1e8)) / 1e4)
        if man > 0:
            return f"{oku}億 {man:,}万円"
        return f"{oku}億円"
    if v >= 1e4:
        return f"{round(v / 1e4):,}万円"
    return f"{v:,}円"


def fmt_range(lo, hi):
    if round(lo) == round(hi):
        return fmt_yen(lo)
    return f"{fmt_yen(lo)} 〜 {fmt_yen(hi)}"


def fmt_pergm2(v):
    """円/㎡ の整数表記。"""
    return f"{round(v):,}円/㎡"


def pct1(v):
    """小数の%を小数1桁表記（例 4.8）。すでに%の数値(例 4.8)ならそのまま。"""
    return f"{v:.1f}"


# ---------------------------------------------------------------------------
# 2. 残価率・積算の計算コア（fudosan/index.html の compute() の建物部分と同一ロジック）
# ---------------------------------------------------------------------------
def residual_rate(useful_life, built_years):
    """残価率 = clamp((耐用年数-築年)/耐用年数, salvageFloor, 1)。"""
    return clamp((useful_life - built_years) / useful_life, SALVAGE_FLOOR, 1)


# zanka（残価率早見）で使う築年ポイント（6区分）。
# ageBands（4区分）はrimawari側で使用。zankaは構造×築年の粒度をより細かく見せるため独自定義。
PAGE_AGES = [
    {"years": 0, "label": "新築", "slug": "shinchiku"},
    {"years": 5, "label": "築5年", "slug": "5nen"},
    {"years": 10, "label": "築10年", "slug": "10nen"},
    {"years": 15, "label": "築15年", "slug": "15nen"},
    {"years": 20, "label": "築20年", "slug": "20nen"},
    {"years": 25, "label": "築25年", "slug": "25nen"},
]


def ageband_of_years(years):
    for b in AGE_BANDS:
        if b["minY"] <= years <= b["maxY"]:
            return b
    return AGE_BANDS[-1]


# ---------------------------------------------------------------------------
# 3. 共有CSS（案Cトークン・最小限のレイアウト）
# ---------------------------------------------------------------------------
PSEO_CSS = """/* =============================================================================
 * fudosan/p/ 共有CSS ─ 案Cトークン（等高線 × スレートティール × 陶土の印章）
 * fudosan/index.html の :root と同一トークンをセルフホストで共有。
 * ============================================================================= */
@font-face{font-family:"Shippori Mincho";src:url("/assets/fonts/ShipporiMincho-Bold.subset.woff2") format("woff2");font-weight:700;font-display:swap}
@font-face{font-family:"Marcellus";src:url("/assets/fonts/Marcellus-400.woff2") format("woff2");font-weight:400;font-display:swap}
@font-face{font-family:"Cormorant";src:url("/assets/fonts/Cormorant-500.woff2") format("woff2");font-weight:500;font-display:swap}
@font-face{font-family:"Cormorant";src:url("/assets/fonts/Cormorant-600.woff2") format("woff2");font-weight:600;font-display:swap}

:root{
  --bg:#F6F1E7; --bg-2:#ECE5D6; --paper:#FCFAF4; --bg-grid:#E4DCC9;
  --teal:#1E4A4E; --teal-2:#366B6C; --teal-3:#5C8A86; --teal-ink:#14383B;
  --clay:#C1663C; --clay-2:#A9542F; --clay-soft:#F0E0D3;
  --gold:#B08D45; --gold-hi:#D6BE84;
  --ink:#2B2A26; --muted:#6D685E;
  --line:#D9CFBB; --line-2:#C7BCA3;
  --danger:#B4472E; --ok:#2F6B4F;
  --radius:12px; --radius-sm:8px;
  --shadow-card:0 10px 30px rgba(30,74,78,.08); --shadow-soft:0 1px 0 rgba(30,74,78,.04);
  --serif-jp:"Shippori Mincho","Yu Mincho","YuMincho","Hiragino Mincho ProN","Hiragino Mincho Pro",serif;
  --serif-en:"Marcellus",var(--serif-jp);
  --num:"Cormorant","Marcellus",Georgia,serif;
  --sans:system-ui,-apple-system,"Segoe UI","Hiragino Kaku Gothic ProN","Yu Gothic UI","Meiryo",sans-serif;
  --mono:"DIN Alternate","Roboto Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;font-family:var(--sans);color:var(--ink);line-height:1.8;letter-spacing:.01em;
  background:
    radial-gradient(1000px 480px at 88% -8%, rgba(30,74,78,.06), transparent 60%),
    radial-gradient(760px 420px at -4% 3%, rgba(193,102,60,.04), transparent 58%),
    repeating-linear-gradient(0deg, transparent 0 27px, var(--bg-grid) 27px 28px),
    repeating-linear-gradient(90deg, transparent 0 27px, var(--bg-grid) 27px 28px),
    var(--bg);
  background-size:auto,auto,100% 28px,28px 100%,auto;min-height:100vh;display:flex;flex-direction:column}
.wrap{max-width:880px;margin:0 auto;padding:0 22px;width:100%}
h1,h2,h3{font-family:var(--serif-jp);color:var(--teal);letter-spacing:.02em;line-height:1.5;font-weight:700}
a{color:var(--teal-2)}
::selection{background:var(--clay-soft)}
:focus-visible{outline:2px solid var(--teal);outline-offset:2px;border-radius:3px}

/* HEADER */
header.site{padding:16px 0;border-bottom:1px solid var(--line);background:rgba(246,241,231,.7)}
header.site .wrap{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:10px;color:var(--teal);text-decoration:none}
.brand .mark{font-family:var(--serif-jp);font-size:18px;letter-spacing:.05em;line-height:1.1;color:var(--teal)}
.brand .sub{font-size:10.5px;color:var(--muted);letter-spacing:.1em}
.navlinks{display:flex;gap:14px;flex-wrap:wrap;justify-content:flex-end}
.navlink{font-family:var(--serif-en);color:var(--teal);text-decoration:none;font-size:12px;letter-spacing:.04em;white-space:nowrap;border-bottom:1px solid transparent;padding-bottom:1px}
.navlink:hover{border-bottom-color:var(--clay)}

main{flex:1}
.pad{padding:32px 0}

/* 可視の写真バンド（全面多用） */
.photo-band{position:relative;overflow:hidden;height:clamp(150px,26vw,240px)}
.photo-band img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;filter:saturate(1.03)}
.photo-band::after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(20,56,59,.78),rgba(20,56,59,.34) 55%,rgba(20,56,59,.06))}
.photo-band .cap{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;z-index:2;color:#fff}
.photo-band .cap .inner{max-width:880px;margin:0 auto;padding:0 22px;width:100%}
.photo-band .cap .e{font-family:var(--serif-en);font-size:10.5px;letter-spacing:.22em;color:var(--gold-hi);display:inline-flex;align-items:center;gap:8px}
.photo-band .cap .e::before{content:"";width:22px;height:1px;background:var(--gold-hi)}
.photo-band .cap .t{font-family:var(--serif-jp);font-size:clamp(17px,3.2vw,25px);margin:7px 0 0;line-height:1.5;text-shadow:0 2px 12px rgba(0,0,0,.3)}
.crumbs{font-size:12px;color:var(--muted);margin:16px 0 4px}
.crumbs a{color:var(--muted);text-decoration:underline;text-underline-offset:2px}
.crumbs a:hover{color:var(--teal)}

.eyebrow{color:var(--clay-2);font-size:11.5px;letter-spacing:.18em;font-weight:700;margin:12px 0 12px;display:inline-flex;align-items:center;gap:9px}
.eyebrow::before{content:"";width:24px;height:1px;background:linear-gradient(90deg,transparent,var(--clay))}
h1{font-size:clamp(22px,4.6vw,32px);margin:0 0 14px}
h2{font-size:clamp(19px,3.4vw,25px);margin:0 0 10px}
p.lead{color:var(--ink);font-size:clamp(14px,2.1vw,15.5px);max-width:42em;margin:0 0 16px}

/* 直答ブロック（GEO） */
.answer{position:relative;background:var(--paper);border:1px solid var(--line);border-left:4px solid var(--clay);
  border-radius:var(--radius);padding:16px 18px;box-shadow:var(--shadow-card);margin:8px 0 22px;max-width:44em}
.answer .k{font-family:var(--serif-en);font-size:10.5px;letter-spacing:.14em;color:var(--clay-2);text-transform:uppercase;display:block;margin-bottom:5px}
.answer p{margin:0;font-size:13.5px;color:var(--ink);line-height:1.75}
.answer .src{display:block;margin-top:8px;font-size:11px;color:var(--muted)}

section{padding:8px 0}
.sec-sub{color:var(--muted);font-size:13px;margin:2px 0 14px}

/* 区切り .orn（測量基準点） */
.orn{display:flex;align-items:center;gap:12px;color:var(--teal-3);margin:28px 0 16px}
.orn .ln{flex:1;height:1px;background:linear-gradient(90deg,transparent,var(--teal-3),transparent)}
.orn .mk{width:14px;height:14px;flex:0 0 auto;border-radius:50%;border:1.5px solid var(--clay)}
.orn .lbl{font-family:var(--serif-en);font-size:11.5px;letter-spacing:.14em;color:var(--teal-2);white-space:nowrap}

.card{background:var(--paper);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow-card)}
.card-pad{padding:20px 20px 18px}

/* 表 */
.wrap-table{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:0 0 18px}
table.zk{width:100%;border-collapse:collapse;font-size:13.5px;margin:6px 0}
table.zk caption{text-align:left;font-size:12px;color:var(--muted);margin-bottom:8px}
table.zk th,table.zk td{border-bottom:1px solid var(--line);padding:9px 8px;text-align:right;white-space:nowrap}
table.zk th:first-child,table.zk td:first-child{text-align:left;color:var(--ink)}
table.zk thead th{color:var(--teal);font-family:var(--serif-jp);font-weight:700;border-bottom:1px solid var(--teal-3);background:var(--bg-2)}
table.zk tbody tr:hover{background:var(--bg-2)}
table.zk tbody tr.hl{background:var(--clay-soft)}
table.zk tbody tr.hl td:first-child{font-weight:700;color:var(--teal)}
.num{font-family:var(--num);font-weight:600}

/* マトリクス（ハブ用） */
.matrix{width:100%;border-collapse:collapse;font-size:13px;margin:10px 0}
.matrix th,.matrix td{border:1px solid var(--line);padding:8px;text-align:center}
.matrix thead th{background:var(--bg-2);color:var(--teal);font-family:var(--serif-jp)}
.matrix tbody th{background:var(--bg-2);color:var(--teal);text-align:left;padding-left:12px;font-family:var(--serif-jp)}
.matrix td a{display:block;color:var(--teal-2);text-decoration:none;font-size:12.5px;padding:4px 2px}
.matrix td a:hover{color:var(--clay-2);text-decoration:underline}

/* クロスリンクカード */
.crossgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin:14px 0}
.crosscard{display:block;background:var(--paper);border:1px solid var(--line);border-left:4px solid var(--teal-3);border-radius:var(--radius-sm);
  padding:12px 14px;text-decoration:none;color:inherit;font-size:12.5px;transition:transform .12s,border-color .15s}
.crosscard:hover{transform:translateY(-2px);border-color:var(--teal)}
.crosscard .t{font-family:var(--serif-jp);font-size:14px;color:var(--teal);margin:0 0 4px}
.crosscard p{margin:0;color:var(--muted)}

.note-box{background:var(--clay-soft);border:1px solid var(--line-2);border-radius:var(--radius-sm);padding:12px 15px;font-size:12px;color:var(--ink);line-height:1.75;margin:14px 0}
.note-box strong{color:var(--clay-2)}
.disclaimer-box{margin:16px 0;background:var(--bg-2);border:1px solid var(--line-2);border-radius:var(--radius-sm);padding:13px 15px;font-size:11.5px;color:var(--ink);line-height:1.8}
.disclaimer-box strong{color:var(--teal-2)}

/* CTA帯 */
.cta-band{display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between;
  background:linear-gradient(180deg,var(--teal-2),var(--teal));border-radius:var(--radius);padding:20px 22px;color:#eef3f2;margin:22px 0}
.cta-band h3{color:#fff;font-size:16.5px;margin:0 0 4px}
.cta-band p{color:#d7e6e4;font-size:12.5px;margin:0;max-width:36em}
.cta{font-family:var(--sans);font-size:14px;font-weight:700;border:none;border-radius:var(--radius-sm);padding:12px 20px;cursor:pointer;
  transition:transform .12s,box-shadow .15s;text-decoration:none;display:inline-flex;align-items:center;justify-content:center;gap:8px;white-space:nowrap}
.cta.clay{background:linear-gradient(120deg,var(--clay-2),var(--clay));color:#fff}
.cta.clay:hover{transform:translateY(-2px);box-shadow:0 8px 20px rgba(193,102,60,.28)}
.cta.ghost{background:transparent;color:#eaf1ef;border:1px solid rgba(255,255,255,.4)}
.cta.ghost:hover{border-color:#fff}

/* FAQ */
#faq{padding:24px 0}
.faq details{border-bottom:1px solid var(--line)}
.faq summary{cursor:pointer;padding:13px 26px 13px 4px;font-family:var(--serif-jp);font-size:14px;color:var(--teal);position:relative;list-style:none}
.faq summary::-webkit-details-marker{display:none}
.faq summary::after{content:"＋";position:absolute;right:6px;top:12px;color:var(--clay);font-size:14px}
.faq details[open] summary::after{content:"－"}
.faq .a{padding:0 4px 15px;font-size:13px;color:var(--ink);line-height:1.85}

.linklist{display:flex;flex-wrap:wrap;gap:8px 16px;margin:0 0 8px;font-size:12.5px}
.linklist a{text-decoration:underline;text-underline-offset:2px}

/* FOOTER */
footer.site{position:relative;background:var(--teal-ink);color:#c7d8d6;padding:26px 0 22px;margin-top:28px;font-size:11.5px;line-height:1.85}
footer.site a{color:var(--gold-hi);text-decoration:none}
footer.site a:hover{text-decoration:underline}
.footlinks{display:flex;flex-wrap:wrap;gap:8px 16px;margin:0 0 12px;font-size:12px}
.foot-discl{color:#9db3b0;margin:6px 0 0}

@media(max-width:640px){
  table.zk{font-size:12px}
  .matrix{font-size:11px}
  .pad{padding:24px 0}
}
@media(max-width:400px){
  .brand .mark{font-size:16px}
}
@media (prefers-reduced-motion: reduce){
  *{scroll-behavior:auto !important}
}
"""


# ---------------------------------------------------------------------------
# 4. HTML部品（head / header / footer / crumb-ld / faq-ld）
# ---------------------------------------------------------------------------
CSP = (
    "default-src 'self'; base-uri 'self'; object-src 'none'; img-src 'self' data:; "
    "style-src 'self' 'unsafe-inline'; font-src 'self'; script-src 'self' 'unsafe-inline'; "
    "frame-src 'none'; connect-src 'self'; form-action 'self'; frame-ancestors 'none';"
)
FRAME_BUST_JS = "if (window.top !== window.self) { window.top.location = window.self.location; }"


def rel_css_path(depth):
    """このページから fudosan/p/assets/pseo.css への相対パス。
    depth = このページのディレクトリが fudosan/p/ から何階層下にあるか。
    例: fudosan/p/zanka/wood-shinchiku/index.html は depth=2 → ../../assets/pseo.css
        fudosan/p/zanka/index.html は depth=1 → ../assets/pseo.css
        fudosan/p/index.html は depth=0 → ./assets/pseo.css
    """
    if depth <= 0:
        return "./assets/pseo.css"
    return "../" * depth + "assets/pseo.css"


def head_block(title, description, canonical_path, css_rel, og_type="article"):
    canonical = f"{SITE_ORIGIN}{canonical_path}"
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta http-equiv="Content-Security-Policy" content="{CSP}">
<meta name="referrer" content="strict-origin-when-cross-origin">
<!-- 公開前は noindex。go-live 時に index, follow へ一括切替（オーケストレーター担当）。 -->
<meta name="robots" content="index, follow">
<meta name="google-site-verification" content="rRCFvRt35WuMDgaJUTpLJkmSAA1NzeVrREi59gar3B4">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="お金のカルテ">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE_ORIGIN}/fudosan/assets/ogp.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<link rel="stylesheet" href="{css_rel}">"""


def header_block(css_rel_root):
    """css_rel_root は使わない（linkはhead側）。ヘッダーは相対リンクでトップ/診断へ。"""
    return """<header class="site">
  <div class="wrap">
    <a class="brand" href="/fudosan/">
      <span><span class="mark">お金のカルテ</span><br><span class="sub">不動産 早見表（pSEO）</span></span>
    </a>
    <nav class="navlinks">
      <a class="navlink" href="/fudosan/#shindan">診断する →</a>
      <a class="navlink" href="/fudosan/index-definition/">指数の定義</a>
      <a class="navlink" href="/fudosan/sources/">データ出典</a>
    </nav>
  </div>
</header>"""


def footer_block():
    takken = esc(DISCLAIMER["takken"])
    zeirishi = esc(DISCLAIMER["zeirishi"])
    return f"""<footer class="site">
  <div class="wrap">
    <div class="disclaimer-box"><strong>宅地建物取引業法について：</strong> {takken}</div>
    <div class="disclaimer-box"><strong>税理士法について：</strong> {zeirishi}</div>
    <div class="footlinks">
      <a href="/">お金のカルテ トップ</a>
      <a href="/fudosan/">不動産かんたん評価診断</a>
      <a href="/fudosan/index-definition/">不動産カルテ指数の定義</a>
      <a href="/fudosan/sources/">データ出典</a>
      <a href="/fudosan/p/">早見表トップ</a>
      <a href="/sozoku/">相続のカルテ</a>
    </div>
    <p class="foot-discl">© <span id="year"></span> リブメーカーズ株式会社（LIVmakers Co., Ltd.）／ お金のカルテ ／ 本サイトは公開データに基づく概算の情報提供であり、宅地建物取引業者の査定・不動産鑑定・税務助言ではありません。正式な判断は専門家にご確認ください。</p>
  </div>
</footer>
<script>document.getElementById('year').textContent=String(new Date().getFullYear());{FRAME_BUST_JS}</script>"""


def breadcrumb_ld(items):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": it["name"], "item": f"{SITE_ORIGIN}{it['path']}"}
            for i, it in enumerate(items)
        ],
    }


def faq_ld(qas):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": qa["q"], "acceptedAnswer": {"@type": "Answer", "text": qa["a"]}}
            for qa in qas
        ],
    }


def ld_script(obj):
    return f'<script type="application/ld+json">\n{json.dumps(obj, ensure_ascii=False, indent=2)}\n</script>'


def band_block(img, cap, eyebrow="OKANE CARTE / FUDOSAN"):
    # ルート相対（/fudosan/...）＝ローカルプレビューでも本番でも読み込める・サブディレクトリ固定。
    return f"""<div class="photo-band">
  <img src="/fudosan/assets/img/{img}" alt="" width="1600" height="640" loading="eager">
  <div class="cap"><div class="inner"><span class="e">{esc(eyebrow)}</span><p class="t">{esc(cap)}</p></div></div>
</div>"""


def render_page(head, ld_list, body, css_rel, band_img="townscape.webp", band_cap="不動産の価値を、公開データで匿名概算する。", band_e="OKANE CARTE / FUDOSAN"):
    ld_scripts = "\n".join(ld_script(o) for o in ld_list)
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
{head}
{ld_scripts}
</head>
<body>
{header_block(css_rel)}
{band_block(band_img, band_cap, band_e)}
<main>
{body}
</main>
{footer_block()}
</body>
</html>
"""


def faq_block(faqs):
    items = "\n".join(
        f'''        <details>
          <summary>{esc(qa["q"])}</summary>
          <div class="a">{esc(qa["a"])}</div>
        </details>'''
        for qa in faqs
    )
    return f"""<section id="faq">
    <div class="wrap">
      <h2>よくある質問</h2>
      <div class="faq">
{items}
      </div>
    </div>
  </section>"""


# ---------------------------------------------------------------------------
# 5. (a) 残価率 早見ページ ─ 構造4種 × 築年6区分 = 24ページ
# ---------------------------------------------------------------------------
def build_zanka_page(struct, age_point):
    st_key = struct["key"]
    st_label = struct["label"]
    useful_life = struct["usefulLife"]
    rc_lo, rc_hi = struct["replacementCost"]
    kotei_ratio = struct["koteiRatio"]
    years = age_point["years"]
    age_label = age_point["label"]
    slug = f"{st_key}-{age_point['slug']}"
    path = f"/fudosan/p/zanka/{slug}/"

    residual = residual_rate(useful_life, years)
    residual_pct = round(residual * 100)
    per_m2_lo = rc_lo * residual
    per_m2_hi = rc_hi * residual

    # 例：延床100㎡での建物概算
    example_area = 100
    ex_lo = per_m2_lo * example_area
    ex_hi = per_m2_hi * example_area

    title = f"{st_label}・{age_label}の建物残価率と評価額の目安｜不動産 早見表｜お金のカルテ"
    description = (
        f"{st_label}（法定耐用年数{useful_life}年）・{age_label}の建物残価率は約{residual_pct}%。"
        f"再調達価格レンジから、延床1㎡あたりの建物評価と延床100㎡での概算を早見表で提示。出典：国税庁。"
    )

    direct_answer = (
        f"{st_label}（法定耐用年数{useful_life}年）で{age_label}の建物の残価率は、"
        f"(耐用年数−築年数)÷耐用年数の計算で約{residual_pct}%が目安です。"
        f"再調達価格{fmt_pergm2(rc_lo)}〜{fmt_pergm2(rc_hi)}に残価率を掛けると、"
        f"延床1㎡あたり{fmt_pergm2(per_m2_lo)}〜{fmt_pergm2(per_m2_hi)}が建物評価の概算レンジです。"
        f"出典：国税庁「建物の標準的な建築価額表」・法定耐用年数省令。"
    )

    faqs = [
        {
            "q": f"{st_label}の法定耐用年数は何年ですか？",
            "a": (
                f"{st_label}の法定耐用年数（住宅用）は{useful_life}年です。"
                f"国税庁の耐用年数省令 別表第一に基づく制度値で、木造22年・軽量鉄骨造19〜27年・重量鉄骨造34年・"
                f"鉄筋コンクリート造（RC・SRC）47年と構造により異なります。"
            ),
        },
        {
            "q": f"{age_label}の{st_label}は、まだ価値が残っていますか？",
            "a": (
                f"残価率の目安は約{residual_pct}%です。(法定耐用年数−築年数)÷法定耐用年数で計算し、"
                f"耐用年数を超えても再調達価格の{round(SALVAGE_FLOOR*100)}%を名目上の残価として残す設計です"
                f"（実際の取引では建物価値がほぼ0とみなされることもあります）。"
            ),
        },
        {
            "q": "延床100㎡の場合、建物の評価額はいくらくらいになりますか？",
            "a": (
                f"再調達価格レンジ{fmt_pergm2(rc_lo)}〜{fmt_pergm2(rc_hi)}に、延床100㎡と残価率約{residual_pct}%を掛けると、"
                f"概算で{fmt_range(ex_lo, ex_hi)}が建物評価の目安です。土地の評価は別途エリアの㎡単価で計算します。"
            ),
        },
        {
            "q": "この数値はそのまま査定額に使えますか？",
            "a": (
                "使えません。本ページは構造別・築年別の平均的な公開データによる概算レンジで、"
                "個別物件の状態（維持管理・リフォーム履歴・再建築可否など）は反映していません。"
                "正確な評価は宅地建物取引業者・不動産鑑定士にご確認ください。"
            ),
        },
    ]

    # 同一構造・他築年へのクロスリンク
    same_struct_links = "\n      ".join(
        f'<a class="crosscard" href="/fudosan/p/zanka/{st_key}-{ap["slug"]}/"><p class="t">{esc(st_label)}・{esc(ap["label"])} →</p><p>残価率と評価額の目安</p></a>'
        for ap in PAGE_AGES
        if ap["slug"] != age_point["slug"]
    )
    # 同一築年・他構造へのクロスリンク
    same_age_links = "\n      ".join(
        f'<a class="crosscard" href="/fudosan/p/zanka/{s["key"]}-{age_point["slug"]}/"><p class="t">{esc(s["label"])}・{esc(age_label)} →</p><p>残価率と評価額の目安</p></a>'
        for s in STRUCTURES
        if s["key"] != st_key
    )

    body = f"""
  <div class="wrap">
    <p class="crumbs"><a href="/">お金のカルテ</a> ＞ <a href="/fudosan/">不動産かんたん評価診断</a> ＞ <a href="/fudosan/p/">早見表</a> ＞ <a href="/fudosan/p/zanka/">建物残価率</a> ＞ {esc(st_label)}・{esc(age_label)}</p>
    <p class="eyebrow">建物残価率 早見表</p>
    <h1>{esc(st_label)}・{esc(age_label)}の<br>建物残価率と評価額の目安</h1>
    <p class="lead">{esc(st_label)}（法定耐用年数{useful_life}年）で{esc(age_label)}の建物について、残価率と延床1㎡あたりの評価額レンジ、延床100㎡での概算例を早見表にまとめました。すべて概算・目安です。</p>
    <div class="answer">
      <span class="k">Direct Answer</span>
      <p>{esc(direct_answer)}</p>
      <span class="src">出典：国税庁「建物の標準的な建築価額表」／耐用年数省令 別表第一。確認日 {BUILD_DATE}。</span>
    </div>
  </div>

  <div class="wrap">
    <div class="card card-pad">
      <div class="wrap-table">
        <table class="zk">
          <caption>{esc(st_label)}・{esc(age_label)}（法定耐用年数{useful_life}年・残価率 約{residual_pct}%）の建物評価早見表</caption>
          <thead>
            <tr><th>項目</th><th>金額・数値の目安</th></tr>
          </thead>
          <tbody>
            <tr><td>構造</td><td class="num">{esc(st_label)}</td></tr>
            <tr><td>法定耐用年数</td><td class="num">{useful_life}年</td></tr>
            <tr><td>築年数</td><td class="num">{esc(age_label)}（{years}年）</td></tr>
            <tr class="hl"><td>残価率の目安</td><td class="num">約{residual_pct}%</td></tr>
            <tr><td>再調達価格レンジ（円/㎡）</td><td class="num">{fmt_pergm2(rc_lo)} 〜 {fmt_pergm2(rc_hi)}</td></tr>
            <tr class="hl"><td>建物評価レンジ（延床1㎡あたり）</td><td class="num">{fmt_pergm2(per_m2_lo)} 〜 {fmt_pergm2(per_m2_hi)}</td></tr>
            <tr class="hl"><td>例：延床100㎡での建物概算</td><td class="num">{fmt_range(ex_lo, ex_hi)}</td></tr>
            <tr><td>固定資産税評価の目安割合</td><td class="num">再調達価格の約{round(kotei_ratio*100)}%</td></tr>
          </tbody>
        </table>
      </div>
      <div class="note-box"><strong>計算式：</strong> 残価率 ＝ (法定耐用年数 − 築年数) ÷ 法定耐用年数（下限{round(SALVAGE_FLOOR*100)}%）。建物評価 ＝ 延床面積 × 再調達価格（円/㎡） × 残価率。土地の評価は含みません。</div>
      <div class="disclaimer-box"><strong>この早見表について：</strong> {esc(DISCLAIMER["standardsNote"])} {esc(DISCLAIMER["method"])}</div>
    </div>
  </div>

  <div class="wrap">
    <div class="cta-band">
      <div>
        <h3>あなたの物件で、土地も含めて概算する</h3>
        <p>早見表は構造・築年の平均値です。エリア・面積・収益状況まで入力すると、積算・収益・税務の3レイヤーで「不動産カルテ指数」を無料・匿名で発行できます。</p>
      </div>
      <a class="cta clay" href="/fudosan/#shindan">不動産カルテを発行する →</a>
    </div>
  </div>

  <div class="wrap"><div class="orn"><span class="ln"></span><span class="mk"></span><span class="lbl">SAME STRUCTURE</span><span class="ln"></span></div></div>
  <div class="wrap">
    <h2>{esc(st_label)}の他の築年数</h2>
    <p class="sec-sub">同じ構造で、築年数による残価率の違いを比較できます。</p>
    <div class="crossgrid">
      {same_struct_links}
    </div>
  </div>

  <div class="wrap"><div class="orn"><span class="ln"></span><span class="mk"></span><span class="lbl">SAME AGE</span><span class="ln"></span></div></div>
  <div class="wrap">
    <h2>{esc(age_label)}の他の構造</h2>
    <p class="sec-sub">同じ築年数で、構造による残価率・評価額の違いを比較できます。</p>
    <div class="crossgrid">
      {same_age_links}
    </div>
  </div>

  {faq_block(faqs)}

  <div class="wrap">
    <div class="linklist">
      <a href="/fudosan/#shindan">不動産かんたん評価診断（無料・匿名）</a>
      <a href="/fudosan/index-definition/">不動産カルテ指数の定義</a>
      <a href="/fudosan/sources/">データ出典</a>
      <a href="/fudosan/p/zanka/">建物残価率マトリクスに戻る</a>
    </div>
  </div>
"""

    head = head_block(title, description, path, rel_css_path(2))
    ld_list = [
        breadcrumb_ld(
            [
                {"name": "お金のカルテ", "path": "/"},
                {"name": "不動産かんたん評価診断", "path": "/fudosan/"},
                {"name": "早見表", "path": "/fudosan/p/"},
                {"name": "建物残価率", "path": "/fudosan/p/zanka/"},
                {"name": f"{st_label}・{age_label}", "path": path},
            ]
        ),
        faq_ld(faqs),
    ]
    zpic = {"木造": "house-street.webp", "軽量鉄骨造": "suburban-home.webp",
            "重量鉄骨造（S造）": "apartment-building.webp",
            "鉄筋コンクリート造（RC・SRC）": "city-building.webp"}.get(st_label, "house-white.webp")
    html = render_page(head, ld_list, body, rel_css_path(2),
                       band_img=zpic, band_cap=f"{st_label}・{age_label}｜建物の残価率と評価額の目安",
                       band_e="ZANKA / BUILDING VALUE")
    return path, html


def build_zanka_hub():
    path = "/fudosan/p/zanka/"
    title = "建物残価率マトリクス｜構造×築年で早見｜お金のカルテ"
    description = "木造・軽量鉄骨・重量鉄骨・RCの4構造 × 新築〜築25年の6区分、全24パターンの建物残価率と評価額の目安を一覧化した早見表マトリクス。"

    direct_answer = (
        "建物の残価率は構造（法定耐用年数）と築年数で決まります。"
        "木造22年・軽量鉄骨27年・重量鉄骨34年・RC/SRC47年の法定耐用年数を基準に、"
        "(耐用年数−築年数)÷耐用年数で概算します。下のマトリクスから構造×築年の組み合わせを選ぶと、"
        "残価率と延床1㎡あたりの評価額レンジが確認できます。"
    )

    # マトリクス表
    header_cells = "".join(f"<th>{esc(ap['label'])}</th>" for ap in PAGE_AGES)
    rows = []
    for s in STRUCTURES:
        cells = "".join(
            f'<td><a href="/fudosan/p/zanka/{s["key"]}-{ap["slug"]}/">{round(residual_rate(s["usefulLife"], ap["years"])*100)}%</a></td>'
            for ap in PAGE_AGES
        )
        rows.append(f'<tr><th>{esc(s["label"])}<br><span style="font-weight:400;color:var(--muted);font-size:11px">耐用{s["usefulLife"]}年</span></th>{cells}</tr>')
    rows_html = "\n          ".join(rows)

    faqs = [
        {
            "q": "建物残価率マトリクスはどう使えばいいですか？",
            "a": "縦軸に構造（木造・軽量鉄骨・重量鉄骨・RC/SRC）、横軸に築年数（新築〜築25年）を並べています。該当するセルの数値（残価率）をクリックすると、その組み合わせの詳細ページ（延床1㎡あたりの評価額レンジ・延床100㎡での概算例）に移動します。",
        },
        {
            "q": "残価率はどの構造が一番高く残りますか？",
            "a": "同じ築年数であれば、法定耐用年数が長い構造ほど残価率は高くなります。目安は鉄筋コンクリート造（RC・SRC、耐用47年）＞重量鉄骨造（34年）＞軽量鉄骨造（27年）＞木造（22年）の順です。",
        },
        {
            "q": "残価率がマイナスになったり0になったりしますか？",
            "a": f"0にはなりません。本ツールでは耐用年数を超えても再調達価格の{round(SALVAGE_FLOOR*100)}%を名目上の残価として下限に設定しています。ただし実際の市場では、老朽化した建物の取引価値がほぼ0と評価されることもあります。",
        },
    ]

    body = f"""
  <div class="wrap">
    <p class="crumbs"><a href="/">お金のカルテ</a> ＞ <a href="/fudosan/">不動産かんたん評価診断</a> ＞ <a href="/fudosan/p/">早見表</a> ＞ 建物残価率マトリクス</p>
    <p class="eyebrow">建物残価率 早見表</p>
    <h1>建物残価率マトリクス<br>構造 × 築年数で早見</h1>
    <p class="lead">木造・軽量鉄骨造・重量鉄骨造・RC/SRCの4構造と、新築〜築25年の6区分を組み合わせた全24パターンの残価率を一覧にしました。セルをクリックすると詳細ページ（評価額レンジ）に移動します。</p>
    <div class="answer">
      <span class="k">Direct Answer</span>
      <p>{esc(direct_answer)}</p>
      <span class="src">出典：国税庁 耐用年数省令 別表第一・「建物の標準的な建築価額表」。確認日 {BUILD_DATE}。</span>
    </div>
  </div>

  <div class="wrap">
    <div class="card card-pad">
      <div class="wrap-table">
        <table class="matrix">
          <thead><tr><th>構造 ＼ 築年数</th>{header_cells}</tr></thead>
          <tbody>
          {rows_html}
          </tbody>
        </table>
      </div>
      <div class="note-box"><strong>見方：</strong> セルの数値は残価率の目安（%）。クリックすると、その構造・築年数の建物評価額レンジ（円/㎡・延床100㎡例）の詳細ページに移動します。</div>
    </div>
  </div>

  <div class="wrap">
    <div class="cta-band">
      <div>
        <h3>あなたの物件の座標を、無料・匿名で発行する</h3>
        <p>早見表は構造・築年の平均値です。土地・エリア・収益状況まで入力すると「不動産カルテ指数」が発行できます。</p>
      </div>
      <a class="cta clay" href="/fudosan/#shindan">不動産カルテを発行する →</a>
    </div>
  </div>

  {faq_block(faqs)}

  <div class="wrap">
    <div class="linklist">
      <a href="/fudosan/p/rimawari/">想定利回りマトリクスを見る</a>
      <a href="/fudosan/p/">早見表トップに戻る</a>
      <a href="/fudosan/#shindan">不動産かんたん評価診断（無料・匿名）</a>
    </div>
  </div>
"""

    head = head_block(title, description, path, rel_css_path(1))
    ld_list = [
        breadcrumb_ld(
            [
                {"name": "お金のカルテ", "path": "/"},
                {"name": "不動産かんたん評価診断", "path": "/fudosan/"},
                {"name": "早見表", "path": "/fudosan/p/"},
                {"name": "建物残価率マトリクス", "path": path},
            ]
        ),
        faq_ld(faqs),
    ]
    html = render_page(head, ld_list, body, rel_css_path(1),
                       band_img="house-white.webp", band_cap="建物の残価率を、構造×築年で早見する。",
                       band_e="ZANKA MATRIX")
    return path, html


# ---------------------------------------------------------------------------
# 6. (b) 想定利回り 早見ページ ─ エリア5種 × 築年帯4区分 = 20ページ
# ---------------------------------------------------------------------------
ASSUMED_RENT_ANNUAL = 10_000_000  # 満室想定家賃1,000万円/年
ASSUMED_OCCUPANCY = 0.95  # 稼働95%


def build_rimawari_page(area, ageband):
    area_key = area["key"]
    area_label = area["label"]
    band_key = ageband["key"]
    band_label = ageband["label"]
    slug = f"{area_key}-{band_key}"
    path = f"/fudosan/p/rimawari/{slug}/"

    cr = CAP_RATES.get(area_key, {}).get("income", {}).get(band_key, [6.0, 9.0])
    cr_lo, cr_hi = cr

    noi = ASSUMED_RENT_ANNUAL * ASSUMED_OCCUPANCY * (1 - OPEX_RATIO)
    price_hi = noi / (cr_lo / 100)
    price_lo = noi / (cr_hi / 100)

    title = f"{area_label}・{band_label}の想定利回りはどれくらい？収益価格の早見表｜お金のカルテ"
    description = (
        f"{area_label}・{band_label}の収益物件の想定還元利回りは約{pct1(cr_lo)}〜{pct1(cr_hi)}%が目安。"
        f"満室想定家賃1,000万円/年・稼働95%・運営費20%の逆算例つき早見表。出典：JREI不動産投資家調査。"
    )

    direct_answer = (
        f"{area_label}・{band_label}の賃貸住宅における想定還元利回り（期待利回り）は、"
        f"概ね{pct1(cr_lo)}〜{pct1(cr_hi)}%が目安です。満室想定家賃1,000万円/年・稼働率95%・"
        f"運営費率20%で実質収益（NOI）を計算し、この利回りレンジで還元すると、"
        f"収益価格は約{fmt_range(price_lo, price_hi)}が目安になります。"
        f"出典：日本不動産研究所（JREI）「不動産投資家調査」2025年10月。"
    )

    faqs = [
        {
            "q": f"{area_label}・{band_label}の収益物件の想定利回りはどれくらいですか？",
            "a": (
                f"想定還元利回り（期待利回り）は約{pct1(cr_lo)}〜{pct1(cr_hi)}%が目安です。"
                f"日本不動産研究所（JREI）の不動産投資家調査を軸に、エリアの流動性と築年帯による賃料下落・"
                f"修繕リスクを織り込んだレンジです。"
            ),
        },
        {
            "q": "満室想定家賃1,000万円/年の場合、収益価格はいくらになりますか？",
            "a": (
                f"稼働率95%・運営費率{round(OPEX_RATIO*100)}%とすると、実質収益（NOI）は約{fmt_yen(noi)}/年です。"
                f"これを想定還元利回り{pct1(cr_lo)}〜{pct1(cr_hi)}%で割り戻すと、収益価格は約{fmt_range(price_lo, price_hi)}が目安になります。"
                f"利回りが低いほど価格は高く、利回りが高いほど価格は低く計算されます。"
            ),
        },
        {
            "q": "築年帯によって利回りはどう変わりますか？",
            "a": (
                "一般に築年数が経過するほど、賃料下落・修繕リスク・流動性低下を織り込んで、想定利回り（期待利回り）は"
                "高くなる（＝同じ家賃でも価格は下がる）傾向があります。新築〜10年が最も低く、31年以上が最も高いレンジです。"
            ),
        },
        {
            "q": "この利回り・収益価格はそのまま投資判断に使えますか？",
            "a": (
                "使えません。本ページはエリア区分・築年帯の平均的な公開データによる概算レンジで、"
                "個別物件の立地・建物状態・賃貸借契約・修繕履歴などは反映していません。"
                "正確な収益性の判断は宅地建物取引業者・不動産鑑定士にご確認ください。"
            ),
        },
    ]

    same_area_links = "\n      ".join(
        f'<a class="crosscard" href="/fudosan/p/rimawari/{area_key}-{b["key"]}/"><p class="t">{esc(area_label)}・{esc(b["label"])} →</p><p>想定利回りと収益価格の目安</p></a>'
        for b in AGE_BANDS
        if b["key"] != band_key
    )
    same_band_links = "\n      ".join(
        f'<a class="crosscard" href="/fudosan/p/rimawari/{a["key"]}-{band_key}/"><p class="t">{esc(a["label"])}・{esc(band_label)} →</p><p>想定利回りと収益価格の目安</p></a>'
        for a in AREAS
        if a["key"] != area_key
    )

    body = f"""
  <div class="wrap">
    <p class="crumbs"><a href="/">お金のカルテ</a> ＞ <a href="/fudosan/">不動産かんたん評価診断</a> ＞ <a href="/fudosan/p/">早見表</a> ＞ <a href="/fudosan/p/rimawari/">想定利回り</a> ＞ {esc(area_label)}・{esc(band_label)}</p>
    <p class="eyebrow">想定利回り 早見表</p>
    <h1>{esc(area_label)}・{esc(band_label)}の<br>想定利回りと収益価格の目安</h1>
    <p class="lead">{esc(area_label)}にある{esc(band_label)}の賃貸住宅について、想定還元利回りのレンジと、満室想定家賃1,000万円/年での収益価格の逆算例を早見表にまとめました。すべて概算・目安です。</p>
    <div class="answer">
      <span class="k">Direct Answer</span>
      <p>{esc(direct_answer)}</p>
      <span class="src">出典：日本不動産研究所（JREI）「第53回 不動産投資家調査」2025年10月現在。確認日 {BUILD_DATE}。</span>
    </div>
  </div>

  <div class="wrap">
    <div class="card card-pad">
      <div class="wrap-table">
        <table class="zk">
          <caption>{esc(area_label)}・{esc(band_label)}の想定利回り・収益価格 早見表</caption>
          <thead><tr><th>項目</th><th>数値の目安</th></tr></thead>
          <tbody>
            <tr><td>エリア区分</td><td class="num">{esc(area_label)}</td></tr>
            <tr><td>築年帯</td><td class="num">{esc(band_label)}</td></tr>
            <tr class="hl"><td>想定還元利回りレンジ</td><td class="num">{pct1(cr_lo)}% 〜 {pct1(cr_hi)}%</td></tr>
            <tr><td>満室想定家賃（前提）</td><td class="num">{fmt_yen(ASSUMED_RENT_ANNUAL)}/年</td></tr>
            <tr><td>稼働率（前提）</td><td class="num">{round(ASSUMED_OCCUPANCY*100)}%</td></tr>
            <tr><td>運営費率（前提）</td><td class="num">{round(OPEX_RATIO*100)}%</td></tr>
            <tr><td>実質収益（NOI）</td><td class="num">約 {fmt_yen(noi)}/年</td></tr>
            <tr class="hl"><td>収益価格（逆算例）</td><td class="num">約 {fmt_range(price_lo, price_hi)}</td></tr>
          </tbody>
        </table>
      </div>
      <div class="note-box"><strong>計算式：</strong> 実質収益（NOI）＝満室想定家賃 × 稼働率 × (1−運営費率)。収益価格 ＝ NOI ÷ 想定還元利回り（利回りが低いほど価格は高くなります）。</div>
      <div class="disclaimer-box"><strong>この早見表について：</strong> {esc(DISCLAIMER["standardsNote"])} {esc(DISCLAIMER["method"])}</div>
    </div>
  </div>

  <div class="wrap">
    <div class="cta-band">
      <div>
        <h3>あなたの物件の実際の家賃で概算する</h3>
        <p>早見表は前提家賃1,000万円/年での試算です。実際の家賃・稼働率・エリアを入力すると、積算・収益・税務の3レイヤーで「不動産カルテ指数」を無料・匿名で発行できます。</p>
      </div>
      <a class="cta clay" href="/fudosan/#shindan">不動産カルテを発行する →</a>
    </div>
  </div>

  <div class="wrap"><div class="orn"><span class="ln"></span><span class="mk"></span><span class="lbl">SAME AREA</span><span class="ln"></span></div></div>
  <div class="wrap">
    <h2>{esc(area_label)}の他の築年帯</h2>
    <p class="sec-sub">同じエリアで、築年帯による想定利回りの違いを比較できます。</p>
    <div class="crossgrid">
      {same_area_links}
    </div>
  </div>

  <div class="wrap"><div class="orn"><span class="ln"></span><span class="mk"></span><span class="lbl">SAME AGE BAND</span><span class="ln"></span></div></div>
  <div class="wrap">
    <h2>{esc(band_label)}の他のエリア</h2>
    <p class="sec-sub">同じ築年帯で、エリアによる想定利回りの違いを比較できます。</p>
    <div class="crossgrid">
      {same_band_links}
    </div>
  </div>

  {faq_block(faqs)}

  <div class="wrap">
    <div class="linklist">
      <a href="/fudosan/#shindan">不動産かんたん評価診断（無料・匿名）</a>
      <a href="/fudosan/index-definition/">不動産カルテ指数の定義</a>
      <a href="/fudosan/sources/">データ出典</a>
      <a href="/fudosan/p/rimawari/">想定利回りマトリクスに戻る</a>
    </div>
  </div>
"""

    head = head_block(title, description, path, rel_css_path(2))
    ld_list = [
        breadcrumb_ld(
            [
                {"name": "お金のカルテ", "path": "/"},
                {"name": "不動産かんたん評価診断", "path": "/fudosan/"},
                {"name": "早見表", "path": "/fudosan/p/"},
                {"name": "想定利回り", "path": "/fudosan/p/rimawari/"},
                {"name": f"{area_label}・{band_label}", "path": path},
            ]
        ),
        faq_ld(faqs),
    ]
    rpic = {"東京23区": "city-building.webp", "東京都下・首都圏中核": "apartment-exterior.webp",
            "政令市・県庁所在地": "apartment-building.webp", "地方都市（一般市）": "suburban-home.webp",
            "郊外・町村部": "house-street.webp"}.get(area_label, "apartment-exterior.webp")
    html = render_page(head, ld_list, body, rel_css_path(2),
                       band_img=rpic, band_cap=f"{area_label}・{band_label}｜想定利回りと収益価格の目安",
                       band_e="RIMAWARI / INCOME YIELD")
    return path, html


def build_rimawari_hub():
    path = "/fudosan/p/rimawari/"
    title = "想定利回りマトリクス｜エリア×築年帯で早見｜お金のカルテ"
    description = "東京23区・東京都下・政令市・地方都市・郊外の5エリア × 築年帯4区分、全20パターンの想定還元利回りと収益価格の目安を一覧化した早見表マトリクス。"

    direct_answer = (
        "収益物件の想定還元利回りは、エリアの流動性と築年帯によって大きく変わります。"
        "都心・築浅ほど利回りは低く（＝価格は高く）、郊外・築古ほど利回りは高く（＝価格は低く）なる傾向です。"
        "下のマトリクスからエリア×築年帯の組み合わせを選ぶと、利回りレンジと収益価格の逆算例が確認できます。"
    )

    header_cells = "".join(f"<th>{esc(b['label'])}</th>" for b in AGE_BANDS)
    rows = []
    for a in AREAS:
        cells = []
        for b in AGE_BANDS:
            cr = CAP_RATES.get(a["key"], {}).get("income", {}).get(b["key"], [6.0, 9.0])
            cells.append(
                f'<td><a href="/fudosan/p/rimawari/{a["key"]}-{b["key"]}/">{pct1(cr[0])}〜{pct1(cr[1])}%</a></td>'
            )
        rows.append(f'<tr><th>{esc(a["label"])}</th>{"".join(cells)}</tr>')
    rows_html = "\n          ".join(rows)

    faqs = [
        {
            "q": "想定利回りマトリクスはどう使えばいいですか？",
            "a": "縦軸にエリア区分（東京23区〜郊外）、横軸に築年帯（新築〜10年・11〜20年・21〜30年・31年以上）を並べています。該当セルの数値（想定利回りレンジ）をクリックすると、収益価格の逆算例付きの詳細ページに移動します。",
        },
        {
            "q": "なぜ都心の利回りは低いのですか？",
            "a": "都心（東京23区など）は流動性が高く、資産としての安定性が評価されるため、投資家が求める利回り（期待利回り）が低くても購入されやすく、結果として利回りは低め（価格は高め）になる傾向があります。逆に地方・郊外は流動性リスクの分、利回りは高め（価格は低め）になります。",
        },
        {
            "q": "この利回りは実際の取引でも同じですか？",
            "a": "個別物件によって差があります。本マトリクスは日本不動産研究所の投資家調査を軸にしたエリア区分・築年帯の平均的な目安であり、立地の細かな違い・建物状態・賃貸借契約の内容などは反映していません。",
        },
    ]

    body = f"""
  <div class="wrap">
    <p class="crumbs"><a href="/">お金のカルテ</a> ＞ <a href="/fudosan/">不動産かんたん評価診断</a> ＞ <a href="/fudosan/p/">早見表</a> ＞ 想定利回りマトリクス</p>
    <p class="eyebrow">想定利回り 早見表</p>
    <h1>想定利回りマトリクス<br>エリア × 築年帯で早見</h1>
    <p class="lead">東京23区・東京都下／首都圏中核・政令市／県庁所在地・地方都市・郊外／町村部の5エリアと、築年帯4区分を組み合わせた全20パターンの想定還元利回りを一覧にしました。セルをクリックすると詳細ページ（収益価格の逆算例）に移動します。</p>
    <div class="answer">
      <span class="k">Direct Answer</span>
      <p>{esc(direct_answer)}</p>
      <span class="src">出典：日本不動産研究所（JREI）「第53回 不動産投資家調査」2025年10月現在。確認日 {BUILD_DATE}。</span>
    </div>
  </div>

  <div class="wrap">
    <div class="card card-pad">
      <div class="wrap-table">
        <table class="matrix">
          <thead><tr><th>エリア ＼ 築年帯</th>{header_cells}</tr></thead>
          <tbody>
          {rows_html}
          </tbody>
        </table>
      </div>
      <div class="note-box"><strong>見方：</strong> セルの数値は想定還元利回りのレンジ（%）。クリックすると、その組み合わせの収益価格の逆算例（満室想定家賃1,000万円/年）の詳細ページに移動します。</div>
    </div>
  </div>

  <div class="wrap">
    <div class="cta-band">
      <div>
        <h3>あなたの物件の実際の家賃で、収益価格を概算する</h3>
        <p>マトリクスは前提家賃1,000万円/年での試算です。実際の家賃・エリア・築年を入力すると「不動産カルテ指数」を無料・匿名で発行できます。</p>
      </div>
      <a class="cta clay" href="/fudosan/#shindan">不動産カルテを発行する →</a>
    </div>
  </div>

  {faq_block(faqs)}

  <div class="wrap">
    <div class="linklist">
      <a href="/fudosan/p/zanka/">建物残価率マトリクスを見る</a>
      <a href="/fudosan/p/">早見表トップに戻る</a>
      <a href="/fudosan/#shindan">不動産かんたん評価診断（無料・匿名）</a>
    </div>
  </div>
"""

    head = head_block(title, description, path, rel_css_path(1))
    ld_list = [
        breadcrumb_ld(
            [
                {"name": "お金のカルテ", "path": "/"},
                {"name": "不動産かんたん評価診断", "path": "/fudosan/"},
                {"name": "早見表", "path": "/fudosan/p/"},
                {"name": "想定利回りマトリクス", "path": path},
            ]
        ),
        faq_ld(faqs),
    ]
    html = render_page(head, ld_list, body, rel_css_path(1),
                       band_img="apartment-exterior.webp", band_cap="想定利回りを、エリア×築年帯で早見する。",
                       band_e="RIMAWARI MATRIX")
    return path, html


# ---------------------------------------------------------------------------
# 7. pSEO 早見表トップ（ハブ）
# ---------------------------------------------------------------------------
def build_p_index():
    path = "/fudosan/p/"
    title = "不動産 早見表｜建物残価率・想定利回りをすぐ確認｜お金のカルテ"
    description = "構造×築年の建物残価率マトリクス（24パターン）、エリア×築年帯の想定利回りマトリクス（20パターン）。公開データに基づく概算・目安を早見表で確認できます。"

    direct_answer = (
        "不動産の価値は、建物の『残価率』（構造と築年数で決まる建物価値の目安）と、"
        "収益物件の『想定利回り』（エリアと築年帯で決まる収益価格の目安）の2つの早見表からおおよその座標を確認できます。"
        "個別物件で正確に概算したい場合は、無料・匿名の不動産かんたん評価診断をご利用ください。"
    )

    faqs = [
        {
            "q": "この早見表とトップページの診断（不動産カルテ）はどう違いますか？",
            "a": "早見表は構造・築年・エリアの代表的な組み合わせをあらかじめ計算した一覧で、登録・入力なしにすぐ数値の目安を確認できます。トップページの診断は、あなたの物件の面積・築年・エリア・家賃などを入力して、積算・収益・税務の3レイヤーと『不動産カルテ指数』を個別に発行するツールです。",
        },
        {
            "q": "早見表の数値はどこから来ていますか？",
            "a": "建物残価率は国税庁の法定耐用年数省令・建物の標準的な建築価額表、想定利回りは日本不動産研究所（JREI）の不動産投資家調査を主な出典としています。詳細は「データ出典」ページで一覧公開しています。",
        },
        {
            "q": "早見表の数値はそのまま査定・投資判断に使えますか？",
            "a": "使えません。早見表は構造・築年・エリア区分の平均的な公開データによる概算レンジであり、個別物件の状態・立地・契約内容などは反映していません。正確な判断は宅地建物取引業者・不動産鑑定士・税理士にご確認ください。",
        },
    ]

    body = f"""
  <div class="wrap">
    <p class="crumbs"><a href="/">お金のカルテ</a> ＞ <a href="/fudosan/">不動産かんたん評価診断</a> ＞ 早見表</p>
    <p class="eyebrow">不動産 早見表（pSEO）</p>
    <h1>不動産の価値・利回りを、<br>早見表ですぐ確認する</h1>
    <p class="lead">「建物残価率」と「想定利回り」の2系統、あわせて44パターンの早見表をご用意しました。構造・築年・エリアを選ぶだけで、公開データに基づく概算レンジがすぐ分かります。個別物件で正確に概算したい場合は、無料・匿名の診断（不動産カルテ）もご利用ください。</p>
    <div class="answer">
      <span class="k">Direct Answer</span>
      <p>{esc(direct_answer)}</p>
      <span class="src">出典：国税庁・日本不動産研究所（JREI）。詳細は <a href="/fudosan/sources/">データ出典</a> ページ。確認日 {BUILD_DATE}。</span>
    </div>
  </div>

  <div class="wrap"><div class="orn"><span class="ln"></span><span class="mk"></span><span class="lbl">ZANKA</span><span class="ln"></span></div></div>
  <div class="wrap">
    <h2>建物残価率マトリクス</h2>
    <p class="sec-sub">木造・軽量鉄骨・重量鉄骨・RC/SRCの4構造 × 新築〜築25年の6区分、全24パターン。</p>
    <div class="crossgrid">
      <a class="crosscard" href="/fudosan/p/zanka/"><p class="t">建物残価率マトリクスを見る →</p><p>構造×築年の全24パターンを一覧</p></a>
    </div>
  </div>

  <div class="wrap"><div class="orn"><span class="ln"></span><span class="mk"></span><span class="lbl">RIMAWARI</span><span class="ln"></span></div></div>
  <div class="wrap">
    <h2>想定利回りマトリクス</h2>
    <p class="sec-sub">東京23区・東京都下・政令市・地方都市・郊外の5エリア × 築年帯4区分、全20パターン。</p>
    <div class="crossgrid">
      <a class="crosscard" href="/fudosan/p/rimawari/"><p class="t">想定利回りマトリクスを見る →</p><p>エリア×築年帯の全20パターンを一覧</p></a>
    </div>
  </div>

  <div class="wrap">
    <div class="cta-band">
      <div>
        <h3>あなたの物件で、無料・匿名の座標を発行する</h3>
        <p>早見表は代表値です。実際の面積・築年・エリア・家賃を入力すると、積算・収益・税務の3レイヤーで「不動産カルテ指数」を個別に発行できます。営業電話は鳴りません。</p>
      </div>
      <a class="cta clay" href="/fudosan/#shindan">不動産カルテを発行する →</a>
    </div>
  </div>

  {faq_block(faqs)}

  <div class="wrap">
    <div class="linklist">
      <a href="/fudosan/#shindan">不動産かんたん評価診断（無料・匿名）</a>
      <a href="/fudosan/index-definition/">不動産カルテ指数の定義</a>
      <a href="/fudosan/sources/">データ出典</a>
    </div>
  </div>
"""

    head = head_block(title, description, path, rel_css_path(0))
    ld_list = [
        breadcrumb_ld(
            [
                {"name": "お金のカルテ", "path": "/"},
                {"name": "不動産かんたん評価診断", "path": "/fudosan/"},
                {"name": "早見表", "path": path},
            ]
        ),
        faq_ld(faqs),
    ]
    html = render_page(head, ld_list, body, rel_css_path(0),
                       band_img="townscape.webp", band_cap="不動産の価値・利回りを、早見表ですぐ確認する。",
                       band_e="OKANE CARTE / FUDOSAN")
    return path, html


# ---------------------------------------------------------------------------
# 8. 書き出し
# ---------------------------------------------------------------------------
def write_page(pagepath, html):
    """pagepath: '/fudosan/p/zanka/wood-shinchiku/' → fudosan/p/zanka/wood-shinchiku/index.html"""
    rel = pagepath
    assert rel.startswith("/fudosan/p/")
    rel = rel[len("/fudosan/p/"):].strip("/")
    out_dir = P_DIR if rel == "" else P_DIR / rel
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html, encoding="utf-8")


def main():
    print("=== お金のカルテ /fudosan/p/ pSEO ビルド開始 ===")

    # 出力ディレクトリは作り直す（p/ 配下のみ。所有範囲外には触れない）
    if P_DIR.exists():
        import shutil
        shutil.rmtree(P_DIR)
    P_DIR.mkdir(parents=True, exist_ok=True)
    (P_DIR / "assets").mkdir(parents=True, exist_ok=True)

    # 共有CSS
    (P_DIR / "assets" / "pseo.css").write_text(PSEO_CSS, encoding="utf-8")

    pages = []

    # (a) zanka 24ページ + ハブ
    for st in STRUCTURES:
        for ap in PAGE_AGES:
            pages.append(build_zanka_page(st, ap))
    pages.append(build_zanka_hub())

    # (b) rimawari 20ページ + ハブ
    for a in AREAS:
        for b in AGE_BANDS:
            pages.append(build_rimawari_page(a, b))
    pages.append(build_rimawari_hub())

    # トップハブ
    pages.append(build_p_index())

    for p, html in pages:
        write_page(p, html)

    zanka_count = len(STRUCTURES) * len(PAGE_AGES)
    rimawari_count = len(AREAS) * len(AGE_BANDS)
    hub_count = 3
    total = zanka_count + rimawari_count + hub_count
    print(f"[zanka] {zanka_count} ページ（構造{len(STRUCTURES)} × 築年{len(PAGE_AGES)}）")
    print(f"[rimawari] {rimawari_count} ページ（エリア{len(AREAS)} × 築年帯{len(AGE_BANDS)}）")
    print(f"[hub] {hub_count} ページ（p/ ・ p/zanka/ ・ p/rimawari/）")
    print(f"[合計] {total} ページ生成（実際の書き出し件数: {len(pages)}）")

    # _urls.txt（1行1URL・絶対URL）
    urls = []
    urls.append(f"{SITE_ORIGIN}/fudosan/")
    urls.append(f"{SITE_ORIGIN}/fudosan/index-definition/")
    urls.append(f"{SITE_ORIGIN}/fudosan/sources/")
    for p, _ in pages:
        urls.append(f"{SITE_ORIGIN}{p}")
    urls_text = "\n".join(urls) + "\n"
    (P_DIR / "_urls.txt").write_text(urls_text, encoding="utf-8")
    print(f"[_urls.txt] {len(urls)} 行 → {P_DIR / '_urls.txt'}")

    print("=== ビルド完了 ===")


if __name__ == "__main__":
    main()

# お金のカルテ 2サイト 最終デザインシステム（design-brief）

確定版 / 作成: design-director / 2026-07-05
土台: `design/trend-report.md`（trend-scout）＋ CLAUDE.md 最上位原則「日本の土台 × 海外の格」＋ web-editorial-minimal（明るい富裕・引き算・ヘアライン・差し色1色）

---

## コンセプト1行

**「暗い金融サイトの逆を行く。明るい石とインクの余白に、深い色をひとしずく、金は印章の一点だけ ── 富裕層の応接室の静けさ」**

- 地色(明るい石/紙)が主役 = 面積70〜80%。
- 深色(A:深緑 / B:深紺)が構造色 = 見出し・罫・図表で15〜25%。
- 金は「印章・数値・CTA・1pxライン」だけの差し色 = 総面積5%未満(過剰使用は compliance-qa 差し戻し対象)。
- 写真は主役にしない。地色マルチプライ or 不透明度0.06〜0.12 の「透かし」として罫線の下に沈める。

## 借りた"格"と出典(構造・原則のみ / 視覚的リサイクルなし)

- 老舗百貨店/英国式ラグジュアリー(Harrods emerald × champagne × ivory)の「王道の富=緑×金」配色構造 → 案A。出典: zoviz.com/blog/luxury-brand-colors-meanings
- Old Money(ivory/olive/navy/charcoal)の抑制型高級配色 → A/B共通の面積比思想。出典: icolorpalette.com/color/old-money
- Awwwards Luxury/Real-estate(Elyse Residence "timeless refinement")の「静かな高級感=大きな余白+控えめヒーロー」構造 → ヒーロー方針。出典: awwwards.com/websites/luxury
- SiteInspire "Stack Asset Management"(資産運用会社)の格式レイアウト原則 → 案B。出典: siteinspire.com/website/13111
- 同業フィンテック(暗い濃紺×ネオン金、量産カード)が絶対に参照しない畑=美術館/邸宅内装/庭園エディトリアルから「格」を借用 → 差別化ゲート通過。

**差別化ゲート判定: PASS。** 同業の型(ダーク×金の量産フィンテック)を明るい石基調へ反転し、緑/紺の色相分離・金の質感差(シャンパン金 vs アンティーク金)・明朝の性格差(丸い vs 旧字形)の3軸で別ブランド化。模倣でなく構造の再構築。

---

## A/B が並んでも別ブランドに見える 5軸(trend-report 差別化を踏襲)

| 軸 | 案A(index.html ポータル) | 案B(jikabuka 診断) |
|---|---|---|
| 色相 | 緑(暖色寄り・自然/富の緑) | 紺(寒色寄り・格式) |
| 地の温度 | アイボリー(黄み・あたたかい) | パール(青白み・ひんやり) |
| 金の質感 | シャンパンゴールド(明るく軽い) | アンティークゴールド(くすんだ真鍮) |
| 罫/字間 | 細罫 + 丸い明朝 = 親しみ+上質 | 直線罫 + 字間広め大文字 = 権威 |
| 写真テーマ | 庭園・自然光・大理石(暮らしの豊かさ) | 邸宅内装・スカイライン・建築(資産/権威) |

---

## 実装前の重要な事実確認(実装者=site-builder への申し送り)

現状 `assets/fonts/` に**実在するのは `ShipporiMincho-Bold.ttf` と `ZenOldMincho-Bold.ttf` の2ファイルのみ**(サブセット用 `_chars.txt` あり)。trend-report が触れた `cormorant.css`/`shippori.css` および欧文4種・本文和文は**まだ未調達**。`assets/photos/` も**空**(写真18枚は未DL)。したがって:

1. **和文見出しは即実装可**(A=Shippori Bold / B=ZenOld Bold が既にある)。まず最優先でこの2つを @font-face 登録し `--serif` を差し替える。
2. 欧文(Marcellus/Cormorant/Cormorant Garamond/Playfair/Cinzel)・本文和文(Zen Kaku Gothic New/Noto Serif JP)は OFL を DL→`_chars.txt` ベースでサブセット→`/assets/fonts/` 同梱。**未調達の間は下記フォールバックで先行実装し、後から @font-face を足すだけで昇格できる設計**にする(font-family 指定は最初から最終名で書き、ファイルが無い分はフォールバックが効く)。
3. 写真は CSS 変数スロット方式(`--photo-hero` 等の `url()`)で後差替。**写真ゼロでも配色・罫・余白だけで成立するのが基準**(写真は"あれば透かし"の上位装飾)。
4. **CSP**: `jikabuka/index.html` は `font-src 'self'` を既に含む(OK)。**ルート `index.html` の CSP には `font-src` が無い**ため、セルフホスト font 読込前に `font-src 'self';` を追記すること(既存 style-src/img-src の並びに1語追加、他は不可侵)。

---

## ページ構成

### 案A: index.html(ポータル)
現状の1カラム構成を活かす。ヘッダー(ブランド) → eyebrow → h1ヒーロー → orn(区切り) → feature(公開中診断=jikabukaへの動線) → orn → grid(今後の6領域タイル) → note → footer。
装飾追加は「地色の反転」と「orn/feature/tileの見た目付与」のみ。DOM追加は最小(ヒーロー透かし写真スロット1つ・任意)。

### 案B: jikabuka/index.html(診断・DOM不可侵)
現状構成のまま(header.site → hero → wave-divider → answer → section#shindan[wizard/resultwrap] → orn → section#method[formula] → orn → section#faq → footer.site)。**CSSと装飾スロットのみで刷新**。

---

## ヒーロー方針

- **A**: 明るいアイボリー地。左に h1(Shippori 明朝 深緑)+lead、余白大。ヒーローに写真を敷く場合は庭園/大理石を `opacity .07` の右上透かし + 深緑グラデ薄膜。`.g`(現状は金グラデ文字)は**深緑ベース + 金は下線/圏点1点のみ**に格下げ。ドラマは色でなく余白で作る。
- **B**: 現状ヒーローは濃紺グラデ(`.hero`)で暗い。これを**パール地 or 極薄スレートグラデの明るいヒーロー**へ反転。h1 は ZenOld 明朝 深紺。既存インラインSVG図版(評価カルテ)は活かすが、背景を暗→明にしたことに合わせSVG内の白抜き前提色(`#fbf6ec`紙/`#12233d`ヘッダ帯)はそのままで映える(紙×紺は明地でも成立)。`.hero-wm`/`.hero-pulse` の透かしは opacity 据え置き。CTA(`.hero .cta`)はアンティーク金グラデのまま(=金は"行動の一点"として正当)。

## トーン&ボイス

- 品位のある常体〜敬体。断定を避ける(「概算の目安」「〜の可能性」)。景表法/薬機法は非該当だが、金融の信頼として**過度な保証・効果断定は禁止**(既存の免責文言は死守)。
- A=「間口は広いが上質」= やわらかく招き入れる。B=「重厚な財務の格式」= 静かに信頼させる。
- 数値は主役級に大きく美しく(A=Cormorant / B=Playfair の数字)。ただし桁の演出であって煽りではない。

---

## やらないことリスト(統一基準・compliance-qa の差し戻し根拠)

1. 金を面積で使わない。金グラデの大ブロック・金地ボタンの多用・金の背景塗り = 禁止(金は総面積5%未満/1pxライン・数値・CTA・印章のみ)。
2. 暗い地色に戻さない。ダークネイビー全面・黒背景ヒーロー = 禁止(明るい石が主役)。
3. 写真を主役にしない。フルブリード鮮明写真・彩度の高い装飾写真 = 禁止(透かし0.06〜0.12 / 地色マルチプライのみ)。
4. 極太ゴシック見出し・ネオン・影の濃いカード乱用・絵文字アイコン = 禁止(web-editorial-minimal 既定/2度却下の教訓)。
5. A と B を同じ配色・同じフォントにしない(5軸で必ず差をつける)。
6. **jikabuka の DOM/id/class/JS を変更しない**(下記制約)。CSS と装飾スロット追加のみ。
7. 外部フォント/CDN のホットリンク・外部画像ホットリンク = 禁止(全てセルフホスト/ローカル同梱)。
8. 断定的・保証的コピー = 禁止(概算/目安の姿勢を維持)。

---

## サイトB 厳守制約(jikabuka/index.html)

**DOM構造・id・class・JavaScript は一切変更不可。** 刷新は下記に限定する。

- `:root` の CSS 変数を書き換える(色/フォント変数の値だけ差し替え。変数名は維持)。
- 既存クラス/idセレクタに対する見た目の再定義(色・罫・影・font-family の上書き)。
- `@font-face` 追加と装飾用写真の `url()` スロット追加(CSSのみ)。
- 触ってよい変数(値のみ変更): `--navy --navy-2 --indigo --ink --muted --line --bg --bg-2 --paper --gold --gold-2 --gold-hi --gold-soft --serif`(→ B配色トークンへ)。
- 見た目を当て直す既存クラス/id: `header.site .hero .answer .card .opt .kpi .stat .consult .formcard .orn .emblem .formula .faq #wizard #resultwrap #totalVal #industryOpts #leadForm .btn .goldtext .wave-divider` 等。**セレクタ名は既存のまま、宣言(色/罫/font)だけ差し替える。**
- インラインSVG `linearGradient#goldGrad`(3 stop)はアンティーク金へ微調整可(stop色のみ)。SVGの構造・viewBox・id は不可侵。
- **禁止**: HTML要素の増減、id/class のリネーム、`hidden`属性やJS制御下の要素の表示ロジック変更、`.step[data-step]`/`.resultwrap`(JSが display 制御)への `display` 固定上書き。

具体トークン・フォント割当・写真配置・コンポーネント別トリートメントは `design/design-tokens.md` を正とする(実装者はそちらをCSSに転記)。

---

## 総括

trend-report の HEX・フォント・写真URLを採用しつつ、"実在するアセットは何か"で実装順序を確定した。**まず和文明朝2ファイル(既存)で見出しの格を立て、地色を暗→明へ反転する**だけで、同業フィンテック感からの脱却は達成できる。欧文・写真は後差替スロットで段階昇格。A(シャンパン×深緑・丸い明朝)と B(パール×深紺・旧字形明朝+アンティーク金)は、色相・地の温度・金の質感・書体の性格・写真テーマの5軸で別ブランドとして識別できる。金の総量は5%未満を compliance-qa の重点チェックに据える。

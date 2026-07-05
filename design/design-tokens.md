# お金のカルテ 2サイト 確定デザイントークン(実装転記用)

正典 / design-director 確定 / 2026-07-05
相棒: `design/design-brief.md`(狙い・制約・やらないこと)。本ファイルは**CSSにそのまま落とす粒度**。

面積比の絶対指針(全体を貫く): 明るい地色 70〜80% / 深色(緑or紺) 15〜25% / 金 5%未満(1pxライン・数値・CTA・印章のみ)。**金を面積で塗ったら不合格。**

---

## 1. 確定 :root トークン

### 案A — index.html(ポータル / シャンパン×ディープグリーン)

```css
:root{
  /* ── 地色(主役 70-80%) ── */
  --bg:        #FBF7EF;   /* ページ地色 アイボリーホワイト(温かい白) */
  --bg-2:      #F3EADA;   /* セクション切替・カード地 シャンパンベージュ */
  --paper:     #FFFDF9;   /* 最も明るい紙面(入力欄・カード内) */
  /* ── 構造色(深緑 15-25%) ── */
  --green:     #1F4B3E;   /* 見出し・ロゴ・重要ライン ディープグリーン(富の緑) */
  --green-2:   #7C9A82;   /* 補助アイコン・グラフ セージグリーン */
  /* 旧 --navy 系は緑にマッピング(互換のため名前も残す) */
  --navy:      #1F4B3E;
  --navy-2:    #2C6350;
  /* ── 金(差し色 5%未満) ── */
  --gold:      #C9A24B;   /* CTA・数値強調・罫 シャンパンゴールド */
  --gold-2:    #B98E3A;   /* 金の陰(グラデ用) */
  --gold-hi:   #E7D3A1;   /* ホバー・グラデ終点 ペールゴールド */
  --gold-soft: #F5ECD8;   /* 金のごく淡い地(notice等) */
  /* ── 文字 ── */
  --ink:       #2E2A24;   /* 本文 チャコールブラウン(純黒回避) */
  --muted:     #6B6459;   /* 注記 ストーングレー */
  /* ── 罫線 ── */
  --line:      #DCD0BC;   /* 1px罫線 ヘアラインベージュ */
  --line-strong:#C9A24B;  /* 強調罫=金(細く) */
  /* ── 影・角丸(下記共通トークン参照) ── */
  --radius:    14px;
  --radius-sm: 9px;
  --shadow-card:0 10px 30px rgba(31,75,62,.07);   /* 深緑を落とした柔影 */
  --shadow-soft:0 1px 0 rgba(31,75,62,.03);
  /* ── フォント(下記2章) ── */
  --serif-jp:  "Shippori Mincho B1","Shippori Mincho",var(--serif-fallback);
  --serif-en:  "Marcellus",var(--serif-jp);
  --num:       "Cormorant","Marcellus",Georgia,serif;
  --sans:      "Zen Kaku Gothic New",system-ui,-apple-system,"Segoe UI","Hiragino Kaku Gothic ProN","Yu Gothic UI","Meiryo",sans-serif;
  --serif-fallback:"Yu Mincho","YuMincho","Hiragino Mincho ProN",serif;
}
```

### 案B — jikabuka/index.html(診断 / パール×ロイヤルブルー×アンティーク金)

**注意: 変数名は既存を維持し値だけ差し替える(brief のB制約)。** 下記は既存 `:root` の各値の置換先。

```css
:root{
  /* 既存変数名 = 新しい値(パール×深紺×アンティーク金) */
  --navy:      #1B2A4A;   /* ロイヤルブルー(深紺・信頼/格式) 主役構造色 */
  --navy-2:    #4C5A78;   /* ダスティスレート サブ見出し・グラフ背景 */
  --indigo:    #2B3F63;   /* 中間紺(グラデ用) */
  --ink:       #2A2D33;   /* 本文 インクグレー(冷たい=Aの茶と対比) */
  --muted:     #767C87;   /* 注記 ミストグレー */
  --line:      #D8DBE0;   /* 1px罫線 ヘアラインスレート */
  --bg:        #F7F6F5;   /* ページ地色 パールホワイト(青白い高級白) */
  --bg-2:      #EDEAE5;   /* セクション背景・カード地 マーブルグレージュ */
  --paper:     #FFFFFF;   /* 紙面(入力欄・カード内 純白でパール感) */
  --gold:      #B08D45;   /* アンティークゴールド(くすんだ真鍮=Aと質感差) */
  --gold-2:    #9A7A38;   /* 金の陰 */
  --gold-hi:   #D6BE84;   /* サテンゴールド ホバー・細光沢 */
  --gold-soft: #F1ECDF;   /* 金のごく淡い地(notice) */
  --radius:    10px;      /* Aより角を締める=格式(直線的) */
  /* --serif は @font-face 登録後に下記へ差し替え */
  --serif:     "Zen Old Mincho","ZenOldMincho",var(--serif-fallback);
  --serif-fallback:"Yu Mincho","YuMincho","Hiragino Mincho ProN",serif;
}
/* B専用の追加トークン(新規変数=既存名と衝突しないので追加可) */
:root{
  --serif-en:  "Cormorant Garamond",var(--serif);
  --num:       "Playfair Display","Cormorant Garamond",Georgia,serif;
  --cinzel:    "Cinzel",var(--serif-en);   /* バッジ極小専用 */
  --sans-b:    "Noto Serif JP",system-ui,"Hiragino Kaku Gothic ProN","Yu Gothic UI","Meiryo",sans-serif; /* B本文は可読なら既存--sansのままでも可 */
  --shadow-card:0 8px 24px rgba(27,42,74,.09);  /* 紺を落とした影 */
}
```

### 影 / 角丸 / 罫線の指針(A/B共通思想)

- **角丸**: A=14px(やわらか) / B=10px(締める)。入力・小要素は -5px 前後。丸みで A の親しみ・B の格式を出す。
- **影**: 濃い黒影は禁止。**主役の深色を10%以下に落とした柔影**のみ(`rgba(緑or紺, .07〜.09)`)。カードは"浮く"のでなく"紙が置いてある"程度。
- **罫線**: 既定は 1px `--line`(ベージュ/スレート)。強調は 1px の金(`--gold`)を"線"としてのみ。太い金枠・二重金枠の乱用禁止。区切りは金グラデを `transparent→gold→transparent` で細く。
- **モーション方針**: 静かな高級感。transition は 120〜180ms ease、hover は `translateY(-2px)` 程度と border-color の変化のみ。パララックスは写真透かしに ±8px 以内の緩やかなもの1箇所まで。派手なdraw-on/回転は禁止(B は特にJS不可侵ゆえCSSのみの微動)。

### ブレークポイント(A/B共通)

- `max-width:760px` = タブレット→1カラム化の主分岐(既存hero/gridに合わせる)。
- `max-width:640px` = スマホ(透かし縮小・padding圧縮)。
- `max-width:520px` = grid2 → 1カラム(既存)。
- `max-width:420px` = ポータルgridを1カラム(既存)。
- 最小検証幅 **360px**(文字はみ出し根絶=clamp流動を全見出しに)。

---

## 2. フォント割当 & @font-face 方針

**セルフホスト前提(`/assets/fonts/`)。CSPは `font-src 'self'`(Bは既存OK・A は要追記)。** 既存実ファイルは `ShipporiMincho-Bold.ttf` `ZenOldMincho-Bold.ttf` の2つのみ。他はOFLをDL→`_chars.txt`でサブセット→woff2化して同梱。**未調達フォントはフォールバックが効くので font-family は最初から最終名で記述**する。

### 案A 割当

| 用途 | フォント(1st) | フォールバック | 変数 | 状態 |
|---|---|---|---|---|
| 和文見出し(h1/h2/ブランド/tile.t/feature.t) | Shippori Mincho B1 (Bold) | Yu Mincho | `--serif-jp` | **既存TTFで即実装可** |
| 欧文見出し/ロゴ(英字見出し・eyebrow英字) | Marcellus | Shippori→Yu Mincho | `--serif-en` | 要調達(OFL) |
| 数字・金額(feature内数値・将来のKPI) | Cormorant | Marcellus→Georgia | `--num` | 要調達(OFL) |
| 本文/lead/UI | Zen Kaku Gothic New | system-ui 系 | `--sans` | 要調達(無ければsystem-uiで可読성OK) |

### 案B 割当

| 用途 | フォント(1st) | フォールバック | 変数 | 状態 |
|---|---|---|---|---|
| 和文見出し(h1,h2,h3/.mark/.kpi .big/.stat .v) | Zen Old Mincho (Bold) | Yu Mincho | `--serif` | **既存TTFで即実装可** |
| 欧文見出し/ロゴ | Cormorant Garamond | Zen Old→Yu Mincho | `--serif-en` | 要調達(OFL) |
| 数字・評価額(#totalVal, .breakdown 数字) | Playfair Display | Cormorant Garamond→Georgia | `--num` | 要調達(OFL) |
| 認定バッジ/ラベル(極小・全角大文字・字間広) | Cinzel | Cormorant Garamond | `--cinzel` | 要調達 / **多用禁止・ラベル1〜2箇所のみ** |
| 本文 | Noto Serif JP or 既存 --sans | system-ui 系 | `--sans-b`/`--sans` | 可読優先。無ければ既存--sansのゴシックで可 |

### @font-face テンプレ(実装者用・パスと形式のみ確定)

```css
/* 即実装可(既存ファイル) ─ Aの見出し */
@font-face{font-family:"Shippori Mincho B1";src:url("/assets/fonts/ShipporiMincho-Bold.woff2") format("woff2"),
  url("/assets/fonts/ShipporiMincho-Bold.ttf") format("truetype");font-weight:700;font-display:swap;}
/* 即実装可(既存ファイル) ─ Bの見出し */
@font-face{font-family:"Zen Old Mincho";src:url("/assets/fonts/ZenOldMincho-Bold.woff2") format("woff2"),
  url("/assets/fonts/ZenOldMincho-Bold.ttf") format("truetype");font-weight:700;font-display:swap;}
/* 以降(要調達): Marcellus / Cormorant / CormorantGaramond / PlayfairDisplay / Cinzel / ZenKakuGothicNew / NotoSerifJP
   → OFL DL → _chars.txt でサブセット → woff2 化 → 同 /assets/fonts/ に配置し同型の @font-face を追記。
   欧文は英数記号のみサブセットで軽量化。font-display:swap 固定。 */
```

- **A/Bで欧文ファイルを共有しない**(Aは Marcellus+Cormorant、Bは Cormorant Garamond+Playfair+Cinzel)。同じ"Cormorant系"でも A=Cormorant / B=Cormorant Garamond と字幅違いを使い分け、別ブランド感を担保。
- TTF直リンクでも動くが、初手で **woff2 サブセット化**を推奨(日本語明朝は重い。`_chars.txt` 収録字のみで十分)。

---

## 3. 写真配置マップ(透かし運用)

**大原則: 写真は主役にしない。地色・罫線の"下"に沈める透かし。写真ゼロでも成立が基準(=写真は上位装飾スロット)。** 全てローカル同梱(`/assets/photos/`、ホットリンク禁止)。CSS変数 `url()` スロットで後差替。オーバーレイは地色(A=`#1F4B3E` / B=`#1B2A4A`)の multiply か薄膜グラデ。

### 案A(index.html)配置

| 場所 | 写真(trend-report番号) | 処理 |
|---|---|---|
| ヒーロー右上 透かし | #12 円形枯山水 / #14 庭園の小径 | 部分配置(右上1/3)・`opacity:.07`・深緑グラデ薄膜。h1と罫の下に沈める |
| セクション背景(featureの地) | #3 ピンクベージュ石材(温かい) | `opacity:.06`・`grayscale(1) sepia(.15)` デュオトーンをアイボリーに寄せる |
| grid(領域タイル)区切り帯 | #9 夕景スカイライン | `opacity:.08`・clip-path で斜め帯に細く(資産形成の広がり) |
| フッター | #2 白大理石の壁面 | `opacity:.05`・地色マルチプライで質感だけ |
| 金の抽象(任意・CTA hover) | #17 抽象ゴールド | CTA hover のグラデ参照のみ(面で敷かない) |

### 案B(jikabuka)配置

| 場所 | 写真(trend-report番号) | 処理 |
|---|---|---|
| ヒーロー背景 透かし(`.hero-wm`枠付近) | #6 大階段+シャンデリアの明ロビー / #5 装飾手すり | 部分配置・`opacity:.09`・ロイヤルブルー multiply。既存インラインSVG図版は前面維持 |
| answer / method セクション地 | #1 白大理石(青白い光) | `opacity:.06`・目地の質感のみ。テキスト可読最優先 |
| kpi 結果カード裏 | #7 パリ風金シャンデリア / #16 縦ラインの金 | `opacity:.10`・紺グラデに blend(評価額の格を上げる)。既存 `.kpi-wm` 透かしと二重にしない(どちらか) |
| formula(計算式)ブロック | #4 黒大理石 | `opacity:.12`・暗部アクセント(この1箇所だけ濃色地が許容=既存デザインが濃紺formulaのため踏襲) |
| footer.site | #8 タージマハル・ドーム(遠景) or #2 大理石壁 | `opacity:.05`・格式の余韻 |

- **A=庭園/自然光/温かい石(暮らしの豊かさ)、B=邸宅内装/建築/青白い石(資産・権威)** とテーマを棲み分け、写真だけでも別サイトに見せる(5軸「写真テーマ」)。
- どのセクションも「写真+ヘアライン1px+テキスト通常表示」の3層構造。写真の彩度・不透明度が上がって"賑やか"になったら compliance-qa 差し戻し。

---

## 4. コンポーネント別トリートメント

表記: 地色 / 罫 / 写真 / フォント / アクセント。**A→B の順で併記。**

### ヘッダー
- **A**: 地=`--bg`(アイボリー、暗い帯を廃止) / 下罫 1px `--line` / 写真なし / ブランド`--serif-jp` 深緑`--green` / emblem SVGは金グラデ維持(小)。現状は白文字前提だが**文字色を`--green`に反転**。
- **B**: `header.site` は現状 `background:var(--navy)`(濃紺帯)。**帯を廃し `--bg`(パール)地 + 下罫1px `--line`**。`.brand .mark` は`--serif`深紺`--navy`、`.sub`は`--muted`。`.navlink`は`--navy-2`。emblem金はアンティーク金へ。

### ヒーロー
- **A**: 地=`--bg`。h1=`--serif-jp` clamp(27→44px) 色`--green`。`.g`(現状金グラデ文字)→ **深緑ベース+金の下線/圏点1点**。eyebrowは金`--gold`の細ラインアイコン維持(小)。写真=庭園を右上`opacity.07`透かし。
- **B**: `.hero` の `linear-gradient(155deg,#0e1c31...)`(濃紺)→ **明るいパール/極薄スレートグラデ**(例 `linear-gradient(155deg,#F7F6F5,#EDEAE5)`)。`.hero h1`色`#fff`→`--navy`。`.lead`色→`--ink`。`.metaline`→`--muted`。CTA(`.hero .cta`)= アンティーク金グラデ維持(=金の正当な一点)。既存SVG図版(紙×紺)は明地でも映えるので維持。`.hero-wm`/`.hero-pulse` opacity据置。

### 直接回答ブロック(.answer / #directAnswer)
- **A**: 該当要素はポータルには無し(feature が相当)。feature: 地`--paper`/罫 1px `--gold`(左4px金アクセント可)/`.t`=`--serif-jp`深緑/`.d`=`--ink`/badge"公開中"は金グラデ小。hoverは`translateY(-2px)`+金罫濃く。
- **B**: `.answer` 現状=金箔枠+左4px金。**維持しつつ地を`--paper`(白)、`.k`ラベルはアンティーク金、本文`--ink`**。金箔グラデ枠(`::before`)の金をアンティーク金stopへ。

### 診断カード・入力(#wizard / .card / .opt / .field / input)
- **B のみ(Aに診断UIなし)**。`.card`地=`--paper`(白)/罫`--line`/柔影`--shadow-card`。`#wizard::before`上辺3px金→アンティーク金グラデ。`.opt`地=`--paper`罫`--line`、`.opt.sel`=罫`--gold`+地`#FBF3E2`系の淡金(既存踏襲・彩度は上げない)。`.opt input` accent=`--gold`。入力欄=白地`--paper`罫`--line`、focus outline=`--navy`(紺)。`.stepbar .seg.on`=金/`.done`=紺(既存ロジック維持)。ラベル`--ink`、hint`--muted`。

### 結果KPI(.kpi / #totalVal / .stat / .breakdown)
- **B のみ**。`.kpi` 現状=濃紺グラデ+金枠(評価額の主役)。**この1箇所は濃紺地を許容**(明基調の中の"重心"として正当、金でなく紺で締める)。ただし紺は`--navy`系へ更新、金枠はアンティーク金。`#totalVal`=`--num`(Playfair)特大 clamp、`.yen`は金。`.stat`地=`--paper`罫`--line`、`.v`=`--serif`紺。`.breakdown`罫`--line`、数字は`--num`。
- **A**(将来KPIを持つ診断を足す場合): 同様だが重心色は`--green`、数字は`--num`(Cormorant)。

### 相談フォーム(.consult / .formcard / #leadForm / .btn)
- **B のみ**。`.consult` 現状=濃紺グラデ。**明基調に合わせ濃度を下げた紺**(例 `linear-gradient(180deg,#243b63,#1B2A4A)`)へ、金枠アンティーク金。`.formcard`=白`--paper`罫`--line`。入力欄=白地。`.btn.primary`=`--navy`(紺)、`.btn.gold`(送信)=アンティーク金グラデ、`.btn.ghost`=白地紺文字紺罫。consent/turnstile据置。`.thanks .chk`=淡金地に金チェック。

### 方式解説(#method / .formula / .steps-ol)
- **B のみ**。`#method`背景 現状=クリームグラデ→ **`--bg-2`(マーブルグレージュ)グラデ**+上下罫`--line`。`.formula`=**濃紺地維持(黒大理石透かし #4 を`opacity.12`)** — 数式は濃地に金ハイライトが最も読みやすく格が出る(既存の意図を尊重)。`.hl`=金。`.steps-ol li::before`丸番号=`--navy`地に白`--serif`。

### FAQ(#faq / .faq details)
- **B**: 地`--bg`/各details下罫`--line`/summary`--serif`紺+`＋/－`アイコンはアンティーク金/回答`--ink`。写真なし(可読最優先)。
- **A**: ポータルにFAQ無し(将来追加時は同様、紺→緑・金はシャンパン金)。

### 区切り(.orn / .wave-divider)
- **A**: `.orn` = ラベル+金グラデ細線(`transparent→gold`)。シャンパン金。丸みラベル。
- **B**: `.orn` = 中央◇紋章(`#ornMark`)+左右金グラデ線。アンティーク金。`.wave-divider`(流水紋)= 金の細線 opacity据置。**SVG構造不可侵、色=currentColor をアンティーク金に。**

### フッター
- **A**: 地=`--bg`(明るいまま)/上罫1px`--line`/文字`--muted`/写真=大理石`opacity.05`任意。暗い帯にしない。
- **B**: `footer.site` 現状=濃紺帯。**明基調全体との整合で、濃紺のまま"締めの重心"として残すのは可**(ヒーローを明るくした分、フッターの紺は許容範囲/ただし`--navy`更新色)。文字`#c7d0de`系維持。写真=大理石/ドーム`opacity.05`任意。**A(明フッター)とB(紺フッター)の差もブランド差別化に寄与。**

---

## 5. 金の総量チェックリスト(compliance-qa 用・自己点検)

- [ ] 金の背景塗り(面)が無い。金は 1pxライン / 数値 / CTA / 印章SVG / アイコン細線 に限定。
- [ ] 金グラデの大ブロックが無い(CTAボタンと.answerの1px箔枠は可)。
- [ ] 画面スクロール1画面あたり金の可視面積が5%未満。
- [ ] A=シャンパン金 / B=アンティーク金 で質感が分かれている。
- [ ] 地色が明るい石/紙で70%以上を占める(kpi/formula/フッターの濃色は"重心"の例外として許容)。
- [ ] 写真の不透明度が 0.06〜0.12(kpiのみ最大.12)で、彩度が抑えられ透かしになっている。
- [ ] A と B を並べて別ブランドに見える(5軸)。
- [ ] jikabuka の DOM/id/class/JS が未変更(CSSと装飾スロットのみ)。

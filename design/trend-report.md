okane-carte.jp / jikabuka 明るい高級・富裕層デザイン刷新
トレンド調査レポート
============================================================

作成日: 2026-07-05
対象: ①okane-carte.jp（くらしと経済の無料診断ポータル） ②/jikabuka/（自社株・事業承継 相続税評価診断）
現状: 両サイトとも濃紺(#101f38系)×金(#a9843f)のダーク基調 → 脱・暗色、明るく上質・富裕層(HNWI/プライベートバンク層)を想起させる方向へ刷新。

---

## 0. 現状コードの確認（起点）

- `index.html` の `:root` で `--navy:#101f38; --navy2:#1b3058; --indigo:#22406e; --gold:#a9843f; --gold-hi:#e6c983` を確認。背景は `radial-gradient(...#1a2f56, #0c1a30)` の濃紺グラデ。
- `assets/fonts/` に `cormorant.css` `shippori.css` が既に存在（セルフホスト運用の土台は既にある）。`assets/photos/` にテスト画像あり（Unsplash/Pexels/picsum の3種テスト実績＝ローカル同梱運用が既に検証済み）。
- 方針: 既存の金(gold)ロジックとフォントのセルフホスト運用は活かしつつ、**背景・地色を暗→明**に反転し、ネイビーは「主張色」から「差し色/信頼アクセント」に格下げする。

---

## 1. カラーパレット2案

### 案A — okane-carte.jp ポータル本体（広い層の「明るい富裕」＝シャンパン×ディープグリーン）

くらし・生活全般の相談窓口として「間口は広いが上質」。プライベートバンクのラウンジ、老舗百貨店外商、鎌倉/京都の高級旅館フロントの明るさをイメージ。

| 役割 | 名称 | HEX | 用途・連想 |
|---|---|---|---|
| ベース(最明) | アイボリーホワイト | `#FBF7EF` | ページ地色。大理石ロビーの床のような温かい白 |
| ベース2 | シャンパンベージュ | `#F3EADA` | セクション背景の切替、カード地 |
| 主役色 | ディープグリーン(深緑) | `#1F4B3E` | 見出し・ロゴ・重要ライン。Harrods/老舗銀行を想起する「富の緑」 |
| 主役色2(サブ) | セージグリーン | `#7C9A82` | 補助アイコン・グラフの落ち着いた差し色 |
| 金・差し色 | シャンパンゴールド | `#C9A24B` | CTAボタン、数値・金額の強調、罫線 |
| 金・差し色(淡) | ペールゴールド | `#E7D3A1` | ホバー・グラデーション終点、微細な光沢演出 |
| 文字色(本文) | チャコールブラウン | `#2E2A24` | 本文。純黒を避け温かみを残す |
| 文字色(補助) | ストーングレー | `#6B6459` | キャプション・注記 |
| 境界線/罫 | ヘアラインベージュ | `#DCD0BC` | 1px罫線、区切り |

**連想の根拠**: 「Harrods emerald × brut champagne × ivory cream」の組み合わせは、シャンパンゴールドと柔らかいクリームが"報酬・洗練・長期的価値"を伝え、CTAや資産額のような重要数値に金を使い、チャコールで締めると高級銀行系の定番配色になるという分析と一致（ゾビズ社ラグジュアリーカラーガイド、iColorPalette調査）。緑×金は英国式デパート/老舗ブランドの「王道の富」の色。

### 案B — /jikabuka/ 自社株・事業承継診断（重厚な財務＝真珠×ロイヤルブルー、アンティークゴールド）

案Aとは明確に色相を変え、「相続税評価・M&A・財務」という重厚なテーマに寄せる。プライベートバンクの応接室、老舗信託銀行の格式、パールと紺碧の「静けさと格」。

| 役割 | 名称 | HEX | 用途・連想 |
|---|---|---|---|
| ベース(最明) | パールホワイト | `#F7F6F5` | ページ地色。真珠光沢のようなわずかに冷たい白 |
| ベース2 | マーブルグレージュ | `#EDEAE5` | セクション背景、カード地（大理石の目地色） |
| 主役色 | ロイヤルブルー(深紺) | `#1B2A4A` | 見出し・キーライン・図表。信託・格式・権威の色 |
| 主役色2(サブ) | ダスティスレート | `#4C5A78` | サブ見出し、グラフ背景 |
| 金・差し色 | アンティークゴールド | `#B08D45` | 数値強調、罫線、印章的アクセント |
| 金・差し色(淡) | サテンゴールド | `#D6BE84` | ホバー、細い光沢ライン |
| 文字色(本文) | インクグレー | `#2A2D33` | 本文。案Aの茶系文字と対比する冷たいグレー系 |
| 文字色(補助) | ミストグレー | `#767C87` | 注記・出典 |
| 境界線/罫 | ヘアラインスレート | `#D8DBE0` | 1px罫線、表組み罫線 |

**差別化オプション**: ボルドー×アンティークゴールド案（`#5C2A34` 深いボルドー + `#B08D45`）も可。ただし相続税・自社株は「財務の重厚さ」を最優先するため、本案は落ち着いた信頼色であるロイヤルブルー系を第一候補とし、ボルドー案は季節キャンペーン等のバリエーションとして温存する。

### 2案が「別サイト」に見える差別化の指針

1. **色相を対極に振る**: Aは緑(暖色寄りの自然色)、Bは紺(寒色寄りの格式色)。同じ「金」を差し色に使っても、地の色相が違うため印象が別ブランドになる。
2. **ベースの温度感を変える**: Aはアイボリー(黄み)、Bはパール(青白み)。並べたときに明確に「あたたかい」「ひんやりした格式」の対になる。
3. **金の質感を変える**: Aは「シャンパンゴールド」＝軽く明るい金、Bは「アンティークゴールド」＝くすんだ真鍮寄りの金。金度数を変えることで重さの違いを演出。
4. **罫線とタイポの太さ**: Aはやや丸みのある明朝と細罫線で「親しみ+上質」、Bは直線的な罫線とレターケーシング(字間広め大文字)で「格式+専門性」。
5. **写真テーマの棲み分け**: Aは庭園・自然光・調度品などの「暮らしの豊かさ」、Bは大理石・高層スカイライン・建築ディテールなどの「資産・権威」。

---

## 2. フリー写真の透かし活用（テーマ別・実在URL）

すべてダウンロードしてローカル保存（`assets/photos/` 配下、CSS変数スロット方式で後差替）する前提。ホットリンク禁止のルールに準拠。Unsplash Licence / Pexels License はいずれも商用可・帰属表記不要。

### テーマ1: 大理石・上質な質感（案A・案B共通の背景透かし向き）
1. `https://images.unsplash.com/photo-1566041510394-cf7c8fe21800` — 白大理石クローズアップ（案B背景向き、青白い光）
2. `https://images.unsplash.com/photo-1558346648-9757f2fa4474` — 白大理石の壁面（広い余白があり見出し背景に最適）
3. `https://images.unsplash.com/photo-1554755229-ca4470e07232` — ピンクベージュの石材質感（案A向き、温かい色味）
4. `https://images.unsplash.com/photo-1550053808-52a75a05955d` — 黒大理石クローズアップ（フッターや区切りセクションの暗部アクセントに）

### テーマ2: ラグジュアリー建築/邸宅内装（信頼・格の象徴、案B向き中心）
5. `https://images.pexels.com/photos/34971588/pexels-photo-34971588.jpeg` — 装飾的な手すりとシャンデリアのある階段
6. `https://images.pexels.com/photos/8092431/pexels-photo-8092431.jpeg` — 大階段とシャンデリアのある明るいロビー
7. `https://images.pexels.com/photos/34136612/pexels-photo-34136612.jpeg` — パリ風建築の金色シャンデリアと階段のディテール
8. `https://images.pexels.com/photos/10902405/pexels-photo-10902405.jpeg` — タージマハル・パレスホテルの歴史的ドーム建築（格式の象徴、遠景で使用）

### テーマ3: 夕景の都市スカイライン（案A=経済全体の広がり、資産形成のイメージ）
9. `https://images.unsplash.com/photo-1590622594883-e3096eb84e9e` — 夕景シルエットの都市スカイライン
10. `https://images.unsplash.com/photo-1727163941304-f8a0bd94f52b` — 都市スカイラインに沈む夕日
11. `https://images.unsplash.com/photo-1727163941327-f015aa272761` — 水面越しに見る夕景都市（水面反射が高級感を強める）

### テーマ4: 静かな自然・庭園（案A=暮らしの豊かさ・和の静けさ）
12. `https://images.unsplash.com/photo-1674893168376-c3d8efc23906` — 円形の枯山水、石庭のミニマルな構図
13. `https://images.unsplash.com/photo-1672758688257-a110c93de407` — 日本庭園と建築物
14. `https://images.unsplash.com/photo-1674255960810-8b2f2eab5b58` — 日本庭園の小径（木々と石畳）

### テーマ5: 金の抽象テクスチャ（差し色・オーバーレイ用、両案共通）
15. `https://images.unsplash.com/photo-1545873509-33e944ca7655` — ゴールドメタリックフォイルの質感（Hero背景の低不透明度オーバーレイ向き）
16. `https://images.unsplash.com/photo-1517196084897-498e0abd7c2d` — 縦ラインの入ったゴールドメタリック背景（区切りセクションのアクセントに）
17. `https://images.unsplash.com/photo-1760784213096-4545961ba4a8` — 光の反射を伴う抽象的ゴールド背景（ボタンhover用グラデ参照）

### テーマ6: 上質な調度・ディテール（案B=財務・専門性の権威づけ）
18. `https://images.pexels.com/photos/33599113/pexels-photo-33599113.jpeg` — 大理石とダブルシンク、間接照明の上質バスルーム（質感見本として、UIの背景トリミング用）

**使用手法（コード転載なし・原則のみ）**:
- **オーバーレイ**: 上記写真の上に地の色(案Aは`#1F4B3E`、案Bは`#1B2A4A`)を `mix-blend-mode: multiply` または線形グラデーション `rgba(色,0.85)→rgba(色,0.55)` で重ね、彩度を落として「透かし」化する。
- **低不透明度の背景装飾**: セクション背景に写真を `opacity: 0.06〜0.12` 程度で敷き、その上にテキストと罫線を通常表示。ヘアライン(1px罫)と組み合わせると「編集ミニマル×写真」の共存が破綻しない。
- **デュオトーン化**: CSS `filter: grayscale(1) sepia(.2)` 等でモノトーン化した上に主役色のグラデーションを `background-blend-mode` で重ね、案A/案Bそれぞれの色相に統一する。
- **マスク**: `clip-path` で写真を弧・斜めラインなど有機的な形にトリミングし、直線的なカード全面ではなく「一部だけ覗く」ように配置する（大理石・建築ディテール系に効果的）。
- **部分配置**: フルブリードで使わず、Hero右1/3や罫線の裏など「余白の中の一区画」に収める。写真を主役にせず、地色と罫線の下に控えめに置くことで「編集ミニマル×富裕層の静けさ」を両立させる（web-editorial-minimal.md の既定思想を継承）。

---

## 3. フォントの多様化（サイト別ペアリング・セルフホスト前提）

両サイトとも OFL(SIL Open Font License) 系でセルフホスト可能なフォントのみを採用。既存 `assets/fonts/cormorant.css` `shippori.css` の資産を活かしつつ、案A/案Bで組み合わせを変える。

### 案A（okane-carte.jp ポータル）— 親しみ+上質、丸みのある明朝

| 用途 | フォント | 入手元 |
|---|---|---|
| 和文見出し | Shippori Mincho B1（角の丸い柔らかい明朝、筆致がやや温かい） | https://fonts.google.com/specimen/Shippori+Mincho+B1 |
| 和文本文 | Zen Kaku Gothic New（可読性の高いゴシック、本文向け） | https://fonts.google.com/specimen/Zen+Kaku+Gothic+New |
| 欧文見出し/ロゴ | Marcellus（優美で控えめなセリフ、ワードマーク向き） | https://fonts.google.com/specimen/Marcellus |
| 数字・金額 | Cormorant（Garamond由来の繊細なディスプレイセリフ、桁の大きい数字を上質に見せる） | https://fonts.google.com/specimen/Cormorant |

構成方針: 見出し=Shippori Mincho B1（和文）+ Marcellus（欧文ロゴ・英字見出し）、本文=Zen Kaku Gothic New、金額・統計数字=Cormorantの数字（オールドスタイル数字風の落ち着いた見え方）。既存の `shippori.css` はそのまま流用し、ウェイト違い（B1の方が親しみ寄り）に差し替える。

### 案B（/jikabuka/ 自社株・事業承継診断）— 格式・専門性、直線的な明朝

| 用途 | フォント | 入手元 |
|---|---|---|
| 和文見出し | Zen Old Mincho（伝統的な旧字形寄りの明朝、格式が高い） | https://fonts.google.com/specimen/Zen+Old+Mincho |
| 和文本文 | Noto Serif JP（もしくは既存指針のNoto系ゴシック本文、可読性最優先） | https://fonts.google.com/noto/specimen/Noto+Serif+JP |
| 欧文見出し/ロゴ | Cormorant Garamond（Cormorantよりやや落ち着いた字幅、財務資料と相性が良い） | https://fonts.google.com/specimen/Cormorant+Garamond |
| 印章・ラベル的強調 | Cinzel（ローマ碑文由来の格調高い大文字専用書体。全角大文字+字間広めでロゴマーク・認定バッジ的に使用） | https://fonts.google.com/specimen/Cinzel |
| 数字・金額 | Playfair Display（数字の対比が強くコントラストがあり、金額の桁の説得力を演出） | https://fonts.google.com/specimen/Playfair+Display |

構成方針: 見出し=Zen Old Mincho（和文）+ Cormorant Garamond（欧文見出し）、本文=Noto Serif JP or Zen Kaku Gothic New（可読性優先で本文はゴシックに寄せても可）、数字=Playfair Displayの数字（強いコントラストで「評価額」を際立たせる）、Cinzelは「事業承継診断」等の認定バッジ・ラベル用に極小使用（多用禁止、字間広め・全角大文字限定）。

**案A/案Bのフォント差別化ロジック**: Aは「丸みのあるB1明朝×Marcellus×Cormorant」で温かく親しみやすい上質、Bは「旧字形寄りのOld Mincho×Cormorant Garamond×Playfair Display+Cinzel」で直線的・権威的な専門性。同じ明朝でも「柔らかい系(Shippori Mincho B1)」と「格式系(Zen Old Mincho)」を使い分けることで、フォントだけでも別サイトに見える設計。

---

## 4. 参考にした構造・原則（転載なし・URLのみ併記）

以下は構造・原則のみを抽出し、ビジュアル/コードの模倣は行っていない。

- Awwwards 不動産/ラグジュアリーカテゴリ — フルブリード写真とシネマティックなヒーロー映像、緩やかなパララックス/GSAPで「静かな高級感」を演出する構造原則。 https://www.awwwards.com/websites/real-estate/ / https://www.awwwards.com/websites/luxury/
- Awwwards Elyse Residence（Honorable Mention） — 「timeless refinement」を掲げる不動産サイトの落ち着いたレイアウト原則。 https://www.awwwards.com/sites/elyse-residence
- Awwwards Contemporary Hotels — ホテル横断ギャラリーの「Discover the world in Luxury」訴求構造。 https://www.awwwards.com/sites/contemporary-hotels
- SiteInspire — Stack Asset Management（資産運用会社のサイト事例、Finance & Businessカテゴリ）。 https://www.siteinspire.com/website/13111-stack-asset-management
- Land-book Financeカテゴリ — 金融特化ギャラリー、業界横断の配色・余白トレンドの定点観測先。 https://land-book.com/
- 老舗百貨店/英国式ラグジュアリーの配色分析（Harrods emerald×champagne×ivory cream の組み合わせ根拠） — https://zoviz.com/blog/luxury-brand-colors-meanings
- Old Money(オールドマネー)配色分析（ivory/camel/olive/navy/charcoalの落ち着いた高級配色の根拠） — https://www.backgroundremover.com/color-palettes/old-money-aesthetic / https://icolorpalette.com/color/old-money/
- フォント選定の裏付け（Shippori Mincho/Zen Old Mincho の性格分析、Cormorant/Cinzelのラグジュアリー適性） — https://fonts.google.com/specimen/Shippori+Mincho+B1 / https://fonts.google.com/specimen/Zen+Old+Mincho / https://www.fontpair.co/fonts/google/shippori-mincho / https://madegooddesigns.com/best-luxury-fonts/

---

## 総括

現状の「暗い濃紺×金」は金融サイトとして無難だが、富裕層(HNWI/プライベートバンク層)が求める"静けさ・格・軽やかさ"よりも、量産的なフィンテック感を残してしまっている。今回の調査で確認できた最新トレンドは、黒×ネオンではなく「アイボリー/パールのような明るいベースに、緑または紺の深色を主役として少量置き、金は"小さな差し色"としてCTAや数値だけに使う」という抑制型のラグジュアリー配色であり、これは既存コードの `--navy` と `--gold` の関係を反転させるだけで移行可能な設計である。案A(シャンパン×ディープグリーン)はokane-carte.jpの「間口は広いが上質」というポータル性格に、案B(パール×ロイヤルブルー+アンティークゴールド)は/jikabuka/の「相続税評価・事業承継という重い財務テーマ」に対応させ、色相・金の質感・フォントの直線性(丸い明朝 vs 旧字形明朝)という3つの軸で明確に別サイトとして識別できるよう設計した。写真は主役にせず、大理石・邸宅内装・夕景スカイライン・庭園・金の抽象テクスチャを低不透明度やデュオトーンで「透かし」として使うことで、CLAUDE.mdの編集ミニマル標準(大胆な余白・ヘアライン・差し色1色)とラグジュアリー感を両立できる。次工程(design-director/site-builder)では、本レポートのHEXコード・フォント指定・写真URLをそのままCSS変数とローカル画像アセットに落とし込み、compliance-qaで「金の使用量が過多になっていないか(小さな差し色に留まっているか)」を重点チェック項目に加えることを推奨する。

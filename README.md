# お金のカルテ — 自社株評価診断（M&Aリード獲得装置）

非上場株式（自社株）の相続税評価額を、国税庁の**類似業種比準方式（簡易版）**で概算するブラウザ内シミュレーターです。
無料診断を入口に、事業承継を控えた非上場企業オーナー（＝M&Aの売り手見込み客）から「概算評価額を算出済みの濃いリード」を獲得します。

- 本番：**https://okane-carte.jp/jikabuka/** （GitHub Pages 配信・CNAME は触らない）
- 計算はすべてブラウザ内で完結。外部API・生成AIを一切呼ばない（**継続課金ゼロ**）。
- リード受信のみ Google Apps Script（無料枠）を使用。

## ディレクトリ構成（サブディレクトリ方式）

`okane-carte.jp` では複数の診断サイトを作るため、各診断は**サブディレクトリ**に置きます。ルートは診断ポータル、この自社株評価診断は `/jikabuka/` です（診断を増やすときは `/xxx/` フォルダを足すだけ・相対パスなので移設耐性あり）。

| パス | 役割 |
|---|---|
| `index.html`（ルート） | 診断ポータル（各診断への入口）。現状は準備中＋自社株診断へのリンク。noindex。 |
| `jikabuka/index.html` | 自社株評価 診断本体（診断フロー→計算→結果→相談フォーム）。GEO/AEO・セキュリティ・華やか意匠（インラインSVGの印章エンブレム／脈波→株価ライン／台帳罫）全込みの単一HTML。 |
| `jikabuka/config.json` | 業種標準値・免責文・会社規模ルール・相談先・GAS/exec URL・Turnstile sitekey。**非エンジニアが書き換える設定ファイル。** |
| `gas/receiver.gs` | リード受信バックエンド（Turnstile検証・スクリプトプロパティ・シート蓄積・メール通知・honeypot）。GAS側に貼る。 |
| `robots.txt` / `sitemap.xml` | ドメイン直下（SEO標準）。sitemap は `/jikabuka/` を指す。 |
| `CNAME` | 独自ドメイン設定（`okane-carte.jp`）。**絶対に触らない。** |

> 透かし意匠は全てインラインSVG（外部画像ホットリンクなし＝セキュリティ標準準拠）。写真OGPを使う場合のみ `jikabuka/assets/ogp.png` をローカル同梱。

---

## 1. 計算ロジックと出典

### 類似業種比準方式（財産評価基本通達 180）

```
1株(50円換算)当たり比準価額
  = A × ( (b/B + c/C + d/D) ÷ 3 ) × 斟酌率

  A,B,C,D … 類似業種の 株価 / 1株当たり配当 / 1株当たり利益 / 1株当たり簿価純資産（業種別）
  b,c,d   … 評価会社の 1株(50円換算)当たり 配当 / 利益 / 簿価純資産
  斟酌率  … 大会社 0.7 ／ 中会社 0.6 ／ 小会社 0.5

1株当たり評価額 = 比準価額(50円) × ( 1株当たり資本金等の額 ÷ 50 )
```

- 3要素（配当・利益・純資産）の加重は現行 **1：1：1**。平成29年（2017年）改正前は利益 c/C を3倍に加重していた（1：3：1）。
- 会社規模は、従業員数・総資産価額・取引金額から **大会社／中会社／小会社** に区分（従業員70人以上は一律大会社）。

**出典（要点は上記の通り。最新の正確な計算・標準値は下記一次情報を必ず参照）：**
- 国税庁 財産評価基本通達 180「類似業種比準価額」 https://www.nta.go.jp/law/tsutatsu/kihon/sisan/hyoka_new/08/03.htm
- 国税庁 「類似業種比準価額計算上の業種目及び業種目別株価等について」（毎年度公表・A/B/C/Dの標準値） 例：令和6年分 https://www.nta.go.jp/law/tsutatsu/kobetsu/hyoka/r06/2406/index.htm
- 国税庁 財産評価基本通達 178「取引相場のない株式の評価上の区分（会社規模の判定）」

### 本ツールの簡略化（＝概算である理由・免責の根拠）

正確な税額計算ではなく「おおよその目安」です。以下を簡略化しています（`index.html` 冒頭コメント・結果画面・免責にも明記）。

1. **標準値 A/B/C/D はサンプル値**。実際は国税庁が業種別に毎年更新・公表する値を使う。→ 年度更新が必要（下記2章）。
2. **配当は直前期の年額**を使用（正式には直前2期の平均）。
3. **会社規模は従業員数と総資産の下位区分で判定**（正式判定で使う取引金額・中会社の細区分〈L=0.90/0.75/0.60〉は省略）。
4. **純資産価額方式との併用を行わない**。中会社・小会社は本来この方式と併用するため、概算額と実際の評価額が乖離することがある。
5. 業種区分は大分類のみ（正式には細かい業種目番号で判定）。

### なぜ「資本金等の額」を入力に追加したか（仕様からの追加点）

当初仕様の入力は「業種・配当・利益・簿価純資産・発行済株式数・会社規模」でしたが、
類似業種比準方式は **1株当たり資本金等の額を50円に換算** して計算する方式のため、
`資本金等の額` が無いと 50円換算株式数（＝資本金等の額 ÷ 50）が定まらず、金額が数十〜数百倍ずれて**意味のある概算になりません**。
そこで正式手順に合わせ `資本金等の額` を入力に追加しました（決算書・登記簿から転記できる項目で、オーナーの負担は小さい）。

---

## 2. 標準値（A/B/C/D）の年度更新方法

`jikabuka/config.json` の `industries` 配列を書き換えるだけです（コード変更不要・再デプロイ不要、`?t=` で即反映）。

```json
{ "key": "manufacturing", "label": "製造業", "sizeGroup": "other",
  "A": 300, "B": 5.0, "C": 35, "D": 350 }
```

- `A`＝類似業種の株価、`B`＝1株当たり配当、`C`＝1株当たり利益、`D`＝1株当たり簿価純資産（いずれも1株=50円換算）。
- 最新値は国税庁「業種目別株価等」（毎年6月頃に前年分が公表）から、該当業種目の数値を転記する。
- `sizeGroup` は会社規模判定のグループ：`wholesale`（卸売業）／`retail_service`（小売・サービス業）／`other`（それ以外）。

> 標準値はサンプルのため、断定表示はせず「正確な評価には最新年度の公表値と税理士確認が必要」と免責に明記しています（`jikabuka/config.json > disclaimer`）。

---

## 3. GAS（リード受信）のセットアップ ★方法B・共通の受け皿（設定は一度きり）

`gas/receiver.gs` は **全診断の共通レシーバ**。1回作れば、今後増える診断（家計・相続・住まい…）も同じ `/exec` を使い回せる。
問い合わせは1枚のシートに「**診断**」「**診断サマリー**」列付きで溜まるので混ざらない。**方法B（スプレッドシートの中から作る）＝ SHEET_ID 不要。**

### 3-1. スプレッドシート＋Apps Script（SHEET_ID 不要）
1. Google スプレッドシートを新規作成（名前は「お金のカルテ_リード」など）。
2. そのシートの上メニュー **「拡張機能」→「Apps Script」** を開く。
3. 開いた編集画面に `gas/receiver.gs` の中身を丸ごと貼り付けて保存。
   - ※これで「このシート自身」に書き込む構成になり、**SHEET_ID の控えは不要**。

### 3-2. スクリプトプロパティ（秘密情報）を登録
プロジェクトの設定（歯車）→ **スクリプト プロパティ**：

| プロパティ名 | 値 | 必須 |
|---|---|---|
| `NOTIFY_TO` | 通知先メール（例 `info@livmakers.co.jp`）。個人でなく共有アドレス。 | **必須** |
| `ALLOWED_HOSTS` | `okane-carte.jp,www.okane-carte.jp` | 推奨 |
| `TURNSTILE_SECRET` | Turnstile シークレットキー（下記4章。後日でも可） | 任意 |
| `SHEET_ID` | 別のシートに書きたいときだけ設定（方法Bでは**不要**） | 不要 |

> **HTML・リポジトリには宛先メールを一切書きません。**すべてスクリプトプロパティに隔離（`web-security-baseline` A/C 準拠）。

### 3-3. ウェブアプリとしてデプロイ
1. 右上「デプロイ」→ **新しいデプロイ** → 種類「ウェブアプリ」。
2. **実行するユーザー：自分** ／ **アクセスできるユーザー：全員**。初回は権限承認。
3. 発行された **`/exec` URL** を控える。

### 3-4. フロントに接続（新しい診断もこの1行だけ）
`jikabuka/config.json`（以後の診断も各 `config.json`）の `gas.endpoint` に `/exec` URL を設定する。

```json
"gas": { "endpoint": "https://script.google.com/macros/s/XXXX/exec", "turnstileSitekey": "0x4AAA..." }
```

- フロントは `fetch(..., { mode:'no-cors' })` の fire-and-forget で送信します（GASはCORSヘッダを返さないため、レスポンスは読まず送信成功として「送信ありがとうございます」を表示。bot/スパムの排除と記録・通知はGAS側で完結）。
- コード更新時は「デプロイを管理」→ 既存デプロイを**編集して新バージョン**にすると `/exec` URL は変わりません（URL維持）。

---

## 4. Cloudflare Turnstile

1. Cloudflare ダッシュボード → Turnstile → サイトを追加（ドメイン `okane-carte.jp`）。
2. **サイトキー** を `jikabuka/config.json > gas.turnstileSitekey` に設定（公開情報でOK）。
3. **シークレットキー** を GAS のスクリプトプロパティ `TURNSTILE_SECRET` に設定（**HTMLに書かない**）。
4. sitekey 未設定（`__TURNSTILE_SITEKEY__` のまま）の場合、フロントはTurnstileを読み込まず、GASも検証をスキップします（段階導入可）。

---

## 5. セキュリティ（web-security-baseline 準拠）

- **CSP（meta）**：自サイト＋Turnstile＋GAS送信先のみ許可。`object-src 'none'`。
- **クリックジャッキング対策**：frame-busting JS（metaでは `frame-ancestors` が効かない静的ホスティングの補完）。
- **フォーム**：honeypot（`website`）／サーバー側バリデーション／ヘッダインジェクション対策（改行除去）／各項目の最大長／送信元ホスト許可リスト（`ALLOWED_HOSTS`）。
- **秘密情報を置かない**：宛先メール・APIシークレットはGASのスクリプトプロパティのみ。リポジトリにコミットしない。
- **接続情報をAIに渡さない**：デプロイ・FTPはBOSS本人が実施。
- **画像**：外部ホットリンク禁止。OGP等は `assets/` にローカル同梱する（`assets/ogp.png` を配置）。

## 6. 公開（go-live）手順

1. `jikabuka/index.html` の `<meta name="robots" content="noindex, nofollow">` を **`index, follow`** に切替（＝公開ボタン）。あわせて `jikabuka/config.json > meta.indexable` を `true` に。ルート `index.html`（ポータル）も公開する場合は同様に切替。
2. Google Search Console でドメイン所有権を確認し、`sitemap.xml`（必要なら追加）を送信、トップURLをインデックス登録リクエスト。
3. メール送信を伴うため、必要に応じて **SPF / DKIM / DMARC** を設定。
4. GitHub アカウントの **2FA** を確認（乗っ取り対策）。

---

## 7. BOSSが埋める実データ（プレースホルダ一覧）

`jikabuka/config.json` 内の `__...__` を実データに置き換えてください。

1. **`gas.endpoint`** … GASデプロイ後の `/exec` URL。
2. **`gas.turnstileSitekey`** … Cloudflare Turnstile のサイトキー。
3. **`consult.orgName` / `orgTagline` / `contactLine`** … リブメーカーズの相談先表示文言・会社情報。
4. GASスクリプトプロパティ4つ … `NOTIFY_TO`（グループ共有アドレス）／`SHEET_ID`／`TURNSTILE_SECRET`／`ALLOWED_HOSTS`。
5. （任意）`assets/ogp.png` … OGP画像をローカル同梱。

> **免責**：本サイトは自社株評価の概算を提供する情報サービスであり、税務・法務・投資助言ではありません。正確な評価額の算定・申告は税理士等の専門家にご確認ください。

---

# 付録：不動産かんたん評価診断（/fudosan/）— 不動産の売却/購入/相続リード獲得装置

自宅・収益物件・相続不動産の価値を「積算・収益・税務」の3レイヤーで**匿名・ブラウザ内**概算し、固有の「不動産カルテ指数」を発行するサブサイト。**一括査定サイトの逆設計（比較しない・営業電話なし・匿名・物件データを外部送信しない）**をポジショニングの核とし、売却/購入/相続の相談リードを リブアセッツ宛に獲得する。

## F-1. ディレクトリ構成

```
fudosan/
├─ index.html              # 診断本体（案C：等高線×スレートティール×陶土。3レイヤー診断＋カルテ発行演出）
├─ config.json             # ★唯一の真実。数値テーブル・免責・出典・指数定義・フォーム文言。診断とpSEOビルドが共有
├─ index-definition/       # 「不動産カルテ指数」算出式の完全公開ページ（GEO一次ソース）
├─ sources/                # 全数値テーブルの出典・確認日一覧
├─ p/                      # pSEO量産ページ（build_fudosan.py が生成）
│   ├─ index.html          # 早見表ハブ
│   ├─ zanka/{構造}-{築年}/ # 建物残価率 早見（構造4×築年6 ≒ 24p）
│   ├─ rimawari/{エリア}-{築年帯}/ # 想定利回り 早見（エリア5×築年帯4 = 20p）
│   └─ assets/pseo.css     # pSEO共有CSS
└─ assets/
    ├─ img/*.webp          # 装飾透かし写真（Unsplash・CREDITS.md）
    ├─ ogp.jpg             # OGP（1200×630）
    └─ CREDITS.md          # 画像ライセンス台帳
scripts/build_fudosan.py    # pSEO静的量産スクリプト（Python3 stdlib）
```

## F-2. 計算ロジックと出典（3レイヤー＋不動産カルテ指数）

- **積算**＝ 土地面積×エリア㎡単価（路線価入力時は路線価÷0.8で逆算）＋ 延床×構造別再調達価格×残価率〔残価率=(法定耐用年数−築年)/法定耐用年数、下限 salvageFloor〕。
- **収益**（収益物件のみ）＝ 年間家賃×稼働率×(1−運営費率) ÷ 想定還元利回りレンジ。
- **税務**＝ 土地(路線価≒公示地価×0.8) ＋ 建物(固定資産税評価の目安)〔賃貸中は貸家建付地・貸家の評価減〕。市場価値との**ギャップ率**を可視化。
- **不動産カルテ指数(0-100)**＝ 収益性×流動性×税務効率 の加重合成。定義・重み・バンドは `fudosan/index-definition/` で完全公開。
- 出典（確認日 2026-07-07）：国税庁「建物の標準的な建築価額表」令和5年（再調達価格）／国税庁 法定耐用年数（No.2100・耐用年数省令）／日本不動産研究所 第53回不動産投資家調査 2025年10月（想定利回り）／国交省 令和7年地価公示（地価水準）／国税庁 財産評価基本通達（路線価8割・借家権割合30%・貸家建付地26・貸家93・小規模宅地 No.4124）。全出典は `fudosan/config.json > sources[]` と `fudosan/sources/` に一覧。

## F-3. 数値テーブルの年度更新（市場変動値）

`fudosan/config.json > data` の **市場変動値**は毎年更新する（制度値は税制改正時のみ）。
- `structures[].replacementCost` … 国税庁「建物の標準的な建築価額表」最新年で更新。
- `capRates` … 日本不動産研究所 不動産投資家調査（半期）で更新。
- `areas[].landPrice` … 国交省 地価公示（毎年3月）で更新。
- 更新後は **`python scripts/build_fudosan.py` を再実行**して早見ページを作り直す（config が唯一の真実）。

## F-4. GAS / Turnstile

**GAS は jikabuka と同じ共通レシーバ（`gas/receiver.gs`）を流用**。`fudosan/config.json > gas.endpoint` は稼働中の共通 `/exec` を初期設定済み（`formName` で診断が区別され同一シートに集約）。個人オーナー向けに会社名は不要のため、送信時に hidden `company` を `gas.companyFallback`（「（個人・不動産カルテ）」）で自動補完し、GAS の必須チェックを満たす（**GAS 改修不要**）。Turnstile は `gas.turnstileSitekey` を実キーに差し替えると自動で有効化・サーバー側検証が働く。

## F-5. 公開（go-live）手順（/fudosan/）

1. 以下すべての `<meta name="robots" content="noindex, nofollow">` を **`index, follow`** に切替（＝公開ボタン）：
   `fudosan/index.html` / `fudosan/index-definition/index.html` / `fudosan/sources/index.html`。あわせて `fudosan/config.json > meta.indexable` を `true` に。
2. pSEOページの index 化は **`scripts/build_fudosan.py` の noindex 定数を index に変えて再実行**（全 `fudosan/p/` を一括再生成）。
3. `sitemap.xml` に `fudosan/p/_urls.txt` の全URLが反映されていることを確認（本リポジトリでは統合済み。ページ追加時は `_urls.txt` を基に再統合）。
4. Google Search Console でドメイン所有権を確認し、`https://okane-carte.jp/sitemap.xml` を**再送信**、`/fudosan/` と `/fudosan/index-definition/` をインデックス登録リクエスト。
5. CNAME は絶対に触らない（GitHub Pages のカスタムドメイン設定）。相対パスのため /fudosan/ 一式はサブディレクトリのまま移設可。

## F-6. BOSSが埋める実データ（/fudosan/ プレースホルダ）

`fudosan/config.json` 内の `__...__` を実データに置換：
1. **`gas.turnstileSitekey`** … Cloudflare Turnstile サイトキー（GAS `/exec` は共通レシーバ流用のため設定済み）。
2. **`consult.orgName` / `orgNamePlaceholder` / `contactLine`** … 相談先「リブアセッツ」の正式会社名・宅建業免許番号・住所・電話。
3. （GAS 側スクリプトプロパティは jikabuka のセットアップ済みなら追加設定不要。`ALLOWED_HOSTS` に `okane-carte.jp` が含まれていることのみ確認）。

> **免責（宅建業法・税理士法）**：本サービスは公開データに基づく一般的な概算シミュレーションであり、宅地建物取引業者による査定・価格意見、不動産鑑定、税務相談ではありません。相続税評価の記述は「目安」です。実際の売買・相続・申告の判断は、宅地建物取引業者・不動産鑑定士・税理士にご確認ください。

---

# 付録：相続シリーズ（/sozoku/・/zoyo/・/fukuri/・/hayami/）— 相続・生前贈与・M&Aリード獲得装置

母屋・`/jikabuka/` のデザイントークン・GAS共通レシーバ・Turnstile構成・`config.json` 登録方式を継承したファミリー実装。対象読者は経営者以外も含む資産保有者全般。

## S-1. ディレクトリ構成

| パス | 役割 | robots |
|---|---|---|
| `sozoku/index.html` ＋ `config.json` | 相続税かんたん診断（母艦）。5〜8問→相続税の概算＋独自「相続準備指数」→「家族へのカルテ」発行→3方向リード出口。 | 公開前 noindex |
| `sozoku/index-definition/index.html` | 相続準備指数の算出式を完全公開する一次ソース（GEO被引用の核）。 | 公開前 noindex |
| `zoyo/index.html` ＋ `config.json` | 生前贈与診断（暦年課税 vs 相続時精算課税・渡しきれる総額タイムライン）→ /sozoku/ へ送客。 | 公開前 noindex |
| `fukuri/index.html` ＋ `config.json` | 複利体験シミュレーター（3/5/7%成長カーブ・将来成果非保証）→ /zoyo/→/sozoku/ へ送客。 | 公開前 noindex |
| `hayami/`（35ページ） | 相続税の概算早見表 pSEO（索引1＋構成別6＋総額別28）。`scripts/build_hayami.py` で生成。 | 公開前 noindex |
| `scripts/build_hayami.py` | 早見表ジェネレータ（Python・依存ゼロ）。詳細は `scripts/README-hayami.md`。 | — |
| `design/tax-sources.md` | 税制数値の出典・確認日台帳（全診断共通SSoT）。 | — |

## S-2. 計算ロジックと出典（design/tax-sources.md が正・2026-07-07確認）

- 相続税：基礎控除＝3,000万＋600万×法定相続人（No.4152）／生命保険非課税＝500万×人数（No.4114）／速算表10〜55%（No.4155・令和7年4月1日現在法令等）／配偶者の税額軽減＝1.6億か法定相続分の多い方（No.4158）／小規模宅地330㎡80%は「適用可能性フラグ」表示のみ（No.4124）。
- 生前贈与：暦年110万基礎控除（No.4402）／生前贈与加算3→7年・令和6年以後の贈与から・経過措置で令和13年満7年／相続時精算課税＝累計2,500万＋令和6年から年110万基礎控除（No.4103）。
- **相続準備指数**（独自一次データ）：指数＝100×R1^0.45×R2^0.30×R3^0.25（重み付き幾何平均）。R1=納税資金カバー率／R2=分割準備度／R3=生前対策着手度。定義ページで完全公開。
- 計算は全てブラウザ内完結（外部API・生成AIを呼ばない＝継続課金ゼロ）。財産・贈与・シミュレーション入力値はサーバー送信しない（フォーム連絡先のみ送信）。

## S-3. GAS / Turnstile（jikabuka と共通の受け皿を流用）

- 各 `config.json` の `gas.endpoint` は jikabuka と同一の `/exec`（全診断共通レシーバ）。`formName` で診断を判別し1枚のシートに蓄積。
- `turnstileSitekey` は各 `config.json` の `__TURNSTILE_SITEKEY__` を実サイトキーに置換（GAS側 `TURNSTILE_SECRET`・`ALLOWED_HOSTS=okane-carte.jp` は jikabuka セットアップ済みなら追加不要）。
- 個人向け診断のため、GAS必須項目 `company` にはフォームの「お名前」を充当（`submitLead` 参照）。

## S-4. 早見表の再生成
```bash
python scripts/build_hayami.py   # hayami/ 35ページ＋sitemap-hayami.xml を再生成（冪等）
```
起動時に自己検算（遺産5,000万・配偶者+子2人→総額20万/軽減後10万）を実行し、不一致なら停止。

## S-5. 公開（go-live）／デプロイ手順

1. **ローカル確認**：`python -m http.server`（またはプレビュー）で `http://localhost:8801/sozoku/` 等を表示確認。診断→結果→カルテ→フォーム、早見表の表・リンクを目視。
2. **noindex→index 切替（公開ボタン）**：公開する各ページの `<meta name="robots">` を `index, follow` に、各 `config.json > meta.indexable` を `true` に。早見表は `scripts/build_hayami.py` の `indexable=False`（`head_block` の既定）を `True` にして再生成、または一括置換。
3. **commit・push**：`git add` → `git commit` → `git push origin main`。**CNAME は絶対に触らない**（`okane-carte.jp`）。GitHub Pages が数分で反映。
4. **反映確認**：`https://okane-carte.jp/sozoku/`・`/zoyo/`・`/fukuri/`・`/hayami/` を実機表示確認（noindexのままでもURLは有効）。
5. **Search Console**：ドメイン所有権確認済みのプロパティで `sitemap.xml` を（再）送信。主要URLをインデックス登録リクエスト。
6. GitHub 2FA・（任意）SPF/DKIM/DMARC を確認。

## S-6. BOSSが埋める実データ（プレースホルダ一覧）

各 `sozoku/zoyo/fukuri/config.json` 内の `__...__`：
1. **`gas.turnstileSitekey`** … Cloudflare Turnstile サイトキー（`/exec` は共通レシーバ流用のため設定済み）。
2. **`consult.orgName` / `orgTagline` / `contactLine`** … 相談先「リブメーカーズ／リブアセッツ」の正式表示文言・会社情報。
3. （GAS スクリプトプロパティは jikabuka セットアップ済みなら追加不要。`ALLOWED_HOSTS` に `okane-carte.jp` が含まれることのみ確認。）
4. （任意）各 `assets/ogp.png` … OGP画像をローカル同梱（未配置時は `/sozoku/assets/ogp.png` を参照）。

> **免責（税理士法）**：本シリーズは相続・贈与に関する一般的な情報提供および概算シミュレーションであり、税理士法に定める個別の税務相談・税務代理・税務書類の作成を行うものではありません。fukuri は将来の運用成果を保証しない教育目的のシミュレーションです。正確な計算・申告・対策は税理士等の専門家にご確認ください。

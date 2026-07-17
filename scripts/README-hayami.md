# 相続税の概算早見表 pSEO ジェネレータ

`/hayami/` 配下に、相続税の概算早見表を **静的HTMLで35ページ量産**するスクリプトです。
GEO/AEO（検索・生成AIでの被引用）を狙い、各ページに固有の直答・表・FAQ・内部リンク・JSON-LDを持たせています。

## 実行

```bash
python scripts/build_hayami.py
```

- 出力：`hayami/`（`index.html` ＋ 構成別6 ＋ 総額別28 ＝ 計35ページ）＋ `hayami/sitemap-hayami.xml`
- 依存ゼロ（Python標準ライブラリのみ）。外部API・CDNなし。実行のたびに `hayami/` を作り直します（冪等）。

> **なぜPython版か**：当初 `scripts/build-hayami.mjs`（Node.js）で実装しましたが、本制作環境に Node.js が未導入だったため、
> **同一ロジック・同一URL体系・同一テンプレート**を Python に移植したのが `build_hayami.py` です（`/fudosan/` の `build_fudosan.py` と同じくPython系に統一）。
> `.mjs` は設計の記録として残置。今後の再生成は **`build_hayami.py` を正**とします。

## ページ構成（35ページ）

| 種別 | 枚数 | URL 例 |
|---|---|---|
| 索引トップ | 1 | `/hayami/` |
| 構成別一覧 | 6 | `/hayami/haigusha-ko2/`（配偶者＋子2人 等） |
| 遺産総額別 | 28 | `/hayami/isan-5000man/`（3,000万〜3億円・1,000万刻み） |

構成6種：`haigusha-ko1`／`haigusha-ko2`／`haigusha-ko3`／`ko2`（子のみ2人）／`ko3`（子のみ3人）／`haigusha-nomi`（配偶者のみ）。
各ページは相互に内部リンク（総額⇄構成が交差参照）し、診断本体 `/sozoku/`・定義 `/sozoku/index-definition/` へ送客します。孤立ページゼロ。

## 計算の一致と検算

税額計算は `sozoku/index.html` の `calc()`／`taxOn()` と**完全一致**（基礎控除3,000万＋600万×人数／速算表10〜55%／配偶者は法定相続分取得と仮定し(1−配偶者法定相続分)を掛ける）。
起動時に自己検算を実行し、不一致なら停止します：

```
遺産5,000万円・配偶者+子2人 → 基礎控除4,800万 / 課税遺産200万 / 総額20万 / 配偶者軽減後10万
```

**簡略化（各ページ免責に明記）**：早見表は「財産＝課税価格」とみなし、生命保険の非課税枠（500万×人数）・土地建物の個別評価・小規模宅地等の特例・二次相続は反映しません（概算の目安）。

## 出典（design/tax-sources.md と同一・2026-07-07確認）
- 基礎控除：国税庁 No.4152 ／ 速算表：No.4155（令和7年4月1日現在法令等）
- 生命保険非課税：No.4114（本表では不使用・注記のみ）／ 配偶者の税額軽減：No.4158

## sitemap への統合
`hayami/sitemap-hayami.xml` を生成後、ルート `sitemap.xml` に35ページ分を統合済み（索引 `/hayami/` は priority 0.7、個別ページは 0.5）。
再生成でURLが増減した場合は、ルート `sitemap.xml` の該当 `<url>` も合わせて更新すること。

## 公開前 / go-live
全ページは `<meta name="robots" content="noindex, nofollow">` で生成されます（公開前標準）。
go-live 時に index へ一括切替（全診断共通の公開手順に従う）。

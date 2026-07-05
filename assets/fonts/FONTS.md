# セルフホスト・フォント（すべて無料・商用可・SIL Open Font License）

外部CDNを使わず `/assets/fonts/` にローカル同梱（web-security-baseline 準拠：外部JS/CSS実行を避ける）。
すべて SIL Open Font License 1.1（OFL）。再配布時は各 OFL 条項に従う（本ディレクトリに license 同梱）。

| ファイル | フォント | 用途 | 出典 |
|---|---|---|---|
| `ShipporiMincho-Bold.subset.woff2` | Shippori Mincho（しっぽり明朝）Bold | サイトA 和文見出し（柔らかい明朝） | Google Fonts / OFL |
| `ZenOldMincho-Bold.subset.woff2` | Zen Old Mincho Bold | サイトB 和文見出し（格式の明朝） | Google Fonts / OFL |
| `Marcellus-400.woff2` | Marcellus | サイトA 欧文ロゴ・見出し | Google Fonts / OFL |
| `Cormorant-500/600.woff2` | Cormorant | サイトA 数字・繊細な欧文 | Google Fonts / OFL |
| `CormorantGaramond-500/600.woff2` | Cormorant Garamond | サイトB 欧文見出し | Google Fonts / OFL |
| `PlayfairDisplay-600/700.woff2` | Playfair Display | サイトB 数字・金額の強調 | Google Fonts / OFL |
| `Cinzel-600.woff2` | Cinzel | サイトB 認定バッジ・ラベル（極小使用） | Google Fonts / OFL |

- 和文フォントは巨大なため `subset` スクリプトで**実際に使う字形＋かな/ラテン/約物**に絞った `.subset.woff2` を配信（元TTFは配信しない）。
- 見出しの日本語を大きく変更した場合は、`design/subset-jp-fonts.py` を再実行して字形を追加すること（未収録字はシステム明朝にフォールバック）。
- OFL 全文：`OFL-ShipporiMincho.txt` / `OFL-ZenOldMincho.txt`（ラテン各フォントも同一 OFL）。

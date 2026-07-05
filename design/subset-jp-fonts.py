#!/usr/bin/env python
"""
和文フォント（Shippori Mincho / Zen Old Mincho）を、実際に使う字形＋かな/ラテン/約物に
絞って軽量 woff2 にサブセットする。見出しコピーを変更したら再実行すること。
  python design/subset-jp-fonts.py
元TTF（assets/fonts/*.ttf）は配信せず、生成された *.subset.woff2 のみ配信する。
"""
import subprocess, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 見出しに使われうる全テキストを収集（HTML/JSON/README）
SRC = ['index.html', 'jikabuka/index.html', 'jikabuka/config.json', 'README.md']
chars = set()
for f in SRC:
    p = os.path.join(ROOT, f)
    if os.path.exists(p):
        chars |= set(open(p, encoding='utf-8').read())
chars = {c for c in chars if ord(c) >= 0x20 and c not in '\r\n\t'}
charfile = os.path.join(ROOT, 'assets/fonts/_chars.txt')
open(charfile, 'w', encoding='utf-8').write(''.join(sorted(chars)))
# 安全域：ラテン/約物/かな/全角半角（本文外の予備）
RANGES = "U+0020-007E,U+00A0-00FF,U+2000-206F,U+2212,U+3000-303F,U+3040-30FF,U+FF00-FFEF"
FONTS = [
    ('assets/fonts/ShipporiMincho-Bold.ttf', 'assets/fonts/ShipporiMincho-Bold.subset.woff2'),
    ('assets/fonts/ZenOldMincho-Bold.ttf',   'assets/fonts/ZenOldMincho-Bold.subset.woff2'),
]
for src, out in FONTS:
    srcp, outp = os.path.join(ROOT, src), os.path.join(ROOT, out)
    if not os.path.exists(srcp):
        print('skip (missing):', src); continue
    subprocess.run([sys.executable, '-m', 'fontTools.subset', srcp,
        '--text-file=' + charfile, '--unicodes=' + RANGES,
        '--layout-features=*', '--flavor=woff2', '--output-file=' + outp], check=True)
    print('subset ->', out, os.path.getsize(outp) // 1024, 'KB')
os.remove(charfile)
print('done. 元TTFは配信しない（.gitignore 済み想定）。')

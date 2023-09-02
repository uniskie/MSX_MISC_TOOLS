# MSX画像ビューア ブラウザ版

SCREEN2～SCREEN12の画像を表示・変換保存可能なツールです。

- 変換保存時はグラフサウルス圧縮形式とBSAVEベタ形式が選択可能
- SCREEN5以上はインターレース画像に対応
- ※ SCREEN1以外に対応。SCREEN9は未テスト

![プレビュー](gsrle_html_preview.png)

ソースコード  
[https://github.com/uniskie/MSX_MISC_TOOLS/tree/main/GSRLE/html](https://github.com/uniskie/MSX_MISC_TOOLS/tree/main/GSRLE/html)

## github pages の WEBページでブラウザから直接実行

[https://uniskie.github.io/MSX_MISC_TOOLS/GSRLE/gsrle.html](https://uniskie.github.io/MSX_MISC_TOOLS/GSRLE/gsrle.html)

github pagesはdocsフォルダに手作業で移動しているので、更新は遅れるかもしれません。

## MSX実機でのロード

ローダーのサンプルがあります。

[https://github.com/uniskie/MSX_MISC_TOOLS/tree/main/LOADSRD](https://github.com/uniskie/MSX_MISC_TOOLS/tree/main/LOADSRD)

ビューアー・ローダーともに、
ソースコードの再利用はご自由にどうぞ。

## 対応拡張子

拡張子で判定して、インターレースモードでの読込先ページを決定します。

1. パレットの有無、画面サイズ、圧縮などはデータの内容を見て判定します。
2. SC1はSSCREEN12のインターレース画像として扱います。
3. SCREEN1画像の場合、SC1の代わりにSR1を使用してみてください。
4. SCREEN 9は未テストです。
5. 保存時は現在表示している縦サイズで保存します。

| 拡張子 | SCREEN番号 | インターレースモード | BSAVE拡張子 | GS拡張子 | 補足 |
|---|---|---|---|---|---|
| .SC2 | SCREEN  2 | non-interlace    | .SC2 |.SR2 | BSAVE
| .SC3 | SCREEN  3 | non-interlace    | .SC3 |.SR4 | BSAVE
| .SC4 | SCREEN  4 | non-interlace    | .SC4 |.SR3 | BSAVE
| .SC5 | SCREEN  5 | non-interlace    | .SC5 |.SR5 | BSAVE
| .SC6 | SCREEN  6 | non-interlace    | .SC6 |.SR6 | BSAVE
| .SC7 | SCREEN  7 | non-interlace    | .SC7 |.SR7 | BSAVE
| .SC8 | SCREEN  8 | non-interlace    | .SC8 |.SR8 | BSAVE
| .S10 | SCREEN 10 | non-interlace    | .S10 |.SRA | BSAVE
| .S12 | SCREEN 12 | non-interlace    | .S12 |.SRC | BSAVE
| .S50 | SCREEN  5 | interlace page:0 | .S50 |.R50 | BSAVE interlace
| .S51 | SCREEN  5 | interlace page:1 | .S51 |.R51 | BSAVE interlace
| .S60 | SCREEN  6 | interlace page:0 | .S60 |.R60 | BSAVE interlace
| .S61 | SCREEN  6 | interlace page:1 | .S61 |.R61 | BSAVE interlace
| .S70 | SCREEN  7 | interlace page:0 | .S70 |.R70 | BSAVE interlace
| .S71 | SCREEN  7 | interlace page:1 | .S71 |.R71 | BSAVE interlace
| .S80 | SCREEN  8 | interlace page:0 | .S80 |.R80 | BSAVE interlace
| .S81 | SCREEN  8 | interlace page:1 | .S81 |.R81 | BSAVE interlace
| .SA0 | SCREEN 10 | interlace page:0 | .SA0 |.RA0 | BSAVE interlace
| .SA1 | SCREEN 10 | interlace page:1 | .SA1 |.RA1 | BSAVE interlace
| .SC0 | SCREEN 12 | interlace page:0 | .SC0 |.RC0 | BSAVE interlace
| .SC1 | SCREEN 12 | interlace page:1 | .SC1 |.RC1 | BSAVE interlace
| .SR2 | SCREEN  2 | non-interlace    | .SC2 |.SR2 | GRAPH SAURUS
| .SR4 | SCREEN  3 | non-interlace    | .SC3 |.SR4 | GRAPH SAURUS
| .SR3 | SCREEN  4 | non-interlace    | .SC4 |.SR3 | GRAPH SAURUS
| .SR5 | SCREEN  5 | non-interlace    | .SC5 |.SR5 | GRAPH SAURUS
| .SR6 | SCREEN  6 | non-interlace    | .SC6 |.SR6 | GRAPH SAURUS
| .SR7 | SCREEN  7 | non-interlace    | .SC7 |.SR7 | GRAPH SAURUS
| .SR8 | SCREEN  8 | non-interlace    | .SC8 |.SR8 | GRAPH SAURUS
| .SRA | SCREEN 10 | non-interlace    | .S10 |.SRA | GRAPH SAURUS
| .SRC | SCREEN 12 | non-interlace    | .S12 |.SRC | GRAPH SAURUS
| .SRS | SCREEN 12 | non-interlace    | .S12 |.SRS | GRAPH SAURUS
| .R50 | SCREEN  5 | interlace page:0 | .S50 |.R50 | GRAPH SAURUS interlace
| .R51 | SCREEN  5 | interlace page:1 | .S51 |.R51 | GRAPH SAURUS interlace
| .R60 | SCREEN  6 | interlace page:0 | .S60 |.R60 | GRAPH SAURUS interlace
| .R61 | SCREEN  6 | interlace page:1 | .S61 |.R61 | GRAPH SAURUS interlace
| .R70 | SCREEN  7 | interlace page:0 | .S70 |.R70 | GRAPH SAURUS interlace
| .R71 | SCREEN  7 | interlace page:1 | .S71 |.R71 | GRAPH SAURUS interlace
| .R80 | SCREEN  8 | interlace page:0 | .S80 |.R80 | GRAPH SAURUS interlace
| .R81 | SCREEN  8 | interlace page:1 | .S81 |.R81 | GRAPH SAURUS interlace
| .RA0 | SCREEN 10 | interlace page:0 | .SA0 |.RA0 | GRAPH SAURUS interlace
| .RA1 | SCREEN 10 | interlace page:1 | .SA1 |.RA1 | GRAPH SAURUS interlace
| .RC0 | SCREEN 12 | interlace page:0 | .SC0 |.RC0 | GRAPH SAURUS interlace
| .RC1 | SCREEN 12 | interlace page:1 | .SC1 |.RC1 | GRAPH SAURUS interlace



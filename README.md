# MSX_MISC_TOOLS

## 他のRepository

|ツール|説明|
|---|---|
| [EXTRACT_MSX_CAS/  ](https://github.com/uniskie/EXTRACT_MSX_CAS/ ) |MSXテープイメージからファイルを取り出す(Python3)

## Windowsで動作するMSX用ツール

|ツール|説明|
|---|---|
| [GSRLE/            ](GSRLE             ) |グラフサウルス形式圧縮ツール (派生型ランレングス圧縮)<BR> ![](img/GSRLE.png) <BR>展開表示(MSX用)は [LOADSRD](LOADSRD)

## Windows向けMSX用お役立ちデータ
|ファイル|説明|
|---|---|
| [Custom Palette for BZ Editor](Custom%20Palette%20for%20BZ%20Editor)|バイナリエディタ Bz Editor 用 MSX Bitmap Palette<BR>![](img/BZ_MSX_PALETTE.png)|

## MSXで動作するツール

|ツール|説明|
|---|---|
| [FieldWork/          ](FieldWork          ) |高速な漢字テキストエディタ(SCREEN2とスクロール使用)<BR>![](img/fieldwork_001.png)|
| [LOADSRD/           ](LOADSRD            ) |BSAVE画像とグラフサウルス画像を読み込み表示 (グラフサウルス圧縮対応)<BR>![](img/MIKTEA%200001.png)<BR>圧縮は [GSRLE](GSRLE)|
| [OPLDRV_BGM_EXTRACT/](OPLDRV_BGM_EXTRACT ) |FMPACとRTYPEのOPLDRV用BGMデータをカートリッジから取り出すプログラム|
| [SCC_WAVE_MODULATE/ ](SCC_WAVE_MODULATE  ) |SCC波形データのボリューム加工（n/256倍率をかけて出力）|
| [FILER.BAS          ](FILER.BAS          ) |ファイル一覧＆ファイル操作プログラム。ファイル名のひらがな→カタカナ変換などもできます。<BR>![](img/MISCTOOLS%200011.png)|
| [SP-EDIT/           ](SP-EDIT            ) |SCREEN5簡易スプライトエディタ(単色)<BR>![](img/MISCTOOLS%200010.png)|
| [CPU_MODE_FOR_BASIC/](CPU_MODE_FOR_BASIC ) |BASICからCPU MODE(Z80/R800)を切り替えるサンプル|
| [HIMEM.BAS          ](HIMEM.BAS          ) |フリーエリア先頭とスタックポインタのアドレスを表示<BR>![](img/MISCTOOLS%200001.png)|
| [GETPALAD.BAS       ](GETPALAD.BAS       ) |現在の画面モードでのVRAMパレットテーブルを返す(サンプルコード)<BR>![](img/MISCTOOLS%200004.png)|
| [KEYMTX.BAS         ](KEYMTX.BAS         ) |簡易キーマトリクス表示<BR>![](img/MISCTOOLS%200007.png)|
| [KEYMTXB.BAS        ](KEYMTXB.BAS        ) |少しリッチなキーマトリクス表示(turboR推奨)<BR>![](img/MISCTOOLS%200008.png)|
| [COLCOMB.BAS        ](COLCOMB.BAS        ) |簡易スプライトモード2重ね合わせカラーリスト<BR>![](img/MISCTOOLS%200005.png)|
| [COLCOMBG.BAS       ](COLCOMBG.BAS       ) |少しリッチなスプライトモード2重ね合わせカラーリスト<BR>![](img/MISCTOOLS%200006.png)|


### 不要かもしれないツール

|ツール|説明|
|---|---|
| [SPCDBL.BAS         ](SPCDBL.BAS         ) |99x8Edit用ツール<BR>(**現在はエクスポート機能が充実しているので不要です**)<BR>スプライトモード2の16x16スプライト用カラーデータをCHR COLOR形式(2倍サイズ)にして出力。<BR><BR>VDPファイルのスプライトカラー情報がCHR COLOR形式のため、エクスポート出力したデータをそのままVDPファイルに書き戻しできないので、このツールで出力したデータをVDPファイルの$1C21～の位置に張り付けるとインポートできます。<BR><BR>***Note***:<br> 出力される```SPCDBL.BIN```は最後に余計な```EOF($1A)```がついてしまいますので、それを取り除いてから貼り付けてください。|


## ご利用について

ソースコード含め、改変・再配布はご自由にどうぞ。
ただし、サポート・保証などはございません。

このプログラムを使用して起きた問題については補償いたしかねますので、
ファイル・ディスクは常にバックアップを取って使用してください。

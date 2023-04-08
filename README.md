# MSX_MISC_TOOLS

## 他のRepository

|ツール|説明|
|---|---|
| [EXTRACT_MSX_CAS/  ](https://github.com/uniskie/EXTRACT_MSX_CAS/ ) |MSXテープイメージからファイルを取り出す(Python3)

## Windowsで動作するツール

|ツール|説明|
|---|---|
| [Custom Palette for BZ Editor](Custom%20Palette%20for%20BZ%20Editor)|バイナリエディタ Bz Editor 用 MSX Bitmap Palette|
| [GSRLE/            ](GSRLE             ) |グラフサウルス圧縮ツール (派生型ランレングス圧縮) 

## MSXで動作するツール

|ツール|説明|
|---|---|
| [CPU_MODE_FOR_BASIC/](CPU_MODE_FOR_BASIC ) |BASICからCPU MODE(Z80/R800)を切り替えるサンプル|
| [LOADSRD/           ](LOADSRD            ) |BSAVE画像とグラフサウルス画像を読み込み表示 (グラフサウルス圧縮対応)<BR>![](img/MIKTEA%200002.png)|
| [HIMEM.BAS          ](HIMEM.BAS          ) |フリーエリア先頭とスタックポインタのアドレスを表示<BR>![](img/MISCTOOLS%200001.png)|
| [GETPALAD.BAS       ](GETPALAD.BAS       ) |現在の画面モードでのVRAMパレットテーブルを返す(サンプルコード)<BR>![](img/MISCTOOLS%200004.png)|
| [SP-EDIT/           ](SP-EDIT            ) |SCREEN5簡易スプライトエディタ(単色)<BR>![](img/MISCTOOLS%200010.png)|
| [KEYMTX.BAS         ](KEYMTX.BAS         ) |簡易キーマトリクス表示<BR>![](img/MISCTOOLS%200007.png)|
| [KEYMTXB.BAS        ](KEYMTXB.BAS        ) |少しリッチなキーマトリクス表示(turboR推奨)<BR>![](img/MISCTOOLS%200008.png)|
| [COLCOMB.BAS        ](COLCOMB.BAS        ) |簡易スプライトモード2重ね合わせカラーリスト<BR>![](img/MISCTOOLS%200005.png)|
| [COLCOMBG.BAS       ](COLCOMBG.BAS       ) |少しリッチなスプライトモード2重ね合わせカラーリスト<BR>![](img/MISCTOOLS%200006.png)|
| [OPLDRV_BGM_EXTRACT/](OPLDRV_BGM_EXTRACT ) |FMPACとRTYPEのOPLDRV用BGMデータをカートリッジから取り出すプログラム|
| [SCC_WAVE_MODULATE/ ](SCC_WAVE_MODULATE  ) |SCC波形データのボリューム加工（n/256倍率をかけて出力）|
| [FILER.BAS          ](FILER.BAS          ) |ファイル一覧＆ファイル操作プログラム。ファイル名のひらがな→カタカナ変換などもできます。<BR>![](img/MISCTOOLS%200011.png)|


### 不要かもしれないツール

|ツール|説明|
|---|---|
| [SPCDBL.BAS         ](SPCDBL.BAS         ) |99x8Edit用ツール<BR>(**現在はエクスポート機能が充実しているので不要です**)<BR>スプライトモード2の16x16スプライト用カラーデータをCHR COLOR形式(2倍サイズ)にして出力。<BR><BR>VDPファイルのスプライトカラー情報がCHR COLOR形式のため、エクスポート出力したデータをそのままVDPファイルに書き戻しできないので、このツールで出力したデータをVDPファイルの$1C21～の位置に張り付けるとインポートできます。<BR><BR>***Note***:<br> 出力される```SPCDBL.BIN```は最後に余計な```EOF($1A)```がついてしまいますので、それを取り除いてから貼り付けてください。|

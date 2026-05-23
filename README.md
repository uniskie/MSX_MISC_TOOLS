# MSX_MISC_TOOLS



## ブラウザで動作するMSX用ツール

https://uniskie.github.io/MSX_MISC_TOOLS/

HTML5+javascript ES6 で動作

|ツール|説明|
|---|---|
| [GSRLE/html/](GSRLE/html/) | 【HTML5版 MSX画像ビューア】<br>BSAVE画像やグラフサウルス形式圧縮画像 (派生型ランレングス圧縮)の読み込み・表示・変換・保存が出来るツール<br> [ブラウザで実行 → https://uniskie.github.io/MSX_MISC_TOOLS/GSRLE/gsrle.html](https://uniskie.github.io/MSX_MISC_TOOLS/GSRLE/gsrle.html) <br> ![](GSRLE/html/img/gsrle_html_default.png) <br>MSX上での展開表示は [LOADSRD](LOADSRD)|

## Windowsで動作するMSX用ツール

|ツール|説明|
|---|---|
| [MSXDumpEditor](MSXDumpEditor)|Python習作バイナリエディタ。スプライトプレビュー窓、MSXフォントでの表示、逆アセンブラなどを搭載。<br>![](MSXDumpEditor/img/screenshot_win.png)![](MSXDumpEditor/img/disasm.png)|
| [Binary Editor Bz for MSX](BinaryEditorBz_for_MSX)|[バイナリエディタBz (MSX/レトロコンソール向けビットマップビュー拡張版)](BinaryEditorBz_for_MSX/ReadMe.md)<br> ![](img/BzEditor_for_msx_2.png) ![](img/BzEditor_for_msx_3.png) |
| [GSRLE/            ](GSRLE             ) |グラフサウルス形式圧縮ツール (派生型ランレングス圧縮)<br> ![](img/GSRLE.png) <br>展開表示(MSX用)は [LOADSRD](LOADSRD)|
| [OPLDRV_BGM_EXTRACT/](OPLDRV_BGM_EXTRACT ) |1. FMPACとRTYPEのOPLDRV用BGMデータをカートリッジから取り出すプログラム<br>2. opldrvデータを解析するプログラム <br> ![](OPLDRV_BGM_EXTRACT/img/OPLDRV_tool.png)|

## Windows向けMSX用お役立ちデータ
|ファイル|説明|
|---|---|
| [OpenMSX custom data](openMSX_custom) | ![](openMSX_custom/osd_setting_2.png)openMSX用のカスタムスクリプトサンプルと小さめのOSDアイコン |

## MSXで動作するプログラム

githubに直接置いてあるBASICプログラムファイルは、
参照しやすいようにアスキー形式のファイルが殆どになっているため、
MSXでロードする処理がとても遅くなります。

ロードの早い中間言語形式でのBASICファイルはDISKイメージファイルに入っています。

### ツール類

DISKイメージ：[misctool.dsk](misctool.dsk)

#### 内容：
```
BINADR.BAS
BLAUNCH.BAS
COLCOMB.BAS
COLCOMBG.BAS
CPUMODE.BAS
FAMIMA.BAS
FILER.BAS
GETPALAD.BAS
HIMEM.BAS
KEYMTX.BAS
KEYMTXB.BAS
VOICE.BAS
UNKOSLOT.BAS
```

|ツール|説明|
|---|---|
| [FieldWork/          ](FieldWork          ) |高速な漢字テキストエディタ(SCREEN2とスクロール使用)<br>![](FieldWork/img/FieldWork.png)|
| [LOADSRD/           ](LOADSRD            ) |BSAVE画像とグラフサウルス画像を読み込み表示<br>(グラフサウルス圧縮対応)<br>圧縮は [GSRLE](GSRLE)<br>![](img/MIKTEA0001.png)|
| [MML加工用 テキストエディタマクロ集<br>(他レポジトリ)](https://github.com/uniskie/msx_music_data/blob/master/macro/) | <ol><li>SCC波形加工 for MGSDRV<li>MML整形 for MGSDRV<li>MML転調 for MGSDRV<li>MMLオクターブ検査 for MGSDRV</ol>![](https://github.com/uniskie/msx_music_data/raw/master/macro/image/SCC_WAVE_VOLUME_2.png) |
| [BLAUNCH.BAS        ](BLAUNCH.BAS        ) |BASICランチャー<br>ターボR DOS2ではCPUモード切替可能 (DOS1では安全のためZ80のみ)<br>スペースキー/リターンキー/Aボタンで決定。<br>十字キー/'N'キー/Bボタンでキャンセル。<br>'M'キー/BボタンでCPU変更。<br>[CPUMODE.ASM](CPU_MODE_FOR_BASIC/CPUMODE.ASM)...械語部分(CPUモード操作)ソース<br>  [CHKDOS.ASM](CPU_MODE_FOR_BASIC/CHKDOS.ASM)...機械語部分(DOSバージョン検査)ソースコード<br>[CLRBLK.ASM](CLRBLK.ASM)...機械語部分(ブリンクテーブルクリア)ソースコード<br>![](img/BLAUNCH.png)|
| [FILER.BAS          ](FILER.BAS          ) |ファイル一覧＆ファイル操作プログラム。<br>ファイル名のひらがな→カタカナ変換可能。<br>(MSX以外での文字化け対策のため)<br>![](img/FILER.png)|
| [SP-EDIT/           ](SP-EDIT            ) |簡易スプライトエディタ(単色)<br>SCREEN5とあるのはスプライトパターンテーブルがSCREEN5と同じ```&H7800```を使うからですが、使用している画面モード自体はSCREEN1です。よってスクリーンモードを0～4に変更してもスプライトパターンデータはVRAMに残ります。<br>```SPRITE?.SC5```をSCREEN1で使うときは```BLOAD"SPRITE0.SC5",S,-&h4000```のようにします。<br>![](img/SP-EDIT.png)|
| [CPU_MODE_FOR_BASIC/](CPU_MODE_FOR_BASIC ) |[CPUMODE.BAS](CPU_MODE_FOR_BASIC/CPUMODE.BAS) ... 比較的安全なCPU切替プログラム<br>その他：BASICからCPU MODE(Z80/R800)を切り替えるサンプル<br>![](img/CPUMODE.png)|
| [HIMEM.BAS          ](HIMEM.BAS          ) |フリーエリア先頭とスタックポインタのアドレスを表示<br>![](img/HIMEM.png)|
| [BINADR.BAS         ](BINADR.BAS         ) |BINファイルの先頭アドレスと終端アドレスを表示<br>(**2026/01/10 EOF対策版に変更**)<br>![](img/BINADR.png)|
| [GETPALAD.BAS       ](GETPALAD.BAS       ) |現在の画面モードでのVRAMパレットテーブルを返す(サンプルコード)<br>![](img/GETPALAD3.png)|
| [KEYMTX.BAS         ](KEYMTX.BAS         ) |簡易キーマトリクス表示<br>![](img/KEYMTX.png)|
| [KEYMTXB.BAS        ](KEYMTXB.BAS        ) |少しリッチなキーマトリクス表示(turboR推奨)<br>![](img/KEYMTXB.png)|
| [COLCOMB.BAS        ](COLCOMB.BAS        ) |簡易スプライトモード2重ね合わせカラーリスト<br>![](img/COLCOMB.png)|
| [COLCOMBG.BAS       ](COLCOMBG.BAS       ) |少しリッチなスプライトモード2重ね合わせカラーリスト<br>![](img/COLCOMBG.png)|
| [MSX_MUSIC_ROM_VOICE_TEST/VOICE.BAS](MSX_MUSIC_ROM_VOICE_TEST/voice.bas) |FMPACと内蔵ROM(A1GT)での音色ライブラリの違いを聞き比べる<br>![](img/MSX_MUSIC_ROM_VOICE_TEST.png)|

### 2026年 年賀状

2026年賀DISKイメージ: [2026/nenga26.dsk](2026/nenga26.dsk)

[source](2026/nenga26/)

![](2026/nenga26.png)

## テキストエディタマクロ　（サクラエディタ/EmEditor）

|ツール|説明|
|---|---|
| [macro/MSXBASIC.js](macro/MSXBASIC.js) | アスキーリスト形式に変換するjavascriptファイル<br>（`元ファイル名.ASC` でアスキーリスト変換後のファイルを作成。<br>**同じファイル名があっても強制上書きするので注意してください**。）<br><br>サクラエディタやEmEditorのマクロとしても、<br>コマンドラインから `CScript MSXBASIC.js ファイル名`としても使用可能です。![](img/MSXBASIC_JS.png)<br><br>エディタマクロとして使用する場合も、**文字化け**回避のために変換後のファイルを保存します。<br>エディタマクロとしての使用方法はエディタのヘルプを参照ください。（基本的に、macroフォルダに置いてメニューから選択して使用します。） |

## 他のRepository

|ツール|説明|
|---|---|
| [EXTRACT_MSX_CAS/  ](https://github.com/uniskie/EXTRACT_MSX_CAS/ ) |MSXテープイメージからファイルを取り出す(Python3)

## ご利用について

利用については独自ライセンスとなります。

文字フォント以外の画像についての再利用はご遠慮ください。

ソースコードやプログラムの、改変・再配布はご自由にどうぞ。  
引用元の表示も不要です。  
ただし、サポート・保証などはございません。  

これらのプログラムを使用して起きた問題については補償いたしかねますので、  
ファイル・ディスクは常にバックアップを取って使用してください。

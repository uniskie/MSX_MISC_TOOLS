# MSX_MISC_TOOLS

雑多にMSX関連のツールやデータを置いています。

---

# OpenMSX向け役立ちデータ＆ツール

## OpenMSX custom data

[OpenMSX custom data](openMSX_custom) 

![](openMSX_custom/osd_setting_2.png)

1. [openMSX用のカスタムスクリプトサンプル](openMSX_custom/share/scripts/)
2. [小さめのOSDアイコン](openMSX_custom/share/skins/uni-set/)
3. [TV風フィルタ](openMSX_custom/share/shader/)
4. [softwaredb.xmlへのROM情報追加ツール](openMSX_custom/msx_softwaredb_xml_merge/)
4. [SofaRun用・ディスクイメージ結合バッチファイル](openMSX_custom/FILE_COMBINE.BAT)

---

# ブラウザで動作するMSX用ツール

[ブラウザ用トップページ](https://uniskie.github.io/MSX_MISC_TOOLS/)

HTML5+javascript ES6 で動作

## HTML5 MSX GRAPHICS Viewer

[GSRLE/html/](GSRLE/html/) 

[説明書](GSRLE/html/index.html)

ブラウザ上でMSXの各種画像ファイルを表示するツール

 ![](GSRLE/html/img/gsrle_html_default.png) 

- VDPのVRAM表示シミュレートによる表示
  - 画面モードやベースアドレスの変更
  - 192ライン、256ライン切り替え
  - アスペクト比調整
- キャラクタビュー
- スプライトビュー
- 裏ページビュー
- 各種MSX向け画像ファイルの読み込み
  - 各スクリーンモードのBINファイル
  - openMSXのVRAM出力ファイル
  - COPY文で保存した画像ファイル
  - グラフサウルス形式（圧縮・非圧縮）ファイル

画像ファイルの拡張子に従って表示画面モード等を自動変更

 [ブラウザで実行 → https://uniskie.github.io/MSX_MISC_TOOLS/GSRLE/gsrle.html](https://uniskie.github.io/MSX_MISC_TOOLS/GSRLE/gsrle.html)
 
 
 MSX上での展開表示は [LOADSRD](LOADSRD)|

---

# Windowsで動作するMSX用ツール

## MSXDumpEditor

[MSXDumpEditor](MSXDumpEditor)

Python習作で作成したバイナリエディタ。

- スプライトプレビュー窓
- MSXフォントでの表示
- 逆アセンブラ

など自分が良く使う機能を搭載。

気が向いたら機能追加。

![](MSXDumpEditor/img/screenshot_win.png)![](MSXDumpEditor/img/disasm.png)

## Binary Editor Bz for MSX 

「Binary Editor Bz」の MSXやレトロコンソール向けビットマップビュー拡張版。

[Binary Editor Bz for MSX](BinaryEditorBz_for_MSX)

[説明書](BinaryEditorBz_for_MSX/ReadMe.md)

![](img/BzEditor_for_msx_2.png) ![](img/BzEditor_for_msx_3.png)

## グラフサウルス形式圧縮ツール GSRLE

[GSRLE/            ](GSRLE             ) 

グラフサウルス形式圧縮 (派生型ランレングス圧縮)を行うツール。

![](img/GSRLE.png)

展開表示(MSX用)は [LOADSRD](LOADSRD)

## OPLDRV BGM Extractor

[OPLDRV_BGM_EXTRACT/](OPLDRV_BGM_EXTRACT/)

[説明書](OPLDRV_BGM_EXTRACT/ReadMe.md)

1. FMPACとRTYPEのOPLDRV用BGMデータをカートリッジから取り出すプログラム
   - R-TYPE用：[RDRTYPE.BAS](OPLDRV_BGM_EXTRACT/EXTEACT_FROM_MSX_CARTRIDGE/RDRTYPE.BAS)
   - FM PAC用：[RDFMPAC.BAS](OPLDRV_BGM_EXTRACT/EXTEACT_FROM_MSX_CARTRIDGE/RDFMPAC.BAS)
2. OPLDRVデータを解析するツール(Windows用)  
   - [OPLDRV_tool.exe](OPLDRV_BGM_EXTRACT/OPLDRV_tool.exe)
   - [ソースコード](OPLDRV_BGM_EXTRACT/OPLDRV_tool/)

![](OPLDRV_BGM_EXTRACT/img/OPLDRV_tool.png)

---

# MSXで動作するプログラム

githubに直接置いてあるBASICプログラムファイルは、
参照しやすいようにアスキー形式のファイルが殆どになっているため、
MSXでロードする処理がとても遅くなります。

ロードの早い中間言語形式でのBASICファイルはDISKイメージファイルに入っています。

## ツール類

DISKイメージ：[misctool.dsk](misctool.dsk)

### 内容：
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

|ツール名|説明|
|---|---|
| MSX2用 高速漢字テキストエディタ          <br> [FieldWork                ](FieldWork                ) |SCREEN2と縦スクロールとHSYNC割り込みを使用した、軽快な漢字テキストエディタ。<br>漢字BASICの単漢字変換インターフェースは外部公開されていない為、漢字入力をする場合はMSX-JEが必要です。漢字入力をしないなら不要です。<br>（ソニーMSX2+やA1WX/WSX/ST/GTはMSX-JE内蔵）<br>漢字変換時に長い割り込みが入ると画面が乱れるのはご愛敬。<br>![](FieldWork/img/FieldWork.png)|
| グラフサウルス形式対応画像ローダー       <br> [LOADSRD                  ](LOADSRD                  ) |BSAVE画像とグラフサウルス画像を読み込み表示するツール。<br>(グラフサウルス圧縮対応)<br>圧縮は [GSRLE](GSRLE)<br>![](img/MIKTEA0001.png)|
| MML加工向け テキストエディタマクロ集     <br> [(他レポジトリ)           ](https://github.com/uniskie/msx_music_data/blob/master/macro/) | <ol><li>SCC波形加工 for MGSDRV<li>MML整形 for MGSDRV<li>MML転調 for MGSDRV<li>MMLオクターブ検査 for MGSDRV</ol>![](https://github.com/uniskie/msx_music_data/raw/master/macro/image/SCC_WAVE_VOLUME_2.png) |
| BASIC用ファイルランチャー                <br> [BLAUNCH.BAS              ](BLAUNCH.BAS              ) |ターボR DOS2ではCPUモード切替可能。 (DOS1では安全のためR800へ切り替えません)<br><dl><li>スペースキー/リターンキー/Aボタンで決定。<li>十字キー/'N'キー/Bボタンでキャンセル。<li>'M'キー/BボタンでCPU変更。</ol><br>[CPUMODE.ASM](CPU_MODE_FOR_BASIC/CPUMODE.ASM)...械語部分(CPUモード操作)ソース<br>  [CHKDOS.ASM](CPU_MODE_FOR_BASIC/CHKDOS.ASM)...機械語部分(DOSバージョン検査)ソースコード<br>[CLRBLK.ASM](CLRBLK.ASM)...機械語部分(ブリンクテーブルクリア)ソースコード<br>![](img/BLAUNCH.png)|
| ファイル名カタカナ変換付きファイラー     <br> [FILER.BAS                ](FILER.BAS                ) |ファイル一覧＆ファイル操作プログラム。<br>ファイル名のひらがな→カタカナ変換可能。<br>(MSX以外での文字化け対策のため)<br>![](img/FILER.png)|
| 単色スプライトエディタ(単色)             <br> [SP-EDIT/                 ](SP-EDIT                  ) |SCREEN5とあるのはスプライトパターンテーブルをSCREEN5と同じ`&H7800`に置くからですが、表示画面モード自体はSCREEN1です。<br>このため、スクリーンモードを0～4に変更してもスプライトパターンデータはVRAMに残ります。<br>保存ファイル名は`SPRITE?.SC5`です。(?は0～9)<br>SCREEN1で使うときは`BLOAD"SPRITE0.SC5",S,-&h4000`のようにオフセット指定して読み込みます。<br>![](img/SP-EDIT.png)|
| BASIC用R800/Z80モード切替                <br> [CPU_MODE_FOR_BASIC/      ](CPU_MODE_FOR_BASIC       ) |[CPUMODE.BAS](CPU_MODE_FOR_BASIC/CPUMODE.BAS) ... 比較的安全なCPU切替プログラム。<br>その他：BASICからCPU MODE(Z80/R800)を切り替えるサンプル。<br>![](img/CPUMODE.png)|
| フリーエリアとスタックポインタ表示       <br> [HIMEM.BAS                ](HIMEM.BAS                ) |BASICでフリーエリアとスタックポインタを調べるサンプルプログラム。<br>![](img/HIMEM.png)|
| BINファイルヘッダ表示                    <br> [BINADR.BAS               ](BINADR.BAS               ) |BINファイルの先頭アドレスと終端アドレスを表示するBASICプログラム。<br>テキストモードで読み込むとEOFを誤検知するので、ランダムレコードでバイナリとして読み込みます。<br>![](img/BINADR.png)|
| VRAMパレット表示                         <br> [GETPALAD.BAS             ](GETPALAD.BAS             ) |現在の画面モードでのVRAMパレットテーブルを返すサンプルコード<br>![](img/GETPALAD3.png)|
| 簡易キーマトリクス表示                   <br> [KEYMTX.BAS               ](KEYMTX.BAS               ) |キーマトリクスの状態をリアルタイム表示します。<br>![](img/KEYMTX.png)|
| 少しリッチなキーマトリクス表示           <br> [KEYMTXB.BAS              ](KEYMTXB.BAS              ) |少しリッチなキーマトリクス表示をしますが、重いのでturboR推奨です。<br>SCREEN0の80行モードで部リンクテーブルを使用するサンプルも兼ねています。<br>![](img/KEYMTXB.png)|
| スプライトMODE2重ね合わせカラー一覧その1 <br> [COLCOMB.BAS              ](COLCOMB.BAS              ) |簡易的なスプライトモード2重ね合わせカラーリスト。<br>![](img/COLCOMB.png)|
| スプライトMODE2重ね合わせカラー一覧その2 <br> [COLCOMBG.BAS             ](COLCOMBG.BAS             ) |少しリッチなスプライトモード2重ね合わせカラーリスト。<br>![](img/COLCOMBG.png)|
| FMPACと内蔵MSX-MUSICの音色ライブラリ比較 <br> [MSX_MUSIC_ROM_VOICE_TEST/](MSX_MUSIC_ROM_VOICE_TEST/) |FMPACと内蔵ROM(A1GT)での音色ライブラリの違いを聞き比べるテスト。<br>![](img/MSX_MUSIC_ROM_VOICE_TEST.png)|

## 2026年 年賀状

2026年賀DISKイメージ: [2026/nenga26.dsk](2026/nenga26.dsk)

[source](2026/nenga26/)

![](2026/nenga26.png)

---

# テキストエディタマクロ （サクラエディタ/EmEditor）

## MSX BASIC 中間言語変換

[MSXBASIC_TokenConverter/MSXBASIC.js](MSXBASIC_TokenConverter/MSXBASIC.js)

アスキーリスト形式に変換するjavascriptファイル

（`元ファイル名.ASC` でアスキーリスト変換後のファイルを作成。  
**同じファイル名があっても強制上書きするので注意してください**。）

サクラエディタやEmEditorのマクロとしても、  
コマンドラインから `CScript MSXBASIC.js ファイル名`としても使用可能です。

![](img/MSXBASIC_JS.png)

エディタマクロとして使用する場合も、**文字化け**回避のために変換後のファイルを保存します。  
エディタマクロとしての使用方法はエディタのヘルプを参照ください。  
（基本的に、macroフォルダに置いてメニューから選択して使用します。）

---

# 他のRepository

## Extract File From CAS Image

[EXTRACT_MSX_CAS/  ](https://github.com/uniskie/EXTRACT_MSX_CAS/ )

MSXのカセットテープイメージファイルから中のファイルを取り出すツール (Python3)

---

# ご利用について

利用については独自ライセンスとなります。

- 文字フォント以外の画像についての再利用はご遠慮ください。
- ソースコードやプログラムの、改変・再配布はご自由にどうぞ。  
- 引用元の表示も不要です。  
- ただし、サポート・保証などはございません。  

これらのプログラムを使用して起きた問題については補償いたしかねますので、  
ファイル・ディスクは常にバックアップを取って使用してください。

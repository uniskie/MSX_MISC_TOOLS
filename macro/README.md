# MSX_MISC_TOOLS javascript編

## BASICリスト変換

[MSXBASIC.js](MSXBASIC.js) ... MSX BASIC中間言語形式のファイルをアスキーファイル形式に変換します。
 
- サクラエディタやEmEditorのマクロとしして使用可能
- コマンドラインから `CScript MSXBASIC.js ファイル名`としても使用可能

### 保存について

`元ファイル名.ASC` でアスキーリストに変換したファイルを保存します。 

> [!CAUTION]  
> **同じファイル名があっても強制上書きするので注意してください**

### テキストエディタマクロとして使用する場合

現在開いているファイルを変換します。

- エディタマクロとして使用する場合も、**文字化け**回避のために変換後のファイルをスクリプトから直接保存します。  
  （SJIS形式ではエディタから保存するとひらがななどが文字化けします）

- エディタマクロとしての使用方法はエディタのヘルプを参照ください。  
  （基本的に、macroフォルダに置いてメニューから選択して使用します。） 

### コマンドラインから使用する場合

例えば`MSXBASIC.js`が`C:\MSX_MISC_TOOL`にある場合

\> `SET ConvMSXBASIC=C:\MSX_MISC_TOOL\MSXBASIC.js`

\> `CSCRIPT %ConvMSXBASIC% AUTOEXEC.BAS`

などとします。

一括で変換したい場合は、

\> `FOR %i IN (*.BAS) DO (CSCRIPT %ConvMSXBASIC% %i)`

のような感じで使います。

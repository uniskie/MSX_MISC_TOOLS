# OpenMSX custom data

| folder | items  |
|---|---|
|[share/scripts](share/scripts)| カスタムコマンド追加サンプルです。 |
|[share/skins](share/skins)| skins/uni-set ... 少し小さめのOnScreenDisplayアイコンセットです。 |
|[layouts](layouts)| skins/uni-setのアイコンを使用したレイアウト保存データです。<BR>openMSXメニューの 「Settings」 → 「GUI」→「Save Layout」で保存、「Restore Layout」で呼び出し。 |


## 使い方

`ユーザーフォルダ/openMSX/share/`
にsciptフォルダやskinフォルダをコピーして使用してください。

> - windows: `%USERPROFILE%\My Documents\openMSX\share`  
> - unix: `~/.openMSX/share`  
>
> (openMSX環境変数 [var(OPENMSX_USER_DATA)] で取得可能) 

もし同名のファイルがある場合は上書しないで名前を変えて使用してください。


## script 解説

share/scriptの中にあるファイルのうち、頭に_（アンダースコア）が付いていない*.tclファイルが起動時に読み込み・実行されます。

OpenMSXコマンドコンソールから使用したいものは、
頭に_のついたtclファイルに書き、
`lazy_add.tcl`の中で登録するという流れになります。

- lazy_add.tcl  
  起動時に実行されます。  
  `_bmp_util.tcl`の中にある`save2bmp`というコマンドを登録します。  

- _bmp_util.tcl  
  `save2bmp`というコマンドのヘルプテキストや処理内容を定義しています。

- _disasm3.tcl  
  `disasm3`や`get_symbol`というコマンドのヘルプテキストや処理内容を定義しています。  
  `disasm3`は[disasm2](https://www.msx.org/forum/msx-talk/openmsx/openmsx-disasm)をベースに拡張した自分用逆アセンブル出力コマンドです。  

  1. 開始アドレス、終了アドレスで範囲を指定
  2. Symbol Managerを参照してラベルに対応
  3. ダンプをコメントとして追加
  4. 開始・終了アドレスの指定にラベル対応（※大文字小文字の区別有り）

  （`disasm3_l`はおまけ。ラベル対応1行逆アセンブル）
  
  `save_to_file {sample.asm} [disasm3 0x0000 0x3fff]`⏎ のようにすると逆アセンブル結果出力をファイルに保存できます。

## skin 解説

### skins/uni-set

少し小さめのOnScreenDisplayアイコンセットです

openMSXメニューの 「Settings」 → 「GUI」 → 「Configure OSD icons...」でアイコンを指定してください。

![](osd_setting_1.png)
![](osd_setting_2.png)

## GUIレイアウト

- layouts/simple.ini
- layouts/debug.ini

各iniファイルを`ユーザーフォルダ/openMSX/layouts`に置いてください。

> - windows: `%USERPROFILE%\My Documents\openMSX\layouts`  
> - unix: `~/.openMSX/layouts`  

skins/uni-setの小さめなアイコンを使用したレイアウト定義です。

openMSXメニューの 「Settings」 → 「GUI」→  
「Save Layout」で保存、「Restore Layout」で呼び出し。

![](osd_setting_3.png)


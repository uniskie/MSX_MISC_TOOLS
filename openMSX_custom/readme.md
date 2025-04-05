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


## 使い方

OPENMSX_USER_DATAフォルダにsciptフォルダを置いてください。

### OPENMSX_USER_DATAフォルダ
- windows: `%USERPROFILE%\My Documents\openMSX\share`  
- unix: `~/.openMSX/share`  

## 解説
OpenMSXユーザーフォルダの
share/scriptの中にあるファイルのうち、頭に_（アンダースコア）が付いていない*.tclファイルが起動時に読み込み・実行されます。

OpenMSXコマンドコンソールから使用したいものは、
頭に_のついたtclファイルに書き、
`lazy_add.tcl`の中で登録するという流れになります。

- lazy_add.tcl  
  起動時に実行されます。  
  `_bmp_util.tcl`の中にある`save2bmp`というコマンドを登録します。  

- _bmp_util.tcl  
  `save2bmp`というコマンドのヘルプテキストや処理内容を定義しています。

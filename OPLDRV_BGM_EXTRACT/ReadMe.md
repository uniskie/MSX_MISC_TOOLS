
## EXTEACT_FROM_MSX_CARTRIDGE

ROMからOPLDRV用BGMデータをファイルに書き出すプログラム。

MSX実機でカートリッジを後挿しして実行すると、
OPLDRV用のBGMデータをファイルに保存します。

MSX実機用のツールです。

ファイルは  
[EXTEACT_FROM_MSX_CARTRIDGE](EXTEACT_FROM_MSX_CARTRIDGE)  
に置いてあります。

- R-TYPE用：```RDRTYPE.BAS```
- FM PAC用：```RDFMPAC.BAS```

一度VRAMに書き出してからBSAVEします。

### 手順

1. BASICが起動
2. PAUSEキーを押すなどしてからカートリッジを挿入
3. ```RDRTYPE.BAS``` または ```RDFMPAC.BAS```を実行
4, スロット番号を聞かれるので、カートリッジを挿しているスロット番号を入力してRETURNキー

> スロット番号の例
> - 例）スロット1 ... ```1``` を入力
> - 例）スロット1-2 ... ```89``` を入力 <br> (0x80 + 拡張スロット*4 + 基本スロット)

### RDFMPAC.BAS で出力されるファイル

FMPAC0.BIN ～ FMPAC4.BIN の 5個が出力されます。

### RDRTYPE.BAS で出力されるファイル

RTYPE0.BIN ～ RTYPEF.BIN の 16個が出力されます。

## OPLDRV_tool.exe

（ [OPLDRV_tool](OPLDRV_tool)にソースコードがあります。）

```
OPLDRV TOOL

OPLDRV_tool [/l:filename][/b:address)][/r:address)] [INPUT FILENAME] [/o:OUTPUT FILENAME]

/l:filename  Log text output to file.
/a:address   set base address for RAW file.
             (Required for data using user voice.)
/r:address   relocate to address.
             (Required for data using user voice.)
/b           add BSAVE header to output.
/-b          RAW output. (remove BSAVE header)


*1 [address] is hexadecimal
             (e.g. 0000, a000, C000)
```

OPLDRVデータのユーティリティーです。

基本的にはデータの検査をするための実験プログラムです。

1. BGMデータの内容を解析表示
2. BSAVE形式からRAWや、RAWからBSAVE形式への変換
3. ユーザー音色を使用しているデータの配置ドレスの変更


| オプション           | 機能                                             |
|----------------------|--------------------------------------------------|
| ```/l:ファイル名```  | 解析情報をテキストファイルに出力
| ```-/o:ファイル名``` | ファイルを出力
| ```/b```             | BSAVE形式で出力（省略時は入力ファイルと同じ形式）
| ```/-b```            | RAW形式で出力（省略時は入力ファイルと同じ形式）
| ```/a:アドレス```    | 入力ファイルがRAW形式の場合、開始アドレスを指定（16進数4桁）
| ```/r:アドレス```    | 出力ファイルの配置アドレスを変更（再配置）（16進数4桁）


### ユーザー音色を使用したデータを使用する場合

OPLDRVデータは、ユーザー音色の指定に絶対アドレスを使用しています。  
ユーザー音色を使用しているデータの場合は、データの開始アドレスが必要になります。  

ユーザー音色を使用していなければアドレスは気にする必要はありません。  
> RTYPE、FMPACともにユーザー音色は使用していません

BSAVEファイルであれば開始アドレスは自動で取得できますが、
RAW形式のファイルを入力ファイルとして使用する場合、
開始アドレスが不明なので```/a:nnnn ```オプションをつけてください。

### 検討中

今のところ予定していない機能

- ユーザー音色を別ファイル出力
- ユーザー音色アドレスを別指定して出力
- MMLの出力

本来作ろうとしていた機能

- MuSICAバイナリファイルからOPLDRVファイルへの変換

MuSCIA2KPLDRVは作ろうと思っています。


## oplファイル

MSXで  
EXTEACT_FROM_MSX_CARTRIDGE/RDRTYPE.BAS  
EXTEACT_FROM_MSX_CARTRIDGE/RDFMPAC.BAS  
を実行してできる*.BINファイルはBSAVEファイルです。

oplファイルはBSAVEヘッダのないRAWデータですので、
oplファイルが欲しい場合は、
BINファイルからoplファイルを生成する必要があります。

手順は2つあります

1. 手作業の場合<br>*.binの先頭の7バイトをバイナリエディタ等で削除して*.oplとして保存します。
2. OPLDRV_tool.exe<br> (Winddowsで）吐き出された*.binを同じフォルダにおいてBIN2OPL.BATを実行します。


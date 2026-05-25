# MSX SoftwareDB merge ツール

`softwaredb.xml`形式のデータベースを合成するツールです。

元となるXML形式のROM DatabaseはBlueMSXのインストールディレクトリーまたは、下記から入手可能です。

https://romdb.vampier.net/downloads.php

此方には登録されていないROMがありますが、登録を追加するにはROMイメージのアップロードを要求するシステムなので、日本からは追加不能です。

そのため、別のxmlファイルに不足分を記述して`softwaredb.xml`と合成することで各自柔軟に対応可能となります。

## 使い方

```
msx_softwaredb_xml_merge 出力ファイル ベースファイル 追加ファイル1 追加ファイル2 ...
```
追加ファイルは必要であれば複数指定可能です。
後に指定した物が優先です。


### pythonでの実行例
```
python3 msx_softwaredb_xml_merge.py softwaredb.xml softwaredb.xml softwaredb.addition.xml
```

### exeでの実行例
```
msx_softwaredb_xml_merge.exe softwaredb.xml softwaredb.xml softwaredb.addition.xml
```

## 添付の softwaredb.addition.xml

添付の `softwaredb.addition.xml` には私の所有する未登録ROMが記述してありますが
本家でとりこみが終わっていますので、これらは追加不要です。

- ハイドライド3 MSX2版 後期ロム（銀製の剣、暴走バグ、ミスタイプ修正版）
- パチコン 後期ロム（ROM埋め込みメッセージ削除版）

```
  <software title="Hydlide 3 - The Space Memories" system="MSX2" company="T&amp;ESOFT" year="1987" country="JP" genmsxid="992">
    <rom sha1="391d07c3772f7245b2c11236f67929c9e499e56f" type="ASCII8" remark="Revision 8809D" />
  </software>

  <software title="Pachicom" system="MSX" company="Toshiba-EMI" year="1985" country="JP" genmsxid="592">
    <rom sha1="39913a574e5c4ff316852868f179dbf3a80d514c" type="Mirrored" remark="Revision 2" />
  </software>
```

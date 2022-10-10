カートリッジを後挿しして、
ROMからOPLDRV用BGMデータをファイルに書き出すプログラム。

R-TYPE用：RDRTYPE.BAS
FM PAC用：RDFMPAC.BAS

一度VRAMに書き出してからBSAVEするだけの処理のため、
BSAVEヘッダが余計についています。
*.oplは*.binの先頭の7バイトをバイナリエディタ等で削除してください。
MSXFAN 1992年10月号 付録ディスク#13収録の
MSX2用イドライド用置き換え画像データ

GAME.XBで読み込んでいる
TITLE.XV8
VRAM-2.XV8
の置き換え用画像データです。

VRAM-2はフォントをHYDLIDE3のエンディングフォントに置き換えています。
TITLEMは最近みかけない丸和太郎に置き換えています。

60 _XUNPACKS("TITLE   xv8",0)
70 _XUNPACKS("VRAM-2  xv8",1)
を
60 _XUNPACKS("TITLE   xv8",0)
70 SETPAGE,1;BLOAD"VRAM-2.SR8",S
（中略）
85 SETPAGE,0:BLOAD"TITLEM.SR8",S
に書き換えてみてください。

TITLEM.SR8はお好みで。
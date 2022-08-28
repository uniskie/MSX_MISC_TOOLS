## 概要

BASICからCHGCPU/GETCPUを呼び出すサンプルです。  

* CHGCPU.BAS ... 選択してCPU切り替え  
* GETCPU.BAS ... 現在のCPU表示  
* Z80.BAS    ... Z80モードに切り替え  
* R800.BAS   ... R800 ROMモードに切り替え（安全のためDRAMにはしません）  

* CHGCPU_FROM_BASIC.txt ... CHGCPU呼び出し処理のアセンブラコード  
* GETCPU_FROM_BASIC.txt ... GETCPU呼び出し処理のアセンブラコード  

## 解説

CHGCPU用機械語コード宣言は1010行でDEFUSR0  
GETCPU用機械語コード宣言は1020行でDEFUSR1  
共通のメモリ書き込み処理は2000行からになります。  
MERGEして両方使う場合にやりやすいかと思いますが、
外部エディタで編集すれば済むのであまり意味は無いかもしれません。  

## 注意事項

フリーエリア宣言を変更しないように、
VOICAQ、VOICBQ を使用しています。

* VOICAQ : $F975 - $F9F4  
* VOICBQ : $F9F5 - $FA74  
* VOICCQ : $FA75 - $FAF4  

この領域はPLAY文での演奏時に内部的に使用するエリアで、
PLAY文で演奏していないときは書き換えても大丈夫らしいので使用しています。  

そのため、PLAY文で音楽を演奏した状態では呼び出さないようにしてください。  


# BASICからのCPUモード操作

![](../img/CPUMODE.png)

## 概要

BASICからCHGCPU/GETCPUを呼び出すサンプルです。  

* [CPUMODE.BAS](CPUMODE.BAS) ... CPUモードの設定/取得  
* [CHGCPU.BAS](CHGCPU.BAS) ... 選択してCPU切り替え  
* [GETCPU.BAS](GETCPU.BAS) ... 現在のCPU表示  
* [Z80.BAS](Z80.BAS)     ... Z80モードに切り替え  
* [R800.BAS](R800.BAS)   ... R800 ROMモードに切り替え（安全のためDRAMにはしません）  

* [CPUMODE.ASM](CPUMODE.ASM) ... CPUMODE.BASの機械語部分アセンブラコード  
* [CHGCPU_FROM_BASIC.txt](CHGCPU_FROM_BASIC.txt) ... CHGCPU呼び出し処理のアセンブラコード  
* [GETCPU_FROM_BASIC.txt](GETCPU_FROM_BASIC.txt) ... GETCPU呼び出し処理のアセンブラコード  

## 解説

### CPUMODE

CPUモードの設定/取得を行います。
BIOSのCHGCPUやGETCPUがない機種では何もしません。

機械語コード宣言は10行でDEFUSR

使い方は
```整数変数=USR(mode値)```

例) ```A=USR(1)``` ... R800に変更する。実際に変更されたモードはAに入る

※ 返り値を受け取る変数と引数(mode値)は整数である事

| mode値 | 動作 |
|---|---|
| 0 | Z80に変更  
| 1 | R800(ROM)  
| 2 | R800(DRAM)  
| それ以外 | =現在のモードを取得  

### CHGCPU / GETCPU

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

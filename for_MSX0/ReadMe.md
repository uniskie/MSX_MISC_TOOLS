# MSX0 関連: IOT I/O ACCESS

MSX0 Iot ROM ver 0.05.04 での実装に基づいた情報です。
独自調査なので一部間違いがある可能性があります。

---

## SAMPLE

![BIGAJUU.png](img/BIGAJUU.png)
[BIGAJUU/](BIJAJUU/)  
[BIGAJUU.DSK](BIGAJUU.DSK)  

###

### 実装

- ジャイロ・加速度センサーの利用
  - タッチまたはトリガで位置リセット
  - 位置リセット時、Y軸の範囲外の時はZ軸に切り替え（逆も同様）
- べーしっ君存在チェック  
  あれば利用する  
  ない場合でも動作
- MSX0 IOT、ジャイロ・加速度センサーの存在チェック  
  あれば利用する  
  ない場合でも動作
- タッチパネルや傾きで目が動く
- 時計機能

## べーしっ君チェック

[CHKXBAS.BAS](BIGAJUU/CHKXBAS.BAS)

```
10 ON ERROR GOTO 1000
20 TR%=2 ' _TURBO ONチェック有効化
30 _TURBO ON(TR%)
40 '※
50 '  _TURBO ON(TR%)にするのは
60 '   DIMの前に
70 '   CLEARやDEFINTやDEFSNG以外の命令があると
80 '   エラーになる為
90 '
100 '*** MAIN ***
110 IF TR% THEN PRINT"TURBO" ELSE PRINT"NORMAL"
120 ' ...
300 TR%=1 ' _TURBO OFFチェック有効化
310 _TURBO OFF
320 ON ERROR GOTO 0
330 PRINT "END"
340 END
350 ' ...
999 '*** ERROR hook ***
1000 '(TR%=2) => _TURBO ONでエラー
1010 IF TR%=2 THEN TR%=0:RESUME 100 'ノーマル実行としてメイン処理へ戻る
1020 '(TR%=1) => _TURBO OFFでエラー
1030 IF TR%=1 THEN TR%=0:RESUME 320 '終了処理へ戻る
1040 '通常のエラー処理
1050 PRINT"Error in ";ERL
1060 ERROR ERR
```

- TR=2で_TURBO ON  
  TR=1ならべーしっ君有効
- TR=1で_TURBO OFF  
  単にエラーを無視するだけ

## MSX0 IOT命令/I2Cデバイスチェック

[I2C68CHK.BAS](BIGAJUU/I2C68CHK.BAS)

```
100 CLEAR 200:DEFINT A-Z
110 '********************************
120 '* AE : MSX0 IOT & MPU06886
130 '********************************
140 AE=0:ON ERROR GOTO 300
160 ND$="device/i2c_i":_IOTFIND(ND$,CN):IF CN<1 THEN 210
170 DIM D$(CN-1):_IOTFIND(ND$,D$(0),CN)
180 FOR I=0 TO CN-1:AE=AE OR (D$(I)="68"):NEXT '68=MPU6886
190 ERASE D$:GOTO 210
200 RESUME 210
210 ON ERROR GOTO 0 'END of CHECK
220 PRINT ND$+"68 is";
230 IF AE=0 THEN PRINT" not";
240 PRINT" found."
250 END
260 '
300 '*** ERROR
310 RESUME 210
```

- AEが0以外なら有効

- デバイスID
  - device/i2c_i/08 ... [Faces キーボード]
  - device/i2c_i/34 ... AXP192(電源管理ユニット)
  - device/i2c_i/38 ... FT6226U(タッチパネル)
  - device/i2c_i/51 ... BM8563(RTC)
  - device/i2c_i/68 ... [Bottom2] MPU6886(9軸加速度センサー

  ※ 接続デバイスの一覧は付属SDに入っている```SAMPLE.DSK```の```TREE.BAS```で確認可能。

  ※ IDとの対応はm5 stackドキュメントの [I2C Address表](https://docs.m5stack.com/en/product_i2c_addr)を参照。


## _TURBO ON/OFF TIPS

### ```ON STOP``` ```STOP ON``` ```ON ERROR``` の挙動

- ```ON STOP GOSUB 行番号:STOP ON```
- ```ON ERROR GOTO 行番号```

1. コンパイルモードでなければ使用できる。  

   コンパイルモードでは実行できないが、  
  ```_TURBO ON```の前や```_TURBO OFF```の後では使用できる。

2. 飛び先行番号は  
   ```_TURBO ON```の前か```_TURBO OFF```の後でないと、   
   基本的にエラーになる。

3. ```_TURBO ON```の前に使用していた場合、  
   ```_TURBO ON```から```STOP OFF```までの間は反応しないが、  
   ```_TURBO OFF```の後に実行される。

   ```ON ERROR```は  
   ```_TURBO ON```実行でコンパイルする際に発生するエラーにも反応する。

### CTRL+STOPの挙動

- ```_TURBO ON```から```_TURBO OFF```の間に```CTRL+STOP```を押した場合
  1. ```_TURBO OFF```までは反応しない。
  2. ```_TURBO OFF```の**直後**に実行がブレイクされてしまう。

  そのため、```_TURBO OFF```の後に（コンパイル実行できない）処理を書いていた場合、  
  それらの処理が実行されずに終了してしまう事になる。

  H.TIMIフックを戻す処理など、  
  必ず実行したい処理がある場合は、  
  ```_TURBO OFF```の前に実行すると良い。

  ファイルセーブやロードなどは  ON STOP を利用すると良い。  

  1. ```_TURBO ON```の前に```ON STOP GOSUB 行番号```:```STOP ON```を実行しておく。
  2. ```ON STOP GOSUB``` の飛び先は、```_TURBO ON```から```_TURBO OFF```の範囲外である事。

### 呼び出し・ジャンプ可能な行番号の範囲

- ```_TURBO ON```～```_TURBO OFF```の間でだけアクセスできる。
- ```_TURBO ON```～```_TURBO OFF```の外から外ならアクセスできる。  

  例)  
  ```_TURBO ON```より前の行番号から  
  ```_TURBO OFF```より後の行番号がアクセスできる

---

## MSX0 I/Oポート
- PORT 8 : IOT操作（入出力）
- PORT 16: ターミナルコンソールへの出力（出力）

## MSX0 IOT操作 基本の流れ
1. コマンド出力
2. データ出力 or データ取得

読み書きはI/Oポート8番を使用する

## MSX0 IOT操作 ノード読み書きの流れ
1. コマンド出力（ノード指定）
2. ノード名出力
3. 1byte I/O読み込み → bit7 が 1ならエラー
4. コマンド出力 (put/get/find)
5. データ出力 or データ取得

※ 配列ならデータ取得開始```out (8), #80```から繰り返す

## (1) #E0: 処理開始
```
#e0, #01, コマンド+型ID
```
- #e0 ... コマンド指定  
- #01 ... コマンドデータサイズ
- コマンド+型ID
  | bit | 7 - 4 | 3 | 2 - 0 |
  |-----|-------|---|-------|
  |     | CMD   | ? |  型   |
  
  bit6 が 1 なら 書き込み が 共通？

### #50: ノード指定 開始
  ```
	#e0,#01,#53
  ```
  - 型指定は文字列(3)で固定なので3バイト目は#53固定
  - ノード指定後にポートを1回読み込み、Bit7が立っていればエラー

###  #40: iotput 開始
  ```
	#e0,#01,#40 + 型ID
  ```
###  #00: iotget 開始
  ```
	#e0,#01#,#00 + 型ID
  ```
###  #10: iotfind 開始
  ```
	#e0,#01,#10 + 型ID
  ```

###   型ID
- 1=2バイト整数型
- 2=単精度実数型
- 3=文字列
- 4=倍精度実数型

> DACの型情報[VALTYP]からの変換(c/c++/js)  
> ```[VALTYP] == 3 ? [VALTYP] : [VALTYP] >> 1;```

> **おまけ**  
> DACの型情報[VALTYP]は変数記述子のサイズと一致する
> - 2=整数型(2バイト)
> - 3=文字列型(3バイト)(文字数+文字列データアドレス)
> - 4=単精度実数型(4バイト)
> - 8=倍精度実数型(8バイト)



## (2-A) #C0: データ出力
```
	#c0, データ長n, データ*n個, #00
```
> **CAUTION**  
> ※ データ長が64byte以上の場合は分割が必要  
> ```
> #C0を出力 ;データ出力の開始
> WHILE (データ長 >= 64) 
>     (データ長ではなく)#7Fを出力  
>     データを63byte出力
>     データ長 -= 63
>     データの位置 += 63
> LOOP
> IF (データ長 > 0)
>     データ長を出力
>     データを全部出力
> ENDIF
> #00を出力 ;データ出力の終了
> ```

### 2バイト整数出力:
```
	#c0, #02, 数値下位1byte, 数値上位1byte, #00
```

### 文字列出力:
```
	#c0, [データ長, 文字列], #00
```

## (2-B)  #80: データ取得
```
	(out)#80, (in)データ長n, データ*n
```

### 数値取得
```
	(out)#80, (in)データ長, (in)Low 1byte, (in) High 1byte
```

※ 現在は2バイト整数しか返さない
※ そのため、データ長は2byte決め打ちで読み捨てでも良い

### 文字列取得
```
	(out)#80, (in)データ長, (in)文字列データ*データ長分繰り返し
```

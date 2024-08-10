;-*- tab-width: 8 -*-
;============================================
; MSX0 IOT操作 ライブラリ IOTCMD.INC
; 使用アセンブラ：TNIASMかSJASMPLUS
;============================================

;================================================================
;	MSX0 Iot ROM
;		ver 0.05.04
;		ver 0.07.08 - I/Oポート変更
;			旧：08H → 新：58H
;			旧：10H → 新：57H
;
; デバイス拡張：使用しない方が良い
;	 OPEN"iot:" #n:PRINT#n:INPUT#n は未完成。フリーズもあり
;
; ステートメント拡張：
;	 ※ Vは数値変数か文字変数
;	 ※ Nは数値変数
;	CALL IOTINIT()
;	CALL IOTPUT("NodeNname", V)
;	CALL IOTGET("NodeNname", V)
;	CALL IOTFIND("NodeNname", N)
;	CALL IOTFIND("NodeNname", V(0), COUNT)
;	
;	機能不明：CALL IOTSEND("", "")
;		他の命令とプロトコルが異なる
;
;================================================================
;I/Oポート
;	8 	IOT操作（入出力）
;	16	ターミナルコンソールへの出力（出力）
;================================================================
;ノードアクセスの流れ
;	(1) コマンド出力（ノード指定）
;	(2) ノード名出力
;	(3) 1byte I/O読み込み→bit7が1なら存在しない
;	(4) コマンド出力 (put/get/find)
;	(5) データ出力 or データ取得
;================================================================
;基本の流れ
;	(1) コマンド出力
;	(2) データ出力 or データ取得

;################################################################
;(1) コマンド #e0, #01, コマンド+型ID
;   ※ #E0 = コマンド指定
;   ※ #01 = コマンドデータサイズ
;################################################################
;   ノード指定	#e0, #01, #53
;		※ #53 ... コマンド #50
;		           型指定は文字列(3)で固定
;		※ ノード指定後にポートを1回読み込み、
;		   bit7が立っていればエラー
;----------------------------------------------------------------
;   iotput	#e0, #01, #40 + 型ID
;----------------------------------------------------------------
;   iotget	#e0, #01#, #00 + 型ID
;----------------------------------------------------------------
;   iotfind	#e0, #01, #10 + 型ID
;----------------------------------------------------------------

;================================================================
;   型ID
;================================================================
;		1=2バイト整数型
; 		2=単精度実数型
; 		3=文字列
; 		4=倍精度実数型

;################################################################
;(2) データ
;################################################################
;================================================================
;(2)-A データ出力 #c0, データ長n, データ*n, #00
;================================================================
;	※ データ長が64を超える場合は分割が必要
;	WHILE (データ長 > 64)
;	    #7Fを出力
;	    データを64byte出力
;	    データ長 -= 64
;	    データの位置 += 64
;	LOOP
;	IF (データ長 > 0)
;	    データ長を出力
;	    データを全部出力
;	ENDIF
;----------------------------------------------------------------
;   2バイト整数出力:
;	#c0, #02, 数値下位1byte, 数値上位1byte, #00
;----------------------------------------------------------------
;   文字列出力:
;	#c0, [データ長, 文字列], #00
;----------------------------------------------------------------
;================================================================
;(2)-B データ取得 (out)#80, (in)データ長n, データ*n
;================================================================
;----------------------------------------------------------------
;   数値取得:
;----------------------------------------------------------------
;	(out) #80, (in)データ長, (in)Low 1byte, (in) High 1byte
;----------------------------------------------------------------
;   文字列取得
;----------------------------------------------------------------
;	(out) #80, (in)データ長, (in)文字列データ*データ長分繰り返し
;----------------------------------------------------------------
;   ※ 配列の場合
;----------------------------------------------------------------
;   (out)#80 は データの頭出しなので、
;   配列などの場合は、(out)#80 せずに連続で読み込む
;   例）
;       (out)#80, (in)データ長n, データ*n, (in)データ長n, データ*n,
;                 (in)データ長n, データ*n ....

;================================================================
; 値定義
;================================================================
; I/O port
; ver 0.05.04
;iot_io:		equ	#08	;I/O port IOT制御
;terminal_io:	equ	#10	;I/O port ターミナルコンソールへ出力
; ver 0.07.08 - I/Oポート変更
iot_io:		equ	#58	;I/O port IOT制御
terminal_io:	equ	#57	;I/O port ターミナルコンソールへ出力

; (VALTYP)の値 = BASIC変数記述子のサイズ
valtyp_int:	equ	#02	;2=2バイト整数型
valtyp_str:	equ	#03	;3=文字列型
valtyp_sng:	equ	#04	;4=単精度実数型
valtyp_dbl:	equ	#08	;8=倍精度実数型

; IOTコマンドの変数型
;	iodtyp = (VALTYP)==3 ? (VALTYP) : (VALTYP) >> 1;
iodtyp_int	equ	#01	;1=2バイト整数型
iodtyp_sng	equ	#02	;2=単精度実数型	* 現在未対応
iodtyp_str	equ	#03	;3=文字列
iodtyp_dbl	equ	#04	;4=倍精度実数型	* 現在未対応

; コマンド出力
;	#e0, コマンドデータサイズ, コマンド本体(IOTコマンドビット|IOT変数型)
iod_cmd_start:	equ	#e0	;コマンド設定のはじめ
iod_cmd_node:	equ	#50	;node name
iod_cmd_put:	equ	#40	;iotput
iod_cmd_get:	equ	#00	;iotget
iod_cmd_find:	equ	#10	;iotfind

; データ出力
;	#c0, データサイズ, データ本体, #00
iod_data_start:	equ	#c0	;データ出力のはじめ
iod_data_end:	equ	#00	;データ出力のおわり

; データ取得
;	#80, データサイズ, データ本体
;	整数要求時、データサイズは読み捨てしている様子
iod_data_req:	equ	#80	;データ取得リクエスト

; データサイズが64以上ある場合のサイズ情報
iod_data_ov64:	equ	#7f	;データサイズが64以上ある場合のサイズ情報

;================================================================
; ノード名設定
; in:	hl = string address
;	a  = string length
; ret:	Cy = 1:error
; use:	af, hl, e, bc
;================================================================
iotlib_set_node:
	ld	c, a	;長さ

	; node set
	ld	e, iod_cmd_node + iodtyp_str
	call	iotlib_set_cmd

	; node data
	ld	a, c	;長さ
	call	iotlib_write_buf

	; node check
	in	a, (iot_io)
	rlca

	ret

;================================================================
; iotfind (int)
; in:	iotlib_set_node で ノード指定
; out: 	hl = 見つかったサブノードの個数
; use:	af, hl
;================================================================
iotlib_find_int:
	; get(int) cmd
	ld	e, iod_cmd_find + iodtyp_int
	call	iotlib_set_cmd
	
	; 2バイト受信
	call	iotlib_read_start	;頭出し
	call	iotlib_read_int
	ret

;================================================================
; iotfind (buffer)
; in:	iotlib_set_node で ノード指定
;	hl = buffer address
;	a  = max size
; out: 	[hl] = 一つ目のサブノード(文字列)
;	a  = 受信した data size
;	※ サブノードが複数あって、
;	   続いて次のサブノードを取得したい場合は
;	   新しい bufferとmax sizeを指定して
;	   iotlib_read_bufを呼び出す
; use:	af, bc, hl
;================================================================
iotlib_find_buf:
	ld	c, a	;max size

	; get(int) cmd
	ld	e, iod_cmd_find + iodtyp_str
	call	iotlib_set_cmd
	
	; 多バイト受信
	call	iotlib_read_start	;頭出し
	ld	a, c
	call	iotlib_read_buf

	ret

;================================================================
; iotget (int)
; in:	iotlib_set_node で ノード指定
; out: 	hl = data
; use:	af, hl
;================================================================
iotlib_get_int:
	; get(int) cmd
	ld	e, iod_cmd_get + iodtyp_int
	call	iotlib_set_cmd
	
	; 2バイト受信
	call	iotlib_read_start	;頭出し
	call	iotlib_read_int
	ret

;================================================================
; iotget (buffer)
; in:	iotlib_set_node で ノード指定
;	hl = buffer address
;	a  = max size
; out: 	[hl] = data(byte配列)
;	a  = 受信した data size
; use:	af, bc, hl
;================================================================
iotlib_get_buf:
	ld	c, a	;max size

	; get(int) cmd
	ld	e, iod_cmd_get + iodtyp_str
	call	iotlib_set_cmd
	
	; 多バイト受信
	call	iotlib_read_start	;頭出し
	ld	a, c
	call	iotlib_read_buf

	ret

;================================================================
; iotput (int)
; in:	iotlib_set_node で ノード指定
;	hl = data
; use:	af, hl
;================================================================
iotlib_put_int:
	; get(int) cmd
	ld	e, iod_cmd_put + iodtyp_int
	call	iotlib_set_cmd
	
	; 2バイト送信
	call	iotlib_write_int
	ret

;================================================================
; iotput (buffer)
; in:	iotlib_set_node で ノード指定
;	hl = data address
;	a  = data size
; use:	af, bc, hl
;================================================================
iotlib_put_buf:
	ld	c, a	;max size

	; get(int) cmd
	ld	e, iod_cmd_put + iodtyp_str
	call	iotlib_set_cmd
	
	; 多バイト送信
	ld	a, c
	call	iotlib_write_buf

	ret

;================================================================
; 開始信号送信
; in:	e = cmd
; use:	af
;================================================================
iotlib_set_cmd:
	; node set
	ld	a, iod_cmd_start
	out	(iot_io), a
	ld	a, 1
	out	(iot_io), a
	ld	a, e
	out	(iot_io), a
	ret

;================================================================
; データ受信開始
; 頭出し（読み出しがデータの先頭からになる）
; use:	af
;================================================================
iotlib_read_start:
	ld	a, iod_data_req
	out	(iot_io), a
	ret

;================================================================
; 2バイトデータ受信
; 事前に iotlib_read_start を呼び出しておく（頭出し）
; out:	hl = data
; use:	af, hl
;================================================================
iotlib_read_int:
	in	a, (iot_io)	;size = 2
	;読み捨て

	in	a, (iot_io)
	ld	l, a

	in	a, (iot_io)
	ld	h, a

	ret

;================================================================
; 多バイトデータ受信
; 事前に iotlib_read_start を呼び出しておく（頭出し）
; in:	a = max size
;	hl = buffer address
; out:	a = size
;	[hl] = data * size
; use:	af, bc, hl
;================================================================
iotlib_read_buf:
	ld	c, a		;max size

	in	a, (iot_io)	;size
	cp	c
	jr	c, iotlib_read_buf_1 ;size < maxsize
	ld	a, c		;size = max size

iotlib_read_buf_1:
	ld	c, a
	ld	b, a
	
iotlib_read_buf_lp:
	in	a, (iot_io)
	ld	(hl), a
	inc	hl
	djnz	iotlib_read_buf_lp

	ld	a, c
	ret

;================================================================
; 2バイトデータ送信
; in:	hl = data
; use:	af, hl
;================================================================
iotlib_write_int:
	ld	a, iod_data_start
	out	(iot_io), a

	ld	a, 2
	out	(iot_io), a	;size = 2

	ld	a, l
	out	(iot_io), a

	ld	a, h
	out	(iot_io), a

 if iod_data_end
	ld	a, iod_data_end
 else
	xor	a
 endif
	out	(iot_io), a

	ret

;================================================================
; 多バイトデータ送信
; in:	hl = address
;	a  = size
; use:	af, bc, hl
;================================================================
iotlib_write_buf:
	ld	c, a ;全体の長さ

	; データ開始
	ld	a, iod_data_start
	out	(iot_io), a

iotlib_write_buf_lp:
	ld	a, c
	cp	64
	jr	c, iotlib_write_buf_1
	
	ld	a, iod_data_ov64	; 64byte以上

iotlib_write_buf_1:
	; データサイズ
	;size info (size or $7f)
	out	(iot_io), a

	; if (size >= 64):  $7f  & 63 = 63
	; if (size <  63):  size & 63 = size
	and	$3f
	ld	b, a	; 書き出しサイズ

	ld	a, c
	sub	b
	ld	c, a	; size -= 書き出しサイズ

	; データをbバイト送信
iotlib_write_buf_ll:
	ld	a, (hl)
	out	(iot_io), a
	inc	hl
	djnz	iotlib_write_buf_ll

	; 残りサイズ0になるまで繰り返し
	xor	a
	or	c
	jr	nz, iotlib_write_buf_lp

	; データ終端
 if iod_data_end
	ld	a, iod_data_end
 else
	xor	a
 endif
	out	(iot_io), a

	ret

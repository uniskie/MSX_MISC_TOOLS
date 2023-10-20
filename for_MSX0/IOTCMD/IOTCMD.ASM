;-*- tab-width: 8 -*-
;============================================
; MSX0 IOT操作 ライブラリ IOTCMD.INC 用
; XBASIC/BASIC向けインターフェース
; 使用アセンブラ：TNIASMかSJASMPLUS
;============================================
	fname	"IOTCMD.BIN"

start_adr:	equ	$D000

VALTYP:		equ	$F663
DAC:		equ	$F7F6
	;======================
	;BINHEADER
	;======================
	db	0xfe
	dw	start_adr
	dw	end_adr - 1
	dw	start_adr
	;======================

	org	start_adr

usr_tbl:
	jp	set_xbasic	;+0	TURBOモードの時に A=USR(1)
	jp	iot_node	;+3	A=USR1(VARPTR(ND$))	ノード名を設定する
	jp	iot_put_i	;+6	A=USR2(D)		整数を送信
	jp	iot_put_s	;+9	A=USR3(VARPTR(D$))	文字列を送信
	jp	iot_get_i	;+12	A=USR4(0)		整数を受信
	jp	iot_get_s	;+15	A=USR5(VARPTR(D$))	文字列を受信（D$の文字長まで）
	jp	iot_find_i	;+18	A=USR6(0)		サブノード数を受信
	jp	iot_find_s	;+21	A=USR7(VARPTR(D$))	サブノード名文字列を受信（D$の文字長まで）
				;				※ 複数ある場合、2個目以降は iot_read_s を使う
	jp	iot_read_i	;+24	A=USR8(0)		配列の次の整数を受信（整数配列用）
	jp	iot_read_s	;+27	A=USR9(VARPTR(D$))	配列の次の文字列を受信（D$の文字長まで）

is_xbasic:	db	0

;================================================
; べーしっ君のTURBO ONを使用中なら1を指定
; ※ べーしっ君TURBOモードでは
;    通常と文字変数の扱いが異なる為
;    ここで指定して処理を変えないと大変な事になる。
; in:	a=usr(0)
;	または
;	a=usr(1)
;================================================
set_xbasic:
	cp	valtyp_int
	ret	nz

	inc	hl
	inc	hl
	ld	a, (hl)
	ld	(is_xbasic), a
	ret

;================================================
; ノードを指定
; in:	a=usr(varptr(nd$))
; ret: -1=エラー
;================================================
iot_node:
	cp	valtyp_int
	ret	nz	;整数のみ受け付け

	push	hl
	call	get_usr_string
	jr	c, iot_node_end	;引数が適合しないなら何もしない

	call	iotlib_set_node

iot_node_end:
	pop	ix
	ld	(ix+2), 0
	ld	(ix+3), 0
	ret	nc

	; ノードエラー -1を返す
	ld	(ix+2), 255
	ld	(ix+3), 255
	ret

;================================================
; iotput (int)
;	事前にiot_nodeでノード指定してから呼ぶ
; in:	a=usr(d)
;================================================
iot_put_i:
	cp	valtyp_int
	ret	nz	;整数のみ受け付け

	call	get_usr_int
	call	iotlib_put_int

	ret

;================================================
; iotput (string)
;	事前にiot_nodeでノード指定してから呼ぶ
; in:	a=usr(varptr(d$))
;	a$=usr(d$) ※TURBO ON不可
;================================================
iot_put_s:
	call	get_usr_string
	ret	c	;引数の型が一致しない

	call	iotlib_put_buf

	ret

;================================================
; iotget (int)
;	事前にiot_nodeでノード指定してから呼ぶ
; out:	a=usr(0) ... 読み込んだ整数
;================================================
iot_get_i:
	cp	valtyp_int
	ret	nz	;整数のみ受け付け

	push	hl
	call	iotlib_get_int
	pop	ix
	ld	(ix+2), l
	ld	(ix+3), h

	ret

;================================================
; iotget (string)
;	事前にiot_nodeでノード指定してから呼ぶ
; a=usr(varptr(d$))
; out:	d$ = 取得した値
;	a  = 長さ
;	TURBO OFF: d$の文字数までしか取得できない
;	TURBO ON:  255文字までしか取得できない
;================================================
iot_get_s:
	cp	valtyp_int
	ret	nz	;整数以外なら何もしない

	push	hl
	call	get_usr_string
	jr	c, iot_get_s_end

	ld	a, b	;格納可能最大サイズ
			;文字列領域に読み込む
	or	a	;最大サイズが0なら実行不能
	jr	z, iot_get_s_end

	call	iotlib_get_buf

iot_get_s_end:
	pop	ix
	ld	(ix+2), a	;長さを返す
	ld	(ix+3), 0
	ret

;================================================
; iotfind (int)
;	事前にiot_nodeでノード指定してから呼ぶ
; out:	a=usr(0) ... 読み込んだ整数
;================================================
iot_find_i:
	cp	valtyp_int
	ret	nz	;整数のみ受け付け

	push	hl
	call	iotlib_find_int
	pop	ix
	ld	(ix+2), l
	ld	(ix+3), h

	ret

;================================================
; iotfind (string)
;	事前にiot_nodeでノード指定してから呼ぶ
; a=usr(varptr(d$))
; out:	d$ = 取得した値
;	a  = 長さ
;	TURBO OFF: d$の文字数までしか取得できない
;	TURBO ON:  255文字までしか取得できない
;================================================
iot_find_s:
	cp	valtyp_int
	ret	nz	;整数以外なら何もしない

	push	hl
	call	get_usr_string
	jr	c, iot_find_s_end

	ld	a, b	;格納可能最大サイズ
			;文字列領域に読み込む
	or	a	;最大サイズが0なら実行不能
	jr	z, iot_find_s_end

	call	iotlib_find_buf

iot_find_s_end:
	pop	ix
	ld	(ix+2), a	;長さを返す
	ld	(ix+3), 0
	ret

;================================================
; read next (int)
;	配列用：次の整数を読み込む
; out:	a=usr(0) ... 読み込んだ整数
;================================================
iot_read_i:
	cp	valtyp_int
	ret	nz	;整数のみ受け付け

	push	hl
	call	iotlib_read_int
	pop	ix
	ld	(ix+2), l
	ld	(ix+3), h

	ret

;================================================
; read next (string)
;	配列用：次の文字列を読み込む
;	iot_find_sを呼び出して1個目を取得した後
;	子ノードの2個目以降を取得する際などに使う
; a=usr(varptr(d$))
; out:	d$ = 取得した値
;	a  = 長さ
;	TURBO OFF: d$の文字数までしか取得できない
;	TURBO ON:  255文字までしか取得できない
;================================================
iot_read_s:
	cp	valtyp_int
	ret	nz	;整数以外なら何もしない

	push	hl
	call	get_usr_string
	jr	c, iot_read_s_end

	ld	a, b	;格納可能最大サイズ
			;文字列領域に読み込む
	or	a	;最大サイズが0なら実行不能
	jr	z, iot_read_s_end

	;次のデータを読むので頭出ししない
	;call	iotlib_read_start
	;ld	a, b

	call	iotlib_read_buf

iot_read_s_end:
	pop	ix
	ld	(ix+2), a	;長さを返す
	ld	(ix+3), 0
	ret

;================================================
; 整数を取得する
; in:	a  ... vartyp
;	hl ... usr引数アドレス
; out:	hl ... 整数
; use:	de, hl
;================================================
get_usr_int:
	inc	hl
	inc	hl
	ld	e, (hl)
	inc	hl
	ld	d, (hl)
	ex	de, hl
	ret

;================================================
; ターボON/OFFに合わせて
; 文字列アドレスと長さを取得
; in:	a  ... vartyp
;	hl ... usr引数アドレス
; out:	hl ... data address
;	a  ... length
;	b  ... max length
;	c  ... vartyp
;	cy ... 1 = error ... hl, a, cは無効
; use:	af, c, de, hl
;================================================
get_usr_string:
	ld	c, a	;a=valtype
	ld	a, (is_xbasic)
	or	a
	ld	a, c
	jr	nz, get_usr_string_xbasic	;べーしっ君用処理へ

; normal basic
	cp	valtyp_str
	jr	z, get_usr_string_bas
; 通常BASIC string引数
; a$=usr(a$)
; deレジスタ
;	+0: (1) 文字数
;	+1: (2) 文字格納領域アドレス

	cp	valtyp_int
	jr	nz, get_usr_string_err
; 通常BASIC integer引数
; a=usr(varptr(a$))
; [hl+2]:
; varptr(a$):
;	+0: (1) 文字数
;	+1: (2) 文字格納領域アドレス

	inc	hl
	inc	hl
	ld	e, (hl)
	inc	hl
	ld	d, (hl)

get_usr_string_bas:
; deレジスタ
;	+0: (1) 文字数
;	+1: (2) 文字格納領域アドレス
	ex	de, hl
	ld	a, (hl)	;a = length
	ld	b, a	;c = max = length
	inc	hl
	ld	e, (hl)
	inc	hl
	ld	d, (hl)
	ex	de, hl
	or	a	;cy=0
	ret

; xbasic べーしっ君 int引数
; a=usr(varptr(a$))
; [hl+2]:
; varptr(a$):
;	+0:(1)   文字数
;	+1:(255) 255バイトの文字格納領域
get_usr_string_xbasic:
	cp	valtyp_int
	jr	nz, get_usr_string_err
	
	inc	hl
	inc	hl
	ld	e, (hl)
	inc	hl
	ld	d, (hl)
	ex	de, hl

	ld	a, (hl)	;a = length
	ld	b, 255	;c = max べーしっ君では最大255バイト固定で確保されている
	inc	hl
	or	a	;cy = 0
	ret

get_usr_string_err:
	xor	a
	scf	;cy = 1
	ret

;;================================================
;; BASICエラー処理に飛ばす
;ERR_Syntax error:		equ	2	;Syntax error
;ERR_Illegal_function_call:	equ	5	;Illegal function call
;ERR_Type_Mismatch:		equ	13	;Type mismatch
;ERR_Device_Io_Error:		equ	19	;Device I/O error
;;================================================
;go_error_type_mismatch:
;	ld	e, ERR_Type_Mismatch	;13.	Type mismatch
;	ld	ix, #406f	;BASIC内部ルーチン：エラーの発生 E=エラー番号
;	jr	#41e1

;================================================
	include	"IOTCMD.INC"
;================================================


end_adr:
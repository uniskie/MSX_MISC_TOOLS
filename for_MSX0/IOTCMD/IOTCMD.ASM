;-*- tab-width: 8 -*-
;============================================
; MSX0 IOT操作 ライブラリ IOTCMD.INC 用
; XBASIC/BASIC向けインターフェース
; 使用アセンブラ：TNIASMかSJASMPLUS
;============================================
	fname	"IOTCMD.BIN"

include_datetime:	equ	1	;時刻日付取得ルーチンを組み込む

start_adr:	equ	$D000

;==== system wor ====k
;VALTYP:		equ	$F663
;DAC:		equ	$F7F6

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
	jp	set_flag	;+0	a=user(flag)
				;	べーしっ君モード:   flagにbit0=1(1)
				;	疑似バーストリード: flagにbit1=1(2)
				;	（レジスタアドレスを加算しながら連続読み込み）
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

 if include_datetime
	JP	read_datetime	;+30	A=USR10(VARPTR(D$))	クロックICを読み込む
				;				"GET TIME" または
				;				"GET DATE" を指定
 endif ;include_datetime

;==== 動作フラグ ===
mode_flag_xbasic:	equ	$01	;bit0
mode_flag_burst_read:	equ	$02	;bit1	for iot_get_s
					;       疑似バーストリードモードにする
					;	渡された文字長までレジスタアドレス加算しながら
					;	連続読み込み
mode_flag:	db	0

no_reg:		equ	255		;レジスタ指定なし
;i2c_i_flag:	db	0		;ノードが"device/i2c_i"かどうか
i2c_i_reg:	db	no_reg		;最後に指定したi2c_i レジスタアドレス
					;iot_nodeでno_regに初期化
					;iot_nodeのあとの最初のiot_put_sの最初の1バイト

;================================================
; べーしっ君のTURBO ONを使用中なら1を指定
; ※ べーしっ君TURBOモードでは
;    通常と文字変数の扱いが異なる為
;    ここで指定して処理を変えないと大変な事になる。
; in:	a=usr(f)
;	f ... bit0=xbasic
;	  ... bit1=burst read (iot_get_sでアドレス加算しながら連続リード)
;================================================
set_flag:
	cp	valtyp_int
	ret	nz

	inc	hl
	inc	hl
	ld	a, (hl)
	ld	(mode_flag), a
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

	ld	a, no_reg
	ld	(i2c_i_reg), a	;最終アクセスレジスタクリア
	
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
	jr	z, iot_put_s_1

	ld	e, a	;長さ保存
	ld	a, (hl)
	ld	(i2c_i_reg), a	;最終アクセスレジスタに保存
	ld	a, e	;長さ復帰

iot_put_s_1:
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

	ld	e, a	;長さ保存
	ld	a, (mode_flag)
	and	mode_flag_burst_read
	jr	z, iot_get_s_burst

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

	;渡されたバッファ（文字列）長さの分だけ
	;レジスタアドレスを加算しながら連続で読み込む
iot_get_s_burst:
	ld	b, e	;長さ復帰
	ld	c, 0	;読み込んだサイズ合計

iot_get_s_burst_loop:
	ld	a, b
	push	bc
	call	iotlib_get_buf
	pop	bc

	ld	e, a	;e=読み込んだ長さ
	add	c
	ld	c, a	;読み込んだサイズ合計
	ld	a, b	;残りの長さ OLD
	sub	e	;残りの長さ-今回読み込んだ長さ
	ld	b, a	;残りの長さ NEW

	ld	a, c	;読み込んだサイズ合計(endへ飛ぶ準備)
	jr	z, iot_get_s_end
	jr	c, iot_get_s_end

	; レジスタアドレス加算
	push	bc
	push	hl
	ld	hl, i2c_i_reg
	inc	(hl)
	ld	a, 1
	ld	hl, i2c_i_reg
	call	iotlib_put_buf		;新しいレジスタを指定
	pop	hl
	pop	bc
	jr	iot_get_s_burst_loop	;ループ

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
; out:	hl ... データアドレス
;	a  ... 長さ
;	b  ... 文字列バッファに格納可能な最大の長さ
;	c  ... vartyp
;	z  ... 長さが0ならz=1
;	cy ... 1 = error ... hl, a, cは無効
; use:	af, c, de, hl
;================================================
get_usr_string:
	ld	c, a	;a=valtype
	ld	a, (mode_flag)
	and	mode_flag_xbasic
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

;;================================================
;; device/i2c_iチェック
;; in:	hl :string
;; out:  z  :0=OK
;;================================================
;is_device_ic2_i:
;	push	hl
;	push	de
;
;	ld	de, str_device_ic2_i
;
;is_device_ic2_i_loop:
;	ld	a, (de)
;	inc	de
;	or	a
;	jr	z, is_device_ic2_i_end	; match all
;	
;	cp	(hl)
;	inc	hl
;	jr	z, is_device_ic2_i_loop	; not match
;
;is_device_ic2_i_end:
;	pop	de
;	pop	hl
;	ret
;str_device_ic2_i:
;	db	"device/i2c_i"
;	db	0

 if include_datetime ;---------------------------
;================================================
; クロックICを読み込む
; in:	A$="GET TIME":A=USR(VARPTR(A$)) または
;	A$="GET DATE":A=USR(VARPTR(A$))
; out:  "hh:mm:ss" または
;	"yy/mm/dd" を返す
;================================================
read_datetime:
	cp	valtyp_int
	ret	nz	;整数以外は無視

	push	hl
	call	get_usr_string
	; a = length
	; hl = address
	push	af

	cp	8
	jr	c, read_clock_end	;8文字未満は無視
	
	push	hl
	ld	de, str_gettime
	call	cmpstr
	pop	hl
	jr	z, read_gettime
	
	push	hl
	ld	de, str_getdate
	call	cmpstr
	pop	hl
	jr	z, read_getdate

read_clock_end:
	pop	af
	pop	ix
	ld	(ix+2), a
	ld	(ix+3), a
	ret

;------------------------------------------------
REDCLK:	equ	01F5H	;(SUB-ROM) CLOCK-ICへデータを書き込みます
			;in:	c: bit5-4:block, bit3-0:reg_id
			;out:	a: データ(下位4bitのみ有効）
			;use:	af
;WRTCLK:	equ	01F9H	;(SUB-ROM) クロック・データを書き込む
;			;in:	A に書き込むデータ。C にクロック RAM アドレス
;			;out:	なし
;			;use:	F
SUBROM:	equ	015CH	;SUB-ROM をインタースロット・コール
			;in:	IX をスタックに積んでからIX に呼び出すアドレスを入れてjp
			;out:	呼び出すルーチンによる
			;desc:	pop ixしてretするので
			;	read_clockic:
			;		push	ix
			;		ld	ix, REDCLK
			;		jp	SUBROM
			;       の様にして call read_clockic で呼び出す
			;use:	裏レジスタと IY はリザーブされる
EXTROM:	equ	015FH	;SUB-ROM をインタースロット・コール
			;in	IX に呼び出すアドレス
			;out	呼び出すルーチンによる
			;use:	裏レジスタと IY はリザーブされる
;------------------------------------------------
;in:	hl : データ格納先
;use:	裏レジスタはリザーブされる
;------------------------------------------------
read_gettime:
	ld	bc, 5
	call	read_clockic_dec	;5:時(10の位)
	call	read_clockic_dec	;4:時( 1の位)
	ld	(hl), ':'
	inc	hl
	call	read_clockic_dec	;3:分(10の位)
	call	read_clockic_dec	;2:分( 1の位)
	ld	(hl), ':'
	inc	hl
	call	read_clockic_dec	;1:秒(10の位)
	call	read_clockic_dec	;0:秒( 1の位)
	jr	read_clock_end

;------------------------------------------------
read_getdate:
	ld	bc, 12 + 8 * 100H	;年は80を足す
	call	read_clockic_dec	;12:年(10の位)
	ld	b, 0
	call	read_clockic_dec	;11:年( 1の位)
	ld	(hl), '/'
	inc	hl
	call	read_clockic_dec	;10:月(10の位)
	call	read_clockic_dec	; 9:月( 1の位)
	ld	(hl), '/'
	inc	hl
	call	read_clockic_dec	; 8:日(10の位)
	call	read_clockic_dec	; 7:日( 1の位)
	jr	read_clock_end

;------------------------------------------------
;in:	hl = address
;	c = clock-ic reg id
;	b = value offset
;out:	(hl) = '0'+click-ic num(0-9)
;	hl = hl + 1
;	c = c - 1
;use:	hl,cは継続する
;------------------------------------------------
read_clockic_dec:
	push	bc
	push	hl
	ld	ix, REDCLK
	call	EXTROM
	pop	hl
	pop	bc

	add	b
	daa
	and	15

	add	'0'

	ld	(hl), a
	inc	hl
	dec	c
	ret

;================================================
; 文字列比較
cmpstr_ignoreLetterCase:	equ	1
			; 1 = 大文字小文字区別なし
; in:	hl:str address
;	de: zero ended string
; out:	z=一致/nz=不一致
; use: af,hl,de,c
;================================================
cmpstr:
cmpstr_l:
	ld	a, (de)
	inc	de
	or	a
	ret	z

	cp	(hl)

 if cmpstr_ignoreLetterCase ;--------------------
	jr	z, cmpstr_j	;完全一致

	ld	c, #20		;大文字→小文字
	cp	'A'
	jr	c, cmpstr_e	;大文字ではない
	cp	'Z'+1
	jr	c, cmpstr_cp2	;大文字である

	ld	c, -#20		;小文字→大文字
	cp	'a'
	jr	c, cmpstr_e	;大文字でもない
	cp	'z'+1
	jr	nc, cmpstr_e	;小文字でもない

cmpstr_cp2:
	add	c		;小→大/大→小文字変換
	cp	(hl)
 endif ; cmpstr_ignoreLetterCase ----------------

cmpstr_j:
	inc	hl
	jr	z, cmpstr_l
cmpstr_e:
 if cmpstr_ignoreLetterCase ;--------------------
	or	255	; non-zero
 endif ; cmpstr_ignoreLetterCase ----------------
	ret

str_gettime:
	db	"GET TIME"
	db	0
str_getdate:
	db	"GET DATE"
	db	0

 endif ;include_datetime ;-----------------------

end_adr:

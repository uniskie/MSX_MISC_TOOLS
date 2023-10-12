USE_PSG_BIOS:	equ	1	;ジョイポートアクセスにI/Oポート直接アクセスを使用しない。互換性のため
USE_BINHEADER:	equ	1	;テスト用

 IF USE_PSG_BIOS

WRTPSG:		equ	$0093	;in{ a=psg#n, e=dat }
RDPSG:		equ	$0096	;in{ a=psg#n }, ret{ a=dat }

 ENDIF

start_adr:	equ	$d000

 IF USE_BINHEADER
	db	$fe
	dw	start_adr
	dw	end_adr-1
	dw	start_adr

	org	start_adr

;================================================
; ジョイスティック情報取得
; a = usr(ジョイスティック番号) ※ INT型を使う事
; データのアドレスを返す
;	ジョイポートの状態
;	+0: press   ... 現在の押下状態
;	+1: trig    ... 今回初めて押したもの
;	+2: release ... 今回初めて離したもの
;	+3: repeat  ... 押しっぱなしリピート機能付きのtrig
;	+4: リピート開始ウェイト
;	+5: リピート連続ウェイト
;	bit 0: U 上↑
;	bit 1: D 下↓
;	bit 2: L 左←
;	bit 3: R 右→
;	bit 4: A Aボタン
;	bit 5: B Bボタン
;================================================
usr_func:
	cp	2	;int?
	ret	nz

	push	hl
	pop	ix
	ld	a,(ix+2)

	call	proc_joy
	ld	(ix+2),l
	ld	(ix+3),h
	ret
 ENDIF

;================================================
; ジョイポート入力
; in:  a=ジョイポート0 or 1
; out: a=ビットが1ならそれぞれON
;	bit 0: U 上↑
;	bit 1: D 下↓
;	bit 2: L 左←
;	bit 3: R 右→
;	bit 4: A Aボタン
;	bit 5: B Bボタン
;	bit 6: 常に0にマスク (マスクしない場合の値は 1=JIS配列/0=50音配列)
;	bit 7: 常に0にマスク (マスクしない場合の値は カセットテープ入力)
; use: af, bc, e, ei
;================================================
joygetd:			;a=ジョイポート番号
	ld	b, $af		;ジョイポート0の8番=bit4、PSG#14に接続するジョイポート選択=bit6
	ld	c, $0		;PSG#14に接続するジョイポートが0 = bit6 = 0
	or	a
	jr	z, joygetd_sel
	ld	b, $9f		;ジョイポート1の8番=bit5、PSG#14に接続するジョイポート選択=bit6
	ld	c, $40		;PSG#14に接続するジョイポートが1 = bit6 = 1
joygetd_sel:
 IF USE_PSG_BIOS
	ld	a, 15
	call	RDPSG
	and	b		;ジョイポートaの8番へ0を出力。ジョイポート選択をクリア他は維持
	or	c		;ジョイポート選択
	ld	e, a
	ld	a, 15
	call	WRTPSG
	ld	a, 14
	call	RDPSG		;CKBARLDU
	cpl			;0ならONなのでビット反転
	and	$3f		;ジョイスティック情報だけ返す
	ret
 ELSE
	ld	a, 15
	di
	out	($A0), a
	in	a, ($A2)
	and	b		;ジョイポートaの8番へ0を出力。ジョイポート選択をクリア他は維持
	or	c		;ジョイポート選択
	out	($A1), a
	ld	a, 14
	out	($A0), a
	ei			;割り込みを解除：しないで返すのもアリ
	in	a, ($A2)	;CKBARLDU
	cpl			;0ならONなのでビット反転
	and	$3f		;ジョイスティック情報だけ返す
	ret
 ENDIF

;================================================
; ジョイスティック処理
; in:	a=ジョイポート
; out: hl=w_joy0またはw_joy1のアドレス
;	ジョイポートの状態
;	+0: press   ... 現在の押下状態
;	+1: trig    ... 今回初めて押したもの
;	+2: release ... 今回初めて離したもの
;	+3: repeat  ... 押しっぱなしリピート機能付きのtrig
;	bit 0: U 上↑
;	bit 1: D 下↓
;	bit 2: L 左←
;	bit 3: R 右→
;	bit 4: A Aボタン
;	bit 5: B Bボタン
; use: hl, ei
;================================================
proc_joy:
	push	af
	push	bc
	push	de
	ld	hl, w_joy0
	or	a
	jr	nz, proc_joy_s
	ld	hl, w_joy1

proc_joy_s:
	push	hl	;格納先ワークエリア先頭を保存

	call	joygetd
	ld	b, a
	ld	c, (hl)	;前回押されていたもの
	ld	(hl), a	;press 現在押されているもの
	inc	hl
	xor	c	;a = 前回との差分
	ld	e, a	;e = 前回との差分
	and	b	;今回のONでビットマスク=trig
	ld	(hl), a	;trig 今回ONに変化したもの
	ld	d, a	;d = trig
	inc	hl
	ld	a, e	;a = 前回との差分
	and	c	;前回のONでビットマスク＝release
	ld	(hl), a	;release 今回OFFに変化したもの
	inc	hl
	ld	a, b	;今回
	or	a
	jr	z,proc_joy_repeat_reset	;押されていない
	xor	c	;前回との差分
	jr	z, proc_joy_repeat	;変化が無い

proc_joy_repeat_reset:
	;	変化があったのでリピートカウンターリセット
	ld	(hl), d	;d=trig
	inc	hl
	ld	a, (def_repeat_start)
	ld	(hl), a	;リピート開始ウェイトを初期値に設定
	inc	hl
	ld	a, (def_repeat_interval)
	ld	(hl), a;リピート連続ウェイトを初期値に設定

pcor_joy_end:
	pop	hl	;保存したものを復帰 使用したワークエリアのアドレス
	pop	de
	pop	bc
	pop	af
	ret		;終了

proc_joy_repeat:
	;前回と状態が同じなのでリピート処理
	inc	hl
	ld	a, (hl)	;リピート開始ウェイト
	or	a
	jr	nz, proc_joy_repeat_start
	inc	hl
	ld	a, (hl)	;リピート連続ウェイト
	or	a
	jr	nz, proc_joy_repeat_interval

;	リピート
	ld	a, (def_repeat_interval)
	ld	(hl), a	;リピート連続ウェイトを初期値に設定
	dec	hl
	dec	hl
	ld	(hl), b	;リピート押下状態＝現在の押下状態
	jr	pcor_joy_end

proc_joy_repeat_interval:
	;連続入力ウェイト
	dec	a
	ld	(hl), a	;リピート連続ウェイト-1
	dec	hl
	dec	hl
	xor	a
	ld	(hl), a	;リピート押下状態＝なし
	jr	pcor_joy_end

proc_joy_repeat_start:
;	リピート開始待ち
	dec	a
	ld	(hl), a	;リピート開始待ち-1
	dec	hl
	xor	a
	ld	(hl), a	;リピート押下状態＝なし
	jr	pcor_joy_end


;data segment
def_repeat_start:	db	15
def_repeat_interval:	db	1
w_joy0:
w_joy0_press:	db	0
w_joy0_trig:	db	0
w_joy0_release:	db	0
w_joy0_repeat:	db	0
w_joy0_repeat_start:	db	0
w_joy0_repeat_interval:	db	0
w_joy1:
w_joy1_press:	db	0
w_joy1_trig:	db	0
w_joy1_release:	db	0
w_joy1_repeat:	db	0
w_joy1_repeat_start:	db	0
w_joy1_repeat_interval:	db	0
;end dseg

 IF USE_BINHEADER
end_adr:
 ENDIF

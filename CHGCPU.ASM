;-*- tab-width: 8 -*-
CHGCPU:	equ	0180h
GETCPU:	equ	0183h

	org	0c000h

;================================
;  A=USR(n)
;  in:	n=0 : Z80
;	n=1 : R800(ROM)
;	n=2 : R(00(RAM) ※起動時にR800出ない場合は暴走
;	n=255 : 問い合わせ
;  ret: 呼び出し前のCPUモード
;================================
usr_chgcpu:
	cp	2	;整数でなかったら終了
	ret	nz

; --> 正式な方法 : hl=(hl+2)
; DAC+2から取得する手抜きもアリ
; LD HL,(0F7F8H)
; <--
	push	hl
	pop	ix		;(IX+2) = INT VALUE

;	GETCPUとCHGCPUが使えるか
	ld	a,(GETCPU)
	or	a
	jr	z,end_chgcpu

	call	GETCPU

	push	af		;現在のCPUモード
	ld	a,(ix+2)	;get value(low)
	cp	4		;範囲外は現在のモード取得のみ
	jr	nc,end_chgcpu0

	or	80h		;LEDを変化させる
	call	CHGCPU		;CPUモード変更

end_chgcpu0:
	pop	af

end_chgcpu:
	ld	(ix+2),a
	ld	(ix+3),0
	ret


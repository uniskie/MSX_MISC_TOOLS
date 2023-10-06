;-*- tab-width: 8 -*-
BDOS:	equ	0F37DH	;BDOS function call
_DOSVER: equ	6Fh	;MSX-DOSバージョン取得

	fname	"CHKDOS.BIN"

;======== Bsave Header ==========
	db	0FEh
	dw	start_of_program
	dw	end_of_program-1
	dw	start_of_program
;================================

	org	0C000h

start_of_program:
;================================
; MSX-DOSバージョンを取得する
;  A=USR(0)
;  ret:	n=0 : MSX-DOSではない
;	n=1 : MSX-DOS1
;	n=2 : MSX-DOS2
;================================
usr_chkdos:
	cp	2	;整数でなかったら終了
	ret	nz

; --> 正式な方法 : hl=(hl+2)
; DAC+2から取得する手抜きもアリ
; LD HL,(0F7F8H)
; <--
	push	hl

	ld	c,_DOSVER
	call	BDOS

	or	a
	ld	a,0
	jr	nz,end_chkdos

	ld	a,b

end_chkdos:
	pop	ix
	ld	(ix+2),a
	ld	(ix+3),0
	ret

end_of_program:

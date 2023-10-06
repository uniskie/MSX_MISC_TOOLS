;-*- tab-width: 8 -*-
BIGFIL: equ 016Bh ;VRAMをFILL HL=アドレス, BC=長さ, A=データ
TXTCOL: equ 0F3B5H ;TEX2 カラーテーブル(MSX2、MSX2+のみ)

	fname	"CLRBLK.BIN"

;======== Bsave Header ==========
	db	0FEh
	dw	start_of_program
	dw	end_of_program-1
	dw	start_of_program
;================================

	org	0C000h

start_of_program:
;================================
; TEXT2モードのブリンクテーブルをクリア
;  A=USR(0)
;================================
usr_clrblk:
	ld	hl,(TXTCOL)
	ld	bc,80*24/8
	xor	a
	call	BIGFIL
	ret

end_of_program:

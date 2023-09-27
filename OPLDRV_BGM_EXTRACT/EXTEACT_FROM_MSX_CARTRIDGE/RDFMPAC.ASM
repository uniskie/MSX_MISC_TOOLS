;-*- tab-width: 8 -*-
RDSLT:	equ	000CH
WRSLT:	equ	0014H
CALSLT:	equ	001CH
ENASLT:	equ	0024H
CALLF:	equ	0030H

EXPTBL:	equ 0FCC1H	;MAIN ROM SLOT

RAMAD0:	equ	0F341H	;RAM SLOT page 0
RAMAD1:	equ	0F342H	;RAM SLOT page 1
RAMAD2:	equ	0F343H	;RAM SLOT page 2
RAMAD3:	equ	0F344H	;RAM SLOT page 3

	fname	"RDFMPAC.BIN"
;--> bin file header -->
	db	$fe	;*binhead*
	dw	orgadr	;*binhead*
	dw	endfl-1	;*binhead*
	dw	orgadr	;*binhead*
;<-- bin file header <--

orgadr:	equ	$c000
	org	orgadr

;--- jump table for usr()
	jp	rom2vram
;---
fmpac_slot:	db	1

;■ FMPACのバンク選択
;
;レジスタ: 7FF7h
;http://bifi.msxnet.org/msxnet/utils/saverom
;SAVEROM FMPAC.ROM?
;Select Type: Custom
;Switch Address: 7FF7
;Save Address: 4000
;Block Size: 4000
;First Block: 0
;Last Block: 3
;
;■ FMPACの曲データ
;
;RAM 0CBF4H(環境による)へ転送して再生される
;
;(ROMイメージ先頭から)
;$8080	曲データアドレスリスト
;	(2byte*5)
;	$408A	1曲目
;	$478C	2曲目
;	$590E	3曲目
;	$5B90	4曲目
;	$6612	5曲目
;
;$808A	1曲目 サイズ $0700 ($808A),データ($808C-$878B)
;$878C	2曲目 サイズ $1180 ($878C),データ($878E-$990D)
;$990E	3曲目 サイズ $0280 ($990E),データ($9910-$9B8F)
;$9B90	4曲目 サイズ $0A80 ($9B90),データ($9B92-$A611)
;$A612	5曲目 サイズ $0580 ($A612),データ($A614-$AB93)

fmpac_bank_reg1:	equ	7FF7H

fmpac_bgm_bank:		equ	2

;BGMデータの範囲は $9073- $BF5D
fmpac_bgm_start:	equ	$408A
fmpac_bgm_size:		equ	$6B93 + 1 - fmpac_bgm_start

use_page:		equ	$4000
vram_dest:		equ	fmpac_bgm_start; - use_page

;================================
;  rom to vram
;	A=USR(0)
;================================
	ds	orgadr + $100 - $
rom2vram:
	call	getint
	ret	nz
	push	ix
	di
; change sp
	ld	(sp_sav),sp
	ld	sp,endfl
; slot page1 = fmpac
	ld	a,(fmpac_slot)
	ld	hl,$4000
	call	ENASLT
; bank change
	ld	a,fmpac_bgm_bank
	ld	(fmpac_bank_reg1),a
; write to vram
	ld	de,vram_dest
	call 	VSETWRT
	dec	c

	ld	hl,fmpac_bgm_start
	ld	de,fmpac_bgm_size
	ld	b,e
	inc	d
wvram_l:
	outi
	jr	nz,wvram_l
	dec	d
	jr	nz,wvram_l
; slot page 1 = main rom
	ld	a,(EXPTBL)
	ld	hl,$4000
	call	ENASLT
; restore sp
	ld	sp,(sp_sav)
;
	ei
	pop	ix
	ld	hl,vram_dest
	ld	(ix+2),l
	ld	(ix+3),h
	ret

;================================
	include	"USR_FUNC.ASM"
	include	"VRAM.ASM"
;================================

sp_sav:	dw	0
sp_space:	ds	$20

endfl:

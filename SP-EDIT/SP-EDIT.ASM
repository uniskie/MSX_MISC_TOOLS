;-*- tab-width: 8 -*-

DAC:		EQU	0F7F6H	;16 byte 演算の対象となる値を設定するエリア
INTDAC:		EQU	DAC+2	;2 byte USR引数のINT時の値を格納
LDIRVM:		EQU	005CH	;LDIR RAM to VRAM HL,DE,BC
NRDVRM:		EQU	0174H	;READ VRAM A=[HL]
NWRVRM:		EQU	0177H	;WRITE VRAM [HL]=A
BIGFIL:		EQU	016BH	;VRAMをFILL HL=アドレス, BC=長さ, A=データ

PATNAM:		EQU	1800H	;SC1 PATNAM TABLE

DOTV_X1:	EQU	1	;ドット拡大表示窓位置1(X)
DOTV_X2:	EQU	9	;ドット拡大表示窓位置2(X)
DOTV_Y:		EQU	2	;ドット拡大表示窓位置(Y)
BITCHR:		EQU	9FH	;"そ"

SELSPR_X:	EQU	1	;スプライト選択窓位置(X)
SELSPR_Y:	EQU	20	;スプライト選択窓位置(Y)
SELSPR_CUR:	EQU	0	;選択中背景 "@"
SELSPR_BLK:	EQU	' '	;非選択

	ORG	0C000H

	JP	bit2char_16x16
	JP	draw_select_bg

; スプライトのビットパターン16X16を読みだして
; 1ビットずつ1文字文字表示する
;
bit2char_16x16:
	LD	HL,(INTDAC)	;PATTERN ADDRESS
	LD	DE,PATNAM + DOTV_Y*32 + DOTV_X1	;LOCATE 1,2
	LD	B,20H
.LOOP0:
	PUSH	BC
	CALL	NRDVRM
	INC	HL
	LD	C,A
	LD	B,8
	PUSH	HL
	LD	HL,PATWORK
.LOOP1:
	XOR	A
	RLC	C
	ADC	A,BITCHR
	LD	(HL),A
	INC	HL
	DJNZ	.LOOP1

	PUSH	DE
	LD	HL,PATWORK
	LD	BC,8
	CALL	LDIRVM

	POP	DE
	POP	HL

	LD	A,E
	ADD	A,32	;次の行へ
	LD	E,A
	JR	NC,.NC1
	INC	D
.NC1:
	POP	BC
	LD	A,B
	CP	11H
	JR	NZ,.NZ1
	LD	DE,PATNAM + DOTV_Y*32 + DOTV_X2	;LOCATE 9,2
.NZ1:
	DJNZ	.LOOP0

	RET

; スプライト選択欄の選択状態表示
; A=USR(POS) ... POS= 0 ~ 3
draw_select_bg:

	; RAMに1行作成
	LD	HL,PATWORK
	LD	DE,PATWORK+1
	LD	(HL),SELSPR_BLK
	LD	BC,4*4-1
	LDIR

	LD	HL,PATWORK
	LD	A,(INTDAC)
	RLCA
	RLCA
	ADD	L
	LD	L,A
	JR	NC,.NC_0
	INC	H
.NC_0
	LD	A,SELSPR_CUR
	LD	(HL),A
	INC	HL
	LD	(HL),A
	INC	HL
	LD	(HL),A
	INC	HL
	LD	(HL),A
	INC	HL

	;VRAMに4行表示
	LD	A,4	; Y COUNT
	LD	DE,PATNAM + SELSPR_Y*32 + SELSPR_X	;LOCATE 1,20
.LOOP_2:
	PUSH	AF
	PUSH	DE
	LD	HL,PATWORK
	LD	BC,4*4
	CALL	LDIRVM
	POP	DE
	LD	A,E
	ADD	32	;次の行
	LD	E,A
	JR	NC,.NC_1
	INC	D
.NC_1:
	POP	AF
	DEC	A
	JR	NZ,.LOOP_2
	
	RET

PATWORK: DS	8

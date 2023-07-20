;-- KANJI EDITOR "FIELD WORK" --

;  PUT KANJI with FONT

;    _SAVE("FW-KJ.ASF"

;  need (LFCHCK)  (external) rutine :LINE FEED CHECK

KJ_IO1:	EQU		0D8H
KJ_IO2:	EQU		0DAH

CL_OO_:	EQU		0FFH
CL_OX_:	EQU		0F0H
CL_XO_:	EQU		00FH
CL_XX_:	EQU		000H

ZENKA_X:	EQU		2
HANKA_X:	EQU		1

;ENTRY:
;  KANJI_C   COLOR CHANGE
;             A:COLOR
;
;  KANJI_RM  DRAW FONT (ROM CODE)
;             HL:CODE
;
;  KANJI_CK  SHIFT-JIS CHECK
;             DE:STRINGS ADDRESS
;
;  KANJI_F   SHIFT-JIS CHECK
;             A:CHR CODE
;
;  KANJI_S   DRAW FONT (SHIFT-JIS)
;             DE:STRINGS ADDRESS
;
;   KANJI_PC DRAW FONT (KANJI CODE)
;             HL:KANJI-CODE
;             (PR_AXS):DRAW AXIS
;
;   FONT_CL  DRAW COLOR
;             (KJCL_F):COLOR WRITE =0 / NO WRITE =1
;             (FONTCOL):COLOR
;             HL:VRAM ADDRESS
;             E:LENGTH(8/16)
;    FONT_C  DRAW COLOR
;             D:COLOR
;             HL:VRAM ADDRESS
;             E:LENGTH(8/16)
;    FONT_CU DRAW COLOR (UNDER)
;             D:COLOR
;             HL:VRAM ADDRESS
;             E:LENGTH(8/16)

;= VDP resister buffer for kanji
PR_AXS:	DB		0		;X
		DB		0		;Y
		DB		1		;NX

SCRL_L:	DB		0		;SCROL HEAD Y AXIS
SCRL_F:	DB		0		; 0:SCROLL ON/OTHE:OFF

KJCL_F:	DB		0		; COLOR 0:WRITE / 1:NO WRITE

;= WORK AREA
FONTCOL:	EQU		FONT_CL+1	;FONT COLOR

;//
;  CHANGE COLOR 
;                           //
; A:COLOR
;  USE : AF
KANJI_C:
		LD		(FONTCOL),A
		RET
;//
;   PUT KANJI (with ROM-CODE)
;                                 //
;// Check X Size //
;( HL:KANJI ROM-CODE)
KANJI_RM:
		LD		A,H
		OR		A
		JP		NZ,RM60H
		LD		A,L		;ÊÝ¶¸(000H-060H)
		CP		60H
		JP		C,RMHAN
		JP		RMZEN
RM60H:	CP		3		;ÊÝ¶¸(0A0H-0DFH)
		JP		NZ,RMZEN
		LD		A,L
		CP		60H
		JP		C,RMZEN
		CP		0C0H
		JP		C,RMHAN
RMZEN:	LD		A,ZENKA_X
		JP		KANJI_PC
RMHAN:	LD		A,HANKA_X
		JP		KANJI_PC

;// >> CHECK KANJI
;  KANJI (with S-JIS) CHECK
;                               //
; (DE:ADDRESS)
; USE : AF

; RET : Cy: 1=ZENKAKU / 0=HANKAKU

KANJI_CK:
		LD		A,(DE)		;S-JIS(H)
KANJI_F:
		CP		20H
		JR		C,CK_ZEN
ZENKA_CK:
		CP		7FH
		JR		C,CK_HANK
		CP		0A0H
		JR		C,CK_ZEN
		CP		0E0H
		JR		NC,CK_ZEN
CK_HANK:
		OR		A
		RET
CK_ZEN:	OR		A
		SCF
		RET

;// >> KANJI PUT
;  KANJI (with S-JIS) PUT
;                               //
; (DE:ADDRESS) SHIFT-JI >> JIS >>KANJI CODE
; USE : HL,AF,DE,BC (ALL)

; CHECK CHRARACTER

KANJI_S:
		LD		A,(DE)		;S-JIS(H)
		INC		DE
; (ÊÝ¶¸ CHECK)
		LD		H,0

		CP		80H
		JP		C,HANK		;ÊÝ¶¸ ASC(0)-(127)
		CP		0A0H
		JP		C,SJH_1
		CP		0E0H
		JP		NC,SJH_2
		LD		H,3		;ÊÝ¶¸ ASC(A0H)-(DFH)
		SUB		20H
HANK:	SUB		20H
		LD		L,A

		CP		TAB-20H
		LD		A,HANKA_X
		JP		NZ,KANJI_PC
		LD		HL,03A3H
		JP		KANJI_PC

; (¾ÞÝ¶¸ CHECK)
SJH_1:	ADD		A,0B1H-71H
SJH_2:	SUB		0B1H
		ADD		A,A
		SUB		20H-1
		LD		L,A		; L:JIS(H)-32 (A*2+1-32)

SJL_:	LD		A,(DE)
		INC		DE
		CP		7FH+1		;(7FH:DEL)
		JP		C,SJL_1
		DEC		A
SJL_1:	INC		L
		CP		9EH
		JP		NC,SJL_2
		DEC		L
		ADD		A,7DH-1FH
SJL_2:	SUB		7DH+20H

KJCODE:	PUSH	DE
		LD		C,A
		LD		B,0
		LD		A,L
		RRCA
		RRCA
		RRCA
		LD		H,A
		AND		0E0H
		LD		L,A
		LD		A,H
		AND		1FH
		LD		H,A		;HL=L*32
		LD		D,H
		LD		E,L
		ADD		HL,HL		;HL=L*64
		ADD		HL,DE		;HL=L*(64+32) = L*96
		ADD		HL,BC		; HL= (JIS_H-32)*96 + (JIS_L-32)
		POP		DE

		LD		A,H
		CP		6		;H<=>16*96
		LD		A,ZENKA_X
		JP		C,KANJI_PC
		DEC		H
		DEC		H		;HL=HL-512

;       JP   KANJI_PC

;// Trancefer FONT to RAM //
;( HL:KANJI-CODE/PR_AXS:SET )
;( Out put KANJI CODE )
KANJI_PC:
		CALL	LFCHCK
		LD		A,H		;KANJI-ROM max
		CP		10H
		LD		C,KJ_IO1
		JP		C,DAI1_K
		LD		C,KJ_IO2
DAI1_K:	OUT		(C),L		;Write KANJI CODE Low6bit
		LD		B,L
		RL		B
		RLA
		RL		B
		RLA

		INC		C
		OUT		(C),A		;Write KANJI CODE Hi 6bit
		LD		A,C
		EXX
		LD		C,A
;( Convert Font to bit-map )
		LD		HL,(PR_AXS)
		LD		A,(SCRL_F)
		OR		A
		JR		NZ,KJ_PC_
		LD		A,(SCRL_L)
		ADD		A,H
		AND		31
		LD		H,A
KJ_PC_:	LD		A,L
		RLCA
		RLCA
		RLCA
		LD		L,A
		LD		A,(PR_AXS+2)
		CP		HANKA_X
		JP		Z,FONTHK
		CALL	VRAM1
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		CALL	VRAM2
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		LD		E,16
		JP		FONTCL

FONTHK:	CALL	VRAM1

		IN		A,(C)
		IN		A,(C)
		IN		A,(C)
		IN		A,(C)
		IN		A,(C)
		IN		A,(C)
		IN		A,(C)
		IN		A,(C)

		IN		A,(C)
		IN		A,(C)

		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
; IN A,(C)
; OUT (98H),A
; IN A,(C)
; OUT (98H),A
		IN		A,(C)
		IN		A,(C)
		IN		A,(C)
		IN		A,(C)
		IN		A,(C)
		IN		A,(C)
		IN		A,(C)
		IN		A,(C)

		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A

		CALL	VRAM2
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		OUT		(98H),A
		IN		A,(C)
		XOR		A		;
		OUT		(98H),A
		IN		A,(C)
		XOR		A		;
		OUT		(98H),A
		LD		E,8
		JP		FONTCL

;( Set VRAM ADRESS )

VRAM1:	LD		A,L
		DI
		OUT		(99H),A
		LD		A,H
		OR		40H
		OUT		(99H),A
		EI
		RET

VRAM2:	LD		A,L
		DI
		OUT		(99H),A
		LD		A,H
		INC		A
		OR		40H
		OUT		(99H),A
		EI
		RET

FONTCL:	LD		A,(KJCL_F)
		OR		A
		JR		NZ,FONT_CE
FONT_CL:
		LD		D,0F1H		;DUMMY
FONT_C:	LD		A,L
		DI
		OUT		(99H),A
		LD		A,H
		OR		60H
		OUT		(99H),A
		EI
		LD		B,E
		LD		A,D
_COLF0:	OUT		(98H),A
		DJNZ	_COLF0
FONT_CU:
		LD		A,L
		DI
		OUT		(99H),A
		LD		A,H
		INC		A
		OR		60H
		OUT		(99H),A
		EI
		LD		B,E
		LD		A,D
		CP		C_MJOF
		JR		Z,_COLF1_
		CP		C_KJON
		JR		Z,_COLF1_
		CP		C_EROR
		JR		Z,_COLF1_
		CP		C_MENU
		JP		NZ,_COLF1
		LD		A,C_MEND+10H
_COLF1_:
		SUB		10H
_COLF1:	OUT		(98H),A
		DJNZ	_COLF1
FONT_CE:
		EXX
		RET

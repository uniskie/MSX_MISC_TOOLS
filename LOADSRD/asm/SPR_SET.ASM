;-*- tab-width: 8 -*-
;================================
; INCLUDE FILE for LOADSRD
;================================
; for SPRITE mode 2
; for 16x16 * 2 combo use.
; not for 8X8
; for SCREEN 5/6/7/8/9/10/11
; FLICKER is not support SCREEN 4.(not enough space for double buffer)
;USR():
;	SPR_SET - write SPRITE for 16x16
;	SPC_SET - set SPRITE PAT COLOR TABLE for 16x16
;	SPR_INT - set / reset H.TIMI for SPRITE
;================================
;---- WRITE SPRITE from 16BIT(INT) ARRAY ----
;SPR_ATU {
;	s16_t	Y*2;
;	s16_t	X*2;
;	s16_t	PATTERN_NO;
;	s16_t	FLAG;
;} spr_attribute_list[32];
SFG_AWAIT:	EQU	0FH	;FLAG bit 3 -0	: auto anim wait (0-15)
SFG_ATYPE:	EQU	10H	;FLAG bit 4	: 0=2pattern / 1=4pattern ANIM
SFG_ACNTR:	EQU	0FH	;FLAG bit 11-8	: wait counter (0-15)
SFG_APAT:	EQU	30H	;FLAG bit 13-12 : pat offset (0-3)
SFG_PBIT:	EQU	10H	;                 lowest bit of pat offset
SFG_SKIP:	EQU	80H	;FLAG bit 15	: SKIP(ERASE)
;SPR_COL {
;	u8	COLOR;	// EC(1).CC(1).IC(1).0(1).COLOR(4)
;} spr_color_list[64]

;VDPIOR:	EQU	0006H	;VDP I/O port m (READ)
;VDPIOW:	EQU	0007H	;VDP I/O port n (WRITE)
;ATRBAS:	EQU 0F928H

CCLSIZE:	EQU	400H	;(16*64) for 16x16 SPRITE
;CCLSIZE:	EQU	800H	;(8*256) for 8x8 SPRITE

;--- BIOS / SYSTEM WORK
H_TIMI:		EQU	0FD9FH	;VSYNC INTERRUPT

;--- CONSTANTS ---

SPRU_OY:	EQU	0	; SPRITE ATTRIBUTE USR ARRAY offset : Y
SPRU_OX:	EQU	2	; SPRITE ATTRIBUTE USR ARRAY offset : X
SPRU_OP:	EQU	4	; SPRITE ATTRIBUTE USR ARRAY offset : PAT
SPRU_OF:	EQU	6	; SPRITE ATTRIBUTE USR ARRAY offset : FLAG

SPRW_OY:	EQU	0	; SPRITE ATTRIBUTE WORK offset : Y
SPRW_OX:	EQU	1	; SPRITE ATTRIBUTE WORK offset : X
SPRW_OP:	EQU	2	; SPRITE ATTRIBUTE WORK offset : PAT
SPRW_OF:	EQU	3	; SPRITE ATTRIBUTE WORK offset : FLAG

BIT_ND:		EQU	10H	; NO DISPLAY
BIT_EC:		EQU	80H	; EC bit (LEFT SHIFT 32 dot)
BIT_IC:		EQU	10H	; NO COLLISION
;SPW_SKIP:	EQU	0FFH	; SKIP WRITE

SPRATS:		EQU	080H	; SPRITE ATTRIBUTE TABLE BUFFER SIZE 4*32
SPRCLS:		EQU	200H	; SPRITE COLOR TABLE SIZE 16*32
SPRMAX:		EQU	32	; SPRITE ENTRY COUNT
SPCOFS:		EQU	512	; (ATRBAS)-SPCOFS = SPRITE COLOR TABLE

VRMSPGX:	EQU	200H	; SPRITE Color & Atrtribute page address diff.

SSYNCMD0:	EQU	0	; NO USE VSYNC, TRUE IMMEDIATE MODE
SSYNCMD1:	EQU	1	; VSYNC + IMMEDIATE DRAW MODE
SSYNCMD2:	EQU	2	; VSYNC + LATE DRAW MODE

;================================
;--- SET SPRITE COLOR DATA ---
;================================
; U=USR(ADR)
;	ADR = SPRITE COLOR / 16*64 bytes(for 16X16)
SPC_SET:
	CALL	GETINT		;HL=USR(XXXX)
	RET	NZ

;	LD	(CCLTBL),HL
	LD	DE,CCLTBL
	LD	BC,CCLSIZE
	LDIR
	RET

;================================
;--- SET SPRITE ATTRIBUTE ----
;================================
; U=USR(ADR)
SPR_SET:
	CALL	GETINT		;HL=USR(XXXX)
	RET	NZ
;
	LD	A,1
	LD	(SPRINTD),A	;DISALE HOOK

	PUSH	HL		;(SP)=USR ADR

	LD	A,(SSYNCMD)
	CP	SSYNCMD0
	JR	NZ,SPRST_0	;use vsync -> jump
;				 not use vsync -> ...
;--- IMMEDIATE double buffer mode
	LD	HL,(ATRBAS)	;sprite atr.
	CALL	REVATRBAS
	LD	(ATRBAS),HL	;write to back buffer

SPRST_0:
	POP	IX		;IX=USR ADR

	LD	B,32
	LD	IY,SPRATB	;IY=SPRATR WORK BUFFER

SPRSETL:
;--SKIP FLAG
	LD	D,(IX+SPRU_OF+1)
	BIT	7,D		;FLAG bit15 (SFG_SKIP)
	JR	Z,SPRST_S
;	LD	(IY+SPRW_OF),SPW_SKIP	;SKIP FLAG
;	JP	SPRSTNX
	LD	A,BIT_ND	;bit4=NoDisp
	JR	SPRSTY2
SPRST_S:
;--ANIM FLAG
	LD	E,(IX+SPRU_OF)
	LD	A,E
	AND	SFG_AWAIT	;FLAG bit 3 -0	: auto anim wait (0-15)
	JR	Z,SPRSTY1
	LD	E,A
	LD	A,D
	INC	A
	AND	SFG_ACNTR	;FLAG bit 11-8	: wait counter (0-15)
	LD	D,A
	CP	E
	JR	C,SPRANIN	; COUNT < WAIT ?
;	add pattern ofs
	LD	A,(IX+SPRU_OF)
	AND	SFG_ATYPE	;FLAG bit 4	: 0=2pattern / 1=4pattern ANIM
	RLCA
	OR	SFG_ATYPE	;pat mask : 30H or 10H
	LD	E,A
	LD	A,(IX+SPRU_OF+1)
	ADD	A,SFG_PBIT
	AND	E		;FLAG bit 13-12 : pat offset (0-3)
	LD	(IX+SPRU_OF+1),A
	LD	D,0		; reset count
SPRANIN:
	LD	A,(IX+SPRU_OF+1)
	AND	0F0H
	OR	D
	LD	(IX+SPRU_OF+1),A
;--SPR Y
SPRSTY1:
	LD	E,(IX+SPRU_OY)	;DE=Y
	LD	D,(IX+SPRU_OY+1)
	SRA	D		;Y/2
	RR	E
;	SRA	D		;Y/4
;	RR	E
	LD	A,BIT_ND	;bit4=NoDisp
	LD	HL,31
	OR	A
	ADC	HL,DE		;ADD HL,rr not use Sign flag
	JP	M,SPRSTY2	;Smaller than -31? = NoDisp
	PUSH	DE
	LD	DE,212+31
	OR	A
	SBC	HL,DE
	POP	DE
	JR	NC,SPRSTY2	;Laeger than 211 = NoDisp

	LD	A,(ERASEY)	;Y=216 : erase after sprite
	CP	E
	LD	A,0		;Disp
	JR	NZ,SPRSTY2
	DEC	E		;avoid Y=216
SPRSTY2:
	LD	(IY+SPRW_OF),A	;save NoDisp(bit4)
	LD	(IY+SPRW_OY),E	;save Y

;--SPR X
	LD	E,(IX+SPRU_OX)	;DE=X
	LD	D,(IX+SPRU_OX+1)
	SRA	D		;X/2
	RR	E
;	SRA	D		;X/4
;	RR	E
	LD	A,BIT_ND	;A=NoDisp(bit4)
	LD	HL,31
	OR	A
	ADC	HL,DE		;* need ADC. (ADD HL,rr is not change sign flag)
	JP	M,SPRSTX2	;Smaller than -31? = NoDisp
	PUSH	DE
	LD	DE,256+31
	OR	A
	SBC	HL,DE
	POP	DE
	JR	NC,SPRSTX2	;Laeger than 255? = NoDisp

	XOR	A		;Disp,no EC
	RLC	D
	JR	NC,SPRSTX2	;PLUS?
	LD	A,E
	ADD	A,32		;SHIFT 32dot
	LD	E,A
	LD	A,BIT_EC	;EC(bit7)
SPRSTX2:
	LD	(IY+SPRW_OX),E	;save X
;-- Process NoDisp bit
	OR	(IY+SPRW_OF)
	LD	(IY+SPRW_OF),A	;save EC(bit7),NoDisp(bit4)
	AND	BIT_ND		;No Disp?
	JR	Z,SPRSTP1	; Disp -> JUMP
	LD	A,(NDISPY)	; NoDisp -> ...
	LD	(IY+SPRW_OY),A	; Y=NoDisp
	XOR	A
	LD	(IY+SPRW_OP),A	; PAT No.=0
	JR	SPRSTNX		; goto Next entry
SPRSTP1:
;-- Pattern No.
	LD	E,(IX+SPRU_OP)
	LD	A,(IX+SPRU_OF+1)
	AND	SFG_APAT	;FLAG bit13-12 : pat offset (0-3)
	JR	Z,SPRSTP2
	RRCA			;..pp.... -> ...pp...
	RRCA			;...pp... -> ....pp..
	RRCA			;....pp.. -> .....pp.
	ADD	A,E		; pat + pp*2
	LD	E,A		; pat = pat + pat_ofs * 2
SPRSTP2:
	SLA	E		;n*2
	SLA	E		;n*4 (for 16x16)
	LD	(IY+SPRW_OP),E	; PAT No.
;-- Loop param
SPRSTNX:
	LD	DE,4
	ADD	IY,DE		;IY+=4
	ADD	IX,DE
	ADD	IX,DE		;IX+=8
	DEC	B
	JP	NZ,SPRSETL	;DJNZ is out of range
SPRSTE1:
	XOR	A
	LD	(SPRINTD),A

	LD	A,(SSYNCMD)	;USE HOOK?
	CP	SSYNCMD2	;VSYNC + LATE DRAW MODE
	RET	Z

;	LD	A,(SPRFLKF)	;USE FLICKER?
;	OR	A
;	JR	Z,SPRLNER	;MAKE ATTRIBUTE TABLE (LNINER)

	CALL	SPRFLIK		;MAKE ATTRIBUTE TABLE (FLICKER)
SPRSTE2:
;#IF SPRCOL_USE_RAM_BUFFER
;	CALL	SPCMAKE		;MAKE COLOR TABLE
;#ENDIF ;SPRCOL_USE_RAM_BUFFER
	CALL	WAITCMD		;VDP����� ���خ���
	CALL	SPRVRMT		;WRITE to VRAM

	LD	A,(SSYNCMD)	;USE HOOK?
	OR	A
	JR	NZ,SPRSTEE	; -> YSE = END
;				  -> NO = FLIP IMMEDIATELY
	LD	HL,(ATRBAS)	;sprite atr.
	CALL	SETATRBAS	;SWAP
SPRSTEE:
	EI
	RET

;;-- MAKE ATTRIBUTE TABLE (LINER)
;SPRLNER:	;
;	LD	HL,SPRATB
;	LD	DE,SPRATR
;	LD	BC,SPRATS
;	LDIR
;	JR	SPRSTE2

;================================
;--- FLICKER
;================================
;---ADD START OFFSET
SPRFLIK:
	LD	A,(SPTOFS)	; FLICKER
	ADD	A,10		; 5*2 (for SPRITE COMB)
	AND	SPRMAX-1	; MASK
	LD	(SPTOFS),A
;---SUFFLE
;--> TEST
;	LD	HL,SPRATB
;	LD	DE,SPRATR
;	LD	BC,SPRATS
;	LDIR
;	RET
;<-- TEST
	LD	A,(SPTOFS)	; FLICKER
	LD	L,A
	LD	H,0
	ADD	HL,HL
	ADD	HL,HL		; offset*4
	LD	DE,SPRATB
	ADD	HL,DE
	LD	DE,SPRATR
	LD	A,32
SPRFLKL:
	LDI
	LDI
	LDI
	LDI

	BIT	0,A
	JR	Z,SPRFLK0	; ODD for SPRITE COMBO

	EX	AF,AF'
	LD	BC,SPRATB-16	; BASE ADDRESS - 4*4
	OR	A
	SBC	HL,BC		; HL=OFFSET + 4*4 (INCLEASE 1+1+4=6)
	LD	A,L
	AND	SPRATS-1	; MASK
	LD	L,A
	LD	BC,SPRATB	; BASE ADDRESS
	ADD	HL,BC		; HL=ADDRESS
	EX	AF,AF'
SPRFLK0:
	DEC	A
	JR	NZ,SPRFLKL
	RET

;#IF SPRCOL_USE_RAM_BUFFER
;;================================
;;--- MAKE SPRITE COLOR TABLE to RAM
;;================================
;;	SPRATR + CCLTBL -> RAM SPRCOL
;;
;SPCMAKE:	;
;	LD	B,32
;;	LD	IX,SPRATB
;	LD	IX,SPRATR
;	LD	HL,SPRCOL
;;--COL LOOP
;SPCMAKL:	;
;;--GET FLAG & PAT No.
;	LD	E,(IX+2)	;E=PAT No.
;	LD	D,(IX+3)	;D=FLAG
;	INC	IX
;	INC	IX
;	INC	IX
;	INC	IX		;IX+=4
;	LD	A,D		;A=FLAG
;	AND	BIT_ND
;	JR	Z,SPCMK0
;;--SKIP (CLEAR)
;	LD	D,BIT_IC
;	LD	A,16
;SPCSKL:	;
;	LD	(HL),D
;	INC	HL
;	DEC	A
;	JR	NZ,SPCSKL
;	DJNZ	SPCMAKL
;	RET
;;
;;--CALC COLOR SOURCE ADDRESS
;SPCMK0:
;	LD	A,D		; A=FLAG
;	EX	AF,AF'	; A'=FLAG
;	LD	A,E		; A=PAT No.
;	EXX			; HL'=SPRCOL / B'=MAIN COUNTER
;	LD	E,A		; DE=PAT No.
;	LD	D,0
;	SLA	E
;	RL	D
;	SLA	E
;	RL	D		; DE=PAT*16/4
;;	SLA	E
;;	RL	D		; DE=PAT*16/2
;;	SLA	E
;;	RL	D		; DE=PAT*16
;	LD	HL,CCLTBL
;	ADD	HL,DE	;PATTERN COLOR ADDRESS
;	EX	AF,AF'	; A=FLAG / A'=PAT No.
;	AND	BIT_EC	; A=EC bit
;	LD	E,A		; C=EC bit
;;
;;--WRITE TO SPRCOL (RAM)
;	LD	B,16
;SPCMAK1:	;
;	LD	A,(HL)
;	INC	HL
;;	AND	15		; TEST
;	OR	E		; A=COLOR OR EC
;	EXX			; HL=SPRCOL / B=MAIN COUNTER
;	LD	(HL),A
;	INC	HL
;	EXX			; HL'=SPRCOL / B'=MAIN COUNTER
;	DJNZ	SPCMAK1
;	EXX			; HL=SPRCOL / B=MAIN COUNTER
;	DJNZ	SPCMAKL
;	RET
;#ELSE ;SPRCOL_USE_RAM_BUFFER

;================================
;--- write SPRITE COLOR TABLE to VRAM
;================================
;  IN: C=VRAM PORT
;	   SPRATR + CCLTBL -> VRAM SPRCOL

SPCTVRM:
	LD	A,C		; A=PORT
	EXX			; C'=PORT
	LD	C,A		; C=PORT
	LD	B,32
	LD	HL,SPRATR
;--COL LOOP
SPCTVL:
;--GET FLAG & PAT No.
	INC	HL
	INC	HL
	LD	E,(HL)	;E=(HL+2) PAT No.
	INC	HL
	LD	D,(HL)	;D=(HL+3) FLAG
	INC	HL
	LD	A,D		;A=FLAG
	AND	BIT_ND
	JR	Z,SPCTV0
;--SKIP (CLEAR)
	LD	A,BIT_IC
	LD	D,16
SPCCVL:
	OUT	(C),A
	DEC	D
	JR	NZ,SPCCVL
	DJNZ	SPCTVL
	RET

;--CALC COLOR SOURCE ADDRESS
SPCTV0:
	LD	A,D		; A=FLAG
	EX	AF,AF'	; A'=FLAG
	LD	A,E		; A=PAT No.
	EXX			; HL'=SPRATR / B'=MAIN COUNTER / C'=PORT / C=PORT
	LD	E,A		; DE=PAT No.
	LD	D,0
	SLA	E
	RL	D
	SLA	E
	RL	D		; DE=PAT*16/4
;	SLA	E
;	RL	D		; DE=PAT*16/2
;	SLA	E
;	RL	D		; DE=PAT*16
	LD	HL,CCLTBL
	ADD	HL,DE	;PATTERN COLOR ADDRESS
	EX	AF,AF'	; A=FLAG / A'=PAT No.
	AND	BIT_EC	; A=EC bit
	LD	E,A		; C=EC bit

;--WRITE TO SPRCOL (RAM)
	LD	B,16
SPCTV1:
	LD	A,(HL)
	INC	HL
;	AND	15		; TEST
	OR	E		; A=COLOR OR EC
	OUT	(C),A
	DJNZ	SPCTV1
	EXX			; HL=SPRATR / B=MAIN COUNTER / C=PORT / C'=PORT
	DJNZ	SPCTVL
	RET
;#ENDIFE ;SPRCOL_USE_RAM_BUFFER

;================================
;--- WRITE TO VRAM (SPRITE COLOR TABLE)
;	 with vsync and command wait
;================================
SPRVRMT:
	LD	HL,(ATRBAS)	;sprite atr.
	LD	DE,-SPCOFS	;-512
	ADD	HL,DE
	EX	DE,HL

	DI
	CALL	VSETWRT
	DEC	C

;#IF SPRCOL_USE_RAM_BUFFER
;	LD	HL,SPRCOL
;	LD	B,0
;	OTIR			;OTIR=21state < 29state(TMS9918 VRAM access limit)
;	LD	B,0
;	OTIR			;512 bytes
;#ELSE ;SPRCOL_USE_RAM_BUFFER
	CALL	SPCTVRM		;MAKE SPRCOL ENTRY & WRITE to VRAM
;#ENDIF ;SPRCOL_USE_RAM_BUFFER

;--- WRITE TO VRAM (SPRITE PATTERN TABLE)
	LD	HL,SPRATR
	LD	B,SPRATS	;4*32
	OTIR

	LD	A,1
	LD	(SPRINTW),A

	RET

;================================
;--- SET/RESET SPRITE V INTERRUPT ----
;  IN: U=USR(1)	... SET VSYNC IMMEDIATE DRAW MODE (SLOW)
;	   U=USR(2)	... SET VSYNC LATE DRAW MODE (FAST)
;	   U=USR(OTHER) ... REMOVE VSYNC MODE (TOO FAST)
;================================
SPR_INT:
	CALL	GETINT
	LD	A,L
	CP	SSYNCMD1	; SSYNCMD1
	JR	Z,SPRINT0
	CP	SSYNCMD2	; SSYNCMD2
	JR	Z,SPRINT0
	LD	L,SSYNCMD0	; OTHER VALUE = SSYNCMD0
	LD	A,L
SPRINT0:
	CP	SSYNCMD0
	JR	NZ,SPRISET	; -1 = REMOVE HOOK

SPRIRES:
	LD	A,(SSYNCMD)
	CP	SSYNCMD0
	RET	Z

	DI
	LD	HL,HTIMIB
	LD	DE,H_TIMI
	LD	BC,5
	LDIR

	XOR	A
	LD	(HTIMIB),A
	LD	A,SSYNCMD0
	LD	(SSYNCMD),A

	EI
	RET
;
SPRISET:
	LD	A,(HTIMIB)
	OR	A
	LD	A,L
	LD	(SSYNCMD),A	;ALLOW MODE CHANGE
	RET	NZ

;-- MAKE DOUBLE BUFFER
	LD	HL,(ATRBAS)	;sprite atr.
	LD	(ATRBASA),HL
	CALL	SETATRBAS
	CALL	REVATRBAS
	LD	(ATRBASB),HL
	LD	(ATRBAS),HL
;-- CHANGE HOOK
	DI
	LD	HL,H_TIMI
	LD	DE,HTIMIB
	LD	BC,5
	LDIR
	LD	HL,SPRIJP
	LD	DE,H_TIMI
	LD	BC,3
	LDIR
	LD	A,1
	LD	A,(SPRINTD)

	EI
	RET
SPRIJP:
	JP	SPRINTR

;================================
;--- SPRITE V INTERRUPT ----
;================================
SPRINTR:
	PUSH	AF		;A=#S0 /**need SAVE**
;	BIT	7,A
;	JP	Z,SPRINTNE

	LD	A,(SPRINTD)
	OR	A
	JP	NZ,SPRINTNE
;
	LD	A,(SPRINTW)
	OR	A
	JP	Z,SPRINTR0

	LD	HL,(ATRBAS)	;sprite atr.
	LD	(ATRBASA),HL
	CALL	SETATRBAS
	CALL	REVATRBAS
	LD	(ATRBASB),HL
	LD	(ATRBAS),HL
	;
	XOR	A
	LD	(SPRINTW),A

SPRINTR0:

;-- CHECK VDP COMMAND
	LD	A,(VDPIOW)
	LD	C,A
	INC	C
	LD	A,2
	OUT	(C),A
	LD	A,15+80H
	OUT	(C),A
	IN	A,(C)
	RLCA
	JP	C,SPRINRSE	;SKIP


	CALL	SPRFLIK		;FLICKER
;#IF SPRCOL_USE_RAM_BUFFER
;	CALL	SPCMAKE		;MAKE COLOR TABLE
;#ENDIF ;SPRCOL_USE_RAM_BUFFER
	CALL	SPRVRMT		;WRITE to VRAM

;-- END HOOK
SPRINRSE:
;	XOR	A
;	LD	(SPRINTD),A

;-- SET S#0
	LD	A,(VDPIOW)
	LD	C,A
	INC	C
	XOR	A
	OUT	(C),A
	LD	A,15+80H
	OUT	(C),A

;	LD	A,(VDPIOW)
;	LD	C,A
;	INC	C
;	IN	A,(C)	;trash #s1 vsync
;
SPRINTNE:
	LD	A,(HTIMIB)
	OR	A
	JR	Z,SPRITNHE

	POP	AF
	JP	HTIMIB

;-- NO HOOK
SPRITNHE:
	POP	AF
	RET

;--- HL = HL XOR 400H
REVATRBAS:
	LD	A,H
	XOR	4
	LD	H,A
	RET

;================================
;--- WORK AREA ---
SSYNCMD:	DB	SSYNCMD0	;VSYNC MODE: 0=NO USE / 1=IMMEDIATE / 2=LATE
HTIMIB:		DB	0,0,0,0,0	;H.TIMI backup
SPRINTD:	DB	1	; disable SPRITE interrupt rutine
SPRINTW:	DB	0	; bACK buffer is written
NDISPY:		DB	256-32	; NO DISPLAY Y
ERASEY:		DB	216	; ERASE AFTER SPR(216=mode2/208=mode1)
SPTOFS:		DW	0	; OFFSET for BLINK

CCLTBL:	;	DW	0	; COLOR for each 16x16 PATTERN (16*64) ADDRESS
		DS	CCLSIZE	; COLOR for each 16x16 PATTERN (16*64) BUFFER
SPRATB:		DS	SPRATS	; SPRITE ATTRIBUTE WORK BUFFER 4*32
;				: X,Y,PAT,FLAG

;-- for TRANSEFR to VRAM --
ATRBASA:	DW	7400H	; do set (ATRBAS)-512
ATRBASB:	DW	7000H	; do set (ATRBAS)-512 Back buffer

;#IF SPRCOL_USE_RAM_BUFFER
;SPRCOL:	DS	SPRCLS	; SPRITE COLOR TABLE for VRAM (16*32)
;#ENDIF ;SPRCOL_USE_RAM_BUFFER
SPRATR:		DS	SPRATS	; SPRITE ATTRIBUTE TABLE for VRAM (4*32)



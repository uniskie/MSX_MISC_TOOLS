;-*- tab-width: 8 -*-
;================================
; INCLUDE FILE for LOADSRD
;================================
;USR():
;	SPR_TIME - write TIME
;		   to SPR_PAT No
;		   of SPR#0 - #7
;================================
;---- WRITE TIME to SPRITE ----
;	  for CLOCK.BAS
EXTROM:		EQU	015FH
REDCLK:		EQU	01F5H
WRTCLK:		EQU	01F9H
;ATRBAS:	EQU	0F928H
TIMEBUF:	DS	8
TIMECNT:	DB	11

;VDPIOR:	EQU	0006H	;VDP I/O port m (READ)
;VDPIOW:	EQU	0007H	;VDP I/O port n (WRITE)

REDCRAM:
	PUSH	BC
	PUSH	HL
	LD	IX,REDCLK
	CALL	EXTROM
	POP	HL
	POP	BC
	RET

WRTCRAM:
	PUSH	BC
	PUSH	HL
	LD	IX,WRTCLK
	CALL	EXTROM
	POP	HL
	POP	BC
	RET

;--- MAIN ---
; U=USR()
; RET: U=TIMEBUFF[8]
;	1-A = "0"-"9"
;	B=":"
;	F=" "

SPR_TIME:
	CP	2
	RET	NZ
	PUSH	HL
; (24¼Þ¶ÝË®³¼Þ)
	LD	A,1
	LD	C,1AH
	CALL	WRTCRAM

	LD	C,5
	LD	B,6
	LD	HL,TIMEBUF
TIMSPR_0:
	CALL	REDCRAM
	DEC	C
	INC	A
	LD	(HL),A
	INC	HL
	DJNZ	TIMSPR_0
; (ÃÞ°ÀÉ ¾²ÚÂ)
	LD	HL,(TIMEBUF+4)
	LD	(TIMEBUF+6),HL
	LD	HL,(TIMEBUF+2)
	LD	(TIMEBUF+3),HL
	LD	A,(TIMECNT)
	LD	(TIMEBUF+2),A
	LD	(TIMEBUF+5),A
; (ÃÝÒÂ)
	LD	A,(TIMECNT)
	XOR	4
	LD	(TIMECNT),A

;---WRITE to SPRITE TABLE
; (VDPºÏÝÄÞ ¼­³Ø®³ÏÁ)
	CALL	WAITCMD

	LD	DE,(ATRBAS)	;sprite atr.
	CALL	VSETWRT
	DEC	C
	LD	B,8
	LD	HL,TIMEBUF
;	LD	DE,SPRATB	;add for SPRSET.ASM
TIMSPR_2:
	IN	A,(C)	;SKIP
	IN	A,(C)	;SKIP
	LD	A,(HL)
	INC	HL
	RLCA
	RLCA
	OUT	(C),A

;	INC	DE		;add for SPRSET.ASM
;	INC	DE		;add for SPRSET.ASM
;	INC	DE		;add for SPRSET.ASM
;	LD	(DE),A		;add for SPRSET.ASM

	IN	A,(C)		;SKIP
	DJNZ	TIMSPR_2
	EI

	POP	IX
	LD	HL,TIMEBUF
	LD	(IX+2),L
	LD	(IX+3),H
	RET


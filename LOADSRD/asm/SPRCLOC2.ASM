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
; U=USR(ADR)
;  IN: ADR= {int X,Y,P,F}*8
; RET: ADR[0].P ... ADR[7].P = TIMEBUFF[n]
;	1-A = "0"-"9"
;	B=":"
;	0=" "

SPR_TIME:
	CALL	GETINT
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
	XOR	11
	LD	(TIMECNT),A

;----disable for SPRSET.ASM
;;---WRITE to SPRITE TABLE
;; (VDPºÏÝÄÞ ¼­³Ø®³ÏÁ)
;	CALL	WAITCMD
;;
;;	LD	DE,(ATRBAS)	;sprite atr.
;;	CALL	VSETWRT
;;	DEC	C
;	LD	B,8
;	LD	HL,TIMEBUF
;TIMSPR_2:	;
;;	IN	A,(C)	;SKIP
;;	IN	A,(C)	;SKIP
;	LD	A,(HL)
;	INC	HL
;	RLCA
;	RLCA
;;	OUT	(C),A
;;	IN	A,(C)	;SKIP
;	DJNZ	TIMSPR_2
;;	EI

	POP	DE		; DE=SPR_INT_ATR_ARRAY[8]
	LD	A,E
	OR	D
	RET	Z		; NOP

	LD	HL,TIMEBUF
	LD	B,8
TIMSPR_1:
	LD	A,(HL)
	INC	HL
	INC	DE		; SKIP X
	INC	DE
	INC	DE		; SKIP Y
	INC	DE
	LD	(DE),A		; WRITE P
	INC	DE
	INC	DE
	INC	DE		; SKIP F
	INC	DE
	DJNZ	TIMSPR_1
	RET


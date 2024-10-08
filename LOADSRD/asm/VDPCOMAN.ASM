;-*- tab-width: 8 -*-
;================================
; INCLUDE FILE for LOADSRD
;================================
;USR():
;	WAITVDPC - WAIT VDP COMMAND
;	VDPCMD	 - EXEC VDP COMMAND (nx/ny check)
;	VDPCMDD	 - EXEC VDP COMMAND (Direct)
;================================
;---- VDP Command ----

;VDPIOR:	EQU	0006H	;VDP I/O port m (READ)
;VDPIOW:	EQU	0007H	;VDP I/O port n (WRITE)


; (VDP Command Operation Code)
CMR_HMMC:	EQU	0F0H	;High  CPU->VRAM
CMR_YMMM:	EQU	0E0H	;Yγ�� VRAM->VRAM
CMR_HMMM:	EQU	0D0H	;High  VRAM->VRAM
CMR_HMMV:	EQU	0C0H	;High  fill VRAM
CMR_LMMC:	EQU	0B0H	;Logic CPU->VRAM
CMR_LMCM:	EQU	0A0H	;Logic VRAM->CPU
CMR_LMMM:	EQU	090H	;Logic VRAM->VRAM
CMR_LMMV:	EQU	080H	;Logic fill VRAM
CMR_LINE:	EQU	070H	;Draw Line
CMR_SRCH:	EQU	060H	;Search Color
CMR_PSET:	EQU	050H	;Write Pixel
CMRPOINT:	EQU	040H	;Read Pixel
CMR_STOP:	EQU	000H	;Stop Command

; (Logical Operation Code)
LOG_PSET:	EQU	0
LOG_AND:	EQU	1
LOG_OR:		EQU	2
LOG_XOR:	EQU	3
LOG_NOT:	EQU	4
LOG_TPSET:	EQU	8
LOG_TAND:	EQU	9
LOG_TOR:	EQU	10
LOG_TXOR:	EQU	11
LOG_TNOT:	EQU	12

; (ARGUMENT BITS)
;ARG : bit|__7|__6|__5|__4|__3|__2|__1|__0|
;	  | 0 | - |MXD|MXS|DIY|DIX| EQ|MAJ|
; MXD : DESTINATION �� �����VRAM
; MXS : SORCE �� �����VRAM
; DIY : 0:��   (Y) + NY
;	1:��   (Y) - NY
; DIX : 0:з�  (X) + NX
;	1:���� (X) - NX
; EQ  : (SEARCH) 1:�������� ��޲ ��� ���خ�
; MAJ : (LINE) 0:(NX > NY) ֺŶ�
;	       1:(NX < NY) ��Ŷ�
ARG_DIY:	EQU	08H
ARG_DIX:	EQU	04H
ARG_EQ:	EQU	02H
ARG_MAJ:	EQU	01H

;--- work area ---

CMD_SRC:	DW	0,0	;SX,SY (R#32)
CMD_DST:	DW	0,0	;DX,DY (R#36)
CMD_SIZ:	DW	0,0	;NX,NY (R#40)
CMD_CLR:	DB	0	;COLOR (R#44)
CMD_ARG:	DB	0	;ARGUMENT (R#45)
CMD_CMR:	DB	0	;OPERATION (R#46)

CMD_DAT:	EQU	CMD_SRC

COPYPRM:
	CALL	GETINT		;HL=USR(XXXX)
	RET	NZ

	LD	DE,CMD_DAT
	LD	BC,CMD_CMR-CMD_DAT+1
	LDIR
	RET

;================================
;--- WAIT VDP COMMAND finish
; U=USR(0)
;================================
WAITVDPC:
	CALL	WAITCMD
	EI
	RET

;================================
;--- DO VDP COMMAND (direct data)
; U=USR(address)
;	DW	0,0	;SX,SY (R#32)
;	DW	0,0	;DX,DY (R#36)
;	DW	0,0	;NX,NY (R#40)
;	DB	0	;COLOR (R#44)
;	DB	0	;ARGUMENT (R#45)
;	DB	0	;OPERATION (R#46)
;	-- 9 bytes
;	OR
;	DW	0,0	;SX,SY (R#32)
;	DW	0,0	;DX,DY (R#36)
;	DW	0,0	;NX,NY (R#40)
;	DW	0	;COLOR (R#44) + ARGUMENT (R#45)*256
;	DW	0	;OPERATION (R#46)
;	-- 10 bytes
;================================
VDPCMDD:
	CALL	COPYPRM
	RET	NZ
	JP	VDPCOMAND

;================================
;--- DO VDP COMMAND (use nx,ny,page modify)
; U=USR(address)
;	DW	0,0	;SX,SY (R#32)
;	DW	0,0	;DX,DY (R#36)
;	DW	0,0	;NX,NY (R#40)
;	DB	0	;COLOR (R#44)
;	DB	0	;ARGUMENT (R#45)
;	DB	0	;OPERATION (R#46)
;	-- 9 bytes
;	OR
;	DW	0,0	;SX,SY (R#32)
;	DW	0,0	;DX,DY (R#36)
;	DW	0,0	;NX,NY (R#40)
;	DW	0	;COLOR (R#44) + ARGUMENT (R#45)*256
;	DW	0	;OPERATION (R#46)
;	-- 10 bytes

;	arg=0 �� nx,ny � ϲŽ��� ok
;	sy,dy � active page � ����� � ���
;================================
VDPCMD:
	CALL	COPYPRM
	RET	NZ
	CALL	M_VDPC
	RET	C		;cancel command
	JP	VDPCOMAND

;================================
;--- exec. vdp command
; IN:	HL=ADDRESS (CMD_DAT etc.)
; USE:	AF,BC,HL
;================================
VDPCOMAND:
	LD	A,(VDPIOW)
	LD	C,A
	INC	C
	CALL	WAITCMD2
	LD	A,32		;R#32
	DI
	OUT	(C),A
	LD	A,17+80H	;�ݿ޸ ����
	OUT	(C),A
	INC	C
	INC	C
	LD	B,15
	LD	HL,CMD_DAT
	OTIR
	NOP
	EI
	RET

;================================
;--- wait until vdp-command finish
; USE: AF,AF',C
;================================
WAITCMD:
	LD	A,(VDPIOR)
	LD	C,A
	INC	C
WAITCMD2:
	LD	A,2
	DI
	OUT	(C),A
	LD	A,15+80H
	OUT	(C),A
WAITCMD_:
	IN	A,(C)
	RRCA
	EX	AF,AF'		; use EI
	XOR	A
	OUT	(C),A
	LD	A,15+80H
	OUT	(C),A
	EI			; use EI
	EX	AF,AF'
	JR	C,WAITCMD2	; use EI
;	JR	C,WAITCMD_	; no EI
	RET

;================================
;--- modify nx,ny parameter for USR()
; OUT:	Cy = cancel command
; USE:	AF,HL,DE,BC
;================================
M_VDPC:
;--- mofidy sx,dx minus
	LD	A,(CMD_SRC+1)	;SX-high
	RLCA
	JR	NC,SX_PLUS
	LD	DE,(CMD_SRC)	;SX
	XOR	A
	LD	L,A
	LD	H,A
	LD	(CMD_SRC),HL
	SBC	HL,DE		;offset = minus -> plus
	EX	DE,HL
	LD	HL,(CMD_DST)	;DX+offset
	ADD	HL,DE
	LD	(CMD_DST),HL
	XOR	A
	LD	HL,(CMD_SIZ)	;NX+offset
	SBC	HL,DE
	RET	C		;ERROR: zero size
	LD	(CMD_SIZ),HL
SX_PLUS:
	LD	A,(CMD_SRC+3)	;SY-high
	RLCA
	JR	NC,SY_PLUS
	LD	DE,(CMD_SRC+2)	;SY
	XOR	A
	LD	L,A
	LD	H,A
	LD	(CMD_SRC+2),HL
	SBC	HL,DE		;offset = minus -> plus
	EX	DE,HL
	LD	HL,(CMD_DST+2)	;DY+offset
	ADD	HL,DE
	LD	(CMD_DST+2),HL
	XOR	A
	LD	HL,(CMD_SIZ+2)	;NY+offset
	SBC	HL,DE
	RET	C		;ERROR: zero size
	LD	(CMD_SIZ+2),HL
SY_PLUS:
;--- modify nx,ny parameter
	LD	A,(CMD_ARG)	;ARG
	LD	C,A
; check NX,DIX
	LD	DE,(CMD_SIZ)
	LD	A,D
	RLCA			;sign check
	JR	NC,NX_PLUS	;NX = plus
	LD	A,ARG_DIX	;NX = minus
	OR	C
	LD	C,A
	LD	HL,0
	SBC	HL,DE		;ABS(NX)
	EX	DE,HL
NX_PLUS:
	LD	A,D
	AND	1		; NX=NX AND 511
	LD	D,A
	LD	(CMD_SIZ),DE

; check NY,DIY
	LD	DE,(CMD_SIZ+2)
	LD	A,D
	RLCA			;sign check
	JR	NC,NY_PLUS	;NY = plus
	LD	A,ARG_DIY	;NY = minus
	OR	C
	LD	C,A
	LD	HL,0
	SBC	HL,DE		;ABS(NY)
	EX	DE,HL
NY_PLUS:
	LD	A,D
	AND	3		;NX=NX AND 1023
	LD	D,A
	LD	(CMD_SIZ+2),DE

	LD	A,C
	LD	(CMD_ARG),A	;ARG

	OR	A
	RET


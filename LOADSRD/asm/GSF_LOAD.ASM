; INCLUDE FILE for LOADSRD 
;================================
;USR():
;	LOAD_SRD - Load BSAVE/SRN(GRAPH SAURUS)
;	SET_PLT  - Set palette
;================================
;--- work area
;LOADOFS:	DW	0	;LOAD_SRD VRAM offset
; read buffer:  B000H-CFFFH
;DMA:		DW	0B000H	;Read buffer address
;DMASIZ:		DW	2000H	;Read buffer size
;
W_TYPE:		DB	0	;0:binary/ff:packed
W_DSIZE:	DW	0	;DATA SIZE LOW16
W_DSIZH:	DB	0	;DATA SIZE HIGH8
W_VRAM:		DW	0000H
W_LOOP:		DW	0
W_MODE:		DB	0
;
W_YMAX:		DB	255	; y max (size-1)
W_YSIZE:	DW	100H	; y size
;
FCB:		DB	0
		DB	'FILENAMEEXT'	;*DM*
		DS	37-12
FCB_BS:		EQU	16	;Ãß≤Ÿª≤Ωﬁ(32bit)… µÃæØƒ
;
;--- symbols
;BUF:		EQU	0F55EH	;Type char buffer(258 bytes)
;
SYSCALL:	EQU	0F37DH	;ºΩ√—∫∞Ÿ
;
;(VRAM.ASM)
;SCRMOD:	EQU	0FCAFH	;Ω∏ÿ∞› ”∞ƒﬁ
;VDPIOR:	EQU	0006H	;VDP I/O port m (READ)
;VDPIOW:	EQU	0007H	;VDP I/O port n (WRITE)
;
; BSAVE/SRN FILE ID
ID_SRN:		EQU	0FEH	;ID:LINER PIXEL
ID_CMP:		EQU	0FDH	;ID:COMPRESSED PIXEL
;
BSVHSZ:		EQU	7	;BSAVE/SRN HEADER SIZE
;
;==== sub routines ========
;
;======================
;---- file access ----
;
;--- set fcb's filename by filemane string
SETNAME:	;use: all
; in hl:adr. / a:length
; '.'¡™Ø∏
	LD	C,A
	LD	B,8
	LD	DE,FCB+1
STNAM_0:	;
	LD	A,(HL)
	INC	HL
	CP	'.'
	JR	Z,STNAM_1	;8”ºﬁœ√ﬁ' '√ﬁ≥“Ÿ
	LD	(DE),A
	INC	DE
	DEC	B
	JR	Z,STNAM_2
	DEC	C
	JP	NZ,STNAM_0
	JR	STNAM_F1	;µ‹ÿœ√ﬁ' '√ﬁ≥“Ÿ(1)
STNAM_1:	;
;filename(8”ºﬁœ√ﬁ)¶ ' '√ﬁ ≥“Ÿ
	LD	A,' '
	LD	(DE),A
	INC	DE
	DJNZ	STNAM_1
STNAM_2:	;
; filename=OK -> ∂∏¡Æ≥º
	LD	B,3		; ∂∏¡Æ≥º = 3”ºﬁ
	LD	A,(HL)
	CP	'.'		; 9 ”ºﬁ“ = '.' ≈◊ Ω∑ØÃﬂ
	JR	NZ,STNAM_3
	INC	HL
	DEC	C
	JR	Z,STNAM_F2	;µ‹ÿœ√ﬁ≥“Ÿ(2)
STNAM_3:	;
;∂∏¡Æ≥º √›ø≥
	LD	A,(HL)
	INC	HL
	LD	(DE),A
	INC	DE
	DEC	B
	RET	Z		; complete
	DEC	C
	JP	NZ,STNAM_3
	JR	STNAM_F2
; µ‹ÿœ√ﬁ' '√ﬁ ≥“Ÿ
STNAM_F1:	;
	INC	B
	INC	B
	INC	B
STNAM_F2:	;
	LD	A,' '
	LD	(DE),A
	INC	DE
	DJNZ	STNAM_F2
	RET
;
;--- open file
FILEOPEN:	;
	LD	DE,FCB
	LD	C,0FH
	CALL	SYSCALL
	LD	IX,FCB
	LD	(IX+14),1
	LD	(IX+15),0	;rec.size(1)
	LD	(IX+33),0
	LD	(IX+34),0
	LD	(IX+35),0
	LD	(IX+36),0	;rec.
	OR	A
	LD	HL,_M_OPEN
	JP	NZ,ERROR
;
; (set dma)
	LD	DE,(DMA)
	LD	C,1AH
	CALL	SYSCALL
	RET
;
;--- set file information from file header
GET_HEAD:	;
; (read header)
	LD	HL,7
	LD	DE,FCB
	LD	C,27H
	CALL	SYSCALL
	OR	A
	LD	HL,_M_TYPE
	JP	NZ,ERROR
;
; check head
	LD	IX,(DMA)
	LD	A,(IX+0)	;bin:FEH / pack:FDH
	ADD	A,3
	LD	(W_TYPE),A
	CP	2
	LD	HL,_M_TYPE
	JP	NC,ERROR	; A>=2
;
	LD	E,(IX+1)	; START ADDRESS
	LD	D,(IX+2)
	LD	(W_VRAM),DE
;
;==> OLD (USE HEADER START ADDRESS & ENDADDRESS)
;; calc dat size
;	LD	L,(IX+3)	; END ADDRESS
;	LD	H,(IX+4)
;	XOR	A
;	SBC	HL,DE
;	LD	A,(IX+0)	; ID
;	CP	0FDH		; COMMPRESSED
;	JR	Z,WRDSIZ	; ø…œœ … ±¿≤
;;
;	INC	HL		; END - START + 1
;	LD	A,L
;	AND	254		; ∏ﬁ≥Ω≥ œŸ“∫–
;	LD	L,A
;WRDSIZ: ;
;	LD	(W_DSIZE),HL
;	LD	A,L
;	OR	H
;	JR	Z,WRDSZ1
;	XOR	A		; SIZE <= $0FFFF
;	LD	(W_DSIZH),A
;	RET
;WRDSZ1: ;
;	INC	A		; SIZE = $10000
;	LD	(W_DSIZH),A
;	RET
;==< OLD (USE HEADER START ADDRESS & ENDADDRESS)
;
;==> NEW (USE FCB File size)
; calc dat size
	LD	IY,FCB+FCB_BS	; FILE SIZE(32bit)
	LD	L,(IY+0)
	LD	H,(IY+1)
	LD	A,(IY+2)	; 24bitœ√ﬁ¿≤µ≥
; File size - 7 = Data size
	LD	DE,BSVHSZ	; HEADER SIZE = 7
	OR	A
	SBC	HL,DE
	SBC	A,0
	LD	(W_DSIZE),HL
	LD	(W_DSIZH),A
	RET
;<== NEW (USE FCB File size)
;
;--- calc. read size & rest size
CALREC:	; RET HL:SIZE

	LD	HL,(W_DSIZE)
	LD	A,(W_DSIZH)
	LD	DE,(DMASIZ)
	SBC	HL,DE
	SBC	A,0
	JR	NC,CALREC_
	ADD	HL,DE		; HL = (W_DSIZE)
	LD	DE,0
	LD	(W_DSIZE),DE
	XOR	A
	LD	(W_DSIZH),A
	RET
CALREC_:	;
	LD	(W_DSIZE),HL
	LD	(W_DSIZH),A
	LD	HL,(DMASIZ) 	; HL = (DMASIZ)
	RET
;
;--- read file
FILEREAD:	; IN H:SIZE
	LD	DE,FCB
	LD	C,27H
	CALL	SYSCALL
	OR	A
	RET
;
;======================
;---- graphics ----
;
;--- check screen mode
CHKSCMD:	;
	LD	A,(SCRMOD)	;screen mode
	CP	7
	LD	A,255		;max y = 255
	JR	NC,CHKSCMD_
	LD	A,127		;max y = 127
CHKSCMD_:	;
	LD	(W_YMAX),A
	LD	L,A
	LD	H,0
	INC	HL
	LD	(W_YSIZE),HL
	RET
;
;--- set vram address to write
; use:A,C,DE
;
VSETWR:	;
	LD	DE,(W_VRAM)
	JP	VSETWRT
;
;--- ERROR routine ---
;
ERROR:	; ¥◊∞ºÆÿ
	LD	SP,(ERROR_SP)
	EI
;
	XOR	A
	LD	DE,_M_OK
	SBC	HL,DE
	RET	Z	; SUCCESS
;
; -- ¥◊∞ ¶ µ∫Ω
; CALL CRUNCH ; ¡≠≥∂›ƒﬁ∞ƒﬁ Õ Õ›∂›
; LD HL,KBUF
	CALL	NEWSTT	; ¡≠≥∂›∫∞ƒﬁ ºﬁØ∫≥
	RET
;
ERROR_SP:	;
	DW	0
;
;CRUNCH:	EQU	42B2H	; TEXT TO INTERMEDIATE CODE
NEWSTT:		EQU	4601H ; EXEC BASIC INTERMEDIATE CODE
;KBUF:		EQU	0F41FH ; INTERMEDIATE CODE BUFFER
_M_OK:		EQU	0
_M_OPEN:	;':ERROR53',0 ; File not found
	DB	':'
	DB	0A6H
	DB	0FH
	DB	53
	DB	0
_M_TYPE:	;':ERROR254',0 ; Unprintable error 244
	DB	':'
	DB	0A6H
	DB	0FH
	DB	254
	DB	0
_M_UERR:	;':ERROR255',0 ; Unprintable error 244
	DB	':'
	DB	0A6H
	DB	0FH
	DB	255
	DB	0
;
;
;======================
;--- LOAD CG DATA ----
;
LOAD_SRD:	;
; (SETUP ERROR TRAP)
	LD	(ERROR_SP),SP
	LD	HL,_M_UERR
;
; check variable type
	CP	3
	JP	NZ,ERROR
;
; (a=STRING LENGTH)
	LD	A,(DE)
; OR A
; JP Z,ERROR
	CP	11	;11”ºﬁ≤∂   ¥◊∞
	JP	C,ERROR
;
; (hl=STRING ADDRESS)
	INC	DE
	EX	DE,HL
	LD	E,(HL)
	INC	HL
	LD	D,(HL)
	EX	DE,HL
;
; (SET FILENAME)
	CALL	SETNAME
;
	CALL	CHKSCMD	;¡™Ø∏ Ω∏ÿ∞› ”∞ƒﬁ
;
; (LOAD & DRAW)
	CALL	FILEOPEN
	CALL	GET_HEAD
	CALL	CALREC
	PUSH	HL
	CALL	FILEREAD
	POP	DE
	CALL	WRTCG_F
	LD	HL,(W_DSIZE)
	LD	A,(W_DSIZH)
	OR	H
	OR	L
	JP	Z,END_OK
L_MAIN:	;
	CALL	CALREC
	PUSH	HL
	CALL	FILEREAD
	POP	DE
	CALL	WRTCG_N
	LD	HL,(W_DSIZE)
	LD	A,(W_DSIZH)
	OR	H
	OR	L
	JP	NZ,L_MAIN
END_OK:	;
	LD	HL,_M_OK
	JP	ERROR
;
; --WRITE CG DATA to VRAM --
; in:  DE = Size
;
WRTCG_F:	;
	EXX
	CALL	VSETWR
	DEC	C
	LD	DE,(W_VRAM)
	EXX
	LD	HL,(DMA)
;
	LD	A,(W_TYPE)
	CP	1
	JP	C,EXTSR7_F
	JP	Z,NORSR7_F
	RET
;
WRTCG_N:	;
	EXX
	LD	A,(VDPIOW)
	LD	C,A
	LD	DE,(W_VRAM)
	EXX
	LD	HL,(DMA)
;
	LD	A,(W_TYPE)
	CP	1
	JP	C,EXTSR7_N
	JP	Z,NORSR7_F
	RET
;
;
; -- DECODE "Graph Saurus RLE" --
REQ_ESR7:	;
	LD	(W_MODE),A
	LD	(W_LOOP),BC
	EXX
	LD	(W_VRAM),DE
	RET
EXTSR7_N:	;
	LD	BC,(W_LOOP)
	LD	A,(W_MODE)
	CP	1
	JP	C,EXTSR7_F
	JP	Z,EXSR7_1
	JP	EXSR7_2
;
; START CHECK DATA
EXTSR7_F:	;
; CHECK BUFFER 0
	LD	A,D
	OR	E
	LD	A,0
	JR	Z,REQ_ESR7
;
; A=0 ≈◊ Ÿ∞Ãﬂ∂∑∫– Õ ºﬁ¨›Ãﬂ
	LD	A,(HL)
	INC	HL	;adr.+
	DEC	DE	;size-
	AND	A
	JR	Z,EXSR7_1
;
; A<=15 ≈◊ B=A √ﬁ Ÿ∞Ãﬂ∂∑∫–
	CP	10H
	LD	B,A
	JR	C,EXSR7_2
;
; ¡Æ∏æ¬ º√≤ ∂∑∫–
	EXX
	OUT	(C),A
	INC	DE	;vram+
	LD	A,D
	OR	E
	JR	Z,EXSR7_E
	LD	A,(W_YMAX)
	CP	D
	EXX
	JR	NC,EXTSR7_F
	JP	END_OK
;
; Ÿ∞Ãﬂ ∂∑∫– …  ºﬁ“
EXSR7_1:	;
;  ﬁØÃß¡™Ø∏ 1
	LD	A,D
	OR	E
	LD	A,1
	JR	Z,REQ_ESR7
;
; Ÿ∞Ãﬂ∂≤Ω≥ ¶ ∆≠≥ÿÆ∏
	LD	B,(HL)
	INC	HL	;adr.+
	DEC	DE	;size-
;
; Ÿ∞Ãﬂ∂∑∫– ºﬁØ∫≥
EXSR7_2:	;
;  ﬁØÃß¡™Ø∏ 2
	LD	A,D
	OR	E
	LD	A,2
	JR	Z,REQ_ESR7
;
; ∂◊∞∫∞ƒﬁ ¶ ∆≠≥€∏
	LD	A,(HL)
	INC	HL	;adr.+
	DEC	DE	;size-
;
; Ÿ∞Ãﬂ
EXSR7_3:	;
	LD	C,A
	EXX
	OUT	(C),A
	INC	DE	;vram+
	LD	A,D
	OR	E
	JR	Z,EXSR7_E
	LD	A,(W_YMAX)
	CP	D
	EXX
	JR	C,EXSR7_E
	LD	A,C
	DJNZ	EXSR7_3
	JP	EXTSR7_F
;
EXSR7_E:	;
	JP	END_OK
;
;
;-- NORMAL BINARY --
REQ_NSR7:	;
	EXX
	LD	(W_VRAM),DE
	RET
;
NORSR7_F:	;
;( ﬁØÃß¡™Ø∏)
	LD	A,D
	OR	E
	JR	Z,REQ_NSR7
;
	LD	A,(HL)
	INC	HL
	DEC	DE
;
	EXX
	OUT	(C),A
	INC	DE	;vram+
	LD	A,D
	OR	E
	JP	Z,END_OK
	LD	A,(W_YMAX)
	CP	D
	EXX
	JP	NC,NORSR7_F
	JP	END_OK
;
;======================
;---- SET PALETTE ----
; a=usr(address)
; address:palette*16
; parette:2byte:rb,0g
SET_PLT:	;
	CP	2
	RET	NZ
	CALL	GETINT		;HL=USR(XXXX)
;
	LD	A,(VDPIOW)
	LD	C,A
	INC	C
;
	DI
	XOR	A
	OUT	(C),A
	LD	A,16+80H
	OUT	(C),A
;
	CALL	WAIT_VR2
	INC	C
;
	LD	B,32
	OTIR
	EI
	RET

; INCLUDE FILE for LOADSRD 
;================================
;USR():
;	LOAD_SRD - Load SR?,SC? file
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
FCB_BS:		EQU	16	;Ì§²Ù»²½Þ(32bit)É µÌ¾¯Ä
;
;--- symbols
;BUF:		EQU	0F55EH	;Type char buffer(258 bytes)
;
SYSCALL:	EQU	0F37DH	;¼½ÃÑº°Ù
ACPAGE:		EQU	0FAF6H	;±¸Ã¨ÌÞÍß°¼Þ
SCRMOD:		EQU	0FCAFH	;½¸Ø°Ý Ó°ÄÞ
;
VDPIOR:		EQU	0006H	;VDP I/O port m (READ)
VDPIOW:		EQU	0007H	;VDP I/O port n (WRITE)
;
ID_SRN:		EQU	0FEH	;ID:LINER PIXEL
ID_CMP:		EQU	0FDH	;ID:COMPRESSED PIXEL
;
BSVHSZ:		EQU	7	;BSAVE HEADER SIZE
;
;==== sub routines ========
;---- file access ----
;
;--- set fcb's filename by filemane string
SETNAME:	;use: all
; in hl:adr. / a:length
; '.'Áª¯¸
	LD	C,A
	LD	B,8
	LD	DE,FCB+1
STNAM_0:	;
	LD	A,(HL)
	INC	HL
	CP	'.'
	JR	Z,STNAM_1	;8Ó¼ÞÏÃÞ' 'ÃÞ³ÒÙ
	LD	(DE),A
	INC	DE
	DEC	B
	JR	Z,STNAM_2
	DEC	C
	JP	NZ,STNAM_0
	JR	STNAM_F1	;µÜØÏÃÞ' 'ÃÞ³ÒÙ(1)
STNAM_1:	;
;filename(8Ó¼ÞÏÃÞ)¦ ' 'ÃÞ ³ÒÙ
	LD	A,' '
	LD	(DE),A
	INC	DE
	DJNZ	STNAM_1
STNAM_2:	;
; filename=OK -> ¶¸Á®³¼
	LD	B,3		; ¶¸Á®³¼ = 3Ó¼Þ
	LD	A,(HL)
	CP	'.'		; 9 Ó¼ÞÒ = '.' Å× ½·¯Ìß
	JR	NZ,STNAM_3
	INC	HL
	DEC	C
	JR	Z,STNAM_F2	;µÜØÏÃÞ³ÒÙ(2)
STNAM_3:	;
;¶¸Á®³¼ ÃÝ¿³
	LD	A,(HL)
	INC	HL
	LD	(DE),A
	INC	DE
	DEC	B
	RET	Z		; complete
	DEC	C
	JP	NZ,STNAM_3
	JR	STNAM_F2
; µÜØÏÃÞ' 'ÃÞ ³ÒÙ
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
;	JR	Z,WRDSIZ	; ¿ÉÏÏ É ±À²
;;
;	INC	HL		; END - START + 1
;	LD	A,L
;	AND	254		; ¸Þ³½³ ÏÙÒºÐ
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
	LD	A,(IY+2)	; 24bitÏÃÞÀ²µ³
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
;
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
; de = vram address
VSETWR2:	;
	LD	A,(VDPIOW)
	INC	A
	LD	C,A
	LD	A,(SCRMOD)	;screen mode
	CP	7
	JR	NC,VSETWR3	; page / 1
; SCREEN 5,6 = page : A16,15
	LD	A,D
	RLA			; c=d7
	RLA			; c=d6
	LD	A,(ACPAGE)	; Active Page
	RLA			;00000pp6
	AND	7		; xxxxxpp6 ÈÝÉÀÒ mask
	JR	VSETWR4
VSETWR3:	;
; SCREEN 7,8 = page : A16
	LD	A,(ACPAGE)	; Active Page
	RRA			;c=page(p)
	LD	A,D
	RLA			;6543210p/c=7
	RLA			;543210p7/c=6
	RLA			;43210p76/c=5
	AND	7		; xxxxxp76
VSETWR4:	;
	DI
	OUT	(C),A		;bit2-0:A16-14 / bit7-3:00000
	LD	A,8EH
	OUT	(C),A
;
	OUT	(C),E		;A7-0
	RES	7,D		;bit7:0
	SET	6,D		;bit6:WRITE=1
	OUT	(C),D		;bit5-0:A13-8
	RET
;
;--- wait until vdp-command finish
WAITCMD:	;
	LD	A,(VDPIOW)
	LD	C,A
	INC	C
	DI
WAITCMD2:	;
	LD	A,2
	OUT	(C),A
	LD	A,15+80H
	OUT	(C),A
WAITCMD_:	;
	IN	A,(C)
	RRCA
	JP	C,WAITCMD_
	XOR	A
	OUT	(C),A
	LD	A,15+80H
	OUT	(C),A
	RET
;
;--- wait until v-sync cycle
WAIT_VR:	;
	LD	A,(VDPIOW)
	LD	C,A
	INC	C
	DI
WAIT_VR2:	;
	LD	A,2
	OUT	(C),A
	LD	A,15+80H
	OUT	(C),A
WAITVR_:	;
	IN	A,(C)
	AND	40H
	JP	Z,WAITVR_
	XOR	A
	OUT	(C),A
	LD	A,15+80H
	OUT	(C),A
	RET
;
;--- ERROR routine ---
;
ERROR:	; ´×°¼®Ø
	LD	SP,(ERROR_SP)
	EI
;
	XOR	A
	LD	DE,_M_OK
	SBC	HL,DE
	RET	Z	; SUCCESS
;
; -- ´×° ¦ µº½
; CALL CRUNCH ; Á­³¶ÝÄÞ°ÄÞ Í ÍÝ¶Ý
; LD HL,KBUF
	CALL	NEWSTT	; Á­³¶Ýº°ÄÞ ¼Þ¯º³
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
;
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
	CP	11	;11Ó¼Þ²¶ Ê ´×°
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
	CALL	CHKSCMD	;Áª¯¸ ½¸Ø°Ý Ó°ÄÞ
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
; A=0 Å× Ù°Ìß¶·ºÐ Í ¼Þ¬ÝÌß
	LD	A,(HL)
	INC	HL	;adr.+
	DEC	DE	;size-
	AND	A
	JR	Z,EXSR7_1
;
; A<=15 Å× B=A ÃÞ Ù°Ìß¶·ºÐ
	CP	10H
	LD	B,A
	JR	C,EXSR7_2
;
; Á®¸¾Â ¼Ã² ¶·ºÐ
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
; Ù°Ìß ¶·ºÐ É Ê¼ÞÒ
EXSR7_1:	;
; ÊÞ¯Ì§Áª¯¸ 1
	LD	A,D
	OR	E
	LD	A,1
	JR	Z,REQ_ESR7
;
; Ù°Ìß¶²½³ ¦ Æ­³Ø®¸
	LD	B,(HL)
	INC	HL	;adr.+
	DEC	DE	;size-
;
; Ù°Ìß¶·ºÐ ¼Þ¯º³
EXSR7_2:	;
; ÊÞ¯Ì§Áª¯¸ 2
	LD	A,D
	OR	E
	LD	A,2
	JR	Z,REQ_ESR7
;
; ¶×°º°ÄÞ ¦ Æ­³Û¸
	LD	A,(HL)
	INC	HL	;adr.+
	DEC	DE	;size-
;
; Ù°Ìß
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
;(ÊÞ¯Ì§Áª¯¸)
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
;
;---- SET PALETTE ----
; a=usr(address)
; address:palette*16
; parette:2byte:rb,0g
SET_PLT:	;
	CP	2
	RET	NZ
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
; --> ÃÇ· ÃÞ Á®¸¾Â Ó¼ÞÚÂ ±ÄÞÚ½ ¼­Ä¸
; LD HL,(0F7F8H)
; <--
; --> Ã¸ÊÝ É ÔØ¶À : hl=(hl+2)
	PUSH	HL
	POP	IX	;IX := string descriptor
	LD	L,(IX+2)	;get value(low)
	LD	H,(IX+3)	;get value(high)
; <--
	LD	B,32
	OTIR
	EI
	RET
;

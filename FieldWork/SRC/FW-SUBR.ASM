;-- KANJI EDITOR "FIELD WORK" --

;    SUB RUTINES 1 (CONTROL)

;      _SAVE("FW-SUBR

TA_HEAD:	EQU		08000H+1		;add HOF
TA_SIZE:	EQU		PROHEAD-TA_HEAD-2		;add EOF*2

;--- ASCII CONTROL CODE ---
;CTRL_E		EQU		5	; ^E
BS:			EQU		8	; ^H [BS]
TAB:		EQU		9	; ^I [TAB]
LF:			EQU		10	; ^J [LF]
HOME:		EQU		11	; ^K [HOME]
CLS:		EQU		12	; ^L [CLS]
CR:			EQU		13	; ^M [CR]
INS:		EQU		18	; ^R [INS]
SELECT:		EQU		24	; ^X [SELECT]
EOF:		EQU		1AH	; ^Z [EOF] (26)
ESC:		EQU		27	; ^[ [ESC]
RIGHT:		EQU		28	; ^\ [RIGHT]
LEFT:		EQU		29	; ^] [LEFT]
UP:			EQU		30	; ^^ [UP]
DOWN:		EQU		31	; ^_ [DOWN]
DEL:		EQU		127	; [DEL]

HOF:		EQU		0FFH	; HEAD of FILE

;--- BIOS ---
BEEP:		EQU		00C0H

;--- SCREEN CONSTANT ---
LINOVER:	EQU		255		; 255
NOLINE:		EQU		255

;--- WORK AREA ---
CUR_AXS:	DW		0		;CURSOL(X,Y) BUCK UP
TD_MODE:	DW		0		;MODE(0:OVER WRITE/1:INSERT)
TD_YNOW:	DW		0		;Y NOW(SCR. TOP LINE)
TD_YMAX:	DW		0		;Y MAX
TD_MSIZ:	DW		0		;MEM_SIZE
TD_EOFS:	DW		0		;EOF OFFSET FROM END OG FILE (FOOTER SIZE)
TD_LIN:		DS		36		;3*12 : Address(2) + WIDTH(1)
MJD_HED:	DW		0		;ONE LINE BUF
MJD_XMX:	DB		0		;ONE LINE BUF X MAX

;-- KEY BUF CLEAR --
KEYCLR:	LD		HL,(0F3F8H)
		LD		(0F3FAH),HL
		RET
;-- INPUT TYPE 2 (UPPER CASED) --
INPUT2:	CALL	INPUT
		CP		'a'
		RET		C
		CP		'z'+1
		RET		NC
		SUB		20H
		RET

;- GET LINE DATA-
; IN | ---
; OUT| DE:ADDRESS
; OUT| A:X MAX
; USE| AF,DE,HL
GETYLIN:
		LD		A,(CUR_AXS+1)
		LD		L,A
		SRL		A
GYLIN_:	ADD		A,L		;A+A\2
		LD		HL,TD_LIN
		ADD		A,L
		LD		L,A
		JR		NC,GYLIN__
		INC		H
GYLIN__:
		LD		E,(HL)
		INC		HL
		LD		D,(HL)
		INC		HL
		LD		A,(HL)
		RET

;--- CALC.RUTINES ---
GETYNOW:
		LD		A,(CUR_AXS+1)
		SRL		A
CALYNOW:
		LD		HL,(TD_YNOW)
ADDHLA:	ADD		A,L
		LD		L,A
		RET		NC
		INC		H
		RET
ADDDEA:	ADD		A,E
		LD		E,A
		RET		NC
		INC		D
		RET
SUBHLA:	NEG
		ADD		A,L
		LD		L,A
		RET		C
		DEC		H
		RET
GET_ADT:
		ADD		A,L
		LD		L,A
		JR		NC,GETADT_
		INC		H
GETADT_:
		LD		E,(HL)
		INC		HL
		LD		D,(HL)
		EX		DE,HL
		RET

;--- INFOMATION ---
CLR_INF:
		CALL	PAGE1
		LD		DE,1C20H
		CALL	VSETW
		LD		A,' '
		LD		BC,2098H
L_CLRIF:
		OUT		(C),A
		DJNZ	L_CLRIF
		JP		PAGE0
STR_INF:
		CALL	PAGE1
		LD		DE,1C20H+7
		CALL	VSETW
		LD		C,98H
L_STRIF:
		LD		A,(HL)
		INC		HL
		CP		'@'
		JP		Z,PAGE0
		OUT		(C),A
		JP		L_STRIF

PUT_INF:
		CALL	PAGE1
		LD		DE,1C20H
		CALL	VSETW
		LD		HL,INFO_MS
		LD		C,98H
		OUTI
		OUTI
		EX		DE,HL
		LD		HL,(CUR_AXS)
		LD		H,0
		CALL	PUT_D2	;X
		LD		A,'/'
		OUT		(98H),A
		PUSH	DE
		CALL	GETYLIN
		LD		(PTINF0+1),DE	;ADR.
		LD		(PTINF1+1),A	;X-MAX
		LD		L,A
		LD		H,0
		CALL	PUT_D2	;MAX X
		POP		DE
		CALL	INFOMES
		CALL	GETYNOW
		CALL	PUT_D5
		LD		A,'/'
		OUT		(98H),A
		LD		HL,(TD_YMAX)
		CALL	PUT_D5
		CALL	INFOMES
		CALL	INFOMES
		LD		HL,(TD_MSIZ)
		CALL	PUT_D5
; JP PAGE0

		LD		DE,1C40H
		CALL	VSETW
PTINF0:	LD		HL,0	;ADR. dummy
PTINF1:	LD		D,0		;X-MAX dummy
		LD		A,(CUR_AXS)
		CP		D
		JR		Z,PTINF_
		JR		NC,PTINFX
PTINF_:	CALL	ADDHLA
		LD		A,(HL)
		CALL	PUT_NB
		LD		DE,1C40H+30
		CALL	VSETW
		INC		HL
		LD		A,(HL)
		CALL	PUT_NB
		JP		PAGE0
PTINFX:	; NO DATA
		LD		A,'-'
		OUT		(98H),A
		NOP
		OUT		(98H),A
		LD		DE,1C40H+30
		CALL	VSETW
		LD		A,'-'
		OUT		(98H),A
		NOP
		OUT		(98H),A
		JP		PAGE0

INFOMES:
		EX		DE,HL
		LD		C,98H
		OUTI
		OUTI
		OUTI
		EX		DE,HL
		RET
INFO_MS:
		DB		'X: Y: SIZE:'	;*DM*


;--- PRINT ERROR ---
ERROR_W:
		PUSH	AF
		CALL	GETERMA
		CALL	ERROR_S
		POP		AF
		CP		11
		JP		NZ,JEMODE_
		LD		HL,BINARYD
		CALL	ERROR_S
		JP		JEMODE_
ERROR_S:
		PUSH	HL
		LD		HL,ERRORMC
		CALL	STBSET
		LD		A,'$'
		LD		(STB_FLG+1),A
		POP		HL
		CALL	STBSET
		XOR		A
		LD		(STB_FLG+1),A
		CALL	KEYCLR
		CALL	BEEP
		CALL	INPUT
		RET

GETERMA:
		LD		D,A
		INC		D
		LD		HL,ERROR_M
		LD		A,'$'
		LD		BC,0
L_GERMA:
		CPIR
		DEC		D
		RET		Z
		JP		L_GERMA
ERRORMC:
		DB		12,26,C_EROR,0
BINARYD:
		DB		'先頭0000:終了0000:開始0000$'	;*DM*
ERROR_M:	; (ｴﾗｰ ﾒｯｾｰｼﾞ28ﾓｼﾞ ﾏﾃﾞ)
		DB		'$'	;*DM*
		DB		'指定された行がありません$'		; 0 ;*DM*
		DB		'ﾃｷｽﾄ領域が満杯です$'			; 1 ;*DM*
		DB		'中止されました$'				; 2 ;*DM*
		DB		'3$'	;*DM*
		DB		'4$'	;*DM*
		DB		'5$'	;*DM*
		DB		'6$'	;*DM*
		DB		'7$'	;*DM*
		DB		'指定ﾌｧｲﾙが存在しません$'		; 8 ;*DM*
		DB		'ﾌｧｲﾙｻｲｽﾞが異常です$'			; 9 ;*DM*
		DB		'ﾃﾞｨｽｸ容量が満杯です$'			; 10 ;*DM*
		DB		'これはBSAVEﾌｧｲﾙです$'			; 11 ;*DM*
		DB		'これはBASICﾌﾟﾛｸﾞﾗﾑです$'		; 12 ;*DM*
		DB		'指定ﾌｧｲﾙが大き過ぎます$'		; 13 ;*DM*
		DB		'FATが破壊されています$'		; 14 ;*DM*
		DB		'ﾌﾟﾛﾃｸﾄﾉｯﾁを開けて下さい$'		; 15 ;*DM*
		DB		'ﾃﾞｨｽｸが入っていません$'		; 16 ;*DM*
		DB		'ﾃﾞｰﾀ が 異常です:CRCｴﾗｰ$'		; 17 ;*DM*
		DB		'記憶装置が不調です:SEEKｴﾗｰ$'	; 18 ;*DM*
		DB		'ﾚｺｰﾄﾞが存在しません$'			; 19 ;*DM*
		DB		'ﾌｫｰﾏｯﾄ形式 が 違います$'		; 20 ;*DM*
		DB		'書き込みが正常に出来ません$'	; 21 ;*DM*
		DB		'原因不明のｴﾗｰです$'			; 22 ;*DM*
		DB		'ﾌｧｲﾙ名が不正です$'				; 23 ;*DM*

;----- DATA CONTROL -----

;---  GO NEXT LINE ---
; IN | HL:ADDRESS
; OUT| A :255  (NO LINE)
;    |    0-31 (LAST X)
;    | B :0-31 (LAST X)
;    | HL:ADDRESS

LINFWD:	LD		A,(HL)
		CP		EOF
		LD		A,255
		RET		Z
		CALL	LINTES_
		PUSH	HL
		CALL	LINTES_
		POP		HL
		LD		A,B
		RET

;--- GO BACK LINE ---
; IN  | HL:ADDRESS
; OUT | A :255   (NO LINE)
;     |    00-31 (LAST X)
;     | B  00-31 (LAST X)
;     | HL:ADDRESS
;     | Zf:1 (NORMAL LINE)
;     |    0 (ZENKAKU BREAK 31)
; USE | AF',AF,BC,DE,HL

LINREV:	LD		D,H
		LD		E,L
		CALL	LINREV_
		LD		A,255
		RET		Z
LLNREVL:
		LD		(LNREV1E+1),HL
		CALL	LINTES_

		LD		C,A
		EX		AF,AF'

		OR		A
		SBC		HL,DE
		JP		NC,LNREV1E

		ADD		HL,DE
		JP		LLNREVL
LNREV1E:
		LD		HL,0		;dummy
		
		PUSH	AF
		LD		A,C
		CP		EOF			;END LINE
		JR		Z,LINRV1C	;RETRY
		POP		AF

		JR		Z,LNREV1F	;END=SRC
		JP		LINREV
LNREV1F:
		EX		AF,AF'
		LD		A,B
		RET
LINRV1C:
		POP		AF
		JR		LINREV

;--- SKIP LINE FORWARD 2 ---
; IN  | HL:ADDRESS
;     | DE:LINE COUNT
; OUT | HL:ADDRESS
;     | DE:REST COUNT
; USE | AF,BC,DE,HL

LINFWD2:
		LD		A,E
		OR		D
		RET		Z
		CALL	LINTES_
		CP		EOF
		RET		Z
		DEC		DE
		JP		LINFWD2

;<--- NORMAL VER (SLOW)
;--- SKIP LINE REVERSE 2 ---
; IN  | HL:ADDRESS
;     | DE:LINE COUNT
; OUT | HL:ADDRES
;     | DE:REST COUNT
; USE | AF,BC,DE,HL,DE

LINREV2:
		LD		A,E
		OR		D
		RET		Z
		PUSH	DE
		CALL	LINREV
		POP		DE
		INC		A
		RET		Z	;HOF
		DEC		DE
		JP		LINREV2
;<---
;<--- LITTLE FAST VER
;;--- SKIP LINE REVERSE 2 ---
;; IN  | HL:ADDRESS
;;     | DE:LINE COUNT
;; OUT | HL:ADDRES
;;     | DE:REST COUNT
;; USE | AF,BC,DE,HL,DE'HL'
;
;LINREV2:
;		PUSH	DE
;		LD		D,H
;		LD		E,L
;		CALL	LINREV_
;		JP		Z,LNREV2E
;		LD		(LNREV2A+1),HL
;		EXX
;		LD		DE,1
;		EXX
;LNREV2T:
;		CALL	LINTES_
;;<---
;;		CP		EOF			;ERROR (bad eof)
;;		JR		Z,LNREV2_	;ｹｯｷｮｸ ﾊﾞｸﾞﾙ(Yｶﾞ ｲｼﾞｮｳ ﾆ)
;;--->
;		OR		A
;		SBC		HL,DE
;		JR		NC,LNREV2_
;		ADD		HL,DE
;		EXX
;		INC		DE
;		EXX
;		JP		LNREV2T
;LNREV2_:
;		EXX
;		POP		HL
;		OR		A
;		SBC		HL,DE
;		EX		DE,HL
;LNREV2A:
;		LD		HL,0		;ﾀﾞﾐｰ
;		JP		Z,LNREV2B
;		JP		NC,LINREV2
;LNREV2B:
;		DEC		DE
;		LD		A,E			; NEG DE
;		CPL
;		LD		E,A
;		LD		A,D
;		CPL
;		LD		D,A
;LREV2BL:
;		LD		A,D
;		OR		E
;		RET		Z
;		CALL	LINTES_
;		DEC		DE
;		JP		LREV2BL
;LNREV2E:
;		POP		DE
;		RET
;--->

;--- LINE TEST SUB ---
; IN  | HL:ADDRESS
; OUT | B :0-31 (LAST X)
;     | A :0-31 (END CODE)
;     |    255 (WIDTH OVER)
;     | Zf:1 (NORMAL LINE)
;     |    0 (ZENKAKU BREAK)
; USE | AF,BC,HL

LINTES_:
		LD		B,0
LINTE_L:
		LD		A,(HL)
		CP		TAB
		JP		NZ,LITS
		LD		A,' '
LITS:	CP		EOF
		RET		Z			;Zf=ON
		INC		HL
		CP		LF
		RET		Z
		CP		CR
		JP		Z,LITS_C	;Zf=ON
		CP		' '
		JR		C,LINTE_L
		INC		B
		CP		DEL
		JR		C,LITS_H	;HANLAKU
		CP		0A0H
		JR		C,LITS_Z	;ZENKAKU
		CP		0E0H
		JR		C,LITS_H	;HANKAKU
LITS_Z:	LD		A,(HL)		;ZENKAKU
		CP		' '
		JR		C,LITS		;CONTROL CODE
		INC		B
		INC		HL
LITS_H:	LD		A,B
		CP		SCWIDTH
		JP		C,LINTE_L
		DEC		B
		CP		SCWIDTH		;LAST_X 31 / 32 bytes
		LD		A,255
		RET		Z			;Zf=ON / LAST X = 31
		DEC		B			;LAST_X 31 / 30 bytes
		DEC		HL
		DEC		HL			;ADDRESS - 2
		RET					;Zf=OFF (DEC B -> 31)
LITS_C:	INC		HL
		RET					;Zf=ON

;-SEARCH REVERSE to LF or HoF -
; IN  | HL:ADDRESS
; OUT | HL:ADDRESS
;     | Zf:0(FOUND)
;     |    1(NO LINE)
; USE | AF,BC,DE,HL

LINREV_:
		DEC		HL
		LD		A,(HL)
		INC		HL
		CP		HOF
		RET		Z
		DEC		HL
LLREV_:	DEC		HL
		LD		A,(HL)
		CP		HOF
		JR		Z,WLREV_
		CP		LF
		JR		NZ,LLREV_
WLREV_:	INC		HL
		OR		H
		RET

;--- COUNT LINES (MAX) ---
; OUT | (TD_YMAX):Y LIMIT
;     | HL: [EOF] offset from end of file
; USE | AF,BC,DE,HL

LINTES0:
		LD		HL,TA_HEAD
		LD		DE,-1
LNTES0_:
		CALL	LINTES_
		INC		DE
		CP		EOF
		JR		NZ,LNTES0_
LNTES0W:
		LD		(TD_YMAX),DE
		
		LD		DE,TA_HEAD
		OR		A
		SBC		HL,DE
		
		LD		DE,(TD_MSIZ)
		OR		A
		SBC		HL,DE

		INC		HL
;		LD		(TD_EOFS),HL
		RET

;--- COUNT LINE (to CR LF CODE) ---
; IN  | HL:ADDRESS
; OUT | DE:LINE COUNT
; USE | AF,BC,DE,HL

LINTES1:
		LD		DE,-1
LNTES1_:
		CALL	LINTES_
		INC		DE
		INC		A
		JP		Z,LNTES1_
		RET

;--- MAKE 12 LINE DATA
; IN  | HL:ADDRESS
; OUT | (TD_LIN):DATAS
; USE | AF,BC,DE,HL

MAKLINE:
		LD		DE,TD_LIN
		LD		B,12
L_MAKLN:
		EX		DE,HL
		LD		(HL),E
		INC		HL
		LD		(HL),D
		INC		HL
		EX		DE,HL
		PUSH	BC
		CALL	LINTES_
		CP		EOF
		JR		Z,E_MAKLN
		LD		A,B
		LD		(DE),A
		INC		DE
		POP		BC
		DJNZ	L_MAKLN
		RET
E_MAKLN:
		LD		A,B
		LD		(DE),A
		POP		BC
		XOR		A
LEMAKLN:
		INC		DE
		INC		DE
		INC		DE
		LD		(DE),A
		DJNZ	LEMAKLN
		RET

;--- OUTPUT NUMBER RUTINES ---
;--- HEX.NUM. (2byte) ---
; IN  | HL: HEX.NUMBER
;     | DE: dest adr.(RAM mode)
PUT_N:	LD		A,H
		CALL	PUT_NB
		LD		A,L

;--- HEX.NUM. (1byte) ---
; IN  | A: HEX.NUMBER
;     | DE: dest adr.(RAM mode)
PUT_NB:	LD		B,A
		RRCA
		RRCA
		RRCA
		RRCA
		CALL	PUT_NH
		LD		A,B
PUT_NH:	AND		15
		CP		10
		JR		C,PUTN
		ADD		A,7

;--- PUT NUM. (1byte CODE) ---
; IN  | A : decimal number
;     | DE: dest adr.(RAM mode)
PUTN:	ADD		A,'0'
PUT_MD:	JP		PUT_NV	;ow: PUT_NV/PUT_NM
PUT_NV:	OUT		(98H),A
		RET
PUT_NM:	LD		(DE),A
		INC		DE
		RET

;--- OUTPUT MODE CHANGE ---
; PUT NUM to VRAM
PUTM_V:	LD		HL,PUT_NV
		LD		(PUT_MD+1),HL
		RET
; PUT NUM to RAM(DE)
PUTM_M:	LD		HL,PUT_NM
		LD		(PUT_MD+1),HL
		RET

;--- PUT NUMBER (DECIMAL)
;  IN  | HL:HEX.NUMBER
;      | DE:dest adr.(RAM mode)
;  OUT | (OUT):BCD DATA
;  USE | AF,BC,HL

PUT_D5:	LD		BC,10000
		CALL	PUTD_
PUT_D4:	LD		BC,1000
		CALL	PUTD_
PUT_D3:	LD		BC,100
		CALL	PUTD_
PUT_D2:	LD		BC,10
		CALL	PUTD_
		LD		A,L
		JP		PUTN
PUTD_:	XOR		A
PUTBCD:	SBC		HL,BC
		JR		C,PUTBCE
		INC		A
		JP		PUTBCD
PUTBCE:	ADD		HL,BC
		JP		PUTN

;--- RAM BACK UP TO VRAM --
; IN  | A:BANK No.(0-5)
; OUT | Cy: 1(BACKED UP)
;     |     0(FAULT)

MEMSAVE:
		ADD		A,2
		CP		8
		RET		NC
		DI
		OUT		(99H),A
		LD		A,14+80H
		OUT		(99H),A
		XOR		A
		OUT		(99H),A
		LD		A,40H
		OUT		(99H),A
		EI

		PUSH	DE
		LD		HL,8000H
		LD		DE,PROHEAD-8000H
		LD		C,98H
L_MEMS:	OUTI
		DEC		DE
		LD		A,D
		OR		E
		JP		NZ,L_MEMS
		POP		DE
		JP		PAGE0

;--- RAM RESTORE FROM VRAM --
; IN  | A:BANK No.(0-5)
; OUT | Cy: 1(RESTORED)
;     |     0(FAULT)

MEMLOAD:
		ADD		A,2
		CP		8
		RET		NC
		DI
		OUT		(99H),A
		LD		A,14+80H
		OUT		(99H),A
		XOR		A
		OUT		(99H),A
		XOR		A
		OUT		(99H),A
		EI

		PUSH	DE
		LD		HL,8000H
		LD		DE,PROHEAD-8000H
		LD		C,98H
L_MEML:	INI
		DEC		DE
		LD		A,D
		OR		E
		JP		NZ,L_MEML
		POP		DE
		JP		PAGE0

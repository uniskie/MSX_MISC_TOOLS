;-- KANJI EDITOR "FIELD WORK" --

;    SUB RUTINES 2 (FUNCTION)

;      _SAVE("FW-FUNC


;--- INPUT STR WORK AREA---
INSTRMD:	DB		0	; 1 = NUMBER ONLY

;--- INPUT STR ---
INPSTR:	LD		HL,M_INSTR
		CALL	STBSET
		LD		HL,STR
		LD		DE,STR+1
		LD		BC,STRSIZ
		LD		(HL),' '
		LDIR
		LD		HL,STR+STRSIZ
		LD		(HL),24
		LD		E,0
		LD		HL,STR
		JR		LEINSTR

L_INSTR:
		CALL	INPUT2
		CP		ESC
		JR		Z,ESINSTR
		CP		CR
		JR		Z,E_INSTR
		CP		DEL
		JR		Z,D_INSTR
		CP		BS
		JR		Z,INSTRBS
		CP		RIGHT
		JR		Z,I_INSTR
		CP		LEFT
		JR		Z,INSTRLF
;<---
		LD		B,A
		LD		A,(INSTRMD)
		OR		A
		LD		A,B
		JR		Z,N_INSTR
		
		CP		'0'
		JR		C,L_INSTR
		CP		'9'
		JR		NC,L_INSTR
		
N_INSTR:
;--->
		CALL	KANJI_F
		JP		C,L_INSTR
		LD		(HL),A
I_INSTR:
		LD		A,E
		CP		STRSIZ-1
		JR		NC,LEINSTR
		INC		E
		INC		HL

LEINSTR:
		LD		A,E
		ADD		A,6+1
		LD		(STR+STRSIZ+1),A
		PUSH	HL
		PUSH	DE
		LD		HL,M_STR
		CALL	STBSET
		POP		DE
		POP		HL
		JR		L_INSTR

E_INSTR:
		CALL	JEMODE_
		LD		HL,STR
		RET
ESINSTR:
		CALL	JEMODE_
		LD		HL,EOFF
		RET

INSTRLF:
		CALL	R_INSTR
		JP		LEINSTR
INSTRBS:
		CALL	R_INSTR
		JP		D_INSTR
R_INSTR:
		LD		A,E
		OR		A
		RET		Z
		DEC		E
		DEC		HL
		RET
D_INSTR:
		PUSH	HL
		PUSH	DE
		LD		A,STRSIZ
		SUB		E
		LD		C,A
		LD		B,0
		LD		E,L
		LD		D,H
		INC		HL
		LDIR
		LD		A,' '
		LD		(STR+STRSIZ-1),A
		POP		DE
		POP		HL
		JP		LEINSTR

;--- TEXT CLEAR & PRINT Etc.
TXCLEAR:
		LD		HL,TA_HEAD-1
		LD		(HL),HOF
		INC		HL
		LD		(HL),EOF
		LD		BC,1
		LD		(TD_MSIZ),BC
		CALL	LINTES0

;--- PRINT & MAKE LINE (HEAD)
TX_HEAD:
		CALL	CD_CLS
		LD		HL,TA_HEAD
		CALL	MAKLINE
		LD		A,12
		CALL	LFSET
		LD		DE,TA_HEAD
		CALL	PRINT
		CALL	LFRSET
		LD		HL,0
		LD		(TD_YNOW),HL
		LD		(CUR_AXS),HL
		RET

;--- PRINT & MAKE LINE (TAIL)
TX_TAIL:
		CALL	CD_CLS
		LD		HL,(TD_MSIZ)
		LD		DE,(TD_EOFS)
		ADD		HL,DE		;(HL) = EOF
		LD		DE,TA_HEAD-1
		ADD		HL,DE
		LD		DE,11
		CALL	LINREV2
TXTAILE:
		LD		BC,(TD_YMAX)
		LD		A,C
		OR		B
		JR		Z,TXTAIE_
		LD		A,E
		SUB		11
		ADD		A,C
		LD		C,A
		JR		C,TXTAIE_
		DEC		B
TXTAIE_:
		LD		(TD_YNOW),BC
		PUSH	HL
		CALL	MAKLINE
		LD		A,12
		POP		DE
		CALL	LFSET
		CALL	PRINT
		CALL	LFRSET
		LD		HL,0
		LD		(CUR_AXS),HL
		RET

;--- NEXT LINE (UP)
TX_SCRU:
		LD		HL,(TD_YNOW)
		LD		A,H
		OR		L
		RET		Z
		DEC		HL
		LD		(TD_YNOW),HL
		LD		HL,TD_LIN+35-3
		LD		DE,TD_LIN+35
		LD		BC,36-3
		LDDR
		LD		HL,(TD_LIN)
		CALL	LINREV
		LD		A,B
		LD		(TD_LIN),HL
		LD		(TD_LIN+2),A
		EX		DE,HL
		CALL	SCRL_DW
		LD		HL,0
		LD		(PR_AXS),HL
		LD		A,1
		CALL	LFSET
		CALL	PRINT
		CALL	LFRSET
		RET

;--- NEXT LINE (DOWN)
TX_SCRD:
		LD		A,11
		CALL	CALYNOW
		LD		DE,(TD_YMAX)
		OR		A
		SBC		HL,DE
		RET		Z
		LD		HL,(TD_YNOW)
		INC		HL
		LD		(TD_YNOW),HL
		LD		HL,TD_LIN+3
		LD		DE,TD_LIN
		LD		BC,36-3
		LDIR
		LD		HL,(TD_LIN+36-3)
		CALL	LINFWD
		LD		A,B
		LD		(TD_LIN+36-3),HL
		LD		(TD_LIN+36-1),A
		EX		DE,HL
		CALL	SCRL_UP
		LD		H,UD_SCR
		LD		L,0
		LD		(PR_AXS),HL
		LD		A,1
		CALL	LFSET
		CALL	PRINT
		CALL	LFRSET
		RET

;--- SKIP TO NEXT SCREEN(HEAD)
TX_SKPU:
		LD		HL,(TD_LIN)
		LD		DE,12
		CALL	LINREV2
		PUSH	DE
		CALL	MAKLINE
		POP		DE
		LD		A,12
		SUB		E
		RET		Z
		LD		B,A
		LD		HL,(TD_YNOW)
		ADD		HL,DE
		LD		DE,-12
		ADD		HL,DE
		LD		(TD_YNOW),HL
L_TXSKU:
		PUSH	BC
; XOR A
; LD (TIMERC),A
		CALL	SCRL_DW
		LD		HL,0
		LD		(PR_AXS),HL
; POP BC
; PUSH BC
		LD		A,B
		ADD		A,A
		ADD		A,B
		LD		HL,TD_LIN-3
		CALL	ADDHLA
		LD		E,(HL)
		INC		HL
		LD		D,(HL)
		LD		A,1
		CALL	LFSET
		CALL	PRINT
;WTSKPU LD A,(TIMERC)
; CP 1
; JP C,WTSKPU
		POP		BC
		DJNZ	L_TXSKU
		JP		LFRSET

;--- SKIP TO NEXT SCREEN(TAIL)
TX_SKPD:
		LD		A,11
		CALL	CALYNOW
		LD		DE,(TD_YMAX)
		OR		A
		SBC		HL,DE
		RET		NC
		LD		A,L
		LD		DE,12
		ADD		HL,DE
		JP		NC,TXSKPD
		NEG
		LD		E,A
		LD		D,0
TXSKPD:	LD		HL,(TD_LIN)
		PUSH	DE
		CALL	LINFWD2
		CALL	MAKLINE
		POP		DE
		LD		B,E
		LD		HL,(TD_YNOW)
		ADD		HL,DE
		LD		(TD_YNOW),HL
L_TXSKD:
		PUSH	BC
; XOR A
; LD (TIMERC),A
		CALL	SCRL_UP
		LD		H,UD_SCR
		LD		L,0
		LD		(PR_AXS),HL
; POP BC
; PUSH BC
		LD		A,B
		ADD		A,A
		ADD		A,B
		LD		HL,TD_LIN+36
		CALL	SUBHLA
		LD		E,(HL)
		INC		HL
		LD		D,(HL)
		LD		A,1
		CALL	LFSET
		CALL	PRINT
;WTSKPD LD A,(TIMERC)
; CP 1
; JP C,WTSKPD
		POP		BC
		DJNZ	L_TXSKD
		JP		LFRSET

;--- LINE SEARCH
; INP| DE:LINE SEARCH NUMBER

TX_LINE:
		LD		HL,(TD_YMAX)
		LD		BC,11
		OR		A
		SBC		HL,BC
		EX		AF,AF'
		ADD		HL,BC
		EX		AF,AF'
		JP		NC,TXLIN_
		LD		B,E
		SLA		B
		LD		C,0
		LD		DE,0
		JP		TXLINE
TXLIN_:	SBC		HL,DE
		LD		A,0
		JP		C,ERROR_W
		LD		A,H
		OR		A
		JR		NZ,TXLINE
		LD		A,L
		CP		11-1
		JR		NC,TXLINE
		NEG
		ADD		A,11
		LD		C,0		;CURSOL X
		RLA
		LD		B,A		;CURSOL Y
		LD		HL,(TD_YMAX)
		LD		DE,-11
		ADD		HL,DE
		EX		DE,HL
TXLINE:	LD		HL,TA_HEAD
		LD		(TD_YNOW),DE
		PUSH	BC
L_TXLIN:
		LD		A,D
		OR		E
		JR		Z,E_TXLIN
		CALL	LINTES_
		DEC		DE
		JP		L_TXLIN
E_TXLIN:
		CALL	MAKLINE
		CALL	CD_CLS
		LD		DE,(TD_LIN)
		LD		A,12
		CALL	LFSET
		CALL	PRINT
		CALL	LFRSET
		POP		HL
		LD		(CUR_AXS),HL
		RET

;;--- HELP MODE ---
;HELP_PG:	DW	M_HELP
;TX_HELP:
;		LD		DE,M_HELP
;TX_HEL_:
;		LD		(HELP_PG),DE
;		CALL	CD_CLS
;		LD		A,C_MENU
;		LD		(SPCFLG),A
;		CALL	KANJI_C
;		CALL	PRINT
;		XOR		A
;		LD		(SPCFLG),A
;		LD		HL,161EH
;		LD		(PR_AXS),HL
;		LD		A,C_EROR
;		CALL	KANJI_C
;
;L_HELP:	CALL	INPUT2
;		CALL	KANJI_F
;		JP		C,L_HELP2
;L_HELP2:
;;		LD		HL,HELPCHG
;;		CP		' '
;;		JP		Z,E_HELP
;		LD		HL,TX_FILE
;		CP		13
;		JP		Z,E_HELP
;		LD		HL,CSLFILE
;		CP		27
;		JP		Z,E_HELP
;		LD		HL,HELPCHG
;;		JP		L_HELP
;E_HELP:	PUSH	HL
;		CALL	COLFLOD
;		POP		HL
;		JP		(HL)
;HELPCHG:
;		LD		HL,(HELP_PG)
;		LD		DE,M_HELP2
;		OR		A
;		SBC		HL,DE
;		JR		C,TX_HEL_
;		ADD		HL,DE
;		LD		DE,M_HELP3
;		OR		A
;		SBC		HL,DE
;		JR		C,TX_HEL_
;		LD		DE,M_HELP
;		JR		TX_HEL_
;
;M_HELP:
;		DB		'HELP (PAGE 1/3)'	;*DM*
;		DB		CR,LF,CR,LF	;*DM*
;		DB		'[ESC]   メニュー表示／キャンセル'	;*DM*
;		DB		'[SELECT](CTRL+X)  MSX-JEのON/OFF'	;*DM*
;		DB		'[INS]        挿入/上書き切り替え'	;*DM*
;		DB		'[DEL]   カーソル位置の１文字削除'	;*DM*
;		DB		'[BS]    カーソル手前の１文字削除'	;*DM*
;		DB		'[CTRL+E]    カーソルより右を削除'	;*DM*
;		DB		CR,LF	;*DM*
;		DB		'* ﾌｧｲﾙ名入力時 *'	;*DM*
;		DB		CR,LF	;*DM*
;		DB		'[ﾌｧｲﾙ名無しでRETURN]    ﾌｧｲﾙ一覧'	;*DM*
;		DB		'- PUSH SPACE -'	;*DM*
;		DB		0
;M_HELP2:
;		DB		'HELP (PAGE 2/3)'	;*DM*
;		DB		CR,LF,CR,LF	;*DM*
;		DB		'[HOME]          先頭ページを表示'	;*DM*
;		DB		'[SHIFT+HOME]    最終ページを表示'	;*DM*
;		DB		'[CTRL+上]       前のページを表示'	;*DM*
;		DB		'[CTRL+下]       次のページを表示'	;*DM*
;		DB		'[CTRL+左]             行頭へ移動'	;*DM*
;		DB		'[CTRL+右]             行末へ移動'	;*DM*
;		DB		CR,LF	;*DM*
;		DB		'[SHIFT+ESC]       エディタを終了'	;*DM*
;		DB		CR,LF	;*DM*
;		DB		'- PUSH SPACE -'	;*DM*
;		DB		0
;M_HELP3:
;		DB		'HELP (PAGE 3/3)'	;*DM*
;		DB		CR,LF,CR,LF	;*DM*
;		DB		'* MSX-JE 入力時 *'	;*DM*
;		DB		CR,LF	;*DM*
;		DB		'[SPACE]             変換・次候補'	;*DM*
;		DB		'[SHIFT+SPACE]             前候補'	;*DM*
;		DB		'[F1]          ローマ字・英数切替'	;*DM*
;		DB		'[F2]            全角カタカナ変換'	;*DM*
;		DB		'[F3]            半角カタカナ変換'	;*DM*
;		DB		'[F4](数字4文字+F4) JISコード変換'	;*DM*
;		DB		'[F5][RETURN]                確定'	;*DM*
;		DB		'[かな]        ローマ字・かな切替'	;*DM*
;		DB		'- PUSH SPACE -'	;*DM*
;		DB		0


;-*- tab-width: 8 -*-
;================================
;  GET USR(INT)
;================================
; USE:	F,IX,HL
; RET:	HL=VAL
;	Z=OK/NZ=ERROR
GETINT: ;
	CP	2
	RET	NZ
;
; --> �Ƿ �� ����� Ӽ��� ���ڽ ��ĸ
; LD HL,(0F7F8H)
; <--
; --> ø�� � �ض� : hl=(hl+2)
	PUSH	HL
	POP	IX		;(IX+2) = INT VALUE
	LD	L,(IX+2)	;get value(low)
	LD	H,(IX+3)	;get value(high)
; <--
	RET


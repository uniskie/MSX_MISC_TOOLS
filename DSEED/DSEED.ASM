;*TAB 4*
;----------------------------------
		FNAME	"DSEED.BIN"		;*BINHEAD*
;--> BIN FILE HEADER -->
		DB		$FE		;*BINHEAD*
		DW		ORGADR	;*BINHEAD*
		DW		ENDFL-1	;*BINHEAD*
		DW		ORGADR	;*BINHEAD*
;<-- BIN FILE HEADER <--

ORGADR:	EQU		$C000
		ORG		ORGADR

;--- jump table for USR()
		JP		DS_INIT
		JP		DS_MAIN
;---

;---- CONSTANT VALUES
;STAR 
;{
OFS_STAR_X:			EQU	0	;		BYTE X
OFS_STAR_Y:			EQU	1	;		BYTE Y
OFS_STAR_V:			EQU	2	;		BYTE V
OFS_STAR_C:			EQU	3	;		BYTE COLOR + ORIGINAL COLOR * 16
STAR_STRUCT_SIZE:	EQU	4
;}
STAR_COUNT:			EQU	64
STAR_WORK_SIZE:		EQU	STAR_STRUCT_SIZE * STAR_COUNT

;======================================
;---- INITIALIZE
;======================================
DS_INIT:
;	-- INIT RAND
		LD		A,R
;		LD		(RNDL_LAST+1),A	; "RAND.ASM"
		LD		(RNDK_LAST+1),A	; "RAND.ASM"
		
		CALL	INIT_STAR_WORK
		RET

;======================================
;---- NAIN
;======================================
DS_MAIN:
		CALL	STAR_MOVE
;		CALL	WAIT_VDPC
		RET
		
;======================================
;---- INITIALIZE STAR WORK
;======================================
INIT_STAR_WORK:
;	-- INITIALIZE STAR WORK
		LD		B,STAR_COUNT
		LD		HL,STAR_WORK
DS_INIT_L:
;X=RND(255)
		EXX
		CALL	RNDK
		LD		A,H
		EXX
		LD		(HL),A			;X=RND(255)
		INC		HL
;Y=RND(211)
;211=127+63+15+3+3
		EXX
		CALL	RNDK
		LD		A,H
		AND		127
		LD		C,A				;C=RND(127)
		LD		A,L
		AND		63
		ADD		A,C
		EXX
		LD		C,A				;C=RND(127)+RND(63)
		EXX
		CALL	RNDK
		LD		A,H
		AND		15
		LD		C,A				;C=RND(15)
		LD		A,L
		AND		3
		ADD		A,C
		LD		C,A				;C=RND(15)+RND(3)
		LD		A,L
		RRCA
		RRCA
		AND		3
		ADD		A,C				;A=RND(15)+RND(3)+RND(3)
		EXX
		ADD		A,C				;A=RND(127)+RND(63)+RND(15)+RND(3)+RND(3)
		LD		(HL),A			;Y=RND(211)
		INC		HL
;V=RND(7)
		EXX
		CALL	RNDK
		LD		A,H
		EXX
		AND		7
		INC		A
		LD		(HL),A			;X=RND(255)+1
		INC		HL
;C=(RND(5)+5) + 16
;5=3+1+1
		EXX
		CALL	RNDK
		LD		A,H
		AND		3				;A=RND(3)
		RL		H
		ADC		A,0				;A=RND(3)+RND(1)
		RL		H
		ADC		A,15H			;A=(RND(3)+RND(1)+RND(1)+5) + 16
		EXX
		LD		(HL),A			;C=(RND(5)+5) + 16
		INC		HL
;		
		DJNZ	DS_INIT_L
		RET

;======================================
;---- MOVE STARS
;======================================
STAR_MOVE:
		LD		B,STAR_COUNT
		LD		IX,STAR_WORK
		LD		DE,STAR_STRUCT_SIZE

STAR_MOVE_L:
; RESTORE COLOR
		LD		A,(IX+OFS_STAR_C)
		RLCA
		RLCA
		RLCA
		RLCA
		AND		0FH
		JR		NZ,STAR_MOVE_V

		CALL	WAIT_VDPC
		XOR		A
		CALL	DS_PSET				;PSET(X,Y,0),0

STAR_MOVE_V:
; Y=Y+V
		LD		A,(IX+OFS_STAR_Y)
		SUB		(IX+OFS_STAR_V)
; IF Y<0 THEN Y=Y+212
		JR		NC,STAR_MOVE_D
		ADD		A,212
		EX		AF,AF'
		EXX
		CALL	RNDK
		LD		(IX+OFS_STAR_X),A	;X=RND(255)
		EXX
		EX		AF,AF'
STAR_MOVE_D:
		LD		(IX+OFS_STAR_Y),A
; (STAR_C)=POINT(X,Y,1)*16+COLOR
		CALL	WAIT_VDPC
		CALL	DS_POINT
		RLCA
		RLCA
		RLCA
		RLCA						;A=ORG_COLOR*16
		LD		C,A
		LD		A,(IX+OFS_STAR_C)
		AND		0FH
		OR		C
		LD		(IX+OFS_STAR_C),A	;COLOR+ORG_COLOR*16

		LD		A,C
		OR		A
		JR		NZ,STAR_MOVE_NX

; IF ORG_COLOR THEN PSET(X,Y,0),C
		LD		A,(IX+OFS_STAR_C)
		AND		0FH
		CALL	DS_PSET				;PSET(X,Y,0),C
;
STAR_MOVE_NX:
		ADD		IX,DE				;IX=IX+STAR_STRUCT_SIZE
		DJNZ	STAR_MOVE_L

		RET

;======================================
;--- MAIN WORK
;======================================
STAR_WORK:
		DS		STAR_WORK_SIZE


;======================================
;--- POINT
; IN:	IX=STAR_WORK
; OUT:	A=COLOR
; USE:	AF
;======================================
DS_POINT:
		PUSH	BC
		PUSH	HL

;		CALL	WAIT_VDPC

; SET POINT CMD
		LD		A,(VDPIOW)
		LD		C,A
		INC		C

		LD		A,VDPR_SX		;R#32
		DI
		OUT		(C),A
		LD		A,VDPR_IND+80H	;Continuous write
		OUT		(C),A
		
		INC		C
		INC		C
		
		LD		A,(IX+OFS_STAR_X)
		OUT		(C),A			;SX #R32
		XOR		A
		OUT		(C),A			;SX #R33

		LD		A,(IX+OFS_STAR_Y)
		OUT		(C),A			;SY #R34
		LD		A,1				;PAGE=1
		OUT		(C),A			;SY #R35
		
		DEC		C
		DEC		C

		XOR		A				;ARG=0
		OUT		(C),A
		LD		A,VDPR_ARG+80H	;ARG #45
		OUT		(C),A
		LD		A,CMRPOINT		;CMR=POINT
		OUT		(C),A
		LD		A,VDPR_CMR+80H	;CMR #46
		OUT		(C),A
		EI

; WAIT CMD
		CALL	WAIT_VDPC2
		
; READ COLOR
		LD      A,VDPS_CLR		;S#7
		DI
		OUT     (C),A
		LD      A,8FH			;S#n READ SET
		OUT     (C),A
		IN      A,(C)			;A=S#7=COLOR
		LD		L,A				;L=COLOR

		XOR		A				;S#0
		OUT     (C),A
		LD      A,8FH			;S#n READ SET
		OUT     (C),A
		EI
		
		LD		A,L				;A=COLOR
		POP		HL
		POP		BC
		RET

;======================================
;--- PSET
; IN:	IX=STAR_WORK
; 		A=COLOR
; USE:	AF
;======================================
DS_PSET:
		PUSH	BC
		PUSH	HL
		
		PUSH	AF			;(SP)=COLOR
		
;		CALL	WAIT_VDPC
		
; SET PSET CMD
		LD		A,(VDPIOW)
		LD		C,A
		INC		C

		XOR		A				;ARG=0
		LD		A,VDPR_DX		;R#36
		DI
		OUT		(C),A
		LD		A,VDPR_IND+80H	;Continuous write
		OUT		(C),A

		INC		C
		INC		C
		
		LD		A,(IX+OFS_STAR_X)
		OUT		(C),A			;SX #R36
		XOR		A
		OUT		(C),A			;SX R#37
		LD		A,(IX+OFS_STAR_Y)
		OUT		(C),A			;SY #R38
		XOR		A				;PAGE=0
		OUT		(C),A			;SY R#39
		
		DEC		C
		DEC		C

		POP		AF				;COLOR=(SP)
		OUT		(C),A
		LD		A,VDPR_CLR+80H	;CLR #44
		OUT		(C),A
		XOR		A				;ARG=0
		OUT		(C),A
		LD		A,VDPR_ARG+80H	;ARG #45
		OUT		(C),A
		LD		A,CMR_PSET		;CMR=PSET
		OUT		(C),A
		LD		A,VDPR_CMR+80H	;CMR #46
		OUT		(C),A
		EI

;		CALL	WAIT_VDPC
		
		POP		HL
		POP		BC
		RET

;======================================
;--- wait until vdp-command finish
; USE:	AF,AF',C
; OUT:	C=(VDPIOR)+1 ... always 99H
;======================================
WAIT_VDPC:
		LD		A,(VDPIOR)
		LD		C,A
		INC		C
WAIT_VDPC2:
		LD		A,VDPS_S2		;S#2
		DI
		OUT		(C),A
		LD		A,VDPR_STA+80H	;Set status register number
		OUT		(C),A
WAIT_VDPC_:
		IN		A,(C)
		EX		AF,AF'
		XOR		A				;S#0
		OUT		(C),A
		LD		A,VDPR_STA+80H	;Set status register number
		OUT		(C),A
		EI						;use EI
		EX		AF,AF'
		RRCA					;Cy=CE bit
		JR		C,WAIT_VDPC2	;use EI
;		JR		C,WAIT_VDPC_	;no EI
		RET

;================================
;  RANDOM KUROSAWA-SHIKI for byte
;================================
; USE:	AF,HL,DE
; RET:	HL=RND
;
RNDK:
;
RNDK_INIV:		EQU	$123
RNDK_XORH:		EQU $96
RNDK_XORL:		EQU $30
RNDK_SUBV:		EQU $6553
;
;		HL=HL XOR $9630
		LD		A,(RNDK_LAST)
		XOR		A,RNDK_XORL
		LD		L,A
		LD		A,(RNDK_LAST+1)
		XOR		A,RNDK_XORH
		LD		H,A
;		HL=HL - $6553
		LD		DE,RNDK_SUBV
		SBC		HL,DE
;		HL= (HL<<2) | (HL>>14)
		LD		A,H
		RLCA
		RL		L
		RL		H
		RLCA
		RL		L
		RL		H
		LD		(RNDK_LAST),HL
		RET

RNDK_LAST:
		DW		RNDK_INIV

;======================================
;--- INCLUDE
		INCLUDE	"VDPCMD_D.ASM"
;======================================

ENDFL:

;*TAB 4*
;================================
; (from BASIC) USR CALL hra BGM DRIVER
;================================
;ENTRY:
;		bgmdriver_initialize
;		bgmdriver_play					;[HL]...DATA
;		bgmdriver_stop
;		bgmdriver_check_playing			;Z ... STOP
;		bgmdriver_fadeout				;A ... SPEED
;		bgmdriver_play_sound_effect		;[HL] ... DATA
;		bgmdriver_mute_psg
;		bgmdriver_interrupt_handler		; CALL from H.TIMI

;================================
;--- INITIALIZE BGM DRIVER ---
;================================
; U=USR(1)  : INSTALL BGM DRIVER
; U=USR(OTHER) : UNINSTALL BGM DRIVER
BGM_INIT:
		CALL	GETINT
		LD		A,L
		CP		1
		JR		Z,BGM_INSTALL
		JR		BGM_UNINSTALL

BGM_INSTALL:
		CALL	bgmdriver_initialize

		LD		A,(HTIMI_BGM)
		OR		A
		RET		NZ

		DI
		LD		HL,H_TIMI
		LD		DE,HTIMI_BGM
		LD		BC,5
		LDIR

		LD		HL,JP_BGM_HTIMI
		LD		DE,H_TIMI
		LD		BC,3
		LDIR
		EI
		RET

JP_BGM_HTIMI:
		JP		bgmdriver_interrupt_handler

BGM_UNINSTALL:
		CALL	bgmdriver_stop
		CALL	bgmdriver_mute_psg
		
		LD		A,(HTIMI_BGM)
		OR		A
		RET		Z
		
		DI
		LD		HL,HTIMI_BGM
		LD		DE,H_TIMI
		LD		BC,5
		LDIR

		XOR		A
		LD		(HTIMI_BGM),A
		EI
		RET

HTIMI_BGM:
		DS		5		;H.TIMI backup


;================================
;--- PLAY BGM ---
;================================
; A=USR(ADDRESS)
BGM_PLAY:
		CALL	GETINT
		RET		NZ
		JP		bgmdriver_play

;================================
;--- PLAY BGM ---
;================================
; A=USR()
BGM_STOP:
		JP		bgmdriver_stop

;================================
;--- PLAY SOUND EFFECT ---
;================================
; A=USR(ADDRESS)
BGM_SE:
		CALL	GETINT
		RET		NZ
		JP		bgmdriver_play_sound_effect


;================================
;--- FADE OUT BGM ---
;================================
; A=USR(SPEED)
BGM_FADEOUT:
		CALL	GETINT
		RET		NZ
		LD		A,L
		JP		bgmdriver_fadeout

;================================
;--- IS PLAYING? ---
;================================
; A=USR(0)
;	A>0 ... PLAYING
BGM_IS_PLAY:
		CALL	GETINT
		RET		NZ

		PUSH	IX	;(IX+2) = INT VALUE
		CALL	bgmdriver_check_playing
		LD		HL,0
		JR		NZ,BGM_IS_STOP
		INC		HL
BGM_IS_STOP:
		LD		(IX+2),L
		LD		(IX+3),H
		RET

;		INCLUDE	"USR_FUNC.ASM"
		INCLUDE "BGMDRV.ASM"

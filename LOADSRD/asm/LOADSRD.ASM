;-*- tab-width: 8 -*-
;----------------------------------
; GRAPH SAURUS DATA LOADER
;  + PALETTE SET
;  + VDP COMMAND
;----------------------------------
; 256 byte * n line ÃÞ¼®Ø»ÚÙ
; SCREEN5 Ê line½³ ÊÝÌÞÝ‚Å¼®Ø
;----------------------------------
	FNAME	"LOADSRD.BIN"	;*BINHEAD*
;--> BIN FILE HEADER -->
	DB	0FEH		;*BINHEAD*
	DW	ORGADR		;*BINHEAD*
	DW	ENDFL-1		;*BINHEAD*
	DW	ORGADR		;*BINHEAD*
;<-- BIN FILE HEADER <--

DMAADR:	EQU	0B000H
ORGADR:	EQU	0D000H
	ORG	ORGADR

;--- jump table for USR()
	JP	LOAD_SRD	;"GSF_LOAD.ASM"
	JP	SET_PLT		;"GSF_LOAD.ASM"
;	JP	SPR_TIME	;"SPRCLOCK.ASM"
;	JP	VDPCMD		;"VDPCOMAN.ASM"
;	JP	WAITVDPC	;"VDPCOMAN.ASM"
;	JP	SPR_SET		;"SPR_SET.ASM"
;	JP	SPC_SET		;"SPR_SET.ASM"
;	JP	SPR_INT		;"SPR_SET.ASM"

;--- work area for LOAD_SRD
LOADOFS:	DW	0	;LOAD_SRD VRAM offset

; read buffer:
DMA:		DW	DMAADR		;Read buffer address
DMASIZ:		DW	ORGADR-DMAADR	;Read buffer size

	INCLUDE	"GSF_LOAD.ASM"	;*FILE*
	INCLUDE	"VRAMFUNC.ASM"	;*FILE*
	INCLUDE	"USR_FUNC.ASM"	;*FILE*
;	INCLUDE "VDPCOMAN.ASM"	;*FILE*
;	INCLUDE "SPRCLOCK.ASM"	;*FILE*
;	INCLUDE "SPR_SET.ASM"	;*FILE*

ENDFL:


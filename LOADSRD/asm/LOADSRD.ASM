;*TAB 4*
;----------------------------------
; GRAPH SAURUS DATA LOADER
;  + PALETTE SET
;  + VDP COMMAND
;----------------------------------
; 256 byte * n line ?޼?ػ??
; SCREEN5 ? line?? ????݂ż??
;----------------------------------
		FNAME	"LOADSRD.BIN"	;*BINHEAD*
;--> BIN FILE HEADER -->
		DB		0FEH	;*BINHEAD*
		DW		ORGADR	;*BINHEAD*
		DW		ENDFL-1	;*BINHEAD*
		DW		ORGADR	;*BINHEAD*
;<-- BIN FILE HEADER <--


ORGADR:		EQU		0D000H
		ORG		ORGADR

;--- jump table for USR()
		JP		LOAD_SRD	;"GSF_LOAD.ASM"
		JP		SET_PLT		;"GSF_LOAD.ASM"
;		JP		SPR_TIME	;"SPRCLOCK.ASM"
;		JP		VDPCMD		;"VDPCOMAN.ASM"
;		JP		WAITVDPC	;"VDPCOMAN.ASM"
;		JP		SPR_SET		;"SPR_SET.ASM"
;		JP		SPC_SET		;"SPR_SET.ASM"
;		JP		SPR_INT		;"SPR_SET.ASM"

;--- work area for LOAD_SRD
LOADOFS:	DW		0			;LOAD_SRD VRAM offset
; read buffer:	B000H-CFFFH
DMA:		DW		0B000H		;Read buffer address
DMASIZ:		DW		2000H		;Read buffer size

		INCLUDE	"GSF_LOAD.ASM"	;*FILE*
		INCLUDE	"VRAM.ASM"		;*FILE*
		INCLUDE	"USR_FUNC.ASM"	;*FILE*
;		INCLUDE "VDPCOMAN.ASM"	;*FILE*
;		INCLUDE "SPRCLOCK.ASM"	;*FILE*
;		INCLUDE "SPR_SET.ASM"	;*FILE*

ENDFL:

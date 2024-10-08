;-*- tab-width: 8 -*-
;----------------------------------
; GRAPH SAURUS DATA LOADER
;  + PALETTE SET
;  + VDP COMMAND
;  + CLOCK TO BUF
;  + SPRITE ENGINE
;  + HRA'S BGM DRIVER
;----------------------------------
; 256 byte * n line �޼�ػ��
; SCREEN5 � line�� ����݂ż��
;----------------------------------
	FNAME	"SRX3.BIN"	;*BINHEAD*
;--> BIN FILE HEADER -->
	DB	$FE	;*BINHEAD*
	DW	ORGADR	;*BINHEAD*
	DW	ENDFL-1	;*BINHEAD*
	DW	ORGADR	;*BINHEAD*
;<-- BIN FILE HEADER <--


DMAADR:	EQU	$B000
ORGADR:	EQU	$C000
	ORG	ORGADR

;--- jump table for USR()
	JP	LOAD_SRD	;00	UA+&H00	"GSF_LOAD.ASM"
	JP	SET_PLT		;01	UA+&H03	"GSF_LOAD.ASM"
	JP	SPR_TIME	;02	UA+&H06	"SPRCLOC2.ASM"
	JP	VDPCMD		;03	UA+&H09	"VDPCOMAN.ASM"
	JP	WAITVDPC	;04	UA+&H0C	"VDPCOMAN.ASM"
	JP	SPR_SET		;05	UA+&H0F	"SPR_SET.ASM"
	JP	SPC_SET		;06	UA+&H12	"SPR_SET.ASM"
	JP	SPR_INT		;07	UA+&H15	"SPR_SET.ASM"
	JP	BGM_INIT	;08	UA+&H18	"BGM.ASM"
	JP	BGM_PLAY	;09	UA+&H1B	"BGM.ASM"
	JP	BGM_STOP	;10	UA+&H1E	"BGM.ASM"
	JP	BGM_SE		;11	UA+&H21	"BGM.ASM"
	JP	BGM_FADEOUT	;12	UA+&H24	"BGM.ASM"
	JP	BGM_IS_PLAY	;13	UA+&H27	"BGM.ASM"

;--- work area for LOAD_SRD
LOADOFS:	DW	0	;LOAD_SRD VRAM offset
; read buffer:
DMA:		DW	DMAADR		;Read buffer address
DMASIZ:		DW	ORGADR-DMAADR	;Read buffer size

	INCLUDE	"GSF_LOAD.ASM"
	INCLUDE	"VRAMFUNC.ASM"
	INCLUDE	"USR_FUNC.ASM"
	INCLUDE	"VDPCOMAN.ASM"
	INCLUDE	"SPRCLOC2.ASM"
	INCLUDE	"SPR_SET.ASM"
	INCLUDE "BGM.ASM"

ENDFL:


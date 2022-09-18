;*TAB 4*
;================================
;---- VDP Command DEFINES----
;================================

; (rom address at I/O port number)
VDPIOR:		EQU		0006H	;VDP I/O port m (READ)
VDPIOW:		EQU		0007H	;VDP I/O port n (WRITE)

; (VDP Status Registers)
VDPS_S2:		EQU		2	;S#2  bit7=TransferReady / bit0=CommandExecuting
VDPS_CLR:		EQU		7	;S#7  Receive color fom command

; (VDP Control Registers)
VDPR_STA:		EQU		15	;R#15 Indirect access to VDP Status register
VDPR_IND:		EQU		17	;R#17 Indirect access to VDP regiseer

; (VDP Command Registers)
VDPR_SX:		EQU		32	;R#32,R#33 SX
VDPR_SY:		EQU		34	;R#34,R#35 SY
VDPR_DX:		EQU		36	;R#36,R#37 DX
VDPR_DY:		EQU		38	;R#38,R#29 DY
VDPR_NX:		EQU		40	;R#40,R#41 NX
VDPR_NY:		EQU		42	;R#42,R#43 NY
VDPR_CLR:		EQU		44	;R#44      COLOR
VDPR_ARG:		EQU		45	;R#45      ARGUMENT
VDPR_CMR:		EQU		46	;R#46      OPERATION


; (VDP Command Operation Code)
CMR_HMMC:		EQU		0F0H	;High  CPU->VRAM
CMR_YMMM:		EQU		0E0H	;YÎ³º³ VRAM->VRAM
CMR_HMMM:		EQU		0D0H	;High  VRAM->VRAM
CMR_HMMV:		EQU		0C0H	;High  fill VRAM
CMR_LMMC:		EQU		0B0H	;Logic CPU->VRAM
CMR_LMCM:		EQU		0A0H	;Logic VRAM->CPU
CMR_LMMM:		EQU		090H	;Logic VRAM->VRAM
CMR_LMMV:		EQU		080H	;Logic fill VRAM
CMR_LINE:		EQU		070H	;Draw Line
CMR_SRCH:		EQU		060H	;Search Color
CMR_PSET:		EQU		050H	;Write Pixel
CMRPOINT:		EQU		040H	;Read Pixel
CMR_STOP:		EQU		000H	;Stop Command

; (Logical Operation Code)
LOG_PSET:		EQU		0
LOG_AND:		EQU		1
LOG_OR:			EQU		2
LOG_XOR:		EQU		3
LOG_NOT:		EQU		4
LOG_TPSET:		EQU		8
LOG_TAND:		EQU		9
LOG_TOR:		EQU		10
LOG_TXOR:		EQU		11
LOG_TNOT:		EQU		12

; (ARGUMENT BITS)
;ARG : bit|__7|__6|__5|__4|__3|__2|__1|__0|
;		  | 0 | - |MXD|MXS|DIY|DIX| EQ|MAJ|
; MXD : DESTINATION ¶Þ ¶¸Á®³VRAM
; MXS : SORCE ¶Þ ¶¸Á®³VRAM
; DIY : 0:¼À   (Y) + NY
;		1:³´   (Y) - NY
; DIX : 0:Ð·Þ  (X) + NX
;		1:ËÀÞØ (X) - NX
; EQ  : (SEARCH) 1:·®³¶²¼®¸ ²¶Þ² ÃÞÓ ¼­³Ø®³
; MAJ : (LINE) 0:(NX > NY) ÖºÅ¶Þ
;			   1:(NX < NY) ÀÃÅ¶Þ
ARG_DIY:		EQU		08H
ARG_DIX:		EQU		04H
ARG_EQ:			EQU		02H
ARG_MAJ:		EQU		01H


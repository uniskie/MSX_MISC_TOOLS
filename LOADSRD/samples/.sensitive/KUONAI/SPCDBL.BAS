10 CLEAR1500,&HB000:DEFINTA-Z:DIM SC$(63)
20 SCREEN 0:WIDTH 40:O$="SPCDBL.BIN"
30 FILES:PRINT
40 PRINT"-- SPRITE COLOR TABLE DOUBLER"
50 PRINT"    for 99x8Edit VDP FILE"
60 INPUT"SPRITE COLOR file";F$
70 OPEN F$ FOR INPUT AS#1
80 FOR I=0 TO 63:SC$(I)=INPUT$(16,#1):NEXT:CLOSE #1
90 OPEN O$ FOR OUTPUT AS#1
100 FOR I=0 TO 63:PRINT#1,SC$(I);SC$(I);:NEXT:CLOSE #1
110 PRINT"> ";O$;" Í¤ ¼­ÂØ®¸ ¼Ï¼À¡"
120 PRINT
130 PRINT"*** ???.VDPÌ§²Ù É º³¿Þ³ **************
140 PRINT"  +1321H - 1B20H : SPRITE PATTERN
150 PRINT"  +1C21H - 2420H : SPRITE CHR COLOR
160 PRINT"                   (DOUBLED SIZE)
170 PRINT"**************************************
180 PRINT"  (";O$;" É Å¶Ð Ê 1C21H Í Íß°½Ä)"
190 PRINT
200 PRINT"* »²ºÞÉ EOF(1AH)Ê¤ ÖÌÞÝ ÅÉÃÞ"
210 PRINT"  ÄØÉ¿Þ²Ã ¶× VDPÌ§²Ù Æ ÊØÂ¹Ã ¸ÀÞ»²¡ *"



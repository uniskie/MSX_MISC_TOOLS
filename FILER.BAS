10 DEFINTA-Z:KEY7,CHR$(12)+"run"+CHR$(34)+"filer.bas"+CHR$(13)
20 WD=80:SCREEN0:WIDTHWD:KEYOFF:COLOR15,0,0:ONSTOPGOSUB700:STOPON
30 S$="A:":D$="B:":LOCATE0,0,0:PRINT"Filer v0.2      [Space]=Run / [N]=Rename / [C]=Copy / [A]=All Copy / [K]=Delete":PRINTSPC(24);"* Rename [ ��� ƭ�خ� ��� RETURN ] = �׶�� -> ���� �ݶ�"
40 ON ERROR GOTO 600:FILES:ON ERROR GOTO 0 'FILES"*":FILES"*.BAS":FILES"*.MUS"
50 AC=1:XM=WD\12:YY=CSRLIN-2:XX=XM-1:IF VPEEK(CSRLIN*WD)=32 THEN YY=YY-1
60 A$=INKEY$:IF A$="" THEN S=9 ELSE S=ASC(A$)-28
70 IF AC=1 AND(A$="A" OR A$="a")THEN S=10
80 S=S*AC:X=X+(S=1)-(S=0):Y=Y+(S=2 OR X<0)-(S=3 OR X>XX)
90 AC=AC OR(-(X>XX AND Y>YY)):X=(X-(X<0)*XM)*-(X<XM):Y=Y-(Y<0)+(Y>YY)
100 XP=X*13:YP=Y+2:FOR I=0 TO 12:LOCATE XP+I,YP,1:NEXT:LOCATE,,0
110 M=-STRIG(0)-2*(A$="N" OR A$="n")-4*(A$="C" OR A$="c")-8*(A$="K" OR A$="k")-16*(AC=0 OR S=10):IF M=0 THEN 60
120 F$="":AD=XP+(YP)*WD:FOR I=0 TO 11:F$=F$+CHR$(VPEEK(AD+I)):NEXT
130 LOCATE0,1,0:PRINTSPC(WD-1):IF S=10 THEN 400 ELSEIF LEFT$(F$,1)=" "OR MID$(F$,2,2)=":\" OR LEFT$(F$,1)="." OR INSTR(F$,"?")>0 THEN BEEP:GOTO 60
140 IF AC=0 THEN 450 ELSEIF M=2 THEN 200 ELSEIF M=4 THEN 350 ELSEIF M=8 THEN 500
150 '=== RUN
160 LOCATE 2,1,1:PRINT"Run "+CHR$(34)+F$+CHR$(34)+"  Ready?(Y/N)";:A$=INPUT$(1)
170 IF A$="N" OR A$="n" THEN PRINTA$;:BEEP:LOCATE0,1,0:PRINTSPC(WD-1):GOTO 60
180 IF A$="Y" OR A$="y" THEN PRINTA$;:LOCATE,,0:COLOR15,4,7:SCREEN1:RUN F$
190 GOTO 160
200 '=== RENAME FILE
210 LOCATE 2,1,1:PRINT"Rename "+CHR$(34)+F$+CHR$(34)+" > ";:LINEINPUT N$
220 IF N$="" THEN GOSUB 300
230 IF N$="" THEN BEEP:LOCATE0,1,0:PRINTSPC(WD-1):GOTO 60
240 N=INSTR(N$,".")
250 IF N THEN N$=LEFT$(N$,N+3) ELSE N$=LEFT$(N$,8)+MID$(F$,9,4)
260 LOCATE 2,1,1:PRINT"Rename "+CHR$(34)+F$+CHR$(34)+" > "+CHR$(34)+N$+CHR$(34)+" Ok?(Y/N)";:A$=INPUT$(1)
270 IF A$="N" OR A$="n" THEN PRINTA$:BEEP:LOCATE0,1,0:PRINTSPC(WD-1):GOTO 60
280 IF A$="Y" OR A$="y" THEN PRINTA$:LOCATE,,0:NAME F$ AS N$:GOTO 20
290 GOTO 260
300 '=== HIRAGANA TO KATAKANA
310 K$=F$:KH$="":FOR I=&H86 TO &H9F:KH$=KH$+CHR$(I):NEXT:FOR I=&HE0 TO &HFD:KH$=KH$+CHR$(I):NEXT:KK$="��������������������������������������������������������"
320 FOR I=1 TO 8:N=INSTR(KH$,MID$(F$,I,1)):IF N THEN MID$(K$,I,1)=MID$(KK$,N,1)
330 NEXT:IF F$<>K$ THEN N$=K$
340 RETURN
350 '=== COPY FILE
360 LOCATE 2,1,1:PRINT"Copy "+CHR$(34)+S$+F$+CHR$(34)+" to "+CHR$(34)+D$+F$+CHR$(34)+" Ready?(Y/N)";:A$=INPUT$(1)
370 IF A$="N" OR A$="n" THEN PRINTA$:BEEP:LOCATE0,1,0:PRINTSPC(WD-1):GOTO 60
380 IF A$="Y" OR A$="y" THEN PRINTA$:LOCATE0,1,0:COPY S$+F$ TO D$+F$:LOCATE0,1,0:PRINTSPC(WD-1):GOTO 60
390 GOTO 360
400 '=== ALL COPY START?
410 LOCATE 2,1,1:PRINT"All Copy "+S$+" to "+D$+" Ready?(Y/N)";:A$=INPUT$(1)
420 IF A$="N" OR A$="n" THEN PRINTA$:BEEP:LOCATE0,1,0:PRINTSPC(WD-1):GOTO 60
430 IF A$="Y" OR A$="y" THEN PRINTA$:AC=0:X=0:Y=0:LOCATE0,1,0:PRINTSPC(WD-1):GOTO 60
440 GOTO 410
450 '=== ALL COPY
460 LOCATE 2,1,1:PRINT"Copy "+CHR$(34)+S$+F$+CHR$(34)+" to "+CHR$(34)+D$+F$+CHR$(34);
470 LOCATE0,1,0:ON ERROR GOTO 600:COPY S$+F$ TO D$+F$:ON ERROR GOTO 0
480 LOCATE0,1,0:PRINTSPC(WD-1):GOTO 60
490 '
500 '=== DELETE FILE
510 LOCATE 2,1,1:PRINT"Delete "+CHR$(34)+S$+F$+CHR$(34)+"  Ready?(Y/N)";:A$=INPUT$(1)
520 IF A$="N" OR A$="n" THEN PRINTA$;:BEEP:LOCATE0,1,0:PRINTSPC(WD-1):GOTO 60
530 IF A$="Y" OR A$="y" THEN PRINTA$; ELSE 510
540 LOCATE 2,1,1:PRINT"Delete "+CHR$(34)+S$+F$+CHR$(34)+"  Really?(R/N)";:A$=INPUT$(1)
550 IF A$="N" OR A$="n" THEN PRINTA$;:BEEP:LOCATE0,1,0:PRINTSPC(WD-1):GOTO 60
560 IF A$="R" OR A$="r" THEN PRINTA$;:LOCATE0,1,0:KILL S$+F$:GOTO 20
570 GOTO 550
580 '
590 '
600 '=== ERROR CHECK SUB
610 ER=ERR:A$="":BEEP
620 IF ER=61 THEN A$="Bad File Mode (BASIÇ�� ���Ų)"
630 IF ER=69 THEN A$="Disk I/O Error (Disk�޵���)"
640 IF ER=70 THEN A$="Disk Offline (Disk��ʲ��Ų)"
650 IF ER=60 THEN A$="BadFat (FAT�޺��ò�)"
660 IF ER=53 THEN A$="File not Found (File��Ų)"
670 IF A$="" THEN ERROR ER ELSE RESUME 680
680 LOCATE 0,1,0:PRINTSPC(WD-1);:LOCATE 2,1,1:PRINTCHR$(34)+F$+CHR$(34)+" "+A$+" -Hit any key-";
690 A$=INPUT$(1):LOCATE0,1,0:PRINTSPC(WD-1):GOTO 60
700 '=== END
710 BEEP:LOCATE 0,22,0:END

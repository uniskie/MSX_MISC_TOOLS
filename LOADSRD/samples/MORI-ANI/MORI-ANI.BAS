1000 COLOR 15,0,0:VDP(9)=VDP(9)AND253
1010 '
1020 CLEAR 200,&HB000:DEFINT A-Z:SC=7
1030 DIM P(255),X(8,3),Y(8,3),A(3),W(3),AP(9,3),AF(3),VC(15,8,3)
1040 SCREEN SC:DEFUSR=&H156
1050 BLOAD"SRX.BIN"
1060 DEFUSR1=&HD000 'LOAD_SR
1070 DEFUSR2=&HD003 'SET_PAL
1080 DEFUSR3=&HD006 'TIMER SPRITE
1090 DEFUSR4=&HD009 'VDP COMMAND
1100 DEFUSR5=&HD00C 'VDP COMMAND WAIT
1110 F$="MORI-ANI"
1120 COPY F$+".PL7" TO P
1130 'FOR I=0TO7:P(I*16)=33:NEXT
1140 PN=0:GOSUB 2190
1150 SCREEN,2:BLOAD"TIME.SPR",S,&H7800
1160 SETPAGE0,1:A$=USR1(F$+".SR7"):SETPAGE0,0
1170 '
1180 '???? ??߰ ?? ? ??ˮ?
1190 OX=0:OY=0:SX=0:SY=0:SW=400:SH=212
1200 FOR I=0TO3
1210  READ X(0,I),Y(0,I)
1220  FOR J=1 TO 8
1230   READ X(J,I),Y(J,I)
1240   VC(0,J,I)=X(J,I):VC(1,J,I)=Y(J,I)+256 'SX,SY
1250   VC(2,J,I)=X(1,I)+OX:VC(3,J,I)=Y(1,I)+OY 'DX,DY
1260   VC(4,J,I)=X(0,I):VC(5,J,I)=Y(0,I) 'NX,NY
1270   VC(6,J,I)=0 'COLOR+ARG*256
1280   VC(7,J,I)=&HD0 'CMD HMMM
1290  NEXT
1300  READ A$,B$
1310  FOR J=0 TO 9
1320   AP(J,I)=VAL(MID$(A$,J+1,1))
1330  NEXT
1340 NEXT
1350 '     SIZE     ORG(0)  ANIME(1) ,2,3,4,5,6,7(X,Y)
1360 DATA  105,29,  250,80,  406,0, 406,32, 406,64, 406,96, 406,128, 0,0, 0,0
1370 DATA "1234543210",EYE
1380 DATA  37,19,  316,126,  406,160, 406,182, 0,0, 0,0, 0,0, 0,0, 0,0
1390 DATA "1012......",MOUTH
1400 DATA  21,11, 192,126,   448,160, 448,174, 448,188, 0,0, 0,0, 0,0, 0,0
1410 DATA "121030....",YIER RING
1420 DATA  00,00,   00,00,   0,0,  0,0, 0,0, 0,0, 0,0, 0,0, 0,0
1430 DATA "..........",-----
1440 '
1450 'CLOCK
1460 FOR I=0 TO 7:PUTSPRITE I,(186+I*8,0),10,15:COLORSPRITE$(I)=STRING$(4,15)+STRING$(4,12):NEXT
1470 '?Լ? ? ??ˮ?
1480 KX=40:KY=100
1490 PUTSPRITE 9,(KX,KY),13,12
1500 PUTSPRITE 8,(KX,KY),7,13
1510 PUTSPRITE 31,(KX,KY+2),15,14
1520 O1=52:O2=48:MF=56
1530 '
1540 ONINTERVAL=4 GOSUB 2080:GOSUB 2080
1550 '
1560 A$="t80l8s0m20000o5 ge-o4b-o5e- fb-4. fgfo4b-o5e-2"
1570 B$="t80l8v13o4 r4g4o5d4.o4f b-4 b-4 sm20000g2"
1580 PLAY A$,B$
1590 '
1600 '???? ??߰
1610 COPY (SX,SY)-(SX+SW-1,SY+SH-1),1 TO (OX,OY),0
1620 TM=TC:EF=((TM AND 32)>0)
1630 'VDP(26)=2
1640 '
1650 'MAIN LOOP
1660 'VS=(VS-1)AND255:VDP(27)=VS\8:VDP(28)=255-VS
1670 I$=INKEY$:A=USR(0)
1680 IF I$=" " THEN GOSUB 2150
1690 IF I$<>CHR$(13) THEN 1710
1700 O1=60+(O1=60)*8:O2=60+(O2=60)*12:VPOKE -1502,O1:VPOKE -1498,O2
1710 IF I$<>CHR$(11) THEN 1730
1720 MF=60+(MF=60)*4:VPOKE -1410,MF
1730 ' (ANIMATION)
1740 VPOKE -1412,KY+TF+TF+2
1750 VPOKE -1504,KY+TF+TF
1760 VPOKE -1500,KY+TF+TF
1770 TM=TC:EF=((TM AND 32)>0)
1780 IF TB=TM THEN 1860
1790 TB=TM
1800 TF=(TF+1)AND 3
1810 IF PC THEN PC=0:GOSUB 2150 '??گ? +1
1820 A=2:GOSUB 3210
1830 A=1:GOSUB 3110
1840 A=0:GOSUB 3010
1850 'A=3:GOSUB 1300
1860 GOTO 1650
1870 '
2000 '------ SUB COMMON
2010 '
2020 ' COPY
2030 U=USR4(VARPTR(VC(0,P+1,A)))
2040 'COPY (X(P+1,A),Y(P+1,A))-STEP(X(0,A),Y(0,A)),1 TO (X(1,A)+OX,Y(1,A)+OY),0
2050 RETURN
2060 '
2070 'TIMER
2080 INTERVAL OFF
2090 TC=(TC+1)AND 2047:IF (TC AND 511)= 0 THEN PC=1
2100 IF TC AND 7 THEN 2120
2110 U=USR3(0) 'TIME SPRITE
2120 INTERVAL ON
2130 RETURN
2140 '
2150 'PALETTE +1
2160 PN=(PN+1)AND7
2170 GOTO 2190
2180 '
2190 'PALETTE (PN=PALETTE NO)
2200 PJ=PN*16
2210 U=USR2(VARPTR(P(PJ)))
2220 RETURN
2230 '
2990 '-------SUB COMMON END
3000 '
3010 'EYES
3020 IF W(A) THEN W(A)=W(A)-1:RETURN
3030 P=AP(A(A),A)
3040 GOSUB 2030
3050 A(A)=A(A)+1:IF (A(A)<>5)AND(A(A)<>10) THEN 3070
3060 W(1)=0:W(A)=RND(3)*30+30
3070 IF A(A)<10 THEN RETURN
3080 A(A)=0
3090 RETURN
3100 '
3110 'MOUTH
3120 IF W(A) THEN W(A)=W(A)-1:RETURN
3130 P=AP(A(A),A)
3140 GOSUB 2000
3150 A(A)=A(A)+1
3160 IF A(A)=2 THEN W(A)=1
3170 IF (A(A)<4) THEN RETURN
3180 A(A)=0:W(A)=RND(3)*60+20
3190 RETURN
3200 '
3210 '???ݸ?
3220 'IF W(A) THEN W(A)=W(A)-1:RETURN
3230 P=AP(A(A),A)
3240 GOSUB 2000
3250 A(A)=A(A)+1
3260 IF A(A)<5 THEN 3280
3270 A(A)=0
3280 RETURN
3290 '

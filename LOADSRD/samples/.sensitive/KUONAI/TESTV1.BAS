1000 COLOR 15,13,0:VDP(9)=VDP(9)AND253':VDP(9)=VDP(9)OR2
1010 CLEAR 200,&HB000:DEFINT A-Z:SC=5:A=RND(-TIME)
1020 SCREEN SC':VDP(10)=VDP(10)AND 127'192 line mode
1030 FOR I=0TO14:COLOR=(I,0,0,0):NEXT
1040 AM=4:DIM A(AM),P(AM),W(AM),AP(15,AM),VC(7,8,AM)
1050 DEFUSR=&H156
1060 BLOAD"SRX3.BIN"
1061 UA=&HC000:DIM UA(14):FOR I=0 TO 14:UA(I)=UA+I*3:NEXT
1070 DEFUSR1=UA(0) 'LOAD_SRD
1080 DEFUSR2=UA(1) 'SET_PAL
1090 DEFUSR3=UA(2) 'TIMER SPRITE
1100 DEFUSR4=UA(3) 'VDP COMMAND
1110 DEFUSR5=UA(4) 'VDP COMMAND WAIT
1120 DEFUSR6=UA(5) 'SET SPRITE
1130 DEFUSR7=UA(6) 'SET SPRITE COLOR
1140 DEFUSR8=UA(7) 'SET SPRITE INTERRUPT
1150 'U=USR8(0) 'reset VSYNC sprite MODE
1160 ON STOP GOSUB 1170:STOP ON:ON ERROR GOTO 1170:GOTO 1180
1170 U=USR8(-1):STOPOFF:ONERRORGOTO0:END 'revove timer hook
1180 F$="KUONAI":F$=LEFT$(F$+SPACE$(8),8)
1190 DIM PL(255):COPY F$+".PL"+HEX$(SC) TO PL
1200 PL(0)=33:FOR I=1 TO 7:FOR J=0 TO 15:A=I*16+J:PL=PL(A-16):G=PL\256:R=(PL\16)AND 15:B=PL AND 15:B=(B-1)*-(B>0):R=(R-1)*-(R>0):G=(G-1)*-(G>0):PL(A)=B+R*16+G*256:NEXT:NEXT
1210 SETPAGE,2:CLS:SETPAGE,3:CLS
1220 SETPAGE0,1:A$=USR1(F$+".SR"+HEX$(SC)):SETPAGE0,0
1230 SCREEN,2:BLOAD"KUONAI.SPR",S,-(SC>6)*&H7800
1240 DIM SC(16*64):COPY"KUONAI.SPC"TO SC:U=USR7(VARPTR(SC(0))):ERASE SC
1250 U=USR8(1) 'set VSYNC sprite MODE1 (SLOW)
1251 'U=USR8(2) 'set VSYNC sprite MODE2 (FAST)
1260 '
1270 '���� ��߰ �� � ��ˮ�
1280 OX=32:OY=40:SX=0:SY=0:SW=192:SH=128:SP=256:BP=768*0:DX=OX-SX:DY=OY-SY
1290 '
1300 RESTORE 3310:XM=1-2*(SC<7)
1310 DIM CX(8,AM),CY(8,AM)
1320 FOR I=0 TO AM
1330  READ CX(0,I),CY(0,I)
1340  FOR J=1 TO 8
1350   READ CX(J,I),CY(J,I)
1360   VC(0,J,I)=CX(J,I):VC(1,J,I)=CY(J,I)+SP 'SX,SY
1370   VC(2,J,I)=CX(1,I)+OX:VC(3,J,I)=CY(1,I)+OY+BP 'DX,DY
1380   VC(4,J,I)=CX(0,I):VC(5,J,I)=CY(0,I) 'NX,NY
1390   VC(6,J,I)=0 'COLOR+ARG*SP
1400   L=(VC(0,J,I)OR VC(2,J,I)OR VC(4,J,I))AND XM
1410   IF L=0 THEN VC(7,J,I)=&HD0 'CMD HMMM
1420   IF L THEN VC(7,J,I)=&H90 'CMD LMMM
1430   'VC(7,J,I)=&H98 'CMD lMMM TPSET
1440  NEXT
1450  READ A$,B$
1460  FOR J=0 TO 15
1470   AP(J,I)=VAL(MID$(A$,J+1,1))
1480  NEXT
1490 NEXT
1500 ERASE CX,CY
1510 '
1520 DIM VD(7,7)
1530 A=0:VD(0,A)=0:VD(1,A)=192+SP:VD(2,A)=0:VD(3,A)=112+BP:VD(4,A)=16:VD(5,A)=16:VD(6,A)=0:VD(7,A)=&H98 'LMMM TPSET
1540 '
1550 DIM SR(4*32-1),S(31),X(8),Y(8),VX(8),VY(8)
1560 FORI=0TO31:S(I)=I*4:SR(S(I)+3)=-1:NEXT
1570 SS=8*(1-((VDP(1)AND 2)>0))*(1+(VDP(1)AND 1))
1580 MY=(212+((VDP(10)AND 127)=0)*20-SS)*2
1590 LX=(-SS)*2:MX=255*2
1600 '
1610 'CLOCK
1620 FOR I=0 TO 7:J=I*4
1630  'PUTSPRITE I,(132+I*12,16),2,15
1640  'COLORSPRITE$(I)=STRING$(4,10)+STRING$(4,12)
1650  SR(J)=MY:SR(J+1)=(256-(8*SS*8\16)+I*(SS\2))*2:SR(J+2)=15:SR(J+3)=0
1660 NEXT
1670 LINE(0,192)-(255,211),0,BF
1680 '
1690 '���
1700 X0=108*2:V0=2+RND(3)*3:Y0=MY-32:W0=-2-RND(3)*30
1710 N=8 :X=X0:Y=Y0:P=16:F=&H14:GOSUB 1980
1720 X1=10*2:V1=-2-RND(3)*3:Y1=MY-32:W1=-2-RND(3)*30
1730 N=10:X=X1:Y=Y1:P=24:F=&H14:GOSUB 1980
1740 X2=0+RND(3)*64:V2=8-RND(3)*16*2:Y2=MY:W2=4-RND(3)*8
1750 N=12:X=X2:Y=Y2:P=32:F=&H14:GOSUB 1980
1760 X3=64+RND(3)*64:V3=8-RND(3)*16*2:Y3=MY-64:W3=4-RND(3)*8
1770 N=14:X=X3:Y=Y3:P=40:F=&H14:GOSUB 1980
1780 X4=128+RND(3)*64:V4=8-RND(3)*16*2:Y4=MY-76:W4=4-RND(3)*8
1790 N=16:X=X4:Y=Y4:P=24:F=&H4:GOSUB 1980
1800 X5=192+RND(3)*64:V5=8-RND(3)*16*2:Y5=MY-64:W5=4-RND(3)*8
1810 N=18:X=X5:Y=Y5:P=12:F=&H4:GOSUB 1980
1820 '
1830 X6=256+RND(3)*64:V6=8-RND(3)*16*2:Y6=MY-76:W6=4-RND(3)*8
1840 N=20:X=X6:Y=Y6:P=56:F=&H12:GOSUB 1980
1850 X7=320+RND(3)*64:V7=8-RND(3)*16*2:Y7=MY-64:W7=4-RND(3)*8
1860 N=22:X=X7:Y=Y7:P=48:F=&H12:GOSUB 1980
1870 X8=96+RND(3)*64:V8=8-RND(3)*16*2:Y8=SS*2:W8=4-RND(3)*8
1880 N=24:X=X8:Y=Y8:P=56:F=&H12:GOSUB 1980
1890 X9=256+RND(3)*64:V9=8-RND(3)*16*2:Y9=SS*2:W9=4-RND(3)*8
1900 N=26:X=X9:Y=Y9:P=48:F=&H12:GOSUB 1980
1910 XA=380+RND(3)*64:VA=8-RND(3)*16*2:YA=SS*2:WA=4-RND(3)*8
1920 N=28:X=XA:Y=YA:P=40:F=&H12:GOSUB 1980
1930 XA=0+RND(3)*64:VA=8-RND(3)*16*2:YA=SS*2:WA=4-RND(3)*8
1940 N=30:X=XA:Y=YA:P=32:F=&H12:GOSUB 1980
1950 '
1960 GOTO 2020
1970 '
1980 J=S(N+0):SR(J)=Y:SR(J+1)=X:SR(J+2)=P+0:SR(J+3)=F
1990 J=S(N+1):SR(J)=Y:SR(J+1)=X:SR(J+2)=P+1:SR(J+3)=F
2000 RETURN
2010 '
2020 ONINTERVAL=8 GOSUB 2750:GOSUB 2750
2030 '
2040 A$="t80l8s0m20000o5 ge-o4b-o5e- fb-4. fgfo4b-o5e-2"
2050 B$="t80l8v13o4 r4g4o5d4.o4f b-4 b-4 sm20000g2"
2060 PLAY A$,B$
2070 '
2080 FORI=0TO7:J=(7-I)*32:U=USR2(VARPTR(PL(J))):NEXT
2090 '
2100 '���� ��߰
2110 'COPY (SX,SY)-(SX+SW-1,SY+SH-1),1 TO (OX,OY),0
2120 A=6:VD(0,A)=SX:VD(1,A)=SY+SP:VD(2,A)=OX:VD(3,A)=OY+BP:VD(4,A)=SW:VD(5,A)=SH:VD(6,A)=0:VD(7,A)=&HD0 'HMMM
2130 A=6:GOSUB 2720
2140 TM=TC:EF=((TM AND 32)>0)
2150 'VDP(26)=2
2160 '
2170 'MAIN LOOP
2180 'U=USR5(0)'WAIT VDP COMMAND
2190 I$=INKEY$:A=USR(0)
2200 TM=TC:EF=((TM AND 64)>0)
2210 'IF TB=TM THEN 2340
2220 TB=TM
2230 '
2240 ' (ANIMATION)
2250 '
2260  Y0=Y0+W0:W0=W0+1:IF Y0>MY THEN Y0=MY:W0=-16-RND(3)*16
2270  X0=X0+V0:IF(X0<LX)OR(X0>MX)THEN X0=X0-V0:V0=-V0
2280 '
2290  Y1=Y1+W1:W1=W1+1:IF Y1>MY THEN Y1=MY:W1=-16-RND(3)*16
2300  X1=X1+V1:IF(X1<LX)OR(X1>MX)THEN X1=X1-V1:V1=-V1
2310 '
2320 'ON TF GOTO 2130,2160,2190,2220:GOTO 2250
2330 '
2340  Y2=Y2+W2:W2=W2+1:IF Y2>MY THEN Y2=MY:W2=-16-RND(3)*16
2350  X2=X2+V2:IF(X2<LX)OR(X2>MX)THEN X2=X2-V2:V2=-V2':GOTO 2250
2360 '
2370  'Y3=Y3+W3:W3=W3+1:IF Y3>MY THEN Y3=MY:W3=-16-RND(3)*16
2380  'X3=X3+V3:IF(X3<LX)OR(X3>MX)THEN X3=X3-V3:V3=-V3':GOTO 2250
2390 '
2400  'Y4=Y4+W4:W4=W4+1:IF Y4>MY THEN Y4=MY:W4=-16-RND(3)*16
2410  'X4=X4+V4:IF(X4<LX)OR(X4>MX)THEN X4=X4-V4:V4=-V4':GOTO 2250
2420 '
2430  'Y5=Y5+W5:W5=W5+1:IF Y5>MY THEN Y5=MY:W5=-16-RND(3)*16
2440  'X5=X5+V5:IF(X5<LX)OR(X5>MX)THEN X5=X5-V5:V5=-V5':GOTO 2250
2450 '
2460 SR(32)=Y0:SR(36)=Y0:SR(33)=X0:SR(37)=X0'8*4=32
2470 SR(40)=Y1:SR(44)=Y1:SR(41)=X1:SR(45)=X1
2480 'ON TF GOTO 2254,2255,2256,2257:GOTO 2290
2490  SR(48)=Y2:SR(52)=Y2:SR(49)=X2:SR(53)=X2':GOTO 2290
2500  'SR(56)=Y3:SR(60)=Y3:SR(57)=X3:SR(61)=X3':GOTO 2290
2510  'SR(64)=Y4:SR(68)=Y4:SR(65)=X4:SR(69)=X4':GOTO 2290
2520  'SR(72)=Y5:SR(76)=Y5:SR(73)=X5:SR(77)=X5':GOTO 2290
2530 '
2540 TF=(TF+1)AND 7
2550 U=USR6(VARPTR(SR(0)))'SPRITE SET
2560 '
2570 A=0:GOSUB 2880
2580 A=1:GOSUB 2880
2590 A=2:GOSUB 2880
2600 A=3:GOSUB 2880
2610 A=4:GOSUB 2880
2620 '
2630 'U=USR3(VARPTR(SR(0))) 'TIME SPRITE
2640 GOTO 2180
2650 '
2660 '------ COMMON
2670 '
2680 ' COPY VC
2690 U=USR4(VARPTR(VC(0,P(A)+1,A))):RETURN
2700 '
2710 ' COPY VD
2720 U=USR4(VARPTR(VD(0,A))):RETURN
2730 '
2740 'TIMER
2750 INTERVAL OFF
2760 TC=(TC+1)AND 2047
2770 IF TC AND 3 THEN 2790
2780 U=USR3(VARPTR(SR(0))) 'TIME SPRITE
2790 INTERVAL ON
2800 RETURN
2810 '
2820 'PALETTE (PN=PALETTE NO)
2830 PJ=PN*16
2840 U=USR2(VARPTR(PL(PJ)))
2850 RETURN
2860 '
2870 '------- CUSTOMIZE
2880 ON A+1 GOTO 2910,2990,3070,3150,3230:RETURN
2890 '
2900 'EYES
2910 IF W(A) THEN W(A)=W(A)+(W(A)>0):RETURN
2920 P(A)=AP(A(A),A):GOSUB 2690
2930 A(A)=(A(A)+1) AND 15
2940 IF (A(A)AND 7)<>0 THEN 2960
2950 A(A)=-8*(RND(3)*10<8):W(A)=RND(3)*3
2960 RETURN
2970 '
2980 'MOUTH
2990 IF W(A) THEN W(A)=W(A)+(W(A)>0):RETURN
3000 P(A)=AP(A(A),A):GOSUB 2690
3010 A(A)=(A(A)+1)AND 15
3020 IF (A(A) AND 7)<>0 THEN W(A)=RND(3)*3:GOTO 3040
3030 A(A)=-8*(RND(3)*10<2):W(A)=(1+EF)*5+RND(3)*20
3040 RETURN
3050 '
3060 'BUSTR
3070 IF W(A) THEN W(A)=W(A)+(W(A)>0):RETURN
3080 P(A)=AP(A(A),A):GOSUB 2690
3090 A(A)=A(A)+1
3100 IF A(A)<4 THEN 3120
3110 A(A)=0:W(A)=RND(3)*(10-EF*20)
3120 RETURN
3130 '
3140 'BUSTL
3150 IF W(A) THEN W(A)=W(A)+(W(A)>0):RETURN
3160 P(A)=AP(A(A),A):GOSUB 2690
3170 A(A)=A(A)+1
3180 IF A(A)<4 THEN 3200
3190 A(A)=0:W(A)=RND(3)*(10-EF*20)
3200 RETURN
3210 '
3220 'HIP
3230 IF W(A) THEN W(A)=W(A)+(W(A)>0):RETURN
3240 P(A)=AP(A(A),A):GOSUB 2690
3250 A(A)=A(A)+1
3260 IF A(A)<4 THEN 3280
3270 A(A)=0:W(A)=10+RND(3)*60
3280 RETURN
3290 '
3300 '     SIZE     ORG     ANIME1,2,3,4,5,6,7(X,Y)
3310 DATA  24,20,   40,45,  0,128,   24,128,  48,128, 72,128, 0,0, 0,0, 0,0
3320 DATA "12310...40......","EYE"
3330 DATA  16,12,   44,80,  192,96,  208,96,  224,96, 240,96, 0,0, 0,0, 0,0
3340 DATA "21220...320.....","MOUTH"
3350 DATA  52,32,   24,96,  192,0,   192,32,  0,0, 0,0, 0,0, 0,0, 0,0
3360 DATA "1210............","BUSTR"
3370 DATA  68,54,   76,68,  112,132, 184,132, 0,0, 0,0, 0,0, 0,0, 0,0
3380 DATA "1210............","BUSTL"
3390 DATA  28,28,  164, 0,  196,64,  228,64, 0,0, 0,0, 0,0, 0,0, 0,0
3400 DATA "1210............","HIP"
3410 '
3420 ' MOVIN
3430 '
3440 '------ COMMON


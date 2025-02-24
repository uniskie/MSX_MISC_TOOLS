100 SCREEN 1:WIDTH 32:PRINT"WAIT"
110 CALL MUSIC(1,0,1,1,1) ' FMx3+RHYTHM+PSG
120 CLEAR 2000:DEFINT A-Z
130 DIM NA$(63),VA$(63), NB$(63),VB$(63),M$(1),V(16),R(7)
131 DIM LA$(63),LB$(63)
140 M$(0)="FS-A1GT"
150 M$(1)="FMPAC  "
160 RESTORE 1100:FOR I=0 TO 63:READ VA$(I),NA$(I),LA$(I):PRINT".";:NEXT
170 RESTORE 1200:FOR I=0 TO 63:READ VB$(I),NB$(I),LB$(I):PRINT".";:NEXT
180 '
220 M=0:S=0
230 '
240 CLS:PRINT"MSX-MUSIC ROM VOICE DATA TEST"
250 LOCATE 2,2:PRINT M$(M)
260 ON M GOTO 280
270 N$=NA$(S):V$=VA$(S):L$=LA$(S):GOTO 290
280 N$=NB$(S):V$=VB$(S):L$=LB$(S):GOTO 290
290 LOCATE 2,3:PRINT "@";HEX$(S\10);HEX$(S MOD10);" ";N$
291 LOCATE 0,4:PRINT SPACE$(31)
292 LOCATE 6,4:PRINT L$
300 GOSUB 800 ' SET VOICE
310 PLAY #2,"O4V15L4CDEl8FGABO5C&C2"
320 IF INKEY$<>"" THEN CALL STOPM
330 CALL PLAY(0,A):IF A THEN 320
340 S=(S+M)AND 63:M=1-M
350 GOTO 250
360 '
800 'SET VOICE - N$=NAME:V$=VOICE
810 FOR I=0 TO 7:R(I)=VAL("&H"+MID$(V$,I*2+1,2)):NEXT
820 FOR I=0 TO 7:POKE VARPTR(V(0))+I, ASC(MID$(N$,I+1,1)):NEXT
830 FOR I=0 TO 3
840  POKE VARPTR(V(0))+16+I,R(I*2)   ' CARRY
850  POKE VARPTR(V(0))+24+I,R(I*2+1) ' MODULETOR
860 NEXT
870 POKE VARPTR(V(0))+10,(R(3)AND7)*2 ' FB
880 CALL VOICE(V)
890 RETURN
988 '
989 ' ** VOICE REGISTER **
990 ' 0: (C) AM:PM:EG:KSR:MULTIPLE(4)
991 ' 1: (M) AM:PM:EG:KSR:MULTIPLE(4)
992 ' 2: (C) KS(2):TL(6)
993 ' 3: (M) KS(2):1:DC:DM:0:FB(3)
994 ' 4: (C) AR(4):DR(4)
995 ' 5: (M) AR(4):DR(4)
996 ' 6: (C) AL(4):RR(4)
997 ' 7: (M) AL(4):RR(4)
998 '
999 ' MSX-MUSIC BIOS (A1GT)
1100 DATA "11112020FFB2F4F4", "Piano 1 ", "Piano 1*"
1101 DATA "30102020FBB2F3F3", "Piano 2 ", "Piano 2"
1102 DATA "61612020B4561717", "Violin  ", "Violin*"
1103 DATA "3131202043432626", "Flute   ", "Flute 1*"
1104 DATA "A230202088540606", "Clarinet", "Clarinet*"
1105 DATA "3134202072561C1C", "Oboe    ", "Oboe*"
1106 DATA "7171202053522424", "Trumpet ", "Trumpet*"
1107 DATA "3430202050300606", "PipeOrgn", "Pipe Organ 1"
1108 DATA "FF522020D9D92424", "Xylophon", "Xylophone"
1109 DATA "63632020FCF82929", "Organ   ", "Organ*"
1110 DATA "41412020A3A30505", "Guitar  ", "Guitar*"
1111 DATA "53532020F5F50303", "Santool ", "Santool 1"
1112 DATA "23432920BFBF0505", "Elecpian", "Electric Piano 1*"
1113 DATA "03092020D2B4F5F5", "Clavicod", "Clavicode 1"
1114 DATA "01002020A3E2F4F4", "Harpsicd", "Harpsicode 1*"
1115 DATA "01012020C0B4F6F6", "Harpscd2", "Harpsicode 2"
1116 DATA "F1F12020D1D1F2F2", "Vibraphn", "Vibraphone*"
1117 DATA "11112020FCD28383", "Koto    ", "Koto 1"
1118 DATA "01102020CAE62424", "Taiko   ", "Taiko"
1119 DATA "E0F42020F1F00808", "Engine  ", "Engine 1"
1120 DATA "FF7020201F1F0101", "UFO     ", "UFO"
1121 DATA "11112020FAF2F4F4", "SynBell ", "Synthesizer bell"
1122 DATA "A6422020B9B90202", "Chime   ", "Chime"
1123 DATA "31312020F9F90404", "SynBass ", "Synthesizer bass*"
1124 DATA "4244202094B0F6F6", "Synthsiz", "Synthesizer*"
1125 DATA "03032020D9D90606", "SynPercu", "Synthesizer Percussion"
1126 DATA "40002020D9D90404", "SynRhyth", "Synthesizer Rhythm"
1127 DATA "03032020FFFF0606", "HarmDrum", "Harm Drum"
1128 DATA "18112020F5F52626", "Cowbell ", "Cowbell"
1129 DATA "0B042020F5F52727", "ClseHiht", "Close Hi-hat"
1130 DATA "40402020D0D62727", "SnareDrm", "Snare Drum"
1131 DATA "00012020E3E32525", "BassDrum", "Bass Drum"
1132 DATA "11110820FAB2F4F4", "Piano 3 ", "Piano 3"
1133 DATA "1111BD20C0B2F4F4", "Elecpia2", "Electric Piano 2*"
1134 DATA "1953FF20E7950303", "Santool2", "Santool 2"
1135 DATA "3070FF2042622424", "Brass   ", "Brass"
1136 DATA "6271252064432626", "Flute 2 ", "Flute 2"
1137 DATA "21032B2090D4F5F5", "Clavicd2", "Clavicode 2"
1138 DATA "01030A2090A4F5F5", "Clavicd3", "Clavicode 3"
1139 DATA "43530E20B5E98404", "Koto 2  ", "Koto 2"
1140 DATA "3430202050300606", "PipeOrg2", "Pipe Organ 2"
1141 DATA "33332020F5F51515", "PohdsPLA", "PohdsPLA"
1142 DATA "13133420F5F50303", "PohdsPRA", "RohdsPRA"
1143 DATA "6121202076540606", "Orch L  ", "Orch L"
1144 DATA "637020204B4B1515", "Orch R  ", "Orch R"
1145 DATA "A1A1202076540707", "SynViol ", "Synthesizer Violin"
1146 DATA "6178202085F20303", "SynOrgan", "Synthesizer Organ"
1147 DATA "31713520B6F92626", "SynBrass", "Synthesizer Brass"
1148 DATA "6171AD2075F20303", "Tube    ", "Tube*"
1149 DATA "030C1420A7FC1515", "Shamisen", "Shamisen"
1150 DATA "133220202085AFAF", "Magical ", "Magical"
1151 DATA "F131FF2023400909", "Huwawa  ", "Huwawa"
1152 DATA "F074B7205A43FCFC", "WnderFlt", "Wander Flat"
1153 DATA "20712020D5D50606", "Hardrock", "Hardrock"
1154 DATA "3032202040407474", "Machine ", "Machine"
1155 DATA "3032202040407474", "MachineV", "Machine V"
1156 DATA "0108202078F8F9F9", "Comic   ", "Comic"
1157 DATA "C8C02020F7F7F9F9", "SE-Comic", "SE-Comic"
1158 DATA "49402920F9F90505", "SE-Laser", "SE-Laser"
1159 DATA "CD422020A2F00101", "SE-Noise", "SE-Noise"
1160 DATA "5142202013100101", "SE-Star ", "SE-Star 1"
1161 DATA "5142202013100101", "SE-Star2", "SE-Star 2"
1162 DATA "3034202023700202", "Engine 2", "Engine 2"
1163 DATA "000020200000FFFF", "Silence ", "Silence"
1199 ' FM-PAC 
1200 DATA "31110E20D9B211F4", "Piano 1 ", "Piano 1*"
1201 DATA "30100F20D9B210F3", "Piano 2 ", "Piano 2"
1202 DATA "61611220B4561417", "Violin  ", "Violin*"
1203 DATA "613120206C431826", "Flute   ", "Flute 1*"
1204 DATA "A230A02088541406", "Clarinet", "Clarinet*"
1205 DATA "3134202072560A1C", "Oboe    ", "Oboe*"
1206 DATA "3171162051522624", "Trumpet ", "Trumpet*"
1207 DATA "3430372050307606", "PipeOrgn", "Pipe Organ 1"
1208 DATA "1752182088D96624", "Xylophon", "Xylophone"
1209 DATA "E1630A20FCF82829", "Organ   ", "Organ*"
1210 DATA "02411520A3A37505", "Guitar  ", "Guitar*"
1211 DATA "19530C20C7F51103", "Santool ", "Santool 1"
1212 DATA "23430920DDBF4A05", "Elecpian", "Electric Piano 1*"
1213 DATA "03091120D2B4F4F5", "Clavicod", "Clavicode 1"
1214 DATA "01000620A3E2F4F4", "Harpsicd", "Harpsicode 1*"
1215 DATA "01011120C0B401F6", "Harpscd2", "Harpsicode 2"
1216 DATA "F9F1242095D1E5F2", "Vibraphn", "Vibraphone*"
1217 DATA "13110C20FCD23383", "Koto    ", "Koto 1"
1218 DATA "01100E20CAE64424", "Taiko   ", "Taiko"
1219 DATA "E0F41B2011F00408", "Engine  ", "Engine 1"
1220 DATA "FF701920501F0501", "UFO     ", "UFO"
1221 DATA "13111120FAF221F4", "SynBell ", "Synthesizer bell"
1222 DATA "A6421020FBB91102", "Chime   ", "Chime"
1223 DATA "40318920C7F91404", "SynBass ", "Synthesizer bass*"
1224 DATA "42440B2094B033F6", "Synthsiz", "Synthesizer*"
1225 DATA "01030B20BAD92506", "SynPercu", "Synthesizer Percussion"
1226 DATA "40000020FAD93704", "SynRhyth", "Synthesizer Rhythm"
1227 DATA "02030920CBFF3906", "HarmDrum", "Harm Drum"
1228 DATA "18110920F8F52626", "Cowbell ", "Cowbell"
1229 DATA "0B040920F0F50127", "ClseHiht", "Close Hi-hat"
1230 DATA "40400720D0D60127", "SnareDrm", "Snare Drum"
1231 DATA "00010720CBE33625", "BassDrum", "Bass Drum"
1232 DATA "11110820FAB220F4", "Piano 3 ", "Piano 3"
1233 DATA "11111120C0B201F4", "Elecpia2", "Electric Piano 2*"
1234 DATA "19531520E7952103", "Santool2", "Santool 2"
1235 DATA "3070192042622624", "Brass   ", "Brass"
1236 DATA "6271252064431226", "Flute 2 ", "Flute 2"
1237 DATA "21030B2090D402F5", "Clavicd2", "Clavicode 2"
1238 DATA "01030A2090A403F5", "Clavicd3", "Clavicode 3"
1239 DATA "43530E20B5E98404", "Koto 2  ", "Koto 2"
1240 DATA "3430262050307606", "PipeOrg2", "Pipe Organ 2"
1241 DATA "73335A2099F51415", "PohdsPLA", "PohdsPLA"
1242 DATA "73131620F9F53303", "PohdsPRA", "RohdsPRA"
1243 DATA "6121152076542306", "Orch L  ", "Orch L"
1244 DATA "63701B20754B4515", "Orch R  ", "Orch R"
1245 DATA "61A10A2076541207", "SynViol ", "Synthesizer Violin"
1246 DATA "61780D2085F21403", "SynOrgan", "Synthesizer Organ"
1247 DATA "31711520B6F90326", "SynBrass", "Synthesizer Brass"
1248 DATA "61710D2075F21803", "Tube    ", "Tube*"
1249 DATA "030C1420A7FC1315", "Shamisen", "Shamisen"
1250 DATA "13328020208503AF", "Magical ", "Magical"
1251 DATA "F131172023401409", "Huwawa  ", "Huwawa"
1252 DATA "F07417205A4306FC", "WnderFlt", "Wander Flat"
1253 DATA "20710D20C1D55606", "Hardrock", "Hardrock"
1254 DATA "3032062040400474", "Machine ", "Machine"
1255 DATA "3032032040400474", "MachineV", "Machine V"
1256 DATA "01080D2078F87FF9", "Comic   ", "Comic"
1257 DATA "C8C00B2076F711F9", "SE-Comic", "SE-Comic"
1258 DATA "49400B20B4F9FF05", "SE-Laser", "SE-Laser"
1259 DATA "CD420C20A2F00001", "SE-Noise", "SE-Noise"
1260 DATA "5142132013104201", "SE-Star ", "SE-Star 1"
1261 DATA "5142132013104201", "SE-Star2", "SE-Star 2"
1262 DATA "3034122023702602", "Engine 2", "Engine 2"
1263 DATA "0000FF200000FFFF", "Silence ", "Silence"

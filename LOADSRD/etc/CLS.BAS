10 SCREEN8:VDP(9)=VDP(9)OR2
20 FOR I=0 TO1:SETPAGE I,I
30 BLOAD"cc.sc8",S,0
40 BLOAD"cc.sc8",S,32768!
50 NEXT

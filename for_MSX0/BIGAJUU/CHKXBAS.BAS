10 ON ERROR GOTO 1000
20 TR%=2 ' _TURBO ONチェック有効化
30 _TURBO ON(TR%)
40 '※
50 '  _TURBO ON(TR%)にするのは
60 '   DIMの前に
70 '   CLEARやDEFINTやDEFSNG以外の命令があると
80 '   エラーになる為
90 '
100 '*** MAIN ***
110 IF TR% THEN PRINT"TURBO" ELSE PRINT"NORMAL"
120 ' ...
300 TR%=1 ' _TURBO OFFチェック有効化
310 _TURBO OFF
320 ON ERROR GOTO 0
330 PRINT "END"
340 END
350 ' ...
999 '*** ERROR hook ***
1000 '(TR%=2) => _TURBO ONでエラー
1010 IF TR%=2 THEN TR%=0:RESUME 100 'ノーマル実行としてメイン処理へ戻る
1020 '(TR%=1) => _TURBO OFFでエラー
1030 IF TR%=1 THEN TR%=0:RESUME 320 '終了処理へ戻る
1040 '通常のエラー処理
1050 PRINT"Error in ";ERL
1060 ERROR ERR

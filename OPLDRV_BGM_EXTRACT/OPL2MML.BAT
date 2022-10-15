SETLOCAL ENABLEEXTENSIONS
CD %~dp0

REM =========================================
REM Convert OPLDRV BGM to MML (MGSDRV)
REM =========================================
REM 未検証
REM テンポ合わせはログを見て /@t:指定などしてください。
REM
REM (BSAVE形式) ... 定義音色データがあるならこちら推奨
REM               ユーザー音色コンバートあり
REM for %%i in ("*.bin") do (
REM 	OPLDRV_tool %%i /mml:%%~ni.mml /l:%%~ni.mml.log /@t:32 /dl:16 /v+- /loop /cv:fmpac 
REM )
REM (RAW形式) ... 定義音色データが無いもの向け。
REM               ユーザー音色コンバートなし
REM for %%i in ("*.opl") do (
REM 	OPLDRV_tool %%i /mml:%%~ni.mml /l:%%~ni.mml.log /@t:32 /dl:16 /v+- /loop
REM )
REM (RAW形式) ... 定義音色データががあるなら
REM               /a:xxxx でアドレス指定が必要
REM               ユーザー音色コンバートあり
REM for %%i in ("*.opl") do (
REM 	OPLDRV_tool %%i /mml:%%~ni.mml /l:%%~ni.mml.log /@t:32 /dl:16 /v+- /loop /a:9000 /cv:fmpac
REM )

REM =========================================
REM Convert FMPAC BGM to MML (MGSDRV)
REM =========================================
REM 4分音符が24tick =T150、デフォルト音長L16
REM ユーザー音色コンバートあり
call :convert fmpac0.bin /t:150 /dl:16
call :convert fmpac1.bin /t:150 /dl:16
REM 4分音符が28tick = T128、デフォルト音長L16
REM ユーザー音色コンバートあり
call :convert fmpac2.bin /@t:28 /dl:16
call :convert fmpac3.bin /@t:28 /dl:16
call :convert fmpac4.bin /@t:28 /dl:16

REM =========================================
REM Convert RTYPE BGM to MML (MGSDRV)
REM =========================================
call :convert rtype0.bin /@t:32 /dl:16
call :convert rtype1.bin /@t:24 /dl:16
call :convert rtype2.bin /@t:32 /dl:16
call :convert rtype3.bin /@t:32 /dl:16
call :convert rtype4.bin /@t:24 /dl:16
call :convert rtype5.bin /@t:40 /dl:16
call :convert rtype6.bin /@t:24 /dl:8
call :convert rtype7.bin /@t:40 /dl:8
call :convert rtype8.bin /@t:32 /dl:16
call :convert rtype9.bin /@t:32 /dl:16
call :convert rtypea.bin /@t:32 /dl:16
call :convert rtypeb.bin /@t:32 /dl:8
call :convert rtypec.bin /@t:24 /dl:16
call :convert rtyped.bin /@t:24 /dl:16
call :convert rtypee.bin /@t:32 /dl:4
call :convert rtypef.bin /@t:32 /dl:16

call :convert rtype0m.opl /@t:32 /dl:16
call :convert rtype1m.opl /@t:24 /dl:16
call :convert rtype2m.opl /@t:32 /dl:16
call :convert rtype3m.opl /@t:32 /dl:16
call :convert rtype4m.opl /@t:24 /dl:16
call :convert rtype5m.opl /@t:40 /dl:16
call :convert rtype6m.opl /@t:24 /dl:8
call :convert rtype7m.opl /@t:40 /dl:8
call :convert rtype8m.opl /@t:32 /dl:16
call :convert rtype9m.opl /@t:32 /dl:16
call :convert rtypeam.opl /@t:32 /dl:16
call :convert rtypebm.opl /@t:32 /dl:8
call :convert rtypecm.opl /@t:24 /dl:16
call :convert rtypedm.opl /@t:24 /dl:16
call :convert rtypeem.opl /@t:32 /dl:4
call :convert rtypefm.opl /@t:32 /dl:16

exit /b

REM =========================================
:convert
REM =========================================
OPLDRV_tool %1 /mml:%~n1.mml /l:%~n1.mml.log %2 %3 /v+- /loop /cv:fmpac
exit /b

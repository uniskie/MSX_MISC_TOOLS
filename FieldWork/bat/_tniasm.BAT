@ECHO OFF

SET ASM=TNIASM

rem %ASM% の存在確認
where /Q %ASM%.exe
IF ERRORLEVEL 1 GOTO EXE_NOT_FOUND


IF "%2"=="/P" GOTO SETCHECK
IF NOT "%1"=="/P" GOTO ASM

:SHIFT
	SHIFT /1
:SETCHECK
	SET ERCHK=1

:ASM
ECHO %ASM% "%1"
%ASM% "%1"
IF ERRORLEVEL 1 GOTO ERR

:REN
IF EXIST "%~n1.SYM" DEL "%~n1.SYM"
ECHO REN %ASM%.SYM "%~n1.SYM"
REN %ASM%.SYM "%~n1.SYM"
EXIT /B

:EXE_NOT_FOUND
echo %ASM%.exe が見つかりません。
echo 同じフォルダか、Pathの通ったフォルダに %ASM%.exe を置いてください。

:ERR
IF NOT "%ERCHK%"=="1" GOTO ERREND
PAUSE

:ERREND
EXIT /B %ERRORLEVEL%

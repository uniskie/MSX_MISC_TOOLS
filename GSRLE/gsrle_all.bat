REM このバッチファイルと同じフォルダにgsrle.exeを置き
REM 実行すると、このフォルダと全てのサブフォルダにある
REM *.S??ファイルに対して 画像圧縮を実行します。

@ECHO OFF
IF "%GSRLE%"="" SET SET GSRLE=%~dp0gsrle.exe
FOR /R %%i in (*.S??) DO (
	%GSRLE% /S "%%~i"
)
PAUSE
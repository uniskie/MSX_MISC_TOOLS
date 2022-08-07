REM このバッチファイルと同じフォルダにgsrle.exeを置き
REM 実行すると、このフォルダと全てのサブフォルダにある
REM *.S??ファイルに対して 画像圧縮を実行します。
REM ※ 強制256ライン & PLT出力なしです。

@ECHO OFF
IF "%GSRLE%"=="" SET GSRLE=%~dp0gsrle.exe
FOR /R %%i in (*.S??) DO (
	%GSRLE% /S /256 /NP "%%~i"
)
PAUSE
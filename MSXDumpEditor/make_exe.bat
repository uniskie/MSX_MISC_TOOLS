@echo off
set app=%~n1
if "%app"=="" (
	echo ファイル名を指定するか、ドロップしてください。
	pause
	exit/b
)
rem call python -m PyInstaller --onefile --noconsole --noupx "%app%.py"
call python -m PyInstaller --onefile --noupx "%app%.py"
if exist "dist\%app%.exe" (
	copy /y "dist\%app%.exe" ".\"
)
pause

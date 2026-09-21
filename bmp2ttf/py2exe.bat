@echo off
set app=%~n1
if "%app"=="" (
	echo ファイル名を指定するか、ドロップしてください。
	pause
	exit/b
)
set opt=--onefile --noupx
rem set opt=%opt% --noconsole
if exist %app%.ico (
 set opt=%opt% --icon %app%.ico
)
echo call python -m PyInstaller %opt% "%app%.py"
call python -m PyInstaller %opt% "%app%.py"
if exist "dist\%app%.exe" (
	copy /y "dist\%app%.exe" ".\"
)
timeout /t 5


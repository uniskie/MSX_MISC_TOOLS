@echo off
set app=%~n1
if "%app"=="" (
  set app=msx_softwaredb_xml_merge
)
rem call python -m PyInstaller --onefile --noconsole --noupx "%app%.py"
call python -m PyInstaller --onefile --noupx "%app%.py"
if exist "dist\%app%.exe" (
	copy /y "dist\%app%.exe" ".\"
)
pause

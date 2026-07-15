set app=MSXDumpEditor
call python -m PyInstaller --onefile --noconsole --noupx "%app%.py"
if exist "dist\%app%.exe" (
	copy /y "dist\%app%.exe" ".\"
)
pause

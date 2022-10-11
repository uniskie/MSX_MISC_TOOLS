CD %~dp0

REM Convert to BSAVE file, and
REM Relocate to 0x9000, and
REM Convert ROM Voice command to USER Voice command.
for %%i in (*.bin) do (
	if not exist "%%~ni.dat" (
		REM backup original
		copy "%%~i" "%%~ni.dat"
	)
	REM use original data
	OPLDRV_tool "%%~ni.dat" /o:%%~ni.bin /l:%%~ni.bin.log /r:9000 /cv:fmpac /b
)

REM Convert to RAW file, and
REM Relocate to 0x9000, and
REM Convert ROM Voice command to USER Voice command.
for %%i in (*.bin) do (
	OPLDRV_tool %%i /o:%%~ni.opl /l:%%~ni.opl.log /r:9000 /cv:fmpac /-b
)

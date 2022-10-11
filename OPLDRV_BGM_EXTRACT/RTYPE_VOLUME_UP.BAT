CD %~dp0

REM RTYPE VOLUME 3 UP (munus = loud)
for %%i in (rtype?.opl) do (
	OPLDRV_tool %%i /l:"%%~nim.log" /o:"%%~nim%%~xi" /-b /v:-3
)

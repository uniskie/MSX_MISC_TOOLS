CD %~dp0

REM RTYPE VOLUME 2 UP (munus = loud)
REM  max -3
for %%i in (rtype?.opl) do (
	OPLDRV_tool %%i /l:"%%~nim.log" /o:"%%~nim%%~xi" /-b /v:-2
)

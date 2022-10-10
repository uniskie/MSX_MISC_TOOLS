CD %~dp0
for %%i in (*.bin) do (OPLDRV_tool %%i /l:%%~ni.log /-b /o:%%~ni.opl)

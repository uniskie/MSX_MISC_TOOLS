@echo off
setlocal

set filebase=font_for_bz_msx
set fontname=MSXFontForDump
set fontfamily=MSXFontForDumpN

set input=%filebase%.bmp
set nowait=1

set output=%filebase%.ttf
call bmp2msxfont "%input%" "%fontname%" "%fontfamily%"
copy /y "%output%" "%fontfamily%.ttf"

set output=%filebase%_p.ttf
call bmp2msxfont "%input%" "%fontname%P" "%fontfamily%P" --proportional
copy /y "%output%" "%fontfamily%P.ttf"


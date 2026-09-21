@echo off
setlocal

set filebase=font_for_bz_msx
set fontname=MSXFontForDump
set fontfamily=MSXFontForDump
set input=%filebase%.bmp
set output=%filebase%.ttf
set nowait=1

call bmp2msxfont "%input%" "%fontname%" "%fontfamily%"

copy /y "%output%" "%fontfamily%.ttf"


@echo off
setlocal

echo =====================================================
echo Bmp to MSX-Font True Type Font

rem --- 引数が指定されていれば環境変数に格納（前後の引用符除去） ---
if not "%~1"=="" set "input=%~1"
if not "%~2"=="" set "fontname=%~2"
if not "%~3"=="" set "fontfamily=%~3"
if not "%~4"=="" set "exopt=%~4"

rem --- 環境変数の未定義チェック ---
if "%input%"=="" (
    echo [Error] Input file is not specified.
    echo         Usage: %~nx0 ^<input_file^> [fontname]
    echo         e.g.^) %~nx0 msxfont.aseprite MSXDotFont
    echo         or set environment variable 'input'
    set "err=1"
)
if "%fontname%"=="" (
    echo [Error] Font name is not specified.
    echo         Usage: %~nx0 ^<input_file^> ^<fontname^>
    echo         e.g.^) %~nx0 msxfont.aseprite MSXDotFont
    echo         or set environment variable 'fontname'
    set "err=1"
)
if "%err%"=="1" goto :err_end

rem --- 入力ファイルの存在チェック ---
if not exist "%input%" (
    echo [Error] Input file not found: "%input%"
    goto :err_end
)

rem --- 出力ファイルパスの生成 ---
if "%output%"=="" (
 set "output=%fontname%.ttf"
)
echo "%input%" to "%output%"

echo =====================================================
echo bmp2ttf2

set "opt="
set "opt=%opt% --name "%fontname%""
if not "%fontfamily%"=="" (
 set "opt=%opt% --family "%fontfamily%""
)
set "opt=%opt% --cell-width 8"
set "opt=%opt% --cell-height 8"
set "opt=%opt% --baseline 1"
set "opt=%opt% --margin-top 1"
set "opt=%opt% --margin-bottom 1"
set "opt=%opt% --units-per-em 2048"

rem bmp2ttf互換
set "opt=%opt% --scale-copy 0xE000,0xE100,256"
set "opt=%opt% --charmap "char_map_msx.def",0xE100"

set "opt=%opt% --output "%output%""
set "opt=%opt% %exopt%"

echo ^> py bmp2ttf2.py %opt% "%input%"
py bmp2ttf2.py %opt% "%input%"
if errorlevel 1 goto :err_python

echo.
echo Complete!
if "%nowait%"=="" timeout /t 5
exit /b 0

rem ======================================
rem エラー処理
rem ======================================
:err_ase2ttf
echo.
rem ase2ttf コマンドが認識されているかを判定
where ase2ttf >nul 2>&1
if errorlevel 1 (
    echo [Error] 'ase2ttf' command is not found.
    echo         Please make sure ase2ttf is installed and added to your PATH.
    echo         exe file: https://github.com/nuskey8/ase2ttf/releases
) else (
    echo [Error] ase2ttf failed during font conversion.
)
goto :err_end

:err_python
echo.
echo [Error] Failed to execute 'modify_msx_font.py'.
goto :err_end

:err_end
echo.
echo Conversion aborted.
pause
exit /b 1
@echo off
setlocal

echo =====================================================
echo Bmp to MSX-Font True Type Font

rem --- 引数が指定されていれば環境変数に格納（前後の引用符除去） ---
if not "%~1"=="" set "input=%~1"
if not "%~2"=="" set "fontname=%~2"
if not "%~3"=="" set "fontfamily=%~3"

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
echo bmp2tff
rem usage: bmp2ttf.py [-h] [-o OUTPUT] [-n NAME] [-f FAMILY_NAME] [-s CELL_SIZE] [-cw CELL_WIDTH] [-ch CELL_HEIGHT]
rem                   [-b BASELINE] [-mt MARGIN_TOP] [-mb MARGIN_BOTTOM] [-e UNITS_PER_EM]
rem                   input
rem 
rem MSXフォント画像 (BMP/PNG) から等幅 TrueType フォント (.ttf) を生成します。
rem 
rem positional arguments:
rem   input                 入力画像ファイルパス (BMP, PNGなど)
rem 
rem options:
rem   -h, --help            show this help message and exit
rem   -o, --output OUTPUT   出力TTFファイル名 (省略時は <画像名>.ttf)
rem   -n, --name NAME       フォント名 (デフォルト: MSX-Font)
rem   -f, --family, --family-name FAMILY_NAME
rem                         フォントファミリー名 (省略時は --name と同じ)
rem   -s, --cell-size CELL_SIZE
rem                         文字のセルサイズ (例: 8x8, 16x16, 8)。デフォルト: 8x8
rem   -cw, --cell-width CELL_WIDTH
rem                         セル幅
rem   -ch, --cell-height CELL_HEIGHT
rem                         セル高
rem   -b, --baseline BASELINE
rem                         ベースライン位置 (セル下端からのドット数/ディセンダドット数。省略時はセル高さの1/8)
rem   -mt, --margin-top MARGIN_TOP
rem                         上余白ドット数 (アセンダ側の追加余白。デフォルト: 0)
rem   -mb, --margin-bottom MARGIN_BOTTOM
rem                         下余白ドット数 (ディセンダ側の追加余白。デフォルト: 0)
rem   -e, --em, --units-per-em UNITS_PER_EM
rem                         EMの高さ (Units per em。デフォルト: 1024)

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
set "opt=%opt% --output "%output%""

echo ^> py bmp2ttf.py %opt% "%input%"
py bmp2ttf.py %opt% "%input%"
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
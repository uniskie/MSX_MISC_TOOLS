@set path=%cd%;%path%
@if "%~1"=="" exit/b
cd "%~1"
%~d1

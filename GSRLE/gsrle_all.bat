REM ���̃o�b�`�t�@�C���Ɠ����t�H���_��gsrle.exe��u��
REM ���s����ƁA���̃t�H���_�ƑS�ẴT�u�t�H���_�ɂ���
REM *.S??�t�@�C���ɑ΂��� �摜���k�����s���܂��B

@ECHO OFF
IF "%GSRLE%"="" SET SET GSRLE=%~dp0gsrle.exe
FOR /R %%i in (*.S??) DO (
	%GSRLE% /S "%%~i"
)
PAUSE
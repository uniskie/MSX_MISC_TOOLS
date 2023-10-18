@set ERCHK=1
@rem set asm=_sjasm
@set asm=_tniasm
call %asm% LOADSRD.ASM
call %asm% SRX.ASM
call %asm% SRX2.ASM
call %asm% SRX3.ASM

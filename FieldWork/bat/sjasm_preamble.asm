; tniASM compatibility macros defining unrecognized directives: rb, rw, fname

rb      MACRO count?
            ds count?
            ; in tniASM the `rb/rw` does not emit bytes to output, so rewind the output
            FPOS -(count?)
        ENDM

rw      MACRO count?
            ds 2 * count?
            ; in tniASM the `rb/rw` does not emit bytes to output, so rewind the output
            FPOS -(2 * count?)
        ENDM

fname   MACRO name?
            DEFINE __CURRENT_OUTPUT_NAME__ name?
            OUTPUT name?,t      ; truncate the file first
            OUTPUT name?,r      ; reopen it to allow also position seeks (for rb/rw macros)
        ENDM

; switch multiarg delimiter to ",," (to produce correct opcode for `sub a,7` ("a" option)
; treat "wholesome" round parentheses as memory access ("b" option)
; warn about any fake instruction ("f")
;        OPT --syntax=abf
; Case insensitive instructions/directives ("i")
        OPT --syntax=abfi

; command line to build migrated sources with sjasmplus (inside the "engine" folder):
; sjasmplus --sym=theproject.sym --dirbol --fullpath --longptr ../sjasm_preamble.asm Main.asm


; support Upper case

RB      MACRO count?
            ds count?
            ; in tniASM the `rb/rw` does not emit bytes to output, so rewind the output
            FPOS -(count?)
        ENDM

RW      MACRO count?
            ds 2 * count?
            ; in tniASM the `rb/rw` does not emit bytes to output, so rewind the output
            FPOS -(2 * count?)
        ENDM

FNAME   MACRO name?
            DEFINE __CURRENT_OUTPUT_NAME__ name?
            OUTPUT name?,t      ; truncate the file first
            OUTPUT name?,r      ; reopen it to allow also position seeks (for rb/rw macros)
        ENDM


; reference: https://specnext.dev/blog/2020/11/13/migration-of-msx-project-from-tniasm-to-sjasmplus/

; Option flags as follows:
;	-h or --help[=warnings]	�w���v���
;	--version		��{��� (--nologo �̏ꍇ�͐��̃o�[�W����������̂�)
;	--zxnext[=cspect]	ZX Next Z80 �g����L���ɂ���
;				(CSpect �G�~�����[�^�ɂ͗]���� "exit" DD00 �� "break" DD01 �U���߂�����)
;	--i8080			�L���Ȗ��߂� i8080 �݂̂ɐ��� (+ �t�F�C�N�Ȃ�)
;	--lr35902		�V���[�vLR35902/SM83 CPU���߃��[�h (+ �t�F�C�N�Ȃ�)
;	--outprefix=<path>	�f�B���N�e�B�u���� save/output/... �t�@�C�����̃v���t�B�b�N�X�B
;				��: �v���t�B�b�N�X���t�H���_�̏ꍇ�A���ɑ��݂��A�����ɃX���b�V�����t������Ă���K�v������܂��B
;				    �v���t�B�b�N�X�̓\�[�X�Œ�`���ꂽfilename�ɂ̂ݓK�p����܂� (CLI �����ɂ͓K�p����܂���)
;	-i<path> or -I<path> or --inc=<path> (���X�g����ɂ���ꍇ�� --inc �Ɂu=�v��t���Ȃ�)
;				�C���N���[�h�p�X (��Œ�`���ꂽ�����D�悳��܂�)
;	--lst[=<filename>]	���X�g�� <filename> �ɕۑ� (<source>.lst ���f�t�H���g)
;	--lstlab[=sort]		[���בւ���ꂽ] �V���{�� �e�[�u�������X�g�ɒǉ����܂�
;	--sym=<filename>	�V���{�� �e�[�u���� <filename> �ɕۑ����܂�
;	--exp=<filename>	�G�N�X�|�[�g�� <filename> �ɕۑ����܂� (EXPORT �^��������Q��)
;	--raw=<filename>	�}�V���R�[�h�� <filename> �ɂ��ۑ�����܂� (- �� STDOUT)
;	--sld[=<filename>]	�\�[�X ���x���̃f�o�b�O �f�[�^�� <filename> �ɕۑ����܂�
;				�f�t�H���g���́u<�ŏ��̓���filename>.sld.txt�v�ł��B
;				��: �o�͂𐧌䂷��ɂ́AOUTPUT�ALUA/ENDLUA�A����т��̑��̋^�����Z���g�p���܂��B
; Logging:
;	--nologo		�N�����b�Z�[�W��\�����܂���
;	--msg=[all|war|err|none|lst|lstlab]	STDERR���b�Z�[�W�̏璷���i"all "���f�t�H���g�j
;				��: "lst "�܂��� "lstlab "��STDERR�����X�g�t�@�C���ɂ���B
;				     (����� `--lst` �ƏՓ˂���̂ŁA�ǂ��炩�̃I�v�V�����������g������)
;				    �܂��A"all" �̐f�f���b�Z�[�W�̓��X�e�B���O�t�@�C���̈ꕔ�ł͂Ȃ��̂ŏȗ������B
;				    "lstlab"�̓V���{�����\�[�g����B
;	--fullpath		�G���[�̂���t�@�C���ւ̃t���p�X��\�����܂�
;				��: "fullpath "�̓t�@�C���V�X�e���̃��[�g����ł͂Ȃ��A���݂̍�ƃf�B���N�g������n�܂�܂��B
;				     (MS_VS �r���h�� v1.15.0 �ȍ~�A���̂悤�ɓ��삷��悤�ɏC������܂���)
;	--color=[on|off|auto]	�x��/�G���[�� ANSI �J���[�����O��L���܂��͖����ɂ��܂��B
;				��: �������o�́A���ϐ�TERM�̑��݂��`�F�b�N���A���̓��e���� "color "�Ƃ����T�u��������X�L��������B
;				    (�Ⴆ�� "xterm-256color"�Ȃ�)
; Other:
;	-D<name>[=<value>] �܂��� --define <name>[=<value>]
;	                         <NAME> �� <value> �Ƃ��Ē�`���܂� (v1.20.3 �ȍ~�� --define)
;	-W[no-]<warning_id>	����̌x���^�C�v�𖳌��܂��͗L���ɂ��܂�
;	- 			STDIN ���\�[�X�Ƃ��ēǂݎ��܂� (�ʏ�̃t�@�C���Ԃł����Ă�)
;	--longptr		�f�o�C�X������܂���: �v���O���� �J�E���^�[ $ �� 0x10000 �𒴂��邱�Ƃ��ł��܂�
;	--reversepop		�t�� POP ������L���ɂ��܂� (SjASM��{�o�[�W�����Ɠ��l)
;	--dirbol		�s������̃f�B���N�e�B�u������L���ɂ��܂��B
;	--nofakes		�t�F�C�N���߂𖳌��ɂ��� (--syntax=F �Ɠ���)
;	--dos866		Windows �R�[�h�y�[�W���� DOS 866 (�L��������) �ɃG���R�[�h���܂��B
;	--syntax=<...>		��͍\���𒲐����܂��B�ڍׂ͈ȉ����Q�Ƃ��Ă��������B
;
; �I�v�V���� --lstlab=sort ��t����ƁA���̃V���{���E�_���v���i���X�g�ɉ����āj�\�[�g����܂��F -sym�ACSPECTMAP�ALABELSLIST�B
; -msg=lstlab�͏�Ƀ\�[�g�� "on "�ɂ��܂��i"unsorted "�I�v�V�����͖����j
;
; syntax�I�v�V�����̒l�͕����̕����ō\������邱�Ƃ�����A����̋@�\�̕������ȗ�����ƃf�t�H���g�̐ݒ肪�g�p����܂��F
;
;	  a	���������̋�؂蕶�� ",," (�f�t�H���g�� ",") (������ dec|inc|pop|push �� "," ���󂯕t����)
;	  b	���S�̂̊��ʂ̓������A�N�Z�X�ł̂ݗL�� (�f�t�H���g = ���l�܂��̓�����)
;	  B	�������A�N�Z�X���� [] �͕K�{ (�f�t�H���g = �\���ɘa�A[] �͒ǉ��Ŏg�p�\)
;	  f	�t�F�C�N����: �x�� (�f�t�H���g = �L��)
;	  F	�t�F�C�N����: ���� (�f�t�H���g = �L��)
;	  i	����/�f�B���N�e�B�u�ő啶������������ʂ��Ȃ� (�f�t�H���g = �����啶�����������K�v)
;	  l	�L�[���[�h���x��(���W�X�^�A���߁A...)�F�x��(�f�t�H���g = ����)
;	  L	�L�[���[�h���x��(���W�X�^�A���߁A...)�F�G���[(�f�t�H���g = ����)
;	  M	8080���C�N�ȍ\�����J�o�[���邽�߂�"(hl)"�̃G�C���A�X"m"��"M"��L���F ADD A,M
;	  s	"�P���� "�S�P��u���݂̂��g�p���A���P��͎g�p���Ȃ� (v1.18.3�ȍ~)
;	  w	�x���I�v�V�����F�x�����G���[�Ƃ��ĕ�
;	  m	*v1.20.0�ō폜*�A-Wno-rdlow���g�p�B
; �� work in progress: �I�v�V���� "l "�� "L "�͂܂���������Ă��Ȃ��B


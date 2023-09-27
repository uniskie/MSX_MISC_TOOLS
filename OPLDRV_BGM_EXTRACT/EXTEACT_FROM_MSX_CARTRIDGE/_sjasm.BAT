@ECHO OFF

SET ASM=sjasmplus

rem %ASM%.exe の存在確認
where %ASM%.exe
IF ERRORLEVEL 1 GOTO EXE_NOT_FOUND

SET CURDIR=%~dp0
IF "%2"=="/P" GOTO SETCHECK
IF NOT "%1"=="/P" GOTO ASM

:SHIFT
	SHIFT /1
:SETCHECK
	SET ERCHK=1

:ASM
ECHO sjasmplus "%1"

rem SET SJASMPLUSOPTS=--dirbol --longptr --fullpath
SET SJASMPLUSOPTS=--longptr --fullpath

%ASM% "%CURDIR%sjasm_preamble.asm" "%1" --sym="%~n1.SYM" --raw="%~n1.BIN"
IF ERRORLEVEL 1 GOTO ERR
EXIT /B

:EXE_NOT_FOUND
echo %ASM%.exe が見つかりません。
echo 同じフォルダか、Pathの通ったフォルダに %ASM%.exe を置いてください。

:ERR
IF NOT "%ERCHK%"=="1" GOTO ERREND
PAUSE

:ERREND
EXIT /B %ERRORLEVEL%

rem Option flags as follows:
rem	-h or --help[=warnings]	ヘルプ情報
rem	--version		基本情報 (--nologo の場合は生のバージョン文字列のみ)
rem	--zxnext[=cspect]	ZX Next Z80 拡張を有効にする
rem				(CSpect エミュレータには余分な "exit" DD00 と "break" DD01 偽命令がある)
rem	--i8080			有効な命令を i8080 のみに制限 (+ フェイクなし)
rem	--lr35902		シャープLR35902/SM83 CPU命令モード (+ フェイクなし)
rem	--outprefix=<path>	ディレクティブ中の save/output/... ファイル名のプレフィックス。
rem				注: プレフィックスがフォルダの場合、既に存在し、末尾にスラッシュが付加されている必要があります。
rem				    プレフィックスはソースで定義されたfilenameにのみ適用されます (CLI 引数には適用されません)
rem	-i<path> or -I<path> or --inc=<path> (リストを空にする場合は --inc に「=」を付けない)
rem				インクルードパス (後で定義された方が優先されます)
rem	--lst[=<filename>]	リストを <filename> に保存 (<source>.lst がデフォルト)
rem	--lstlab[=sort]		[並べ替えられた] シンボル テーブルをリストに追加します
rem	--sym=<filename>	シンボル テーブルを <filename> に保存します
rem	--exp=<filename>	エクスポートを <filename> に保存します (EXPORT 疑似操作を参照)
rem	--raw=<filename>	マシンコードは <filename> にも保存されます (- は STDOUT)
rem	--sld[=<filename>]	ソース レベルのデバッグ データを <filename> に保存します
rem				デフォルト名は「<最初の入力filename>.sld.txt」です。
rem				注: 出力を制御するには、OUTPUT、LUA/ENDLUA、およびその他の疑似演算を使用します。
rem Logging:
rem	--nologo		起動メッセージを表示しません
rem	--msg=[all|war|err|none|lst|lstlab]	STDERRメッセージの冗長性（"all "がデフォルト）
rem				注: "lst "または "lstlab "はSTDERRをリストファイルにする。
rem				     (これは `--lst` と衝突するので、どちらかのオプションだけを使うこと)
rem				    また、"all" の診断メッセージはリスティングファイルの一部ではないので省略される。
rem				    "lstlab"はシンボルをソートする。
rem	--fullpath		エラーのあるファイルへのフルパスを表示します
rem				注: "fullpath "はファイルシステムのルートからではなく、現在の作業ディレクトリから始まります。
rem				     (MS_VS ビルドは v1.15.0 以降、このように動作するように修正されました)
rem	--color=[on|off|auto]	警告/エラーの ANSI カラーリングを有効または無効にします。
rem				注: 自動検出は、環境変数TERMの存在をチェックし、その内容から "color "というサブ文字列をスキャンする。
rem				    (例えば "xterm-256color"など)
rem Other:
rem	-D<name>[=<value>] または --define <name>[=<value>]
rem	                         <NAME> を <value> として定義します (v1.20.3 以降は --define)
rem	-W[no-]<warning_id>	特定の警告タイプを無効または有効にします
rem	- 			STDIN をソースとして読み取ります (通常のファイル間であっても)
rem	--longptr		デバイスがありません: プログラム カウンター $ は 0x10000 を超えることができます
rem	--reversepop		逆の POP 順序を有効にします (SjASM基本バージョンと同様)
rem	--dirbol		行頭からのディレクティブ処理を有効にします。
rem	--nofakes		フェイク命令を無効にする (--syntax=F と同じ)
rem	--dos866		Windows コードページから DOS 866 (キリル文字) にエンコードします。
rem	--syntax=<...>		解析構文を調整します。詳細は以下を参照してください。
rem
rem オプション --lstlab=sort を付けると、他のシンボル・ダンプも（リストに沿って）ソートされます： -sym、CSPECTMAP、LABELSLIST。
rem -msg=lstlabは常にソートを "on "にします（"unsorted "オプションは無い）
rem
rem syntaxオプションの値は複数の文字で構成されることがあり、特定の機能の文字を省略するとデフォルトの設定が使用されます：
rem 
rem	  a	複数引数の区切り文字 ",," (デフォルトは ",") (ただし dec|inc|pop|push は "," も受け付ける)
rem	  b	式全体の括弧はメモリアクセスでのみ有効 (デフォルト = 即値またはメモリ)
rem	  B	メモリアクセス括弧 [] は必須 (デフォルト = 構文緩和、[] は追加で使用可能)
rem	  f	フェイク命令: 警告 (デフォルト = 有効)
rem	  F	フェイク命令: 無効 (デフォルト = 有効)
rem	  i	命令/ディレクティブで大文字小文字を区別しない (デフォルト = 同じ大文字小文字が必要)
rem	  l	キーワードラベル(レジスタ、命令、...)：警告(デフォルト = 無効)
rem	  L	キーワードラベル(レジスタ、命令、...)：エラー(デフォルト = 無効)
rem	  M	8080ライクな構文をカバーするために"(hl)"のエイリアス"m"や"M"を有効： ADD A,M
rem	  s	"単純な "全単語置換のみを使用し、副単語は使用しない (v1.18.3以降)
rem	  w	警告オプション：警告をエラーとして報告
rem	  m	*v1.20.0で削除*、-Wno-rdlowを使用。
rem † work in progress: オプション "l "と "L "はまだ実装されていない。


rem tniasm互換用マクロ
rem sjasm_preamble.asm
rem	; tniASM compatibility macros defining unrecognized directives: rb, rw, fname
rem	
rem	rb      MACRO count?
rem	            ds count?
rem	            ; in tniASM the `rb/rw` does not emit bytes to output, so rewind the output
rem	            FPOS -(count?)
rem	        ENDM
rem	
rem	rw      MACRO count?
rem	            ds 2 * count?
rem	            ; in tniASM the `rb/rw` does not emit bytes to output, so rewind the output
rem	            FPOS -(2 * count?)
rem	        ENDM
rem	
rem	fname   MACRO name?
rem	            DEFINE __CURRENT_OUTPUT_NAME__ name?
rem	            OUTPUT name?,t      ; truncate the file first
rem	            OUTPUT name?,r      ; reopen it to allow also position seeks (for rb/rw macros)
rem	        ENDM
rem	
rem	; switch multiarg delimiter to ",," (to produce correct opcode for `sub a,7` ("a" option)
rem	; treat "wholesome" round parentheses as memory access ("b" option)
rem	; warn about any fake instruction ("f")
rem	        OPT --syntax=abf
rem	
rem	; command line to build migrated sources with sjasmplus (inside the "engine" folder):
rem	; sjasmplus --sym=theproject.sym --dirbol --fullpath --longptr ../sjasm_preamble.asm Main.asm
rem	
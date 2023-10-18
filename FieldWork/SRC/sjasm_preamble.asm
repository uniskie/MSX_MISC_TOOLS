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
;	-h or --help[=warnings]	ヘルプ情報
;	--version		基本情報 (--nologo の場合は生のバージョン文字列のみ)
;	--zxnext[=cspect]	ZX Next Z80 拡張を有効にする
;				(CSpect エミュレータには余分な "exit" DD00 と "break" DD01 偽命令がある)
;	--i8080			有効な命令を i8080 のみに制限 (+ フェイクなし)
;	--lr35902		シャープLR35902/SM83 CPU命令モード (+ フェイクなし)
;	--outprefix=<path>	ディレクティブ中の save/output/... ファイル名のプレフィックス。
;				注: プレフィックスがフォルダの場合、既に存在し、末尾にスラッシュが付加されている必要があります。
;				    プレフィックスはソースで定義されたfilenameにのみ適用されます (CLI 引数には適用されません)
;	-i<path> or -I<path> or --inc=<path> (リストを空にする場合は --inc に「=」を付けない)
;				インクルードパス (後で定義された方が優先されます)
;	--lst[=<filename>]	リストを <filename> に保存 (<source>.lst がデフォルト)
;	--lstlab[=sort]		[並べ替えられた] シンボル テーブルをリストに追加します
;	--sym=<filename>	シンボル テーブルを <filename> に保存します
;	--exp=<filename>	エクスポートを <filename> に保存します (EXPORT 疑似操作を参照)
;	--raw=<filename>	マシンコードは <filename> にも保存されます (- は STDOUT)
;	--sld[=<filename>]	ソース レベルのデバッグ データを <filename> に保存します
;				デフォルト名は「<最初の入力filename>.sld.txt」です。
;				注: 出力を制御するには、OUTPUT、LUA/ENDLUA、およびその他の疑似演算を使用します。
; Logging:
;	--nologo		起動メッセージを表示しません
;	--msg=[all|war|err|none|lst|lstlab]	STDERRメッセージの冗長性（"all "がデフォルト）
;				注: "lst "または "lstlab "はSTDERRをリストファイルにする。
;				     (これは `--lst` と衝突するので、どちらかのオプションだけを使うこと)
;				    また、"all" の診断メッセージはリスティングファイルの一部ではないので省略される。
;				    "lstlab"はシンボルをソートする。
;	--fullpath		エラーのあるファイルへのフルパスを表示します
;				注: "fullpath "はファイルシステムのルートからではなく、現在の作業ディレクトリから始まります。
;				     (MS_VS ビルドは v1.15.0 以降、このように動作するように修正されました)
;	--color=[on|off|auto]	警告/エラーの ANSI カラーリングを有効または無効にします。
;				注: 自動検出は、環境変数TERMの存在をチェックし、その内容から "color "というサブ文字列をスキャンする。
;				    (例えば "xterm-256color"など)
; Other:
;	-D<name>[=<value>] または --define <name>[=<value>]
;	                         <NAME> を <value> として定義します (v1.20.3 以降は --define)
;	-W[no-]<warning_id>	特定の警告タイプを無効または有効にします
;	- 			STDIN をソースとして読み取ります (通常のファイル間であっても)
;	--longptr		デバイスがありません: プログラム カウンター $ は 0x10000 を超えることができます
;	--reversepop		逆の POP 順序を有効にします (SjASM基本バージョンと同様)
;	--dirbol		行頭からのディレクティブ処理を有効にします。
;	--nofakes		フェイク命令を無効にする (--syntax=F と同じ)
;	--dos866		Windows コードページから DOS 866 (キリル文字) にエンコードします。
;	--syntax=<...>		解析構文を調整します。詳細は以下を参照してください。
;
; オプション --lstlab=sort を付けると、他のシンボル・ダンプも（リストに沿って）ソートされます： -sym、CSPECTMAP、LABELSLIST。
; -msg=lstlabは常にソートを "on "にします（"unsorted "オプションは無い）
;
; syntaxオプションの値は複数の文字で構成されることがあり、特定の機能の文字を省略するとデフォルトの設定が使用されます：
;
;	  a	複数引数の区切り文字 ",," (デフォルトは ",") (ただし dec|inc|pop|push は "," も受け付ける)
;	  b	式全体の括弧はメモリアクセスでのみ有効 (デフォルト = 即値またはメモリ)
;	  B	メモリアクセス括弧 [] は必須 (デフォルト = 構文緩和、[] は追加で使用可能)
;	  f	フェイク命令: 警告 (デフォルト = 有効)
;	  F	フェイク命令: 無効 (デフォルト = 有効)
;	  i	命令/ディレクティブで大文字小文字を区別しない (デフォルト = 同じ大文字小文字が必要)
;	  l	キーワードラベル(レジスタ、命令、...)：警告(デフォルト = 無効)
;	  L	キーワードラベル(レジスタ、命令、...)：エラー(デフォルト = 無効)
;	  M	8080ライクな構文をカバーするために"(hl)"のエイリアス"m"や"M"を有効： ADD A,M
;	  s	"単純な "全単語置換のみを使用し、副単語は使用しない (v1.18.3以降)
;	  w	警告オプション：警告をエラーとして報告
;	  m	*v1.20.0で削除*、-Wno-rdlowを使用。
; † work in progress: オプション "l "と "L "はまだ実装されていない。


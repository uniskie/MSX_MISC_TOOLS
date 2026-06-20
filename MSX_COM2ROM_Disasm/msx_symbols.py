from collections import defaultdict

# -----------------------------------------------------------------------------
# MSX シンボルリスト
# msx_symbols_bios
# msx_symbols_work
# msx_symbols_hook
# -----------------------------------------------------------------------------

# 双方向引き辞書
class BidirectionalDict:
    def __init__(self, forward_dict: dict[str, int]):
        self.forward = forward_dict
        self.inverse: defaultdict[str, list[str]] = defaultdict(list)
        for key, address in forward_dict.items():
            self.inverse[self.address_to_str(address)].append(key)

    def address_to_str(self, address : int) -> str:
        return f"0x{address:04X}"

    def get_address(self, key: str) -> int | None:
        return self.forward.get(key)

    def from_address(self, address: int) -> list[str]:
        return self.inverse[self.address_to_str(address)]

msx_symbols_bios = BidirectionalDict({
    # ● SYSTEM SIGNITURE
    "ROMID":    0x002D, # 0=MSX 1=MSX2 2=MSX2+ 3=turboR

    # ● BIOS
    # "CHKRAM":   0x0000, # 
    "SYNCHR":   0x0008, # IF A==[HL] THEN JP CHRGTR ELSE Syntax error
    "RDSLT":    0x000C, # in:A=SLOT / ret:A=[HL], DI
    "CHRGTR":   0x0010, # get basic token A=[HL]
    "WRSLT":    0x0014, # in:A=SLOT / [HL]=E, DI
    "OUTDO":    0x0018, # 現在使っているデバイスにAの値を出力
    "CALSLT":   0x001C, # インタースロットコール in:IYh=SLOT,IX=ADDRESS
    "DCOMPR":   0x0020, # CP HL,DE
    "ENASLT":   0x0024, # A=SLOT,H=ADDRESS(HIGH)
    "GETYPR":   0x0028, # DACの値を返す。DACの型によってZ,S,Z,P/Vフラグが変化する
    "CALLF":    0x0030, # インタースロットコール 次の1バイトでSLOT その次の2バイトで番地
                        # RST 0x30
                        # DB slot
                        # DW address
    "KEYINT":   0x0038, # タイマー割り込み処理ルーチンを実行
    "INITIO":   0x003B, # デバイスを初期化
    "INIFNK":   0x003E, # ファンクションキーの内容を初期化
    "DISSCR":   0x0041, # 画面表示の禁止
    "ENASCR":   0x0044, # 画面表示の許可
    "WRTVDP":   0x0047, # VDPのレジスタにデータを書き込む C=レジスタ番号, B=データ
    "RDVRM":    0x004A, # VRAMを読む(番地は14bitでマスク) A=VRAM[HL]
    "WRTVRM":   0x004D, # VRAMに書く(番地は14bitでマスク) VRAM[HL]=A
    "SETRD":    0x0050, # VDPにVRAMアドレスをセットして読み出せる状態にする(番地は14bitでマスク) HL=番地
    "SETWRT":   0x0053, # VDPにVRAMアドレスをセットして書き込める状態にする(番地は14bitでマスク) HL=番地
    "FILVRM":   0x0056, # VRAMをFILL HL=アドレス, BC=長さ, A=データ
    "LDIRMV":   0x0059, # VRAMからRAMへブロック転送 HL=転送元アドレス, DE=転送先アドレス, BC=長さ
    "LDIRVM":   0x005C, # RAMからVRAMへブロック転送 HL=転送元アドレス, DE=転送先アドレス, BC=長さ
    "CHGMOD":   0x005F, # スクリーンモードを切り替える。 パレットは変更しない
    "CHGCLR":   0x0062, # 画面の色を変える A=画面モード
                        #                  FORCLR (0xF3E9)=前景色
                        #                  BAKCLR (0xF3EA)=背景色
                        #                  BDRCLR (0xF3EB)=周辺色
    "NMI":      0x0066, # NMI処理ルーチンを実行
    "CLRSPR":   0x0069, # 全てのスプライトを初期化
    "INITXT":   0x006C, # SCREEN0(WIDTH40)で画面初期化（パレットは初期化しない）
    "INIT32":   0x006F, # SCREEN1で画面初期化（パレットは初期化しない）
    "INIGRP":   0x0072, # SCREEN2で画面初期化（パレットは初期化しない）
    "INIMLT":   0x0075, # SCREEN3で画面初期化（パレットは初期化しない）
    "SETTXT":   0x0078, # VDPのみSCREEN0(WIDTH40)に変更
    "SETT32":   0x007B, # VDPのみSCREEN1に変更
    "SETGRP":   0x007E, # VDPのみSCREEN2に変更
    "SETMLT":   0x0081, # VDPのみSCREEN3に変更
    "CALPAT":   0x0084, # スプライト・ジェネレータ・テーブルのアドレスを返す
    "CALATR":   0x0087, # スプライトアトリビュート・テーブルのアドレスを返す
    "GSPSIZ":   0x008A, # 現在のスプライト・サイズを返す
    "GRPPRT":   0x008D, # グラフィック画面に文字を表示
    "GICINI":   0x0090, # PSG を初期化し、PLAY 文のための初期値をセット
    "WRTPSG":   0x0093, # PSG のレジスタにデータを書き込む A にPSG のレジスタ番号、E にデータ
    "RDPSG":    0x0096, # PSG のレジスタの値を読む A に PSG のレジスタ番号
    "STRTMS":   0x0099, # バックグラウンド・タスクとして PLAY 文が実行中であるかどうかチェックし、実行中でなければ PLAY 文の実行を開始
    "CHSNS":    0x009C, # キーボード・バッファの状態をチェック バッファが空であれば Z フラグをセット
    "CHGET":    0x009F, # 1 文字入力 (入力待ちあり)
    "CHPUT":    0x00A2, # 1 文字表示
    "LPTOUT":   0x00A5, # 1 文字プリンタ出力 失敗した場合は CY フラグをセット
    "LPTSTT":   0x00A8, # プリンタの状態をチェック
                        # A が 255 で Z フラグがリセットされていなければプリンタは READY。A が 0 で Z フラグがセットされていればプリンタは NO READY
    "CNVCHR":   0x00AB, # グラフィック・ヘッダかどうかをチェックし、コードを変換
                        # CY フラグがリセット → グラフィック・ヘッダではない
                        # CY フラグと Z フラグがセット → A に変換後のコード
                        # CY フラグがセット、Z フラグがリセット → A に変換されていないコード
    "PINLIN":   0x00AE, # リターンキーや STOP キーがタイプされるまでに入力された文字コードを指定されたバッファに格納する
                        # ret: HL にバッファの先頭アドレス -1、STOP キーで終了したときのみ CY フラグをセット
    "INLIN":    0x00B1, # AUTFLG (0xF6AA) がセットされる以外は PINLIN と同じ
    "QINLIN":   0x00B4, # HL にバッファの先頭アドレス -1、STOP キーで終了したときのみ CY フラグをセット
    "BREAKX":   0x00B7, # Ctrl-STOP キーを押しているかどうかチェック。このルーチンでは割り込みが禁止される
                        # 押されていれば CY フラグをセット
    "ISCNTC":   0x00BA, # [非公開] Shift-STOP キーを押しているかどうかチェック。このルーチンでは割り込みが禁止される
                        # 押されていれば CY フラグをセット
    "CKCNTC":   0x00BD, # [非公開] ISCNTCと同じ。 Basicから使用される
    "BEEP":     0x00C0, # ブザーを鳴らす
    "CLS":      0x00C3, # 画面クリア IN:ゼロフラグをセット
    "POSIT":    0x00C6, # カーソルの移動 H=カーソルX座標, L=カーソルY座標 左上原点が(1,1)
    "FNKSB":    0x00C9, # ファンクション・キーの表示がアクティブかどうかFNKFLG (0xFBCE)をチェックし、アクティブなら表示、でなければ消す
    "ERAFNK":   0x00CC, # ファンクション・キーの表示を消す
    "DSPFNK":   0x00CF, # ファンクション・キーを表示
    "TOTEXT":   0x00D2, # 画面を強制的にテキストモードにする
    "GTSTCK":   0x00D5, # ジョイスティックの状態を返す IN:A=スティック番号
    "GTTRIG":   0x00D8, # トリガボタンの状態を返す IN:A=ボタン番号
    "GTPAD":    0x00DB, # タッチパッドの状態を返す IN:A=タッチパッド番号
    "GTPDL":    0x00DE, # パドルの値を返す IN:A=パドル番号
    "TAPION":   0x00E1, # カセットのモーター ON の後、ヘッダ・ブロックを読む 敗した場合は CY フラグをセット
    "TAPIN":    0x00E4, # テープからデータを読む A にデータ。失敗した場合は CY フラグをセット
    "TAPIOF":   0x00E7, # テープからの読み込みをストップ
    "TAPOON":   0x00EA, # カセットのモーター ON の後、ヘッダ・ブロックを書き込む
                        # IN :A ＝ 0 ならショート・ヘッダ
                        #     A ≠ 0 ならロング・ヘッダ
                        # RET:失敗した場合は CY フラグをセット
    "TAPOUT":   0x00ED, # テープにデータを書き込む A にデータ 失敗した場合は CY フラグをセット
    "TAPOOF":   0x00F0, # テープへの書き込みをストップ 失敗した場合は CY フラグをセット
    "STMOTR":   0x00F3, # カセットのモーターの動作設定 A=0:STOP 1:START 255:状態を反転
    "LFTQ":     0x00F6, # [非公開] キュー内のバイト数
    "PUTQ":     0x00F9, # [非公開] キューに追加
    "RIGHTC":   0x00FC, # [非公開] 画面のピクセルを右にシフトします
    "LEFTC":    0x00FF, # [非公開] 画面のピクセルを左にシフトします
    "UPC":      0x0102, # [非公開] 画面のピクセルを上にシフトします
    "TUPC":     0x0105, # [非公開] UPC が可能かどうかをテストし、可能であればUPCを実行します / Cy:操作が画面外で終了する
    "DOWNC":    0x0108, # [非公開] 画面のピクセルを下にシフトします
    "TDOWNC":   0x010B, # [非公開] DOWNC が可能かどうかをテストし、可能であればDOWNCを実行します / Cy:操作が画面外で終了する
    "SCALXY":   0x010E, # [非公開] Scales X and Y coordinates
    "MAPXYC":   0x0111, # [非公開] Places cursor at current cursor address
    "FETCHC":   0x0114, # [非公開] Gets current cursor addresses mask pattern
                        #          ret: HL - Cursor address
                        #               A  - Mask pattern
    "STOREC":   0x0117, # [非公開] Record current cursor addresses mask pattern
                        #          in:  HL - Cursor address
                        #               A  - Mask pattern
    "SETATR":   0x011A, # [非公開] Set attribute byte
    "READC":    0x011D, # [非公開] Reads attribute byte of current screen pixel
    "SETC":     0x0120, # [非公開] 指定されたattribute byteの現在の画面ピクセルを返します
    "NSETCX":   0x0123, # [非公開] Set horizontal screen pixels
    "GTASPC":   0x0126, # [非公開] Gets screen relations DE,HL
    "PNTINI":   0x0129, # [非公開] Initalises the PAINT instruction
    "SCANR":    0x012C, # [非公開] Scans screen pixels to the right
    "SCANL":    0x012F, # [非公開] Scans screen pixels to the left
    "CHGCAP":   0x0132, # CAPSランプの状態を変更 A=0:OFF 0以外:ON
    "CHGSND":   0x0135, # 1 ビット・サウンドポートの状態を変える A=0:OFF 0以外:ON
    "RSLREG":   0x0138, # 基本スロット・レジスタに現在出力している内容を読む
    "WSLREG":   0x013B, # 基本スロット・レジスタにデータを書き込む
    "RDVDP":    0x013E, # VDP のステータス・レジスタを読む
    "SNSMAT":   0x0141, # キーボード・マトリクスからAで指定した行の値を読む
    "PHYDIO":   0x0144, # [非公開] Executes I/O for mass-storage media like disks
                        # Input    : F  - Set carry to write, reset carry to read
                        #            A  - Drive number (0 = A:, 1 = B:, etc.)
                        #            B  - Number of sectors
                        #            C  - Media ID of the disk
                        #            DE - Begin sector
                        #            HL - Begin address in memory
                        # Output   : F  - Carry set on error
                        #            A  - Error code (only if carry set)
                        #                 0 = Write protected
                        #                 2 = Not ready
                        #                 4 = Data error
                        #                 6 = Seek error
                        #                 8 = Record not found
                        #                 10 = Write error
                        #                 12 = Bad parameter
                        #                 14 = Out of memory
                        #                 16 = Other error
                        #            B  - Number of sectors actually written or read
                        # Registers: All
                        # Remark   : Interrupts may be disabled afterwards. On some hard disk interfaces,
                        #            when bit 7 of register C is set, a 23-bit addressing scheme is used
                        #            and bits 0-6 of register C contain bits 23-16 of the sector number.
    "FORMAT":   0x0147, # [非公開] Initialises mass-storage media like formatting of disks
    "ISFLIO":   0x014A, # デバイスが動作中かどうかチェック
    "OUTDLP":   0x014D, # プリンタ出力。LPTOUT とは次の点で異なる
                        # 1. TAB はスペースに展開される
                        # 2. MSX 仕様でないプリンタの場合、ひらがなをカタカナに、グラフィック文字を 1 バイト文字に変換する
                        # 3. 失敗した場合、device I/O error となる
    "GETVCP":   0x0150, # [非公開] Returns pointer to play queue in: A=Channel,  ret: HL=Pointer
    "GETVC2":   0x0153, # [非公開] Returns pointer to variable in queue number VOICEN (byte at # FB38)
                        #          Input    : L  - Pointer in play buffer
                        #          Output   : HL - Pointer
    "KILBUF":   0x0156, # キーボード・バッファをクリア
    "CALBAS":   0x0159, # BASIC インタープリタ内のルーチンをインタースロット・コール IX=アドレス

    # ● MSX 2 BIOS Entries
    "SUBROM":   0x015C, # SUB-ROM をインタースロット・コール IX に呼び出すアドレス、同時に IX をスタックに積む
                        # 裏レジスタと IY はリザーブされる
    "EXTROM":   0x015F, # SUB-ROM をインタースロット・コール IX に呼び出すアドレス。
                        # 裏レジスタと IY はリザーブされる
    "CHKSLZ":   0x0162, # [非公開] Search slots for SUB-ROM
    "CHKNEW":   0x0165, # [非公開] Tests screen mode ret:Carry flag set if screenmode = 5, 6, 7 or 8
    "EOL":      0x0168, # 行の終わりまでデリート
    "BIGFIL":   0x016B, # VRAMをFILL HL=アドレス, BC=長さ, A=データ
                        # 機能的には FILVRM と同じ。ただし、以下の点で異なる。
                        # FILVRM では、スクリーン・モードが 0 ～ 3 であるかをチェックし、もしそうなら VDP は 16K バイトの VRAM しか持っていないものとして扱う (MSX1 とのコンパチビリティのため)。しかし、BIGFIL はモードのチェックは行わず、与えられたパラメータどおりに動作する
    "NSETRD":   0x016E, # VDP にアドレスをセットして、読み込める状態にする
    "NSTWRT":   0x0171, # VDP にアドレスをセットして、書き込める状態にする
    "NRDVRM":   0x0174, # VRAM の内容を読む
    "NWRVRM":   0x0177, # VRAM にデータを書き込む

    # ● MSX 2+ BIOS Entries
    "RDBTST":   0x017A, # RESETポートの内容を読み出します。
    "RDRES":    0x017A,
    "WRBTST":   0x017D, # RESETポートに値を書き込みます。ハードウェアリセットをシミュレートするときは、AレジスタのMSBを0にして、このBIOSをコールした後、BIOSの0番地にジャンプします。
    "WRRES":    0x017D,

    # ● MSX turbo-R BIOS Entries
    "CHGCPU":   0x0180, # CPUを切り換えます。A=0:Z80, 1:R800 ROM, 2:R800 DRAM, 0x80:LEDの変化あり。 変更後は、割り込みは許可されます。
    "GETCPU":   0x0183, # 現在、どちらのCPUが動作しているかを調べます
    "PCMPLY":   0x0186, # PCMのデータを再生します。
                        # in:  A: b0-1:サンプリングレート b7:VRAM/RAM
                        #         サンプリングレート
                        #           00: 15.75KHz
                        #           01: 7.875KHz
                        #           10: 5.25KHz
                        #           11: 3.9375KHz
                        #         メモリ
                        #           0: メインメモリ
                        #           1: VRAM
                        #      HL: CMデータのアドレス
                        #          VRAM指定時は、EレジスタとHLレジスタとをあわせて、3バイトで設定します。Eレジスタが最上位バイトです。
                        #      BC: PCMデータの長さ
                        #          VRAM指定時は、DレジスタとBCレジスタとをあわせて、3バイトで設定します。Dレジスタが最上位バイトです。
                        # Ret: Cy: 結果 0:正常, 1=異常
                        #      A:  原因 1:サンプリングレートの誤り 2:STOPによる中断1
                        #      HL: 終了時アドレス
                        #          VRAM指定時は、EレジスタとHLレジスタとをあわせて、3バイトで設定します。Eレジスタが最上位バイトです。
    "PCMREC":   0x0189, # PCMのデータを録音します。
                        # in:  A: b0-1:サンプリングレート b2:圧縮 b6-3:トリガーレベル b7:VRAM/RAM
                        #         サンプリングレート
                        #           00: 15.75KHz
                        #           01: 7.875KHz
                        #           10: 5.25KHz
                        #           11: 3.9375KHz
                        #         メモリ
                        #           0: メインメモリ
                        #           1: VRAM
                        #      HL: CMデータのアドレス
                        #          VRAM指定時は、EレジスタとHLレジスタとをあわせて、3バイトで設定します。Eレジスタが最上位バイトです。
                        #      BC: PCMデータの長さ
                        #          VRAM指定時は、DレジスタとBCレジスタとをあわせて、3バイトで設定します。Dレジスタが最上位バイトです。
                        # Ret: Cy: 結果 0:正常, 1=異常
                        #      A:  原因 1:サンプリングレートの誤り 2:STOPによる中断1
                        #      HL: 終了時アドレス
                        #          VRAM指定時は、EレジスタとHLレジスタとをあわせて、3バイトで設定します。Eレジスタが最上位バイトです。
})

msx_symbols_work = BidirectionalDict({
    # -----------------------------------------------------------------------------
    # ● ● WORK AREA (RAM)
    # -----------------------------------------------------------------------------
    # ● DISKコール
    "BLDCHK":   0xF378, # (3)   BLOADルーチン
    "BSVCHK":   0xF378, # (3)   BSAVEルーチン
    "ROMBDOS":  0xF37D, # (3)   BDOS function DOSファンクションコール
    "BDOS":     0xF37D,
    # H_PHYD: equ 0xFFA7 # 物理ディスクアクセス：0xC9以外ならばドライブが接続されている

    # ● インタースロットのリード、ライトコール用サブルーチン
    "RDPRIM":   0xF380, # (5)   基本スロットからの読み込み
    "WRPRIM":   0xF385, # (7)   基本スロットへ書き込み
    "CLPRIM":   0xF38C, # (14)  基本スロットコール

    # ● 公開ディスクワークエリア
    "H_PROM":   0xF24F, # (3)   2ドライブシミュレーション表示フック (A=ドライブ文字)
    "HPROM":    0xF24F,
    "H_PROMPT": 0xF24F,
    "HPROMPT":  0xF24F,
    "DISKVE":   0xF323, # (2)   ディスクエラーが起きた時にジャンプするアドレス
                        #       This error handling routine must
                        #       Error handling routine receives:
                        #       C: Error code:
                        #             X x x x X X X X
                        #             |       | | | |
                        #             |       | | | +------------ 1 - Writing / 0 - Reading
                        #             |       | | +----- 0 1 1 # 
                        #             |       | +------- 0 0 0 # - Disk error (other)
                        #             |       +--------- 1 0 1 # 
                        #             |                  | | +--- Unsupported media
                        #             |                  | +----- Not ready
                        #             |                  +------- Write protect
                        #             +-------------------------- 1 - Bad FAT
                        #       And must return register C: 0=Ignore, 1=Retry, 2=Abort
    "BREAKV":   0xF325, # (2)   CTRL+Cが押された時にコールされるアドレス
    "RTCFOUND": 0xF338, # (1)   リアルタイムクロックの有無 A:0=ない 1=ある
    "RAMAD0":   0xF341, # (2)   PAGE0のRAMスロット番号
    "RAMAD1":   0xF342, # (2)   PAGE1のRAMスロット番号
    "RAMAD2":   0xF343, # (2)   PAGE2のRAMスロット番号
    "RAMAD3":   0xF344, # (2)   PAGE3のRAMスロット番号
    "DSKSYS":   0xF436, # (1)   0以外の値を書き込むとBASICからDOSへ行ける
    "MASTER":   0xF348, # (1)   マスターディスクインターフェイスROMスロット
    "DSKRSLT":  0xF348,
    "HIMSAV":   0xF349, # (2)   ディスクインターフェイスワークエリアの先頭番地
    "SECBUF":   0xF34D, # (2)   ディスクドライバ用セクターバッファの先頭番地
    "BUFFER":   0xF34F, # (2)   DOS汎用セクターバッファの先頭番地
    "DIRBUF":   0xF351, # (2)   DOSディレクトリー用セクターバッファの先頭番地
    "FCBBASE":  0xF353, # (2)   FCBエントリの先頭番地
    "DPBLIST":  0xF355, # (2)   DPBテーブルの先頭番地
    "DRVTBL":   0xFB21, # (8)   ディスクインターフェースROM情報
                        #       +0: 第1ディスクインターフェースROMに接続背れている論理ドライブの数
                        #       +1: 第1ディスクインターフェースROMのスロット番号
                        #       +2: 第2ディスクインターフェースROMに接続背れている論理ドライブの数
                        #       +3: 第2ディスクインターフェースROMのスロット番号
                        #       +4: 第3ディスクインターフェースROMに接続背れている論理ドライブの数
                        #       +5: 第3ディスクインターフェースROMのスロット番号
                        #       +6: 第4ディスクインターフェースROMに接続背れている論理ドライブの数
                        #       +7: 第4ディスクインターフェースROMのスロット番号

    # ● USR関数のマシン語プログラムの開始アドレス、テキスト画面
    "USRTAB":   0xF39A, # (20)  (初期値 FCERR) USR関数のマシン語プログラム(0～9)の開始番地、機械語プログラム定義前の値はすべてエラールーチンFCERR(0x475A)を指す
    "LINL40":   0xF3AE, # (1)   (初期値 39) SCREEN0のときの1行の幅(SCREEN0のときのWIDTH文により設定される)
    "LINL32":   0xF3AF, # (1)   (初期値 29) SCREEN1のときの1行の幅(SCREEN1のときのWIDTH文により設定される)
    "LINLEN":   0xF3B0, # (1)   (初期値 29) 現在の画面の1行の幅
    "CRTCNT":   0xF3B1, # (1)   (初期値 24) 現在の画面の行数
    "CLMLST":   0xF3B2, # (1)   (初期値 14) PRINT命令において各項目がカンマで区切られている場合の横位置

    # ● 初期化用ワーク
                        #     === SCREEN 0 ===
    "TXTNAM":   0xF3B3, # (2)   (初期値 0x0000) パターンネーム・テーブル
    "TXTCOL":   0xF3B5, # (2)   (初期値 0x0800) カラーテーブル(MSX2、MSX2+のみ)
    "TXTCGP":   0xF3B7, # (2)   (初期値 0x0800) パターンジェネレータ・テーブル
    "TXTATR":   0xF3B9, # (2)   使用せず
    "TXTPAT":   0xF3BB, # (2)   使用せず
                        #     === SCREEN 1 ===
    "T32NAM":   0xF3BD, # (2)   (初期値 0x1800) パターンネーム・テーブル
    "T32COL":   0xF3BF, # (2)   (初期値 0x2000) カラーテーブル
    "T32CGP":   0xF3C1, # (2)   (初期値 0x0000) パターンジェネレータ・テーブル
    "T32ATR":   0xF3C3, # (2)   (初期値 0x1B00) スプライトアトリビュート・テーブル
    "T32PAT":   0xF3C5, # (2)   (初期値 0x3800) スプライト・ジェネレータ・テーブル
                        #     === SCREEN 2 ===
    "GRPNAM":   0xF3C7, # (2)   (初期値 0x1800) パターンネーム・テーブル
    "GRPCOL":   0xF3C9, # (2)   (初期値 0x2000) カラーテーブル
    "GRPCGP":   0xF3CB, # (2)   (初期値 0x0000) パターンジェネレータ・テーブル
    "GRPATR":   0xF3CD, # (2)   (初期値 0x1B00) スプライトアトリビュート・テーブル
    "GRPPAT":   0xF3CF, # (2)   (初期値 0x3800) スプライト・ジェネレータ・テーブル
                        #     === SCREEN 3 ===
    "MLTNAM":   0xF3D1, # (2)   (初期値 0x0800) パターンネーム・テーブル
    "MLTCOL":   0xF3D3, # (2)   使用せず
    "MLTCGP":   0xF3D5, # (2)   (初期値 0x0000) パターンジェネレータ・テーブル
    "MLTATR":   0xF3D7, # (2)   (初期値 0x1B00) スプライトアトリビュート・テーブル
    "MLTPAT":   0xF3D9, # (2)   (初期値 0x3800) スプライト・ジェネレータ・テーブル

    # ● その他のスクリーン設定
    "CLIKSW":   0xF3DB, # (1)   (初期値 1) キークリックスイッチ(0=OFF、0以外=ON)。SCREEN文の<キークリックスイッチ>により設定される
    "CSRY":     0xF3DC, # (1)   (初期値 1) カーソルのY座標
    "CSRX":     0xF3DD, # (1)   (初期値 1) カーソルのX座標
    "CNSDFG":   0xF3DE, # (1)   (初期値 0) ファンクションキー表示スイッチ(0=表示あり、0以外=表示なし)。KEY ON/OFF文によって設定される

    # ● VDPレジスタのセーブエリアなど
    "RG0SAV":   0xF3DF, # (1)   (初期値 0)
    "RG1SAV":   0xF3E0, # (1)   (初期値 0)
    "RG2SAV":   0xF3E1, # (1)   (初期値 0)
    "RG3SAV":   0xF3E2, # (1)   (初期値 0)
    "RG4SAV":   0xF3E3, # (1)   (初期値 0)
    "RG5SAV":   0xF3E4, # (1)   (初期値 0)
    "RG6SAV":   0xF3E5, # (1)   (初期値 0)
    "RG7SAV":   0xF3E6, # (1)   (初期値 0)
    "STATFL":   0xF3E7, # (1)   (初期値 0)  VDPのステータスを保存(MSX2ではステータスレジスタ0の内容)
    "TRGFLG":   0xF3E8, # (1)   (初期値 0xFF) ジョイスティックのトリガボタンの状態を保存する
    "FORCLR":   0xF3E9, # (1)   (初期値 15) 前景色。COLOR文で設定される
    "BAKCLR":   0xF3EA, # (1)   (初期値 4)  背景色。COLOR文で設定される
    "BDRCLR":   0xF3EB, # (1)   (初期値 7)  周辺色。COLOR文で設定される
    "MAXUPD":   0xF3EC, # (3)   (初期値 JP 0x0000:0xC3,0x00,0x00) CIRCLE文が内部で使用
    "MINUPD":   0xF3EF, # (3)   (初期値 JP 0x0000:0xC3,0x00,0x00) CIRCLE文が内部で使用
    "ATRBYT":   0xF3F2, # (1)   (初期値 15) グラフィック使用時のカラーコード

    # ● VDPレジスタのセーブエリア(MSX2,2+)
    "RG8SAV":   0xFFE7, # (1)   VDPレジスタ# 8のセーブエリア
    "RG9SAV":   0xFFE8, # (1)   VDPレジスタ# 9のセーブエリア
    "RG10SAV":  0xFFE9, # (1)   VDPレジスタ# 10のセーブエリア
    "RG11SAV":  0xFFEA, # (1)   VDPレジスタ# 11のセーブエリア
    "RG12SAV":  0xFFEB, # (1)   VDPレジスタ# 12のセーブエリア
    "RG13SAV":  0xFFEC, # (1)   VDPレジスタ# 13のセーブエリア
    "RG14SAV":  0xFFED, # (1)   VDPレジスタ# 14のセーブエリア
    "RG15SAV":  0xFFEE, # (1)   VDPレジスタ# 15のセーブエリア
    "RG16SAV":  0xFFEF, # (1)   VDPレジスタ# 16のセーブエリア
    "RG17SAV":  0xFFF0, # (1)   VDPレジスタ# 17のセーブエリア
    "RG18SAV":  0xFFF1, # (1)   VDPレジスタ# 18のセーブエリア
    "RG19SAV":  0xFFF2, # (1)   VDPレジスタ# 19のセーブエリア
    "RG20SAV":  0xFFF3, # (1)   VDPレジスタ# 20のセーブエリア
    "RG21SAV":  0xFFF4, # (1)   VDPレジスタ# 21のセーブエリア
    "RG22SAV":  0xFFF5, # (1)   VDPレジスタ# 22のセーブエリア
    "RG23SAV":  0xFFF6, # (1)   VDPレジスタ# 23のセーブエリア
    #        equ 0xFFF7 # (3)   システム予約
    "RG25SAV":  0xFFFA, # (1)   VDPレジスタ# 25のセーブエリア
    "RG26SAV":  0xFFFB, # (1)   VDPレジスタ# 26のセーブエリア
    "RG27SAV":  0xFFFC, # (1)   VDPレジスタ# 27のセーブエリア
    #        equ 0xFFFD # (2)   システム予約

    # ● PLAY文用ワークエリア
    "QUEUES":   0xF3F3, # (2)   (初期値 QUETAB(0xF959)) PLAY文実行時のキューテーブルを指す
    "FRCNEW":   0xF3F5, # (1)   (初期値 255) BASICインタープリタが内部で使用する

    # ● キー入力用ワークエリア
    "SCNCNT":   0xF3F6, # (1)   (初期値 1) キースキャンの時間間隔
    "REPCNT":   0xF3F7, # (1)   (初期値 50) キーのオートリピートが開始するまでの時間
    "PUTPNT":   0xF3F8, # (2)   (初期値 KEYBUF(0xFBF0)) キーバッファへの書き込みを行う番地を指す
    "GETPNT":   0xF3FA, # (2)   (初期値 KEYBUF(0xFBF0)) キーバッファからの読み込みを行う番地を指す

    # ● カセット用パラメータ
    "CS120":    0xF3FC, # (5*2) 波形ビット
                        #       ・1200ボー
                        #         内容(値)
                        #           83(LOW01)  ………ビット0を表すLOWの幅
                        #           92(HIGH01) ………ビット0を表すHIGHの幅
                        #           38(LOW11)  ………ビット1を表すLOWの幅
                        #           45(HIGH11) ………ビット1を表すHIGHの幅
                        #           HEADLEN*2/256  …ショートヘッダ用のヘッダビットのHIGHバイト(HEDLEN=2000)
                        #       ・2400ボー
                        #         内容(値)
                        #           37(LOW02)  ………ビット0を表すLOWの幅
                        #           45(HIGH02) ………ビット0を表すHIGHの幅
                        #           14(LOW12)  ………ビット1を表すLOWの幅
                        #           22(HIGH12) ………ビット1を表すHIGHの幅
                        #           HEADLEN*4/256  …ショートヘッダ用のヘッダビットのHighバイト(HEDLEN=2000)
    "LOW":      0xF406, # (2)   (初期値 LOW01, HIGH01) (デフォルト1200ボー) 現在のボーレートのビット0を表すLOWとHIGHの幅。SCREEN文の<カセットボーレート>により設定される
    "HIGH":     0xF408, # (2)   (初期値 LOW11, HIGH11) (デフォルト1200ボー) 現在のボーレートのビット1を表すLOWとHIGHの幅。SCREEN文の<カセットボーレート>により設定される
    "HEADER":   0xF40A, # (1)   (初期値 HEADLEN*2/256) (デフォルト1200ボー) 現在のボーレートのショートヘッダ用のヘッダビット(HEDLEN=2000)。SCREEN文の<カセットボーレート>により設定される
    "ASPCT1":   0xF40B, # (2)   256/アスペクト比。CIRCLE文で使用するためにSCREEN文で設定される
    "ASPCT2":   0xF40D, # (2)   256*アスペクト比。CIRCLE文で使用するためにSCREEN文で設定される
    "ENDPRG":   0xF40F, # (5)   (初期値 “:”) RESUME NEXT文のための仮のプログラムの終わり

    # ● BASICが内部で使うワーク
    "ERRFLG":   0xF414, # (1)   エラー番号を保存するためのエリア
    "LPTPOS":   0xF415, # (1)   (初期値 0) プリンタのヘッド位置
    "PRTFLG":   0xF416, # (1)   プリンタへ出力するかどうかのフラグ
    "NTMSXP":   0xF417, # (1)   プリンタ種別(0=MSX用プリンタ、0以外=MSX用プリンタでない)
    "RAWPRT":   0xF418, # (1)   raw-modeでプリント中なら0以外
    "VLZADR":   0xF419, # (2)   VAL関数で置き換えられる文字のアドレス
    "VLZDAT":   0xF41B, # (1)   VAL関数で0に置き換わる文字
    "CURLIN":   0xF41C, # (2)   BASICが現在実行中の行番号
    "KBUF":     0xF41F, # (318) クランチバッファ。BUF(0xF55E)から中間言語に直されて入る
    "BUFMIN":   0xF55D, # (1)   (初期値 “,”) INPUT文で使われる
    "BUF":      0xF55E, # (258) タイプした文字が入るバッファ。ダイレクトステートメントがアスキーコードで入る
    "ENDBUF":   0xF660, # (1)   BUF(0xF55E)がオーバーフローするのを防ぐ
    "TTYPOS":   0xF661, # (1)   BASICが内部で持つ仮想的なカーソル位置
    "DIMFLG":   0xF662, # (1)   BASICが内部で使用する
    "VALTYP":   0xF663, # (1)   変数の型の識別に使用する
    "DORES":    0xF664, # (1)   保存されている語がクランチできるかどうかを示す
    "DONUM":    0xF665, # (1)   クランチ用のフラグ
    "CONTXT":   0xF666, # (2)   CHRGETで使うテキストアドレスの保存
    "CONSAV":   0xF668, # (1)   CHRGETが呼ばれた後の定数のトークンを保存
    "CONTYP":   0xF669, # (1)   保存した定数のタイプ
    "CONLO":    0xF66A, # (8)   保存した定数の値
    "MEMSIZ":   0xF672, # (2)   BASICが使用するメモリの最上位番地
    "STKTOP":   0xF674, # (2)   BASICがスタックとして使用する番地。CLEAR文により変化する
    "TXTTAB":   0xF676, # (2)   BASICテキストエリアの先頭番地
    "TEMPPT":   0xF678, # (2)   (初期値 TEMPST(0xF67A)) テンポラリディスクリプタの空きエリアの先頭番地
    "TEMPST":   0xF67A, # (30)  NUMTEMP用の領域 (3 * NUMTMP)
    "DSCTMP":   0xF698, # (3)   ストリング関数の答えのストリングディスクリプタが入る
    "FRETOP":   0xF69B, # (2)   文字列領域の空きエリアの先頭番地
    "TEMP3":    0xF69D, # (2)   ガベージコレクションやUSR関数などに使われる
    "TEMP8":    0xF69F, # (2)   ガベージコレクション用
    "ENDFOR":   0xF6A1, # (2)   FOR文の次の番地を保存する(ループ時にFOR文の次から実行するため)
    "DATLIN":   0xF6A3, # (2)   READ文の実行により読まれたDATA文の行番号
    "SUBFLG":   0xF6A5, # (1)   USR関数などで配列を使うときのフラグ
    "FLGINP":   0xF6A6, # (1)   INPUTやREADで使われるフラグ
    "TEMP":     0xF6A7, # (2)   ステートメントコードのための一時保存場所。変数ポインタ、テキストアドレスなどに使用する
    "PTRFLG":   0xF6A9, # (1)   変換する行番号がなければ0、あれば0以外
    "AUTFLG":   0xF6AA, # (1)   AUTOコマンド有効、無効フラグ(0以外=有効中、0=無効中)
    "AUTLIN":   0xF6AB, # (2)   一番新しく入力された行番号
    "AUTINC":   0xF6AD, # (2)   (初期値 10) AUTOコマンドの行番号の増分値
    "SAVTXT":   0xF6AF, # (2)   実行中のテキストのアドレスを保存する領域。主にRESUME文によりエラー回復で使用される
    "SAVSTK":   0xF6B1, # (2)   スタックを保存する領域。主にエラーが起きたとき、エラー回復ルーチンがスタックをリストアするために使用される
    "ERRLIN":   0xF6B3, # (2)   エラーが起きたときの行番号
    "DOT":      0xF6B5, # (2)   何らかの形で画面に表示された、あるいは入力された最新の行番号
    "ERRTXT":   0xF6B7, # (2)   エラーが起きたテキストのアドレス。主にRESUME文によるエラー回復で使用される
    "ONELIN":   0xF6B9, # (2)   エラーが起きたときの飛び先行のテキストアドレス。ON ERROR GOTO文により設定される
    "ONEFLG":   0xF6BB, # (1)   エラールーチンの実行中を示すフラグ。(0以外=実行中、0=実行中でない)
    "TEMP2":    0xF6BC, # (2)   一時保存用
    "OLDLIN":   0xF6BE, # (2)   Ctrl+STOP、STOP命令、END命令で中断されたか、あるいは最後に実行された行番号
    "OLDTXT":   0xF6C0, # (2)   次に実行する文のテキストアドレス
    "VARTAB":   0xF6C2, # (2)   単純変数の開始番地。NEW文を実行すると〔TXTTAB(0xF676)の内容+2〕が設定される
    "ARYTAB":   0xF6C4, # (2)   配列テーブルの開始番地
    "STREND":   0xF6C6, # (2)   テキストエリアや変数エリアとして使用中であるメモリの最後の番地
    "DATPTR":   0xF6C8, # (2)   READ文の実行により読まれたデータのテキストアドレス
    "DEFTBL":   0xF6CA, # (26)  英文字1字に対し変数の型を保持するエリア。CLEAR、DEFSTR、!、# などの型宣言で変化する

    # ● ユーザー関数のパラメータに関するワーク
    "PRMSTK":   0xF6E4, # (2)   スタック上の以前の定義ブロック(ガベージコレクション用)
    "PRMLEN":   0xF6E6, # (2)   処理対象のテーブルのバイト数
    "PARM1":    0xF6E8, # (100) (PRMSIZ) 処理対象のパラメータ定義テーブル。
                        #       PRMSIZは定義ブロックのバイト数で初期値は100
    "PRMPRV":   0xF74C, # (2)   (初期値 PRMSTK) 以前のパラメータブロックのポインタ(ガベージコレクション用)
    "PRMLN2":   0xF74E, # (2)   パラメータブロックの大きさ
    "PARM2":    0xF750, # (100) パラメータの保存用
    "PRMFLG":   0xF7B4, # (1)   PARM1がサーチ済みかどうかを示すフラグ
    "ARYTA2":   0xF7B5, # (2)   サーチの終点
    "NOFUNS":   0xF7B7, # (1)   処理対象関数がない場合は0
    "TEMP9":    0xF7B8, # (2)   ガベージコレクション用の一時保存場所
    "FUNACT":   0xF7BA, # (2)   処理対象関数の数
    "SWPTMP":   0xF7BC, # (8)   SWAP文の最初の変数の値の一時保存場所
    "TRCFLG":   0xF7C4, # (1)   トレースフラグ。(0以外=TRACE ON、0=TRACE OFF)

    # ● Math-Pack用ワーク
    "FBUFFR":   0xF7C5, # (43)  マスパックが内部で使用する
    "DECTMP":   0xF7F0, # (2)   10進整数を不動小数点数にするときに使用する
    "DECTM2":   0xF7F2, # (2)   除算ルーチンの実行時に使用する
    "DECCNT":   0xF7F4, # (1)   除算ルーチンの実行時に使用する
    "DAC":      0xF7F6, # (16)  演算の対象となる値を設定するエリア
    "HOLD8":    0xF806, # (48)  10進数の乗算のためのレジスタ保存エリア
    "HOLD2":    0xF836, # (8)   マスパックが内部で使用する
    "HOLD":     0xF83E, # (8)   マスパックが内部で使用する
    "ARG":      0xF847, # (16)  DAC(0xF7F6)との演算対象となる値を設定するエリア
    "RNDX":     0xF857, # (8)   最新の乱数を倍精度実数で保存する。RND関数で設定される

    # ● BASICインタープリタが使うデータエリア
    "MAXFIL":   0xF85F, # (1)   ファイル番号の最大値。MAXFILES文により設定される
    "FILTAB":   0xF860, # (2)   ファイルデータエリアの先頭番地
    "NULBUF":   0xF862, # (2)   SAVE、LOADでBASICインタープリタが使用するバッファ
    "PTRFIL":   0xF864, # (2)   アクセス中のファイルのファイルデータがある番地
    "RUNFLG":   0xF866, # (0)   プログラムをロード後実行するなら0でない値。LOAD文のRオプションなどで使用する
    "FILNAM":   0xF866, # (11)  ファイル名の保存エリア
    "FILNM2":   0xF871, # (11)  ファイル名の保存エリア
    "NLONLY":   0xF87C, # (1)   プログラムロード中は0でない値となる
    "SAVEND":   0xF87D, # (2)   セーブするマシン語プログラムの最終番地
    "FNKSTR":   0xF87F, # (160) ファンクションキーの文字列保存エリア(16文字×10)
    "CGPNT":    0xF91F, # (3)   ROM上の文字フォント格納アドレス
    "NAMBAS":   0xF922, # (2)   現在のパターンネーム・テーブルのベース番地
    "CGPBAS":   0xF924, # (2)   現在のパターン・ジェネレーター・テーブルのベース番地
    "PATBAS":   0xF926, # (2)   現在のスプライト・ジェネレーター・テーブルのベース番地
    "ATRBAS":   0xF928, # (2)   現在のスプライトアトリビュート・テーブルのベース番地
    "CLOC":     0xF92A, # (2)   グラフィックルーチンが内部で使用する
    "CMASK":    0xF92C, # (1)   グラフィックルーチンが内部で使用する
    "MINDEL":   0xF92D, # (2)   グラフィックルーチンが内部で使用する
    "MAXDEL":   0xF92F, # (2)   グラフィックルーチンが内部で使用する

    # ● CIRCLE文で使うデータエリア
    "ASPECT":   0xF931, # (2)   円の縦横の比率。CLRCLE文の<比率>により設定される
    "CENCNT":   0xF933, # (2)   CIRCLE文が内部で使用する
    "CLINEF":   0xF935, # (1)   円の中心へ線を引くかどうかのフラグ。CIRCLE文の<角度>で指定
    "CNPNTS":   0xF936, # (2)   プロットする点
    "CPLOTF":   0xF938, # (1)   CIRCLE文が内部で使用する
    "CPCNT":    0xF939, # (2)   円の1/8分割の数
    "CPCNT8":   0xF93B, # (2)   CIRCLE文が内部で使用する
    "CRCSUM":   0xF93D, # (2)   CIRCLE文が内部で使用する
    "CSTCNT":   0xF93F, # (2)   CIRCLE文が内部で使用する
    "CSCLXY":   0xF941, # (1)   xとyのスケール
    "CSAVEA":   0xF942, # (2)   ADVGRPの保存エリア
    "CASVEM":   0xF944, # (1)   ADVGRPの保存エリア
    "CXOFF":    0xF945, # (2)   中心からのxのオフセット
    "CYOFF":    0xF947, # (2)   中心からのyのオフセット

    # ● PAINT文で使用するデータエリア
    "LOHMSK":   0xF949, # (1)   PAINT文が内部で使用する
    "LOHDIR":   0xF94A, # (1)   PAINT文が内部で使用する
    "LOHADR":   0xF94B, # (2)   PAINT文が内部で使用する
    "LOHCNT":   0xF94D, # (2)   PAINT文が内部で使用する
    "SKPCNT":   0xF94F, # (2)   スキップカウント
    "MIVCNT":   0xF951, # (2)   移動カウント
    "PDIREC":   0xF953, # (1)   ペイントの方向
    "LFPROG":   0xF954, # (1)   PAINT文が内部で使用する
    "RTPROG":   0xF955, # (1)   PAINT文が内部で使用する

    # ● PLAYで使うデータエリア
    "MCLTAB":   0xF956, # (2)   PLAYマクロ、あるいはDROWマクロのテーブルの先頭を指す
    "MCLFLG":   0xF958, # (1)   PLAY/DRAWの指示
    "QUETAB":   0xF959, # (24)  キューテーブル
                        #       +0 : PUT オフセット
                        #       +1 : GET オフセット
                        #       +2 : バックアップ・キャラクタ
                        #       +3 : キューの長さ
                        #       +4,5 : キューのアドレス
    "QUEBAK":   0xF971, # (4)   BCKQで使用する
    "VOICAQ":   0xF975, # (128) 音声1のキュー(1=a)
    "VOICBQ":   0xF9F5, # (128) 音声2のキュー(2=b)
    "VOICCQ":   0xFA75, # (128) 音声3のキュー(3=c)

    # ● MSX2で追加されたワークエリア
    "DFPAGE":   0xFAF5, # (1)   ディスプレイページ番号
    "ACPAGE":   0xFAF6, # (1)   アクティブページ番号
    "AVCSAV":   0xFAF7, # (1)   AVコントロールポートの保存
    "EXBRSA":   0xFAF8, # (1)   SUM-ROMのスロットアドレス
    "CHRCNT":   0xFAF9, # (1)   バッファ中のキャラクタのカウンタ。ローマ字カナ変換で使用(値は0<=n<=2)
    "ROMA":     0xFAFA, # (2)   バッファ中のキャラクタを入れておくエリア。ローマ字カナ変換で使用
    "MODE":     0xFAFC, # (1)   ローマ字カナ変換のモードスイッチとVRAMサイズ
                        #       〔Ｋ000ＷＶＶＣ〕
                        #       │ ││││
                        #       │ │││└ 1=変換する、0=変換しない
                        #       │ │││
                        #       │ │└┴─ 00=16KVRAM
                        #       │ │ 01=64KVRAM
                        #       │ │ 10=128KVRAM
                        #       │ │
                        #       │ └─── 0=マスクする、1=マスクしない
                        #       │ スクリーン0～3においてVRAMアドレスを指定するときに0x3FFFとANDを
                        #       │ とって設定するかどうかのフラグ、SCREEN4～8ではつねにマスクしない
                        #       └──────1=カタカナ、0=ひらがな
    "NORUSE":   0xFAFD, # (1)   漢字ドライバが使用
                        #       b7  : グラフィック・文字混在
                        #       b6  : SHIFT+カーソルで上下スクロール
                        #       b5-4: 内部で使用
                        #       b3-0: VDPロジカルオペレーション
    "XSAVE":    0xFAFE, # (2)   〔ＩＯＯＯＯＯＯＯ ＸＸＸＸＸＸＸＸ〕
    "YSAVE":    0xFB00, # (2)   〔×ＯＯＯＯＯＯＯ ＹＹＹＹＹＹＹＹ〕
                        #       Ｉ=1 ライトペンのインターラプト要求あり
                        #       ＯＯＯＯＯＯＯ　　=符号なしオフセット
                        #       ＸＸＸＸＸＸＸＸ　= X座標
                        #       ＹＹＹＹＹＹＹＹ　= Y座標
    "LOGOPR":   0xFB02, # (1)   ロジカル・オペレーション・コード

    # ● RS-232Cで使うデータエリア
    "RSTMP":    0xFB03, # (50)  RS-232Cまたはディスクのワークエリア
    "TOCNT":    0xFB03, # (1)   RS-2332Cルーチンが内部で使用する
    "RSFCB":    0xFB04, # (2)   0xFB04+0 : RS-232CのLOWアドレス
                        #       0xFB04+1 : RS-232CのHIGHアドレス
    "RSIQLN":   0xFB06, # (1)   RS-232Cルーチンが内部で使用する
    "MEXBIH":   0xFB07, # (5)   0xFB07+0 : RST 0x30(0xF7)
                        #       0xFB07+1 : バイトデータ      # 0xFB07+2 : (Low)
                        #       0xFB07+3 : (Hogh)    # 0xFB07+4 : RET (0xC9)
    "OLDSTT":   0xFB0C, # (5)   0xFB0C+0 : RST 0x30(0xF7)
                        #       0xFB0C+1 : バイトデータ      # 0xFB0C+2 : (Low)
                        #       0xFB0C+3 : (Hogh)    # 0xFB0C+4 : RET (0xC9)
    "OLDINT":   0xFB12, # (5)   0xFB12+0 : RST 0x30(0xF7)
                        #       0xFB12+1 : バイトデータ      # 0xFB12+2 : (Low)
                        #       0xFB12+3 : (Hogh)    # 0xFB12+4 : RET (0xC9)
    "DEVNUM":   0xFB17, # (1)   RS-232Cルーチンが内部で使用する
    "DATCNT":   0xFB18, # (3)   0xFB18+0 : バイトデータ
                        #       0xFB18+1 : バイトポインタ
                        #       0xFB18+2 : バイトポインタ
    "ERRORS":   0xFB1B, # (1)   RS-232Cルーチンが内部で使用する
    "FLAGS":    0xFB1B, # (1)   RS-232Cルーチンが内部で使用する
    "ESTBLS":   0xFB1D, # (1)   RS-232Cルーチンが内部で使用する
    "COMMSK":   0xFB1E, # (1)   RS-232Cルーチンが内部で使用する
    "LSTCOM":   0xFB1F, # (1)   RS-232Cルーチンが内部で使用する
    "LSTMOD":   0xFB20, # (1)   RS-232Cルーチンが内部で使用する

    # ● DOSが使用するデータエリア
    # リザーブ(0xFB21～0xFB34) DOSが使用する

    # ● PLAY文が使用するデータエリア　(以下はMSX1と共通)
    "PRSCNT":   0xFB35, # (1)   D1～D0 文字列パース
                        #       D7=0 1パス
    "SAVSP":    0xFB36, # (2)   プレー中のスタックポインタを保存
    "VOICEN":   0xFB38, # (1)   解釈中の現在の音声
    "SAVVOL":   0xFB39, # (2)   休止のために音量を保存する
    "MCLLEN":   0xFB39, # (1)   PLAY文が内部で使用する
    "MCLPTR":   0xFB3C, # (2)   PLAY文が内部で使用する
    "QUEUEN":   0xFB3E, # (1)   PLAY文が内部で使用する
    "MUSICF":   0xFB3F, # (1)   音楽演奏用の割り込みフラグ
    "PLYCNT":   0xFB40, # (1)   キューに格納されているPLAY文の数

    # ● 音声スタティックデータエリアからの変位　(変位は10進数)
    #"METREX":    0,     # (2)   タイマカウントダウン
    #"VCXLEN":    2,     # (1)   この音声のためのMCLLEN
    #"VCXPTR":    3,     # (2)   この音声のためのMCLPTR
    #"VCXSTP":    5,     # (2)   スタックポインタの先頭を保存
    #"QLENGX":    7,     # (1)   キューに格納されるバイト数
    #"NTICSX":    8,     # (2)   新しいカウントダウン
    #"TONPRX":   10,     # (2)   トーンの周期を設定するエリア
    #"AMPPRX":   12,     # (1)   音量、エンベロープの区別
    #"ENVPRX":   13,     # (2)   エンベロープの周期を設定するエリア
    #"OCTAVX":   15,     # (1)   オクターブを設定するエリア
    #"NOTELX":   16,     # (1)   音の長さを設定するエリア
    #"TEMPOX":   17,     # (1)   テンポを設定するエリア
    #"VOLUMX":   18,     # (1)   音量を設定するエリア
    #"ENVLPX":   19,     # (14)  エンベロープの波形を設定するエリア
    #"MCLSTX":   33,     # (3)   スタックの保存場所
    #"MCLSEX":   36,     # (1)   初期化スタック
    #"VCBSIZ":   37,     # (1)   スタティックバッファの大きさ

    # ● 音声スタティック・データエリア
    "VCBA":     0xFB41, # (37)  音声0のスタティックデータ
    "VCBB":     0xFB66, # (37)  音声1のスタティックデータ
    "VCBC":     0xFB8B, # (37)  音声2のスタティックデータ

    # ● データエリア
    "ENSTOP":   0xFBB0, # (1)   [SHIFT+Ctrl+GRAPH+かなキー]によるウォームスタートを可能にするフラグ(0=不可能、0以外=可能)
    "BASROM":   0xFBB1, # (1)   BASICテキストの存在場所を示す(0=RAM上、0以外=ROM上)
    "LINTTB":   0xFBB2, # (24)  ラインターミナルテーブル。テキスト画面の各行の情報を保持するエリア（0=次の行に続く、0xAF=次の行に続かない）
    "FSTPOS":   0xFBCA, # (2)   BIOSのINLIN(0x00B1)で入力した行の最初の文字の位置
    "CODSAV":   0xFBCC, # (1)   カーソルが重なった部分のキャラクタを保存するエリア
    "FNKSWI":   0xFBCD, # (1)   KEY ON時にどのファンクションキーが表示されているか表す(1=F1～F5が表示、0=F6～F10が表示)
    "FNKFLG":   0xFBCE, # (10)  ON KEY GOSUB文により定義された行の実行を許可、禁止、停止するかファンクションキーごとに保存するためのエリア。KEY(n)ON/OFF/STOP文により設定される(0=KEY(n)OFF/STOP、1=KEY(n)ON)
    "ONGSBF":   0xFBD8, # (1)   TRPTBL(0xFC4C)で待機中のイベントが発生したかどうかのフラグ
    "CLIKFL":   0xFBD9, # (1)   キークリック・フラグ
    "OLDKEY":   0xFBDA, # (11)  キーマトリクスの状態(旧)
    "NEWKEY":   0xFBE5, # (11)  キーマトリクスの状態(新)
    "KEYBUF":   0xFBF0, # (40)  キーコードバッファ
    "LINWRK":   0xFC18, # (40)  スクリーンハンドラが使う一時保存場所
    "PATWRK":   0xFC40, # (8)   パターンコンバータが使う一時保存場所
    "BOTTOM":   0xFC48, # (2)   実装したRAMの先頭(低位)番地。MSX2では通常0x8000
    "HIMEM":    0xFC4A, # (2)   利用可能なメモリーの上位番地。CLEAR文の<メモリ上限>により設定される
    "TRPTBL":   0xFC4C, # (78)  割り込み処理で使うトラップテーブル。ひとつのテーブルは3バイトで構成される1バイト目がON/OFF/STOP状態を表し、残りが分岐先のテキストアドレスを表す
                        #       0xFC4C～0xFC69(3*10バイト) ← ON KEY GOSUBで使用
                        #       0xFC6A～0xFC6C(3*1バイト) ← ON STOP GOSUBで使用
                        #       0xFC6D～0xFC6F(3*1バイト) ← ON SPRITE GOSUBで使用
                        #       0xFC70～0xFC7E(3*5バイト) ← ON STRIG GOSUBで使用
                        #       0xFC7F～0xFC81(3*1バイト) ← ON INTERVAL GOSUBで使用
                        #       0xFC82～0xFC99 ← 拡張用
    "RTYCNT":   0xFC9A, # (1)   BASICが内部で使用する
    "INTFLG":   0xFC9B, # (1)   Ctrl+STOPが押された場合など、ここに0x03を入れることによりストップする
    "PADY":     0xFC9C, # (1)   パドルのY座標
    "PADX":     0xFC9D, # (1)   パドルのX座標
    "JIFFY":    0xFC9E, # (2)   PLAY文が内部で使用する
    "INTVAL":   0xFCA0, # (2)   インターバルの間隔。ON INTERVAL GOSUB文により設定される
    "INTCNT":   0xFCA2, # (2)   インターバルのためのカウンタ
    "LOWLIM":   0xFCA4, # (1)   カセットテープからの読み込み中に使う
    "WINWID":   0xFCA5, # (1)   カセットテープからの読み込み中に使う
    "GRPHED":   0xFCA6, # (1)   グラフィックキャラクタを出す時のフラグ(1=グラフィックキャラクタ、0=通常の文字)
    "ESCCNT":   0xFCA7, # (1)   エスケープコードがきてから何文字目かをカウントするエリア
    "INSFLG":   0xFCA8, # (1)   挿入モードのフラグ(0=通常モード、0以外=挿入モード)
    "CSRSW":    0xFCA9, # (1)   カーソル表示の有無(0=表示なし、0以外=表示あり)
                        #       LOCATE文の<カーソルスイッチ>により設定される
    "CSTYLE":   0xFCAA, # (1)   カーソルの形(0=■、0以外=_)
    "CAPST":    0xFCAB, # (1)   CAPSキーの状態(0=CAP OFF、0以外=CAP ON)
    "KANAST":   0xFCAC, # (1)   かなキーの状態(0=かなOFF、0以外=かなON)
    "KANAMD":   0xFCAD, # (1)   かなキー配列の状態(0=50音配列、0以外=JIS配列)
    "FLBMEM":   0xFCAE, # (1)   BASICプログラムをロード中は0
    "SCRMOD":   0xFCAF, # (1)   現在のスクリーンモードの番号
    "OLDSCR":   0xFCB0, # (1)   スクリーンモード保存エリア
    "CASPRV":   0xFCB1, # (1)   CAS:が使う文字保存場所
    "BRDATR":   0xFCB2, # (1)   PAINTで使用する境界色のカラーコード。PAINT文の<境界色>で指定される
    "GXPOS":    0xFCB3, # (2)   X座標
    "GYPOS":    0xFCB5, # (2)   Y座標
    "GRPACX":   0xFCB7, # (2)   グラフィックアキュムレータ(X座標)
    "GRPACY":   0xFCB9, # (2)   グラフィックアキュムレータ(Y座標)
    "DRWFLG":   0xFCBB, # (1)   DRAW文で使用するフラグ
    "DRWSCL":   0xFCBC, # (1)   DRAWスケーリングファクタ(0=スケーリングしない、0以外=する)
    "DRWANG":   0xFCBD, # (1)   DRAWするときの角度
    "RUNBNF":   0xFCBE, # (1)   BLOAD中、BSAVE中、どちらでもない、のいずれかを表すフラグ
    "SAVENT":   0xFCBF, # (2)   BSAVEの開始番地
    "EXPTBL":   0xFCC1, # (4)   拡張スロット用のフラグテーブル。各スロットの拡張の有無
    "SLTTBL":   0xFCC5, # (4)   各拡張スロットレジスタ用の、現在のスロット選択状況
    "SLTATR":   0xFCC9, # (64)  各スロット用に属性を保存する
    "SLTWRK":   0xFD09, # (128) 各スロット用に特定のワークエリアを確保する
    "PROCNM":   0xFD89, # (16)  拡張ステートメント(CALL文の後)、拡張デバイス(OPENの後)の名前が入る。0は終わり
    "DEVICE":   0xFD99, # (1)   カートリッジ用の装置識別に使用する

    # ● 拡張スロット選択レジスタ
    #"EXSREG":   0xFFFF, # (1)   拡張スロット選択レジスタ
})
msx_symbols_hook = BidirectionalDict({
    # ● フック
    "H_KEYI":   0xFD9A, # from 0x0C4A: MSXIO  割り込み処理の始め                       使用目的: RS-232Cなどの割り込み処理を追加する
    "H_TIMI":   0xFD9F, # from 0x0C53: MSXIO  タイマ割り込み処理                       使用目的: タイマー割り込み処理を追加するため
    "H_CHPH":   0xFDA4, # from 0x08C0: MSXIO  CHPUT(1文字出力)の始め                   使用目的: 他のコンソール出力装置をつなぐため
    "H_DSPC":   0xFDA9, # from 0x09E6: MSXIO  DSPCSR(カーソル表示)の始め               使用目的: 他のコンソール装置をつなぐため
    "H_ERAC":   0xFDAE, # from 0x0A33: MSXIO  ERACSR(カーソル消去)の始め               使用目的: 他のコンソール装置をつなぐため
    "H_DSPF":   0xFDB3, # from 0x0B2B: MSXIO  DSPFNK(ファンクションキー表示)の始め     使用目的: 他のコンソール装置をつなぐため
    "H_ERAF":   0xFDB8, # from 0x0B15: MSXIO  ERAFNK(ファンクションキー消去)の始め     使用目的: 他のコンソール装置をつなぐため
    "H_TOTE":   0xFDBD, # from 0x0842: MSXIO  TOTEXT(画面をテキストモードにする)の始め 使用目的: 他のコンソール装置をつなぐため
    "H_CHGE":   0xFDC2, # from 0x10CE: MSXIO  CHGET(1文字取り出し)の始め               使用目的: 他のコンソール装置をつなぐため
    "H_INIP":   0xFDC7, # from 0x071E: MSXIO  INIPAT(文字パターンの初期化)の始め       使用目的: 他の文字セットを使うため
    "H_KEYC":   0xFDCC, # from 0x1025: MSXIO  KEYCOD(キーコード変換)の始め             使用目的: 他のキー配置を使うため
    "H_KYEA":   0xFDD1, # from 0x0F10: MSXIO  NMIルーチン(Key Easy)の始め              使用目的: 他のキー配置を使うため
    "H_NMI":    0xFDD6, # from 0x1398: MSXIO  NMI(ノンマスカブルインタラプト)の始め    使用目的: NMI処理をするため
    "H_PINL":   0xFDDB, # from 0x23BF: MSXINL PINLIN(1行入力)の始め                    使用目的: 他のコンソール入力装置や他の入力方式を使うため
    "H_QINL":   0xFDE0, # from 0x23CC: MSXINL QINLIN(”?”を表示して1行入力)の始め     使用目的: 他のコンソール入力装置や他の入力方式を使うため
    "H_INLI":   0xFDE5, # from 0x23D5: MSXINL INLIN(1行入力)の始め                     使用目的: 他のコンソール入力装置や他の入力方式を使うため
    "H_ONGO":   0xFDEA, # from 0x7810: MSXSTS INGOTP(ON GOTO)の始め                    使用目的: 他の割り込み処理装置を使うため
    "H_DSKO":   0xFDEF, # from 0x7C16: MSXSTS DSKO$(ディスク出力)の始め                使用目的: ディスク装置を接続するため
    "H_SETS":   0xFDF4, # from 0x7C1B: MSXSTS SETS(セット アトリビュート)の始め        使用目的: ディスク装置を接続するため
    "H_NAME":   0xFDF9, # from 0x7C20: MSXSTS NAME(リネーム)の始め                     使用目的: ディスク装置を接続するため
    "H_KILL":   0xFDFE, # from 0x7C25: MSXSTS KILL(ファイルの削除)の始め               使用目的: ディスク装置を接続するため
    "H_IPL":    0xFE03, # from 0x7C2A: MSXSTS IPL(初期プログラムのロード)の始め        使用目的: ディスク装置を接続するため
    "H_COPY":   0xFE08, # from 0x7C2F: MSXSTS COPY(ファイルのコピー)の始め             使用目的: ディスク装置を接続するため
    "H_CMD":    0xFE0D, # from 0x7C34: MSXSTS CMD(拡張コマンド)の始め                  使用目的: ディスク装置を接続するため
    "H_DSKF":   0xFE12, # from 0x7C39: MSXSTS DSKF(ディスクの空き)の始め               使用目的: ディスク装置を接続するため
    "H_DSKI":   0xFE17, # from 0x7C3E: MSXSTS DSKI(ディスク入力)の始め                 使用目的: ディスク装置を接続するため
    "H_ATTR":   0xFE1C, # from 0x7C43: MSXSTS ATTR$(アトリビュート)の始め              使用目的: ディスク装置を接続するため
    "H_LSET":   0xFE21, # from 0x7C48: MSXSTS LSET(左詰め代入)の始め                   使用目的: ディスク装置を接続するため
    "H_RSET":   0xFE26, # from 0x7C4D: MSXSTS RSET(左詰め代入)の始め                   使用目的: ディスク装置を接続するため
    "H_FIEL":   0xDE2B, # from 0x7C52: MSXSTS FIELD(フィールド)の始め                  使用目的: ディスク装置を接続するため
    "H_MKID":   0xFE30, # from 0x7C57: MSXSTS MKI$(整数作成)の始め                     使用目的: ディスク装置を接続するため
    "H_MKSD":   0xFE35, # from 0x7C5C: MSXSTS MKS$(単精度実数作成)の始め               使用目的: ディスク装置を接続するため
    "H_MKDD":   0xFE3A, # from 0x7C61: MSXSTS MKD$(倍精度実数作成)の始め               使用目的: ディスク装置を接続するため
    "H_CVI":    0xFE3F, # from 0x7C66: MSXSTS CVI(整数変換)の始め                      使用目的: ディスク装置を接続するため
    "H_CVS":    0xFE44, # from 0x7C6B: MSXSTS CVS(単精度実数変換)の始め                使用目的: ディスク装置を接続するため
    "H_CVD":    0xFE49, # from 0x7C70: MSXSTS CVD(倍精度実数変換)の始め                使用目的: ディスク装置を接続するため
    "H_GETP":   0xFE4E, # from 0x6A93: SPDSK  GETPTR(ファイルポインタ取り出し)         使用目的: ディスク装置を接続するため
    "H_SETF":   0xFE53, # from 0x6AB3: SPCDSK SETFIL(ファイルポインタ設定)             使用目的: ディスク装置を接続するため
    "H_NOFO":   0xFE58, # from 0x6AF6: SPDSK  NOFOR(OPEN文にFORがない)                 使用目的: ディスク装置を接続するため
    "H_NULO":   0xFE5D, # from 0x6B0F: SPCDSK NULOPN(空きファイルをオープン)           使用目的: ディスク装置を接続するため
    "H_NTFL":   0xFE62, # from 0x6B3B: SPCDSK NTFLO(ファイル番号が0でない)             使用目的: ディスク装置を接続するため
    "H_MERG":   0xFE67, # from 0x6B63: SPCDSK MERGE(プログラムファイルのマージ)        使用目的: ディスク装置を接続するため
    "H_SAVE":   0xFE6C, # from 0x6BA6: SPCDSK SAVE(セーブ)                             使用目的: ディスク装置を接続するため
    "H_BINS":   0xFE71, # from 0x6BCE: SPCDSK BINSAV(機械語セーブ)                     使用目的: ディスク装置を接続するため
    "H_BINL":   0xFE76, # from 0x6BD4: SPCDSK BINLOD(機械語ロード)                     使用目的: ディスク装置を接続するため
    "H_FILE":   0xFD7B, # from 0x6C2F: SPCDSK FILES(ファイル名の表示)                  使用目的: ディスク装置を接続するため
    "H_DGET":   0xFE80, # from 0x6C3B: SPCDSK DGET(ディスクGET)                        使用目的: ディスク装置を接続するため
    "H_FILO":   0xFE85, # from 0x6C51: SPCDSK FILOU1(ファイル出力)                     使用目的: ディスク装置を接続するため
    "H_INDS":   0xFE8A, # from 0x6C79: SPCDSK INDSKC(ディスクの属性を入力)             使用目的: ディスク装置を接続するため
    "H_RSLF":   0xFE8F, # from 0x6CD8: SPCDSK 前のドライブを再び選択する               使用目的: ディスク装置を接続するため
    "H_SAVD":   0xFE94, # from 0x6D03: SPCDSK 現在選択しているドライブを保存する       使用目的: ディスク装置を接続するため
    "H_LOC":    0xFE99, # from 0x6D0F: SPCDSK LOC関数(場所を示す)                      使用目的: ディスク装置を接続するため
    "H_LOF":    0xFE9E, # from 0x6D20: SPCDSK LOF関数(ファイルの長さ)                  使用目的: ディスク装置を接続するため
    "H_EOF":    0xFEA3, # from 0x6D33: SPCDSK EOF関数(ファイルの終わり)                使用目的: ディスク装置を接続するため
    "H_FPOS":   0xFEA8, # from 0x6D43: SPCDSK FPOS関数(ファイルの場所)                 使用目的: ディスク装置を接続するため
    "H_BAKU":   0xFEAD, # from 0x6E36: SPCDSK BAKUPT(バックアップ)                     使用目的: ディスク装置を接続するため
    "H_PARD":   0xFEB2, # from 0x6F15: SPCDEV PARDEV(装置名の取り出し)                 使用目的: 論理装置名を拡張するため
    "H_NODE":   0xFEB7, # from 0x6F33: SPCDEV NODEVN(装置名なし)                       使用目的: 省略装置名を他の装置に設定する
    "H_POSD":   0xFEBC, # from 0x6F37: SPCDEV POSDSK                                   使用目的: ディスク装置を接続するため
    "H_DEVN":   0xFEC1, # from 未使用: SPCDEV DEVNAM(装置名の処理)                     使用目的: 論理装置名を拡張するため
    "H_GEND":   0xFEC6, # from 0x6F8F: SPCDEV GENDSP(装置割り当て)                     使用目的: 論理装置名を拡張するため
    "H_RUNC":   0xFECB, # from 0x629A: BIMISC RUNC(RUNのためのクリア)
    "H_CLEA":   0xFED0, # from 0x62A1: BIMISC CLEARC(CLEAR文のためのクリア)
    "H_LOPD":   0xFED5, # from 0x62AF: BIMISC LOPDFT(繰り返しと省略値の設定)           使用目的: 変数に他の省略値を使うため
    "H_STKE":   0xFEDA, # from 0x62F0: BIMISC STKERR(スタックエラー)
    "H_ISFL":   0xFEDF, # from 0x145F: BIMISC ISFLIO(ファイルの入出力かどうか)
    "H_OUTD":   0xFEE4, # from 0x1B46: BIO    OUTDO(OUTを実行)
    "H_CRDO":   0xFEE9, # from 0x7328: BIO    CRDO(CRLFを実行)
    "H_DSKC":   0xFEEE, # from 0x7374: BIO    DSKCHI(ディスクの属性を入力)
    "H_DOGR":   0xFEF3, # from 0x593C: GENGRP DOGRPH(グラフィック処理を実行)
    "H_PRGE":   0xFEF8, # from 0x4039: BINTRP PRGEND(プログラム終了)
    "H_ERRP":   0xFEFD, # from 0x40DC: BINTRP ERRPRT(エラー表示)
    "H_ERRF":   0xFF02, # from 0x40FD: BINTRP Error handler
    "H_READ":   0xFF07, # from 0x4128: BINTRP Mainloop READY "Ok"
    "H_MAIN":   0xFF0C, # from 0x4134: BINTRP Mainloop
    "H_DIRD":   0xFF11, # from 0x41A8: BINTRP Mainloop DIRDO(ダイレクトステートメント実行)
    "H_FINI":   0xFF16, # from 0x4237: BINTRP Mainloop FINISHED
    "H_FINE":   0xFF1B, # from 0x4247: BINTRP Mainloop finished
    "H_CRUN":   0xFF20, # from 0x42B9: BINTRP Tokenize
    "H_CRUS":   0xFF25, # from 0x4353: BINTRP Tokenize
    "H_ISRE":   0xFF2A, # from 0x437C: BINTRP Tokenize
    "H_NTFN":   0xFF2F, # from 0x43A4: BINTRP Tokenize
    "H_NOTR":   0xFF34, # from 0x44EB: BINTRP Tokenize
    "H_SNGF":   0xFF39, # from 0x45D1: BINTRP "FOR"
    "H_NEWS":   0xFF3E, # from 0x4601: BINTRP Runloop new statement
    "H_GONE":   0xFF43, # from 0x4646: BINTRP Runloop execute
    "H_CHRG":   0xFF48, # from 0x4666: BINTRP CHRGTR standard routine
    "H_RETU":   0xFF4D, # from 0x4821: BINTRP "RETURN"
    "H_PRTF":   0xFF52, # from 0x4A5E: BINTRP "PRINT"
    "H_COMP":   0xFF57, # from 0x4A54: BINTRP "PRINT"
    "H_FINP":   0xFF5C, # from 0x4AFF: BINTRP "PRINT"
    "H_TRMN":   0xFF61, # from 0x4B4D: BINTRP "READ/INPUT" error
    "H_FRME":   0xFF66, # from 0x4C6D: BINTRP Expression Evaluator
    "H_NTPL":   0xFF6B, # from 0x4CA6: BINTRP Expression Evaluator
    "H_EVAL":   0xFF70, # from 0x4DD9: BINTRP Factor Evaluator
    "H_OKNO":   0xFF75, # from 0x4F2C: BINTRP Factor Evaluator
    "H_FING":   0xFF7A, # from 0x4F3E: BINTRP Factor Evaluator
    "H_ISMI":   0xFF7F, # from 0x51C3: BINTRP ISMID$(MID$かどうか)
    "H_WIDT":   0xFF84, # from 0x51CC: BINTRP "WIDTHS(WIDTH)"
    "H_LIST":   0xFF89, # from 0x522E: BINTRP "LIST"
    "H_BUFL":   0xFF8E, # from 0x532D: BINTRP BUFLIN(バッファライン)
    "H_FRQI":   0xFF93, # from 0x543F: BINTRP FRQINT(整数へ変換)
    "H_SCNE":   0xFF98, # from 0x5514: BINTRP Line number to pointer
    "H_FRET":   0xFF9D, # from 0x67EE: BISTRS FRETMP(Free descriptor)
    "H_PTRG":   0xFFA2, # from 0x5EA9: BIPTRG PTRGET(ポインタ取り出し)                 使用目的: 省略値以外の変数を使用するため
    "H_PHYD":   0xFFA7, # from 0x148A: MSXIO  PHYDIO(物理ディスク入出力)               使用目的: ディスク装置を接続するため
                        #                     0xC9ならディスクは接続されていない
    "H_FORM":   0xFFAC, # from 0x148E: MSXIO  FORMAT(ディスクをフォーマットする)       使用目的: ディスク装置を接続するため
    "H_ERRO":   0xFFB1, # from 0x406F: BINTRP ERROR                                    使用目的: アプリケーション・プログラムのエラー処理
    "H_LPTO":   0xFFB6, # from 0x085D: MSXIO  LPTOUT(プリンタ出力)                     使用目的: 省略値以外のプリンタを使うため
    "H_LPTS":   0xFFBB, # from 0x0884: MSXIO  LPTSTT(プリンタの状態)                   使用目的: 省略値以外のプリンタを使うため
    "H_SCRE":   0xFFC0, # from 0x79CC: MSXSTS SCREEN文の入口                           使用目的: SCREEN文を拡張するため
    "H_PLAY":   0xFFC5, # from 0x73E5: MSXSTS PLAY文の入口                             使用目的: PLAY文を拡張するため

    # ● 拡張BIOS用フック
    "EXTBIO":   0xFFCA, # (5) Used by BIOS extensions.
    "FCALL":    0xFFCA, # (5) Old name of EXTBIO

    # ● 拡張DEVICE用フック
    "DISINT":   0xFFCF, # DEFS 5     # Used by DOS. 長期間の割り込み禁止開始
    "ENAINT":   0xFFD4, # DEFS 5     # Used by DOS. 長期間の割り込み禁止解除

    # ● フック 別名定義
    "HKEYI":    0xFD9A, # (5) 0x0C4A Interrupt handler
    "HTIMI":    0xFD9F, # (5) 0x0C53 Interrupt handler
    "HCHPU":    0xFDA4, # (5) 0x08C0 CHPUT standard routine
    "HDSPC":    0xFDA9, # (5) 0x09E6 Display cursor
    "HERAC":    0xFDAE, # (5) 0x0A33 Erase cursor
    "HDSPF":    0xFDB3, # (5) 0x0B2B DSPFNK standard routine
    "HERAF":    0xFDB8, # (5) 0x0B15 ERAFNK standard routine
    "HTOTE":    0xFDBD, # (5) 0x0842 TOTEXT standard routine
    "HCHGE":    0xFDC2, # (5) 0x10CE CHGET standard routine
    "HINIP":    0xFDC7, # (5) 0x071E Copy character set to VDP
    "HKEYC":    0xFDCC, # (5) 0x1025 Keyboard decoder
    "HKYEA":    0xFDD1, # (5) 0x0F10 Keyboard decoder
    "HNMI":     0xFDD6, # (5) 0x1398 NMI standard routine
    "HPINL":    0xFDDB, # (5) 0x23BF PINLIN standard routine
    "HQINL":    0xFDE0, # (5) 0x23CC QINLIN standard routine
    "HINLI":    0xFDE5, # (5) 0x23D5 INLIN standard routine
    "HONGO":    0xFDEA, # (5) 0x7810 "ON DEVICE GOSUB"
    "HDSKO":    0xFDEF, # (5) 0x7C16 "DSKO$"
    "HSETS":    0xFDF4, # (5) 0x7C1B "SET"
    "HNAME":    0xFDF9, # (5) 0x7C20 "NAME"
    "HKILL":    0xFDFE, # (5) 0x7C25 "KILL"
    "HIPL":     0xFE03, # (5) 0x7C2A "IPL"
    "HCOPY":    0xFE08, # (5) 0x7C2F "COPY"
    "HCMD":     0xFE0D, # (5) 0x7C34 "CMD"
    "HDSKF":    0xFE12, # (5) 0x7C39 "DSKF"
    "HDSKI":    0xFE17, # (5) 0x7C3E "DSKI$"
    "HATTR":    0xFE1C, # (5) 0x7C43 "ATTR$"
    "HLSET":    0xFE21, # (5) 0x7C48 "LSET"
    "HRSET":    0xFE26, # (5) 0x7C4D "RSET"
    "HFIEL":    0xFE2B, # (5) 0x7C52 "FIELD"
    "HMKI":     0xFE30, # (5) 0x7C57 "MKI$"
    "HMKS":     0xFE35, # (5) 0x7C5C "MKS$"
    "HMKD":     0xFE3A, # (5) 0x7C61 "MKD$"
    "HCVI":     0xFE3F, # (5) 0x7C66 "CVI"
    "HCVS":     0xFE44, # (5) 0x7C6B "CVS"
    "HCVD":     0xFE49, # (5) 0x7C70 "CVD"
    "HGETP":    0xFE4E, # (5) 0x6A93 Locate FCB
    "HSETF":    0xFE53, # (5) 0x6AB3 Locate FCB
    "HNOFO":    0xFE58, # (5) 0x6AF6 "OPEN"
    "HNULO":    0xFE5D, # (5) 0x6B0F "OPEN"
    "HNTFL":    0xFE62, # (5) 0x6B3B Close I/O buffer 0
    "HMERG":    0xFE67, # (5) 0x6B63 "MERGE/LOAD"
    "HSAVE":    0xFE6C, # (5) 0x6BA6 "SAVE"
    "HBINS":    0xFE71, # (5) 0x6BCE "SAVE"
    "HBINL":    0xFE76, # (5) 0x6BD4 "MERGE/LOAD"
    "HFILE":    0xFE7B, # (5) 0x6C2F "FILES"
    "HDGET":    0xFE80, # (5) 0x6C3B "GET/PUT"
    "HFILO":    0xFE85, # (5) 0x6C51 Sequential output
    "HINDS":    0xFE8A, # (5) 0x6C79 Sequential input
    "HRSLF":    0xFE8F, # (5) 0x6CD8 "INPUT$
    "HSAVD":    0xFE94, # (5) 0x6D03 "LOC", 0x6D14 "LOF",
    "HLOC":     0xFE99, # (5) 0x6D0F "LOC"
    "HLOF":     0xFE9E, # (5) 0x6D20 "LOF"
    "HEOF":     0xFEA3, # (5) 0x6D33 "EOF"
    "HFPOS":    0xFEA8, # (5) 0x6D43 "FPOS"
    "HBAKU":    0xFEAD, # (5) 0x6E36 "LINE INPUT# 
    "HPARD":    0xFEB2, # (5) 0x6F15 Parse device name
    "HNODE":    0xFEB7, # (5) 0x6F33 Parse device name
    "HPOSD":    0xFEBC, # (5) 0x6F37 Parse device name
    "HDEVN":    0xFEC1, # (5) This hook is not used.
    "HGEND":    0xFEC6, # (5) 0x6F8F I/O function dispatcher
    "HRUNC":    0xFECB, # (5) 0x629A Run-clear
    "HCLEA":    0xFED0, # (5) 0x62A1 Run-clear
    "HLOPD":    0xFED5, # (5) 0x62AF Run-clear
    "HSTKE":    0xFEDA, # (5) 0x62F0 Reset stack
    "HISFL":    0xFEDF, # (5) 0x145F ISFLIO standard routine
    "HOUTD":    0xFEE4, # (5) 0x1B46 OUTDO standard routine
    "HCRDO":    0xFEE9, # (5) 0x7328 CR,LF to OUTDO
    "HDSKC":    0xFEEE, # (5) 0x7374 Mainloop line input
    "HDOGR":    0xFEF3, # (5) 0x593C Line draw
    "HPRGE":    0xFEF8, # (5) 0x4039 Program end
    "HERRP":    0xFEFD, # (5) 0x40DC Error handler
    "HERRF":    0xFF02, # (5) 0x40FD Error handler
    "HREAD":    0xFF07, # (5) 0x4128 Mainloop "OK"
    "HMAIN":    0xFF0C, # (5) 0x4134 Mainloop
    "HDIRD":    0xFF11, # (5) 0x41A8 Mainloop direct statement
    "HFINI":    0xFF16, # (5) 0x4237 Mainloop finished
    "HFINE":    0xFF1B, # (5) 0x4247 Mainloop finished
    "HCRUN":    0xFF20, # (5) 0x42B9 Tokenize
    "HCRUS":    0xFF25, # (5) 0x4353 Tokenize
    "HISRE":    0xFF2A, # (5) 0x437C Tokenize
    "HNTFN":    0xFF2F, # (5) 0x43A4 Tokenize
    "HNOTR":    0xFF34, # (5) 0x44EB Tokenize
    "HSNGF":    0xFF39, # (5) 0x45D1 "FOR"
    "HNEWS":    0xFF3E, # (5) 0x4601 Runloop new statement
    "HGONE":    0xFF43, # (5) 0x4646 Runloop execute
    "HCHRG":    0xFF48, # (5) 0x4666 CHRGTR standard routine
    "HRETU":    0xFF4D, # (5) 0x4821 "RETURN"
    "HPRTF":    0xFF52, # (5) 0x4A5E "PRINT"
    "HCOMP":    0xFF57, # (5) 0x4A54 "PRINT"
    "HFINP":    0xFF5C, # (5) 0x4AFF "PRINT"
    "HTRMN":    0xFF61, # (5) 0x4B4D "READ/INPUT" error
    "HFRME":    0xFF66, # (5) 0x4C6D Expression Evaluator
    "HNTPL":    0xFF6B, # (5) 0x4CA6 Expression Evaluator
    "HEVAL":    0xFF70, # (5) 0x4DD9 Factor Evaluator
    "HOKNO":    0xFF75, # (5) 0x4F2C Factor Evaluator
    "HFING":    0xFF7A, # (5) 0x4F3E Factor Evaluator
    "HISMI":    0xFF7F, # (5) 0x51C3 Runloop execute
    "HWIDT":    0xFF84, # (5) 0x51CC "WIDTH"
    "HLIST":    0xFF89, # (5) 0x522E "LIST"
    "HBUFL":    0xFF8E, # (5) 0x532D Detokenize
    "HFRQI":    0xFF93, # (5) 0x543F Convert to integer
    "HSCNE":    0xFF98, # (5) 0x5514 Line number to pointer
    "HFRET":    0xFF9D, # (5) 0x67EE Free descriptor
    "HPTRG":    0xFFA2, # (5) 0x5EA9 Variable search
    "HPHYD":    0xFFA7, # (5) 0x148A PHYDIO standard routine
    "HFORM":    0xFFAC, # (5) 0x148E FORMAT standard routine
    "HERRO":    0xFFB1, # (5) 0x406F Error handler
    "HLPTO":    0xFFB6, # (5) 0x085D LPTOUT standard routine
    "HLPTS":    0xFFBB, # (5) 0x0884 LPTSTT standard routine
    "HSCRE":    0xFFC0, # (5) 0x79CC "SCREEN"
    "HPLAY":    0xFFC5, # (5) 0x73E5 "PLAY" statement
})

# ラベルを探す
def search_labels_dos(address : int) -> list[str]:
    #if len(labels := msx_symbols_bios.from_address(address)) > 0: return labels
    if len(labels := msx_symbols_work.from_address(address)) > 0: return labels
    if len(labels := msx_symbols_hook.from_address(address)) > 0: return labels
    return []

def search_labels(address : int) -> list[str]:
    if len(labels := msx_symbols_bios.from_address(address)) > 0: return labels
    if len(labels := msx_symbols_work.from_address(address)) > 0: return labels
    if len(labels := msx_symbols_hook.from_address(address)) > 0: return labels
    return []

def from_label (label : str) -> int:
    if (address := msx_symbols_bios.get_address(label)) is not None: return address
    if (address := msx_symbols_work.get_address(label)) is not None: return address
    if (address := msx_symbols_hook.get_address(label)) is not None: return address
    return []

# Test
if __name__ == "__main__":
    def test_name(dic_name : str, dic : BidirectionalDict, name : str) -> bool:
        address: int | None = dic.get_address(name)
        if address is not None:
            print(f"{dic_name} {name} = 0x{address:04X}")
            return True
        return False

    def test_address(dic_name : str, dic : BidirectionalDict, address : int) -> bool:
        name: list[str] | None = dic.from_address(address)
        if len(name) > 0:
            print(f"{dic_name} 0x{address:04X} = {name}")
            return True
        return False

    for name in ("CALSLT","CGPBAS","H_TIMI"):
        if   test_name( "msx_symbols_bios", msx_symbols_bios, name): pass
        elif test_name( "msx_symbols_work", msx_symbols_work, name): pass
        elif test_name( "msx_symbols_hook", msx_symbols_hook, name): pass
        else:print(f"{name} not found")

    for address in (0x0024, 0xFB41, 0xFD9F):
        if   test_address( "msx_symbols_bios", msx_symbols_bios, address): pass
        elif test_address( "msx_symbols_work", msx_symbols_work, address): pass
        elif test_address( "msx_symbols_hook", msx_symbols_hook, address): pass
        else:print(f"0x{address:04X} not found")
    
    for address in (0xF3F6,0xF3F8,0xF3FA,0xFAF0):
        if len(label := search_labels_dos(address)):
            print(f"0x{address:04X} = {label}")
        else:print(f"0x{address:04X} not found")

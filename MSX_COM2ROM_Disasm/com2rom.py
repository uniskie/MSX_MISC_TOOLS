# =====================================================================
# COMバイナリ to ROM(32KB page1-2) リロケータ逆アセンブラ
# =====================================================================
# 自己書き換え対策のためのモードが2種類：
# 1. RAM転送モード
#    要RAM16KB：CODE+WORKを0xC000に転送して実行
#    CODEをRAMに置くことで自己書き換えに対応
# 2. パッチモード
#    要RAM8KB：WORKのみ0xE000に配置して実行
#    JR命令の書き換えのみパッチで対応
# 汎用性はない
# =====================================================================
import os
import copy
import argparse
import re
import msx_symbols  # msx_symbols.py から search_labels_dos および search_labels を使用

# =====================================================================
#  グローバルシステム設定（定数パラメータ定義）
# =====================================================================
INPUT_PATH          = "indev.com"
OUTPUT_ASM_PATH     = "indev_rom.asm"
OUTPUT_LOG_PATH     = "indev_rom.log"

RAM_START_NORMAL    = 0xE000     # 通常モードでのRAM開始アドレス
RAM_START_RAMCOPY   = 0xC000     # RAMコピーモードでのRAM開始アドレス

SYSYTEM_WORK        = 0xF380     # システムワークエリア先頭

TARGET_ROM_BASE     = 0x4000             # Page 1 ROM 基準アドレス (Page 1)
TARGET_RAM_BASE     = RAM_START_NORMAL   # Page 3 RAM 基準アドレス (使用可能な裏RAMスペース)

ORIGINAL_LOAD_ADDR  = 0x0100     # MSX-DOS COMファイルのデフォルト実行開始アドレス

# 自己書き換え対策：連続するJP命令の自動検出とパッチフラグ
SCAN_SEQUENTIAL_JP  = True       # 連続ジャンプテーブルの検出をするかどうか
USE_SMC_PATCH       = True       # (通常モード時に)特定の自己書き換えコードにパッチを当てるかどうか

# 自己書き換え対策：CODE/WORK領域をPage 3 RAM上に転送して実行するモードの切替フラグ
COPY_CODE_TO_RAM    = False      # True = 有効 (CODEをRAMへコピーして実行), False = 無効 (CODEをROM上で直接実行)
RAM_MAX_LIMIT       = 0xEFFF     # Page 3 RAMの上限アドレス（システム領域との衝突防止）

# WORKに続く無参照ブロックのマージ最大範囲（デフォルト上限: 3バイト）
# 0にすれば無効になる
MAX_STATIC_MERGE_LIMIT = 3

# パス1を軽い簡易探索にするかどうか
# 簡易的な構造探索：アドレスのみをキーにして重複探索を判定
# 深めの実行経路探索：アドレスだけでなくレジスタ状態もキーにする
PASS1_USE_SIMPLE_PASS = True

# （通常モードのみ）CODEに挟まれた無参照ブロックをCODEに統合するフラグ
USE_CODE_MERGE = False

# アセンブラ種類に応じたシンタックス指定 (1: sjasmplus, 2: AILZ80ASM)
ASSEMBLER_TYPE      = 2          # 1 = .phase / .dephase 形式 (sjasmplus)
                                 # 2 = ORG $C000, $ / ORG $ 形式 (AILZ80ASM)

# スタックポインタの初期アドレス値
STACK_INIT_VAL      = SYSYTEM_WORK

# =====================================================================
# MSX-DOS BDOSコールアドレス
BDOS_CALL_ADDRESS = 0x0005

# =====================================================================
# スタートアップコード
# =====================================================================
ROM_HEADER_SIZE = 0x10
ROM_HEADER = '''
;--- MSX ROM HEADER ---
    db 41H, 42H             ; 'AB' (ROM識別子)
    dw STARTUP_ENTRY        ; INIT (初期化)
    dw 0000H                ; STATEMENT (CALL文拡張)
    dw 0000H                ; DEVICE (入出力装置拡張)
    dw 0000H                ; TEXT (BASICプログラム)
    ds 6, 00H               ; (システム予約)
'''
ENTRY_CODE_SIZE = 67
ENTRY_CODE = '''
;===================================================================
; SET UP 
;===================================================================
STARTUP_ENTRY:
    ld sp, STACK_INIT_ADDR  ; スタックポインタを初期化する
    di
    call RSLREG             ; RSLREG (スロットレジスタを読み込む)
    rrca
    rrca                    ; Page 1(ビット2-3)をビット0-1の位置へシフト
    and 03H                 ; 基本スロットIDにマスク
    ld c, a
    ld b, 0
    ld hl, EXPTBL           ; EXPTBL (スロット拡張フラグテーブル開始)
    add hl, bc
    ld a, (hl)              ; 拡張の有無を取得
    and 80H                 ; 拡張スロット判定ビットのみ抽出
    or c
    ld c, a                 ; C = Page 1 の Slot ID を保持
    ld h, 80H               ; 対象は Page 2 (8000H)
    call ENASLT             ; ENASLT (Page 2を同一スロットに切替)

    ;--- UNIFIED RAM INITIALIZATION VIA TRANSFER TABLE ---
    ld ix, RAM_TRANSFER_TABLE
STARTUP_TRX_LOOP:
    ld l, (ix+0)
    ld h, (ix+1)            ; HL = 転送元(ROM)
    ld e, (ix+2)
    ld d, (ix+3)            ; DE = 転送先(RAM)
    ld c, (ix+4)
    ld b, (ix+5)            ; BC = 転送サイズ
    ld a, b
    or c
    jr z, STARTUP_TRX_DONE    ; サイズ0なら終了
    ldir
    ld de, 6
    add ix, de
    jr STARTUP_TRX_LOOP
STARTUP_TRX_DONE:
    ei
    jp EXEC_ADDRESS         ; 実行
STARTUP_END:

'''

# =====================================================================
# 自己書き換え(SMC)パッチ 1
#    ld (target_label+1), a
#    jr dest_label
# =====================================================================
#    ld (target_label+1), a
smc_patch_jr_code_ld_size = 0
smc_patch_jr_code_ld = (
    "; [SMC PATCH] ld (target_label),a --> 削除"
)

#    jr dest_label
smc_patch_jr_code_jr_size = 9
smc_patch_jr_code_jr = (
 '''add a, low dest_label  ; [SMC PATCH] 'jr dest_label --> jp (dest_label + a)'
    ld l, a
    ld a, high dest_label
    adc a, 00H
    ld h, a
    jp (hl)'''
)

# =====================================================================
#  BDOSファンクション代替サブルーチン
# =====================================================================
BDOS_REPLACE_ROUTINES = {
    0x00: { # システムリセット
        "label": "BDOS_SUB_00_TERM",
        "size": 4,
        "code": """
BDOS_SUB_00_TERM:
    di
    jp 0000H
"""
    },
    0x01: { # コンソールから 1 文字入力 (入力待ちあり、エコーバックあり、コントロールコードチェックあり)
        "label": "BDOS_SUB_01_CONIN",
        "size": 13,
        "code": """
BDOS_SUB_01_CONIN:
    call CHGET                  ; キーボードから1文字入力 (A=入力文字)
    cp 03H                      ; Ctrl+C (中断コード) かチェック
    ret z
    push af                     ; 入力文字を一時退避
    ld e, a
    call CHPUT                  ; 画面へエコーバック表示
    pop af                      ; 入力文字をAレジスタに復帰
    ret
"""
    },
    0x02: { # コンソールへ 1 文字出力
        "label": "BDOS_SUB_02_CONOUT",
        "size": 21,
        "code": """
BDOS_SUB_02_CONOUT:
    ld a, e
    cp 09H                      ; タブ文字 (09H) か確認
    jr nz, .PLAIN_OUT_02
    ld a, 20H
    call CHPUT                  ; タブをスペース3文字に展開して出力
    call CHPUT
    call CHPUT
    ret
.PLAIN_OUT_02:
    call CHPUT                  ; 通常文字を出力
    ret
"""
    },
    0x03: { # 補助入力装置から 1 文字入力
        "label": "BDOS_SUB_03_AUXIN",
        "size" : 3,
        "code": """
BDOS_SUB_03_AUXIN:
    ld a, 1AH                   ; EOF (1AH) をAレジスタに代入
    ret
"""
    },
    0x04: { # 補助出力装置へ 1 文字出力
        "label": "BDOS_SUB_04_AUXOUT",
        "size" : 2,
        "code": """
BDOS_SUB_04_AUXOUT:
    nop
    ret
"""
    },
    0x05: { # プリンタへ 1 文字出力
        "label": "BDOS_SUB_05_LSTOUT",
        "size" : 5,
        "code": """
BDOS_SUB_05_LSTOUT:
    ld a, e
    call LPTOUT                 ; プリンタへ出力
    ret
"""
    },
    0x06: { # コンソールから 1 文字入力 (入力待ちなし、エコーバックなし、コントロールコードチェックなし) / 1 文字出力
        "label": "BDOS_SUB_06_DIRIO",
        "size" : 21,
        "code": """
BDOS_SUB_06_DIRIO:
    ld a, e
    cp 0FFH                     ; 入力要求 (E=0FFH) か確認
    jr nz, .PLAIN_OUT_06
    call CHSNS                 ; キーボードに入力があるかチェック
    jr z, .NO_KEY_06            ; 入力がなければ終了へ
    call CHGET                  ; 1文字入力 (A=入力文字)
    or a                        ; Zフラグをクリア (Z=0: 入力ありを示す)
    ret
.NO_KEY_06:
    xor a                       ; Zフラグをセット (Z=1: 入力なしを示す)、A=00H
    ret
.PLAIN_OUT_06:
    call CHPUT                  ; レジスタEに入っている文字を出力
    ret
"""
    },
    0x07: { # コンソールから 1 文字入力 (入力待ちあり、エコーバックなし、コントロールコードチェックなし)
        "label": "BDOS_SUB_07_DIRIN",
        "size" : 4,
        "code": """
BDOS_SUB_07_DIRIN:
    call CHGET                  ; エコーバックなしでキーボードから1文字入力 (A=入力文字)
    ret
"""
    },
    0x08: { # コンソールから 1 文字入力 (入力待ちあり、エコーバックなし、コントロールコードチェックあり)
        "label": "BDOS_SUB_08_INP_NO_ECHO",
        "size" : 7,
        "code": """
BDOS_SUB_08_INP_NO_ECHO:
    call CHGET                  ; エコーバックなしで1文字入力 (A=入力文字)
    cp 03H                      ; Ctrl+C (中断コード) か確認
    ret z
    ret
"""
    },
    0x09: { # コンソール文字列出力
        "label": "BDOS_SUB_09_STROUT",
        "size" : 15,
        "code": """
BDOS_SUB_09_STROUT:
    ld h, d
    ld l, e                     ; HL = 文字列の先頭アドレス
.STR_LOOP_09:
    ld a, (hl)
    cp 24H                      ; '$' (24H) 終端記号かチェック
    ret z                       ; 終端なら終了
    push hl
    ld e, a
    call CHPUT                  ; 1文字表示
    pop hl
    inc hl                      ; 次の文字のアドレスへ
    jr .STR_LOOP_09
"""
    },
    0x0A: { # コンソール1行入力
        "label": "BDOS_SUB_0A_BUFIN",
        "size" : 97,
        "code": """
BDOS_SUB_0A_BUFIN:
    ld h, d
    ld l, e
    ld a, (hl)                  ; バッファに許容された最大文字数を取得
    ld b, a                     ; B = 最大文字数
    inc hl
    push hl                     ; 実際の入力文字数を書き戻すためのアドレス(DE+1)を退避
    inc hl                      ; HL = 文字格納先のアドレス(DE+2)
    ld c, 0                     ; C = 入力文字数カウンタ
.KB_IN_LOOP_0A:
    push bc
    push hl
    call CHGET                  ; 1文字入力 (A=入力文字)
    pop hl
    pop bc
    cp 0DH                      ; Enterキー (0DH) か確認
    jr z, .KB_END_0A
    cp 08H                      ; Backspaceキー (08H) か確認
    jr z, .KB_BACKSPACE_0A
    
    ld d, a                     ; D = 入力文字を退避
    ld a, c
    cp b                        ; カウンタが上限に達しているかチェック
    jr z, .KB_LIMIT_0A
    
    ld a, d                     ; A = 入力文字を復帰
    ld (hl), a                  ; メモリに入力された文字を格納
    inc hl                      ; 次のメモリアドレスへ進める
    inc c                       ; カウンタをインクリメント
    push bc
    push hl
    ld e, a
    call CHPUT                  ; 入力された文字を画面にエコーバック表示
    pop hl
    pop bc
    jr .KB_IN_LOOP_0A
.KB_LIMIT_0A:
    ld a, d                     ; A = 入力文字を復帰
    push bc
    push hl
    call BEEP                   ; 制限到達のビープ音を鳴らす
    pop hl
    pop bc
    jr .KB_IN_LOOP_0A
.KB_BACKSPACE_0A:
    ld a, c
    or a                        ; 入力文字数がすでに0か確認
    jr z, .KB_IN_LOOP_0A        ; 0ならバックスペースを無視してループへ
    dec hl                      ; 1つ前のアドレスに戻す
    dec c                       ; 文字数カウンタを1つ減らす
    push bc
    push hl
    ld e, 08H
    call CHPUT                  ; 画面上でカーソルを1つ戻す
    ld e, 20H
    call CHPUT                  ; 空白を出力して直前の1文字を消去
    ld e, 08H
    call CHPUT                  ; 再びカーソルを1つ戻す
    pop hl
    pop bc
    jr .KB_IN_LOOP_0A
.KB_END_0A:
    push bc
    push hl
    ld e, 0DH
    call CHPUT                  ; CR (復帰) を出力
    ld e, 0AH
    call CHPUT                  ; LF (改行) を出力
    pop hl
    pop bc
    pop hl                      ; 退避していた入力文字数格納アドレスを復帰
    ld (hl), c                  ; 確定した入力文字数を格納先に書き戻す
    ret
"""
    },
    0x0B: { # コンソール入力チェック
        "label": "BDOS_SUB_0B_STATUS",
        "size" : 9,
        "code": """
BDOS_SUB_0B_STATUS:
    call CHSNS                 ; キー入力があるか確認
    ld a, 00H
    ret z                       ; 入力なしなら A=00H
    ld a, 0FFH                  ; 入力ありなら A=0FFH
    ret
"""
    },
    0x0C: { # 	バージョン番号の取得
        "label": "BDOS_SUB_0C_VERSION",
        "size" : 4,
        "code": """
BDOS_SUB_0C_VERSION:
    ld hl, 0022H                ; バージョン番号 (HL=0022H) を返却
    ret
"""
    },
    "UNSUPPORTED": { # 0DH以降のディスク操作系ファンクション
        "label": "BDOS_SUB_UNSUPPORTED",
        "size" : 4,
        "code": """
BDOS_SUB_UNSUPPORTED:
    di
    jp ROMBDOS
"""
    }
}

# =====================================================================

def center_text(text, cols):
    return text.center(cols + len(text) - len(text.encode('cp932')))

def format_asm_hex(val, width=4):
    """16進数をINTELアセンブラの文法に従ってフォーマットする。(0FFFFH)"""
    hex_str = f"{val:0{width}X}"
    if hex_str[0] in "ABCDEF":
        return "0" + hex_str + "H"
    return hex_str + "H"

def format_hex(val, width=4):
    """16進数をH表記する。(FFFFH)"""
    hex_str = f"{val:0{width}X}"
    return hex_str + "H"

def get_standard_len(opcode):
    """Z80の非プレフィックス（標準）命令について、その命令長（1〜3バイト）を返す。

    後続のオペランドバイト数を識別して命令サイズを算出する。
    """
    # 3バイト命令:
    # - 0x01, 0x11, 0x21, 0x31: LD rp, nn (rp: BC, DE, HL, SP) 16ビットレジスタペア即値ロード
    # - 0x32, 0x22, 0x3A, 0x2A: LD (nn), A / LD (nn), HL / LD A, (nn) / LD HL, (nn) アドレスによるロード・ストア
    # - 0xC3: JP nn (ジャンプ)
    # - 0xCD: CALL nn (コール)
    if opcode in [0x01, 0x11, 0x21, 0x31] or opcode in [0x32, 0x22, 0x3A, 0x2A] or opcode in [0xC3, 0xCD]:
        return 3

    # 3バイト命令: 条件付きジャンプ命令 (JP cc, nn)
    # cc = NZ (0xC2), Z (0xCA), NC (0xD2), C (0xDA), PO (0xE2), PE (0xEA), P (0xF2), M (0xFA)
    if opcode in [0xC2, 0xCA, 0xD2, 0xDA, 0xE2, 0xEA, 0xF2, 0xFA]:
        return 3

    # 3バイト命令: 条件付きコール命令 (CALL cc, nn)
    # cc = NZ (0xC4), Z (0xCC), NC (0xD4), C (0xDC), PO (0xE4), PE (0xEC), P (0xF4), M (0xFC)
    if opcode in [0xC4, 0xCC, 0xD4, 0xDC, 0xE4, 0xEC, 0xF4, 0xFC]:
        return 3

    # 2バイト命令: 
    # - 0x18: JR e (相対ジャンプ)
    # - 0x20, 0x28, 0x30, 0x38: JR cc, e (条件付き相対ジャンプ cc: NZ, Z, NC, C)
    # - 0x10: DJNZ e (Bレジスタデクリメントによる条件付き相対ジャンプ)
    if opcode in [0x18, 0x20, 0x28, 0x30, 0x38] or opcode == 0x10:
        return 2

    # 2バイト命令: 8ビット即値(n)オペランドを伴う演算・ロード、I/Oポート指定
    # - 0x06〜0x3E (ステップ8): LD r, n (r: B, C, D, E, H, L, (HL), A)
    # - 0xC6〜0xFE (ステップ8): ADD/ADC/SUB/SBC/AND/XOR/OR/CP A, n
    # - 0xD3: OUT (n), A / 0xDB: IN A, (n)
    len_map_2byte = [
        0x06, 0x0E, 0x16, 0x1E, 0x26, 0x2E, 0x3E, 0xC6, 
        0xCE, 0xD6, 0xDE, 0xE6, 0xEE, 0xF6, 0xFE, 0xD3, 0xDB, 0x36
    ]
    if opcode in len_map_2byte:
        return 2

    # その他：1バイト命令群 (レジスタ間演算、1バイトロード、PULL/PUSH、リターン等)
    return 1


class Z80Logger:
    """コンソールへのログ表示およびログファイルへの保存を管理するクラス"""
    def __init__(self, log_filepath):
        self.log_filepath = log_filepath
        try:
            with open(self.log_filepath, 'w', encoding='utf-8') as f:
                pass
        except IOError:
            print("[-] エラー: ログファイルの初期化に失敗しました。")

    def log(self, message):
        print(message)
        try:
            with open(self.log_filepath, 'a', encoding='utf-8') as f:
                f.write(message + "\n")
        except IOError:
            print("[-] エラー: ログファイルへの書き込みに失敗しました。")


class Z80Config:
    """アドレス設定やファイルパスなどの動作環境パラメータを管理するクラス"""
    def __init__(self):
        self.input_file = INPUT_PATH
        self.output_asm = OUTPUT_ASM_PATH
        self.output_log = OUTPUT_LOG_PATH
        
        self.rom_start = TARGET_ROM_BASE
        self.ram_start = TARGET_RAM_BASE
        
        self.old_start = ORIGINAL_LOAD_ADDR
        self.old_end = ORIGINAL_LOAD_ADDR


class Z80MemoryImage:
    """仮想Z80メモリ空間におけるバイナリデータと、アドレスごとの属性情報を保持・管理するクラス"""
    def __init__(self, config: Z80Config, logger: Z80Logger):
        self.config = config
        self.logger = logger
        self.raw_bytes = bytearray(65536)
        self.attributes = [set() for _ in range(65536)]

    def is_valid_address(self, addr):
        """指定したアドレスが16ビットのメモリ空間（0〜0xFFFF）に収まっているかを確認する"""
        if not (0 <= addr <= 0xFFFF):
            self.logger.log(f"[-] 警告: 16ビットメモリ空間外へのアクセスを検出しました: {addr}")
            return False
        return True

    def reset_attributes(self, old_start, old_end):
        """メモリ属性を初期化し、バイナリが読み込まれた範囲の属性を一時的に 'DATA' に設定する"""
        for addr in range(65536):
            self.attributes[addr].clear()
        for addr in range(old_start, old_end):
            if self.is_valid_address(addr):
                self.attributes[addr].add('DATA')

    def load_file(self):
        """ダンプファイル（16進数テキスト）またはバイナリファイルを読み込み、仮想メモリ上に展開する"""
        if not os.path.exists(self.config.input_file):
            print(f"[-] エラー: 入力ファイル '{self.config.input_file}' が見つかりません。")
            return False
            
        _, ext = os.path.splitext(self.config.input_file.lower())
        
        try:
            if ext in ['.txt', '.hex']:
                binary = bytearray()
                with open(self.config.input_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # 先頭に16進アドレス表示（コロンを含む、または4桁以上の16進数値）が存在するか判定
                        match = re.match(r'^([0-9A-Fa-f:]+)\s+(.*)', line)
                        if match:
                            addr_part = match.group(1).replace(':', '')
                            if len(addr_part) >= 4 and all(c in '0123456789ABCDEFabcdef' for c in addr_part):
                                data_part = match.group(2).strip()[: 2*16 + 15].replace('-', ' ') # 2文字*16+区切り文字15個
                                for t in data_part.split():
                                    try:
                                        binary.append(int(t, 16))
                                    except ValueError:
                                        print(f"[-] エラー: 16進数表記ではありません。: {e}")
                                        return False
                                continue
                        
                        # アドレス部を含まない一般的なスペース・ハイフン区切りの16進テキスト
                        line_clean = line.replace('-', ' ')
                        for t in line_clean.split():
                            try:
                                binary.append(int(t, 16))
                            except ValueError:
                                print(f"[-] エラー: 16進数表記ではありません。: {e}")
                                return False
            else:
                with open(self.config.input_file, 'rb') as f:
                    binary = bytearray(f.read())
        except Exception as e:
            print(f"[-] エラー: ファイルの読み込みに失敗しました: {e}")
            return False
                
        length = len(binary)
        self.config.old_end = self.config.old_start + length
        
        if self.config.old_start + length > 65536:
            length = 65536 - self.config.old_start
            self.config.old_end = 65536
            
        self.raw_bytes[self.config.old_start:self.config.old_end] = binary[:length]
        return True

    def mark_attribute(self, addr, attr):
        """指定したアドレスに属性（CODE, WORK, MERGE等）を設定する"""
        if not self.is_valid_address(addr):
            return False
        self.attributes[addr].add(attr)
        return True

    def discard_attribute(self, addr, attr):
        """指定したアドレスから特定の属性を取り除く"""
        if not self.is_valid_address(addr):
            return False
        self.attributes[addr].discard(attr)
        return True

    def has_attribute(self, addr, attr):
        """指定したアドレスに特定の属性が設定されているかを調べる"""
        if not self.is_valid_address(addr):
            return False
        return attr in self.attributes[addr]

    def get_byte(self, addr):
        """仮想メモリから1バイト読み出す"""
        if not self.is_valid_address(addr):
            raise IndexError(f"アドレス範囲外アクセス: {addr}")
        return self.raw_bytes[addr]

    def get_word(self, addr):
        """仮想メモリから16ビットのワード（リトルエンディアン形式）を読み出す"""
        addr_next = addr + 1
        if not self.is_valid_address(addr) or not self.is_valid_address(addr_next):
            raise IndexError(f"アドレス範囲外アクセス: {addr}")
        return self.raw_bytes[addr] | (self.raw_bytes[addr_next] << 8)


class SectionRange:
    """CODEやWORKなど、連続するメモリセグメントの開始と終了アドレスを管理する構造体"""
    def __init__(self, start_addr, end_addr, attr_type):
        self.start_addr = start_addr
        self.end_addr = end_addr
        self.attr_type = attr_type


class Z80AddressRecord:
    """リロケーション（再配置）前後のアドレス対応マップと、シンボルの属性情報を保持するクラス"""
    def __init__(self, old_address, label_name, new_address=0, is_code=False, is_work=False, is_bios=False):
        self.old_address = old_address
        self.label_name = label_name
        self.new_address = new_address
        self.is_code = is_code
        self.is_work = is_work
        self.is_bios = is_bios
        self.references = []


class Z80AddressRegistry:
    """ラベル情報の登録・検索、およびリロケーション時のアドレス変換を一括で管理するクラス"""
    def __init__(self, config: Z80Config, mem: Z80MemoryImage, logger: Z80Logger):
        self.config = config
        self.mem = mem
        self.logger = logger
        
        # アドレスとBIOSフラグのタプル(address, is_bios)をキーとして管理する
        self.records = {}
        self.labels = {}
        self.unresolved_records = set()
        
        self.byte_to_instruction_start = {}
        
        self.code_byte_offsets = {}
        self.work_byte_offsets = {}
        self.data_byte_offsets = {}
        self.total_code_size = 0
        self.total_work_size = 0
        self.total_data_size = 0
        self.bdos_rutine_size = 0
        self.patch_delta_offset = 0
        
        self._pre_register_system_symbols()

    def _pre_register_system_symbols(self):
        """初期設定に必要なシステムワークアドレスおよびBDOSサブルーチン等で使用するBIOSアドレスを登録する"""
        key = (STACK_INIT_VAL, True)
        self.labels[key] = "STACK_INIT_ADDR"
        self.records[key] = Z80AddressRecord(
            STACK_INIT_VAL, "STACK_INIT_ADDR", STACK_INIT_VAL, is_code=False, is_work=True, is_bios=True
        )
        
        # システムワークエリアや文字入出力BIOSなどの固定アドレス一覧
        essential_addresses = [
            0x0138,  # RSLREG (システムBIOS)
            0x0024,  # ENASLT (システムBIOS)
            0xFCC1,  # EXPTBL (システム拡張スロット判定テーブル/システムBIOSスロット)
            0xF37D,  # ROMBDOS (BDOSコール用フック)
            0x00A2,  # CHPUT (文字出力BIOS)
            0x009F,  # CHGET (文字入力BIOS)
            0x009C,  # CHSNS (キー入力状態取得)
            0x00C0,  # BEEP (BEEP音)
            0x00A5   # LPTOUT (プリンタ出力)
        ]
        for addr in essential_addresses:
            self.register_bios_address(addr)

    def populate_segment_offsets(self, analyser=None):
        """再配置にあたり、CODE/WORK/DATAの各領域が占有する連続した物理サイズとオフセットを算出する。

        BDOS等の置換処理、およびSMCパッチに伴うアセンブリ出力サイズの変化分（累積オフセット）を事前に検知し、
        アドレスマッピングに反映させてオフセットのズレを自動的に補正する。
        """
        self.code_byte_offsets.clear()
        self.work_byte_offsets.clear()
        self.data_byte_offsets.clear()

        # CODEセグメントのオフセット計算
        current_offset = 0
        accumulated_delta = 0

        pc = self.config.old_start
        while pc < self.config.old_end:
            if self.mem.has_attribute(pc, 'CODE'):
                delta = 0
                opcode = self.mem.get_byte(pc)
                
                # SMCパッチ（通常モードのみ適用）によるサイズ変化の算出
                if USE_SMC_PATCH and not COPY_CODE_TO_RAM and analyser is not None:
                    if pc in analyser.smc_patch_jr_addresses:
                         delta = smc_patch_jr_code_jr_size - 2  # 元のJRは2バイト、パッチ後は9バイト
                    elif (pc - 3) in analyser.smc_patch_jr_addresses:
                        delta = smc_patch_jr_code_ld_size - 3  # 元のld (nn), aは3バイト、パッチ後は省略(0バイト)

                classifier = Z80OpcodeClassifier(self.mem, self)
                length, _, _ = classifier.decode_instruction(pc)
                
                # 展開後のサイズ増加分を加味してアドレスマッピングを登録する
                for i in range(length):
                    addr = pc + i
                    if addr < self.config.old_end:
                        self.code_byte_offsets[addr] = current_offset + accumulated_delta + i
                
                accumulated_delta += delta
                current_offset += length
                pc += length
            else:
                pc += 1

        bdos_replace_routines_size = 0
        for fn_key, routine in BDOS_REPLACE_ROUTINES.items():
            if routine.get("used") is not None:
                bdos_replace_routines_size += routine["size"]
        self.bdos_rutine_size = bdos_replace_routines_size

        self.patch_delta_offset = accumulated_delta

        self.total_code_size = current_offset + accumulated_delta + bdos_replace_routines_size

        # 2. WORKセグメント（ワークエリア）のオフセット計算
        current_offset = 0
        for pc in range(self.config.old_start, self.config.old_end):
            if ((self.mem.has_attribute(pc, 'WORK') or 
                    self.mem.has_attribute(pc, 'MERGE')) and
                    not self.mem.has_attribute(pc, 'CODE')):
                self.work_byte_offsets[pc] = current_offset
                current_offset += 1
        self.total_work_size = current_offset

        # 3. DATAセグメント（ROM常駐データ）のオフセット計算
        current_offset = 0
        for pc in range(self.config.old_start, self.config.old_end):
            if (self.mem.has_attribute(pc, 'DATA') and 
                    not self.mem.has_attribute(pc, 'CODE') and 
                    not self.mem.has_attribute(pc, 'WORK') and 
                    not self.mem.has_attribute(pc, 'MERGE')):
                self.data_byte_offsets[pc] = current_offset
                current_offset += 1
        self.total_data_size = current_offset

    def translate_address(self, addr, is_code=False, is_bios=False):
        """元の古いアドレスを、動作設定に応じた新しい物理アドレスへマッピング変換する"""
        if addr >= SYSYTEM_WORK:
            return addr

        if is_bios:
            return addr

        # 通常モード、RAMコピーモード共通：WORK/MERGEのアドレス変換
        if (self.mem.has_attribute(addr, 'WORK') or 
                self.mem.has_attribute(addr, 'MERGE')):
            offset = self.work_byte_offsets.get(addr, 0)
            if COPY_CODE_TO_RAM:
                work_base = self.config.ram_start + self.total_code_size
            else:
                work_base = self.config.ram_start
            return work_base + offset

        # RAMコピーモード：CODE/DATAのアドレス変換
        if COPY_CODE_TO_RAM:
            if self.mem.has_attribute(addr, 'CODE'):
                offset = self.code_byte_offsets.get(addr, 0)
                return self.config.ram_start + offset
            elif self.mem.has_attribute(addr, 'DATA'):
                offset = self.data_byte_offsets.get(addr, 0)
                rom_code_phys_start = self.config.rom_start + ROM_HEADER_SIZE + ENTRY_CODE_SIZE
                rom_data_phys_start = rom_code_phys_start + self.total_code_size
                return rom_data_phys_start + offset
            return addr

        # 通常モード：CODE/DATAのアドレス変換
        if self.mem.has_attribute(addr, 'CODE') or self.mem.has_attribute(addr, 'DATA'):
            offset = addr - self.config.old_start
            return (self.config.rom_start + ROM_HEADER_SIZE + ENTRY_CODE_SIZE + offset)
        elif addr == self.config.old_start:
            return (self.config.rom_start + ROM_HEADER_SIZE)
        return addr

    def populate_instruction_map(self):
        """解析済みの情報を走査し、各メモリアドレスがどの命令の先頭に属しているかの対応マップを構築する"""
        self.byte_to_instruction_start.clear()
        pc = self.config.old_start
        classifier = Z80OpcodeClassifier(self.mem, self)
        while pc < self.config.old_end:
            if self.mem.has_attribute(pc, 'CODE'):
                length, target, inst_type = classifier.decode_instruction(pc)
                for i in range(length):
                    addr = pc + i
                    if self.mem.is_valid_address(addr) and addr < self.config.old_end:
                        self.byte_to_instruction_start[addr] = pc
                pc += length
            else:
                pc += 1

    def _resolve_system_label_name(self, addr):
        """msx_symbols の定義ファイルからシステムワークやBIOSの公式ラベル名を検索する"""
        label_name = None
        if hasattr(msx_symbols, "search_labels"):
            try:
                msx_labels = msx_symbols.search_labels(addr)
                if len(msx_labels) > 0:
                    label_name = msx_labels[0].replace(".", "_")
            except Exception:
                pass

        if not label_name and hasattr(msx_symbols, "search_labels_dos"):
            try:
                msx_labels = msx_symbols.search_labels_dos(addr)
                if len(msx_labels) > 0:
                    label_name = msx_labels[0].replace(".", "_")
            except Exception:
                pass
        return label_name

    def register_bios_address(self, addr, ref_pc=None):
        """BIOSやシステム固定アドレスを、リロケート対象外（is_bios=True）として登録する"""
        key = (addr, True)
        record = self.records.get(key)
        if record is None:
            label_name = self._resolve_system_label_name(addr)
            if not label_name:
                label_name = f"EXT_REF_{format_hex(addr)}"
            self.labels[key] = label_name
            record = Z80AddressRecord(addr, label_name, addr, is_code=False, is_work=False, is_bios=True)

        if ref_pc is not None and ref_pc not in record.references:
            record.references.append(ref_pc)
        self.records[key] = record

    def register_address(self, addr, ref_pc=None, is_code=False, is_bios=False, is_work=False):
        """プログラム内部で使用されるCODE/DATA/WORKに適切なラベルを割り当てる"""
        if not self.mem.is_valid_address(addr):
            return

        if self.mem.has_attribute(addr, 'CODE'):
            is_code = True

        key = (addr, is_bios)
        record = self.records.get(key)
        if record is not None:
            if ref_pc is not None and ref_pc not in record.references:
                record.references.append(ref_pc)
            record.is_code |= is_code
            record.is_work |= is_work
            return

        reserved = ["SP", "IX", "IY", "PC", "AF", "BC", "DE", "HL", "A", "B", "C", "D", "E", "H", "L"]
        
        if self.config.old_start <= addr < self.config.old_end and not is_bios:
            if key not in self.labels:
                is_work_attr = self.mem.has_attribute(addr, 'WORK') or self.mem.has_attribute(addr, 'MERGE')
                if is_work_attr:
                    is_work = True
                
                if is_code:
                    label_name = f"CODE_{addr:04X}H"
                elif is_work:
                    label_name = f"WORK_{addr:04X}H"
                else:
                    label_name = f"DATA_{addr:04X}H"
                    
                new_addr = self.translate_address(addr, is_code=is_code, is_bios=is_bios)
                record = Z80AddressRecord(addr, label_name, new_addr, is_code=is_code, is_work=is_work, is_bios=is_bios)
                if ref_pc is not None:
                    record.references.append(ref_pc)
                self.records[key] = record
                self.labels[key] = label_name
        else:
            if key not in self.labels:
                label_name = self._resolve_system_label_name(addr)
                
                if not label_name:
                    hex_str = f"{addr:04X}H"
                    if hex_str in reserved or hex_str.startswith("0") or hex_str[0].isdigit():
                        label_name = f"EXT_REF_0{hex_str}"
                    else:
                        label_name = f"EXT_REF_{hex_str}"
                        
                new_addr = self.translate_address(addr, is_code=is_code, is_bios=is_bios)
                record = Z80AddressRecord(addr, label_name, new_addr, is_code=is_code, is_work=is_work, is_bios=is_bios)
                if ref_pc is not None:
                    record.references.append(ref_pc)
                self.records[key] = record
                self.labels[key] = label_name

    def register_all_collected_symbols(self):
        """解析中に検出されたすべてのラベル情報を正式に登録する"""
        for (addr, is_bios) in sorted(list(self.unresolved_records)):
            self.register_address(addr, is_bios=is_bios)

    def get_label(self, addr, default_val=None, is_code=False, is_bios=False):
        """指定したアドレスに対応するアセンブララベル文字列を取得する（命令内のオフセットも自動計算する）"""
        if not is_bios and self.mem.has_attribute(addr, 'CODE'):
            is_code = True

        if addr < 0x100:
            is_bios = True # BDOS / BIOS 共通

        # 特例処理リストによるオフセット付き表記
        SPECIAL_OFFSETS = [
            (0xFCC0, 0xFCC1, -1, True)  # EXPTBL - 1
        ]

        for target_addr, base_addr, offset, is_code in SPECIAL_OFFSETS:
            if addr == target_addr:
                base_key = (base_addr, True)
                if base_key not in self.labels:
                    self.register_address(base_addr, is_code=False, is_bios=True)
                base_label = self.labels.get(base_key, format_asm_hex(base_addr))
                if offset > 0:
                    return f"{base_label} + {offset}"
                elif offset < 0:
                    return f"{base_label} - {abs(offset)}"
                return base_label

        if self.mem.has_attribute(addr, 'CODE'):
            is_code = True

        key = (addr, is_bios)

        # 「命令の先頭アドレス + オフセット」形式での解決を試みる
        if addr in self.byte_to_instruction_start and not is_bios:
            inst_start = self.byte_to_instruction_start[addr]
            offset = addr - inst_start
            if offset > 0:
                self.labels.pop(key, None)
                
                inst_key = (inst_start, is_bios)
                if inst_key not in self.labels:
                    self.register_address(inst_start, is_code=is_code, is_bios=is_bios)
                
                is_actual_code = self.mem.has_attribute(inst_start, 'CODE')
                
                if inst_key in self.labels:
                    inst_label = self.labels[inst_key]
                else:
                    if is_actual_code:
                        inst_label = f"CODE_{inst_start:04X}H"
                    else:
                        is_work = (self.mem.has_attribute(inst_start, 'WORK') or 
                                   self.mem.has_attribute(inst_start, 'MERGE') )
                        if is_work:
                            inst_label = f"WORK_{inst_start:04X}H"
                        else:
                            inst_label = f"DATA_{inst_start:04X}H"
                return f"{inst_label} + {offset}"

        if key in self.labels:
            return self.labels[key]
                
        return default_val


def get_reg8_sss(opcode):
    return {0:"B", 1:"C", 2:"D", 3:"E", 4:"H", 5:"L", 7:"A"}.get(opcode & 0x7, "")

def get_reg8_ddd(opcode):
    return get_reg8_sss(opcode >> 3)

def get_reg16_rp(opcode):
    return {0x00:"BC", 0x10:"DE", 0x20:"HL", 0x30:"SP"}.get(opcode & 0x30, "")

def get_reg16_af(opcode):
    return {0x00:"B", 0x10:"DE", 0x20:"HL", 0x30:"AF"}.get(opcode & 0x30, "")

class Z80OpcodeClassifier:
    """Z80命令をデコードし、各命令の構成（バイト長、分岐ターゲット、アドレッシング特性）を判別する解析クラス"""
    def __init__(self, mem: Z80MemoryImage, db: Z80AddressRegistry):
        self.mem = mem
        self.db = db

        # 1バイト命令マップ
        self.op_map_1byte = {
            0x00: "nop", 0xF3: "di", 0xFB: "ei", 0xC9: "ret", 0x7E: "ld a, (hl)",
            0x77: "ld (hl), a", 0x23: "inc hl", 0x13: "inc de", 0x1C: "inc e",
            0x1D: "dec e", 0x15: "dec d", 0x4F: "ld c, a", 0x3C: "inc a", 0xB7: "or a"
        }
        
        # 8ビット即値(n)をオペランドとする2バイト命令マップ
        self.op_map_2byte = {
            0x06: "ld b, {n}",   0x0E: "ld c, {n}",
            0x16: "ld d, {n}",   0x1E: "ld e, {n}",
            0x26: "ld h, {n}",   0x2E: "ld l, {n}",
            0x36: "ld (hl), {n}",0x3E: "ld a, {n}",
            0xC6: "add a, {n}",  0xCE: "adc a, {n}",
            0xD6: "sub {n}",     0xDE: "sbc a, {n}",
            0xE6: "and {n}",     0xEE: "xor {n}",
            0xF6: "or {n}",      0xFE: "cp {n}"
        }
        
        # 16ビットアドレス(nn)をオペランドとする 3バイト命令マップ
        self.op_map_3byte = {
            0xC3: "jp {nn}", 0xCD: "call {nn}"
        }

    def decode_instruction(self, pc):
        """プログラムカウンタの示すアドレスから1つの命令を切り出し、長さ・分岐先を特定する。

        Z80で定義されている各種命令プレフィックス（CB, ED, DD, FD）を識別して下位デコーダに分岐させる。
        """
        opcode = self.mem.get_byte(pc)
        
        # 1. プレフィックスコード（2バイト以上の命令を構成する先行命令）の検出
        if opcode == 0xED:
            # EDプレフィックス：拡張命令群（16ビット加減算、ブロック転送、I/O操作、レジスタ間ペア転送など）
            return self._decode_ed(pc)
        elif opcode == 0xCB:
            # CBプレフィックス：ビット操作命令群（ビットテスト、セット、リセット、ローテート、シフト）
            return self._decode_cb(pc)
        elif opcode == 0xDD:
            # DDプレフィックス：インデックスレジスタ IX による相対アドレッシング修飾
            return self._decode_index(pc, "ix")
        elif opcode == 0xFD:
            # FDプレフィックス：インデックスレジスタ IY による相対アドレッシング修飾
            return self._decode_index(pc, "iy")

        # 2. MSX特有のシステムインタースロットコール命令 (RST 30H)
        # オ命令に続いて、1バイトのスロットID、2バイトの呼び出し先アドレスが配置されるため計4バイト構成となる。
        if opcode == 0xF7:
            return 4, None, "RST_30"

        # 3. 相対ループ用DJNZ命令
        # デクリメントしたBレジスタが0でなければ相対オフセットへジャンプ（1バイトの符号付き相対アドレスを伴う2バイト命令）。
        if opcode == 0x10:
            offset = self.mem.get_byte(pc+1)
            if offset & 0x80: offset -= 256  # 2の補数キャストによる負方向ジャンプ対応
            target = (pc + 2 + offset) & 0xFFFF
            return 2, target, "DJNZ"

        # 4. 3バイトの無条件絶対アドレスジャンプ・コール命令（C3H = JP nn / CDH = CALL nn）
        if opcode in self.op_map_3byte:
            target = self.mem.get_word(pc+1)
            return 3, target, "jp {nn}" if opcode == 0xC3 else "call {nn}"

        # 5. 条件付きジャンプ命令 (JP cc, nn)（3バイト構成）
        # ビット5-3の判定フィールドに対応する各フラグ条件（cc = NZ, Z, NC, C, PO, PE, P, M）を特定する。
        if opcode in [0xC2, 0xCA, 0xD2, 0xDA, 0xE2, 0xEA, 0xF2, 0xFA]:
            target = self.mem.get_word(pc+1)
            return 3, target, "JP_COND"

        # 6. 条件付きコール命令 (CALL cc, nn)（3バイト構成）
        if opcode in [0xC4, 0xCC, 0xD4, 0xDC, 0xE4, 0xEC, 0xF4, 0xFC]:
            target = self.mem.get_word(pc+1)
            return 3, target, "CALL_COND"

        # 7. 相対ジャンプ命令 (JR cc, e)（2バイト構成）
        # cc = 無条件(0x18)、NZ(0x20)、Z(0x28)、NC(0x30)、C(0x38)。後続の1バイト符号付き相対アドレスによりオフセット算出。
        if opcode in [0x18, 0x20, 0x28, 0x30, 0x38]:
            offset = self.mem.get_byte(pc+1)
            if offset & 0x80: offset -= 256  # 符号付きオフセット計算
            target = (pc + 2 + offset) & 0xFFFF
            return 2, target, "JR"

        # 8. メモリアクセス転送命令 (LD (nn), A / LD A, (nn) 等)（3バイト構成）
        if opcode in [0x32, 0x22, 0x3A, 0x2A]:
            target = self.mem.get_word(pc+1)
            return 3, target, "LD_MEM"

        # 9. 16ビットレジスタペア即値ロード命令 (LD rp, nn)（3バイト構成）
        if opcode in [0x01, 0x11, 0x21, 0x31]:
            val = self.mem.get_word(pc+1)
            return 3, val, "LD_REG16"

        # 10. 8ビット即値(n)を伴う基本命令（2バイト構成）
        # LD r, n や ADD A, n および ポート入出力 OUT (n), A / IN A, (n) を含む。
        len_map_2byte = list(self.op_map_2byte.keys()) + [0xD3, 0xDB]
        if opcode in len_map_2byte:
            return 2, None, "2BYTE"

        # 11. その他の1バイト完結命令（レジスタ間転送・演算等）
        return 1, None, "1BYTE"

    def _decode_ed(self, pc):
        """EDプレフィックス（拡張仕様命令）におけるアドレッシングと命令長判定を行う。"""
        sub_op = self.mem.get_byte(pc + 1)
        # LD (nn), rp / LD rp, (nn) 形式の16ビットレジスタ対とメモリ間の間接ロード命令は4バイト構成
        if sub_op in [0x43, 0x53, 0x73, 0x4B, 0x5B, 0x7B]:
            target = self.mem.get_word(pc + 2)
            return 4, target, "ED_LD"
        # その他の命令（ブロック転送 LDI/LDIR, I/OポートC間接, 16ビット加減算等）はプレフィックス含め2バイト構成
        return 2, None, "ED_OTHER"

    def _decode_cb(self, pc):
        """CBプレフィックス（ビット操作・シフトローテート命令）における判定。

        CB修飾を受けるZ80命令はすべて、プレフィックスを含めて一律2バイト長で構成される。
        """
        return 2, None, "CB"

    def _decode_index(self, pc, reg):
        """DD/FDプレフィックス（IX/IYレジスタ修飾命令）におけるアドレッシング形式と命令長の特定を行う。"""
        # プレフィックスCB、ディスプレースメントd、ビット処理用命令の順番で配置される。
        op = self.mem.get_byte(pc + 1)
        
        # 16ビット即値データまたはアドレス操作 (LD IX/IY, nn / LD (nn), IX/IY / LD IX/IY, (nn)) (4バイト構成)
        if op in [0x21, 0x22, 0x2A]:
            val = self.mem.get_word(pc + 2)
            return 4, val, "INDEX_LD"

        # DDFDプレフィックスにCBプレフィックスがさらに連続する特殊命令形式 (常に4バイト構成)
        # 例: RLC (IX+d), BIT b, (IY+d)
        if op == 0xCB:
            return 4, None, "INDEX_CB"

        # Z80命令表における「(HL)」指定箇所（レジスタフィールド 110b）の有無を特定する。
        # ビット5-3（転送先）またはビット2-0（転送元）が 110b である場合、ディスプレースメント付き間接参照（IX+d/IY+d）となる。
        is_indirect_hl = ((op >> 3) & 7) == 6 or (op & 7) == 6

        # インデックス相対間接参照 (IX+d / IY+d) を伴う演算・転送命令の解析
        if op in [0x34, 0x35, 0x36] or is_indirect_hl:
            # LD (IX/IY+d), n のようにディスプレースメントに加えて即値データを伴う転送は4バイト長となる。
            if op == 0x36:
                return 4, None, "INDEX_WRITE_VAL"
            # その他の LD r, (IX/IY+d) などの演算命令は3バイト構成 (プレフィックス2バイト + ディスプレースメントd)
            return 3, None, "INDEX_LD_DISP"

        # インデックスレジスタの高位・低位部（IXH, IXL等）を独立して操作する未ドキュメント演算命令などの長さ算出
        length = 1 + get_standard_len(op)
        return length, None, "INDEX_OTHER"

class Z80FlowAnalyser:
    """CPUシミュレーションによりプログラムの実行経路を解析し、属性や自己書き換えコード（SMC）を検出するクラス"""
    def __init__(self, config: Z80Config, mem: Z80MemoryImage):
        self.config = config
        self.mem = mem
        self.db = None
        self.logger = None

        self.smc_detections = []
        self.smc_patch_jr_addresses = set()

        self.unsupported_bdos_calls = []

        self.traced_paths = set()

        self.sections = []
        self.max_existing_ram = 0
        self.bdos_fn_map = {}

        self.simple_pass = True

        # 実際にメモリアドレスを指すポインタとして使用された形跡のあるワークエリアアドレス
        self.pointer_work_addresses = set()

        # レジスタの値の変遷を記録・追跡するための管理用情報
        self.register_tracker = {}
        self.memory_load_tracker = {}

        # ログ出力の重複防止
        self.logged_pointer_writes = set()
        self.logged_interrupt_hook_writes = set()

        self.pointer_load_commands = set()
        self.classifier = Z80OpcodeClassifier(self.mem, None)
        self.subroutine_pointer_usage_cache = {}

    def analyze_flow(self, db: Z80AddressRegistry, logger: Z80Logger):
        """プログラムの解析を実行する。仮想スタックに分岐履歴を積みながら全実行経路をトレースする"""
        self.db = db
        self.logger = logger
        self.mem.reset_attributes(self.config.old_start, self.config.old_end)
            
        self.traced_paths.clear()
        self.subroutine_pointer_usage_cache.clear()
        self.pointer_work_addresses.clear()
        
        self.logged_pointer_writes.clear()
        self.logged_interrupt_hook_writes.clear()

        # パス1: プログラムの実行パスと、間接アドレス参照に使用されるワークエリアの特定
        if self.logger is not None:
            self.logger.log("="*70)
            self.logger.log(center_text("解析 Pass 1 （CODE/DATA/WORK属性分け）を実行中...", 70))
            self.logger.log("="*70)
        self.analyze_flow_from_entries([self.config.old_start], db, logger, reset_sections=True, simple_pass=PASS1_USE_SIMPLE_PASS)
        if self.pointer_work_addresses:
            self.logger.log(f"[*] アドレス格納用ワークエリアの検出: {['0x%04X' % addr for addr in sorted(list(self.pointer_work_addresses))]}")

        # パス2: 特定されたアドレス格納用ワークエリアに初期値（即値アドレス）をロードしている箇所を逆引き追跡
        if self.logger is not None:
            self.logger.log("="*70)
            self.logger.log(center_text("解析 Pass 2 （分岐を含めた実行経路のシミュレート・分析）を実行中...", 70))
            self.logger.log("="*70)

        self.traced_paths.clear()
        self.analyze_flow_from_entries([self.config.old_start], db, logger, reset_sections=True)

    def _get_register_state_key(self, regs):
        # ポインタ追跡に関わる主要レジスタの現在値を抽出してタプル化
        return (
            regs['HL']['source_pc'],
            regs['DE']['source_pc'],
            regs['BC']['source_pc'],
            regs['IX']['source_pc'],
            regs['IY']['source_pc'],

            # 重くなるが、値違いでの分岐を処理するなら必要になる
            #regs['HL']['val'],
            #regs['DE']['val'],
            #regs['BC']['val'],
            #regs['IX']['val'],
            #regs['IY']['val'],
        )

    def analyze_flow_from_entries(self, entries, db, logger, reset_sections=False, simple_pass = False):
        """指定された起点（エントリーポイント）から、プログラムの実行パスを追加でシミュレーション解析する"""
        self.db = db
        self.logger = logger
        self.simple_pass = simple_pass

        # 実行分岐時におけるレジスタ状態などを退避・復元するためのシミュレーション用コンテキストスタック
        stack = []
        for entry in entries:
            if entry in self.traced_paths:
                continue
            stack.append((entry, {
                'regs': {
                    'BC':  {'val': 0, 'source_pc': None},
                    'DE':  {'val': 0, 'source_pc': None},
                    'HL':  {'val': 0, 'source_pc': None},
                    'IX':  {'val': 0, 'source_pc': None},
                    'IY':  {'val': 0, 'source_pc': None},
                    'A':   {'val': 0, 'source_pc': None},
                    'B':   {'val': 0, 'source_pc': None},
                    'C':   {'val': 0, 'source_pc': None},
                    'D':   {'val': 0, 'source_pc': None},
                    'E':   {'val': 0, 'source_pc': None},
                    'H':   {'val': 0, 'source_pc': None},
                    'L':   {'val': 0, 'source_pc': None},
                    'IXH': {'val': 0, 'source_pc': None},
                    'IXL': {'val': 0, 'source_pc': None},
                    'IYH': {'val': 0, 'source_pc': None},
                    'IYL': {'val': 0, 'source_pc': None},
                },
                'mem_loads': {}  # ワークエリアのアドレスとロード先レジスタの対応関係マップ
            }))

        if reset_sections:
            self.traced_paths.clear()

        while stack:
            pc, tracker_state = stack.pop()
            
            if not (self.config.old_start <= pc < self.config.old_end):
                continue

            if simple_pass:
                # PC をキーにして重複ルート判定（簡易探索）
                path_key = pc
            else:
                # PC と regsステート をキーにして重複ルート判定
                state_key = self._get_register_state_key(tracker_state['regs'])
                path_key = (pc, state_key)
            if path_key in self.traced_paths:
                continue

            self.traced_paths.add(path_key)
            
            # 分岐先の退避情報から状態をディープコピーして復元する
            self.register_tracker = copy.deepcopy(tracker_state['regs'])
            self.memory_load_tracker = copy.deepcopy(tracker_state['mem_loads'])
            self._trace_instruction(pc, stack)

        if reset_sections:
            self.sections.clear()
        self._group_sections()

    def _check_subroutine_use(self, start_pc, target_reg):
        """指定されたサブルーチンの開始位置から、対象レジスタが上書きされる前にポインタとして使用されているかチェックする"""
        visited = set()
        local_stack = [start_pc]
        
        while local_stack:
            pc = local_stack.pop()
            if pc in visited or not (self.config.old_start <= pc < self.config.old_end):
                continue
            visited.add(pc)
            
            opcode = self.mem.get_byte(pc)
            length, target, inst_type = self.classifier.decode_instruction(pc)
            
            is_overwritten = False
            if target_reg == "HL":
                if inst_type == "LD_REG16" and opcode in [0x21, 0x31]:
                    is_overwritten = True
                elif opcode == 0xE1:
                    is_overwritten = True
            elif target_reg == "DE":
                if inst_type == "LD_REG16" and opcode == 0x11:
                    is_overwritten = True
                elif opcode == 0xD1:
                    is_overwritten = True
            elif target_reg == "BC":
                if inst_type == "LD_REG16" and opcode == 0x01:
                    is_overwritten = True
                elif opcode == 0xC1:
                    is_overwritten = True
                    
            if is_overwritten:
                continue
                
            is_accessed = False
            if target_reg == "HL":
                if 0x40 <= opcode <= 0x7F and opcode != 0x76:
                    if (opcode & 7) == 6 or (opcode & 0x38) == 0x30:
                        is_accessed = True
                elif 0x80 <= opcode <= 0xBF and (opcode & 7) == 6:
                    is_accessed = True
                elif inst_type == "ED_OTHER":
                    sub_op = self.mem.get_byte(pc+1)
                    if sub_op in [0xB0, 0xB8]:
                        is_accessed = True
                    elif sub_op in [0xA1, 0xA9, 0xB1, 0xB9, 0xA2, 0xB2, 0xAA, 0xBA, 0xA3, 0xB3, 0xAB, 0xBB]:
                        is_accessed = True
            elif target_reg == "DE":
                if opcode in [0x1A, 0x12]:
                    is_accessed = True
                elif inst_type == "ED_OTHER":
                    sub_op = self.mem.get_byte(pc+1)
                    if sub_op in [0xB0, 0xB8]:
                        is_accessed = True
            elif target_reg == "BC":
                if opcode in [0x0A, 0x02]:
                    is_accessed = True
                    
            if is_accessed:
                return True
                
            if opcode == 0xC9:
                continue
                
            is_jp_or_call = inst_type.startswith("jp") or inst_type.startswith("call")
            if is_jp_or_call:
                local_stack.append(pc + 3)
                if target is not None:
                    local_stack.append(target)
            elif inst_type in ["JP_COND", "CALL_COND"]:
                local_stack.append(pc + 3)
                if target is not None:
                    local_stack.append(target)
            elif inst_type in ["JR", "DJNZ"]:
                local_stack.append(pc + 2)
                if target is not None:
                    local_stack.append(target)
            else:
                local_stack.append(pc + length)
                
        return False

    def _trace_instruction(self, pc, stack):
        """シミュレータ本体。命令がレジスタや仮想メモリに与える影響を追跡する"""
        opcode = self.mem.get_byte(pc)
        length, target, inst_type = self.classifier.decode_instruction(pc)
        
        for i in range(length):
            addr = pc + i
            if self.mem.is_valid_address(addr):
                self.mem.discard_attribute(addr, 'DATA')
                self.mem.mark_attribute(addr, 'CODE')
        
        #----------------------------------------------------------------
        # 復帰命令
        #----------------------------------------------------------------
        if opcode == 0xC9:  # ret
            return
        if opcode == 0xED:
            sub_op = self.mem.get_byte(pc + 1)
            if sub_op in [0x45, 0x4D]:  # retn, reti
                return

        #----------------------------------------------------------------
        # レジスタ指定分岐命令
        # 簡易処理の為、
        # ポインタ参照位置の操作だけ行い、分岐先には飛ばない
        # （対応するのが望ましいが内部処理の完備が必要なので保留）
        #----------------------------------------------------------------
        if opcode == 0xE9:  # jp (hl)
            self._register_pointer_access("HL", pc)
            return
        if opcode == 0xDD and self.mem.get_byte(pc + 1) == 0xE9:  # jp (ix)
            self._register_pointer_access("IX", pc)
            return
        if opcode == 0xFD and self.mem.get_byte(pc + 1) == 0xE9:  # jp (iy)
            self._register_pointer_access("IY", pc)
            return

        #----------------------------------------------------------------
        # RST 30H インタースロットコール
        # スロット、アドレスの分もPCを進める
        #----------------------------------------------------------------
        if opcode == 0xF7: # rst 30h
            target_bios = self.mem.get_word(pc + 2)
            if self.db is not None:
                self.db.register_bios_address(target_bios, pc)
            stack.append((pc + 4, {
                'regs': copy.deepcopy(self.register_tracker),
                'mem_loads': copy.deepcopy(self.memory_load_tracker)
            }))
            return

        #----------------------------------------------------------------
        # ワークエリア領域から各レジスタへのデータ読み込み状況をチェック
        #----------------------------------------------------------------
        self._track_memory_loads(pc, opcode, inst_type)

        #----------------------------------------------------------------
        # レジスタへのロード追跡
        #----------------------------------------------------------------
        # 16ビットレジスタへの即値ロード
        if inst_type == "LD_REG16":
            reg = get_reg16_rp(opcode)
            if reg != "SP" and reg != "":
                self.register_tracker[reg] = {'val': target, 'source_pc': pc}
                self.register_tracker[reg[0]] = {'val': target >> 8, 'source_pc': pc}
                self.register_tracker[reg[1]] = {'val': target & 0xFF, 'source_pc': pc}
                self.memory_load_tracker.pop(reg, None)  # 即値が代入されたため、ワークエリアからの読み込み履歴はクリアする
        elif inst_type == "INDEX_LD" and opcode == 0xDD:
            self.register_tracker['IX'] = {'val': target, 'source_pc': pc}
            self.register_tracker['IXH'] = {'val': target >> 8, 'source_pc': pc}
            self.register_tracker['IXL'] = {'val': target & 0xFF, 'source_pc': pc}
            self.memory_load_tracker.pop('IX', None)
        elif inst_type == "INDEX_LD" and opcode == 0xFD:
            self.register_tracker['IY'] = {'val': target, 'source_pc': pc}
            self.register_tracker['IYH'] = {'val': target >> 8, 'source_pc': pc}
            self.register_tracker['IYL'] = {'val': target & 0xFF, 'source_pc': pc}
            self.memory_load_tracker.pop('IY', None)
        
        # 8ビットレジスタへの即値ロード
        elif opcode in [0x06,0x0e,0x16,0x1e,0x26,0x2e,0x3e]:  # ld r, n
            # 00rrr110
            reg8 = get_reg8_ddd(opcode)
            reg16 = get_reg16_rp(opcode)
            if reg8 != "":
                val = self.mem.get_byte(pc + 1)
                self.register_tracker[reg8] = {'val': val, 'source_pc': pc}
                if reg16 != "SP" and reg16 != "":
                    self.register_tracker[reg16]['source_pc'] = None
                    self.memory_load_tracker.pop(reg16, None)
        elif inst_type == "INDEX_OTHER" and opcode in [0xDD, 0xFD]: # ld ixh/ixh/iyh/iyl, n
            # LD IXH, n：DD 26 n
            # LD IXL, n：DD 2E n
            # LD IYH, n：FD 26 n
            # LD IYL, n：FD 2E n
            op = self.mem.get_byte(pc + 1)
            if op is not None and op in [0x26, 0x2e]:
                reg16 = "IX" if opcode == 0xDD else "IY"
                reg8 = reg16 + get_reg8_ddd(opcode)
                self.register_tracker[reg8] = {'val': target, 'source_pc': pc}
                self.register_tracker[reg]['source_pc'] = None
                self.memory_load_tracker.pop(reg, None)

        if opcode == 0x7D:  # ld a, l
            self.register_tracker['A'] = {'val': self.register_tracker['HL']['val'] & 0xFF, 'source_pc': pc}
        elif opcode == 0x7C:  # ld a, h
            self.register_tracker['A'] = {'val': (self.register_tracker['HL']['val'] >> 8) & 0xFF, 'source_pc': pc}

        # pop
        elif opcode in [0xC1, 0xD1, 0xE1, 0xF1]: # pop bc/de/hl/af
            # （簡易処理）レジスタ読み込み情報を無効化
            # （メモリや演算のエミュレーションを実装するのが望ましい）
            self._stack_reg_transfer_tracker(opcode, pc)

        # ex （交換命令）
        elif opcode == 0x08: # ex af,af'
            pass # 裏レジスタ管理省略
        elif opcode == 0xEB: # ex de,hl
            # hl と de の記録を交換
            hl = self.register_tracker['HL']
            de = self.register_tracker['DE']
            ml = self.memory_load_tracker
            hl['val'], de['val'] = de['val'], hl['val']
            hl['source_pc'], de['source_pc'] = de['source_pc'], hl['source_pc']
            ml['HL'], ml['DE'] = ml['DE'], ml['HL']
        elif opcode == 0xE3: # ex (sp),hl
            # （簡易処理）レジスタ読み込み情報を無効化
            # （メモリや演算のエミュレーションを実装するのが望ましい）
            self._stack_reg_transfer_tracker(opcode, pc)

        # 16ビット演算によるレジスタ変化の追跡
        # 読み込み元は変更しない。
        # 値の更新は簡単な計算のみ簡易的に行う。（全対応が望ましい）
        elif opcode in [0x03, 0x13, 0x23, 0x33]: # inc rp
            reg16 = get_reg16_rp(opcode)
            if reg16 != "":
                val = self.register_tracker[reg16]['val']
                self.register_tracker[reg16]['val'] = (val + 1) & 0xFFFF
        elif opcode in [0x05, 0x15, 0x25, 0x35]: # dec rp
            reg16 = get_reg16_rp(opcode)
            if reg16 != "":
                val = self.register_tracker[reg16]['val']
                self.register_tracker[reg16]['val'] = (val - 1) & 0xFFFF
        if opcode in [0x09, 0x19, 0x29, 0x39]: # add hl,rp
            #self.memory_load_tracker.pop('HL', None)
            pass # 計算省略
        elif opcode == 0xDD:
            sub_op = self.mem.get_byte(pc + 1)
            if sub_op in [0x09, 0x19, 0x29, 0x39]: # add ix,rp
                #self.memory_load_tracker.pop('IX', None)
                pass # 計算省略
        elif opcode == 0xFD:
            sub_op = self.mem.get_byte(pc + 1)
            if sub_op in [0x09, 0x19, 0x29, 0x39]: # add iy,rp
                #self.memory_load_tracker.pop('IY', None)
                pass # 計算省略
        
        #----------------------------------------------------------------
        # メモリへの書き込み追跡
        #----------------------------------------------------------------
        self._track_writes(pc, opcode, inst_type) # 特殊書き込みのチェック

        #----------------------------------------------------------------
        # 間接参照の追跡
        #----------------------------------------------------------------
        if opcode == 0xED:
            sub_op = self.mem.get_byte(pc + 1)
            if sub_op in [0xB0, 0xB8]:  # ldir, lddr
                self._check_block_transfer_hook_write(pc)

        is_hl_mem_access = False
        if 0x40 <= opcode <= 0x7F and opcode != 0x76:
            if (opcode & 7) == 6 or (opcode & 0x38) == 0x30:
                is_hl_mem_access = True
        elif 0x80 <= opcode <= 0xBF and (opcode & 7) == 6:
            is_hl_mem_access = True

        # CBプレフィックスを伴うビットテスト等における (hl) への間接アクセスを検出
        if opcode == 0xCB:
            sub_op = self.mem.get_byte(pc + 1)
            if (sub_op & 7) == 6:  # bit n, (hl) などの間接参照
                is_hl_mem_access = True

        if is_hl_mem_access:
            self._register_pointer_access("HL", pc)
        elif opcode in [0x0A, 0x02]:
            self._register_pointer_access("BC", pc)
        elif opcode in [0x1A, 0x12]:
            self._register_pointer_access("DE", pc)
        elif inst_type == "ED_OTHER":
            sub_op = self.mem.get_byte(pc + 1)
            # ブロック転送命令における HL, DE の参照登録
            if sub_op in [0xA0, 0xB0, 0xA8, 0xB8]:
                self._register_pointer_access("HL", pc)
                self._register_pointer_access("DE", pc)
            # 各種ブロック比較等の命令における HL 参照登録
            elif sub_op in [0xA1, 0xB1, 0xA9, 0xB9, 0xA2, 0xB2, 0xAA, 0xBA, 0xA3, 0xB3, 0xAB, 0xBB]:
                self._register_pointer_access("HL", pc)

        # IX / IY インデックス修飾付きの間接アドレス参照を検査
        if opcode in [0xDD, 0xFD]:
            op = self.mem.get_byte(pc + 1)
            reg_name = "IX" if opcode == 0xDD else "IY"
            is_index_indirect = False
            if op == 0xCB:
                is_index_indirect = True
            elif inst_type in ["INDEX_LD_DISP", "INDEX_WRITE_VAL"]:
                is_index_indirect = True
            elif inst_type == "INDEX_OTHER":
                is_index_indirect = ((op >> 3) & 7) == 6 or (op & 7) == 6
                
            if is_index_indirect:
                self._register_pointer_access(reg_name, pc)

        #----------------------------------------------------------------
        # JP/CALLの処理
        #----------------------------------------------------------------
        is_jp_or_call = inst_type.startswith("jp") or inst_type.startswith("call")
        if is_jp_or_call:
            if target == 0x001C:
                # CALSLT (スロット間コールBIOS)
                ix_state = self.register_tracker['IX']
                ix_val = ix_state['val']
                ix_source_pc = ix_state['source_pc']
                if ix_source_pc is not None:
                    self.pointer_load_commands.add(ix_source_pc)
                    self._check_and_register_ram(ix_val)
                    if self.db is not None:
                        self.db.register_bios_address(ix_val, ix_source_pc)

            if opcode == 0xCD and target == BDOS_CALL_ADDRESS:
                self._analyse_bdos_call(pc)
                #fn_code = self.bdos_fn_map.get(pc)
                if True: #fn_code is not None:
                    self._check_and_register_ram(target)
                    stack.append((target, {
                        'regs': copy.deepcopy(self.register_tracker),
                        'mem_loads': copy.deepcopy(self.memory_load_tracker)
                    }))
                return

            if target == 0x0000:
                self._check_and_register_ram(target)
                stack.append((target, {
                    'regs': copy.deepcopy(self.register_tracker),
                    'mem_loads': copy.deepcopy(self.memory_load_tracker)
                }))
                return

            #self._check_and_register_ram(target)
            
            is_actual_call = (opcode == 0xCD) or (inst_type == "CALL_COND") # call
            if is_actual_call and target is not None:
                for reg in ["HL", "DE", "BC"]:
                    cache_key = (target, reg)
                    if cache_key not in self.subroutine_pointer_usage_cache:
                        self.subroutine_pointer_usage_cache[cache_key] = self._check_subroutine_use(target, reg)
                    
                    if self.subroutine_pointer_usage_cache[cache_key]:
                        reg_state = self.register_tracker[reg]
                        source_cmd_pc = reg_state['source_pc']
                        if source_cmd_pc is not None:
                            self.pointer_load_commands.add(source_cmd_pc)
                            self._check_and_register_ram(reg_state['val'])
            
            stack.append((target, {
                'regs': copy.deepcopy(self.register_tracker),
                'mem_loads': copy.deepcopy(self.memory_load_tracker)
            }))
            if opcode == 0xCD: # call
                stack.append((pc + 3, {
                    'regs': copy.deepcopy(self.register_tracker),
                    'mem_loads': copy.deepcopy(self.memory_load_tracker)
                }))
            
            if SCAN_SEQUENTIAL_JP and opcode == 0xC3:
                next_pc = pc + 3
                if next_pc < self.config.old_end:
                    if self.mem.get_byte(next_pc) == 0xC3:
                        stack.append((next_pc, {
                            'regs': copy.deepcopy(self.register_tracker),
                            'mem_loads': copy.deepcopy(self.memory_load_tracker)
                        }))

            if opcode == 0xC3:
                return
            return

        elif inst_type in ["JP_COND", "CALL_COND"]:
            self._check_and_register_ram(target)
            
            is_actual_call = (inst_type == "CALL_COND")
            if is_actual_call and target is not None:
                for reg in ["HL", "DE", "BC"]:
                    cache_key = (target, reg)
                    if cache_key not in self.subroutine_pointer_usage_cache:
                        self.subroutine_pointer_usage_cache[cache_key] = self._check_subroutine_use(target, reg)
                    
                    if self.subroutine_pointer_usage_cache[cache_key]:
                        reg_state = self.register_tracker[reg]
                        source_cmd_pc = reg_state['source_pc']
                        if source_cmd_pc is not None:
                            self.pointer_load_commands.add(source_cmd_pc)
                            self._check_and_register_ram(reg_state['val'])

            stack.append((target, {
                'regs': copy.deepcopy(self.register_tracker),
                'mem_loads': copy.deepcopy(self.memory_load_tracker)
            }))
            stack.append((pc + 3, {
                'regs': copy.deepcopy(self.register_tracker),
                'mem_loads': copy.deepcopy(self.memory_load_tracker)
            }))
            return

        elif inst_type in ["JR", "DJNZ"]:
            self._check_and_register_ram(target)
            stack.append((target, {
                'regs': copy.deepcopy(self.register_tracker),
                'mem_loads': copy.deepcopy(self.memory_load_tracker)
            }))
            if opcode == 0x18: # jr adr
                return
            stack.append((pc + 2, {
                'regs': copy.deepcopy(self.register_tracker),
                'mem_loads': copy.deepcopy(self.memory_load_tracker)
            }))
            return

        stack.append((pc + length, {
            'regs': copy.deepcopy(self.register_tracker),
            'mem_loads': copy.deepcopy(self.memory_load_tracker)
        }))

    def _track_memory_loads(self, pc, opcode, inst_type):
        """ワークエリアからレジスタへのポインタデータのロード処理を追跡する"""
        if opcode == 0x2A:  # ld hl, (nn)
            self.memory_load_tracker.pop('HL', None)
            target_work = self.mem.get_word(pc + 1)
            if self.config.old_start <= target_work < self.config.old_end:
                self.memory_load_tracker['HL'] = target_work
        elif opcode == 0xED:
            sub_op = self.mem.get_byte(pc + 1)
            target_work = self.mem.get_word(pc + 2)
            if self.config.old_start <= target_work < self.config.old_end:
                if sub_op == 0x4B:    # ld bc, (nn)
                    self.memory_load_tracker.pop('BC', None)
                    self.memory_load_tracker['BC'] = target_work
                elif sub_op == 0x5B:  # ld de, (nn)
                    self.memory_load_tracker.pop('DE', None)
                    self.memory_load_tracker['DE'] = target_work
        elif opcode in [0xDD, 0xFD]:
            sub_op = self.mem.get_byte(pc + 1)
            target_work = self.mem.get_word(pc + 2)
            reg = 'IX' if opcode == 0xDD else 'IY'
            if sub_op == 0x2A and self.config.old_start <= target_work < self.config.old_end:
                self.memory_load_tracker.pop(reg, None)
                self.memory_load_tracker[reg] = target_work

    def _track_writes(self, pc, opcode, inst_type):
        """自己書き換え（SMC）や割り込みフックのアドレス書き換えを含む、メモリへの出力パターンを検出する"""
        if inst_type == "LD_MEM" and opcode == 0x22:
            target = self.mem.get_word(pc + 1)
            self._check_and_register_ram(target)
            self._check_interrupt_hook_write(target, "HL", pc)
            self._check_pointer_work_write(target, "HL", pc)
            self._mark_memory_write(target, pc)

        elif inst_type == "ED_LD":
            sub_op = self.mem.get_byte(pc + 1)
            target = self.mem.get_word(pc + 2)
            self._check_and_register_ram(target)
            if sub_op == 0x43:
                self._check_interrupt_hook_write(target, "BC", pc)
                self._check_pointer_work_write(target, "BC", pc)
            elif sub_op == 0x53:
                self._check_interrupt_hook_write(target, "DE", pc)
                self._check_pointer_work_write(target, "DE", pc)
            if sub_op in [0x43, 0x53, 0x73]:
                self._mark_memory_write(target, pc)

        elif inst_type == "INDEX_LD":
            sub_op = self.mem.get_byte(pc + 1)
            if sub_op == 0x22:
                target = self.mem.get_word(pc + 2)
                self._check_and_register_ram(target)
                reg = "IX" if opcode == 0xDD else "IY"
                self._check_interrupt_hook_write(target, reg, pc)
                self._check_pointer_work_write(target, reg, pc)
                self._mark_memory_write(target, pc)

        elif opcode == 0x32:  # ld (nn), a
            target = self.mem.get_word(pc + 1)
            self._check_and_register_ram(target)
            self._check_split_accumulator_vector_write(target, pc)
            self._mark_memory_write(target, pc)

    def _check_pointer_work_write(self, target_work, reg_name, pc):
        """ポインタとして機能しているワークエリアへの書き込みを検知し、ロード元のデータアドレスを抽出する"""
        if self.simple_pass:
            return # simple_passモードでは処理しない
        if target_work in self.pointer_work_addresses:
            reg_state = self.register_tracker[reg_name]
            source_pc = reg_state['source_pc']
            if source_pc is not None:
                loaded_val = reg_state['val']
                if self.config.old_start <= loaded_val < self.config.old_end:
                    
                    log_key = (target_work, loaded_val, source_pc, pc) # ログ出力の重複防止
                    if log_key not in self.logged_pointer_writes:
                        self.logged_pointer_writes.add(log_key)
                        if self.db is not None:
                            self.db.register_address(loaded_val, source_pc, is_code=False)
                        self.pointer_load_commands.add(source_pc)
                        if self.logger is not None:
                            self.logger.log(
                                f"[+] 間接参照アドレス用WORKへの代入を検知: WORK: {format_hex(target_work)} "
                                f"<- 代入値: {format_hex(loaded_val)} "
                                f"(レジスタへのロード: {format_hex(source_pc)}, WORK書込: {format_hex(pc)})"
                            )

    def _mark_memory_write(self, target, pc):
        """メモリへのデータ書き込みイベントをマークする。CODE領域への書き込みはSMC（自己書き換え）として処理する"""

        self.mem.mark_attribute(target, 'WORK')
        self.mem.discard_attribute(target, 'DATA')

        # 書き込み先がCODE属性を持つなら、自己書き換え(SMC)とみなす
        is_smc_lane = False
        inst_start = target
        if self.mem.has_attribute(target, 'CODE'):
            is_smc_lane = True
            if target in self.db.byte_to_instruction_start:
                inst_start = self.db.byte_to_instruction_start[target]
        elif target in self.db.byte_to_instruction_start:
            inst_start = self.db.byte_to_instruction_start[target]
            if self.mem.has_attribute(inst_start, 'CODE'):
                is_smc_lane = True
                
        if is_smc_lane:
            if (pc, target) not in self.smc_detections:
                self.smc_detections.append((pc, target))
            
            # SMC検出時の処理。書き換え先ターゲットアドレスと、それが属する命令の開始アドレスの両方をシンボル登録する。
            if self.db is not None:
                self.db.register_address(target, pc, is_code=True, is_work=True)
                if target != inst_start:
                    self.db.register_address(inst_start, pc, is_code=True, is_work=False)

    def _analyse_bdos_call(self, pc):
        """BDOSコールの機能呼び出し番号（Cレジスタの値）を判別する"""
        text_c = self.register_tracker['C']
        fn_code = None
        if text_c is not None:
            cmd_pc = text_c['source_pc']
            opcode = self.mem.get_byte(cmd_pc)
            if opcode == 0x0E:  # ld c, n
                fn_code = self.mem.get_byte(cmd_pc + 1)
            elif opcode == 0x01:  # ld bc, nn
                fn_code = self.mem.get_byte(cmd_pc + 1)
        self.bdos_fn_map[pc] = fn_code

        if fn_code is not None:
            if fn_code in BDOS_REPLACE_ROUTINES:
                BDOS_REPLACE_ROUTINES[fn_code]["used"] = True
            else:
                self.unsupported_bdos_calls.append({'pc': pc, 'fn': fn_code})
                BDOS_REPLACE_ROUTINES["UNSUPPORTED"]["used"] = True

    def _check_interrupt_hook_write(self, target, reg_name, pc):
        """タイマー割り込みフック書き換えを検知する"""
        if self.simple_pass:
            return # simple_passモードでは処理しない
        if target in [0xFDA0, 0xFD9B]:
            reg_state = self.register_tracker[reg_name]
            handler_addr = reg_state['val']
            source_pc = reg_state['source_pc']
            if handler_addr > 0 and self.config.old_start <= handler_addr < self.config.old_end:
                hook_name = "T.TIMI" if target == 0xFDA0 else "H.KEYI"
                
                
                log_key = (target, handler_addr, source_pc, pc) # ログ出力の重複防止
                if log_key not in self.logged_interrupt_hook_writes:
                    self.logged_interrupt_hook_writes.add(log_key)
                    if self.db is not None:
                        self.db.register_address(handler_addr, source_pc, is_code=True)
                    if source_pc is not None:
                        self.pointer_load_commands.add(source_pc)
                    if self.logger is not None:
                        self.logger.log(
                            f"[+] 割り込みフックへの書き込み検出: {hook_name} (アドレス: {format_hex(target)}) "
                            f"ハンドラ先: {format_hex(handler_addr)} "
                            f"(制御命令PC: {format_hex(pc)}, 元ポインタロードPC: {format_hex(source_pc)})"
                        )

    def _check_split_accumulator_vector_write(self, target, pc):
        """Aレジスタを用いた8ビット単位の書き込みによる、割り込みフック書き換えをチェックする"""
        if target in [0xFDA0, 0xFDA1, 0xFD9B, 0xFD9C]:
            base_vector = 0xFDA0 if target in [0xFDA0, 0xFDA1] else 0xFD9B
            reg_state = self.register_tracker['HL']
            handler_addr = reg_state['val']
            source_pc = reg_state['source_pc']
            if handler_addr > 0 and self.config.old_start <= handler_addr < self.config.old_end:
                if self.db is not None:
                    self.db.register_address(handler_addr, source_pc, is_code=True)
                if source_pc is not None:
                    self.pointer_load_commands.add(source_pc)

    def _check_block_transfer_hook_write(self, pc):
        """LDIRなどの転送命令による割り込みフック書き換えをチェックする"""
        de_val = self.register_tracker['DE']['val']
        hl_val = self.register_tracker['HL']['val']
        if (0xFD9B <= de_val <= 0xFDA5) and (self.config.old_start <= hl_val < self.config.old_end):
            try:
                extracted_handler = self.mem.get_word(hl_val)
                if self.config.old_start <= extracted_handler < self.config.old_end:
                    if self.db is not None:
                        self.db.register_address(extracted_handler, pc, is_code=True)
            except IndexError:
                pass

    def _stack_reg_transfer_tracker(self, opcode, pc):
        """レジスタ操作やPOPによる状態変化に伴い、レジスタの追跡情報を初期化する"""
        if opcode in [0xE1, 0xE3]: # pop hl / ex (sp),hl
            self.register_tracker['HL']['source_pc'] = None
            self.register_tracker['H']['source_pc'] = None
            self.register_tracker['L']['source_pc'] = None
            self.memory_load_tracker.pop('HL', None)
        if opcode == 0xD1: # pop de
            self.register_tracker['DE']['source_pc'] = None
            self.register_tracker['D']['source_pc'] = None
            self.register_tracker['E']['source_pc'] = None
            self.memory_load_tracker.pop('DE', None)
        if opcode == 0xC1: # pop bc
            self.register_tracker['BC']['source_pc'] = None
            self.register_tracker['B']['source_pc'] = None
            self.register_tracker['C']['source_pc'] = None
            self.memory_load_tracker.pop('BC', None)
        if opcode == 0xF1: # pop af
            self.register_tracker['A']['source_pc'] = None
        
        if opcode == 0xDD:
            sub_op = self.mem.get_byte(pc + 1)
            if sub_op in [0xE1]: # pop ix
                self.register_tracker['IX']['source_pc'] = None
                self.register_tracker['IXH']['source_pc'] = None
                self.register_tracker['IXL']['source_pc'] = None
                self.memory_load_tracker.pop('IX', None)
        elif opcode == 0xFD:
            sub_op = self.mem.get_byte(pc + 1)
            if sub_op in [0xE1]: # pop iy
                self.register_tracker['IY']['source_pc'] = None
                self.register_tracker['IYH']['source_pc'] = None
                self.register_tracker['IYL']['source_pc'] = None
                self.memory_load_tracker.pop('IY', None)

    def _register_pointer_access(self, reg_name, pc):
        """間接アドレス参照の履歴から、アクセス対象となったアドレスにCODEまたはWORK属性を適用する"""
        reg_state = self.register_tracker[reg_name]
        ptr_val = reg_state['val']
        source_cmd_pc = reg_state['source_pc']
        
        # ロード元のアドレスがワークエリア（ワークエリア）であれば、そのアドレスをポインタワークエリアとして登録する
        if reg_name in self.memory_load_tracker:
            source_work = self.memory_load_tracker[reg_name]
            self.pointer_work_addresses.add(source_work)

        if ptr_val > 0 and source_cmd_pc is not None:
            self.pointer_load_commands.add(source_cmd_pc)
            self._check_and_register_ram(ptr_val)
            if self.mem.has_attribute(ptr_val, 'CODE'):
                self.mem.mark_attribute(ptr_val, 'DATA')
            else:
                self.mem.mark_attribute(ptr_val, 'WORK' if reg_name in ["DE", "BC"] else 'DATA')

    def _check_and_register_ram(self, addr):
        if addr < SYSYTEM_WORK:
            if addr > self.max_existing_ram:
                self.max_existing_ram = addr

    def _group_sections(self):
        """解析により判明した各メモリアドレスの属性情報を、連続するセクションごとにまとめる"""
        self.sections.clear()
        current_type = None
        start_addr = self.config.old_start
        for addr in range(self.config.old_start, self.config.old_end):
            if self.mem.has_attribute(addr, 'WORK') or self.mem.has_attribute(addr, 'MERGE'):
                addr_type = 'WORK'
            elif self.mem.has_attribute(addr, 'CODE'):
                addr_type = 'CODE'
            else:
                addr_type = 'DATA'
            if current_type is None:
                current_type = addr_type
                start_addr = addr
            elif current_type != addr_type:
                self.sections.append(SectionRange(start_addr, addr - 1, current_type))
                current_type = addr_type
                start_addr = addr
        self.sections.append(SectionRange(start_addr, self.config.old_end - 1, current_type))


class Z80SmartRelocator:
    """逆アセンブル前に命令を一巡走査して、必要なすべての参照先ラベルを仮登録するクラス"""
    def __init__(self, config: Z80Config, mem: Z80MemoryImage, db: Z80AddressRegistry, analyser: Z80FlowAnalyser):
        self.config = config
        self.mem = mem
        self.db = db
        self.analyser = analyser

    def get_context_is_bios(self, pc, addr, default_val=None):
        """アドレスの属性情報からシステムBIOS/システムワークエリアに属するかを調べる"""
        if default_val is None:
            # 元バイナリデータの外側を指しているアドレスはリロケーション対象外とする
            default_val = (addr < self.mem.config.old_start or addr >= self.mem.config.old_end)
        record = self.db.records.get((addr, True))
        if record is not None and record.references is not None:
            if pc in record.references:
                return record.is_bios
        return default_val

    def collect_symbols(self):
        """バイナリ内の全命令をデコードして参照先アドレスを検出し、仮シンボルリストに追加する"""
        addr = self.config.old_start
        classifier = Z80OpcodeClassifier(self.mem, self.db)
        
        while addr < self.config.old_end:
            if not self.mem.has_attribute(addr, 'CODE'):
                addr += 1
                continue
            
            length, target, inst_type = classifier.decode_instruction(addr)
            
            is_pointer_loader = addr in self.analyser.pointer_load_commands
            is_jp_or_call = inst_type.startswith("jp") or inst_type.startswith("call")
            is_target_bios = False
            if target is not None:
                is_target_bios = self.get_context_is_bios(addr, target)
            
            if is_jp_or_call or inst_type in ["JP_COND", "CALL_COND", "JR", "DJNZ"]:

                self.db.unresolved_records.add((target, is_target_bios))
            elif inst_type in ["LD_MEM", "ED_LD", "INDEX_CB"]:
                self.db.unresolved_records.add((target, is_target_bios))
            elif inst_type == "LD_REG16" and is_pointer_loader:
                self.db.unresolved_records.add((target, is_target_bios))
            elif inst_type == "INDEX_LD" and is_pointer_loader:
                self.db.unresolved_records.add((target, is_target_bios))
                
            addr += length


class Z80Disassembler:
    """Z80の機械語データを、対応するアセンブリ言語のテキスト表現に変換するデコーダクラス"""
    def __init__(self, mem: Z80MemoryImage, db: Z80AddressRegistry, analyser: Z80FlowAnalyser, logger: Z80Logger):
        self.mem = mem
        self.db = db
        self.analyser = analyser
        self.logger = logger
        self.classifier = Z80OpcodeClassifier(self.mem, self.db)
        
        # 3ビットのレジスタ選択コード(000b〜111b)に対応するZ80標準8ビットレジスタ名の定義マッピング
        # インデックスフィールド d_str が指定された場合はインデックスレジスタ(IX/IY)間接アドレッシングとなる。
        self.Z80_REG_MAP_8BIT = ["b", "c", "d", "e", "h", "l", "(hl)", "a"]
        
        # 機械語における3ビット演算コード（ビット5-3）に対応する、Z80標準算術論理演算命令ニーモニック定義
        self.Z80_ALU_OPS_8BIT = ["add a,", "adc a,", "sub", "sbc a,", "and", "xor", "or", "cp"]

    def get_reg_8bit(self, reg_code, prefix_reg=None, d_str=""):
        """3ビットのレジスタコード値に基づき、適切なアセンブラオペランド文字列にデコードする。

        IX/IYプレフィックスが存在する場合の間接指定、および非公式命令における高位・低位部分レジスタ
        （IXH/IXL, IYH/IYL）へのマッピングを処理する。
        """
        # レジスタコード 110b = (HL) を指す基本アドレッシングコードのデコード
        if reg_code == 6:
            # プレフィックス(IXまたはIY)が存在する場合は、(ix+d) や (iy+d) のインデックス間接参照に差し替える
            if prefix_reg is not None:
                return f"({prefix_reg.lower()}{d_str})"
            return "(hl)"
        
        # プレフィックス(IX/IY)指定下において、基本レジスタH(100b)またはL(101b)が指定されている場合の変形ルール
        # この場合は(HL)へのアクセスではなく、IX/IYのバイト分離レジスタ（IXH, IXL, IYH, IYL）を操作する未ドキュメント命令を処理する。
        if prefix_reg is not None:
            if reg_code == 4:   # Hレジスタフィールド -> IXH / IYH に差し替え
                return f"{prefix_reg.lower()}h"
            elif reg_code == 5: # Lレジスタフィールド -> IXL / IYL に差し替え
                return f"{prefix_reg.lower()}l"
                
        return self.Z80_REG_MAP_8BIT[reg_code]

    def get_context_is_bios(self, pc, addr, default_val=None):
        """アドレスの属性情報からシステムBIOS/システムワークエリアに属するかを判定する"""
        if default_val is None:
            default_val = (addr < self.mem.config.old_start or SYSYTEM_WORK <= addr)
        record = self.db.records.get((addr, True))
        if record is not None and record.references is not None:
            if pc in record.references:
                return record.is_bios
        return default_val

    def decode_inst(self, pc, bdos_fn_map):
        """指定アドレスのデータをデコードしてアセンブリ言語テキストを生成する。"""
        assert(bdos_fn_map is not None)
        # 逆アセンブルの同期ずれを防ぐため、コードパッチでの置き換え時でも
        # 「bytes_len」としては常に元の機械語のバイトサイズ（3等）を返す。
        opcode = self.mem.get_byte(pc)
        
        # === SMC (Self-Modifying Code) に対するパッチ処理 ===
        if USE_SMC_PATCH and not COPY_CODE_TO_RAM and self.analyser is not None and (
            opcode == 0x32  # ld (nn), a 命令
            and (pc + 3) in self.analyser.smc_patch_jr_addresses # jr n
        ):
            target = self.mem.get_word(pc + 1)
            target_label = self.db.get_label(
                target, 
                format_asm_hex(self.relocator_translate(target, is_code=True, is_bios=False)), 
                is_code=True, 
                is_bios=False
            )
            patch_code = smc_patch_jr_code_ld.replace("dest_label", target_label)
            # 元バイナリでの次のアドレスを算出するために使用するので元のバイト数を返す
            return 3, patch_code
        
        if USE_SMC_PATCH and not COPY_CODE_TO_RAM and self.analyser is not None and (
            pc in self.analyser.smc_patch_jr_addresses # jr n
        ):
            # 自己書き換えコード(SMC)へのパッチ
            # JRのジャンプ先書き換え処理を、JP (HL)を使用する処理に変更する
            target = self.mem.get_word(pc - 2)
            jr_addr = pc
            dest_addr = pc + 2
            dest_label = self.db.get_label(
                dest_addr, 
                format_asm_hex(self.relocator_translate(dest_addr, is_code=True, is_bios=False)), 
                is_code=True, 
                is_bios=False
            )
            patch_code = smc_patch_jr_code_jr.replace("dest_label", dest_label)
            self.logger.log(f"[+] 自己書き換えJR命令にパッチを適用: PC: {format_hex(self.relocator_translate(pc, is_code=True))} (オリジナル: {format_hex(pc)}) ( JR命令 PC: {format_hex(self.relocator_translate(jr_addr, is_code=True))} (オリジナル: {format_hex(jr_addr)}) )")
            # 元バイナリでの次のアドレスを算出するために使用するので元のバイト数を返す
            return 2, patch_code
        # ======================================================

        if opcode == 0xCD:
            # BDOSコールの置き換え処理（共通互換サブルーチンの呼び出しへ置換）
            target = self.mem.get_word(pc + 1)
            if target == BDOS_CALL_ADDRESS and pc in bdos_fn_map:
                fn = bdos_fn_map[pc]
                if fn is not None and fn in BDOS_REPLACE_ROUTINES:
                    sub_label = BDOS_REPLACE_ROUTINES[fn]["label"]
                else:
                    sub_label = BDOS_REPLACE_ROUTINES["UNSUPPORTED"]["label"]
                return 3, f"call {sub_label}"

        length, target, inst_type = self.classifier.decode_instruction(pc)
        is_pointer_loader = pc in self.analyser.pointer_load_commands
        is_target_bios = False
        if target is not None:
            is_target_bios = self.get_context_is_bios(pc, target)

        is_jp_or_call = inst_type.startswith("jp") or inst_type.startswith("call")
        if is_jp_or_call:
            label = self.db.get_label(target, format_asm_hex(self.relocator_translate(target, is_code=True, is_bios=is_target_bios)), is_code=True, is_bios=is_target_bios)
            inst = "jp" if opcode == 0xC3 else "call"
            return 3, f"{inst} {label}"

        if inst_type == "JP_COND":
            label = self.db.get_label(target, format_asm_hex(self.relocator_translate(target, is_code=True, is_bios=is_target_bios)), is_code=True, is_bios=is_target_bios)
            jp_conds = {0xC2: "nz", 0xCA: "z", 0xD2: "nc", 0xDA: "c", 0xE2: "po", 0xEA: "pe", 0xF2: "p", 0xFA: "m"}
            return 3, f"jp {jp_conds[opcode]}, {label}"

        if inst_type == "CALL_COND":
            label = self.db.get_label(target, format_asm_hex(self.relocator_translate(target, is_code=True, is_bios=is_target_bios)), is_code=True, is_bios=is_target_bios)
            call_conds = {0xC4: "nz", 0xCC: "z", 0xD4: "nc", 0xDC: "c", 0xE4: "po", 0xEC: "pe", 0xF4: "p", 0xFC: "m"}
            return 3, f"call {call_conds[opcode]}, {label}"

        if inst_type == "JR":
            offset = self.mem.get_byte(pc+1)
            if offset & 0x80: offset -= 256
            dest_addr = pc + 2 + offset
            is_dest_bios = self.get_context_is_bios(pc, dest_addr)
            label = self.db.get_label(dest_addr, format_asm_hex(self.relocator_translate(dest_addr, is_code=True, is_bios=is_dest_bios)), is_code=True, is_bios=is_dest_bios)
            jr_names = {0x18: "jr", 0x20: "jr nz,", 0x28: "jr z,", 0x30: "jr nc,", 0x38: "jr c,"}
            return 2, f"{jr_names[opcode]} {label}"

        if inst_type == "DJNZ":
            offset = self.mem.get_byte(pc+1)
            if offset & 0x80: offset -= 256
            dest_addr = pc + 2 + offset
            is_dest_bios = self.get_context_is_bios(pc, dest_addr)
            label = self.db.get_label(dest_addr, format_asm_hex(self.relocator_translate(dest_addr, is_code=True, is_bios=is_dest_bios)), is_code=True, is_bios=is_dest_bios)
            return 2, f"djnz {label}"

        if inst_type == "LD_MEM":
            label = self.db.get_label(target, format_asm_hex(self.relocator_translate(target, is_code=is_target_bios, is_bios=is_target_bios)), is_code=is_target_bios, is_bios=is_target_bios)
            if opcode == 0x32: return 3, f"ld ({label}), a"
            if opcode == 0x3A: return 3, f"ld a, ({label})"
            if opcode == 0x22: return 3, f"ld ({label}), hl"
            if opcode == 0x2A: return 3, f"ld hl, ({label})"

        if inst_type == "LD_REG16":
            reg = {0x01: "bc", 0x11: "de", 0x21: "hl", 0x31: "sp"}[opcode]
            if is_pointer_loader:
                label = self.db.get_label(target, format_asm_hex(target), is_code=is_target_bios, is_bios=is_target_bios)
                return 3, f"ld {reg}, {label}"
            return 3, f"ld {reg}, {format_asm_hex(target)}"

        if inst_type == "ED_LD":
            sub_op = self.mem.get_byte(pc + 1)
            label = self.db.get_label(target, format_asm_hex(target), is_code=is_target_bios, is_bios=is_target_bios)
            if sub_op in [0x43, 0x53, 0x73]:
                reg = {0x43: "bc", 0x53: "de", 0x73: "sp"}[sub_op]
                return 4, f"ld ({label}), {reg}"
            reg = {0x4B: "bc", 0x5B: "de", 0x7B: "sp"}[sub_op]
            return 4, f"ld {reg}, ({label})"

        if inst_type == "INDEX_LD":
            sub_op = self.mem.get_byte(pc + 1)
            reg = "ix" if opcode == 0xDD else "iy"
            if sub_op == 0x21:
                if is_pointer_loader:
                    label = self.db.get_label(target, format_asm_hex(target), is_code=is_target_bios, is_bios=is_target_bios)
                    return 4, f"ld {reg}, {label}"
                return 4, f"ld {reg}, {format_asm_hex(target)}"
            label = self.db.get_label(target, format_asm_hex(target), is_code=is_target_bios, is_bios=is_target_bios)
            if sub_op == 0x22:
                return 4, f"ld ({label}), {reg}"
            return 4, f"ld {reg}, ({label})"

        if inst_type == "INDEX_CB":
            prefix_reg = "ix" if opcode == 0xDD else "iy"
            d = self.mem.get_byte(pc + 2)
            sub_op = self.mem.get_byte(pc + 3)
            d_str = f"+0{d:02X}H" if d < 128 else f"-0{256-d:02X}H"
            
            reg = self.get_reg_8bit(6, prefix_reg, d_str)
            bit = (sub_op >> 3) & 7
            
            cb_inst = ""
            if 0x00 <= sub_op <= 0x07: cb_inst = f"rlc {reg}"
            elif 0x08 <= sub_op <= 0x0F: cb_inst = f"rrc {reg}"
            elif 0x10 <= sub_op <= 0x17: cb_inst = f"rl {reg}"
            elif 0x18 <= sub_op <= 0x1F: cb_inst = f"rr {reg}"
            elif 0x20 <= sub_op <= 0x27: cb_inst = f"sla {reg}"
            elif 0x28 <= sub_op <= 0x2F: cb_inst = f"sra {reg}"
            elif 0x30 <= sub_op <= 0x37: cb_inst = f"sll {reg}"
            elif 0x38 <= sub_op <= 0x3F: cb_inst = f"srl {reg}"
            elif 0x40 <= sub_op <= 0x7F: cb_inst = f"bit {bit}, {reg}"
            elif 0x80 <= sub_op <= 0xBF: cb_inst = f"res {bit}, {reg}"
            elif 0xC0 <= sub_op <= 0xFF: cb_inst = f"set {bit}, {reg}"
            
            return 4, cb_inst

        if inst_type == "2BYTE":
            n_val = self.mem.get_byte(pc + 1)
            if opcode in self.classifier.op_map_2byte:
                return 2, self.classifier.op_map_2byte[opcode].format(n=format_asm_hex(n_val, 2))
            elif opcode == 0xD3:
                return 2, f"out ({format_asm_hex(n_val, 2)}), a"
            elif opcode == 0xDB:
                return 2, f"in a, ({format_asm_hex(n_val, 2)})"
            return 2, f"db {format_asm_hex(opcode, 2)}, {format_asm_hex(n_val, 2)}"

        if inst_type == "RST_30":
            slot_id = self.mem.get_byte(pc + 1)
            addr_val = self.mem.get_word(pc + 2)
            label = self.db.get_label(addr_val, format_asm_hex(addr_val), is_code=True, is_bios=is_target_bios)
            return 4, f"rst 30H\n    db {format_asm_hex(slot_id, 2)}\n    dw {label}"

        if inst_type == "1BYTE":
            return self._fallback_dissolve(pc, 1)

        if inst_type == "ED_OTHER":
            return self._decode_ed(pc)

        if inst_type in ["INDEX_OTHER", "INDEX_LD_DISP", "INDEX_WRITE_VAL"]:
            return self._decode_index(pc, "ix" if opcode == 0xDD else "iy")

        if inst_type == "CB":
            return self._decode_cb(pc)

        return self._fallback_dissolve(pc, length)

    def relocator_translate(self, addr, is_code=False, is_bios=False):
        return self.db.translate_address(addr, is_code=is_code, is_bios=is_bios)

    def _fallback_dissolve(self, pc, length):
        """標準テーブルから漏れた Z80 1バイト命令をビットフィールド等の基本ルールに基づき切り分ける"""
        if length == 1:
            opcode = self.mem.get_byte(pc)
            one_byte_ops = {
                0x00: "nop", 0x07: "rlca", 0x0F: "rrca", 0x17: "rla", 0x1F: "rra", 0x27: "daa", 0x2F: "cpl", 
                0x37: "scf", 0x3F: "ccf", 0x76: "halt", 0xC9: "ret", 0xD9: "exx", 0xE3: "ex (sp), hl", 
                0xEB: "ex de, hl", 0xF3: "di", 0xFB: "ei", 0xF9: "ld sp, hl", 0x09: "add hl, bc", 
                0x19: "add hl, de", 0x29: "add hl, hl", 0x39: "add hl, sp", 0x08: "ex af, af'",
                0x02: "ld (bc), a", 0x0A: "ld a, (bc)", 0x12: "ld (de), a", 0x1A: "ld a, (de)"
            }
            if opcode in one_byte_ops:
                return 1, one_byte_ops[opcode]
            
            regs_16 = {0xC5: "bc", 0xD5: "de", 0xE5: "hl", 0xF5: "af"}
            if opcode in regs_16: return 1, f"push {regs_16[opcode]}"
            regs_16_p = {0xC1: "bc", 0xD1: "de", 0xE1: "hl", 0xF1: "af"}
            if opcode in regs_16_p: return 1, f"pop {regs_16_p[opcode]}"

            inc_dec_r = {
                0x04: "inc b", 0x0C: "inc c", 0x14: "inc d", 0x1C: "inc e", 0x24: "inc h", 0x2C: "inc l", 0x3C: "inc a",
                0x05: "dec b", 0x0D: "dec c", 0x15: "dec d", 0x1D: "dec e", 0x25: "dec h", 0x2D: "dec l", 0x3D: "dec a",
                0x03: "inc bc", 0x13: "inc de", 0x23: "inc hl", 0x33: "inc sp",
                0x0B: "dec bc", 0x1B: "dec de", 0x2B: "dec hl", 0x3B: "dec sp"
            }
            if opcode in inc_dec_r: return 1, inc_dec_r[opcode]

            ret_conds = {0xC0: "nz", 0xC8: "z", 0xD0: "nc", 0xD8: "c", 0xE0: "po", 0xE8: "pe", 0xF0: "p", 0xF8: "m"}
            if opcode in ret_conds:
                return 1, f"ret {ret_conds[opcode]}"

            if opcode in [0xC7, 0xCF, 0xD7, 0xDF, 0xE7, 0xEF, 0xFF]:
                rst_addr = opcode & 0x38
                return 1, f"rst {format_asm_hex(rst_addr, 2)}"

            # 8ビットレジスタ間転送命令 (LD r, r') のデコード
            # 機械語のビット配置 01xxxYYYH (40H〜7FH) で表現され、xxx=転送先、YYY=転送元となる
            if 0x40 <= opcode <= 0x7F and opcode != 0x76:
                dest = self.get_reg_8bit((opcode >> 3) & 7)
                src = self.get_reg_8bit(opcode & 7)
                return 1, f"ld {dest}, {src}"
                
            # 8ビットレジスタ・メモリ間算術論理演算命令 (ADD/ADC/SUB/SBC/AND/XOR/OR/CP) のデコード
            # 機械語のビット配置 10xxxYYY H (80H〜BFH) で表現され、xxx=演算機能コード、YYY=対象レジスタとなる
            if 0x80 <= opcode <= 0xBF:
                src = self.get_reg_8bit((opcode & 7))
                alu_op = self.Z80_ALU_OPS_8BIT[(opcode >> 3) & 7]
                return 1, f"{alu_op} {src}"

        tokens = []
        for i in range(length):
            tokens.append(format_asm_hex(self.mem.get_byte(pc + i), 2))
        return length, f"db {', '.join(tokens)}"

    def _decode_ed(self, pc):
        """EDプレフィックスに続く拡張命令の判定処理"""
        sub_op = self.mem.get_byte(pc + 1)
        
        # rp（レジスタペア）とアドレス間における各種ロード命令のデコード
        if sub_op in [0x43, 0x53, 0x73, 0x4B, 0x5B, 0x7B]:
            val = self.mem.get_word(pc + 2)
            is_target_bios = self.get_context_is_bios(pc, val)
            reg = {0x43: "bc", 0x53: "de", 0x73: "sp"}[sub_op]
            label = self.db.get_label(val, format_asm_hex(val), is_code=is_target_bios, is_bios=is_target_bios)
            if sub_op in [0x43, 0x53, 0x73]:
                return 4, f"ld ({label}), {reg}"
            return 4, f"ld {reg}, ({label})"

        # ポート入力 IN r, (C) および ポート出力 OUT (C), r 命令のデコード
        # 機械語配置 01xxx000B(IN) および 01xxx001B(OUT) にマッピングされている
        if 0x40 <= sub_op <= 0x7F:
            reg_code = (sub_op >> 3) & 7
            reg_name = ["b", "c", "d", "e", "h", "l", "(c)", "a"][reg_code]
            
            if (sub_op & 7) == 0:  # IN r, (C)
                if reg_code == 6:  # レジスタコード 110b は非公式なフラグ変化のみ行う IN (C) 命令
                    return 2, "in (c)"
                return 2, f"in {reg_name}, (c)"
                
            elif (sub_op & 7) == 1:  # OUT (C), r
                if reg_code == 6:  # レジスタコード 110b はポート(C)に0を出力する非公式命令
                    return 2, "out (c), 0"
                return 2, f"out (c), {reg_name}"

        # 拡張ブロック転送（LDI/LDIR等）、ブロック比較、符号反転、割り込みモード設定、16ビット加減算の処理
        ed_insts = {
            0x79: "out (c), a", 0x78: "in a, (c)",
            0xA0: "ldi", 0xA1: "cpi", 0xA2: "ini", 0xA3: "outi",
            0xB0: "ldir", 0xB1: "cpir", 0xB2: "inir", 0xB3: "otir",
            0xA8: "ldd", 0xA9: "cpd", 0xAA: "ind", 0xAB: "outd",
            0xBB: "otdr", 0x44: "neg", 
            0x45: "retn", 0x55: "retn", 0x65: "retn", 0x75: "retn",
            0x4D: "reti", 0x5D: "reti", 0x6D: "reti", 0x7D: "reti",
            0x46: "im 0", 0x56: "im 1", 0x5E: "im 2",
            0x42: "sbc hl, bc", 0x52: "sbc hl, de", 0x62: "sbc hl, hl", 0x72: "sbc hl, sp",
            0x4A: "adc hl, bc", 0x5A: "adc hl, de", 0x6A: "adc hl, hl", 0x7A: "adc hl, sp"
        }
        if sub_op in ed_insts:
            return 2, ed_insts[sub_op]
        return 2, f"db 0EDH, {format_asm_hex(sub_op, 2)}"

    def _decode_cb(self, pc):
        """CBプレフィックスに続くビット操作・シフト命令のデコード。

        機械語バイト構成は、ビット7-6で処理大別（00b=シフト/ローテート, 01b=BIT, 10b=RES, 11b=SET）を行い、
        ビット5-3で対象ビット位置(0〜7)または処理タイプ、下位3ビットでレジスタフィールド(000b〜111b)を定義する。
        """
        sub_op = self.mem.get_byte(pc + 1)
        reg = self.get_reg_8bit(sub_op & 7)
        bit = (sub_op >> 3) & 7
        
        cb_inst = ""
        if 0x00 <= sub_op <= 0x07: cb_inst = f"rlc {reg}"   # キャリー付き左ローテート
        elif 0x08 <= sub_op <= 0x0F: cb_inst = f"rrc {reg}" # キャリー付き右ローテート
        elif 0x10 <= sub_op <= 0x17: cb_inst = f"rl {reg}"  # 9ビット左ローテート
        elif 0x18 <= sub_op <= 0x1F: cb_inst = f"rr {reg}"  # 9ビット右ローテート
        elif 0x20 <= sub_op <= 0x27: cb_inst = f"sla {reg}" # 算術左シフト
        elif 0x28 <= sub_op <= 0x2F: cb_inst = f"sra {reg}" # 算術右シフト
        elif 0x30 <= sub_op <= 0x37: cb_inst = f"sll {reg}" # 論理左シフト（非公式：最下位ビットに常に1が立つ）
        elif 0x38 <= sub_op <= 0x3F: cb_inst = f"srl {reg}" # 論理右シフト
        elif 0x40 <= sub_op <= 0x7F: cb_inst = f"bit {bit}, {reg}" # 対象ビット状態テスト
        elif 0x80 <= sub_op <= 0xBF: cb_inst = f"res {bit}, {reg}" # 対象ビットリセット
        elif 0xC0 <= sub_op <= 0xFF: cb_inst = f"set {bit}, {reg}" # 対象ビットセット
        
        return 2, cb_inst

    def _decode_index(self, pc, reg_name):
        """DD/FDプレフィックスを伴うインデックスアドレス命令のデコード。"""
        reg = reg_name.lower()
        op = self.mem.get_byte(pc + 1)
        
        is_pointer_loader = pc in self.analyser.pointer_load_commands
        
        # 16ビット即値ロード (LD IX/IY, nn) のデコード
        if op == 0x21:  
            val = self.mem.get_word(pc + 2)
            is_target_bios = self.get_context_is_bios(pc, val)
            if is_pointer_loader:
                label = self.db.get_label(val, format_asm_hex(val), is_code=is_target_bios, is_bios=is_target_bios)
                return 4, f"ld {reg}, {label}"
            return 4, f"ld {reg}, {format_asm_hex(val)}"
            
        # 16ビットストア (LD (nn), IX/IY) のデコード
        if op == 0x22:  
            val = self.mem.get_word(pc + 2)
            is_target_bios = self.get_context_is_bios(pc, val)
            label = self.db.get_label(val, format_asm_hex(val), is_code=is_target_bios, is_bios=is_target_bios)
            return 4, f"ld ({label}), {reg}"
            
        # 16ビットロード (LD IX/IY, (nn)) のデコード
        if op == 0x2A:  
            val = self.mem.get_word(pc + 2)
            is_target_bios = self.get_context_is_bios(pc, val)
            label = self.db.get_label(val, format_asm_hex(val), is_code=is_target_bios, is_bios=is_target_bios)
            return 4, f"ld {reg}, ({label})"

        # インデックス対加算命令 (ADD IX/IY, rp) のデコード
        if op in [0x09, 0x19, 0x29, 0x39]:
            r_pair = {0x09: "bc", 0x19: "de", 0x29: reg, 0x39: "sp"}[op]
            return 2, f"add {reg}, {r_pair}"

        # (IX+d) / (IY+d) のアドレッシング構成パターンを抽出
        is_indirect_hl = ((op >> 3) & 7) == 6 or (op & 7) == 6

        # ディスプレースメントを伴うインデックス相対アドレッシング命令
        if op in [0x34, 0x35, 0x36] or is_indirect_hl:  
            d = self.mem.get_byte(pc + 2)
            # ディスプレースメントバイトを16進の符号付き相対オフセットとしてアセンブラ書式化
            d_str = "+00H" if d == 0 else (f"+0{d:02X}H" if d < 128 else f"-0{256-d:02X}H")
            target_reg = self.get_reg_8bit(6, reg, d_str)
            if op == 0x34: return 3, f"inc {target_reg}"
            if op == 0x35: return 3, f"dec {target_reg}"
            if op == 0x36: return 4, f"ld {target_reg}, {format_asm_hex(self.mem.get_byte(pc + 3), 2)}"

            # LD r, (IX/IY+d) 形式のロード命令のデコード
            if 0x40 <= op <= 0x7F and op != 0x76:
                dest = self.get_reg_8bit((op >> 3) & 7, reg, d_str)
                src = self.get_reg_8bit(op & 7, reg, d_str)
                return 3, f"ld {dest}, {src}"
            # ALUs s, (IX/IY+d) 形式のインデックス相対算術演算命令
            if 0x80 <= op <= 0xBF:
                src = self.get_reg_8bit(op & 7, reg, d_str)
                alu_op = self.Z80_ALU_OPS_8BIT[(op >> 3) & 7]
                return 3, f"{alu_op} {src}"

        # プレフィックス付きながらディスプレースメント無しの命令（非公式なIXH/IXL演算等）の解析
        length = 1 + get_standard_len(op)

        if 0x40 <= op <= 0x7F and op != 0x76:
            dest = self.get_reg_8bit((op >> 3) & 7, reg)
            src = self.get_reg_8bit(op & 7, reg)
            return length, f"ld {dest}, {src}"

        if op in [0x24, 0x25, 0x2C, 0x2D, 0x3C]:
            dest = self.get_reg_8bit(op & 7, reg)
            inst = "inc" if op in [0x24, 0x2C, 0x3C] else "dec"
            return length, f"{inst} {dest}"

        if op in [0x06, 0x0E, 0x16, 0x1E, 0x26, 0x2E, 0x3E]:
            dest = self.get_reg_8bit((op >> 3) & 7, reg)
            n_val = self.mem.get_byte(pc + 2)
            return length, f"ld {dest}, {format_asm_hex(n_val, 2)}"

        # プレフィックスに続くIXH/IXLを用いたディスプレースメントなしの非公式算術演算命令のサポート
        if 0x80 <= op <= 0xBF:
            src = self.get_reg_8bit(op & 7, reg)
            alu_op = self.Z80_ALU_OPS_8BIT[(op >> 3) & 7]
            return length, f"{alu_op} {src}"

        tokens = []
        for i in range(length):
            tokens.append(format_asm_hex(self.mem.get_byte(pc + i), 2))
        return length, f"db {', '.join(tokens)}"


class TransferBlock:
    """初期化用にROMからRAMに一括転送するデータの情報を保持する構造体"""
    def __init__(self, src_label, dest_label, size_val):
        self.src_label = src_label
        self.dest_label = dest_label
        self.size_val = size_val


class Z80OutputGenerator:
    """結果のアセンブリファイルを書き出す出力生成クラス"""
    def __init__(self, config: Z80Config, mem: Z80MemoryImage, db: Z80AddressRegistry, analyser: Z80FlowAnalyser, decoder: Z80Disassembler, logger: Z80Logger):
        self.config = config
        self.mem = mem
        self.db = db
        self.decoder = decoder
        self.logger = logger
        self.analyser = analyser

    def write_assembly_file(self):
        self.logger.log(f"[*] アセンブリコードをASMファイル '{self.config.output_asm}' へ出力中...")
        
        transfer_blocks = []
        
        # WORK/MERGEブロックの初期値を転送登録
        in_block = False
        start_addr = None
        for pc in range(self.config.old_start, self.config.old_end):
            is_target = ((self.mem.has_attribute(pc, 'WORK') or self.mem.has_attribute(pc, 'MERGE'))
                         and not self.mem.has_attribute(pc, 'CODE'))
            if is_target:
                if not in_block:
                    in_block = True
                    start_addr = pc
            else:
                if in_block:
                    size = pc - start_addr
                    dest_lbl = self.db.labels.get((start_addr, False), f"WORK_{start_addr:04X}H")
                    src_lbl = f"INIT_WORK_{start_addr:04X}H" if self.mem.has_attribute(start_addr, 'WORK') else f"INIT_DATA_{start_addr:04X}H"
                    transfer_blocks.append(TransferBlock(src_lbl, dest_lbl, size))
                    in_block = False
        if in_block:
            size = self.config.old_end - start_addr
            dest_lbl = self.db.labels.get((start_addr, False), f"WORK_{start_addr:04X}H")
            src_lbl = f"INIT_WORK_{start_addr:04X}H" if self.mem.has_attribute(start_addr, 'WORK') else f"INIT_DATA_{start_addr:04X}H"
            transfer_blocks.append(TransferBlock(src_lbl, dest_lbl, size))

        if COPY_CODE_TO_RAM:
            transfer_blocks.insert(0, TransferBlock(
                src_label="ROM_CODE_DATA_START",
                dest_label="RAM_BASE",
                size_val=self.db.total_code_size
            ))

        with open(self.config.output_asm, 'w') as out:
            out.write(";===================================================================\n")
            out.write(f"; COM\"{INPUT_PATH}\" to ROM\"{OUTPUT_ASM_PATH}\" 自動リロケート\n")
            out.write(";===================================================================\n\n")

            # EQU定義の出力
            out.write(";=== SYSTEM PARAMETERS ===\n")
            out.write(f"ROM_BASE            EQU {format_asm_hex(self.config.rom_start)}\n")
            out.write(f"RAM_BASE            EQU {format_asm_hex(self.config.ram_start)}\n\n")

            # 外部シンボルの定義を一括出力
            all_external_addrs = []
            # BIOS/BDOS/SYSTEM WORK
            for (addr, is_bios), label_name in self.db.labels.items():
                if addr < self.config.old_start or is_bios:
                    all_external_addrs.append((addr, is_bios, label_name))

            for ext_addr, is_bios, label_name in sorted(all_external_addrs, key=lambda x: (x[0], x[1])):
                out.write(f"{label_name:18} EQU {format_asm_hex(ext_addr)}\n")
            out.write("\n")

            # RAM上のラベル
            internal_data_addrs = []
            for (addr, is_bios), label_name in self.db.labels.items():
                record : Z80AddressRecord = self.db.records[(addr, is_bios)]
                if not record.is_code and not is_bios:
                    is_work = self.mem.has_attribute(addr, 'WORK')
                    is_merged = self.mem.has_attribute(addr, 'MERGE')
                    if is_work or is_merged:
                        internal_data_addrs.append((addr, is_bios, label_name))

            for addr, is_bios, label_name in sorted(internal_data_addrs, key=lambda x: (x[0], x[1])):
                new_ram_addr = self.db.translate_address(addr, is_code=False, is_bios=is_bios)
                out.write(f"{label_name:18} EQU {format_asm_hex(new_ram_addr)}\n")
            out.write("\n")

            if COPY_CODE_TO_RAM:
                out.write("EXEC_ADDRESS       EQU RAM_BASE             ; RAM上の開始アドレス\n\n")
            else:
                entry_target = self.config.old_start
                entry_label = self.db.get_label(entry_target, f"CODE_{entry_target:04X}H", is_code=True, is_bios=False)
                out.write(f"EXEC_ADDRESS       EQU {entry_label}    ; オリジナル版の開始アドレス\n\n")

            out.write("    ORG ROM_BASE\n")
            
            out.write(ROM_HEADER)
           
            out.write(ENTRY_CODE)

            out.write(";===================================================================\n")
            out.write("; APPRICATION SECTION \n")
            out.write(";===================================================================\n")
            
            if COPY_CODE_TO_RAM:
                out.write("ROM_CODE_DATA_START:\n")
                if ASSEMBLER_TYPE == 1:
                    out.write("    .phase RAM_BASE\n\n")
                else:
                    out.write("    ORG  RAM_BASE, STARTUP_END - ROM_BASE\n\n")
            else:
                out.write(f"{entry_label}:\n")

            pc = self.config.old_start
            bdos_fn_map = self.analyser.bdos_fn_map
            
            smc_map = {}
            smc_target_inst_map = {}
            for src_pc, target_addr in self.analyser.smc_detections:
                if src_pc != target_addr:
                    smc_map[src_pc] = target_addr
                    smc_target_inst_map[self.db.byte_to_instruction_start[target_addr]] = src_pc

            while pc < self.config.old_end:
                key_code = (pc, False)
                key_data = (pc, False)
                
                # 行頭ラベル
                if key_code in self.db.labels or key_data in self.db.labels:
                    is_valid_code_start = self.mem.has_attribute(pc, 'CODE') and self.db.byte_to_instruction_start.get(pc) == pc
                    is_data = not self.mem.has_attribute(pc, 'CODE')
                    
                    if is_valid_code_start:
                        label_name = self.db.labels.get(key_code)
                        if not label_name:
                            label_name = self.db.labels.get(key_data)
                        if label_name:
                            out.write(f"\n{label_name}:\n")
                    elif is_data:
                        # WORK属性の初期データ配置は、RAMアドレスとの衝突を避けるために
                        #  INIT_WORK_/INIT_DATA_ で書き出す
                        label_name = self.db.labels.get(key_data)
                        if label_name and not COPY_CODE_TO_RAM:
                            if self.mem.has_attribute(pc, 'WORK'):
                                label_name = f"INIT_WORK_{pc:04X}H"
                            elif self.mem.has_attribute(pc, 'MERGE'):
                                label_name = f"INIT_DATA_{pc:04X}H"
                            out.write(f"\n{label_name}:\n")

                # ニーモニック
                if self.mem.has_attribute(pc, 'CODE'):
                    bytes_len, inst_str = self.decoder.decode_inst(pc, bdos_fn_map)
                    
                    if pc in smc_map and (
                        COPY_CODE_TO_RAM
                        or not (pc + 3) in self.analyser.smc_patch_jr_addresses):
                        dst_addr = smc_map[pc]
                        dst_label = self.db.get_label(dst_addr, format_asm_hex(self.db.translate_address(dst_addr, is_code=True, is_bios=False)), is_code=True, is_bios=False)
                        inst_str += f" ; [SMC WARNING] CODEブロック{dst_label}への書き込みです。"
                    
                    if pc in smc_target_inst_map and (
                        COPY_CODE_TO_RAM 
                        or not pc in self.analyser.smc_patch_jr_addresses):
                        src_addr = smc_target_inst_map[pc]
                        src_label = self.db.get_label(src_addr, format_asm_hex(src_addr), is_code=True, is_bios=False)
                        src_rel_label = self.db.get_label(src_addr, format_asm_hex(self.db.translate_address(src_addr, is_code=True, is_bios=False)), is_code=True, is_bios=False)
                        inst_str += f" ; [SMC WARNING] {src_rel_label}(オリジナル{src_label})からCODEブロックへの書き込みです。"

                    out.write(f"    {inst_str}\n")
                    pc += bytes_len
                elif COPY_CODE_TO_RAM:
                    pc += 1
                else:
                    pc = self._write_db_sequence(pc, out)

            # === 共通BDOS代替サブルーチン群の定義出力 ===
            out.write("\n;===================================================================\n")
            out.write("; BDOS 代替処理\n")
            out.write(";===================================================================\n")
            for fn_key, routine in BDOS_REPLACE_ROUTINES.items():
                if routine.get("used") is not None:
                    out.write(routine["code"] + "\n")

            if COPY_CODE_TO_RAM:
                out.write("\nROM_CODE_DATA_END:\n\n")
                if ASSEMBLER_TYPE == 1:
                    out.write("    .dephase\n\n")
                else:
                    out.write("ROM_CODECONTINUE EQU STARTUP_END + (ROM_CODE_DATA_END - RAM_BASE)\n")
                    out.write("    ORG ROM_CODECONTINUE, (STARTUP_END - ROM_BASE) + (ROM_CODE_DATA_END - RAM_BASE)\n\n")

                out.write("\n;===================================================================\n")
                out.write("; STATIC DATA SECTION\n")
                out.write(";===================================================================\n")
                out.write("ROM_DATA_PHYSICAL_START:\n")
                pc = self.config.old_start
                rom_code_phys_start = self.config.rom_start + ROM_HEADER_SIZE + ENTRY_CODE_SIZE
                rom_data_phys_start = rom_code_phys_start + self.db.total_code_size

                while pc < self.config.old_end:
                    key_data = (pc, False)
                    key_code = (pc, False)
                    if not self.mem.has_attribute(pc, 'CODE'):
                        if key_data in self.db.labels or key_code in self.db.labels:
                            reloc_addr = self.db.translate_address(pc, is_code=False, is_bios=False)
                            if reloc_addr >= rom_data_phys_start:
                                orig_label = self.db.labels.get(key_data)
                                if orig_label:
                                    if self.mem.has_attribute(pc, 'WORK'):
                                        init_label = f"INIT_WORK_{pc:04X}H"
                                        out.write(f"\n{init_label}:\n")
                                    elif self.mem.has_attribute(pc, 'MERGE'):
                                        init_label = f"INIT_DATA_{pc:04X}H"
                                        out.write(f"\n{init_label}:\n")
                                    else:
                                        out.write(f"\n{orig_label}:\n")
                        pc = self._write_db_sequence(pc, out)
                    else:
                        pc += 1
                out.write("ROM_DATA_PHYSICAL_END:\n\n")

            out.write("\n;===================================================================\n")
            out.write("; RAM転送テーブル\n")
            out.write(";===================================================================\n")
            out.write("RAM_TRANSFER_TABLE:\n")
            for block in transfer_blocks:
                out.write(f"    dw {block.src_label:24}, {block.dest_label:24}, {format_asm_hex(block.size_val)}\n")
            out.write("    dw 0000H                   , 0000H                   , 0000H       ; End of Table\n\n")

            out.write("    END\n")

    def _write_db_sequence(self, pc, out):
        db_bytes = []
        temp_pc = pc
        while temp_pc < self.config.old_end:
            if self.mem.has_attribute(temp_pc, 'CODE'):
                break
            if len(db_bytes) >= 16:
                break
            if temp_pc != pc and ((temp_pc, False) in self.db.labels or (temp_pc, True) in self.db.labels):
                break
            db_bytes.append(self.mem.get_byte(temp_pc))
            temp_pc += 1
            
        if temp_pc == pc:
            db_bytes.append(self.mem.get_byte(temp_pc))
            temp_pc += 1

        hex_tokens = [f"{format_asm_hex(b, 2)}" for b in db_bytes]
        out.write(f"    DB {', '.join(hex_tokens)}\n")
        return temp_pc


class MsxComToRomRelocator:
    def __init__(self):
        self.config = Z80Config()
        self.logger = Z80Logger(self.config.output_log)
        self.mem = Z80MemoryImage(self.config, self.logger)
        self.analyser = Z80FlowAnalyser(self.config, self.mem)
        self.db = Z80AddressRegistry(self.config, self.mem, self.logger)
        self.relocator = Z80SmartRelocator(self.config, self.mem, self.db, self.analyser)
        self.classifier = Z80OpcodeClassifier(self.mem, self.db)
        self.disasm = Z80Disassembler(self.mem, self.db, self.analyser, self.logger)
        self.generator = Z80OutputGenerator(self.config, self.mem, self.db, self.analyser, self.disasm, self.logger)
        self.generator.analyser = self.analyser

    def execute(self):
        global COPY_CODE_TO_RAM
        if not self.mem.load_file():
            return

        # プログラム実行経路のシミュレーション
        self.analyser.analyze_flow(self.db, self.logger)

        # 参照先アドレスのシンボル一覧抽出
        self.relocator.collect_symbols()

        # 未参照コード領域（CODEに挟まれた無参照ブロック）の検出と追加解析
        self._run_phase2_analysis()

        # アドレスで逆引き出来る用に命令先頭アドレスマップを構築する
        self.db.populate_instruction_map()

        # 自己書き換えに関連する連続したジャンプテーブルの検出
        self._scan_jr_smc_jump_tables()

        # 追加解析コードを対象に再度シンボルの仮抽出を行う
        self.relocator.collect_symbols()

        # ワークエリアと隣接する無参照ブロックのマージ処理
        self._merge_contiguous_unreferenced_regions()

        # 各セグメントの物理サイズと配置オフセットを算出する
        self.db.populate_segment_offsets(self.analyser)
        
        # 使用可能メモリ領域の診断
        sim_code_size = self.db.total_code_size
        sim_work_size = self.db.total_work_size
        sim_total_bytes = sim_code_size + sim_work_size

        final_copy_to_ram = COPY_CODE_TO_RAM
        final_ram_start = RAM_START_RAMCOPY

        if final_copy_to_ram:
            sim_limit_addr = final_ram_start + sim_total_bytes - 1
            if sim_limit_addr > RAM_MAX_LIMIT:
                self.logger.log(f"[-] 警告: RAM使用範囲の終端 {format_hex(sim_limit_addr)} がRAM制限アドレス {format_hex(RAM_MAX_LIMIT)} を超えました。")
                self.logger.log("[-] RAMコピー実行モードを無効化し、通常モード（ROM直接実行）に切り替えます。")
                final_copy_to_ram = False

        if not final_copy_to_ram:
            if self.analyser.max_existing_ram > 0:
                final_ram_start = max(self.analyser.max_existing_ram + 1, RAM_START_NORMAL)
            else:
                final_ram_start = RAM_START_NORMAL

        # 各動作パラメータの確定
        COPY_CODE_TO_RAM = final_copy_to_ram
        self.config.ram_start = final_ram_start

        self.db.populate_segment_offsets(self.analyser)

        if COPY_CODE_TO_RAM:
            final_ram_end = self.config.ram_start + self.db.total_code_size + self.db.total_work_size - 1
        else:
            final_ram_end = self.config.ram_start + self.db.total_work_size - 1

        self.logger.log(f"[*] 最終RAM配置モード決定: {'RAM実行モード' if COPY_CODE_TO_RAM else 'ROM直接実行モード'}")
        self.logger.log(f"[*] 最終RAMレイアウト境界: {format_hex(self.config.ram_start)} - {format_hex(final_ram_end)}")
        
        if final_ram_end >= RAM_MAX_LIMIT:
            self.logger.log(f"[-] 致命的エラー: RAM配置先がシステム許容安全限界 ({RAM_MAX_LIMIT - 1:04X}H) を突破しました! アドレス: {format_hex(final_ram_end)}")

        self.db.register_all_collected_symbols()

        for (addr, is_bios), record in self.db.records.items():
            record.new_address = self.db.translate_address(addr, is_code=record.is_work==False, is_bios=is_bios)

        self.print_report()
        self.generator.write_assembly_file()
        self.perform_self_inspection()

    def _run_phase2_analysis(self):
        """フェーズ2: CODEセグメントに挟まれた無参照ブロックを検出し、追加解析を行う"""
        if not USE_CODE_MERGE:
            return

        self.logger.log("[*] 無参照ブロックをスキャン...")
        
        # 登録済みの全参照アドレスを検索用セットへ一時登録する
        referenced_addresses = set()
        for (addr, is_bios) in self.db.unresolved_records:
            if not is_bios:
                referenced_addresses.add(addr)
        for (addr, is_bios) in self.db.labels.keys():
            if not is_bios:
                referenced_addresses.add(addr)

        entries_to_trace = []
        in_gap = False
        gap_start = None
        
        # 解析コード領域の全範囲をスキャンする
        for pc in range(self.config.old_start, self.config.old_end):
            is_code = self.mem.has_attribute(pc, 'CODE')
            is_work = self.mem.has_attribute(pc, 'WORK') or self.mem.has_attribute(pc, 'MERGE')
            
            if not is_code and not is_work:
                # CODE属性もWORK属性もないデータ領域
                if not in_gap:
                    # 開始地点：直前がCODE属性
                    if pc > self.config.old_start and self.mem.has_attribute(pc - 1, 'CODE'):
                        in_gap = True
                        gap_start = pc
            else:
                if in_gap:
                    # 終了地点：現在のアドレスがCODE属性またはWORK属性
                    gap_end = pc - 1
                    if is_code: # 終端がCODE属性である時、
                        # これまでにシンボル参照がないかチェックする
                        is_unreferenced = True
                        for gap_addr in range(gap_start, gap_end + 1):
                            if gap_addr in referenced_addresses:
                                is_unreferenced = False
                                break
                        
                        if is_unreferenced:
                            self.logger.log(f"    - CODEブロックに挟まれた無参照ブロックを検出: {format_hex(gap_start)} ～ {format_hex(gap_end)}")
                            entries_to_trace.append(gap_start)
                            
                            # 隙間の開始位置を UNUSED_xxxxH ラベルとして登録する
                            label_name = f"UNUSED_{gap_start:04X}H"
                            key = (gap_start, False)
                            new_addr = self.db.translate_address(gap_start, is_code=True, is_bios=False)
                            record = Z80AddressRecord(gap_start, label_name, new_addr, is_code=True, is_work=False, is_bios=False)
                            self.db.records[key] = record
                            self.db.labels[key] = label_name
                    in_gap = False

        if entries_to_trace:
            self.logger.log(f"[*] 検出された {len(entries_to_trace)} 件の未参照ブロックの追加解析を実行中...")
            self.analyser.analyze_flow_from_entries(entries_to_trace, self.db, self.logger)
        else:
            self.logger.log("    - 無参照ブロックは検出されませんでした。")

    def _scan_jr_smc_jump_tables(self):
        """自己書き換え処理対象となるJR命令に続く、連続したJP命令テーブルの検出およびラベル登録を行う"""
        self.logger.log("[*] 「JRオペランド書き換え + JP命令テーブル」タイプの処理を走査...")
        
        # ログ出力の重複防止
        scanned_smc_targets = set()
        
        for pc, target in self.analyser.smc_detections:
            if not self.mem.is_valid_address(target):
                continue
            if target in scanned_smc_targets:
                continue
            scanned_smc_targets.add(target)
                
            jr_addr = target - 1
            if self.mem.is_valid_address(jr_addr):
                opcode = self.mem.get_byte(jr_addr)
                if opcode == 0x18: # jr n
                    self.logger.log(f"[+] JR命令オペランドへの書き込みを検知: アドレス {format_hex(target)} (JR命令PC: {format_hex(jr_addr)})")

                    if USE_SMC_PATCH:
                        if (self.mem.get_byte(pc) == 0x32 # ld (nn),a
                            and pc + 2 + 2 < self.config.old_end
                            and jr_addr == pc + 3 # 次の命令が書き込み先の jr n である
                        ):
                            self.logger.log(f"    - \"LD(n),A + JR n\"タイプ -> パッチを適用します。")
                            self.analyser.smc_patch_jr_addresses.add(jr_addr)
                    
                    table_pc = target + 1
                    while self.mem.is_valid_address(table_pc) and table_pc < self.config.old_end:
                        if self.mem.get_byte(table_pc) == 0xC3:
                            jp_target = self.mem.get_word(table_pc + 1)
                            
                            self.db.unresolved_records.add((table_pc, False))
                            self.db.unresolved_records.add((jp_target, False))
                            
                            self.mem.mark_attribute(table_pc, 'CODE')
                            self.mem.mark_attribute(table_pc, 'WORK')
                            self.mem.discard_attribute(table_pc, 'DATA')
                            
                            self.logger.log(f"    - 連続したJP命令（ジャンプ命令テーブル）を検知: `JP {format_hex(jp_target)}` at {format_hex(table_pc)}")
                            table_pc += 3
                        else:
                            break

    def _merge_contiguous_unreferenced_regions(self):
        """WORK領域に隣接する、ラベル参照のないDATA領域をマージ（結合）する"""
        for pc in range(self.config.old_start, self.config.old_end):
            self.mem.discard_attribute(pc, 'MERGE')
            
        for pc in range(self.config.old_start, self.config.old_end):
            if self.mem.has_attribute(pc, 'WORK'):
                next_addr = pc + 1
                merge_count = 0
                while next_addr < self.config.old_end:
                    if (next_addr, False) in self.db.unresolved_records or (next_addr, True) in self.db.unresolved_records or self.mem.has_attribute(next_addr, 'WORK'):
                        break
                    
                    if merge_count >= MAX_STATIC_MERGE_LIMIT:
                        break
                        
                    if (self.mem.has_attribute(next_addr, 'DATA') and 
                            not self.mem.has_attribute(next_addr, 'CODE') and 
                            not self.mem.has_attribute(next_addr, 'WORK')):
                        self.mem.mark_attribute(next_addr, 'MERGE')
                        if self.mem.is_valid_address(next_addr):
                            self.mem.discard_attribute(next_addr, 'DATA')
                        merge_count += 1
                        next_addr += 1
                    else:
                        break

    def perform_self_inspection(self):
        """出力されたアセンブリソースコードを事後検証し、未定義ラベルやシンボルに不整合がないか確認する"""
        self.logger.log("[*] 生成アセンブリコードの自己診断を実行中...")
        if not os.path.exists(self.config.output_asm):
            raise AssertionError("[-] 自己診断失敗: 出力アセンブリファイルが存在しません。")
            
        with open(self.config.output_asm, 'r') as f:
            lines = f.readlines()
            
        defined_symbols = set()
        
        for line in lines:
            line_clean = line.strip().split(";")[0].strip()
            if not line_clean:
                continue
                
            if " EQU " in line_clean:
                parts = line_clean.split(" EQU ")
                sym_name = parts[0].strip()
                defined_symbols.add(sym_name)
                
            elif ":" in line_clean and not line_clean.startswith("."):
                parts = line_clean.split(":")
                sym_name = parts[0].strip()
                if sym_name and " " not in sym_name and "\t" not in sym_name:
                    defined_symbols.add(sym_name)
                
        missing_definitions = []
        for (addr, is_bios), label_name in self.db.labels.items():
            if label_name not in defined_symbols:
                if " + " in label_name or " - " in label_name:
                    continue
                    
                # SMC（自己書き換え）用として命令の途中に設定されたラベルの例外検証
                record = self.db.records.get((addr, is_bios))
                if record and record.is_code and record.is_work:
                    if addr in self.db.byte_to_instruction_start:
                        inst_start = self.db.byte_to_instruction_start[addr]
                        inst_key = (inst_start, is_bios)
                        inst_label = self.db.labels.get(inst_key)
                        if inst_label in defined_symbols:
                            continue  # 命令先頭のラベルが定義されていれば検査通過とする
                            
                missing_definitions.append(f"{label_name} (旧アドレス: {addr:04X}H, is_code: {record.is_code}, is_work: {record.is_work}, is_bios: {is_bios})")
                
        if missing_definitions:
            self.logger.log(f"[-] 致命的エラー: 出力アセンブリに未定義ラベルが検出されました: {missing_definitions}")
            raise AssertionError(f"未定義ラベルエラー: {missing_definitions}")
            
        self.logger.log("[+] 自己診断OK: 参照シンボル定義の整合性エラーはありません。")

    def print_report(self):
        """解析結果のメモリセグメント状況や互換性に関する詳細ログを最終表示する"""
        code_bytes = sum(1 for i in range(self.config.old_start, self.config.old_end) if self.mem.has_attribute(i, 'CODE'))
        data_bytes = sum(
            1 for i in range(self.config.old_start, self.config.old_end) 
            if self.mem.has_attribute(i, 'DATA') and
                not self.mem.has_attribute(i, 'CODE') and 
                not self.mem.has_attribute(i, 'WORK') and 
                not self.mem.has_attribute(i, 'MERGE')
        )
        work_bytes = sum(
            1 for i in range(self.config.old_start, self.config.old_end)
            if self.mem.has_attribute(i, 'WORK') and 
                not self.mem.has_attribute(i, 'CODE') and 
                not self.mem.has_attribute(i, 'MERGE')
        )
        merge_data_bytes = sum(
            1 for i in range(self.config.old_start, self.config.old_end)
              if self.mem.has_attribute(i, 'MERGE')
        )
        bdos_rutine_bytes = self.db.bdos_rutine_size
        patch_delta_size = self.db.patch_delta_offset
        assert(code_bytes + bdos_rutine_bytes + patch_delta_size == self.db.total_code_size)
        assert(data_bytes == self.db.total_data_size)
        assert(work_bytes + merge_data_bytes == self.db.total_work_size)
        
        if COPY_CODE_TO_RAM:
            total_ram_used = code_bytes + work_bytes + merge_data_bytes
        else:
            total_ram_used = work_bytes + merge_data_bytes

        self.logger.log("="*70)
        self.logger.log(center_text("解析レポート", 70))
        self.logger.log("="*70)
        self.logger.log("[+] メモリ属性マップ:")
        
        for section in self.analyser.sections:
            orig_start = section.start_addr
            orig_end = section.end_addr
            reloc_start = self.db.translate_address(orig_start, is_code=False, is_bios=False)
            reloc_end = self.db.translate_address(orig_end, is_code=False, is_bios=False)
            self.logger.log(
                f"    - 属性 [{section.attr_type:4}]: "
                f"オリジナル {format_hex(orig_start)} ～ {format_hex(orig_end)} -> "
                f"再配置 {format_hex(reloc_start)} ～ {format_hex(reloc_end)} "
                f"({orig_end - orig_start + 1:6} = {orig_end - orig_start + 1:04X}H Bytes)"
            )
            
        self.logger.log(f"    - 命令コード（CODE）サイズ総計   : {code_bytes:6} = {code_bytes:4X}H Bytes")
        self.logger.log(f"    - 静的データ（DATA）サイズ総計   : {data_bytes:6} = {data_bytes:4X}H Bytes")
        self.logger.log(f"    - ワークエリア（WORK）サイズ総計 : {work_bytes:6} = {work_bytes:4X}H Bytes")
        self.logger.log(f"    - 無名DATA統合（MERGE）サイズ総計: {merge_data_bytes:6} = {merge_data_bytes:4X}H Bytes (上限設定: {MAX_STATIC_MERGE_LIMIT} Bytes)")
        self.logger.log(f"    - パッチによるサイズ差分総計     : {patch_delta_size:6} = {patch_delta_size:4X}H Bytes")
        self.logger.log(f"    - BDOS互換ルーチンサイズ総計     : {bdos_rutine_bytes:6} = {bdos_rutine_bytes:4X}H Bytes")
        self.logger.log(f"    - 実行時RAM使用サイズ総計        : {total_ram_used:6} = {total_ram_used:4X}H Bytes")
        
        self.logger.log(f"\n[+] 自己書き換えコード (SMC) 検出結果:")
        if self.analyser.smc_detections:
            for pc, target in self.analyser.smc_detections:
                if self.mem.has_attribute(target, 'CODE'):
                    if pc == target:
                        label_name = self.db.get_label(pc, format_asm_hex(self.db.translate_address(pc, is_code=True, is_bios=False)), is_code=True, is_bios=False)
                        self.logger.log(
                            f"    - [警告] 書き換えコード自体を書き換える処理を検出しました: "
                            f"{label_name} (オリジナルアドレス: {pc:04X}H)"
                        )
                    else:
                        src_label = self.db.get_label(pc, format_asm_hex(self.db.translate_address(pc, is_code=True, is_bios=False)), is_code=True, is_bios=False)
                        dst_label = self.db.get_label(target, format_asm_hex(self.db.translate_address(target, is_code=False, is_bios=False)), is_code=False, is_bios=False)
                        self.logger.log(
                            f"    - [警告] PC: {src_label} (オリジナル: {pc:04X}H) の書き込み命令が、 "
                            f"コード領域: {dst_label} (オリジナル: {target:04X}H) の書き換えを行っています。"
                        )
        else:
            self.logger.log("    - 自己書き換えコード(SMC)は検出されませんでした。")

        self.logger.log(f"\n[+] BDOS / DISKROM 互換性システム警告:")
        if self.analyser.unsupported_bdos_calls:
            for call in self.analyser.unsupported_bdos_calls:
                self.logger.log(f"    - [警告] アドレス {call['pc']:04X}H: ディスクアクセスを伴うBDOS呼び出し (Fn {call['fn']}) を検出しました。")
                self.logger.log(f"      BDOSコール用フック ROMBDOS (F37DH) を使用するので、ディスク環境でなければ動作しません。")
        else:
            self.logger.log("    - DISKROM環境に依存する致命的なBDOSコールは検出されませんでした。")

        self.logger.log(f"\n[+] 再配置レイアウトパラメータ:")
        self.logger.log(f"    - ROM領域: {self.config.rom_start:04X}H から開始")
        if COPY_CODE_TO_RAM:
            code_size = self.db.total_code_size
            work_size = self.db.total_work_size
            total_ram_bytes = code_size + work_size
            self.logger.log(f"    - RAM実行モード有効 (全CODEブロックおよびWORKブロックは {self.config.ram_start:04X}H ～ {self.config.ram_start + total_ram_bytes - 1:04X}H の範囲に転送)")
        else:
            self.logger.log(f"    - RAM使用領域: {self.config.ram_start:04X}H から開始")
        self.logger.log("="*70 + "\n")


def parse_hex_string(value):
    """16進数文字列を数値に変換する。失敗した場合は ArgumentTypeError を発生させる"""
    try:
        return int(value, 16)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"'{value}' は有効な16進数文字列ではありません。"
        )


def parse_arguments():
    """コマンドライン引数を解析し、パースされた引数オブジェクトを返す"""
    parser = argparse.ArgumentParser(
        description="COMバイナリ to ROM(32KB page1-2) リロケータ逆アセンブラ v0.15.3",
        add_help=False
    )
    parser.add_argument("-i", "--input", type=str, default=INPUT_PATH, help="入力ファイルパス (16進数テキストまたはバイナリ)")
    parser.add_argument("-o", "--output", type=str, default=OUTPUT_ASM_PATH, help="出力アセンブリファイルパス")
    # typeにparse_hex_stringを指定
    parser.add_argument("-a", "--address", type=parse_hex_string, default=f"{ORIGINAL_LOAD_ADDR:04X}", help="入力バイナリのMSX上での開始アドレスを指定 (16進数4桁、例: 0100)")
    parser.add_argument("-s", type=parse_hex_string, help="RAMの先頭アドレスを指定 (16進数4桁、例: C000)")
    parser.add_argument("-l", type=parse_hex_string, help="RAM使用上限アドレスを指定 (16進数4桁、例: EFFF)")
    parser.add_argument("-c", action="store_true", help="RAMコピーモード有効 (CODE+WORKをRAMへコピーして実行)")
    parser.add_argument("-n", action="store_true", help="通常モード有効 (CODEはROM上で実行、WORKのみRAMに配置)")
    parser.add_argument("--patch", action="store_true", help="SMCパッチ有効 (通常モード時：JR命令書き換えをROM用処理でパッチ)")
    parser.add_argument("--nopatch", action="store_true", help="SMCパッチ無効")
    parser.add_argument("--simple", action="store_true", help="軽い探索を使用する")
    parser.add_argument("--deep", action="store_true", help="深い探索を使用する")
    parser.add_argument("--asm-type", type=int, choices=[1, 2], help="アセンブラのタイプ (1 = sjasmplus, 2 = AILZ80ASM)")
    parser.add_argument("-h", "--help", action="help", help="コマンドライン引数のヘルプを表示")
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    
    # コマンドライン引数に基づくパラメータの更新
    if args.input:
        INPUT_PATH = args.input
        
    if args.output:
        OUTPUT_ASM_PATH = args.output
        # ログファイルの出力先を、指定された出力ファイルと同じディレクトリ・同じベース名の.logに自動設定
        base_dir, base_file = os.path.split(OUTPUT_ASM_PATH)
        name, _ = os.path.splitext(base_file)
        OUTPUT_LOG_PATH = os.path.join(base_dir, name + ".log")

    if args.address is not None:
        ORIGINAL_LOAD_ADDR = args.address

    if args.s is not None:
        ram_val = args.s
        RAM_START_NORMAL = ram_val
        RAM_START_RAMCOPY = ram_val
        TARGET_RAM_BASE = ram_val
        
    if args.l is not None:
        RAM_MAX_LIMIT = args.l
        
    if args.c:
        COPY_CODE_TO_RAM = True
    elif args.n:
        COPY_CODE_TO_RAM = False
        
    if args.patch:
        USE_SMC_PATCH = True
    elif args.nopatch:
        USE_SMC_PATCH = False

    if args.simple:
        PASS1_USE_SIMPLE_PASS = True
    elif args.deep:
        PASS1_USE_SIMPLE_PASS = False

    if args.asm_type is not None:
        ASSEMBLER_TYPE = args.asm_type
        
    engine = MsxComToRomRelocator()
    engine.execute()

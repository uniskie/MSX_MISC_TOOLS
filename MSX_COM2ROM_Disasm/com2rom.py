# =====================================================================
# COMバイナリ to ROM(32KB Page 1-2) リロケータ逆アセンブラ
# =====================================================================
# 【概要と背景】
# MSX-DOS環境の実行ファイル（COMバイナリ）は、通常 0x0100 アドレスから
# RAM空間上にロードされ、コード領域も含めてRAM上で動作することを前提としています。
# 本ツールは、このCOMバイナリを静的解析・逆アセンブルし、MSXのカートリッジスロット
# に挿入して起動可能な「32KB ROM (Page 1-2: 0x4000〜0xBFFF)」形式のアセンブリソース
# コードへリロケーション（再配置）変換します。
#
# 【自己書き換え（SMC: Self-Modifying Code）への対策モード】
# 8ビット時代のバイナリでは、ジャンプ先や即値を実行時に動的書き換えする手法（SMC）
# が多用されていました。書き込み不可能なROM上ではこれが破綻するため、本ツールでは
# 以下の2つのアプローチを用意しています：
#
# 1. RAM転送モード (COPY_CODE_TO_RAM = True)
#    - 必要RAM容量：約16KB以上 (0xC000〜)
#    - 動作原理：CODEセグメントおよびWORKセグメントを、ROM起動時にPage 3 RAM
#      (0xC000〜) へ一括転送し、RAM上でプログラムを実行します。
#    - メリット：命令コード自体がRAM上に存在するため、あらゆる自己書き換えコードが
#      原則としてそのまま動作します。
#    - デメリット：MSX本体に十分な空きRAM容量が必要となります。
#
# 2. パッチモード / 通常モード (COPY_CODE_TO_RAM = False)
#    - 必要RAM容量：約8KB (0xE000〜)
#    - 動作原理：CODEセグメントはROM上 (0x4000〜) で直接実行し、変数やバッファ
#      などのWORKセグメントのみをPage 3 RAM (0xE000〜) に配置します。
#    - メリット：RAM消費量を最小限に抑えられます。
#    - デメリット：自己書き換えコードに対応できません。ただし、最も頻出する
#      「JR命令の相対オフセット書き換えによるジャンプ分岐」については、
#      ROM上で動作する代用コード（JP (HL) パッチ）へ自動置換します。
#
# ※汎用的な逆コンパイラではなく、MSXのメモリマップおよびZ80アーキテクチャに
#   特化したリロケータです。
# =====================================================================
import os
import copy
import argparse
import re
import msx_symbols  # msx_symbols.py から search_labels_dos および search_labels を使用

APP_VESRSION = "v15.4"

# =====================================================================
# グローバルシステム設定（定数パラメータ定義）
# =====================================================================
INPUT_PATH          = "indev.com"
OUTPUT_ASM_PATH     = "indev_rom.asm"
OUTPUT_LOG_PATH     = "indev_rom.log"

RAM_START_NORMAL    = 0xE000     # 通常モード（ROM直接実行）でのRAM開始アドレス (Page 3)
RAM_START_RAMCOPY   = 0xC000     # RAMコピーモードでのRAM開始アドレス (Page 3 先頭)

SYSYTEM_WORK        = 0xF380     # MSXシステムワークエリアの先頭アドレス（0xF380以降はOS予約領域）

TARGET_ROM_BASE     = 0x4000     # MSXカートリッジROMの基準アドレス (Page 1: 0x4000〜0x7FFF)
TARGET_RAM_BASE     = RAM_START_NORMAL   # Page 3 RAM 基準アドレス (裏RAMスペース)

ORIGINAL_LOAD_ADDR  = 0x0100     # MSX-DOS COMファイルの標準実行開始アドレス (TPA先頭アドレス)

# 自己書き換え対策：連続するJP命令の自動検出とパッチフラグ
SCAN_SEQUENTIAL_JP  = True       # 連続するジャンプ命令テーブル（JP nn の連続）を検出するかどうか
USE_SMC_PATCH       = True       # 通常モード時、JR命令の書き換えに対してパッチを適用するかどうか

# 自己書き換え対策：CODE/WORK領域をPage 3 RAM上に転送して実行するモードの切替フラグ
COPY_CODE_TO_RAM    = False      # True: RAMコピーモード (CODEをRAMへコピーして実行), False: 通常モード (CODEをROM上で直接実行)
RAM_MAX_LIMIT       = 0xEFFF     # Page 3 RAMの安全上限アドレス（0xF000以降のシステムスタック・ワークとの衝突防止）

# WORKセグメントに続く無参照ブロックのマージ最大範囲（デフォルト上限: 2バイト）
# WORKエリアの直後にある未参照DATA（文字列のNULL終端やアライメントパディング等）を
# DATAセグメントとして孤立させず、RAM上のWORKセグメントに統合して転送するための閾値。
# 0に設定するとマージ処理は無効化されます。
MAX_STATIC_MERGE_LIMIT = 2

# （通常モードのみ）CODEブロックに挟まれた未参照ブロックをCODEセグメントに統合して解析するフラグ
USE_CODE_MERGE = True

# パス1の探索深度設定
# True : 簡易構造探索（アドレスのみをキーにして重複探索を早期判定）
# False: 深い経路探索（アドレスだけでなく主要レジスタの状態もキーにして精密に探索）
PASS1_USE_SIMPLE_PASS = True

# 簡易的なレジスタ値の追跡・計算を行うかどうかの設定
# 【実験機能】不完全なエミュレーションのため、処理が重くなる可能性があります。
USE_REGISTER_CALCULATIONS = False

# 出力アセンブラの種類に応じたシンタックス指定
ASSEMBLER_TYPE      = 2          # 1: sjasmplus 形式 (.phase / .dephase によるRAM配置展開)
                                 # 2: AILZ80ASM 形式 (ORG $C000, $ / ORG $ によるRAM配置展開)

# スタックポインタ (SP) の初期アドレス値
STACK_INIT_VAL      = SYSYTEM_WORK

# =====================================================================
# MSX-DOS システムコール（BDOS）エントリアドレス
# MSX-DOS環境では、0x0005 アドレスへの CALL によってBDOS機能を呼び出します。
# ROM環境にはDOSが存在しないため、本ツールはこのアドレスへのCALLを検知して置換します。
# =====================================================================
BDOS_CALL_ADDRESS = 0x0005

# =====================================================================
# スタートアップコード（ROMヘッダおよびスロット拡張初期化）
# =====================================================================
# MSXカートリッジROMは、先頭16バイトに特定の識別ヘッダが存在する必要があります。
ROM_HEADER_SIZE = 0x10
ROM_HEADER = '''
;--- MSX ROM HEADER ---
    db 41H, 42H             ; 'AB' (MSXカートリッジROM識別子: 41H='A', 42H='B')
    dw STARTUP_ENTRY        ; INIT: リセット・起動時に実行される初期化エントリアドレス
    dw 0000H                ; STATEMENT: CALL文（拡張BASIC文）ハンドラ（未使用: 0000H）
    dw 0000H                ; DEVICE: 拡張デバイスハンドラ（未使用: 0000H）
    dw 0000H                ; TEXT: BASICプログラム自動起動ポインタ（未使用: 0000H）
    ds 6, 00H               ; システム予約領域 (6バイトのゼロクリア)
'''

# 32KB ROMを構成するためのPage 2スロット接続およびRAM初期化ルーチンのサイズ（バイト数）
ENTRY_CODE_SIZE = 67
ENTRY_CODE = '''
;===================================================================
; STARTUP ENTRY (スロット切り替えおよびRAM初期化)
;===================================================================
; 【動作原理】
; MSXのメモリ空間は16KBごとの4つのPage（Page 0: 0000H〜, Page 1: 4000H〜,
; Page 2: 8000H〜, Page 3: C000H〜）に分かれています。
; カートリッジが挿入されたスロットは通常 Page 1 (4000H〜7FFFH) に接続されますが、
; 32KB ROMとして Page 2 (8000H〜BFFFH) までROM領域を連続させるには、
; Page 2 のスロット選択レジスタを Page 1 と同一のスロット（基本スロット＋拡張サブスロット）
; に明示的に切り替える必要があります。
STARTUP_ENTRY:
    ld sp, STACK_INIT_ADDR  ; スタックポインタを安全なシステム領域直前に初期化
    di                      ; スロットレジスタ操作中の割り込みを禁止
    call RSLREG             ; システムBIOS RSLREG: 現在の各Pageの基本スロット選択状態をAに取得
    rrca
    rrca                    ; ビット2-3（Page 1の基本スロットID）をビット0-1の位置へシフト
    and 03H                 ; 基本スロットID (0〜3) のみマスク抽出
    ld c, a
    ld b, 0
    ld hl, EXPTBL           ; システムワーク EXPTBL: スロット拡張フラグテーブルの先頭
    add hl, bc
    ld a, (hl)              ; 対象基本スロットが拡張スロット構成かを取得
    and 80H                 ; 最上位ビット（拡張スロットフラグ）を抽出
    or c                    ; 基本スロットIDと拡張フラグを合成
    ld c, a                 ; Cレジスタ = Page 1 が存在する完全なスロットID (Slot ID)
    ld h, 80H               ; 切り替え対象Pageのアドレス (8000H = Page 2)
    call ENASLT             ; システムBIOS ENASLT: Page 2 をカートリッジと同一スロットへ接続

    ;--- RAM転送テーブル経由での初期化データ展開 ---
    ; ROM内に配置されているWORKエリアの初期値（およびRAMコピーモード時のCODE）を、
    ; LDIR命令を用いてPage 3 RAM領域へ一括転送します。
    ld ix, RAM_TRANSFER_TABLE
STARTUP_TRX_LOOP:
    ld l, (ix+0)
    ld h, (ix+1)            ; HL = 転送元アドレス (ROM側)
    ld e, (ix+2)
    ld d, (ix+3)            ; DE = 転送先アドレス (RAM側)
    ld c, (ix+4)
    ld b, (ix+5)            ; BC = 転送バイト数
    ld a, b
    or c
    jr z, STARTUP_TRX_DONE  ; 転送サイズが 0000H であれば終端とみなしループ終了
    ldir                    ; (DE) <- (HL), BCデクリメントを繰り返すブロック転送
    ld de, 6
    add ix, de              ; 次の転送定義レコード（6バイト幅）へ進める
    jr STARTUP_TRX_LOOP
STARTUP_TRX_DONE:
    ei                      ; 割り込みを再許可
    jp EXEC_ADDRESS         ; リロケートされたプログラムの実行開始アドレスへジャンプ
STARTUP_END:

'''

# =====================================================================
# 自己書き換えコード (SMC) に対する置換パッチ定義
# =====================================================================
# 【自己書き換えパターンの動作原理と回避策】
# 検出対象パターン：
#   ld (target_label + 1), a   ; JR命令の第2バイト（相対変位e）にAレジスタの値を書き込み
#   jr dest_label              ; 書き換えられた相対ジャンプ（ROM上では書き換え不能）
#
# 回避策：
# 1. 書き込み命令「ld (target_label + 1), a」(3バイト) を削除（0バイト化）する。
# 2. 直後の「jr dest_label」(2バイト) を、Aレジスタのインデックスを加算して
#    絶対アドレス間接ジャンプを行うパッチコード（9バイト）へ置換する。
#    これにより、Aレジスタの値に応じたテーブルジャンプがROM上でも正常に機能する。

# 書き込み命令側の置換コード（削除してコメントのみ残す）
smc_patch_jr_code_ld_size = 0
smc_patch_jr_code_ld = (
    "; [SMC PATCH] ld (target_label), a --> ROM化のため削除"
)

# 分岐命令側の置換コード（JP (HL) による絶対アドレス動的ジャンプへ置換）
smc_patch_jr_code_jr_size = 9
smc_patch_jr_code_jr = (
 '''add a, low dest_label  ; [SMC PATCH] Aレジスタの変位を基準ジャンプ先下位バイトへ加算
    ld l, a                ; 計算結果を下位レジスタLへ格納
    ld a, high dest_label  ; 基準ジャンプ先上位バイトを取得
    adc a, 00H             ; キャリーを加算
    ld h, a                ; 上位レジスタHへ格納
    jp (hl)                ; 目的のジャンプ先アドレスへ間接ジャンプ'''
)

# =====================================================================
# BDOSファンクション代替サブルーチン群
# =====================================================================
# 【MSX-DOS BDOSコール置換の動作原理】
# COMファイルはシステムコール呼び出し時、Cレジスタにファンクション番号を格納して
# CALL 0005H を実行します。本ツールはCレジスタの即値ロード（LD C, n / LD BC, nn）を
# 静的解析で検出し、以下のMSX BIOSコールを利用した代替ルーチンへの呼び出しに置き換えます。
# 未対応のディスクアクセス系（0x0D以降）は DISK-ROM のフックアドレスへ転送します。
BDOS_REPLACE_ROUTINES = {
    0x00: { # システムリセット / プログラム終了
        "label": "BDOS_SUB_00_TERM",
        "size": 4,
        "code": """
BDOS_SUB_00_TERM:
    di                          ; 割り込みを禁止
    jp 0000H                    ; 0000H (MSX BIOSリセットエントリ) へジャンプして再起動
"""
    },
    0x01: { # コンソールから1文字入力 (入力待ちあり、画面エコーバックあり、Ctrl+Cチェックあり)
        "label": "BDOS_SUB_01_CONIN",
        "size": 13,
        "code": """
BDOS_SUB_01_CONIN:
    call CHGET                  ; BIOS CHGET (009FH): 1文字入力待ち (A=文字コード)
    cp 03H                      ; Ctrl+C (03H: 中断要求) が押されたか判定
    ret z                       ; 中断ならエコーバックせずに即座に復帰
    push af                     ; 入力文字コードをスタックに退避
    ld e, a                     ; 出力文字をEレジスタへセット
    call CHPUT                  ; BIOS CHPUT (00A2H): 画面に1文字エコーバック表示
    pop af                      ; 入力文字コードをAレジスタに復帰
    ret
"""
    },
    0x02: { # コンソールへ1文字出力 (タブ文字 09H のスペース展開処理を含む)
        "label": "BDOS_SUB_02_CONOUT",
        "size": 21,
        "code": """
BDOS_SUB_02_CONOUT:
    ld a, e                     ; Eレジスタの出力文字コードをAへ転送
    cp 09H                      ; タブ文字 (09H) か判定
    jr nz, .PLAIN_OUT_02        ; タブでなければ通常の1文字出力へ分岐
    ld a, 20H                   ; 空白文字 (20H) をセット
    call CHPUT                  ; 3文字分のスペースを出力して簡易タブ展開
    call CHPUT
    call CHPUT
    ret
.PLAIN_OUT_02:
    call CHPUT                  ; BIOS CHPUT (00A2H): 1文字画面出力
    ret
"""
    },
    0x03: { # 補助入力装置 (AUX) から1文字入力
        "label": "BDOS_SUB_03_AUXIN",
        "size" : 3,
        "code": """
BDOS_SUB_03_AUXIN:
    ld a, 1AH                   ; ROM環境には補助入力が存在しないため EOF (1AH) を返却
    ret
"""
    },
    0x04: { # 補助出力装置 (AUX) へ1文字出力
        "label": "BDOS_SUB_04_AUXOUT",
        "size" : 2,
        "code": """
BDOS_SUB_04_AUXOUT:
    nop                         ; ROM環境には補助出力が存在しないため何もしない (ダミー復帰)
    ret
"""
    },
    0x05: { # プリンタへ1文字出力
        "label": "BDOS_SUB_05_LSTOUT",
        "size" : 5,
        "code": """
BDOS_SUB_05_LSTOUT:
    ld a, e                     ; Eレジスタの出力文字コードをAへ転送
    call LPTOUT                 ; BIOS LPTOUT (00A5H): プリンタへ1文字出力
    ret
"""
    },
    0x06: { # 直接コンソール入出力 (E=FFHなら入力待ちなし入力、それ以外なら直接出力)
        "label": "BDOS_SUB_06_DIRIO",
        "size" : 21,
        "code": """
BDOS_SUB_06_DIRIO:
    ld a, e
    cp 0FFH                     ; Eレジスタが 0FFH (入力要求) かどうか判定
    jr nz, .PLAIN_OUT_06        ; 0FFH 以外なら出力要求として分岐
    call CHSNS                  ; BIOS CHSNS (009CH): キーボードバッファに入力があるか確認
    jr z, .NO_KEY_06            ; 入力がなければ Z=1 となるため分岐
    call CHGET                  ; BIOS CHGET (009FH): バッファから1文字取得 (A=文字コード)
    or a                        ; Zフラグをクリア (Z=0: 入力文字が存在することを示す)
    ret
.NO_KEY_06:
    xor a                       ; Zフラグをセット (Z=1: 入力文字がないことを示す), A=00H
    ret
.PLAIN_OUT_06:
    call CHPUT                  ; BIOS CHPUT (00A2H): Eレジスタの文字コードをそのまま出力
    ret
"""
    },
    0x07: { # コンソールから直接1文字入力 (入力待ちあり、画面エコーバックなし、Ctrl+C判定なし)
        "label": "BDOS_SUB_07_DIRIN",
        "size" : 4,
        "code": """
BDOS_SUB_07_DIRIN:
    call CHGET                  ; BIOS CHGET (009FH): 1文字入力待ち (A=文字コード)
    ret
"""
    },
    0x08: { # コンソールから1文字入力 (入力待ちあり、画面エコーバックなし、Ctrl+C判定あり)
        "label": "BDOS_SUB_08_INP_NO_ECHO",
        "size" : 7,
        "code": """
BDOS_SUB_08_INP_NO_ECHO:
    call CHGET                  ; BIOS CHGET (009FH): 1文字入力待ち (A=文字コード)
    cp 03H                      ; Ctrl+C (03H: 中断要求) が押されたか判定
    ret z
    ret
"""
    },
    0x09: { # コンソールへ文字列出力 (DEレジスタの指すアドレスから '$'(24H) 終端まで出力)
        "label": "BDOS_SUB_09_STROUT",
        "size" : 15,
        "code": """
BDOS_SUB_09_STROUT:
    ld h, d
    ld l, e                     ; HL = 出力対象文字列の先頭アドレス
.STR_LOOP_09:
    ld a, (hl)                  ; メモリから1文字読み出し
    cp 24H                      ; '$' (24H: CP/M・DOS文字列終端マーク) か判定
    ret z                       ; 終端に達したら復帰
    push hl                     ; 文字列ポインタをスタックに退避
    ld e, a
    call CHPUT                  ; BIOS CHPUT (00A2H): 1文字画面出力
    pop hl                      ; 文字列ポインタを復帰
    inc hl                      ; 次の文字アドレスへ進める
    jr .STR_LOOP_09
"""
    },
    0x0A: { # コンソールから1行バッファ入力 (バックスペース・文字数制限・Enter終了に対応)
        "label": "BDOS_SUB_0A_BUFIN",
        "size" : 97,
        "code": """
BDOS_SUB_0A_BUFIN:
    ld h, d
    ld l, e                     ; HL = 入力バッファ先頭アドレス
    ld a, (hl)                  ; バッファ先頭バイト（許容される最大入力文字数）を取得
    ld b, a                     ; B = 最大入力文字数
    inc hl
    push hl                     ; 確定文字数の書き戻しアドレス (DE+1) をスタックへ退避
    inc hl                      ; HL = 文字格納先バッファの開始アドレス (DE+2)
    ld c, 0                     ; C = 現在の入力文字数カウンタ
.KB_IN_LOOP_0A:
    push bc
    push hl
    call CHGET                  ; BIOS CHGET (009FH): 1文字入力待ち
    pop hl
    pop bc
    cp 0DH                      ; Enterキー (0DH: CR) か判定
    jr z, .KB_END_0A
    cp 08H                      ; Backspaceキー (08H: BS) か判定
    jr z, .KB_BACKSPACE_0A
    
    ld d, a                     ; 入力文字をDレジスタへ退避
    ld a, c
    cp b                        ; 入力文字数が上限に達しているか判定
    jr z, .KB_LIMIT_0A
    
    ld a, d                     ; 入力文字を復帰
    ld (hl), a                  ; バッファに入力文字を格納
    inc hl                      ; バッファポインタをインクリメント
    inc c                       ; 入力文字数カウンタをインクリメント
    push bc
    push hl
    ld e, a
    call CHPUT                  ; 入力された文字を画面にエコーバック表示
    pop hl
    pop bc
    jr .KB_IN_LOOP_0A
.KB_LIMIT_0A:
    ld a, d                     ; 入力文字を復帰
    push bc
    push hl
    call BEEP                   ; 上限到達警告音 (BIOS BEEP: 00C0H) を鳴らす
    pop hl
    pop bc
    jr .KB_IN_LOOP_0A
.KB_BACKSPACE_0A:
    ld a, c
    or a                        ; 入力文字数が既に0文字か判定
    jr z, .KB_IN_LOOP_0A        ; 0文字ならバックスペースを無視
    dec hl                      ; バッファポインタを1つ戻す
    dec c                       ; 文字数カウンタをデクリメント
    push bc
    push hl
    ld e, 08H
    call CHPUT                  ; 画面上でカーソルを1つ左へ戻す
    ld e, 20H
    call CHPUT                  ; 空白文字を出力して直前の文字を消去
    ld e, 08H
    call CHPUT                  ; 再びカーソルを1つ左へ戻す
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
    pop hl                      ; 確定文字数の格納先アドレス (DE+1) を復帰
    ld (hl), c                  ; 確定した入力文字数をバッファに書き戻す
    ret
"""
    },
    0x0B: { # コンソール入力状態チェック (キーバッファに入力があるか確認)
        "label": "BDOS_SUB_0B_STATUS",
        "size" : 9,
        "code": """
BDOS_SUB_0B_STATUS:
    call CHSNS                  ; BIOS CHSNS (009CH): キー入力の有無を判定
    ld a, 00H
    ret z                       ; 入力なしなら A=00H を返却
    ld a, 0FFH                  ; 入力ありなら A=0FFH を返却
    ret
"""
    },
    0x0C: { # MSX-DOSバージョン番号の取得
        "label": "BDOS_SUB_0C_VERSION",
        "size" : 4,
        "code": """
BDOS_SUB_0C_VERSION:
    ld hl, 0022H                ; MSX-DOS バージョン 2.2 相当を示す固定値 (HL=0022H) を返却
    ret
"""
    },
    "UNSUPPORTED": { # 未対応ファンクション（0x0D以降のディスクファイルアクセス等）
        "label": "BDOS_SUB_UNSUPPORTED",
        "size" : 4,
        "code": """
BDOS_SUB_UNSUPPORTED:
    di                          ; 割り込みを禁止
    jp ROMBDOS                  ; DISK-ROMが存在する場合のシステムフック ROMBDOS (F37DH) へ中継
"""
    }
}

# =====================================================================
# ユーティリティ関数群
# =====================================================================

def center_text(text, cols):
    """全角文字の表示幅を考慮し、テキストを指定桁数の中央に配置するフォーマット関数"""
    return text.center(cols + len(text) - len(text.encode('cp932')))

def format_asm_hex(val, width=4):
    """数値をINTEL系アセンブラ文法に準拠した16進数文字列へ変換する（例: 0FFFFH, 0040H）"""
    hex_str = f"{val:0{width}X}"
    # 先頭が英字(A〜F)の場合は数値リテラルと識別させるため先頭に '0' を付与
    if hex_str[0] in "ABCDEF":
        return "0" + hex_str + "H"
    return hex_str + "H"

def format_hex(val, width=4):
    """数値を末尾 'H' 形式の16進数文字列へ変換する（例: FFFFH, 0040H）"""
    hex_str = f"{val:0{width}X}"
    return hex_str + "H"

def get_standard_len(opcode):
    """Z80の標準命令（プレフィックスを持たない1バイトオペコード）の命令バイト長（1〜3）を返す。

    後続のオペランドバイト数（即値データやアドレス参照）の有無を判定して命令長を算出します。
    """
    # 3バイト命令: 16ビット即値データまたは絶対アドレスを持つ命令
    # - 0x01, 0x11, 0x21, 0x31: LD rp, nn (rp: BC, DE, HL, SP)
    # - 0x32: LD (nn), A / 0x3A: LD A, (nn)
    # - 0x22: LD (nn), HL / 0x2A: LD HL, (nn)
    # - 0xC3: JP nn (無条件絶対ジャンプ)
    # - 0xCD: CALL nn (無条件コール)
    if opcode in [0x01, 0x11, 0x21, 0x31] or opcode in [0x32, 0x22, 0x3A, 0x2A] or opcode in [0xC3, 0xCD]:
        return 3

    # 3バイト命令: 条件付き絶対ジャンプ命令 (JP cc, nn)
    # ccフラグ: NZ(C2), Z(CA), NC(D2), C(DA), PO(E2), PE(EA), P(F2), M(FA)
    if opcode in [0xC2, 0xCA, 0xD2, 0xDA, 0xE2, 0xEA, 0xF2, 0xFA]:
        return 3

    # 3バイト命令: 条件付きコール命令 (CALL cc, nn)
    # ccフラグ: NZ(C4), Z(CC), NC(D4), C(DC), PO(E4), PE(EC), P(F4), M(FC)
    if opcode in [0xC4, 0xCC, 0xD4, 0xDC, 0xE4, 0xEC, 0xF4, 0xFC]:
        return 3

    # 2バイト命令: 相対ジャンプ命令 (1バイトの符号付き相対変位 e を持つ)
    # - 0x18: JR e (無条件相対ジャンプ)
    # - 0x20, 0x28, 0x30, 0x38: JR cc, e (条件付き相対ジャンプ: NZ, Z, NC, C)
    # - 0x10: DJNZ e (Bレジスタデクリメントによる条件付き相対ループ)
    if opcode in [0x18, 0x20, 0x28, 0x30, 0x38] or opcode == 0x10:
        return 2

    # 2バイト命令: 8ビット即値データ(n)を伴うロード・演算、およびI/Oポート指定命令
    # - 0x06, 0x0E, 0x16, 0x1E, 0x26, 0x2E, 0x3E: LD r, n (r: B, C, D, E, H, L, A)
    # - 0x36: LD (HL), n
    # - 0xC6, 0xCE, 0xD6, 0xDE, 0xE6, 0xEE, 0xF6, 0xFE: ADD/ADC/SUB/SBC/AND/XOR/OR/CP A, n
    # - 0xD3: OUT (n), A / 0xDB: IN A, (n)
    len_map_2byte = [
        0x06, 0x0E, 0x16, 0x1E, 0x26, 0x2E, 0x3E, 0x36,
        0xC6, 0xCE, 0xD6, 0xDE, 0xE6, 0xEE, 0xF6, 0xFE,
        0xD3, 0xDB
    ]
    if opcode in len_map_2byte:
        return 2

    # 1バイト命令: オペランドを持たない命令（レジスタ間転送・演算、PUSH/POP、RET、単体フラグ操作等）
    return 1


class Z80Logger:
    """コンソールへのログ表示およびログファイルへの追記保存を一元管理するクラス"""
    def __init__(self, log_filepath):
        """ロガーを初期化し、ログファイルを新規作成（既存ファイルは上書きクリア）する"""
        self.log_filepath = log_filepath
        try:
            with open(self.log_filepath, 'w', encoding='utf-8') as f:
                pass
        except IOError:
            print("[-] エラー: ログファイルの初期化に失敗しました。")

    def log(self, message):
        """コンソールにログ文字列を出力し、同時にログファイルへ追記する"""
        print(message)
        try:
            with open(self.log_filepath, 'a', encoding='utf-8') as f:
                f.write(message + "\n")
        except IOError:
            print("[-] エラー: ログファイルへの書き込みに失敗しました。")


class Z80Config:
    """メモリ配置アドレスや入出力ファイルパスなどの動作環境設定パラメータを保持するクラス"""
    def __init__(self):
        """設定パラメータをデフォルト値で初期化する"""
        self.input_file = INPUT_PATH
        self.output_asm = OUTPUT_ASM_PATH
        self.output_log = OUTPUT_LOG_PATH
        
        self.rom_start = TARGET_ROM_BASE
        self.ram_start = TARGET_RAM_BASE
        
        self.old_start = ORIGINAL_LOAD_ADDR
        self.old_end = ORIGINAL_LOAD_ADDR


class Z80MemoryImage:
    """64KBの仮想メモリバッファと、1バイトごとの属性フラグ（CODE/DATA/WORK/MERGE）を管理するクラス"""
    def __init__(self, config: Z80Config, logger: Z80Logger):
        """64KB仮想メモリ空間バッファおよび属性マップを初期化する"""
        self.config = config
        self.logger = logger
        self.raw_bytes = bytearray(65536)           # 64KBの仮想メモリアドレス空間
        self.attributes = [set() for _ in range(65536)]  # 各アドレスの属性フラグ集合

    def is_valid_address(self, addr):
        """指定アドレスが有効な16ビットメモリ空間（0x0000〜0xFFFF）に収まっているか検証する"""
        if not (0 <= addr <= 0xFFFF):
            self.logger.log(f"[-] 警告: 16ビットメモリ空間外への不正アクセスを検出しました: {addr}")
            return False
        return True

    def reset_attributes(self, old_start, old_end):
        """全メモリ空間の属性をクリアし、入力バイナリが読み込まれた範囲の属性を初期状態 'DATA' に設定する"""
        for addr in range(65536):
            self.attributes[addr].clear()
        for addr in range(old_start, old_end):
            if self.is_valid_address(addr):
                self.attributes[addr].add('DATA')

    def load_file(self):
        """バイナリファイル、またはテキスト形式の16進ダンプファイルを読み込み、仮想メモリ上に展開する"""
        if not os.path.exists(self.config.input_file):
            print(f"[-] エラー: 入力ファイル '{self.config.input_file}' が見つかりません。")
            return False
            
        _, ext = os.path.splitext(self.config.input_file.lower())
        
        try:
            if ext in ['.txt', '.hex']:
                # テキスト形式の16進数ダンプテキストのパース
                binary = bytearray()
                with open(self.config.input_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # 先頭に16進アドレス表示（コロン区切りまたは4桁以上）が存在するか判定
                        match = re.match(r'^([0-9A-Fa-f:]+)\s+(.*)', line)
                        if match:
                            addr_part = match.group(1).replace(':', '')
                            if len(addr_part) >= 4 and all(c in '0123456789ABCDEFabcdef' for c in addr_part):
                                data_part = match.group(2).strip()[: 2*16 + 15].replace('-', ' ') # 2文字*16バイト + 区切り文字15個
                                for t in data_part.split():
                                    try:
                                        binary.append(int(t, 16))
                                    except ValueError as e:
                                        print(f"[-] エラー: 16進数表記ではありません: {e}")
                                        return False
                                continue
                        
                        # アドレス部を持たない単純な空白・ハイフン区切りの16進数テキスト行
                        line_clean = line.replace('-', ' ')
                        for t in line_clean.split():
                            try:
                                binary.append(int(t, 16))
                            except ValueError as e:
                                print(f"[-] エラー: 16進数表記ではありません: {e}")
                                return False
            else:
                # 生のバイナリファイル (.com等) の直接読み込み
                with open(self.config.input_file, 'rb') as f:
                    binary = bytearray(f.read())
        except Exception as e:
            print(f"[-] エラー: ファイルの読み込みに失敗しました: {e}")
            return False
                
        length = len(binary)
        self.config.old_end = self.config.old_start + length
        
        # 64KB空間を超過しないように終端境界をクリップ
        if self.config.old_start + length > 65536:
            length = 65536 - self.config.old_start
            self.config.old_end = 65536
            
        self.raw_bytes[self.config.old_start:self.config.old_end] = binary[:length]
        return True

    def mark_attribute(self, addr, attr):
        """指定アドレスに特定の属性フラグ（CODE, DATA, WORK, MERGE等）を付与する"""
        if not self.is_valid_address(addr):
            return False
        self.attributes[addr].add(attr)
        return True

    def discard_attribute(self, addr, attr):
        """指定アドレスから特定の属性フラグを取り除く"""
        if not self.is_valid_address(addr):
            return False
        self.attributes[addr].discard(attr)
        return True

    def has_attribute(self, addr, attr):
        """指定アドレスに特定の属性フラグが設定されているか判定する"""
        if not self.is_valid_address(addr):
            return False
        return attr in self.attributes[addr]

    def get_byte(self, addr):
        """仮想メモリから指定アドレスの1バイト（0〜255）を読み出す"""
        if not self.is_valid_address(addr):
            raise IndexError(f"アドレス範囲外アクセス: {addr}")
        return self.raw_bytes[addr]

    def get_word(self, addr):
        """仮想メモリから指定アドレスの16ビットワード（リトルエンディアン形式）を読み出す"""
        addr_next = addr + 1
        if not self.is_valid_address(addr) or not self.is_valid_address(addr_next):
            raise IndexError(f"アドレス範囲外アクセス: {addr}")
        return self.raw_bytes[addr] | (self.raw_bytes[addr_next] << 8)


class SectionRange:
    """連続する同種メモリ属性セグメント（CODE, DATA, WORK等）の開始・終了アドレス範囲を保持する構造体"""
    def __init__(self, start_addr, end_addr, attr_type):
        """セクションの開始アドレス、終了アドレス、属性タイプを初期化する"""
        self.start_addr = start_addr
        self.end_addr = end_addr
        self.attr_type = attr_type


class Z80AddressRecord:
    """リロケーション前後のアドレス対応、属性フラグ、参照元アドレス一覧を保持するレコードクラス"""
    def __init__(self, old_address, label_name, new_address=0, is_code=False, is_work=False, is_bios=False):
        """アドレスレコードの属性情報および再配置先アドレスを初期化する"""
        self.old_address = old_address  # 変換前の元アドレス（COMバイナリ上のアドレス）
        self.label_name = label_name    # 生成されたラベル識別名
        self.new_address = new_address  # 変換後の再配置先アドレス（ROMまたはRAMのアドレス）
        self.is_code = is_code          # 実行可能コード領域フラグ
        self.is_work = is_work          # ワークエリア（書き込み対象RAM領域）フラグ
        self.is_bios = is_bios          # システムBIOS / システムワークエリアフラグ
        self.references = []            # このアドレスを参照している命令のPCアドレス一覧


class Z80AddressRegistry:
    """ラベルの登録・解決、命令先頭アドレスの逆引き、およびアドレス変換を一元管理するレジストリクラス"""
    def __init__(self, config: Z80Config, mem: Z80MemoryImage, logger: Z80Logger):
        """レジストリを初期化し、MSXシステム固有の固定シンボルを先行登録する"""
        self.config = config
        self.mem = mem
        self.logger = logger
        
        # (address, is_bios) のタプルをキーとしてレコードおよびラベル名を管理
        self.records = {}
        self.labels = {}
        self.unresolved_records = set()
        
        # メモリアドレスから命令先頭アドレスへの逆引きマップ（命令の途中にジャンプした場合のオフセット算出用）
        self.byte_to_instruction_start = {}
        
        # セグメント内の相対オフセット管理用
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
        """システムワークエリアのスタック初期値および標準BIOSルーチンのアドレスを先行登録する"""
        key = (STACK_INIT_VAL, True)
        self.labels[key] = "STACK_INIT_ADDR"
        self.records[key] = Z80AddressRecord(
            STACK_INIT_VAL, "STACK_INIT_ADDR", STACK_INIT_VAL, is_code=False, is_work=True, is_bios=True
        )
        
        # MSXシステムの固定BIOSコールおよび主要システム変数アドレス一覧
        essential_addresses = [
            0x0138,  # RSLREG : スロットレジスタ読み込みBIOS
            0x0024,  # ENASLT : スロット切り替え実行BIOS
            0xFCC1,  # EXPTBL : 拡張スロット判定フラグテーブル（スロット0〜3）
            0xF37D,  # ROMBDOS: DISK-ROM BDOSコール中継フックアドレス
            0x00A2,  # CHPUT  : 1文字画面出力BIOS
            0x009F,  # CHGET  : 1文字入力待ちBIOS
            0x009C,  # CHSNS  : キー入力バッファ状態確認BIOS
            0x00C0,  # BEEP   : 警告ビープ音BIOS
            0x00A5   # LPTOUT : プリンタ1文字出力BIOS
        ]
        for addr in essential_addresses:
            self.register_bios_address(addr)

    def populate_segment_offsets(self, analyser=None):
        """再配置にあたり、CODE/WORK/DATAの各領域が占有する連続した物理サイズとオフセットを算出する。

        【累積オフセット（accumulated_delta）による補正の動作原理】
        ROM直接実行モード（通常モード）時、SMCパッチの適用やBDOS代替ルーチンの追加によって、
        元のバイナリ命令長と出力されるアセンブリ命令長との間にサイズ差分が生じます。
        （例: 2バイトのJR命令を9バイトのJP(HL)パッチへ置換すると +7バイト増加）
        後続のコードやラベルのアドレスにズレが発生しないよう、事前に展開後のバイトサイズを
        積算してオフセットマッピングを構築します。
        """
        self.code_byte_offsets.clear()
        self.work_byte_offsets.clear()
        self.data_byte_offsets.clear()

        # CODEセグメントの物理オフセット計算
        current_offset = 0
        accumulated_delta = 0

        pc = self.config.old_start
        while pc < self.config.old_end:
            if self.mem.has_attribute(pc, 'CODE'):
                delta = 0
                opcode = self.mem.get_byte(pc)
                
                # SMCパッチ（通常モードのみ適用）による命令長の変化量を計算
                if USE_SMC_PATCH and not COPY_CODE_TO_RAM and analyser is not None:
                    if pc in analyser.smc_patch_jr_addresses:
                        # 元のJR命令（2バイト）から JP (HL) パッチ（9バイト）への置換によるサイズ増加
                        delta = smc_patch_jr_code_jr_size - 2
                    elif (pc - 3) in analyser.smc_patch_jr_addresses:
                        # 元の LD (nn), A 命令（3バイト）をパッチ適用により削除（0バイト化）
                        delta = smc_patch_jr_code_ld_size - 3

                classifier = Z80OpcodeClassifier(self.mem, self)
                length, _, _ = classifier.decode_instruction(pc)
                
                # 展開後のサイズ増加分を加味してアドレスマッピングを登録
                for i in range(length):
                    addr = pc + i
                    if addr < self.config.old_end:
                        self.code_byte_offsets[addr] = current_offset + accumulated_delta + i
                
                accumulated_delta += delta
                current_offset += length
                pc += length
            else:
                pc += 1

        # 使用されているBDOS代替サブルーチン群の合計サイズを集計
        bdos_replace_routines_size = 0
        for fn_key, routine in BDOS_REPLACE_ROUTINES.items():
            if routine.get("used") is not None:
                bdos_replace_routines_size += routine["size"]
        self.bdos_rutine_size = bdos_replace_routines_size

        self.patch_delta_offset = accumulated_delta

        # CODEセグメントの最終占有合計サイズ
        self.total_code_size = current_offset + accumulated_delta + bdos_replace_routines_size

        # WORKセグメント（RAM上のワークエリア＋統合されたDATA）のオフセット計算
        current_offset = 0
        for pc in range(self.config.old_start, self.config.old_end):
            if ((self.mem.has_attribute(pc, 'WORK') or 
                    self.mem.has_attribute(pc, 'MERGE')) and
                    not self.mem.has_attribute(pc, 'CODE')):
                self.work_byte_offsets[pc] = current_offset
                current_offset += 1
        self.total_work_size = current_offset

        # DATAセグメント（ROM常駐データ）のオフセット計算
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
        """元のバイナリのアドレスを、選択された動作モードに応じた新しい物理アドレスへマッピング変換する"""
        # システムワークエリアおよびBIOS領域はアドレス変換を行わない
        if addr >= SYSYTEM_WORK:
            return addr

        if is_bios:
            return addr

        # WORKおよびMERGE属性のアドレス変換（Page 3 RAM領域へ配置）
        if (self.mem.has_attribute(addr, 'WORK') or 
                self.mem.has_attribute(addr, 'MERGE')):
            offset = self.work_byte_offsets.get(addr, 0)
            if COPY_CODE_TO_RAM:
                # RAMコピーモード時：RAMのCODE領域の直後に配置
                work_base = self.config.ram_start + self.total_code_size
            else:
                # 通常モード時：RAMの先頭アドレスに配置
                work_base = self.config.ram_start
            return work_base + offset

        # RAMコピーモード時のCODEおよびDATAのアドレス変換
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

        # 通常モード（ROM直接実行）時のCODEおよびDATAのアドレス変換
        if self.mem.has_attribute(addr, 'CODE') or self.mem.has_attribute(addr, 'DATA'):
            offset = addr - self.config.old_start
            return (self.config.rom_start + ROM_HEADER_SIZE + ENTRY_CODE_SIZE + offset)
        elif addr == self.config.old_start:
            return (self.config.rom_start + ROM_HEADER_SIZE)
        return addr

    def populate_instruction_map(self):
        """解析済みの全命令を走査し、各アドレスがどの命令の先頭に属しているかの逆引きマップを構築する"""
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
        """msx_symbolsモジュールを参照し、BIOSルーチンやシステム変数の公式シンボル名を検索する"""
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
        """システムBIOSや固定ワークエリアのアドレスをリロケート対象外（is_bios=True）として登録する"""
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
        """プログラム内部で使用されるCODE/DATA/WORKセグメントのアドレスに適切な識別ラベルを割り当てて登録する"""
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

        # アセンブラの予約語との名前衝突を防止するためのリスト
        reserved = ["SP", "IX", "IY", "PC", "AF", "BC", "DE", "HL", "A", "B", "C", "D", "E", "H", "L"]
        
        # 入力バイナリのメモリ範囲内のアドレスに対するラベル命名処理
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
            # バイナリ範囲外の外部参照アドレスに対するラベル命名処理
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
        """解析中に仮収集された未解決シンボル（unresolved_records）を正式にレジストリへ登録する"""
        for (addr, is_bios) in sorted(list(self.unresolved_records)):
            self.register_address(addr, is_bios=is_bios)

    def get_label(self, addr, default_val=None, is_code=False, is_bios=False):
        """指定アドレスに対応するラベル文字列を取得する。

        【命令内オフセット解決の動作原理】
        自己書き換えや特殊な間接参照によって、命令の先頭ではなく「命令の2バイト目（オペランド等）」
        が参照されている場合、単純なアドレス一致ではラベルが見つかりません。
        その場合、逆引きマップ（byte_to_instruction_start）を参照して命令の先頭ラベルを割り出し、
        「LABEL + offset」という相対表現のラベル文字列を自動生成して返却します。
        """
        if not is_bios and self.mem.has_attribute(addr, 'CODE'):
            is_code = True

        if addr < 0x100:
            is_bios = True # 0x0000〜0x00FF はシステムBIOSまたはBDOS共通領域

        # 特例処理: EXPTBL（スロット拡張テーブル）のベースアドレスに対する相対オフセット解決
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

        # 「命令の先頭アドレス + 相対オフセット」形式でのラベル解決
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
                                   self.mem.has_attribute(inst_start, 'MERGE'))
                        if is_work:
                            inst_label = f"WORK_{inst_start:04X}H"
                        else:
                            inst_label = f"DATA_{inst_start:04X}H"
                return f"{inst_label} + {offset}"

        if key in self.labels:
            return self.labels[key]
                
        return default_val


# =====================================================================
# Z80オペコード・レジスタビットフィールド解析補助関数群
# =====================================================================

def get_reg8_sss(opcode):
    """オペコードの下位3ビット (bit 2-0: SSSフィールド) から転送元8ビットレジスタ名を取得する。

    Z80の基本命令体系におけるレジスタエンコード：
      000: B,  001: C,  010: D,  011: E,  100: H,  101: L,  (110: (HL)),  111: A
    """
    return {0: "B", 1: "C", 2: "D", 3: "E", 4: "H", 5: "L", 7: "A"}.get(opcode & 0x7, "")

def get_reg8_ddd(opcode):
    """オペコードのビット5-3 (bit 5-3: DDDフィールド) から転送先8ビットレジスタ名を取得する。"""
    return get_reg8_sss(opcode >> 3)

def get_reg16_rp(opcode):
    """オペコードのビット5-4 (bit 5-4: RPフィールド) から16ビットレジスタペア名を取得する。

    汎用16ビットレジスタペアのエンコード：
      00: BC,  01: DE,  10: HL,  11: SP
    """
    return {0x00: "BC", 0x10: "DE", 0x20: "HL", 0x30: "SP"}.get(opcode & 0x30, "")

def get_reg16_af(opcode):
    """オペコードのビット5-4 (bit 5-4: PUSH/POP用RPフィールド) から16ビットレジスタペア名を取得する。

    PUSH/POP命令系におけるレジスタペアのエンコード（SPではなくAFが割り当てられる）：
      00: BC,  01: DE,  10: HL,  11: AF
    """
    return {0x00: "BC", 0x10: "DE", 0x20: "HL", 0x30: "AF"}.get(opcode & 0x30, "")


class Z80OpcodeClassifier:
    """Z80命令をオペコード単位でデコードし、命令長、分岐・参照ターゲットアドレス、命令種別を判別するクラス"""
    def __init__(self, mem: Z80MemoryImage, db: Z80AddressRegistry):
        """オペコード分類器の基本テーブルを初期化する"""
        self.mem = mem
        self.db = db

        # 1バイトで完結する主要命令のニーモニックマッピング（代表例）
        self.op_map_1byte = {
            0x00: "nop",        0xF3: "di",         0xFB: "ei",         0xC9: "ret",
            0x7E: "ld a, (hl)", 0x77: "ld (hl), a", 0x23: "inc hl",     0x13: "inc de",
            0x1C: "inc e",      0x1D: "dec e",      0x15: "dec d",      0x4F: "ld c, a",
            0x3C: "inc a",      0xB7: "or a"
        }
        
        # 8ビット即値データ (n) を後続に持つ2バイト命令のフォーマット定義
        self.op_map_2byte = {
            0x06: "ld b, {n}",    0x0E: "ld c, {n}",
            0x16: "ld d, {n}",    0x1E: "ld e, {n}",
            0x26: "ld h, {n}",    0x2E: "ld l, {n}",
            0x36: "ld (hl), {n}", 0x3E: "ld a, {n}",
            0xC6: "add a, {n}",   0xCE: "adc a, {n}",
            0xD6: "sub {n}",      0xDE: "sbc a, {n}",
            0xE6: "and {n}",      0xEE: "xor {n}",
            0xF6: "or {n}",       0xFE: "cp {n}"
        }
        
        # 16ビット絶対アドレス (nn) を後続に持つ3バイトジャンプ・コール命令
        self.op_map_3byte = {
            0xC3: "jp {nn}",      0xCD: "call {nn}"
        }

    def decode_instruction(self, pc):
        """プログラムカウンタ (PC) の指すアドレスから命令を切り出し、バイト長、分岐先・参照先アドレス、命令種別を返す。

        Z80アーキテクチャの全命令体系（標準命令、プレフィックス拡張命令、MSX拡張命令）を判定します。
        """
        opcode = self.mem.get_byte(pc)
        
        # --- プレフィックスコード（多バイト拡張命令）の分岐判定 ---
        if opcode == 0xED:
            # EDプレフィックス: 16ビット演算、拡張間接ロード、ブロック転送、I/O等の拡張命令群
            return self._decode_ed(pc)
        elif opcode == 0xCB:
            # CBプレフィックス: 8ビットレジスタに対するローテート・シフト・ビット操作命令群
            return self._decode_cb(pc)
        elif opcode == 0xDD:
            # DDプレフィックス: インデックスレジスタ IX による相対修飾命令群
            return self._decode_index(pc, "ix")
        elif opcode == 0xFD:
            # FDプレフィックス: インデックスレジスタ IY による相対修飾命令群
            return self._decode_index(pc, "iy")

        # --- MSX特有のインタースロットコール命令 (RST 30H) ---
        # オペコード F7H (RST 30H) に続き、1バイトのスロットIDと2バイトの転送先アドレスが配置される計4バイト命令。
        if opcode == 0xF7:
            return 4, None, "RST_30"

        # --- 相対ループ制御命令 (DJNZ e) ---
        # 0x10 (DJNZ e): Bレジスタをデクリメントし、B != 0 なら符号付き相対オフセット e (-128〜+127) へ分岐
        if opcode == 0x10:
            offset = self.mem.get_byte(pc + 1)
            if offset & 0x80:
                offset -= 256  # 2の補数として負のジャンプオフセットを計算
            target = (pc + 2 + offset) & 0xFFFF
            return 2, target, "DJNZ"

        # --- 無条件絶対アドレスジャンプおよびコール命令 (JP nn / CALL nn) ---
        # 0xC3: JP nn,  0xCD: CALL nn (計3バイト)
        if opcode in self.op_map_3byte:
            target = self.mem.get_word(pc + 1)
            return 3, target, "jp {nn}" if opcode == 0xC3 else "call {nn}"

        # --- 条件付き絶対ジャンプ命令 (JP cc, nn) ---
        # 0xC2 (NZ), 0xCA (Z), 0xD2 (NC), 0xDA (C), 0xE2 (PO), 0xEA (PE), 0xF2 (P), 0xFA (M)
        if opcode in [0xC2, 0xCA, 0xD2, 0xDA, 0xE2, 0xEA, 0xF2, 0xFA]:
            target = self.mem.get_word(pc + 1)
            return 3, target, "JP_COND"

        # --- 条件付きコール命令 (CALL cc, nn) ---
        # 0xC4 (NZ), 0xCC (Z), 0xD4 (NC), 0xDC (C), 0xE4 (PO), 0xEC (PE), 0xF4 (P), 0xFC (M)
        if opcode in [0xC4, 0xCC, 0xD4, 0xDC, 0xE4, 0xEC, 0xF4, 0xFC]:
            target = self.mem.get_word(pc + 1)
            return 3, target, "CALL_COND"

        # --- 相対ジャンプ命令 (JR cc, e / JR e) ---
        # 0x18: JR e (無条件)
        # 0x20: JR NZ, e,  0x28: JR Z, e,  0x30: JR NC, e,  0x38: JR C, e
        if opcode in [0x18, 0x20, 0x28, 0x30, 0x38]:
            offset = self.mem.get_byte(pc + 1)
            if offset & 0x80:
                offset -= 256  # 符号付き変位の計算
            target = (pc + 2 + offset) & 0xFFFF
            return 2, target, "JR"

        # --- アドレス直接メモリアクセス転送命令 (LD (nn), A / LD A, (nn) / LD (nn), HL / LD HL, (nn)) ---
        # 0x32: LD (nn), A,  0x3A: LD A, (nn),  0x22: LD (nn), HL,  0x2A: LD HL, (nn) (計3バイト)
        if opcode in [0x32, 0x22, 0x3A, 0x2A]:
            target = self.mem.get_word(pc + 1)
            return 3, target, "LD_MEM"

        # --- 16ビットレジスタペア即値ロード命令 (LD rp, nn) ---
        # 0x01: LD BC, nn,  0x11: LD DE, nn,  0x21: LD HL, nn,  0x31: LD SP, nn (計3バイト)
        if opcode in [0x01, 0x11, 0x21, 0x31]:
            val = self.mem.get_word(pc + 1)
            return 3, val, "LD_REG16"

        # --- 8ビット即値データ命令および直接I/O命令 (計2バイト) ---
        # LD r, n, ADD/ADC/SUB/SBC/AND/XOR/OR/CP A, n, OUT (n), A (0xD3), IN A, (n) (0xDB)
        len_map_2byte = list(self.op_map_2byte.keys()) + [0xD3, 0xDB]
        if opcode in len_map_2byte:
            return 2, None, "2BYTE"

        # --- 単一バイトで完結する標準命令 (計1バイト) ---
        # レジスタ間転送 (LD r, r')、単項演算、PUSH/POP、RET、単体フラグ操作など
        return 1, None, "1BYTE"

    def _decode_ed(self, pc):
        """EDプレフィックス拡張命令におけるアドレッシング形式および命令バイト長を判定する。"""
        sub_op = self.mem.get_byte(pc + 1)
        # 16ビットレジスタペアとメモリ直接参照のアドレス間転送命令 (計4バイト)
        # 0x43: LD (nn), BC,  0x53: LD (nn), DE,  0x63: LD (nn), HL (非公式), 0x73: LD (nn), SP
        # 0x4B: LD BC, (nn),  0x5B: LD DE, (nn),  0x6B: LD HL, (nn) (非公式), 0x7B: LD SP, (nn)
        if sub_op in [0x43, 0x53, 0x63, 0x73, 0x4B, 0x5B, 0x6B, 0x7B]:
            target = self.mem.get_word(pc + 2)
            return 4, target, "ED_LD"
        # その他のED拡張命令群 (計2バイト)
        # ブロック転送 (LDI, LDIR, LDD, LDDR)、ブロック比較 (CPI, CPIR, CPD, CPDR)、
        # 16ビット加減算 (ADC HL, rp / SBC HL, rp)、I/Oレジスタ間接 (IN r, (C) / OUT (C), r) など
        return 2, None, "ED_OTHER"

    def _decode_cb(self, pc):
        """CBプレフィックスビット操作命令の判定。

        ビットテスト (BIT b, r)、リセット (RES b, r)、セット (SET b, r)、
        およびシフト・ローテート命令 (RLC, RRC, RL, RR, SLA, SRA, SLL, SRL) は
        すべてプレフィックスを含めて一律2バイト固定長です。
        """
        return 2, None, "CB"

    def _decode_index(self, pc, reg):
        """DD/FDプレフィックス（IX/IYインデックスレジスタ修飾命令）のアドレッシング形式とバイト長を判定する。"""
        op = self.mem.get_byte(pc + 1)
        
        # 16ビット即値ロードおよび直接メモリアドレス参照命令 (計4バイト)
        # 0x21: LD IX/IY, nn
        # 0x22: LD (nn), IX/IY
        # 0x2A: LD IX/IY, (nn)
        if op in [0x21, 0x22, 0x2A]:
            val = self.mem.get_word(pc + 2)
            return 4, val, "INDEX_LD"

        # DDCB / FDCB プレフィックス複合命令 (計4バイト)
        # 命令形式: DD CB d sub_op (例: BIT b, (IX+d), RES b, (IX+d), SET b, (IX+d))
        # プレフィックス(1B) + CB(1B) + ディスプレースメント変位d(1B) + 操作オペコード(1B)
        if op == 0xCB:
            return 4, None, "INDEX_CB"

        # Z80命令体系における (HL) 間接参照ビットパターン (110b) の検出
        # レジスタフィールド bit 5-3 (転送先) または bit 2-0 (転送元) が 6 の場合、
        # DD/FD修飾により (IX+d) / (IY+d) のディスプレースメント付き間接参照となります。
        is_indirect_hl = (0x40 <= op <= 0xBF and (((op >> 3) & 7) == 6 or (op & 7) == 6))

        # ディスプレースメント d を伴うインデックス相対アドレッシング命令
        # 0x34: INC (IX/IY+d),  0x35: DEC (IX/IY+d),  0x36: LD (IX/IY+d), n
        if op in [0x34, 0x35, 0x36] or is_indirect_hl:
            # 0x36: LD (IX/IY+d), n は変位 d と即値 n を両方持つため計4バイト長
            if op == 0x36:
                return 4, None, "INDEX_WRITE_VAL"
            # LD r, (IX/IY+d) や ALU演算命令 (ADD/SUB/CP等) は計3バイト長
            return 3, None, "INDEX_LD_DISP"

        # プレフィックスに続く未ドキュメント命令（IXH, IXL, IYH, IYLレジスタの個別操作等）
        # 基本オペコード長 + プレフィックス1バイト
        length = 1 + get_standard_len(op)
        return length, None, "INDEX_OTHER"


class Z80FlowAnalyser:
    """プログラムの全実行経路を仮想CPUシミュレーションによって探索し、属性分類と自己書き換えコードを検出するクラス"""
    def __init__(self, config: Z80Config, mem: Z80MemoryImage):
        """解析器の内部状態トラッカーおよびデータ構造を初期化する"""
        self.config = config
        self.mem = mem
        self.db = None
        self.logger = None

        self.smc_detections = []            # 検出された自己書き換え (SMC) のリスト: (書き込み実行PC, 対象アドレス)
        self.smc_patch_jr_addresses = set() # SMCパッチ適用対象となるJR命令のアドレス集合

        self.unsupported_bdos_calls = []    # カートリッジROM単体では未サポートのBDOS呼び出し一覧

        self.traced_paths = set()           # 探索済み経路の追跡ハッシュセット（無限ループ防止用）

        self.sections = []                  # 解析結果により確定した連続セグメント範囲のリスト
        self.max_existing_ram = 0           # プログラムがアクセスしたRAM領域の最大アドレス
        self.bdos_fn_map = {}               # 各BDOSコール実行アドレスにおける機能番号 (Cレジスタ値) の対応マップ

        self.simple_pass = True

        # アドレスを格納するポインタ変数として実際に使用されたワークエリアのアドレス集合
        self.pointer_work_addresses = set()

        # レジスタ値および即値ロード元の追跡管理辞書
        self.register_tracker = {}
        # ワークエリアからレジスタへのロード状況追跡辞書: {レジスタ名: ワークエリアアドレス}
        self.memory_load_tracker = {}

        # ログメッセージの重複出力を抑制するための履歴セット
        self.logged_pointer_writes = set()
        self.logged_interrupt_hook_writes = set()

        # ポインタ（アドレス値）をレジスタへ即値ロードしている命令のPCアドレス集合
        self.pointer_load_commands = set()
        self.classifier = Z80OpcodeClassifier(self.mem, None)
        self.subroutine_pointer_usage_cache = {}

    def analyze_flow(self, db: Z80AddressRegistry, logger: Z80Logger):
        """プログラムの全実行経路をシミュレーション解析する。

        【2パス解析を実行する論理的必然性】
        Z80プログラムでは、ワークエリアに格納されたポインタを経由した間接アクセス
        （例: LD HL, (WORK_PTR); LD A, (HL)）が頻繁に使用されます。
        どのワークエリアがアドレスポインタとして機能しているかは、実際にコードを実行
        経路に沿ってシミュレートし、間接参照命令に到達するまで判明しません。
        そのため、以下の順序厳守の2段階（2パス）解析を行っています：

        手順 1 (Pass 1):
          プログラムの全分岐経路をシミュレーション走査し、命令実行によって参照される
          メモリアドレスの属性（CODE / DATA / WORK）を分類する。
          同時に、間接参照命令で使われたレジスタのロード元を逆引きし、ポインタ変数を保持
          しているワークエリアのアドレス（pointer_work_addresses）を完全に特定する。

        手順 2 (Pass 2):
          Pass 1 で特定された「ポインタ格納用ワークエリア」に対するアドレス値の代入箇所
          （LD (WORK_PTR), HL 等）を特定し、その元となった即値アドレスを確実にリロケート
          対象シンボルラベルとして登録する。
        """
        self.db = db
        self.logger = logger
        self.mem.reset_attributes(self.config.old_start, self.config.old_end)
            
        self.traced_paths.clear()
        self.subroutine_pointer_usage_cache.clear()
        self.pointer_work_addresses.clear()
        
        self.logged_pointer_writes.clear()
        self.logged_interrupt_hook_writes.clear()

        # 手順 1: Pass 1（属性分離およびポインタ格納用ワークエリアの検出）
        if self.logger is not None:
            self.logger.log("="*70)
            self.logger.log(center_text("解析 Pass 1 （CODE/DATA/WORK属性分け）を実行中...", 70))
            self.logger.log("="*70)
        self.analyze_flow_from_entries([self.config.old_start], db, logger, reset_sections=True, simple_pass=PASS1_USE_SIMPLE_PASS)

        # 手順 2: Pass 2（特定されたポインタワークへの即値代入命令の逆引き・シンボル確定）
        if self.logger is not None:
            self.logger.log("="*70)
            self.logger.log(center_text("解析 Pass 2 （分岐を含めた実行経路のシミュレート・分析）を実行中...", 70))
            self.logger.log("="*70)

        self.traced_paths.clear()
        self.analyze_flow_from_entries([self.config.old_start], db, logger, reset_sections=True)

    def _get_register_state_key(self, regs):
        """ポインタ追跡の分岐判定において、主要レジスタの即値ロード元PCをタプル化して状態キーを生成する"""
        return (
            regs['HL']['source_pc'],
            regs['DE']['source_pc'],
            regs['BC']['source_pc'],
            regs['IX']['source_pc'],
            regs['IY']['source_pc'],
        )

    def analyze_flow_from_entries(self, entries, db, logger, reset_sections=False, simple_pass=False):
        """指定されたエントリポイント一覧から実行パスをシミュレーション探索する"""
        self.db = db
        self.logger = logger
        self.simple_pass = simple_pass

        # シミュレーション用コンテキストスタック: 各分岐点における (PC, レジスタ状態, メモリ読み込み状態)
        stack = []
        for entry in entries:
            if entry in self.traced_paths:
                continue
            stack.append((entry, {
                'regs': {
                    # val       : 現在追跡されているレジスタの推定値
                    # source_pc : 当該レジスタに即値アドレスを代入した命令の実行PC
                    # source_val: 即値代入命令実行時点のロード値
                    'BC':  {'val': 0, 'source_pc': None, 'source_val': 0},
                    'DE':  {'val': 0, 'source_pc': None, 'source_val': 0},
                    'HL':  {'val': 0, 'source_pc': None, 'source_val': 0},
                    'IX':  {'val': 0, 'source_pc': None, 'source_val': 0},
                    'IY':  {'val': 0, 'source_pc': None, 'source_val': 0},
                    'A':   {'val': 0, 'source_pc': None, 'source_val': 0},
                    'B':   {'val': 0, 'source_pc': None, 'source_val': 0},
                    'C':   {'val': 0, 'source_pc': None, 'source_val': 0},
                    'D':   {'val': 0, 'source_pc': None, 'source_val': 0},
                    'E':   {'val': 0, 'source_pc': None, 'source_val': 0},
                    'H':   {'val': 0, 'source_pc': None, 'source_val': 0},
                    'L':   {'val': 0, 'source_pc': None, 'source_val': 0},
                    'IXH': {'val': 0, 'source_pc': None, 'source_val': 0},
                    'IXL': {'val': 0, 'source_pc': None, 'source_val': 0},
                    'IYH': {'val': 0, 'source_pc': None, 'source_val': 0},
                    'IYL': {'val': 0, 'source_pc': None, 'source_val': 0},
                },
                'mem_loads': {}  # ワークエリアのアドレスとロード先レジスタの対応マップ
            }))

        if reset_sections:
            self.traced_paths.clear()

        while stack:
            pc, tracker_state = stack.pop()
            
            # 入力バイナリのメモリ範囲外への分岐はシミュレートしない
            if not (self.config.old_start <= pc < self.config.old_end):
                continue

            if simple_pass:
                # 簡易探索モード: PCアドレスのみをキーにして探索の重複を防止
                path_key = pc
            else:
                # 詳細探索モード: PCアドレスと主要レジスタのロード元状態を組み合わせて重複判定
                state_key = self._get_register_state_key(tracker_state['regs'])
                path_key = (pc, state_key)
            if path_key in self.traced_paths:
                continue

            self.traced_paths.add(path_key)
            
            # 分岐先の退避情報からシミュレータのレジスタ状態をディープコピーして復元
            self.register_tracker = copy.deepcopy(tracker_state['regs'])
            self.memory_load_tracker = copy.deepcopy(tracker_state['mem_loads'])
            self._trace_instruction(pc, stack)

        if reset_sections:
            self.sections.clear()
        self._group_sections()

    def _check_subroutine_use(self, start_pc, target_reg):
        """サブルーチン内部で、引数として渡されたレジスタが値の上書き前にポインタ間接参照として使用されているか検査する"""
        visited = set()
        local_stack = [start_pc]
        
        while local_stack:
            pc = local_stack.pop()
            if pc in visited or not (self.config.old_start <= pc < self.config.old_end):
                continue
            visited.add(pc)
            
            opcode = self.mem.get_byte(pc)
            length, target, inst_type = self.classifier.decode_instruction(pc)
            
            # 対象レジスタが破壊（上書き代入）されたかどうかの判定
            is_overwritten = False
            if target_reg == "HL":
                # 0x21: LD HL, nn,  0x31: LD SP, nn,  0xE1: POP HL
                if inst_type == "LD_REG16" and opcode in [0x21, 0x31]:
                    is_overwritten = True
                elif opcode == 0xE1:
                    is_overwritten = True
            elif target_reg == "DE":
                # 0x11: LD DE, nn,  0xD1: POP DE
                if inst_type == "LD_REG16" and opcode == 0x11:
                    is_overwritten = True
                elif opcode == 0xD1:
                    is_overwritten = True
            elif target_reg == "BC":
                # 0x01: LD BC, nn,  0xC1: POP BC
                if inst_type == "LD_REG16" and opcode == 0x01:
                    is_overwritten = True
                elif opcode == 0xC1:
                    is_overwritten = True
                    
            if is_overwritten:
                continue
                
            # 対象レジスタを用いた間接メモリアクセス命令が存在するかの判定
            is_accessed = False
            if target_reg == "HL":
                # LD r, (HL) や LD (HL), r などの基本間接参照
                if 0x40 <= opcode <= 0x7F and opcode != 0x76:
                    if (opcode & 7) == 6 or (opcode & 0x38) == 0x30:
                        is_accessed = True
                # ALU A, (HL) 演算命令
                elif 0x80 <= opcode <= 0xBF and (opcode & 7) == 6:
                    is_accessed = True
                # EDプレフィックスによるブロック転送・比較命令群
                elif inst_type == "ED_OTHER":
                    sub_op = self.mem.get_byte(pc + 1)
                    # 0xB0: LDIR,  0xB8: LDDR
                    if sub_op in [0xB0, 0xB8]:
                        is_accessed = True
                    # CPI, CPIR, CPD, CPDR, INI, INIR, OUTI, OTIR, IND, INDR, OUTD, OTDR
                    elif sub_op in [0xA1, 0xA9, 0xB1, 0xB9, 0xA2, 0xB2, 0xAA, 0xBA, 0xA3, 0xB3, 0xAB, 0xBB]:
                        is_accessed = True
            elif target_reg == "DE":
                # 0x1A: LD A, (DE),  0x12: LD (DE), A
                if opcode in [0x1A, 0x12]:
                    is_accessed = True
                elif inst_type == "ED_OTHER":
                    sub_op = self.mem.get_byte(pc + 1)
                    # 0xB0: LDIR,  0xB8: LDDR (DEは転送先アドレスとしてアクセスされる)
                    if sub_op in [0xB0, 0xB8]:
                        is_accessed = True
            elif target_reg == "BC":
                # 0x0A: LD A, (BC),  0x02: LD (BC), A
                if opcode in [0x0A, 0x02]:
                    is_accessed = True
                    
            if is_accessed:
                return True
                
            if opcode == 0xC9:  # RET命令に達した分岐ルートは終了
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
    
    def _set_reg8_val(self, reg8, val, pc=None):
        """8ビットレジスタの追跡値を更新し、上位・下位を共有する親16ビットレジスタの値にも同期反映する"""
        self.register_tracker[reg8]['val'] = val
        if pc is not None:
            self.register_tracker[reg8]['source_val'] = val
            self.register_tracker[reg8]['source_pc'] = pc

        reg16t = None
        high = False
        if reg8[:2] in ['IX', 'IY']:
            reg16t = self.register_tracker[reg8[:2]]
            high = (reg8[2:3] == 'H')
        else:
            for rp in ['BC', 'DE', 'HL']:
                if reg8 in rp:
                    reg16t = self.register_tracker[rp]
                    high = (rp.find(reg8) == 0)
                    break

        if reg16t is not None:
            val16 = reg16t['val']
            if high:
                reg16t['val'] = (val << 8) | (val16 & 0xFF)
            else:
                reg16t['val'] = (val16 & 0xFF00) | val

    def _set_reg16_val(self, reg16, val, pc=None):
        """16ビットレジスタの追跡値を更新し、構成する上位8ビットおよび下位8ビットレジスタにも同期反映する"""
        self.register_tracker[reg16]['val'] = val
        if pc is not None:
            self.register_tracker[reg16]['source_val'] = val
            self.register_tracker[reg16]['source_pc'] = pc

        if reg16 == 'SP':
            return

        if reg16 in ['IX', 'IY']:
            reg8h = reg16 + 'H'
            reg8l = reg16 + 'L'
        else:
            reg8h = reg16[0]
            reg8l = reg16[1]
        self.register_tracker[reg8h]['val'] = val >> 8
        self.register_tracker[reg8l]['val'] = val & 0xFF
        if pc is not None:
            self.register_tracker[reg8h]['source_val'] = (val >> 8) & 0xFF
            self.register_tracker[reg8l]['source_val'] = val & 0xFF
            self.register_tracker[reg8h]['source_pc'] = pc
            self.register_tracker[reg8l]['source_pc'] = pc

    def _trace_instruction(self, pc, stack):
        """シミュレータ本体。現在PCの命令を実行し、レジスタ状態変化、メモリ参照・書き換え、分岐先を追跡する"""
        opcode = self.mem.get_byte(pc)
        length, target, inst_type = self.classifier.decode_instruction(pc)
        
        # 実行されたアドレス範囲をCODE属性としてマーク（DATA属性は破棄）
        for i in range(length):
            addr = pc + i
            if self.mem.is_valid_address(addr):
                self.mem.discard_attribute(addr, 'DATA')
                self.mem.mark_attribute(addr, 'CODE')
        
        # --- サブルーチン復帰命令の処理 ---
        # 0xC9: RET (無条件リターン)
        if opcode == 0xC9:
            return
        if opcode == 0xED:
            sub_op = self.mem.get_byte(pc + 1)
            # 0x45: RETN (ノンマスカブル割り込み復帰),  0x4D: RETI (割り込み復帰)
            if sub_op in [0x45, 0x4D]:
                return

        # --- レジスタ間接ジャンプ命令の処理 ---
        # 0xE9: JP (HL)
        if opcode == 0xE9:
            self._register_pointer_access("HL", pc)
            return
        # DD E9: JP (IX)
        elif opcode == 0xDD and self.mem.get_byte(pc + 1) == 0xE9:
            self._register_pointer_access("IX", pc)
            return
        # FD E9: JP (IY)
        elif opcode == 0xFD and self.mem.get_byte(pc + 1) == 0xE9:
            self._register_pointer_access("IY", pc)
            return

        # --- MSXインタースロットコール (RST 30H) の処理 ---
        # 0xF7: RST 30H に続く2バイトの呼び出し先BIOSアドレスを登録
        if opcode == 0xF7:
            target_bios = self.mem.get_word(pc + 2)
            if self.db is not None:
                self.db.register_bios_address(target_bios, pc)
            stack.append((pc + 4, {
                'regs': copy.deepcopy(self.register_tracker),
                'mem_loads': copy.deepcopy(self.memory_load_tracker)
            }))
            return

        # --- ワークエリアからレジスタへのロード状況を追跡 ---
        self._track_memory_loads(pc, opcode, inst_type)

        # --- レジスタへの即値およびレジスタ間データロード追跡 ---
        # 16ビットレジスタへの即値ロード命令 (LD rp, nn)
        if inst_type == "LD_REG16":
            reg = get_reg16_rp(opcode)
            if reg != "SP" and reg != "":
                self._set_reg16_val(reg, target, pc)
                self.memory_load_tracker.pop(reg, None)  # 即値が代入されたため、メモリからのロード履歴をクリア
        # インデックスレジスタ即値ロード: DD 21 nn (LD IX, nn)
        elif inst_type == "INDEX_LD" and opcode == 0xDD:
            self._set_reg16_val('IX', target, pc)
            self.memory_load_tracker.pop('IX', None)
        # インデックスレジスタ即値ロード: FD 21 nn (LD IY, nn)
        elif inst_type == "INDEX_LD" and opcode == 0xFD:
            self._set_reg16_val('IY', target, pc)
            self.memory_load_tracker.pop('IY', None)
        
        # 8ビットレジスタへの即値ロード命令 (LD r, n)
        # 0x06: LD B, n,  0x0E: LD C, n,  0x16: LD D, n,  0x1E: LD E, n
        # 0x26: LD H, n,  0x2E: LD L, n,  0x3E: LD A, n
        elif opcode in [0x06, 0x0E, 0x16, 0x1E, 0x26, 0x2E, 0x3E]:
            reg8 = get_reg8_ddd(opcode)
            if reg8 != "":
                val = self.mem.get_byte(pc + 1)
                self._set_reg8_val(reg8, val, pc)
            reg16 = get_reg16_rp(opcode)
            if reg16 != '' and reg16 != 'SP':
                self.memory_load_tracker.pop(reg16, None)
        # インデックスレジスタ上位/下位への即値ロード命令
        # DD 26 n: LD IXH, n,  DD 2E n: LD IXL, n,  FD 26 n: LD IYH, n,  FD 2E n: LD IYL, n
        elif inst_type == "INDEX_OTHER" and opcode in [0xDD, 0xFD]:
            op = self.mem.get_byte(pc + 1)
            if op is not None and op in [0x26, 0x2E]:
                reg16 = "IX" if opcode == 0xDD else "IY"
                reg8 = reg16 + get_reg8_ddd(op)
                val = self.mem.get_byte(pc + 2)
                self._set_reg8_val(reg8, val, pc)
                self.memory_load_tracker.pop(reg16, None)

        # 8ビットレジスタ間転送命令 (LD r, r')
        # 0x40〜0x7F（HALT 0x76 を除く）
        elif opcode in [
            0x40, 0x41, 0x42, 0x43, 0x44, 0x45, 0x47,  # LD B, r
            0x48, 0x49, 0x4A, 0x4B, 0x4C, 0x4D, 0x4F,  # LD C, r
            0x50, 0x51, 0x52, 0x53, 0x54, 0x55, 0x57,  # LD D, r
            0x58, 0x59, 0x5A, 0x5B, 0x5C, 0x5D, 0x5F,  # LD E, r
            0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x67,  # LD H, r
            0x68, 0x69, 0x6A, 0x6B, 0x6C, 0x6D, 0x6F,  # LD L, r
            0x78, 0x79, 0x7A, 0x7B, 0x7C, 0x7D, 0x7F,  # LD A, r
        ]:
            rd = self.register_tracker[get_reg8_ddd(opcode)]
            rs = self.register_tracker[get_reg8_sss(opcode)]
            rd['val'] = rs['val']
            rd['source_pc'] = rs['source_pc']

        # スタック復元命令 (POP rp)
        # 0xC1: POP BC,  0xD1: POP DE,  0xE1: POP HL,  0xF1: POP AF
        elif opcode in [0xC1, 0xD1, 0xE1, 0xF1]:
            self._stack_reg_transfer_tracker(opcode, pc)

        # レジスタ交換命令 (EX)
        elif opcode == 0x08:
            # 0x08: EX AF, AF' (裏レジスタの追跡は省略)
            pass
        elif opcode == 0xEB:
            # 0xEB: EX DE, HL (DEとHLのトラッキング情報を相互交換)
            hl = self.register_tracker['HL']
            de = self.register_tracker['DE']
            ml = self.memory_load_tracker
            hl['val'], de['val'] = de['val'], hl['val']
            hl['source_pc'], de['source_pc'] = de['source_pc'], hl['source_pc']
            ml['HL'], ml['DE'] = ml['DE'], ml['HL']
        elif opcode == 0xE3:
            # 0xE3: EX (SP), HL (スタックトップとHLの交換に伴い、HLの追跡情報をクリア)
            self._stack_reg_transfer_tracker(opcode, pc)

        # --- レジスタ演算による変化の追跡 ---
        self._track_calcukations(pc, opcode, inst_type)

        # --- メモリ書き込みおよびSMC（自己書き換え）の検出 ---
        self._track_writes(pc, opcode, inst_type)

        # --- 間接アドレッシング参照の検出と登録 ---
        # EDプレフィックスによるブロック転送命令
        if opcode == 0xED:
            sub_op = self.mem.get_byte(pc + 1)
            # 0xB0: LDIR,  0xB8: LDDR (タイマー割り込みフック書き換えの可能性があるか判定)
            if sub_op in [0xB0, 0xB8]:
                self._check_block_transfer_hook_write(pc)

        # (HL) 間接メモリアクセスの検出
        is_hl_mem_access = False
        if 0x40 <= opcode <= 0x7F and opcode != 0x76:
            # LD r, (HL) または LD (HL), r
            if (opcode & 7) == 6 or (opcode & 0x38) == 0x30:
                is_hl_mem_access = True
        elif 0x80 <= opcode <= 0xBF and (opcode & 7) == 6:
            # ALU A, (HL)
            is_hl_mem_access = True

        # CBプレフィックス命令における (HL) 間接アクセスの検出
        if opcode == 0xCB:
            sub_op = self.mem.get_byte(pc + 1)
            if (sub_op & 7) == 6:  # BIT b, (HL), RES b, (HL), SET b, (HL), シフト (HL)
                is_hl_mem_access = True

        if is_hl_mem_access:
            self._register_pointer_access("HL", pc)
        elif opcode in [0x0A, 0x02]:
            # 0x0A: LD A, (BC),  0x02: LD (BC), A
            self._register_pointer_access("BC", pc)
        elif opcode in [0x1A, 0x12]:
            # 0x1A: LD A, (DE),  0x12: LD (DE), A
            self._register_pointer_access("DE", pc)
        elif inst_type == "ED_OTHER":
            sub_op = self.mem.get_byte(pc + 1)
            # ブロック転送命令 (0xA0: LDI, 0xB0: LDIR, 0xA8: LDD, 0xB8: LDDR)
            if sub_op in [0xA0, 0xB0, 0xA8, 0xB8]:
                self._register_pointer_access("HL", pc)
                self._register_pointer_access("DE", pc)
            # ブロック比較・入出力命令 (CPI, CPIR, CPD, CPDR, INI, INIR, OUTI, OTIR 等)
            elif sub_op in [0xA1, 0xB1, 0xA9, 0xB9, 0xA2, 0xB2, 0xAA, 0xBA, 0xA3, 0xB3, 0xAB, 0xBB]:
                self._register_pointer_access("HL", pc)

        # IX / IY インデックス修飾による間接参照 ((IX+d) / (IY+d)) の検出
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

        # --- 分岐命令 (JP / CALL / JR / DJNZ) のスタック探索展開 ---
        is_jp_or_call = inst_type.startswith("jp") or inst_type.startswith("call")
        if is_jp_or_call:
            # MSXシステムBIOS CALSLT (001CH: スロット間コール) の特殊処理
            # CALSLT呼び出し時、IXレジスタに目的のルーチンアドレスが渡される
            if target == 0x001C:
                ix_state = self.register_tracker['IX']
                ix_val = ix_state['val']
                ix_source_pc = ix_state['source_pc']
                if ix_source_pc is not None:
                    self.pointer_load_commands.add(ix_source_pc)
                    if self.db is not None:
                        self.db.register_bios_address(ix_val, ix_source_pc)

            # MSX-DOSシステムコール (CALL 0005H) の解析
            if opcode == 0xCD and target == BDOS_CALL_ADDRESS:
                self._analyse_bdos_call(pc)
                # BDOSコール後はそのまま次の命令（pc + 3）へ進む
                stack.append((target, {
                    'regs': copy.deepcopy(self.register_tracker),
                    'mem_loads': copy.deepcopy(self.memory_load_tracker)
                }))
                return

            # リセットエントリ (0000H) へのジャンプ
            if target == 0x0000:
                stack.append((target, {
                    'regs': copy.deepcopy(self.register_tracker),
                    'mem_loads': copy.deepcopy(self.memory_load_tracker)
                }))
                return

            # サブルーチン呼び出し時、サブルーチン内部でポインタとして使用される引数レジスタを検査
            is_actual_call = (opcode == 0xCD) or (inst_type == "CALL_COND")
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
            
            # 分岐先アドレスを探索スタックに追加
            stack.append((target, {
                'regs': copy.deepcopy(self.register_tracker),
                'mem_loads': copy.deepcopy(self.memory_load_tracker)
            }))
            # CALL命令の場合は復帰アドレス (pc + 3) も探索対象に追加
            if opcode == 0xCD:
                stack.append((pc + 3, {
                    'regs': copy.deepcopy(self.register_tracker),
                    'mem_loads': copy.deepcopy(self.memory_load_tracker)
                }))
            
            # 連続するジャンプテーブル (JP nn の直後にさらに JP nn が続くパターン) の検出
            if SCAN_SEQUENTIAL_JP and opcode == 0xC3:
                next_pc = pc + 3
                if next_pc < self.config.old_end:
                    if self.mem.get_byte(next_pc) == 0xC3:
                        stack.append((next_pc, {
                            'regs': copy.deepcopy(self.register_tracker),
                            'mem_loads': copy.deepcopy(self.memory_load_tracker)
                        }))

            # 無条件ジャンプ 0xC3 (JP nn) の場合は直後のアドレスへのフォールスルーを行わない
            if opcode == 0xC3:
                return
            return

        elif inst_type in ["JP_COND", "CALL_COND"]:
            # 条件付きジャンプ・コールの場合は、条件成立時の分岐先と不成立時のフォールスルー（pc + 3）の両方を探索
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
            # 相対ジャンプ (JR cc, e / DJNZ e)
            stack.append((target, {
                'regs': copy.deepcopy(self.register_tracker),
                'mem_loads': copy.deepcopy(self.memory_load_tracker)
            }))
            # 0x18: JR e (無条件相対ジャンプ) であれば直後へのフォールスルーは行わない
            if opcode == 0x18:
                return
            # 条件付き相対ジャンプまたはDJNZの場合は分岐不成立時のアドレス (pc + 2) も探索
            stack.append((pc + 2, {
                'regs': copy.deepcopy(self.register_tracker),
                'mem_loads': copy.deepcopy(self.memory_load_tracker)
            }))
            return

        # 通常の非分岐命令：次の命令 (pc + length) へシミュレーションを進める
        stack.append((pc + length, {
            'regs': copy.deepcopy(self.register_tracker),
            'mem_loads': copy.deepcopy(self.memory_load_tracker)
        }))

    def _track_calcukations(self, pc, opcode, inst_type):
        """レジスタに対する算術演算を簡易エミュレートして値を追跡する（実験的機能）"""
        if not USE_REGISTER_CALCULATIONS:
            return

        # 16ビットレジスタ加減算
        # 0x03, 0x13, 0x23, 0x33: INC rp (BC, DE, HL, SP)
        if opcode in [0x03, 0x13, 0x23, 0x33]:
            reg16 = get_reg16_rp(opcode)
            if reg16 != "":
                val = self.register_tracker[reg16]['val']
                self._set_reg16_val(reg16, (val + 1) & 0xFFFF)
        # 0x05, 0x15, 0x25, 0x35: DEC rp
        elif opcode in [0x05, 0x15, 0x25, 0x35]:
            reg16 = get_reg16_rp(opcode)
            if reg16 != "":
                val = self.register_tracker[reg16]['val']
                self._set_reg16_val(reg16, (val - 1) & 0xFFFF)
        # 0x09, 0x19, 0x29, 0x39: ADD HL, rp
        elif opcode in [0x09, 0x19, 0x29, 0x39]:
            reg16 = get_reg16_rp(opcode)
            val = self.register_tracker['HL']['val']
            par = self.register_tracker[reg16]['val']
            self._set_reg16_val('HL', (val + par) & 0xFFFF)
        # インデックスレジスタ加減算
        elif opcode == 0xDD:
            sub_op = self.mem.get_byte(pc + 1)
            # DD 23: INC IX,  DD 2B: DEC IX
            if sub_op in [0x23, 0x2B]:
                val = self.register_tracker['IX']['val']
                diff = -1 if sub_op & 8 else 1
                self._set_reg16_val('IX', (val + diff) & 0xFFFF)
            # DD 09, 19, 29, 39: ADD IX, rp
            elif sub_op in [0x09, 0x19, 0x29, 0x39]:
                reg16 = get_reg16_rp(sub_op)
                val = self.register_tracker['IX']['val']
                par = self.register_tracker[reg16]['val']
                self._set_reg16_val('IX', (val + par) & 0xFFFF)
        elif opcode == 0xFD:
            sub_op = self.mem.get_byte(pc + 1)
            # FD 23: INC IY,  FD 2B: DEC IY
            if sub_op in [0x23, 0x2B]:
                val = self.register_tracker['IY']['val']
                diff = -1 if sub_op & 8 else 1
                self._set_reg16_val('IY', (val + diff) & 0xFFFF)
            # FD 09, 19, 29, 39: ADD IY, rp
            elif sub_op in [0x09, 0x19, 0x29, 0x39]:
                reg16 = get_reg16_rp(sub_op)
                val = self.register_tracker['IY']['val']
                par = self.register_tracker[reg16]['val']
                self._set_reg16_val('IY', (val + par) & 0xFFFF)

        # 8ビット演算によるレジスタ変化の追跡
        # 0x04: INC B,  0x0C: INC C,  0x14: INC D,  0x1C: INC E,  0x24: INC H,  0x2C: INC L,
        # 0x34: INC (HL), 0x3C: INC A, 0x4C: LD C, H (非公式命令・特殊パターンの追跡)
        elif opcode in [0x04, 0x0C, 0x14, 0x1C, 0x24, 0x2C, 0x34, 0x3C, 0x4C]: # inc r
            reg8 = get_reg8_ddd(opcode)
            reg16 = get_reg16_af(opcode)
            if reg8 != "":
                val = self.register_tracker[reg8]['val']
                self._set_reg8_val(reg8, (val + 1) & 0xFF)
        # 0x05: DEC B,  0x15: DEC D,  0x25: DEC H,  0x35: DEC (HL)
        elif opcode in [0x05, 0x15, 0x25, 0x35]: # dec rp
            reg8 = get_reg8_ddd(opcode)
            if reg8 != "":
                val = self.register_tracker[reg8]['val']
                self._set_reg8_val(reg8, (val - 1) & 0xFF)
        # 0xC6: ADD A, n (8ビット即値加算)
        elif opcode == 0xC6: # add a,n
            #self.memory_load_tracker.pop('A', None)
            reg8 = get_reg8_sss(opcode)
            val = self.register_tracker['A']['val']
            par = self.mem.get_byte(pc + 1)
            self._set_reg8_val('A', (val + par) & 0xFF)
        # 0xCE: ADC A, n (キャリー付き8ビット即値加算: 現状はキャリーフラグCY=0として簡易計算)
        elif opcode == 0xCE: # adc a,n
            #self.memory_load_tracker.pop('A', None)
            reg8 = get_reg8_sss(opcode)
            val = self.register_tracker['A']['val']
            par = self.mem.get_byte(pc + 1)
            cy = 0 # self.register_tracker['F']['val'] & 1
            self._set_reg8_val('A', (val + par + cy) & 0xFF)
        # 0x80〜0x87: ADD A, r (8ビットレジスタ加算: B, C, D, E, H, L, (HL), A)
        elif opcode in [0x80, 0x81, 0x82, 0x83, 0x84, 0x85, 0x87]: # add a, r
            #self.memory_load_tracker.pop('A', None)
            reg8 = get_reg8_sss(opcode)
            val = self.register_tracker['A']['val']
            par = self.register_tracker[reg8]['val']
            self._set_reg8_val('A', (val + par) & 0xFF)
        # 0x88〜0x8F: ADC A, r (キャリー付き8ビットレジスタ加算)
        elif opcode in [0x88, 0x89, 0x8A, 0x8B, 0x8C, 0x8D, 0x8F]: # adc a, r
            #self.memory_load_tracker.pop('A', None)
            reg8 = get_reg8_sss(opcode)
            val = self.register_tracker['A']['val']
            par = self.register_tracker[reg8]['val']
            cy = 0 # self.register_tracker['F']['val'] & 1
            self._set_reg8_val('A', (val + par + cy) & 0xFF)
        # DDプレフィックスによる未ドキュメント8ビット算術演算 (IXH, IXL との加算)
        # DD 84: ADD A, IXH / DD 85: ADD A, IXL / DD 8C: ADC A, IXH / DD 8D: ADC A, IXL
        elif opcode == 0xDD:
            sub_op = self.mem.get_byte(pc + 1)
            if sub_op in [0x84, 0x85, 0x8C, 0x8D]: # add a, ixh/ixl / adc
                #self.memory_load_tracker.pop('IX', None)
                reg8 = 'IX' + 'HL'[sub_op & 1]  # sub_opの最下位ビットで IXH(0) / IXL(1) を選択
                val = self.register_tracker['A']['val']
                par = self.register_tracker[reg8]['val']
                # sub_opの下位4ビットが 8より大きい(8CH, 8DH)なら ADC、それ以下(84H, 85H)なら ADD
                if (sub_op & 15) > 7:
                    self._set_reg8_val('A', (val + par) & 0xFF)
                else:
                    cy = 0 # self.register_tracker['F']['val'] & 1
                    self._set_reg8_val('A', (val + par + cy) & 0xFF)
        # FDプレフィックスによる未ドキュメント8ビット算術演算 (IYH, IYL との加算)
        # FD 84: ADD A, IYH / FD 85: ADD A, IYL / FD 8C: ADC A, IYH / FD 8D: ADC A, IYL
        elif opcode == 0xFD:
            sub_op = self.mem.get_byte(pc + 1)
            if sub_op in [0x84, 0x85, 0x8C, 0x8D]: # add a, iyh/iyl / adc
                #self.memory_load_tracker.pop('IY', None)
                reg8 = 'IY' + 'HL'[sub_op & 1]   # sub_opの最下位ビットで IYH / IYL を選択
                val = self.register_tracker['A']['val']
                par = self.register_tracker[reg8]['val']
                if (sub_op & 15) > 7:
                    self._set_reg8_val('A', (val + par) & 0xFF)
                else:
                    cy = 0 # self.register_tracker['F']['val'] & 1
                    self._set_reg8_val('A', (val + par + cy) & 0xFF)

    def _track_memory_loads(self, pc, opcode, inst_type):
        """ワークエリアからレジスタへのポインタ変数のロード命令を検出・追跡する"""
        # 0x2A: LD HL, (nn)
        if opcode == 0x2A:
            self.memory_load_tracker.pop('HL', None)
            target_work = self.mem.get_word(pc + 1)
            if self.config.old_start <= target_work < self.config.old_end:
                self.memory_load_tracker['HL'] = target_work
        # EDプレフィックスによる間接ロード命令
        elif opcode == 0xED:
            sub_op = self.mem.get_byte(pc + 1)
            target_work = self.mem.get_word(pc + 2)
            if self.config.old_start <= target_work < self.config.old_end:
                # ED 4B: LD BC, (nn)
                if sub_op == 0x4B:
                    self.memory_load_tracker.pop('BC', None)
                    self.memory_load_tracker['BC'] = target_work
                # ED 5B: LD DE, (nn)
                elif sub_op == 0x5B:
                    self.memory_load_tracker.pop('DE', None)
                    self.memory_load_tracker['DE'] = target_work
                # ED 6B: LD HL, (nn) (非公式命令)
                elif sub_op == 0x6B:
                    self.memory_load_tracker.pop('HL', None)
                    self.memory_load_tracker['HL'] = target_work
        # インデックスレジスタ間接ロード: DD 2A nn (LD IX, (nn)) / FD 2A nn (LD IY, (nn))
        elif opcode in [0xDD, 0xFD]:
            sub_op = self.mem.get_byte(pc + 1)
            target_work = self.mem.get_word(pc + 2)
            reg = 'IX' if opcode == 0xDD else 'IY'
            if sub_op == 0x2A and self.config.old_start <= target_work < self.config.old_end:
                self.memory_load_tracker.pop(reg, None)
                self.memory_load_tracker[reg] = target_work

    def _track_writes(self, pc, opcode, inst_type):
        """メモリへのデータストア命令を検出し、自己書き換え(SMC)や割り込みフック変更を追跡する"""
        # 0x22: LD (nn), HL
        if inst_type == "LD_MEM" and opcode == 0x22:
            target = self.mem.get_word(pc + 1)
            self._check_and_register_ram(target)
            self._check_interrupt_hook_write(target, "HL", pc)
            self._check_pointer_work_write(target, "HL", pc)
            self._mark_memory_write(target, pc)

        # EDプレフィックスによるメモリ直接ストア命令 (ED 43 / 53 / 63 / 73: LD (nn), rp)
        elif inst_type == "ED_LD":
            sub_op = self.mem.get_byte(pc + 1)
            target = self.mem.get_word(pc + 2)
            self._check_and_register_ram(target)
            # ED 43: LD (nn), BC
            if sub_op == 0x43:
                self._check_interrupt_hook_write(target, "BC", pc)
                self._check_pointer_work_write(target, "BC", pc)
            # ED 53: LD (nn), DE
            elif sub_op == 0x53:
                self._check_interrupt_hook_write(target, "DE", pc)
                self._check_pointer_work_write(target, "DE", pc)
            # ED 63: LD (nn), HL (非公式命令)
            elif sub_op == 0x63:
                self._check_interrupt_hook_write(target, "HL", pc)
                self._check_pointer_work_write(target, "HL", pc)
            if sub_op in [0x43, 0x53, 0x63, 0x73]:
                self._mark_memory_write(target, pc)

        # インデックスレジスタ直接ストア命令: DD 22 nn (LD (nn), IX) / FD 22 nn (LD (nn), IY)
        elif inst_type == "INDEX_LD":
            sub_op = self.mem.get_byte(pc + 1)
            if sub_op == 0x22:
                target = self.mem.get_word(pc + 2)
                self._check_and_register_ram(target)
                reg = "IX" if opcode == 0xDD else "IY"
                self._check_interrupt_hook_write(target, reg, pc)
                self._check_pointer_work_write(target, reg, pc)
                self._mark_memory_write(target, pc)

        # 0x32: LD (nn), A
        elif opcode == 0x32:
            target = self.mem.get_word(pc + 1)
            self._check_and_register_ram(target)
            self._check_split_accumulator_vector_write(target, pc)
            self._mark_memory_write(target, pc)

    def _check_pointer_work_write(self, target_work, reg_name, pc):
        """Pass 1で特定されたポインタ格納用WORKへの書き込みを検知し、ロード元のデータアドレスを抽出して登録する"""
        if target_work in self.pointer_work_addresses:
            reg_state = self.register_tracker[reg_name]
            source_pc = reg_state['source_pc']
            if source_pc is not None:
                source_val = reg_state['source_val']  # 即値ロード命令実行時のアドレス値
                if self.config.old_start <= source_val < self.config.old_end:
                    self.db.register_address(source_val, source_pc, is_code=False)
                    self.pointer_load_commands.add(source_pc)

                    log_key = (target_work, source_val, source_pc)
                    if log_key not in self.logged_pointer_writes:
                        self.logged_pointer_writes.add(log_key)
                        self.logger.log(
                            f"[+] 間接参照アドレス用WORKへの代入を検知: WORK: {format_hex(target_work)} "
                            f"<- ロード値: {format_hex(source_val)} "
                            f"(ロード位置: {format_hex(source_pc)}, WORK書込: {format_hex(pc)})"
                        )

    def _mark_memory_write(self, target, pc):
        """メモリへのデータ書き込みを記録し、CODE領域への書き込みであれば自己書き換え(SMC)として登録する"""
        self.mem.mark_attribute(target, 'WORK')
        self.mem.discard_attribute(target, 'DATA')

        # 書き込み対象アドレスがCODE属性を持つ、または命令の内部アドレスであれば自己書き換えと判定
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
            
            # 書き換え先アドレスおよびその命令の先頭アドレスの両方をシンボル登録
            if self.db is not None:
                self.db.register_address(target, pc, is_code=True, is_work=True)
                if target != inst_start:
                    self.db.register_address(inst_start, pc, is_code=True, is_work=False)

    def _analyse_bdos_call(self, pc):
        """BDOSコール (CALL 0005H) の呼び出し直前におけるCレジスタの値を特定し、機能番号を割り出す"""
        text_c = self.register_tracker['C']
        fn_code = None
        if text_c is not None:
            cmd_pc = text_c['source_pc']
            if cmd_pc is not None:
                opcode = self.mem.get_byte(cmd_pc)
                # 0x0E: LD C, n
                if opcode == 0x0E:
                    fn_code = self.mem.get_byte(cmd_pc + 1)
                # 0x01: LD BC, nn (下位バイトがCレジスタ)
                elif opcode == 0x01:
                    fn_code = self.mem.get_byte(cmd_pc + 1)
        self.bdos_fn_map[pc] = fn_code

        if fn_code is not None:
            if fn_code in BDOS_REPLACE_ROUTINES:
                BDOS_REPLACE_ROUTINES[fn_code]["used"] = True
            else:
                self.unsupported_bdos_calls.append({'pc': pc, 'fn': fn_code})
                BDOS_REPLACE_ROUTINES["UNSUPPORTED"]["used"] = True

    def _check_interrupt_hook_write(self, target, reg_name, pc):
        """MSXシステムの割り込みフック（H.TIMI: FDA0H, H.KEYI: FD9BH）へのハンドラアドレス書き換えを検出する"""
        if self.simple_pass:
            return  # 簡易探索パスではスキップ
        if target in [0xFDA0, 0xFD9B]:
            reg_state = self.register_tracker[reg_name]
            handler_addr = reg_state['val']
            source_pc = reg_state['source_pc']
            if handler_addr > 0 and self.config.old_start <= handler_addr < self.config.old_end:
                hook_name = "H.TIMI" if target == 0xFDA0 else "H.KEYI"
                
                log_key = (target, handler_addr, source_pc, pc)
                if log_key not in self.logged_interrupt_hook_writes:
                    self.logged_interrupt_hook_writes.add(log_key)
                    if self.db is not None:
                        # 割り込みハンドラ先をCODE属性としてシンボル登録
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
        """Aレジスタを用いたバイト単位のストア（LD (nn), A）による割り込みフック書き換えを検査する"""
        # FDA0H/FDA1H (H.TIMI: タイマー割り込み), FD9BH/FD9CH (H.KEYI: キー割り込み) の上位/下位バイトへの書き込みを検出
        if target in [0xFDA0, 0xFDA1, 0xFD9B, 0xFD9C]:
            # 書き込み先アドレスが属する割り込みフックの先頭ベースアドレスを算出
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
        """LDIR等のブロック転送命令によるシステム割り込みフック（0xFD9B〜0xFDA5）の一括書き換えを検出する"""
        de_val = self.register_tracker['DE']['val']
        hl_val = self.register_tracker['HL']['val']
        if (0xFD9B <= de_val <= 0xFDA5) and (self.config.old_start <= hl_val < self.config.old_end):
            try:
                # 転送元データから割り込みハンドラのアドレスを読み出して登録
                extracted_handler = self.mem.get_word(hl_val)
                if self.config.old_start <= extracted_handler < self.config.old_end:
                    if self.db is not None:
                        self.db.register_address(extracted_handler, pc, is_code=True)
            except IndexError:
                pass

    def _stack_reg_transfer_tracker(self, opcode, pc):
        """スタック操作 (POP / EX (SP), HL) に伴い、破壊されたレジスタの追跡情報をクリアする"""
        # 0xE1: POP HL,  0xE3: EX (SP), HL
        if opcode in [0xE1, 0xE3]:
            self.register_tracker['HL']['source_pc'] = None
            self.register_tracker['H']['source_pc'] = None
            self.register_tracker['L']['source_pc'] = None
            self.memory_load_tracker.pop('HL', None)
        # 0xD1: POP DE
        if opcode == 0xD1:
            self.register_tracker['DE']['source_pc'] = None
            self.register_tracker['D']['source_pc'] = None
            self.register_tracker['E']['source_pc'] = None
            self.memory_load_tracker.pop('DE', None)
        # 0xC1: POP BC
        if opcode == 0xC1:
            self.register_tracker['BC']['source_pc'] = None
            self.register_tracker['B']['source_pc'] = None
            self.register_tracker['C']['source_pc'] = None
            self.memory_load_tracker.pop('BC', None)
        # 0xF1: POP AF
        if opcode == 0xF1:
            self.register_tracker['A']['source_pc'] = None
        
        # インデックスレジスタのPOP
        # DD E1: POP IX
        if opcode == 0xDD:
            sub_op = self.mem.get_byte(pc + 1)
            if sub_op == 0xE1:
                self.register_tracker['IX']['source_pc'] = None
                self.register_tracker['IXH']['source_pc'] = None
                self.register_tracker['IXL']['source_pc'] = None
                self.memory_load_tracker.pop('IX', None)
        # FD E1: POP IY
        elif opcode == 0xFD:
            sub_op = self.mem.get_byte(pc + 1)
            if sub_op == 0xE1:
                self.register_tracker['IY']['source_pc'] = None
                self.register_tracker['IYH']['source_pc'] = None
                self.register_tracker['IYL']['source_pc'] = None
                self.memory_load_tracker.pop('IY', None)

    def _register_pointer_access(self, reg_name, pc):
        """間接メモリアクセス命令を検知した際、参照先アドレスに属性を付与し、ポインタWORKを登録する"""
        reg_state = self.register_tracker[reg_name]
        ptr_val = reg_state['val']
        source_cmd_pc = reg_state['source_pc']
        
        # 当該レジスタがワークエリアからロードされた値であれば、そのワークエリアを「ポインタ格納用WORK」として登録
        if reg_name in self.memory_load_tracker:
            source_work = self.memory_load_tracker[reg_name]
            if source_work not in self.pointer_work_addresses:
                self.pointer_work_addresses.add(source_work)
                self.logger.log(f"[*] アドレス格納用ワークエリアの検出: [{source_work:04X}H] ... reg: {reg_name} pc: {pc:04X}H")

        # レジスタが有効なアドレスを保持しており、ロード元命令が存在する場合
        if ptr_val > 0 and source_cmd_pc is not None:
            self.pointer_load_commands.add(source_cmd_pc)
            self._check_and_register_ram(ptr_val)
            if self.mem.has_attribute(ptr_val, 'CODE'):
                # 既にCODE属性があるアドレスへの参照はDATA属性へ更新
                self.mem.mark_attribute(ptr_val, 'DATA')
            else:
                # DEまたはBCによる書き込み先はWORK属性、それ以外はDATA属性を付与
                self.mem.mark_attribute(ptr_val, 'WORK' if reg_name in ["DE", "BC"] else 'DATA')

    def _check_and_register_ram(self, addr):
        """アクセスされたアドレスがシステム領域外のRAMであれば、使用最大RAMアドレスを更新する"""
        if addr < SYSYTEM_WORK:
            if addr > self.max_existing_ram:
                self.max_existing_ram = addr

    def _group_sections(self):
        """解析により判明したメモリアドレスごとの属性を、連続するセクション（SectionRange）として統合・整理する"""
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


# =====================================================================
# 参照シンボル事前走査クラス
# =====================================================================

class Z80SmartRelocator:
    """逆アセンブル前に命令を一巡走査して、必要なすべての参照先ラベルを仮登録するクラス"""
    def __init__(self, config: Z80Config, mem: Z80MemoryImage, db: Z80AddressRegistry, analyser: Z80FlowAnalyser):
        """スマートリロケータの解析環境参照を初期化する"""
        self.config = config
        self.mem = mem
        self.db = db
        self.analyser = analyser

    def get_context_is_bios(self, pc, addr, default_val=None):
        """参照元PCと対象アドレスの文脈から、そのアドレスがシステムBIOS/システムワークエリアに属するかを調べる"""
        if default_val is None:
            # 元バイナリデータの範囲外を指しているアドレスはリロケーション対象外（BIOS/外部参照）とする
            default_val = (addr < self.mem.config.old_start or addr >= self.mem.config.old_end)
        record = self.db.records.get((addr, True))
        if record is not None and record.references is not None:
            if pc in record.references:
                return record.is_bios
        return default_val

    def collect_symbols(self):
        """バイナリ内の全命令を走査して参照先アドレスを検出し、未解決シンボルリスト（unresolved_records）に追加する"""
        addr = self.config.old_start
        classifier = Z80OpcodeClassifier(self.mem, self.db)
        
        while addr < self.config.old_end:
            # CODE属性を持つ領域のみを命令として走査
            if not self.mem.has_attribute(addr, 'CODE'):
                addr += 1
                continue
            
            length, target, inst_type = classifier.decode_instruction(addr)
            
            # ポインタ（アドレス値）をロードしていると判定された命令か確認
            is_pointer_loader = addr in self.analyser.pointer_load_commands
            is_jp_or_call = inst_type.startswith("jp") or inst_type.startswith("call")
            is_target_bios = False
            if target is not None:
                is_target_bios = self.get_context_is_bios(addr, target)
            
            # 分岐命令（JP / CALL / JR / DJNZ）のジャンプ先を登録
            if is_jp_or_call or inst_type in ["JP_COND", "CALL_COND", "JR", "DJNZ"]:
                self.db.unresolved_records.add((target, is_target_bios))
            # メモリ直接アドレッシング命令（LD (nn), A / LD A, (nn) / LD (nn), HL 等）のアドレスを登録
            elif inst_type in ["LD_MEM", "ED_LD", "INDEX_CB"]:
                self.db.unresolved_records.add((target, is_target_bios))
            # 16ビット即値ロード命令のうち、ポインタとして使われているものを登録
            elif inst_type == "LD_REG16" and is_pointer_loader:
                self.db.unresolved_records.add((target, is_target_bios))
            # インデックスレジスタ即値ロード命令（LD IX/IY, nn）のうち、ポインタとして使われているものを登録
            elif inst_type == "INDEX_LD" and is_pointer_loader:
                self.db.unresolved_records.add((target, is_target_bios))
                
            addr += length


# =====================================================================
# Z80逆アセンブラクラス
# =====================================================================

class Z80Disassembler:
    """Z80の機械語データを、対応するアセンブリ言語テキスト表現に変換する逆アセンブラクラス"""
    def __init__(self, mem: Z80MemoryImage, db: Z80AddressRegistry, analyser: Z80FlowAnalyser, logger: Z80Logger):
        """逆アセンブラのレジスタマップおよび演算子テーブルを初期化する"""
        self.mem = mem
        self.db = db
        self.analyser = analyser
        self.logger = logger
        self.classifier = Z80OpcodeClassifier(self.mem, self.db)
        
        # 3ビットのレジスタ選択コード (000b〜111b) に対応する標準8ビットレジスタ名
        self.Z80_REG_MAP_8BIT = ["b", "c", "d", "e", "h", "l", "(hl)", "a"]
        
        # 3ビットの演算機能コードに対応する標準算術論理演算命令ニーモニック
        self.Z80_ALU_OPS_8BIT = ["add a,", "adc a,", "sub", "sbc a,", "and", "xor", "or", "cp"]

    def get_reg_8bit(self, reg_code, prefix_reg=None, d_str=""):
        """3ビットのレジスタコード値に基づき、適切なアセンブラオペランド文字列にデコードする。

        IX/IYプレフィックスが存在する場合の間接指定 ((ix+d), (iy+d))、および
        未ドキュメント命令における高位・低位部分レジスタ (ixh, ixl, iyh, iyl) へのマッピングを処理します。
        """
        # レジスタコード 110b = (HL) 間接参照
        if reg_code == 6:
            if prefix_reg is not None:
                return f"({prefix_reg.lower()}{d_str})"
            return "(hl)"
        
        # プレフィックス(IX/IY)修飾下で H(100b) または L(101b) が指定された場合、
        # 未ドキュメントの部分レジスタ（ixh, ixl, iyh, iyl）に置き換える
        if prefix_reg is not None:
            if reg_code == 4:   # Hレジスタフィールド -> ixh / iyh
                return f"{prefix_reg.lower()}h"
            elif reg_code == 5: # Lレジスタフィールド -> ixl / iyl
                return f"{prefix_reg.lower()}l"
                
        return self.Z80_REG_MAP_8BIT[reg_code]

    def get_context_is_bios(self, pc, addr, default_val=None):
        """参照元アドレスPCと参照先アドレスの属性情報から、システムBIOS/システムワークエリアに属するかを判定する"""
        if default_val is None:
            default_val = (addr < self.mem.config.old_start or SYSYTEM_WORK <= addr)
        record = self.db.records.get((addr, True))
        if record is not None and record.references is not None:
            if pc in record.references:
                return record.is_bios
        return default_val

    def decode_inst(self, pc, bdos_fn_map):
        """指定アドレスの機械語をデコードし、(命令バイト長, アセンブリ文字列) を生成する。

        SMCパッチの適用やBDOSコールの置換を行う場合でも、逆アセンブラの同期ずれを防ぐため
        「bytes_len」としては常に元の機械語のバイトサイズ（2や3）を返却します。
        """
        assert(bdos_fn_map is not None)
        opcode = self.mem.get_byte(pc)
        
        # === SMC (自己書き換えコード) に対するパッチ適用処理 ===
        # パターン1: JR命令のオペランド書き換え命令 (0x32: LD (nn), A) の削除
        if USE_SMC_PATCH and not COPY_CODE_TO_RAM and self.analyser is not None and (
            opcode == 0x32  # LD (nn), A 命令
            and (pc + 3) in self.analyser.smc_patch_jr_addresses
        ):
            target = self.mem.get_word(pc + 1)
            target_label = self.db.get_label(
                target, 
                format_asm_hex(self.relocator_translate(target, is_code=True, is_bios=False)), 
                is_code=True, 
                is_bios=False
            )
            patch_code = smc_patch_jr_code_ld.replace("target_label", target_label)
            return 3, patch_code
        
        # パターン2: 書き換え対象だったJR命令を、JP (HL) による動的ジャンプコードへ置換
        if USE_SMC_PATCH and not COPY_CODE_TO_RAM and self.analyser is not None and (
            pc in self.analyser.smc_patch_jr_addresses
        ):
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
            return 2, patch_code
        # ======================================================

        # === BDOSコールの置き換え処理 ===
        # CALL 0005H を検知し、対応するBIOS互換ルーチン（BDOS_SUB_xx）への呼び出しへ差し替える
        if opcode == 0xCD:
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

        # 無条件ジャンプ (0xC3: JP nn) および 無条件コール (0xCD: CALL nn)
        is_jp_or_call = inst_type.startswith("jp") or inst_type.startswith("call")
        if is_jp_or_call:
            label = self.db.get_label(target, format_asm_hex(self.relocator_translate(target, is_code=True, is_bios=is_target_bios)), is_code=True, is_bios=is_target_bios)
            inst = "jp" if opcode == 0xC3 else "call"
            return 3, f"{inst} {label}"

        # 条件付き絶対ジャンプ (JP cc, nn)
        if inst_type == "JP_COND":
            label = self.db.get_label(target, format_asm_hex(self.relocator_translate(target, is_code=True, is_bios=is_target_bios)), is_code=True, is_bios=is_target_bios)
            jp_conds = {0xC2: "nz", 0xCA: "z", 0xD2: "nc", 0xDA: "c", 0xE2: "po", 0xEA: "pe", 0xF2: "p", 0xFA: "m"}
            return 3, f"jp {jp_conds[opcode]}, {label}"

        # 条件付きコール (CALL cc, nn)
        if inst_type == "CALL_COND":
            label = self.db.get_label(target, format_asm_hex(self.relocator_translate(target, is_code=True, is_bios=is_target_bios)), is_code=True, is_bios=is_target_bios)
            call_conds = {0xC4: "nz", 0xCC: "z", 0xD4: "nc", 0xDC: "c", 0xE4: "po", 0xEC: "pe", 0xF4: "p", 0xFC: "m"}
            return 3, f"call {call_conds[opcode]}, {label}"

        # 相対ジャンプ (JR cc, e / JR e)
        if inst_type == "JR":
            offset = self.mem.get_byte(pc + 1)
            if offset & 0x80: offset -= 256
            dest_addr = pc + 2 + offset
            is_dest_bios = self.get_context_is_bios(pc, dest_addr)
            label = self.db.get_label(dest_addr, format_asm_hex(self.relocator_translate(dest_addr, is_code=True, is_bios=is_dest_bios)), is_code=True, is_bios=is_dest_bios)
            jr_names = {0x18: "jr", 0x20: "jr nz,", 0x28: "jr z,", 0x30: "jr nc,", 0x38: "jr c,"}
            return 2, f"{jr_names[opcode]} {label}"

        # 相対ループ制御命令 (DJNZ e)
        if inst_type == "DJNZ":
            offset = self.mem.get_byte(pc + 1)
            if offset & 0x80: offset -= 256
            dest_addr = pc + 2 + offset
            is_dest_bios = self.get_context_is_bios(pc, dest_addr)
            label = self.db.get_label(dest_addr, format_asm_hex(self.relocator_translate(dest_addr, is_code=True, is_bios=is_dest_bios)), is_code=True, is_bios=is_dest_bios)
            return 2, f"djnz {label}"

        # 直接メモリロード・ストア命令 (0x32, 0x3A, 0x22, 0x2A)
        if inst_type == "LD_MEM":
            label = self.db.get_label(target, format_asm_hex(self.relocator_translate(target, is_code=is_target_bios, is_bios=is_target_bios)), is_code=is_target_bios, is_bios=is_target_bios)
            if opcode == 0x32: return 3, f"ld ({label}), a"
            if opcode == 0x3A: return 3, f"ld a, ({label})"
            if opcode == 0x22: return 3, f"ld ({label}), hl"
            if opcode == 0x2A: return 3, f"ld hl, ({label})"

        # 16ビットレジスタ即値ロード命令 (0x01: BC, 0x11: DE, 0x21: HL, 0x31: SP)
        if inst_type == "LD_REG16":
            reg = {0x01: "bc", 0x11: "de", 0x21: "hl", 0x31: "sp"}[opcode]
            if is_pointer_loader:
                label = self.db.get_label(target, format_asm_hex(target), is_code=is_target_bios, is_bios=is_target_bios)
                return 3, f"ld {reg}, {label}"
            return 3, f"ld {reg}, {format_asm_hex(target)}"

        # EDプレフィックスによる16ビットレジスタ間接ロード・ストア命令
        if inst_type == "ED_LD":
            sub_op = self.mem.get_byte(pc + 1)
            label = self.db.get_label(target, format_asm_hex(target), is_code=is_target_bios, is_bios=is_target_bios)
            if sub_op in [0x43, 0x53, 0x63, 0x73]:
                reg = {0x43: "bc", 0x53: "de", 0x63: "hl", 0x73: "sp"}[sub_op]
                comment = " ; (undocumented)" if sub_op == 0x63 else ""
                return 4, f"ld ({label}), {reg}{comment}"
            reg = {0x4B: "bc", 0x5B: "de", 0x6B: "hl", 0x7B: "sp"}[sub_op]
            comment = " ; (undocumented)" if sub_op == 0x6B else ""
            return 4, f"ld {reg}, ({label}){comment}"

        # インデックスレジスタ即値ロード・直接メモリアクセス (DD / FD プレフィックス)
        if inst_type == "INDEX_LD":
            sub_op = self.mem.get_byte(pc + 1)
            reg = "ix" if opcode == 0xDD else "iy"
            if sub_op == 0x21:  # LD IX/IY, nn
                if is_pointer_loader:
                    label = self.db.get_label(target, format_asm_hex(target), is_code=is_target_bios, is_bios=is_target_bios)
                    return 4, f"ld {reg}, {label}"
                return 4, f"ld {reg}, {format_asm_hex(target)}"
            label = self.db.get_label(target, format_asm_hex(target), is_code=is_target_bios, is_bios=is_target_bios)
            if sub_op == 0x22:  # LD (nn), IX/IY
                return 4, f"ld ({label}), {reg}"
            return 4, f"ld {reg}, ({label})"  # LD IX/IY, (nn)

        # DDCB / FDCB 複合ビット操作命令群
        if inst_type == "INDEX_CB":
            prefix_reg = "ix" if opcode == 0xDD else "iy"
            d = self.mem.get_byte(pc + 2)
            sub_op = self.mem.get_byte(pc + 3)
            d_str = f"+0{d:02X}H" if d < 128 else f"-0{256-d:02X}H"
            
            operand = self.get_reg_8bit(6, prefix_reg, d_str)
            bit = (sub_op >> 3) & 7
            reg_code = sub_op & 7
            reg_name = self.Z80_REG_MAP_8BIT[reg_code]

            cb_ops = ["rlc", "rrc", "rl", "rr", "sla", "sra", "sll", "srl"]

            op_hex = format_asm_hex(opcode, 2)
            d_hex = format_asm_hex(d, 2)
            sub_hex = format_asm_hex(sub_op, 2)

            if 0x00 <= sub_op <= 0x3F:
                op_name = cb_ops[bit]
                if reg_code == 6:
                    if bit == 6:
                        return 4, f"db {op_hex}, 0CBH, {d_hex}, {sub_hex} ; sll {operand} (undocumented)"
                    return 4, f"{op_name} {operand}"
                else:
                    return 4, f"db {op_hex}, 0CBH, {d_hex}, {sub_hex} ; {op_name} {operand}, {reg_name} (undocumented)"
            elif 0x40 <= sub_op <= 0x7F:
                if reg_code == 6:
                    return 4, f"bit {bit}, {operand}"
                else:
                    return 4, f"db {op_hex}, 0CBH, {d_hex}, {sub_hex} ; bit {bit}, {operand} (undocumented)"
            elif 0x80 <= sub_op <= 0xBF:
                if reg_code == 6:
                    return 4, f"res {bit}, {operand}"
                else:
                    return 4, f"db {op_hex}, 0CBH, {d_hex}, {sub_hex} ; res {bit}, {operand}, {reg_name} (undocumented)"
            elif 0xC0 <= sub_op <= 0xFF:
                if reg_code == 6:
                    return 4, f"set {bit}, {operand}"
                else:
                    return 4, f"db {op_hex}, 0CBH, {d_hex}, {sub_hex} ; set {bit}, {operand}, {reg_name} (undocumented)"

        # 8ビット即値命令および直接I/Oポート命令
        if inst_type == "2BYTE":
            n_val = self.mem.get_byte(pc + 1)
            if opcode in self.classifier.op_map_2byte:
                return 2, self.classifier.op_map_2byte[opcode].format(n=format_asm_hex(n_val, 2))
            elif opcode == 0xD3:  # OUT (n), A
                return 2, f"out ({format_asm_hex(n_val, 2)}), a"
            elif opcode == 0xDB:  # IN A, (n)
                return 2, f"in a, ({format_asm_hex(n_val, 2)})"
            return 2, f"db {format_asm_hex(opcode, 2)}, {format_asm_hex(n_val, 2)}"

        # MSXインタースロットコール (0xF7: RST 30H)
        if inst_type == "RST_30":
            slot_id = self.mem.get_byte(pc + 1)
            addr_val = self.mem.get_word(pc + 2)
            label = self.db.get_label(addr_val, format_asm_hex(addr_val), is_code=True, is_bios=is_target_bios)
            return 4, f"rst 30H\n    db {format_asm_hex(slot_id, 2)}\n    dw {label}"

        # 1バイト標準命令のフォールバックデコード
        if inst_type == "1BYTE":
            return self._fallback_dissolve(pc, 1)

        # EDプレフィックス拡張命令
        if inst_type == "ED_OTHER":
            return self._decode_ed(pc)

        # DD / FD プレフィックスインデックス相対命令
        if inst_type in ["INDEX_OTHER", "INDEX_LD_DISP", "INDEX_WRITE_VAL"]:
            return self._decode_index(pc, "ix" if opcode == 0xDD else "iy")

        # CBプレフィックスビット操作命令
        if inst_type == "CB":
            return self._decode_cb(pc)

        return self._fallback_dissolve(pc, length)

    def relocator_translate(self, addr, is_code=False, is_bios=False):
        """指定アドレスを再配置先のアドレスへ変換する"""
        return self.db.translate_address(addr, is_code=is_code, is_bios=is_bios)

    def _fallback_dissolve(self, pc, length):
        """標準テーブルから漏れたZ80 1バイト命令をビットパターンに基づいてニーモニックへ変換する"""
        if length == 1:
            opcode = self.mem.get_byte(pc)
            one_byte_ops = {
                0x00: "nop",        0x07: "rlca",       0x0F: "rrca",       0x17: "rla",
                0x1F: "rra",        0x27: "daa",        0x2F: "cpl",        0x37: "scf",
                0x3F: "ccf",        0x76: "halt",       0xC9: "ret",        0xD9: "exx",
                0xE3: "ex (sp), hl",0xEB: "ex de, hl",  0xF3: "di",         0xFB: "ei",
                0xF9: "ld sp, hl",  0x09: "add hl, bc", 0x19: "add hl, de", 0x29: "add hl, hl",
                0x39: "add hl, sp", 0x08: "ex af, af'", 0x02: "ld (bc), a", 0x0A: "ld a, (bc)",
                0x12: "ld (de), a", 0x1A: "ld a, (de)"
            }
            if opcode in one_byte_ops:
                return 1, one_byte_ops[opcode]
            
            # PUSH命令: 0xC5: BC, 0xD5: DE, 0xE5: HL, 0xF5: AF
            regs_16 = {0xC5: "bc", 0xD5: "de", 0xE5: "hl", 0xF5: "af"}
            if opcode in regs_16: return 1, f"push {regs_16[opcode]}"
            
            # POP命令: 0xC1: BC, 0xD1: DE, 0xE1: HL, 0xF1: AF
            regs_16_p = {0xC1: "bc", 0xD1: "de", 0xE1: "hl", 0xF1: "af"}
            if opcode in regs_16_p: return 1, f"pop {regs_16_p[opcode]}"

            # INC / DEC 8ビットおよび16ビット命令
            inc_dec_r = {
                0x04: "inc b",  0x0C: "inc c",  0x14: "inc d",  0x1C: "inc e",
                0x24: "inc h",  0x2C: "inc l",  0x3C: "inc a",
                0x05: "dec b",  0x0D: "dec c",  0x15: "dec d",  0x1D: "dec e",
                0x25: "dec h",  0x2D: "dec l",  0x3D: "dec a",
                0x03: "inc bc", 0x13: "inc de", 0x23: "inc hl", 0x33: "inc sp",
                0x0B: "dec bc", 0x1B: "dec de", 0x2B: "dec hl", 0x3B: "dec sp"
            }
            if opcode in inc_dec_r: return 1, inc_dec_r[opcode]

            # 条件付きリターン命令 (RET cc)
            ret_conds = {0xC0: "nz", 0xC8: "z", 0xD0: "nc", 0xD8: "c", 0xE0: "po", 0xE8: "pe", 0xF0: "p", 0xF8: "m"}
            if opcode in ret_conds:
                return 1, f"ret {ret_conds[opcode]}"

            # 再始動命令 (RST p)
            if opcode in [0xC7, 0xCF, 0xD7, 0xDF, 0xE7, 0xEF, 0xFF]:
                rst_addr = opcode & 0x38
                return 1, f"rst {format_asm_hex(rst_addr, 2)}"

            # 8ビットレジスタ間転送命令 (LD r, r': 01xxxYYYb)
            if 0x40 <= opcode <= 0x7F and opcode != 0x76:
                dest = self.get_reg_8bit((opcode >> 3) & 7)
                src = self.get_reg_8bit(opcode & 7)
                return 1, f"ld {dest}, {src}"
                
            # 8ビット算術論理演算命令 (ALU A, r: 10xxxYYYb)
            if 0x80 <= opcode <= 0xBF:
                src = self.get_reg_8bit((opcode & 7))
                alu_op = self.Z80_ALU_OPS_8BIT[(opcode >> 3) & 7]
                return 1, f"{alu_op} {src}"

        # デコードできない不明バイト列は DB 疑似命令として出力
        tokens = []
        for i in range(length):
            tokens.append(format_asm_hex(self.mem.get_byte(pc + i), 2))
        return length, f"db {', '.join(tokens)}"

    def _decode_ed(self, pc):
        """EDプレフィックスに続く拡張命令のデコード処理"""
        sub_op = self.mem.get_byte(pc + 1)
        
        # 16ビットレジスタペアとメモリ直接参照のアドレス間転送命令
        if sub_op in [0x43, 0x53, 0x63, 0x73, 0x4B, 0x5B, 0x6B, 0x7B]:
            val = self.mem.get_word(pc + 2)
            is_target_bios = self.get_context_is_bios(pc, val)
            reg_map = {
                0x43: "bc", 0x53: "de", 0x63: "hl", 0x73: "sp",
                0x4B: "bc", 0x5B: "de", 0x6B: "hl", 0x7B: "sp"
            }
            reg = reg_map[sub_op]
            label = self.db.get_label(val, format_asm_hex(val), is_code=is_target_bios, is_bios=is_target_bios)
            comment = " ; (undocumented)" if sub_op in [0x63, 0x6B] else ""
            if sub_op in [0x43, 0x53, 0x63, 0x73]:
                return 4, f"ld ({label}), {reg}{comment}"
            return 4, f"ld {reg}, ({label}){comment}"

        # I/OポートCレジスタ間接入力 (IN r, (C)) および出力 (OUT (C), r) 命令
        if 0x40 <= sub_op <= 0x7F:
            reg_code = (sub_op >> 3) & 7
            reg_name = ["b", "c", "d", "e", "h", "l", "(c)", "a"][reg_code]
            
            if (sub_op & 7) == 0:  # IN r, (C)
                if reg_code == 6:  # 未ドキュメント命令: フラグ変化のみ行う IN (C)
                    return 2, "in (c)"
                return 2, f"in {reg_name}, (c)"
                
            elif (sub_op & 7) == 1:  # OUT (C), r
                if reg_code == 6:  # 未ドキュメント命令: ポート(C)に0を出力
                    return 2, "out (c), 0"
                return 2, f"out (c), {reg_name}"

        # ブロック転送、ブロック比較、符号反転、割り込みモード、16ビット加減算等の拡張命令
        ed_insts = {
            0x79: "out (c), a", 0x78: "in a, (c)",
            0x47: "ld i, a",    0x57: "ld a, i",    0x4F: "ld r, a",    0x5F: "ld a, r",
            0x67: "rrd",        0x6F: "rld",
            0xA0: "ldi",        0xA1: "cpi",        0xA2: "ini",        0xA3: "outi",
            0xB0: "ldir",       0xB1: "cpir",       0xB2: "inir",       0xB3: "otir",
            0xA8: "ldd",        0xA9: "cpd",        0xAA: "ind",        0xAB: "outd",
            0xB8: "lddr",       0xB9: "cpdr",       0xBA: "indr",       0xBB: "otdr",
            0x44: "neg",        0x4C: "neg ; (undocumented)", 0x54: "neg ; (undocumented)",
            0x5C: "neg ; (undocumented)", 0x64: "neg ; (undocumented)", 0x6C: "neg ; (undocumented)",
            0x74: "neg ; (undocumented)", 0x7C: "neg ; (undocumented)",
            0x45: "retn",       0x55: "retn ; (undocumented)", 0x65: "retn ; (undocumented)", 0x75: "retn ; (undocumented)",
            0x4D: "reti",       0x5D: "reti ; (undocumented)", 0x6D: "reti ; (undocumented)", 0x7D: "reti ; (undocumented)",
            0x46: "im 0",       0x56: "im 1",       0x5E: "im 2",
            0x4E: "im 0 ; (undocumented)", 0x66: "im 0 ; (undocumented)", 0x6E: "im 0 ; (undocumented)",
            0x76: "im 1 ; (undocumented)", 0x7E: "im 2 ; (undocumented)",
            0x42: "sbc hl, bc", 0x52: "sbc hl, de", 0x62: "sbc hl, hl", 0x72: "sbc hl, sp",
            0x4A: "adc hl, bc", 0x5A: "adc hl, de", 0x6A: "adc hl, hl", 0x7A: "adc hl, sp"
        }
        if sub_op in ed_insts:
            return 2, ed_insts[sub_op]
        return 2, f"db 0EDH, {format_asm_hex(sub_op, 2)}"

    def _decode_cb(self, pc):
        """CBプレフィックスビット操作・シフト命令のデコード"""
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
        elif 0x30 <= sub_op <= 0x37: cb_inst = f"sll {reg}" # 論理左シフト（非公式: 最下位ビットに1が入る）
        elif 0x38 <= sub_op <= 0x3F: cb_inst = f"srl {reg}" # 論理右シフト
        elif 0x40 <= sub_op <= 0x7F: cb_inst = f"bit {bit}, {reg}" # ビットテスト
        elif 0x80 <= sub_op <= 0xBF: cb_inst = f"res {bit}, {reg}" # ビットリセット
        elif 0xC0 <= sub_op <= 0xFF: cb_inst = f"set {bit}, {reg}" # ビットセット
        
        return 2, cb_inst

    def _decode_index(self, pc, reg_name):
        """DD/FDプレフィックスを伴うインデックスアドレス命令のデコード"""
        reg = reg_name.lower()
        op = self.mem.get_byte(pc + 1)
        
        is_pointer_loader = pc in self.analyser.pointer_load_commands
        
        # 16ビット即値ロード (LD IX/IY, nn)
        if op == 0x21:  
            val = self.mem.get_word(pc + 2)
            is_target_bios = self.get_context_is_bios(pc, val)
            if is_pointer_loader:
                label = self.db.get_label(val, format_asm_hex(val), is_code=is_target_bios, is_bios=is_target_bios)
                return 4, f"ld {reg}, {label}"
            return 4, f"ld {reg}, {format_asm_hex(val)}"
            
        # 16ビットストア (LD (nn), IX/IY)
        if op == 0x22:  
            val = self.mem.get_word(pc + 2)
            is_target_bios = self.get_context_is_bios(pc, val)
            label = self.db.get_label(val, format_asm_hex(val), is_code=is_target_bios, is_bios=is_target_bios)
            return 4, f"ld ({label}), {reg}"
            
        # 16ビットロード (LD IX/IY, (nn))
        if op == 0x2A:  
            val = self.mem.get_word(pc + 2)
            is_target_bios = self.get_context_is_bios(pc, val)
            label = self.db.get_label(val, format_asm_hex(val), is_code=is_target_bios, is_bios=is_target_bios)
            return 4, f"ld {reg}, ({label})"

        # インデックス加算命令 (ADD IX/IY, rp)
        if op in [0x09, 0x19, 0x29, 0x39]:
            r_pair = {0x09: "bc", 0x19: "de", 0x29: reg, 0x39: "sp"}[op]
            return 2, f"add {reg}, {r_pair}"

        # (IX+d) / (IY+d) の相対アドレッシング判定
        is_indirect_hl = (0x40 <= op <= 0xBF and (((op >> 3) & 7) == 6 or (op & 7) == 6))

        # ディスプレースメントを伴うインデックス相対命令
        if op in [0x34, 0x35, 0x36] or is_indirect_hl: 
            d = self.mem.get_byte(pc + 2)
            d_str = "+00H" if d == 0 else (f"+0{d:02X}H" if d < 128 else f"-0{256-d:02X}H")
            target_reg = self.get_reg_8bit(6, reg, d_str)
            if op == 0x34: return 3, f"inc {target_reg}"
            if op == 0x35: return 3, f"dec {target_reg}"
            if op == 0x36: return 4, f"ld {target_reg}, {format_asm_hex(self.mem.get_byte(pc + 3), 2)}"

            # LD r, (IX/IY+d)
            if 0x40 <= op <= 0x7F and op != 0x76:
                dest = self.get_reg_8bit((op >> 3) & 7, reg, d_str)
                src = self.get_reg_8bit(op & 7, reg, d_str)
                return 3, f"ld {dest}, {src}"
            # ALU A, (IX/IY+d)
            if 0x80 <= op <= 0xBF:
                src = self.get_reg_8bit(op & 7, reg, d_str)
                alu_op = self.Z80_ALU_OPS_8BIT[(op >> 3) & 7]
                return 3, f"{alu_op} {src}"

        # プレフィックス修飾付き・ディスプレースメント無しの命令（非公式命令含む）
        length = 1 + get_standard_len(op)
        pfx_byte = self.mem.get_byte(pc)

        if 0x40 <= op <= 0x7F and op != 0x76:
            d_idx = (op >> 3) & 7
            s_idx = op & 7
            dest = self.get_reg_8bit(d_idx, reg)
            src = self.get_reg_8bit(s_idx, reg)
            if d_idx in [4, 5] or s_idx in [4, 5]:
                return length, f"ld {dest}, {src} ; (undocumented)"
            return length, f"db {format_asm_hex(pfx_byte, 2)}, {format_asm_hex(op, 2)} ; ld {dest}, {src} (undocumented: prefix ignored)"

        if op == 0x24: return length, f"inc {reg}h ; (undocumented)"
        if op == 0x2C: return length, f"inc {reg}l ; (undocumented)"
        if op == 0x25: return length, f"dec {reg}h ; (undocumented)"
        if op == 0x2D: return length, f"dec {reg}l ; (undocumented)"

        if op in [0x26, 0x2E]:
            dest = self.get_reg_8bit((op >> 3) & 7, reg)
            n_val = self.mem.get_byte(pc + 2)
            return length, f"ld {dest}, {format_asm_hex(n_val, 2)} ; (undocumented)"

        if op in [0x06, 0x0E, 0x16, 0x1E, 0x3E]:
            dest = self.Z80_REG_MAP_8BIT[(op >> 3) & 7]
            n_val = self.mem.get_byte(pc + 2)
            return length, f"db {format_asm_hex(pfx_byte, 2)}, {format_asm_hex(op, 2)}, {format_asm_hex(n_val, 2)} ; ld {dest}, {format_asm_hex(n_val, 2)} (undocumented: prefix ignored)"

        # IXH / IXL を用いた算術演算命令（非公式命令）
        if 0x80 <= op <= 0xBF:
            s_idx = op & 7
            src = self.get_reg_8bit(s_idx, reg)
            alu_op = self.Z80_ALU_OPS_8BIT[(op >> 3) & 7]
            if s_idx in [4, 5]:
                return length, f"{alu_op} {src} ; (undocumented)"
            return length, f"db {format_asm_hex(pfx_byte, 2)}, {format_asm_hex(op, 2)} ; {alu_op} {src} (undocumented: prefix ignored)"

        tokens = []
        for i in range(length):
            tokens.append(format_asm_hex(self.mem.get_byte(pc + i), 2))
        return length, f"db {', '.join(tokens)}"


# =====================================================================
# アセンブリ出力生成クラス
# =====================================================================

class TransferBlock:
    """ROMからRAMへ起動時に一括転送（LDIR）するメモリブロックの情報を保持する構造体"""
    def __init__(self, src_label, dest_label, size_val):
        """転送元ラベル（ROM側）、転送先ラベル（RAM側）、転送バイトサイズを初期化する"""
        self.src_label = src_label
        self.dest_label = dest_label
        self.size_val = size_val


class Z80OutputGenerator:
    """解析結果に基づき、再配置済みアセンブリソースコードファイルを生成するクラス"""
    def __init__(self, config: Z80Config, mem: Z80MemoryImage, db: Z80AddressRegistry, analyser: Z80FlowAnalyser, decoder: Z80Disassembler, logger: Z80Logger):
        """アセンブリ出力生成器を初期化する"""
        self.config = config
        self.mem = mem
        self.db = db
        self.decoder = decoder
        self.logger = logger
        self.analyser = analyser

    def write_assembly_file(self):
        """解析結果を統合し、指定されたアセンブラ形式のソースコードを出力する"""
        self.logger.log(f"[*] アセンブリコードをASMファイル '{self.config.output_asm}' へ出力中...")
        
        transfer_blocks = []
        
        # WORKおよびMERGE領域の初期化データをROMからRAMへ転送するためのブロックを抽出
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

        # RAMコピーモード有効時は、先頭に全CODEブロックの転送定義を挿入
        if COPY_CODE_TO_RAM:
            transfer_blocks.insert(0, TransferBlock(
                src_label="ROM_CODE_DATA_START",
                dest_label="RAM_BASE",
                size_val=self.db.total_code_size
            ))

        with open(self.config.output_asm, 'w') as out:
            out.write(";===================================================================\n")
            out.write(f"; COM\"{INPUT_PATH}\" to ROM\"{OUTPUT_ASM_PATH}\" 自動リロケートソースコード\n")
            out.write(";===================================================================\n\n")

            # システム定数のEQU定義
            out.write(";=== SYSTEM PARAMETERS ===\n")
            out.write(f"ROM_BASE            EQU {format_asm_hex(self.config.rom_start)}\n")
            out.write(f"RAM_BASE            EQU {format_asm_hex(self.config.ram_start)}\n\n")

            # BIOS / システムワーク等の外部シンボル定義
            all_external_addrs = []
            for (addr, is_bios), label_name in self.db.labels.items():
                if addr < self.config.old_start or is_bios:
                    all_external_addrs.append((addr, is_bios, label_name))

            for ext_addr, is_bios, label_name in sorted(all_external_addrs, key=lambda x: (x[0], x[1])):
                out.write(f"{label_name:18} EQU {format_asm_hex(ext_addr)}\n")
            out.write("\n")

            # RAM上に配置されるWORK変数のEQU定義
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
                out.write("EXEC_ADDRESS       EQU RAM_BASE             ; RAM転送後の実行開始アドレス\n\n")
            else:
                entry_target = self.config.old_start
                entry_label = self.db.get_label(entry_target, f"CODE_{entry_target:04X}H", is_code=True, is_bios=False)
                out.write(f"EXEC_ADDRESS       EQU {entry_label}    ; ROM直接実行時の開始アドレス\n\n")

            out.write("    ORG ROM_BASE\n")
            out.write(ROM_HEADER)
            out.write(ENTRY_CODE)

            out.write(";===================================================================\n")
            out.write("; APPLICATION SECTION \n")
            out.write(";===================================================================\n")
            
            # RAMコピーモード時のアセンブラ別RAM配置ディレクティブ
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
            
            # 自己書き換え検出情報のマップ化
            smc_map = {}
            smc_target_inst_map = {}
            for src_pc, target_addr in self.analyser.smc_detections:
                if src_pc != target_addr:
                    smc_map[src_pc] = target_addr
                    smc_target_inst_map[self.db.byte_to_instruction_start[target_addr]] = src_pc

            # メインコードの逆アセンブル出力ループ
            while pc < self.config.old_end:
                key_code = (pc, False)
                key_data = (pc, False)
                
                # 行頭ラベルの出力判定
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
                        # WORK属性の初期データ配置は、RAMアドレスとの名前衝突を防ぐため INIT_ プレフィックスを付与
                        label_name = self.db.labels.get(key_data)
                        if label_name and not COPY_CODE_TO_RAM:
                            if self.mem.has_attribute(pc, 'WORK'):
                                label_name = f"INIT_WORK_{pc:04X}H"
                            elif self.mem.has_attribute(pc, 'MERGE'):
                                label_name = f"INIT_DATA_{pc:04X}H"
                            out.write(f"\n{label_name}:\n")

                # 命令コードの逆アセンブルテキスト出力
                if self.mem.has_attribute(pc, 'CODE'):
                    bytes_len, inst_str = self.decoder.decode_inst(pc, bdos_fn_map)
                    
                    # 自己書き換えに関する警告コメントの付与
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
                    # RAMコピーモード時はCODEのみを先に出力するため、非CODEバイトはスキップ
                    pc += 1
                else:
                    # 通常モード時は非コードデータをDB疑似命令として出力
                    pc = self._write_db_sequence(pc, out)

            # === 使用されたBDOS代替サブルーチン群の出力 ===
            out.write("\n;===================================================================\n")
            out.write("; BDOS 代替処理サブルーチン\n")
            out.write(";===================================================================\n")
            for fn_key, routine in BDOS_REPLACE_ROUTINES.items():
                if routine.get("used") is not None:
                    out.write(routine["code"] + "\n")

            # RAMコピーモード時の静的データセクション出力
            if COPY_CODE_TO_RAM:
                out.write("\nROM_CODE_DATA_END:\n\n")
                if ASSEMBLER_TYPE == 1:
                    out.write("    .dephase\n\n")
                else:
                    out.write("ROM_CODECONTINUE EQU STARTUP_END + (ROM_CODE_DATA_END - RAM_BASE)\n")
                    out.write("    ORG ROM_CODECONTINUE, (STARTUP_END - ROM_BASE) + (ROM_CODE_DATA_END - RAM_BASE)\n\n")

                out.write("\n;===================================================================\n")
                out.write("; STATIC DATA SECTION (ROM常駐静的データ)\n")
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

            # === RAM転送テーブルの出力 ===
            out.write("\n;===================================================================\n")
            out.write("; RAM初期化転送テーブル (HL=転送元, DE=転送先, BC=サイズ)\n")
            out.write(";===================================================================\n")
            out.write("RAM_TRANSFER_TABLE:\n")
            for block in transfer_blocks:
                out.write(f"    dw {block.src_label:24}, {block.dest_label:24}, {format_asm_hex(block.size_val)}\n")
            out.write("    dw 0000H                   , 0000H                   , 0000H       ; 終端マーク\n\n")

            out.write("    END\n")

    def _write_db_sequence(self, pc, out):
        """非コード領域の連続するバイト列を、ラベル境界を考慮しながら DB 疑似命令として書き出す"""
        db_bytes = []
        temp_pc = pc
        while temp_pc < self.config.old_end:
            # 命令コード領域に到達した場合は中断
            if self.mem.has_attribute(temp_pc, 'CODE'):
                break
            # 1行あたり最大16バイトで改行
            if len(db_bytes) >= 16:
                break
            # 行の途中にラベルが定義されている場合はそこで行を分割
            if temp_pc != pc and ((temp_pc, False) in self.db.labels or (temp_pc, True) in self.db.labels):
                break
            db_bytes.append(self.mem.get_byte(temp_pc))
            temp_pc += 1
            
        # 最低1バイトは処理を進めるためのフォールバック
        if temp_pc == pc:
            db_bytes.append(self.mem.get_byte(temp_pc))
            temp_pc += 1

        hex_tokens = [f"{format_asm_hex(b, 2)}" for b in db_bytes]
        out.write(f"    DB {', '.join(hex_tokens)}\n")
        return temp_pc


# =====================================================================
# メイン実行制御クラス
# =====================================================================

class MsxComToRomRelocator:
    """COMファイルをMSX用カートリッジROMバイナリ形式にリロケート・逆アセンブルするメイン実行クラス"""
    def __init__(self):
        """各解析・生成モジュールのインスタンスを生成して初期化する"""
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
        """リロケーションおよび逆アセンブルの全解析パイプラインを実行する。

        【実行順序の重要性】
        本パイプラインは各処理の依存関係が極めて強く、実行順序が結果の成否を左右します。
        """
        global COPY_CODE_TO_RAM

        # 手順 1: 入力ファイル（バイナリまたは16進ダンプ）の読み込み
        if not self.mem.load_file():
            return

        # 手順 2: プログラム実行経路のシミュレーション（Pass 1: 属性分類 ＆ Pass 2: ポインタ逆引き）
        self.analyser.analyze_flow(self.db, self.logger)

        # 手順 3: 解析済みの命令から参照先アドレス・シンボルを仮収集
        self.relocator.collect_symbols()

        # 手順 4: CODEセグメント間に挟まれた未探索コードブロックの検出と追加解析（Phase 2）
        # テーブルジャンプや特殊な呼び出しによって初回走査から漏れたコードを救済する
        self._run_phase2_analysis()

        # 手順 5: メモリアドレスから命令先頭への逆引きマップを構築
        # オペランド等の命令途中への参照を「LABEL + offset」として解決できるようにする
        self.db.populate_instruction_map()

        # 手順 6: 自己書き換え（JR相対オフセット書き換え＋連続JPテーブル）の検出とパッチ登録
        self._scan_jr_smc_jump_tables()

        # 手順 7: 追加解析されたコードを対象に再度参照シンボルを収集
        self.relocator.collect_symbols()

        # 手順 8: WORK領域の直後に隣接する孤立した未参照静的データをWORKセグメントへ統合
        self._merge_contiguous_unreferenced_regions()

        # 手順 9: 各セグメントの物理サイズと配置オフセットを仮計算
        self.db.populate_segment_offsets(self.analyser)
        
        # 手順 10: RAM使用量の安全性診断および最終動作モード（RAMコピー vs ROM直接実行）の確定
        sim_code_size = self.db.total_code_size
        sim_work_size = self.db.total_work_size
        sim_total_bytes = sim_code_size + sim_work_size

        final_copy_to_ram = COPY_CODE_TO_RAM
        final_ram_start = RAM_START_RAMCOPY

        # RAMコピーモード時の容量上限チェック
        if final_copy_to_ram:
            sim_limit_addr = final_ram_start + sim_total_bytes - 1
            if sim_limit_addr > RAM_MAX_LIMIT:
                self.logger.log(f"[-] 警告: RAM使用範囲の終端 {format_hex(sim_limit_addr)} がRAM制限アドレス {format_hex(RAM_MAX_LIMIT)} を超えました。")
                self.logger.log("[-] RAMコピー実行モードを無効化し、通常モード（ROM直接実行）に切り替えます。")
                final_copy_to_ram = False

        # 通常モード（ROM直接実行）時の安全なRAM開始アドレスを決定
        if not final_copy_to_ram:
            if self.analyser.max_existing_ram > 0:
                final_ram_start = max(self.analyser.max_existing_ram + 1, RAM_START_NORMAL)
            else:
                final_ram_start = RAM_START_NORMAL

        # 手順 11: 確定した動作パラメータを反映し、最終物理オフセットを再計算
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

        # 手順 12: 収集された全シンボルをレジスタに正式登録し、新アドレスを確定
        self.db.register_all_collected_symbols()
        for (addr, is_bios), record in self.db.records.items():
            record.new_address = self.db.translate_address(addr, is_code=record.is_work == False, is_bios=is_bios)

        # 手順 13: 解析レポートの表示・ログ保存
        self.print_report()

        # 手順 14: 再配置アセンブリソースコードファイルの出力
        self.generator.write_assembly_file()

        # 手順 15: 生成アセンブリコードの未定義ラベル・シンボル整合性自己診断
        self.perform_self_inspection()

    def _run_phase2_analysis(self):
        """フェーズ2: CODEセグメントに挟まれた無参照ブロックを検出し、追加の実行パス解析を行う"""
        if not USE_CODE_MERGE:
            return

        self.logger.log("[*] 無参照ブロックをスキャン...")
        
        # 登録済みの全参照アドレスを一時セットへ集約
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
        
        # バイナリ空間全体をスキャンし、CODEに挟まれた隙間を検出
        for pc in range(self.config.old_start, self.config.old_end):
            is_code = self.mem.has_attribute(pc, 'CODE')
            is_work = self.mem.has_attribute(pc, 'WORK') or self.mem.has_attribute(pc, 'MERGE')
            
            if not is_code and not is_work:
                # CODEでもWORKでもないデータ領域（隙間の開始候補）
                if not in_gap:
                    if pc > self.config.old_start and self.mem.has_attribute(pc - 1, 'CODE'):
                        in_gap = True
                        gap_start = pc
            else:
                if in_gap:
                    gap_end = pc - 1
                    # 隙間の終端がCODE属性である場合、孤立したコードブロックの可能性がある
                    if is_code:
                        is_unreferenced = True
                        for gap_addr in range(gap_start, gap_end + 1):
                            if gap_addr in referenced_addresses:
                                is_unreferenced = False
                                break
                        
                        # 外部からの参照が一切ない隙間であれば、追加トレースのエントリとして登録
                        if is_unreferenced:
                            self.logger.log(f"    - CODEブロックに挟まれた無参照ブロックを検出: {format_hex(gap_start)} ～ {format_hex(gap_end)}")
                            entries_to_trace.append(gap_start)
                            
                            # 隙間の開始位置を UNUSED_xxxxH ラベルとして先行登録
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
        """自己書き換え処理対象となるJR命令に続く、連続したJP命令テーブルの検出およびラベル登録を行う。

        【検出パターン】
          LD (JR_ADDR + 1), A  ; JR命令の第2バイト（相対変位）をAレジスタで書き換え
          JR JUMP_DEST         ; 書き換えられる相対ジャンプ（ROM上では書き換え不能）
          JP ROUTINE_0         ; ジャンプテーブル
          JP ROUTINE_1
          ...
        """
        self.logger.log("[*] 「JRオペランド書き換え + JP命令テーブル」タイプの処理を走査...")
        
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
                # 0x18: JR e 命令の第2バイトへの書き込みか判定
                if opcode == 0x18:
                    self.logger.log(f"[+] JR命令オペランドへの書き込みを検知: アドレス {format_hex(target)} (JR命令PC: {format_hex(jr_addr)})")

                    # LD (nn), A 直後の JR 命令であればSMCパッチの適用対象とする
                    if USE_SMC_PATCH:
                        if (self.mem.get_byte(pc) == 0x32  # 0x32: LD (nn), A
                            and pc + 2 + 2 < self.config.old_end
                            and jr_addr == pc + 3  # 次の命令が書き込み先JR命令である
                        ):
                            self.logger.log(f"    - \"LD(n),A + JR n\"タイプ -> パッチを適用します。")
                            self.analyser.smc_patch_jr_addresses.add(jr_addr)
                    
                    # JR命令に続く連続した 0xC3 (JP nn) 命令テーブルを走査して登録
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
        """WORK領域に隣接する、参照ラベルのないDATA領域をマージ（結合）する。

        文字列終端文字（NULL文字等）やアライメントパディングがDATAセグメントとしてROM側に
        取り残されるのを防ぎ、RAM上のWORK領域に統合して初期値転送に含めます。
        """
        for pc in range(self.config.old_start, self.config.old_end):
            self.mem.discard_attribute(pc, 'MERGE')
        
        if MAX_STATIC_MERGE_LIMIT < 1:
            return
            
        for pc in range(self.config.old_start, self.config.old_end):
            if self.mem.has_attribute(pc, 'WORK'):
                next_addr = pc + 1
                merge_count = 0
                while next_addr < self.config.old_end:
                    # 他から参照されているラベルまたは既にWORK属性の領域に達したら終了
                    if (next_addr, False) in self.db.unresolved_records or (next_addr, True) in self.db.unresolved_records or self.mem.has_attribute(next_addr, 'WORK'):
                        break
                    
                    if merge_count >= MAX_STATIC_MERGE_LIMIT:
                        break
                        
                    # DATA属性であり、CODEでもWORKでもない領域をMERGE属性として統合
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
            
        with open(self.config.output_asm, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        defined_symbols = set()
        
        # 出力ソースコード内に定義されているシンボル（EQU定義または行頭ラベル）を全抽出
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
                
        # 登録ラベルがすべてアセンブリファイル内で定義されているか検証
        missing_definitions = []
        for (addr, is_bios), label_name in self.db.labels.items():
            if label_name not in defined_symbols:
                # 「LABEL + offset」形式の相対ラベルは定義不要のため除外
                if " + " in label_name or " - " in label_name:
                    continue
                    
                # SMC用として命令途中に設定されたラベルの例外検証（命令先頭ラベルが定義されていればOK）
                record = self.db.records.get((addr, is_bios))
                if record and record.is_code and record.is_work:
                    if addr in self.db.byte_to_instruction_start:
                        inst_start = self.db.byte_to_instruction_start[addr]
                        inst_key = (inst_start, is_bios)
                        inst_label = self.db.labels.get(inst_key)
                        if inst_label in defined_symbols:
                            continue
                            
                missing_definitions.append(f"{label_name} (旧アドレス: {addr:04X}H, is_code: {record.is_code}, is_work: {record.is_work}, is_bios: {is_bios})")
                
        if missing_definitions:
            self.logger.log(f"[-] 致命的エラー: 出力アセンブリに未定義ラベルが検出されました: {missing_definitions}")
            raise AssertionError(f"未定義ラベルエラー: {missing_definitions}")
            
        self.logger.log("[+] 自己診断OK: 参照シンボル定義の整合性エラーはありません。")

    def print_report(self):
        """解析結果のメモリセグメント状況や互換性に関する詳細レポートを最終出力する"""
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
        
        # セグメント集計サイズとレジストリ計算値の整合性検証
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
        if MAX_STATIC_MERGE_LIMIT:
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

        self.logger.log(f"\n[+] BDOS / DISK-ROM 互換性システム警告:")
        if self.analyser.unsupported_bdos_calls:
            for call in self.analyser.unsupported_bdos_calls:
                self.logger.log(f"    - [警告] アドレス {call['pc']:04X}H: ディスクアクセスを伴うBDOS呼び出し (Fn {call['fn']}) を検出しました。")
                self.logger.log(f"      BDOSコール用フック ROMBDOS (F37DH) を使用するため、DISK-ROM環境でなければ動作しません。")
        else:
            self.logger.log("    - DISK-ROM環境に依存する致命的なBDOSコールは検出されませんでした。")

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


# =====================================================================
# コマンドライン引数解析・エントリポイント
# =====================================================================

def parse_hex_string(value):
    """16進数表記文字列（'C000', '0x0100'等）を整数値へ変換するパーサ関数"""
    try:
        return int(value, 16)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"'{value}' は有効な16進数文字列ではありません。"
        )


def parse_arguments():
    """コマンドライン引数を定義・解析し、オプションオブジェクトを返却する"""
    parser = argparse.ArgumentParser(
        description="COMバイナリ to ROM(32KB Page 1-2) リロケータ逆アセンブラ " + APP_VESRSION,
        add_help=False
    )
    parser.add_argument("-i", "--input", type=str, default=INPUT_PATH, help="入力ファイルパス (16進数テキストまたはバイナリ)")
    parser.add_argument("-o", "--output", type=str, default=OUTPUT_ASM_PATH, help="出力アセンブリファイルパス")
    parser.add_argument("-a", "--address", type=parse_hex_string, default=f"{ORIGINAL_LOAD_ADDR:04X}", help="入力バイナリのMSX上での開始アドレスを指定 (16進数4桁、例: 0100)")
    parser.add_argument("-s", type=parse_hex_string, help="RAMの先頭アドレスを指定 (16進数4桁、例: C000)")
    parser.add_argument("-l", type=parse_hex_string, help="RAM使用上限アドレスを指定 (16進数4桁、例: EFFF)")
    parser.add_argument("-c", action="store_true", help="RAMコピーモード有効 (CODE+WORKをRAMへコピーして実行)")
    parser.add_argument("-n", action="store_true", help="通常モード有効 (CODEはROM上で実行、WORKのみRAMに配置)")
    parser.add_argument("--patch", action="store_true", help="SMCパッチ有効 (通常モード時：JR命令書き換えをROM用処理でパッチ)")
    parser.add_argument("--nopatch", action="store_true", help="SMCパッチ無効")
    parser.add_argument("--simple", action="store_true", help="簡易探索パスを使用する（探索高速化）")
    parser.add_argument("--deep", action="store_true", help="詳細探索パスを使用する（レジスタ状態を考慮した精密探索）")
    parser.add_argument("--asm-type", type=int, choices=[1, 2], help="アセンブラのシンタックスタイプ (1 = sjasmplus, 2 = AILZ80ASM)")
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

    # リロケータの初期化と全解析・逆アセンブルの実行
    engine = MsxComToRomRelocator()
    engine.execute()

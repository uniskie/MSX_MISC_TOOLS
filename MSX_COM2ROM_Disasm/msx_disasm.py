#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =====================================================================
# MSX Z80 Intelligent Disassembler (msx_disasm)
# =====================================================================
# - ROM / COM / BLOAD バイナリ対応の実行フロー解析型逆アセンブラ
# - CODE / DATA / WORK / MERGE 属性の自動分類
# - レジスタ追跡による間接参照ポインタ・ワークエリアの逆引き特定
# - MSX ROMヘッダ (ABヘッダ) および割り込みフック登録の自動検出
# - JP (HL) / JP (IX) ジャンプテーブルパターンの検出と追跡
# - CODEギャップ (未参照ブロック) の走査回収
# =====================================================================

import os
import sys
import copy
import argparse

# 外部シンボル定義モジュール (msx_symbols.py) のインポート試行
# 存在する場合は BIOS コール、システムワークエリア、フック等の公式シンボル名を自動解決する
try:
    import msx_symbols
    HAS_MSX_SYMBOLS = True
except ImportError:
    HAS_MSX_SYMBOLS = False


# =====================================================================
# 共通ユーティリティ関数
# =====================================================================
def format_asm_hex(val, width=4):
    """数値をアセンブラ表記 (例: 0100H, 0C000H) の16進文字列に変換する。

    アセンブラの文法規約上、アルファベット(A～F)で始まる16進数値は
    ラベルや識別子と誤認されるのを防ぐため先頭に '0' を付加する。
    また、負数が渡された場合は指定ビット幅でマスクして符号なし整数に正規化する。

    引数:
        val (int): 変換対象の整数値 (負数可)
        width (int): 桁数 (2: 8ビット, 4: 16ビット)

    戻り値:
        str: アセンブラ形式の16進数文字列
    """
    # 負数が渡された場合のビットマスク処理（構文エラーとなる負号出力を防止）
    if width == 2:
        val = val & 0xFF
    else:
        val = val & 0xFFFF

    hex_str = f"{val:0{width}X}"
    if hex_str[0] in "ABCDEF":
        return "0" + hex_str + "H"
    return hex_str + "H"


def signed_byte(b):
    """符号なし8ビット整数 (0～255) を符号付き整数 (-128～127) に変換する。

    相対ジャンプ (JR, DJNZ) のオフセットや、IX/IY のインデックス相対
    ディスプレースメント (+d) の計算に使用する。

    引数:
        b (int): 8ビット値 (0～255)

    戻り値:
        int: 符号付き整数 (-128～127)
    """
    return b - 256 if b >= 128 else b


def get_symbol_name(addr):
    """指定アドレスに対応する MSX 公式シンボル名 (BIOS/ワーク/フック/DOS) を取得する。

    msx_symbols モジュールが読み込まれている場合、アドレスに対応する標準シンボルを検索する。
    ドットを含むシンボル名 (例: RDSLT.CALL) はアセンブラ互換のためアンダースコアに置換する。

    引数:
        addr (int): 検索対象の16ビットメモリアドレス

    戻り値:
        str or None: シンボル名。未定義またはモジュール不在の場合は None
    """
    if not HAS_MSX_SYMBOLS:
        return None
    try:
        # BIOS エントリの検索 (0000H～3FFFH)
        if hasattr(msx_symbols, "msx_symbols_bios"):
            b_labels = msx_symbols.msx_symbols_bios.from_address(addr)
            if b_labels:
                return b_labels[0].replace(".", "_")
        # システムワークエリアの検索 (F380H～FFFFH)
        if hasattr(msx_symbols, "msx_symbols_work"):
            w_labels = msx_symbols.msx_symbols_work.from_address(addr)
            if w_labels:
                return w_labels[0].replace(".", "_")
        # 割り込み/システムフックの検索 (FD9AH～)
        if hasattr(msx_symbols, "msx_symbols_hook"):
            h_labels = msx_symbols.msx_symbols_hook.from_address(addr)
            if h_labels:
                return h_labels[0].replace(".", "_")
        # 汎用ラベルの検索
        if hasattr(msx_symbols, "search_labels"):
            labels = msx_symbols.search_labels(addr)
            if labels:
                return labels[0].replace(".", "_")
        # MSX-DOS 関連シンボルの検索
        if hasattr(msx_symbols, "search_labels_dos"):
            labels = msx_symbols.search_labels_dos(addr)
            if labels:
                return labels[0].replace(".", "_")
    except Exception:
        pass
    return None


# =====================================================================
# 定数テーブル定義
# =====================================================================
# Z80 命令デコード用 8ビットレジスタテーブル (r フィールド 000B～111B)
# 0: B, 1: C, 2: D, 3: E, 4: H, 5: L, 6: (HL), 7: A
REG8 = ["b", "c", "d", "e", "h", "l", "(hl)", "a"]

# IX レジスタプレフィックス (DDH) 時の 8ビットレジスタテーブル
# H/L の位置が IXH/IXL に置き換わり、(HL) の位置がインデックス間接 (IX+d) に置き換わる
REG8_IX = ["b", "c", "d", "e", "ixh", "ixl", "(ix+d)", "a"]

# IY レジスタプレフィックス (FDH) 時の 8ビットレジスタテーブル
# H/L の位置が IYH/IYL に置き換わり、(HL) の位置がインデックス間接 (IY+d) に置き換わる
REG8_IY = ["b", "c", "d", "e", "iyh", "iyl", "(iy+d)", "a"]

# 算術論理演算命令 (ALU) ニーモニックテーブル (ビット 3～5: 000B～111B)
# 0: ADD, 1: ADC, 2: SUB, 3: SBC, 4: AND, 5: XOR, 6: OR, 7: CP
ALU = ["add a,", "adc a,", "sub", "sbc a,", "and", "xor", "or", "cp"]

# 8ビットローテート・シフト演算命令 (CBプレフィックス) ニーモニックテーブル (ビット 3～5: 000B～111B)
# 0: RLC, 1: RRC, 2: RL, 3: RR, 4: SLA, 5: SRA, 6: SLL (未定義命令), 7: SRL
ROT = ["rlc", "rrc", "rl", "rr", "sla", "sra", "sll", "srl"]

# 代表的なMSX割り込みフックアドレス
# ゲームや常駐プログラムがタイマー割り込み(H.TIMI)やキー入力(H.KEYI)をフックする検出に使用
MSX_HOOK_ADDRS = {
    0xFD9A: "H_KEYI", 0xFD9B: "H_KEYI", # キーボード割り込みフック
    0xFD9F: "H_TIMI", 0xFDA0: "H_TIMI", 0xFDA1: "H_TIMI", # タイマー割り込みフック (毎フレーム実行)
}

# 引数としてメモリアドレスを取る主要な MSX BIOS / 拡張ルーチン一覧
# レジスタ追跡時、ここに登録されたルーチン呼び出し直前のレジスタ値をデータ参照としてマークする
BIOS_MEM_ARGS = {
    0x005C: ["HL"],  # LDIRVM (HL = 転送元メインRAMアドレス, DE = 転送先VRAMアドレス, BC = バイト長)
    0x0059: ["DE"],  # LDIRMV (HL = 転送元VRAMアドレス, DE = 転送先メインRAMアドレス, BC = バイト長)
    0x005F: ["HL"],  # WRTTVV (HL = 転送元文字列アドレス, BC = 長さ)
    0x00E1: ["HL"],  # TAPIN  (HL = カセットテープ読込バッファアドレス)
    0x00ED: ["HL"],  # TAPOUT (HL = カセットテープ書込バッファアドレス)
    0x0144: ["HL"],  # PHYDIO (非公開BIOSエントリ: ディスクセクタ読み書きバッファアドレス)
    0xFFA7: ["HL"],  # H_PHYD (PHYDIO フックルーチン)
    0x4010: ["HL"],  # DISK-ROM PHYDIO ルーチン
    0x014D: ["HL"],  # SETPLT (HL = パレットデータ配列アドレス)
    0x0150: ["HL"],  # GETPLT (HL = パレットデータ格納バッファアドレス)
    0x0186: ["HL"],  # NVBGET (HL = バックアップRAM読込格納バッファアドレス)
    0x0189: ["HL"],  # NVBSET (HL = バックアップRAM書込データ元アドレス)
    0x008D: ["HL"],  # GRPPRT (HL = グラフィック描画用文字列バッファアドレス)
}

# BDOSコールエントリ (MSX-DOS 0005H および Disk BASIC 0F37DH)
BDOS_ENTRY_ADDRS = {0x0005, 0xF37D}

# BDOSファンクション別の引数レジスタ定義
# Cレジスタに設定されたファンクションコードに応じて、ポインタ引数を保持するレジスタを特定する
BDOS_ARG_REGS = {
    0x09: ["DE"], # _STROUT: 文字列出力 (DE = '$'終端文字列アドレス)
    0x0A: ["DE"], # _BUFIN : 1行入力 (DE = 入力バッファアドレス)
    0x0F: ["DE"], # _FOPEN : ファイルオープン (DE = FCBアドレス)
    0x10: ["DE"], # _FCLOSE: ファイルクローズ (DE = FCBアドレス)
    0x11: ["DE"], # _SFIRST: 最初のエントリ検索 (DE = FCBアドレス)
    0x12: ["DE"], # _SNEXT : 次のエントリ検索 (DE = FCBアドレス)
    0x13: ["DE"], # _FDEL  : ファイル削除 (DE = FCBアドレス)
    0x14: ["DE"], # _RDSEQ : シーケンシャル読み出し (DE = FCBアドレス)
    0x15: ["DE"], # _WRSEQ : シーケンシャル書き込み (DE = FCBアドレス)
    0x16: ["DE"], # _FMAKE : ファイル作成 (DE = FCBアドレス)
    0x17: ["DE"], # _FREN  : ファイル名変更 (DE = FCBアドレス)
    0x1A: ["DE"], # _SETDTA: DTAアドレス設定 (DE = 転送バッファアドレス)
    0x21: ["DE"], # _RDRND : ランダムレコード読み出し (DE = FCBアドレス)
    0x22: ["DE"], # _WRRND : ランダムレコード書き込み (DE = FCBアドレス)
    0x23: ["DE"], # _FSIZE : ファイルサイズ取得 (DE = FCBアドレス)
    0x24: ["DE"], # _SETRND: ランダムレコード番号設定 (DE = FCBアドレス)
    0x27: ["DE"], # _WRBLK : ランダムブロック書き込み (DE = FCBアドレス)
    0x28: ["DE"], # _RDBLK : ランダムブロック読み出し (DE = FCBアドレス)
    0x43: ["DE"], # _EXPLAIN: エラー解説文字列取得 (DE = 出力バッファアドレス)
    0x48: ["DE"], # _ALLOC : メモリ確保
    0x49: ["DE"], # _FREE  : メモリ解放
    0x6B: ["DE"], # _GENV  : 環境変数取得 (MSX-DOS2)
    0x6C: ["DE"], # _SENV  : 環境変数設定 (MSX-DOS2)
    0x4B: ["HL", "DE"],  # _GENV (HL = 変数名文字列アドレス, DE = 値格納バッファアドレス)
    0x4C: ["HL", "DE"],  # _SENV (HL = 変数名文字列アドレス, DE = 設定値文字列アドレス)
}


# =====================================================================
# ログ管理クラス
# =====================================================================
class DisasmLogger:
    """逆アセンブルおよび解析ログを標準出力とログファイルに並行出力するクラス。"""

    def __init__(self, log_filepath):
        """ロガーを初期化し、指定パスのログファイルを新規作成する。

        引数:
            log_filepath (str): 出力先ログファイルのパス
        """
        self.log_filepath = log_filepath
        try:
            with open(self.log_filepath, "w", encoding="utf-8") as f:
                pass
        except IOError:
            print("[-] エラー: ログファイルの初期化に失敗しました。")

    def log(self, message):
        """メッセージをコンソールに出力し、ログファイルへ追記する。

        引数:
            message (str): 記録するログメッセージ文字列
        """
        print(message)
        try:
            with open(self.log_filepath, "a", encoding="utf-8") as f:
                f.write(message + "\n")
        except IOError:
            pass


# =====================================================================
# メモリイメージクラス
# =====================================================================
class BinaryImage:
    """逆アセンブル対象バイナリのメモリイメージおよび各バイトの属性を管理するクラス。

    各メモリアドレスに対して以下の属性を排他および重複を許容して管理する:
      - CODE : 実行パスの解析により確定した命令バイト
      - DATA : 静的データ（初期状態は全領域が DATA）
      - WORK : プログラム実行中に書き込みが行われる変数・バッファ領域
      - MERGE: WORK の直後に隣接し、無参照のまま埋め込まれたパディングデータ
    """

    def __init__(self, raw_bytes, base_addr, logger):
        """バイナリイメージを初期化する。

        引数:
            raw_bytes (bytes or bytearray): バイナリデータ本体
            base_addr (int): メモリへの配置開始アドレス (例: 0x4000)
            logger (DisasmLogger): ログ出力用インスタンス
        """
        self.raw_bytes = bytearray(raw_bytes)
        self.base_addr = base_addr
        # 終端アドレスは内部処理上、Exclusive (末尾アドレス + 1) として一元管理する
        self.end_addr = base_addr + len(raw_bytes)
        self.logger = logger
        # 全バイトを初期属性 'DATA' としてマーク
        self.attributes = [set(["DATA"]) for _ in range(len(raw_bytes))]

    @property
    def last_addr(self):
        """バイナリの最終バイトのアドレス (Inclusive: 包含) を返す。"""
        return self.end_addr - 1

    def is_valid_address(self, addr):
        """指定アドレスが本バイナリイメージの有効範囲内にあるか判定する。"""
        return self.base_addr <= addr < self.end_addr

    def get_byte(self, addr):
        """指定アドレスの1バイト (0～255) を取得する。範囲外の場合は 0 を返す。"""
        if not self.is_valid_address(addr):
            return 0
        return self.raw_bytes[addr - self.base_addr]

    def get_word(self, addr):
        """指定アドレスからリトルエンディアン形式で2バイト (16ビット値) を取得する。"""
        return self.get_byte(addr) | (self.get_byte(addr + 1) << 8)

    def mark_attribute(self, addr, attr):
        """指定アドレスに属性 (CODE, DATA, WORK, MERGE) を付与する。"""
        if self.is_valid_address(addr):
            self.attributes[addr - self.base_addr].add(attr)

    def discard_attribute(self, addr, attr):
        """指定アドレスから属性を除去する。"""
        if self.is_valid_address(addr):
            self.attributes[addr - self.base_addr].discard(attr)

    def has_attribute(self, addr, attr):
        """指定アドレスが特定の属性を持っているか判定する。"""
        if not self.is_valid_address(addr):
            return False
        return attr in self.attributes[addr - self.base_addr]


# =====================================================================
# Z80 命令デコーダ
# =====================================================================
class Z80InstructionDecoder:
    """仮想メモリ上の機械語データを解析し、命令長・分岐先・参照アドレス・アセンブラ文字列を生成するクラス。"""

    def __init__(self, mem: BinaryImage, is_com_format=False):
        """デコーダを初期化する。

        引数:
            mem (BinaryImage): デコード対象のメモリイメージ
            is_com_format (bool): COM形式バイナリか否か (RST 30Hの解釈判定に使用)
        """
        self.mem = mem
        self.is_com_format = is_com_format

    def decode(self, pc, get_label_fn=None):
        """プログラムカウンタ位置から1命令をデコードする。

        引数:
            pc (int): デコード開始アドレス
            get_label_fn (callable, optional): アドレスをラベル名に変換するコールバック

        戻り値:
            tuple: (
                命令バイト長 (int),
                静的分岐先アドレスリスト (list[int]),
                アセンブリニーモニック文字列 (str),
                終端命令フラグ (bool: RET/JP無条件分岐などフォールスルーしない命令の場合True),
                メモリアクセス先アドレス (int or None: (nn) 形式の絶対アクセスアドレス),
                メモリアクセスサイズ (int: 1バイトまたは2バイト),
                16ビット即値 (int or None: ld reg, nn 命令などの即値)
            )
        """
        b0 = self.mem.get_byte(pc)

        def lbl(addr):
            # 登録済みラベルがあればラベル名を返し、なければ16進表記文字列を返す
            if get_label_fn:
                return get_label_fn(addr)
            return format_asm_hex(addr)

        # -------------------------------------------------------------
        # ED プレフィックス: 拡張命令群
        # -------------------------------------------------------------
        if b0 == 0xED:
            b1 = self.mem.get_byte(pc + 1)

            # 16ビットレジスタ間接メモリアクセス: ld (nn), rp
            # 43H: ld (nn), bc / 53H: ld (nn), de / 73H: ld (nn), sp
            if b1 in [0x43, 0x53, 0x73]:
                target = self.mem.get_word(pc + 2)
                reg = {0x43: "bc", 0x53: "de", 0x73: "sp"}[b1]
                return 4, [], f"ld ({lbl(target)}), {reg}", False, target, 2, None

            # 16ビットレジスタ間接メモリアクセス: ld rp, (nn)
            # 4BH: ld bc, (nn) / 5BH: ld de, (nn) / 7BH: ld sp, (nn)
            if b1 in [0x4B, 0x5B, 0x7B]:
                target = self.mem.get_word(pc + 2)
                reg = {0x4B: "bc", 0x5B: "de", 0x7B: "sp"}[b1]
                return 4, [], f"ld {reg}, ({lbl(target)})", False, target, 2, None

            # 未定義命令: ld (nn), hl (ED 63H) - 通常の 22H と同一動作
            if b1 == 0x63:
                target = self.mem.get_word(pc + 2)
                return 4, [], f"ld ({lbl(target)}), hl ; (undocumented: ED 63H)", False, target, 2, None

            # 未定義命令: ld hl, (nn) (ED 6BH) - 通常の 2AH と同一動作
            if b1 == 0x6B:
                target = self.mem.get_word(pc + 2)
                return 4, [], f"ld hl, ({lbl(target)}) ; (undocumented: ED 6BH)", False, target, 2, None

            # I/O 命令群: in r, (c) / out (c), r (40H～7FH)
            if 0x40 <= b1 <= 0x7F:
                reg_code = (b1 >> 3) & 7
                reg_name = REG8[reg_code]
                # ビット 0～2 が 000B: in r, (c)
                if (b1 & 7) == 0:
                    # ED 70H: in (c) または in f, (c) - 入力値を保存せずフラグのみ変化させる未定義命令
                    if reg_code == 6:
                        return 2, [], "in (c) ; (undocumented: flags only)", False, None, 0, None
                    return 2, [], f"in {reg_name}, (c)", False, None, 0, None
                # ビット 0～2 が 001B: out (c), r
                elif (b1 & 7) == 1:
                    # ED 71H: out (c), 0 - ポートCに0を出力する未定義命令 (一部CMOS版ではFFH)
                    if reg_code == 6:
                        return 2, [], "out (c), 0 ; (undocumented)", False, None, 0, None
                    return 2, [], f"out (c), {reg_name}", False, None, 0, None

            # ED系 標準算術・制御・ブロック転送命令群
            ed_ops = {
                0x44: ("neg", False),          # 2の補数演算: A = 0 - A
                0x45: ("retn", True),          # NMI (ノンマスカブル割り込み) からの復帰
                0x4D: ("reti", True),          # マスカブル割り込みからの復帰
                0x46: ("im 0", False),         # 割り込みモード 0 設定
                0x56: ("im 1", False),         # 割り込みモード 1 設定
                0x5E: ("im 2", False),         # 割り込みモード 2 設定 (ベクタ割り込み)
                0x42: ("sbc hl, bc", False),   # キャリー付き16ビット減算: HL = HL - BC - CY
                0x52: ("sbc hl, de", False),   # キャリー付き16ビット減算: HL = HL - DE - CY
                0x62: ("sbc hl, hl", False),   # キャリー付き16ビット減算: HL = HL - HL - CY
                0x72: ("sbc hl, sp", False),   # キャリー付き16ビット減算: HL = HL - SP - CY
                0x4A: ("adc hl, bc", False),   # キャリー付き16ビット加算: HL = HL + BC + CY
                0x5A: ("adc hl, de", False),   # キャリー付き16ビット加算: HL = HL + DE + CY
                0x6A: ("adc hl, hl", False),   # キャリー付き16ビット加算: HL = HL + HL + CY
                0x7A: ("adc hl, sp", False),   # キャリー付き16ビット加算: HL = HL + SP + CY
                0x47: ("ld i, a", False),      # 割り込みベクタベースレジスタ I へ A を転送
                0x57: ("ld a, i", False),      # I レジスタの値を A へ転送 (フラグ変化あり)
                0x4F: ("ld r, a", False),      # DRAM リフレッシュカウンタレジスタ R へ A を転送
                0x5F: ("ld a, r", False),      # R レジスタの値を A へ転送 (フラグ変化あり)
                0x67: ("rrd", False),          # A の下位4ビットと (HL) の4ビット×2 を右ローテート
                0x6F: ("rld", False),          # A の下位4ビットと (HL) の4ビット×2 を左ローテート
                0xA0: ("ldi", False),          # ブロック転送 (インクリメント): (DE)=(HL), HL++, DE++, BC--
                0xA1: ("cpi", False),          # ブロック比較 (インクリメント): A-(HL), HL++, BC--
                0xA2: ("ini", False),          # ブロック入力 (インクリメント): (HL)=IN(C), HL++, B--
                0xA3: ("outi", False),         # ブロック出力 (インクリメント): OUT(C)=(HL), HL++, B--
                0xB0: ("ldir", False),         # 連続ブロック転送 (BC=0まで実行): (DE)=(HL)...
                0xB1: ("cpir", False),         # 連続ブロック比較 (BC=0または一致まで実行)
                0xB2: ("inir", False),         # 連続ブロック入力 (B=0まで実行)
                0xB3: ("otir", False),         # 連続ブロック出力 (B=0まで実行)
                0xA8: ("ldd", False),          # ブロック転送 (デクリメント): (DE)=(HL), HL--, DE--, BC--
                0xA9: ("cpd", False),          # ブロック比較 (デクリメント): A-(HL), HL--, BC--
                0xAA: ("ind", False),          # ブロック入力 (デクリメント): (HL)=IN(C), HL--, B--
                0xAB: ("outd", False),         # ブロック出力 (デクリメント): OUT(C)=(HL), HL--, B--
                0xB8: ("lddr", False),         # 連続ブロック転送 (デクリメント・BC=0まで実行)
                0xB9: ("cpdr", False),         # 連続ブロック比較 (デクリメント・BC=0または一致まで実行)
                0xBA: ("indr", False),         # 連続ブロック入力 (デクリメント・B=0まで実行)
                0xBB: ("otdr", False),         # 連続ブロック出力 (デクリメント・B=0まで実行)
            }
            if b1 in ed_ops:
                mnemonic, is_term = ed_ops[b1]
                return 2, [], mnemonic, is_term, None, 0, None

            # ED系 未定義命令群の網羅
            # 同一動作を行うエイリアスオペコード
            if b1 in [0x4C, 0x54, 0x5C, 0x64, 0x6C, 0x74, 0x7C]:
                return 2, [], f"neg ; (undocumented: ED {format_asm_hex(b1, 2)})", False, None, 0, None
            if b1 in [0x55, 0x65, 0x75]:
                return 2, [], f"retn ; (undocumented: ED {format_asm_hex(b1, 2)})", True, None, 0, None
            if b1 in [0x5D, 0x6D, 0x7D]:
                return 2, [], f"reti ; (undocumented: ED {format_asm_hex(b1, 2)})", True, None, 0, None
            if b1 in [0x4E, 0x66, 0x6E]:
                return 2, [], f"im 0 ; (undocumented: ED {format_asm_hex(b1, 2)})", False, None, 0, None
            if b1 == 0x76:
                return 2, [], "im 1 ; (undocumented: ED 76H)", False, None, 0, None
            if b1 == 0x7E:
                return 2, [], "im 2 ; (undocumented: ED 7EH)", False, None, 0, None

            # その他の未定義 ED シーケンスはバイト定義として出力
            return 2, [], f"db 0EDH, {format_asm_hex(b1, 2)}", False, None, 0, None

        # -------------------------------------------------------------
        # CB プレフィックス: ビット操作・ローテート・シフト命令
        # -------------------------------------------------------------
        if b0 == 0xCB:
            b1 = self.mem.get_byte(pc + 1)
            reg_idx = b1 & 7         # 対象レジスタ (0～7: B, C, D, E, H, L, (HL), A)
            bit_idx = (b1 >> 3) & 7  # 対象ビット番号 (0～7) または演算種別
            reg_str = REG8[reg_idx]

            # 00H～3FH: ローテート・シフト命令群
            if 0x00 <= b1 <= 0x3F:
                # ビット種別 6 (0110B) は未定義シフト命令 SLL (左シフトしてビット0に1をセット)
                if bit_idx == 6:
                    return 2, [], f"sll {reg_str} ; (undocumented: shift left logical)", False, None, 0, None
                return 2, [], f"{ROT[bit_idx]} {reg_str}", False, None, 0, None

            # 40H～7FH: ビットテスト命令 BIT b, r (Zフラグに反転結果を反映)
            elif 0x40 <= b1 <= 0x7F:
                return 2, [], f"bit {bit_idx}, {reg_str}", False, None, 0, None

            # 80H～BFH: ビットリセット命令 RES b, r (指定ビットを 0 にクリア)
            elif 0x80 <= b1 <= 0xBF:
                return 2, [], f"res {bit_idx}, {reg_str}", False, None, 0, None

            # C0H～FFH: ビットセット命令 SET b, r (指定ビットを 1 にセット)
            elif 0xC0 <= b1 <= 0xFF:
                return 2, [], f"set {bit_idx}, {reg_str}", False, None, 0, None

        # -------------------------------------------------------------
        # DD / FD プレフィックス: インデックスレジスタ (IX / IY) 命令
        # -------------------------------------------------------------
        if b0 in [0xDD, 0xFD]:
            pfx = "ix" if b0 == 0xDD else "iy"
            reg8_idx = REG8_IX if b0 == 0xDD else REG8_IY
            b1 = self.mem.get_byte(pc + 1)

            # 16ビット即値・メモリロード命令
            if b1 == 0x21:  # ld ix/iy, nn (4バイト)
                target = self.mem.get_word(pc + 2)
                return 4, [], f"ld {pfx}, {lbl(target)}", False, None, 0, target
            if b1 == 0x22:  # ld (nn), ix/iy (4バイト)
                target = self.mem.get_word(pc + 2)
                return 4, [], f"ld ({lbl(target)}), {pfx}", False, target, 2, None
            if b1 == 0x2A:  # ld ix/iy, (nn) (4バイト)
                target = self.mem.get_word(pc + 2)
                return 4, [], f"ld {pfx}, ({lbl(target)})", False, target, 2, None

            # 16ビット算術演算命令
            if b1 in [0x09, 0x19, 0x29, 0x39]:  # add ix/iy, rp (2バイト)
                rp = {0x09: "bc", 0x19: "de", 0x29: pfx, 0x39: "sp"}[b1]
                return 2, [], f"add {pfx}, {rp}", False, None, 0, None
            if b1 in [0x23, 0x2B]:              # inc / dec ix/iy (2バイト)
                op = "inc" if b1 == 0x23 else "dec"
                return 2, [], f"{op} {pfx}", False, None, 0, None

            # レジスタ間接ジャンプ・スタック操作
            if b1 == 0xE9:  # jp (ix) / jp (iy) (2バイト)
                return 2, [], f"jp ({pfx})", True, None, 0, None
            if b1 in [0xE1, 0xE5]:  # pop / push ix/iy (2バイト)
                op = "pop" if b1 == 0xE1 else "push"
                return 2, [], f"{op} {pfx}", False, None, 0, None
            if b1 == 0xE3:  # ex (sp), ix/iy (2バイト)
                return 2, [], f"ex (sp), {pfx}", False, None, 0, None
            if b1 == 0xF9:  # ld sp, ix/iy (2バイト)
                return 2, [], f"ld sp, {pfx}", False, None, 0, None

            # DDCB / FDCB プレフィックス: インデックス相対ビット操作・シフト命令 (4バイト命令)
            # 書式: DD CB d op / FD CB d op (オフセット d が 3 バイト目に配置される)
            if b1 == 0xCB:
                raw_d = self.mem.get_byte(pc + 2)
                d = signed_byte(raw_d)
                b3 = self.mem.get_byte(pc + 3)
                d_str = f"+{d}" if d >= 0 else f"{d}"
                bit = (b3 >> 3) & 7
                reg_code = b3 & 7
                operand = f"({pfx}{d_str})"
                b0_hex = format_asm_hex(b0, 2)
                d_hex = format_asm_hex(raw_d, 2)
                b3_hex = format_asm_hex(b3, 2)

                # シフト・ローテート命令群 (00H～3FH)
                if 0x00 <= b3 <= 0x3F:
                    rot = ROT[bit]
                    if reg_code == 6:
                        if bit == 6:
                            # SLL (未定義命令: 最下位ビットを1にして左シフト)
                            return 4, [], f"db {b0_hex}, 0CBH, {d_hex}, {b3_hex} ; sll {operand} (undocumented)", False, None, 0, None
                        return 4, [], f"{rot} {operand}", False, None, 0, None
                    else:
                        # 未定義命令: シフト結果を (IX+d) と 8ビットレジスタの双方に同時書き戻す
                        return 4, [], f"db {b0_hex}, 0CBH, {d_hex}, {b3_hex} ; {rot} {operand}, {REG8[reg_code]} (undocumented)", False, None, 0, None
                # BIT 命令群 (40H～7FH)
                elif 0x40 <= b3 <= 0x7F:
                    if reg_code == 6:
                        return 4, [], f"bit {bit}, {operand}", False, None, 0, None
                    else:
                        return 4, [], f"db {b0_hex}, 0CBH, {d_hex}, {b3_hex} ; bit {bit}, {operand} (undocumented)", False, None, 0, None
                # RES 命令群 (80H～BFH)
                elif 0x80 <= b3 <= 0xBF:
                    if reg_code == 6:
                        return 4, [], f"res {bit}, {operand}", False, None, 0, None
                    else:
                        return 4, [], f"db {b0_hex}, 0CBH, {d_hex}, {b3_hex} ; res {bit}, {operand}, {REG8[reg_code]} (undocumented)", False, None, 0, None
                # SET 命令群 (C0H～FFH)
                elif 0xC0 <= b3 <= 0xFF:
                    if reg_code == 6:
                        return 4, [], f"set {bit}, {operand}", False, None, 0, None
                    else:
                        return 4, [], f"db {b0_hex}, 0CBH, {d_hex}, {b3_hex} ; set {bit}, {operand}, {REG8[reg_code]} (undocumented)", False, None, 0, None

            # インデックス相対間接アクセス: (IX+d) / (IY+d)
            is_ind = (0x40 <= b1 <= 0xBF and (((b1 >> 3) & 7) == 6 or (b1 & 7) == 6))
            if is_ind or b1 in [0x34, 0x35, 0x36]:
                d = signed_byte(self.mem.get_byte(pc + 2))
                d_str = f"+{d}" if d >= 0 else f"{d}"
                operand = f"({pfx}{d_str})"
                if b1 == 0x34: return 3, [], f"inc {operand}", False, None, 0, None
                if b1 == 0x35: return 3, [], f"dec {operand}", False, None, 0, None
                if b1 == 0x36:
                    val = self.mem.get_byte(pc + 3)
                    return 4, [], f"ld {operand}, {format_asm_hex(val, 2)}", False, None, 0, None
                if 0x40 <= b1 <= 0x7F and b1 != 0x76:
                    dest = operand if ((b1 >> 3) & 7) == 6 else REG8[(b1 >> 3) & 7]
                    src = operand if (b1 & 7) == 6 else REG8[b1 & 7]
                    return 3, [], f"ld {dest}, {src}", False, None, 0, None
                if 0x80 <= b1 <= 0xBF:
                    return 3, [], f"{ALU[(b1 >> 3) & 7]} {operand}", False, None, 0, None

            # インデックスレジスタの半身 (IXH, IXL, IYH, IYL) を操作する未定義命令群
            if b1 in [0x24, 0x2C]:  # inc ixh/ixl / iyh/iyl (2バイト)
                r = f"{pfx}h" if b1 == 0x24 else f"{pfx}l"
                return 2, [], f"inc {r} ; (undocumented)", False, None, 0, None
            if b1 in [0x25, 0x2D]:  # dec ixh/ixl / iyh/iyl (2バイト)
                r = f"{pfx}h" if b1 == 0x25 else f"{pfx}l"
                return 2, [], f"dec {r} ; (undocumented)", False, None, 0, None
            if b1 in [0x26, 0x2E]:  # ld ixh/ixl / iyh/iyl, n (3バイト)
                r = f"{pfx}h" if b1 == 0x26 else f"{pfx}l"
                n = self.mem.get_byte(pc + 2)
                return 3, [], f"ld {r}, {format_asm_hex(n, 2)} ; (undocumented)", False, None, 0, None

            # インデックスレジスタ半身に対する 8ビット算術論理演算 (未定義命令: 2バイト)
            if 0x80 <= b1 <= 0xBF:
                s_idx = b1 & 7
                if s_idx in [4, 5]:
                    src = reg8_idx[s_idx]
                    return 2, [], f"{ALU[(b1 >> 3) & 7]} {src} ; (undocumented)", False, None, 0, None

            # インデックスレジスタ半身を含むレジスタ間ロード (未定義命令: 2バイト)
            if 0x40 <= b1 <= 0x7F and b1 != 0x76:
                d_idx = (b1 >> 3) & 7
                s_idx = b1 & 7
                if d_idx in [4, 5] or s_idx in [4, 5]:
                    dest = reg8_idx[d_idx]
                    src = reg8_idx[s_idx]
                    return 2, [], f"ld {dest}, {src} ; (undocumented)", False, None, 0, None

            # 【不具合修正】Prefix Ignored (プレフィックス無視):
            # DD/FDの直後に対象外の通常命令が来た場合、ハードウェアはDD/FDを単独で無視(1バイト消費)し、
            # 次の命令を通常通り実行する。2バイト消費して後続の境界が崩れるのを防ぐため、1バイト命令として返す。
            return 1, [], f"db {format_asm_hex(b0, 2)} ; (prefix ignored: undocumented)", False, None, 0, None

        # -------------------------------------------------------------
        # 標準 1 バイトプレフィックス命令群 (MSX 拡張 RST 含む)
        # -------------------------------------------------------------
        # 【不具合修正】MSX インタースロットコール (RST 30H / CALSLT) の安全化判定
        # 後続にスロットID(1バイト)とターゲットアドレス(2バイト)がインライン配置される特殊形式
        if b0 == 0xF7:
            # COM形式バイナリの場合、またはバイナリ範囲外で後続データが読めない場合は通常の1バイト命令としてデコード
            slot = self.mem.get_byte(pc + 1)
            target = self.mem.get_word(pc + 2)
            # スロット番号が妥当(0～3、または拡張スロットフラグ 80H～8FH)かつ非COMの場合のみ4バイト命令と判定
            is_valid_slot = (slot in [0x00, 0x01, 0x02, 0x03]) or ((slot & 0x80) and ((slot & 0x0C) >> 2) in [0, 1, 2, 3])
            if not self.is_com_format and is_valid_slot and (self.mem.is_valid_address(pc + 3) or target < 0x4000):
                return 4, [target], f"rst 30H\n    db  {format_asm_hex(slot, 2)}\n    dw  {lbl(target)}", False, None, 0, None
            else:
                return 1, [0x0030], "rst 30H", False, None, 0, None

        # 終端・制御命令
        if b0 == 0xC9: return 1, [], "ret", True, None, 0, None       # サブルーチン無条件復帰
        if b0 == 0xE9: return 1, [], "jp (hl)", True, None, 0, None  # HLレジスタ間接ジャンプ
        if b0 == 0x76: return 1, [], "halt", False, None, 0, None     # CPU一時停止 (割り込み待ち)

        # 無条件絶対ジャンプ: jp nn (3バイト)
        if b0 == 0xC3:
            target = self.mem.get_word(pc + 1)
            return 3, [target], f"jp {lbl(target)}", True, None, 0, None

        # 無条件サブルーチン呼び出し: call nn (3バイト)
        if b0 == 0xCD:
            target = self.mem.get_word(pc + 1)
            return 3, [target], f"call {lbl(target)}", False, None, 0, None

        # 条件付き絶対ジャンプ: jp cc, nn (3バイト)
        # C2H: NZ, CAH: Z, D2H: NC, DAH: C, E2H: PO, EAH: PE, F2H: P, FAH: M
        if b0 in [0xC2, 0xCA, 0xD2, 0xDA, 0xE2, 0xEA, 0xF2, 0xFA]:
            target = self.mem.get_word(pc + 1)
            cond = {0xC2: "nz", 0xCA: "z", 0xD2: "nc", 0xDA: "c", 0xE2: "po", 0xEA: "pe", 0xF2: "p", 0xFA: "m"}[b0]
            return 3, [target], f"jp {cond}, {lbl(target)}", False, None, 0, None

        # 条件付きサブルーチン呼び出し: call cc, nn (3バイト)
        # C4H: NZ, CCH: Z, D4H: NC, DCH: C, E4H: PO, ECH: PE, F4H: P, FCH: M
        if b0 in [0xC4, 0xCC, 0xD4, 0xDC, 0xE4, 0xEC, 0xF4, 0xFC]:
            target = self.mem.get_word(pc + 1)
            cond = {0xC4: "nz", 0xCC: "z", 0xD4: "nc", 0xDC: "c", 0xE4: "po", 0xEC: "pe", 0xF4: "p", 0xFC: "m"}[b0]
            return 3, [target], f"call {cond}, {lbl(target)}", False, None, 0, None

        # 無条件相対ジャンプ: jr e (2バイト)
        if b0 == 0x18:
            offset = signed_byte(self.mem.get_byte(pc + 1))
            target = (pc + 2 + offset) & 0xFFFF
            return 2, [target], f"jr {lbl(target)}", True, None, 0, None

        # 条件付き相対ジャンプ: jr cc, e (2バイト)
        # 20H: JR NZ, 28H: JR Z, 30H: JR NC, 38H: JR C
        if b0 in [0x20, 0x28, 0x30, 0x38]:
            offset = signed_byte(self.mem.get_byte(pc + 1))
            target = (pc + 2 + offset) & 0xFFFF
            names = {0x20: "jr nz,", 0x28: "jr z,", 0x30: "jr nc,", 0x38: "jr c,"}
            return 2, [target], f"{names[b0]} {lbl(target)}", False, None, 0, None

        # ループカウンタ減算相対ジャンプ: djnz e (2バイト: B = B - 1, B != 0 ならジャンプ)
        if b0 == 0x10:
            offset = signed_byte(self.mem.get_byte(pc + 1))
            target = (pc + 2 + offset) & 0xFFFF
            return 2, [target], f"djnz {lbl(target)}", False, None, 0, None

        # 絶対アドレスメモリアクセス (8ビット / 16ビット)
        if b0 == 0x32:  # ld (nn), a (3バイト: アドレス nn に A を格納)
            target = self.mem.get_word(pc + 1)
            return 3, [], f"ld ({lbl(target)}), a", False, target, 1, None
        if b0 == 0x3A:  # ld a, (nn) (3バイト: アドレス nn から A に読込)
            target = self.mem.get_word(pc + 1)
            return 3, [], f"ld a, ({lbl(target)})", False, target, 1, None
        if b0 == 0x22:  # ld (nn), hl (3バイト: アドレス nn に HL を格納)
            target = self.mem.get_word(pc + 1)
            return 3, [], f"ld ({lbl(target)}), hl", False, target, 2, None
        if b0 == 0x2A:  # ld hl, (nn) (3バイト: アドレス nn から HL に読込)
            target = self.mem.get_word(pc + 1)
            return 3, [], f"ld hl, ({lbl(target)})", False, target, 2, None

        # 16ビット即値ロード: ld rp, nn (3バイト)
        # 01H: BC, 11H: DE, 21H: HL, 31H: SP
        if b0 in [0x01, 0x11, 0x21, 0x31]:
            target = self.mem.get_word(pc + 1)
            r = {0x01: "bc", 0x11: "de", 0x21: "hl", 0x31: "sp"}[b0]
            return 3, [], f"ld {r}, {lbl(target)}", False, None, 0, target

        # 条件付き復帰: ret cc (1バイト)
        # C0H: NZ, C8H: Z, D0H: NC, D8H: C, E0H: PO, E8H: PE, F0H: P, F8H: M
        if b0 in [0xC0, 0xC8, 0xD0, 0xD8, 0xE0, 0xE8, 0xF0, 0xF8]:
            cond = {0xC0: "nz", 0xC8: "z", 0xD0: "nc", 0xD8: "c", 0xE0: "po", 0xE8: "pe", 0xF0: "p", 0xF8: "m"}[b0]
            return 1, [], f"ret {cond}", False, None, 0, None

        # スタック操作: push rp / pop rp (1バイト)
        if b0 in [0xC5, 0xD5, 0xE5, 0xF5]:  # PUSH: C5H: BC, D5H: DE, E5H: HL, F5H: AF
            r = {0xC5: "bc", 0xD5: "de", 0xE5: "hl", 0xF5: "af"}[b0]
            return 1, [], f"push {r}", False, None, 0, None
        if b0 in [0xC1, 0xD1, 0xE1, 0xF1]:  # POP : C1H: BC, D1H: DE, E1H: HL, F1H: AF
            r = {0xC1: "bc", 0xD1: "de", 0xE1: "hl", 0xF1: "af"}[b0]
            return 1, [], f"pop {r}", False, None, 0, None

        # 8ビット即値ロード: ld r, n (2バイト)
        # 06H: B, 0EH: C, 16H: D, 1EH: E, 26H: H, 2EH: L, 3EH: A
        if b0 in [0x06, 0x0E, 0x16, 0x1E, 0x26, 0x2E, 0x3E]:
            n = self.mem.get_byte(pc + 1)
            r = REG8[(b0 >> 3) & 7]
            return 2, [], f"ld {r}, {format_asm_hex(n, 2)}", False, None, 0, None

        # 8ビット即値演算: op a, n (2バイト)
        # C6H: ADD, CEH: ADC, D6H: SUB, DEH: SBC, E6H: AND, EEH: XOR, F6H: OR, FEH: CP
        if b0 in [0xC6, 0xCE, 0xD6, 0xDE, 0xE6, 0xEE, 0xF6, 0xFE]:
            n = self.mem.get_byte(pc + 1)
            op = ALU[(b0 >> 3) & 7]
            return 2, [], f"{op} {format_asm_hex(n, 2)}", False, None, 0, None

        # 直接 I/O ポート入出力 (2バイト)
        if b0 == 0xD3:  # out (n), a: ポート n に A を出力
            n = self.mem.get_byte(pc + 1)
            return 2, [], f"out ({format_asm_hex(n, 2)}), a", False, None, 0, None
        if b0 == 0xDB:  # in a, (n): ポート n から A に入力
            n = self.mem.get_byte(pc + 1)
            return 2, [], f"in a, ({format_asm_hex(n, 2)})", False, None, 0, None

        # メモリ直接代入: ld (hl), n (2バイト)
        if b0 == 0x36:
            n = self.mem.get_byte(pc + 1)
            return 2, [], f"ld (hl), {format_asm_hex(n, 2)}", False, None, 0, None

        # リスタート命令: rst p (1バイト: 00H, 08H, 10H, 18H, 20H, 28H, 38H)
        # C7H: 00H, CFH: 08H, D7H: 10H, DFH: 18H, E7H: 20H, EFH: 28H, FFH: 38H
        if b0 in [0xC7, 0xCF, 0xD7, 0xDF, 0xE7, 0xEF, 0xFF]:
            rst_target = b0 & 0x38
            return 1, [rst_target], f"rst {format_asm_hex(rst_target, 2)}", False, None, 0, None

        # 8ビットレジスタ間転送: ld r, r' (1バイト: 40H～7FH、HALT(76H)を除く)
        if 0x40 <= b0 <= 0x7F:
            return 1, [], f"ld {REG8[(b0 >> 3) & 7]}, {REG8[b0 & 7]}", False, None, 0, None

        # 8ビットレジスタ演算: op a, r (1バイト: 80H～BFH)
        # 80H～87H: ADD, 88H～8FH: ADC, 90H～97H: SUB, 98H～9FH: SBC
        # A0H～A7H: AND, A8H～AFH: XOR, B0H～B7H: OR,  B8H～BFH: CP
        if 0x80 <= b0 <= 0xBF:
            return 1, [], f"{ALU[(b0 >> 3) & 7]} {REG8[b0 & 7]}", False, None, 0, None

        # 単一バイト基本命令群 (詳細解説付き)
        one_byte_ops = {
            0x00: "nop",           # 何もしない (No Operation)
            0x02: "ld (bc), a",    # BC の指すアドレスに A を格納
            0x0A: "ld a, (bc)",    # BC の指すアドレスから A に読込
            0x12: "ld (de), a",    # DE の指すアドレスに A を格納
            0x1A: "ld a, (de)",    # DE の指すアドレスから A に読込
            0x03: "inc bc",        # 16ビットインクリメント: BC = BC + 1
            0x13: "inc de",        # 16ビットインクリメント: DE = DE + 1
            0x23: "inc hl",        # 16ビットインクリメント: HL = HL + 1
            0x33: "inc sp",        # 16ビットインクリメント: SP = SP + 1
            0x0B: "dec bc",        # 16ビットデクリメント: BC = BC - 1
            0x1B: "dec de",        # 16ビットデクリメント: DE = DE - 1
            0x2B: "dec hl",        # 16ビットデクリメント: HL = HL - 1
            0x3B: "dec sp",        # 16ビットデクリメント: SP = SP - 1
            0x04: "inc b",         # 8ビットインクリメント: B = B + 1
            0x0C: "inc c",         # 8ビットインクリメント: C = C + 1
            0x14: "inc d",         # 8ビットインクリメント: D = D + 1
            0x1C: "inc e",         # 8ビットインクリメント: E = E + 1
            0x24: "inc h",         # 8ビットインクリメント: H = H + 1
            0x2C: "inc l",         # 8ビットインクリメント: L = L + 1
            0x3C: "inc a",         # 8ビットインクリメント: A = A + 1
            0x05: "dec b",         # 8ビットデクリメント: B = B - 1
            0x0D: "dec c",         # 8ビットデクリメント: C = C - 1
            0x15: "dec d",         # 8ビットデクリメント: D = D - 1
            0x1D: "dec e",         # 8ビットデクリメント: E = E - 1
            0x25: "dec h",         # 8ビットデクリメント: H = H - 1
            0x2D: "dec l",         # 8ビットデクリメント: L = L - 1
            0x3D: "dec a",         # 8ビットデクリメント: A = A - 1
            0x34: "inc (hl)",      # HL の指すメモリの値をインクリメント
            0x35: "dec (hl)",      # HL の指すメモリの値をデクリメント
            0x07: "rlca",          # A を左ローテート (ビット7をキャリーおよびビット0にコピー)
            0x0F: "rrca",          # A を右ローテート (ビット0をキャリーおよびビット7にコピー)
            0x17: "rla",           # A をキャリーを介して左ローテート
            0x1F: "rra",           # A をキャリーを介して右ローテート
            0x27: "daa",           # BCD (2進化10進) 補正演算
            0x2F: "cpl",           # A の各ビットを反転 (1の補数)
            0x37: "scf",           # キャリーフラグをセット (CY = 1)
            0x3F: "ccf",           # キャリーフラグを反転 (CY = ~CY)
            0xD9: "exx",           # 汎用レジスタ群の交換 (BC, DE, HL <=> BC', DE', HL')
            0xE3: "ex (sp), hl",   # スタックトップ (SP) と HL の交換
            0xEB: "ex de, hl",     # DE と HL の交換
            0xF3: "di",            # 割り込み禁止 (Disable Interrupts)
            0xFB: "ei",            # 割り込み許可 (Enable Interrupts)
            0xF9: "ld sp, hl",     # HL の値をスタックポインタ SP にロード
            0x08: "ex af, af'",    # アキュムレータおよびフラグの交換 (AF <=> AF')
            0x09: "add hl, bc",    # 16ビット加算: HL = HL + BC
            0x19: "add hl, de",    # 16ビット加算: HL = HL + DE
            0x29: "add hl, hl",    # 16ビット加算: HL = HL + HL (2倍)
            0x39: "add hl, sp"     # 16ビット加算: HL = HL + SP
        }
        if b0 in one_byte_ops:
            return 1, [], one_byte_ops[b0], False, None, 0, None

        # 未定義の単一バイトは db で出力
        return 1, [], f"db {format_asm_hex(b0, 2)}", False, None, 0, None

# =====================================================================
# アドレスおよびシンボル管理クラス
# =====================================================================
class AddressRegistry:
    """ラベル、シンボル名、変数サイズ、命令開始位置オフセットを集中管理するクラス。"""

    def __init__(self, mem: BinaryImage, logger: DisasmLogger):
        """レジストリを初期化する。

        引数:
            mem (BinaryImage): メモリイメージ
            logger (DisasmLogger): ログ出力インスタンス
        """
        self.mem = mem
        self.logger = logger
        self.labels = {}                    # addr -> ラベル名
        self.var_sizes = {}                 # addr -> アクセスバイト幅 (1 または 2)
        self.byte_to_instruction_start = {} # 各バイトアドレス -> そのバイトが属する命令の先頭アドレス
        self.uncalled_entries = set()       # ギャップ走査で発見された未参照エントリのアドレス集合

    def populate_instruction_map(self):
        """CODE属性が付与された全バイトについて、所属する命令の先頭アドレスへの逆引きマップを構築する。

        自己書き換えコード(SMC)で命令内の即値バイトが書き換えられる場合や、
        テーブル参照等で命令途中のアドレスが参照された場合に「LABEL + offset」表記を生成するために使用する。
        """
        self.byte_to_instruction_start.clear()
        pc = self.mem.base_addr
        decoder = Z80InstructionDecoder(self.mem)
        while pc < self.mem.end_addr:
            if self.mem.has_attribute(pc, "CODE"):
                length, _, _, _, _, _, _ = decoder.decode(pc)
                for i in range(length):
                    addr = pc + i
                    if self.mem.is_valid_address(addr):
                        self.byte_to_instruction_start[addr] = pc
                pc += length
            else:
                pc += 1

    def register_address(self, addr, size=0, is_code=False, is_work=False):
        """指定アドレスをラベルレジストリに登録し、属性に応じたプレフィックスを割り当てる。

        引数:
            addr (int): 登録するメモリアドレス
            size (int): 参照時のデータ幅 (1: byte, 2: word)
            is_code (bool): コードエントリ (CODE_xxxxH) として登録するか
            is_work (bool): ワーク変数 (WORK_xxxxH) として登録するか
        """
        if size > 0:
            cur_sz = self.var_sizes.get(addr, 0)
            if size > cur_sz:
                self.var_sizes[addr] = size

        if addr in self.labels:
            return

        # 外部シンボル定義モジュールからの名称解決
        sym_name = get_symbol_name(addr)
        if sym_name:
            self.labels[addr] = sym_name
            return

        # メモリ領域および属性に応じた命名規則の適用
        if self.mem.is_valid_address(addr):
            if is_code or self.mem.has_attribute(addr, "CODE"):
                self.labels[addr] = f"CODE_{addr:04X}H"
            elif is_work or self.mem.has_attribute(addr, "WORK"):
                self.labels[addr] = f"WORK_{addr:04X}H"
            elif self.mem.has_attribute(addr, "MERGE"):
                self.labels[addr] = f"DATA_{addr:04X}H"
            else:
                self.labels[addr] = f"DATA_{addr:04X}H"
        elif addr >= 0xC000:
            # バイナリ外かつ C000H 以上は MSX の一般的な RAM ワークエリア
            self.labels[addr] = f"WORK_{addr:04X}H"
        else:
            # バイナリ外の前方領域 (BIOS / 拡張ROM領域等)
            self.labels[addr] = f"EXT_{addr:04X}H"

    def get_label(self, addr):
        """指定アドレスに対応するアセンブリ表記（ラベル名、オフセット加算式、または16進数値）を返す。

        引数:
            addr (int): 対象アドレス

        戻り値:
            str: ソースコードに展開する文字列表記
        """
        # 特殊ケース: MSX の拡張スロット選択テーブル EXPTBL (FCC1H) の手前アドレス (FCC0H) は
        # アセンブラコード上で EXPTBL - 1 として表現される慣例に対応する
        if addr == 0xFCC0:
            if 0xFCC1 not in self.labels:
                self.register_address(0xFCC1)
            base_lbl = self.labels.get(0xFCC1, "EXPTBL")
            return f"{base_lbl} - 1"

        # 自己書き換えコード(SMC)や複数バイト命令の内部オペランドを参照している場合、
        # 「命令先頭ラベル + オフセット」形式で出力する (例: CODE_4020H + 1)
        if addr in self.byte_to_instruction_start:
            inst_start = self.byte_to_instruction_start[addr]
            offset = addr - inst_start
            if offset > 0:
                if inst_start not in self.labels:
                    self.register_address(inst_start, is_code=True)
                base_lbl = self.labels[inst_start]
                return f"{base_lbl} + {offset}"

        if addr in self.labels:
            return self.labels[addr]
        return format_asm_hex(addr)


# =====================================================================
# 実行フロー解析クラス
# =====================================================================
class Z80FlowAnalyser:
    """実行パスのシミュレーションを行い、コード・データ・ワークエリアの属性判別とポインタ逆引きを行うクラス。"""

    def __init__(self, mem: BinaryImage, registry: AddressRegistry, logger: DisasmLogger, max_merge_limit=2):
        """フロー解析インスタンスを初期化する。

        引数:
            mem (BinaryImage): メモリイメージ
            registry (AddressRegistry): アドレス・ラベル管理レジストリ
            logger (DisasmLogger): ログ出力インスタンス
            max_merge_limit (int): WORK領域に隣接する未参照DATAをマージする上限バイト数
        """
        self.mem = mem
        self.registry = registry
        self.logger = logger
        self.max_merge_limit = max_merge_limit
        self.decoder = Z80InstructionDecoder(mem)

        # ポインタ (メモリアドレス) を保持しているRAMワークエリアのアドレス集合
        self.pointer_work_addresses = set()
        # ポインタアドレスをレジスタへロードしている命令のPC集合
        self.pointer_load_pcs = set()
        # 探索済み経路の追跡状態キー (同一状態での無限ループ解析を防止)
        self.traced_paths = set()

        # ログ重複出力防止用の管理セット
        self.logged_pointer_writes = set()
        self.logged_pointer_works = set()
        self.logged_interrupt_hooks = set()
        self.logged_jump_tables = set()
        self.logged_sys_args = set()

    def analyze_flow(self, entry_points):
        """指定されたエントリポイントから実行フロー解析を実行する。

        処理順が重要な2パス構成で実行する:
        - パス 1: 全分岐の走査、レジスタへの即値ロード追跡、書き込み先ワーク領域の特定
        - パス 2: 特定されたポインタ用ワークエリアへの代入箇所を再走査し、動的参照先を確定

        引数:
            entry_points (list[int]): 解析開始アドレスのリスト
        """
        self.logged_pointer_writes.clear()
        self.logged_pointer_works.clear()
        self.logged_interrupt_hooks.clear()
        self.logged_jump_tables.clear()
        self.logged_sys_args.clear()

        # パス 1: 基本フロー走査
        self.logger.log("=" * 70)
        self.logger.log("[*] 解析 Pass 1: 実行フローおよびレジスタ・ポインタの追跡を開始...")
        self.logger.log("=" * 70)
        self._trace_from_entries(entry_points)

        # パス 2: 間接参照ポインタの再走査シミュレーション
        self.logger.log("=" * 70)
        self.logger.log("[*] 解析 Pass 2: 間接参照ポインタの再走査シミュレーション...")
        self.logger.log("=" * 70)
        self.traced_paths.clear()
        self._trace_from_entries(entry_points)

    def _trace_from_entries(self, entries):
        """エントリポイント一覧から深さ優先で静的フロー追跡を実行する。

        レジスタの値(val)とロード元命令アドレス(source_pc)を追跡し、
        間接参照 (HL), (DE), (BC), (IX+d), (IY+d) が実行された際に
        ポインタの発生元を逆引きしてシンボル登録を行う。
        """
        stack = []
        for e in entries:
            if self.mem.is_valid_address(e):
                stack.append((e, {
                    "regs": {
                        "BC": {"val": 0, "source_pc": None, "source_val": 0},
                        "DE": {"val": 0, "source_pc": None, "source_val": 0},
                        "HL": {"val": 0, "source_pc": None, "source_val": 0},
                        "IX": {"val": 0, "source_pc": None, "source_val": 0},
                        "IY": {"val": 0, "source_pc": None, "source_val": 0},
                        "A":  {"val": 0, "source_pc": None, "source_val": 0},
                        "B":  {"val": 0, "source_pc": None, "source_val": 0},
                        "C":  {"val": 0, "source_pc": None, "source_val": 0},
                    },
                    "mem_loads": {}, # レジスタ名 -> ロード元ワークメモリアドレス
                    "history": []    # 【不具合修正】各実行経路に閉じた直近命令履歴 (履歴汚染を防止)
                }))

        while stack:
            pc, tracker_state = stack.pop()
            if not self.mem.is_valid_address(pc):
                continue

            # ループ検知: 同じPCかつ同じレジスタ起源状態で訪問済みの場合は枝刈り
            state_key = (
                pc,
                tracker_state["regs"]["HL"]["source_pc"],
                tracker_state["regs"]["DE"]["source_pc"],
                tracker_state["regs"]["BC"]["source_pc"],
                tracker_state["regs"]["IX"]["source_pc"],
                tracker_state["regs"]["IY"]["source_pc"]
            )
            if state_key in self.traced_paths:
                continue
            self.traced_paths.add(state_key)

            regs = copy.deepcopy(tracker_state["regs"])
            mem_loads = copy.deepcopy(tracker_state["mem_loads"])
            history = list(tracker_state["history"]) # 現在の実行経路の履歴を複製

            length, branch_targets, _, is_terminal, access_addr, access_sz, imm16 = self.decoder.decode(pc)

            # 確定した命令バイトを CODE 属性にマーク (DATA属性から除外)
            for i in range(length):
                cur_a = pc + i
                self.mem.discard_attribute(cur_a, "DATA")
                self.mem.mark_attribute(cur_a, "CODE")

            opcode = self.mem.get_byte(pc)

            # ---------------------------------------------------------
            # 16ビット即値ロード命令の追跡 (ld rp, nn)
            # ---------------------------------------------------------
            if imm16 is not None:
                # 01H: ld bc, nn / 11H: ld de, nn / 21H: ld hl, nn
                if opcode in [0x01, 0x11, 0x21]:
                    rname = {0x01: "BC", 0x11: "DE", 0x21: "HL"}[opcode]
                    regs[rname] = {"val": imm16, "source_pc": pc, "source_val": imm16}
                    mem_loads.pop(rname, None)
                    if opcode == 0x01:
                        # Cレジスタ (下位バイト) および Bレジスタ (上位バイト) も個別追跡
                        regs["C"] = {"val": imm16 & 0xFF, "source_pc": pc, "source_val": imm16 & 0xFF}
                        regs["B"] = {"val": (imm16 >> 8) & 0xFF, "source_pc": pc, "source_val": (imm16 >> 8) & 0xFF}
                # DD 21H: ld ix, nn / FD 21H: ld iy, nn
                elif opcode in [0xDD, 0xFD]:
                    sub_op = self.mem.get_byte(pc + 1)
                    if sub_op == 0x21:
                        rname = "IX" if opcode == 0xDD else "IY"
                        regs[rname] = {"val": imm16, "source_pc": pc, "source_val": imm16}
                        mem_loads.pop(rname, None)

            # ---------------------------------------------------------
            # 8ビット即値ロード命令の追跡 (ld r, n)
            # ---------------------------------------------------------
            # 06H: ld b, n / 0EH: ld c, n / 16H: ld d, n / 1EH: ld e, n
            # 26H: ld h, n / 2EH: ld l, n / 3EH: ld a, n
            if opcode in [0x06, 0x0E, 0x16, 0x1E, 0x26, 0x2E, 0x3E]:
                r_map = {0x06: "B", 0x0E: "C", 0x16: "D", 0x1E: "E", 0x26: "H", 0x2E: "L", 0x3E: "A"}
                r_name = r_map[opcode]
                n = self.mem.get_byte(pc + 1)
                regs[r_name] = {"val": n, "source_pc": pc, "source_val": n}

            # ---------------------------------------------------------
            # ワークエリアからのメモリロード追跡 (ld rp, (nn))
            # ---------------------------------------------------------
            if opcode == 0x2A:          # 2AH: ld hl, (nn)
                mem_loads["HL"] = access_addr
            elif opcode == 0xED:
                sub_op = self.mem.get_byte(pc + 1)
                if sub_op == 0x4B:      # ED 4BH: ld bc, (nn)
                    mem_loads["BC"] = access_addr
                elif sub_op == 0x5B:    # ED 5BH: ld de, (nn)
                    mem_loads["DE"] = access_addr
            elif opcode in [0xDD, 0xFD]:
                sub_op = self.mem.get_byte(pc + 1)
                if sub_op == 0x2A:      # DD/FD 2AH: ld ix/iy, (nn)
                    rname = "IX" if opcode == 0xDD else "IY"
                    mem_loads[rname] = access_addr

            # ---------------------------------------------------------
            # メモリへの書き込み命令の検出 (WORK属性の決定)
            # ---------------------------------------------------------
            if access_addr is not None:
                is_write = False
                w_reg = None
                # 32H: ld (nn), a / 22H: ld (nn), hl
                if opcode in [0x32, 0x22]:
                    is_write = True
                    w_reg = "A" if opcode == 0x32 else "HL"
                elif opcode == 0xED:
                    sub_op = self.mem.get_byte(pc + 1)
                    # ED 43H: ld (nn), bc / ED 53H: ld (nn), de / ED 73H: ld (nn), sp
                    if sub_op in [0x43, 0x53, 0x73]:
                        is_write = True
                        w_reg = {0x43: "BC", 0x53: "DE", 0x73: "SP"}[sub_op]
                elif opcode in [0xDD, 0xFD]:
                    sub_op = self.mem.get_byte(pc + 1)
                    # DD/FD 22H: ld (nn), ix / ld (nn), iy
                    if sub_op == 0x22:
                        is_write = True
                        w_reg = "IX" if opcode == 0xDD else "IY"

                if is_write:
                    # 書き込み先は静的DATAではなく変数領域(WORK)としてマーク
                    self.mem.mark_attribute(access_addr, "WORK")
                    self.mem.discard_attribute(access_addr, "DATA")
                    self.registry.register_address(access_addr, size=access_sz, is_work=True)

                    # MSX 割り込みフック登録の検出 (例: ld (H_TIMI), hl 等)
                    if access_addr in MSX_HOOK_ADDRS and w_reg in regs:
                        h_addr = regs[w_reg]["val"]
                        h_src_pc = regs[w_reg]["source_pc"]
                        if self.mem.is_valid_address(h_addr):
                            log_key = (access_addr, h_addr, h_src_pc)
                            if log_key not in self.logged_interrupt_hooks:
                                self.logged_interrupt_hooks.add(log_key)
                                self.logger.log(
                                    f"[+] 割り込みフック登録を検出: {format_asm_hex(access_addr)} <- ハンドラ: "
                                    f"{format_asm_hex(h_addr)} (PC: {format_asm_hex(pc)})"
                                )
                            # フック先ハンドラをコードエントリとして追跡スタックに追加
                            self.registry.register_address(h_addr, is_code=True)
                            stack.append((h_addr, {
                                "regs": copy.deepcopy(regs),
                                "mem_loads": copy.deepcopy(mem_loads),
                                "history": list(history)
                            }))

                    # ポインタ保持用ワークエリアへの書き込み検出
                    if access_addr in self.pointer_work_addresses and w_reg in regs:
                        s_pc = regs[w_reg]["source_pc"]
                        s_val = regs[w_reg]["source_val"]
                        if s_pc is not None and self.mem.is_valid_address(s_val):
                            self.pointer_load_pcs.add(s_pc)
                            self.registry.register_address(s_val)
                            log_key = (access_addr, s_val, s_pc)
                            if log_key not in self.logged_pointer_writes:
                                self.logged_pointer_writes.add(log_key)
                                self.logger.log(
                                    f"[+] 間接参照アドレス用WORK代入を検出: WORK: {format_asm_hex(access_addr)} "
                                    f"<- 値: {format_asm_hex(s_val)} (ロード位置: {format_asm_hex(s_pc)})"
                                )
                else:
                    self.registry.register_address(access_addr, size=access_sz)

            # ---------------------------------------------------------
            # 間接参照ポインタの検出 (HL, DE, BC, IX, IY による間接アクセス)
            # ---------------------------------------------------------
            # (HL) 間接参照:
            # 40H～7FH のうち (HL) 参照命令 (76H HALT 除く)、80H～BFH の (HL) 演算命令、36H: ld (hl), n
            is_ind_hl = (0x40 <= opcode <= 0x7F and (opcode & 7) == 6 and opcode != 0x76) or \
                        (0x80 <= opcode <= 0xBF and (opcode & 7) == 6) or (opcode == 0x36)
            if opcode == 0xCB:
                # CBプレフィックス下位3ビットが 6 の場合: rlc (hl), bit b, (hl) 等
                sub_cb = self.mem.get_byte(pc + 1)
                if (sub_cb & 7) == 6:
                    is_ind_hl = True

            if is_ind_hl:
                self._handle_pointer_dereference("HL", pc, regs, mem_loads)
            elif opcode in [0x0A, 0x02]: # 0AH: ld a, (bc) / 02H: ld (bc), a
                self._handle_pointer_dereference("BC", pc, regs, mem_loads)
            elif opcode in [0x1A, 0x12]: # 1AH: ld a, (de) / 12H: ld (de), a
                self._handle_pointer_dereference("DE", pc, regs, mem_loads)
            elif opcode in [0xDD, 0xFD]:
                sub_op = self.mem.get_byte(pc + 1)
                reg_name = "IX" if opcode == 0xDD else "IY"
                is_ind_idx = False
                if sub_op == 0xCB:
                    is_ind_idx = True # DDCB / FDCB は常に (IX+d) / (IY+d) 間接アクセス
                elif sub_op in [0x34, 0x35, 0x36]: # inc/dec/ld (ix+d), n
                    is_ind_idx = True
                elif 0x40 <= sub_op <= 0xBF and sub_op != 0x76:
                    if ((sub_op >> 3) & 7) == 6 or (sub_op & 7) == 6:
                        is_ind_idx = True
                if is_ind_idx:
                    self._handle_pointer_dereference(reg_name, pc, regs, mem_loads)
            elif opcode == 0xED:
                sub_op = self.mem.get_byte(pc + 1)
                # ブロック転送命令による HL(転送元) / DE(転送先) の間接参照
                # A0H: LDI, B0H: LDIR, A8H: LDD, B8H: LDDR
                if sub_op in [0xA0, 0xB0, 0xA8, 0xB8]:
                    self._handle_pointer_dereference("HL", pc, regs, mem_loads)
                    self._handle_pointer_dereference("DE", pc, regs, mem_loads)

            # ---------------------------------------------------------
            # システムコール引数の検出 (RST 30H または CALL BIOS/BDOS)
            # ---------------------------------------------------------
            if opcode == 0xF7:  # RST 30H (MSX CALSLT)
                target_sys = self.mem.get_word(pc + 2)
                self._check_system_args(target_sys, regs)
            for tgt in branch_targets:
                self._check_system_args(tgt, regs)
                self.registry.register_address(tgt, is_code=True)
                if self.mem.is_valid_address(tgt):
                    stack.append((tgt, {
                        "regs": copy.deepcopy(regs),
                        "mem_loads": copy.deepcopy(mem_loads),
                        "history": list(history)
                    }))

            # ---------------------------------------------------------
            # ジャンプテーブルの検出と追跡
            # ---------------------------------------------------------
            # E9H: jp (hl)
            if opcode == 0xE9:
                self._detect_and_expand_jump_table("HL", history, stack, regs, mem_loads)
            # DD E9H: jp (ix) / FD E9H: jp (iy)
            elif opcode in [0xDD, 0xFD] and self.mem.get_byte(pc + 1) == 0xE9:
                target_reg = "IX" if opcode == 0xDD else "IY"
                self._detect_and_expand_jump_table(target_reg, history, stack, regs, mem_loads)

            # 連続するJPテーブル (C3H xx xx が直後に連続して配置されている領域) の追跡
            if opcode == 0xC3:
                next_pc = pc + 3
                if self.mem.is_valid_address(next_pc) and self.mem.get_byte(next_pc) == 0xC3:
                    stack.append((next_pc, {
                        "regs": copy.deepcopy(regs),
                        "mem_loads": copy.deepcopy(mem_loads),
                        "history": list(history)
                    }))

            # 現在の実行経路の命令履歴を更新 (直近12命令分を保持)
            history.append((pc, opcode, imm16))
            if len(history) > 12:
                history.pop(0)

            # フォールスルー (無条件分岐命令以外は後続命令もスタックに追加)
            if not is_terminal:
                stack.append((pc + length, {
                    "regs": copy.deepcopy(regs),
                    "mem_loads": copy.deepcopy(mem_loads),
                    "history": list(history)
                }))

    def _handle_pointer_dereference(self, reg_name, pc, regs, mem_loads):
        """レジスタ間接参照命令の発生時に、ポインタの参照先および元変数を登録する。

        引数:
            reg_name (str): 間接参照を行っているレジスタ名 ("HL", "DE", "BC", "IX", "IY")
            pc (int): 間接参照命令の実行アドレス
            regs (dict): 現在のレジスタ追跡辞書
            mem_loads (dict): メモリからのロード履歴辞書
        """
        if reg_name in mem_loads:
            w_addr = mem_loads[reg_name]
            if w_addr not in self.pointer_work_addresses:
                self.pointer_work_addresses.add(w_addr)
                if w_addr not in self.logged_pointer_works:
                    self.logged_pointer_works.add(w_addr)
                    self.logger.log(f"[*] アドレス格納用WORKを検出: [{format_asm_hex(w_addr)}] (reg: {reg_name}, PC: {format_asm_hex(pc)})")

        reg_info = regs.get(reg_name)
        if reg_info and reg_info["source_pc"] is not None:
            src_pc = reg_info["source_pc"]
            ptr_val = reg_info["val"]
            self.pointer_load_pcs.add(src_pc)
            # バイナリ内、またはRAM領域(C000H以上)ならシンボル登録
            if self.mem.is_valid_address(ptr_val) or ptr_val >= 0xC000:
                is_work = (ptr_val >= 0xC000)
                self.registry.register_address(ptr_val, size=1, is_work=is_work)

    def _check_system_args(self, target_addr, regs):
        """呼び出される BIOS / BDOS エントリの引数レジスタに渡されたポインタを登録する。

        引数:
            target_addr (int): 呼び出し先システムエントリのアドレス
            regs (dict): 現在のレジスタ追跡辞書
        """
        # MSX BIOS コールの引数ポインタ判定
        if target_addr in BIOS_MEM_ARGS:
            for rname in BIOS_MEM_ARGS[target_addr]:
                if regs.get(rname) and regs[rname]["source_pc"] is not None:
                    arg_addr = regs[rname]["val"]
                    if self.mem.is_valid_address(arg_addr):
                        log_key = (target_addr, rname, arg_addr)
                        if log_key not in self.logged_sys_args:
                            self.logged_sys_args.add(log_key)
                            self.logger.log(
                                f"[+] システム引数参照を検出: {format_asm_hex(target_addr)} 用 "
                                f"{rname}={format_asm_hex(arg_addr)}"
                            )
                        self.registry.register_address(arg_addr)
                        self.pointer_load_pcs.add(regs[rname]["source_pc"])

        # MSX-DOS BDOS コールの引数ポインタ判定
        elif target_addr in BDOS_ENTRY_ADDRS:
            fn_code = regs.get("C", {}).get("val")
            if fn_code in BDOS_ARG_REGS:
                for rname in BDOS_ARG_REGS[fn_code]:
                    if regs.get(rname) and regs[rname]["source_pc"] is not None:
                        arg_addr = regs[rname]["val"]
                        if self.mem.is_valid_address(arg_addr):
                            log_key = (target_addr, fn_code, rname, arg_addr)
                            if log_key not in self.logged_sys_args:
                                self.logged_sys_args.add(log_key)
                                self.logger.log(
                                    f"[+] BDOS Fn {format_asm_hex(fn_code, 2)} 引数参照を検出: "
                                    f"{rname}={format_asm_hex(arg_addr)}"
                                )
                            self.registry.register_address(arg_addr)
                            self.pointer_load_pcs.add(regs[rname]["source_pc"])

    def _detect_and_expand_jump_table(self, target_reg, history, stack, regs, mem_loads):
        """JP (HL) / JP (IX) パターンからジャンプテーブルのベースアドレスを特定し分岐先を回収する。

        【不具合修正・ロジック強化】
        直前の実行履歴（同一経路のみ）からベースアドレス候補を探索し、
        さらにテーブル参照イディオムの妥当性を検証した上で安全に分岐先を展開する。

        引数:
            target_reg (str): ジャンプに使用されたレジスタ ("HL", "IX", "IY")
            history (list): その実行経路で直前に実行された命令履歴
            stack (list): 解析待ちスタック
            regs (dict): レジスタ状態辞書
            mem_loads (dict): メモリロード状態辞書
        """
        table_base = None
        has_table_calc = False

        # 直前の履歴を逆順に走査し、テーブルベースロードとポインタ計算のイディオムを照合
        for h_pc, h_op, h_imm in reversed(history):
            # 29H: add hl, hl / 09H: add hl, bc / 19H: add hl, de などのテーブル加算
            if target_reg == "HL" and h_op in [0x09, 0x19, 0x29]:
                has_table_calc = True
            elif target_reg in ["IX", "IY"] and h_op in [0x09, 0x19]:
                has_table_calc = True

            # テーブルベースアドレスのロード命令を特定
            if target_reg == "HL" and h_op == 0x21 and h_imm is not None:  # 21H: ld hl, nn
                table_base = h_imm
                break
            elif target_reg == "IX" and h_op == 0xDD and h_imm is not None:  # DD 21H: ld ix, nn
                table_base = h_imm
                break
            elif target_reg == "IY" and h_op == 0xFD and h_imm is not None:  # FD 21H: ld iy, nn
                table_base = h_imm
                break

        if table_base is None or not self.mem.is_valid_address(table_base):
            return

        self.registry.register_address(table_base)
        cur_ptr = table_base
        invalid_consecutive = 0
        collected_targets = []

        # テーブルから2バイト単位 (リトルエンディアン) でターゲットアドレスを走査
        while self.mem.is_valid_address(cur_ptr):
            if cur_ptr > table_base:
                # 既に別ラベルが定義されている、あるいは確定済みCODE領域に衝突した場合は終了
                if cur_ptr in self.registry.labels:
                    break
                if self.mem.has_attribute(cur_ptr, "CODE"):
                    break

            # 1つのテーブルの走査上限は安全のため 512 バイト (256エントリ) とする
            if (cur_ptr - table_base) >= 512:
                break

            tgt_addr = self.mem.get_word(cur_ptr)
            # アドレスの妥当性検証 (バイナリ範囲内かつ 0000H, FFFFH でないこと)
            is_valid = self.mem.is_valid_address(tgt_addr) and tgt_addr not in [0x0000, 0xFFFF]

            if is_valid:
                invalid_consecutive = 0
                self.registry.register_address(tgt_addr, is_code=True)
                stack.append((tgt_addr, {
                    "regs": copy.deepcopy(regs),
                    "mem_loads": copy.deepcopy(mem_loads),
                    "history": list(history)
                }))
                collected_targets.append(tgt_addr)
            else:
                invalid_consecutive += 1
                # 無効なアドレスが2ワード連続した時点でテーブル終端と判定
                if invalid_consecutive >= 2:
                    break
            cur_ptr += 2

        if collected_targets and table_base not in self.logged_jump_tables:
            self.logged_jump_tables.add(table_base)
            tbl_end = cur_ptr - 1
            min_tgt = min(collected_targets)
            max_tgt = max(collected_targets)
            self.logger.log(
                f"[+] ジャンプテーブルを自動検出: {format_asm_hex(table_base)} - {format_asm_hex(tbl_end)} "
                f"({len(collected_targets)} エントリ)"
            )
            self.logger.log(
                f"    - 分岐先範囲: {format_asm_hex(min_tgt)} - {format_asm_hex(max_tgt)}"
            )

    def run_gap_sweep(self):
        """CODE属性の間に挟まれた未参照ブロック(間接コール等で通常の追跡から漏れたルーチン)を検出し、追加解析を行う。"""
        new_entries = []
        in_gap = False
        gap_start = None

        referenced = set(self.registry.labels.keys())

        for addr in range(self.mem.base_addr, self.mem.end_addr):
            is_code = self.mem.has_attribute(addr, "CODE")
            is_work = self.mem.has_attribute(addr, "WORK")

            if not is_code and not is_work:
                # 直前がCODEで現在地がDATA(未確定)の場合、ギャップの開始とみなす
                if not in_gap:
                    if addr > self.mem.base_addr and self.mem.has_attribute(addr - 1, "CODE"):
                        in_gap = True
                        gap_start = addr
            else:
                if in_gap:
                    gap_end = addr - 1
                    # ギャップの終端が再びCODEに接続しており、かつ内部に既存ラベル参照が存在しない場合
                    if is_code and gap_end >= gap_start:
                        has_ref = any(a in referenced for a in range(gap_start, gap_end + 1))
                        if not has_ref:
                            first_b = self.mem.get_byte(gap_start)
                            # パディング (00H や FFH の連続) でなければ未呼び出しコードエントリとして回収
                            if first_b not in [0x00, 0xFF]:
                                self.logger.log(f"[*] 未参照コードブロックを検出: {format_asm_hex(gap_start)} - {format_asm_hex(gap_end)}")
                                new_entries.append(gap_start)
                                self.registry.register_address(gap_start, is_code=True)
                                self.registry.uncalled_entries.add(gap_start)
                    in_gap = False

        # 発見した未参照ブロックの先頭から再度フロー解析を実行
        if new_entries:
            self._trace_from_entries(new_entries)

    def merge_unreferenced_work_data(self):
        """WORK変数の直後に存在する未参照の短いDATA領域をMERGE属性として統合する。

        ROMバイナリ内でワークエリアや変数の直後に存在する1～2バイトの余白（パディングや
        複数バイト変数の後続バイト）が孤立した db として出力されるのを抑制する。
        """
        if self.max_merge_limit < 1:
            return

        for addr in range(self.mem.base_addr, self.mem.end_addr):
            if self.mem.has_attribute(addr, "WORK"):
                next_addr = addr + 1
                merge_count = 0
                while next_addr < self.mem.end_addr:
                    if next_addr in self.registry.labels or self.mem.has_attribute(next_addr, "WORK"):
                        break
                    if merge_count >= self.max_merge_limit:
                        break
                    if (self.mem.has_attribute(next_addr, "DATA") and
                            not self.mem.has_attribute(next_addr, "CODE") and
                            not self.mem.has_attribute(next_addr, "WORK")):
                        self.mem.mark_attribute(next_addr, "MERGE")
                        self.mem.discard_attribute(next_addr, "DATA")
                        merge_count += 1
                        next_addr += 1
                    else:
                        break

# =====================================================================
# 出力生成クラス
# =====================================================================
class DisassemblyOutputGenerator:
    """解析結果をもとに、再アセンブル可能な標準 Z80 アセンブラソースを出力するクラス。"""

    def __init__(self, mem: BinaryImage, registry: AddressRegistry, logger: DisasmLogger,
                 input_file, file_format, base_addr, end_addr, header_addr, entry_addr, output_path):
        """ジェネレータを初期化する。

        引数:
            mem (BinaryImage): メモリイメージ
            registry (AddressRegistry): シンボルレジストリ
            logger (DisasmLogger): ロガーインスタンス
            input_file (str): 入力ファイルパス
            file_format (str): ファイル形式 ("ROM", "COM", "BLOAD")
            base_addr (int): 配置開始アドレス
            end_addr (int): 配置終了アドレス (Exclusive: 終端アドレス + 1)
            header_addr (int or None): ROMヘッダアドレス
            entry_addr (int or None): エントリポイントアドレス
            output_path (str): 出力先 asm ファイルパス
        """
        self.mem = mem
        self.registry = registry
        self.logger = logger
        self.input_file = input_file
        self.file_format = file_format
        self.base_addr = base_addr
        self.end_addr = end_addr
        self.header_addr = header_addr
        self.entry_addr = entry_addr
        self.output_path = output_path
        self.decoder = Z80InstructionDecoder(mem, is_com_format=(file_format == "COM"))

    def generate(self):
        """ヘッダ、シンボル定義 (EQU)、および逆アセンブル本文をアセンブリソースとして書き出す。"""
        self.logger.log(f"[*] アセンブリソースを出力中: {self.output_path}")

        bios_symbols = []
        system_work_symbols = []
        user_work_symbols = []
        external_symbols = []

        # バイナリ外のアドレスをカテゴリ別に分類して EQU 定義セクションを生成
        for addr, name in self.registry.labels.items():
            if self.mem.is_valid_address(addr):
                continue
            if addr < 0x4000:
                # 0000H～3FFFH: MSX メインBIOS / 拡張BIOSルーチン
                bios_symbols.append((addr, name))
            elif addr >= 0xF380:
                # F380H～FFFFH: MSX システムワークエリア
                system_work_symbols.append((addr, name))
            elif name.startswith("WORK_") or (0xC000 <= addr < 0xF380):
                # C000H～F37FH: 一般ユーザーRAMワークエリア
                user_work_symbols.append((addr, name))
            else:
                # その他の外部参照アドレス
                external_symbols.append((addr, name))

        with open(self.output_path, "w", encoding="utf-8") as out:
            # 表示用のアドレス範囲文字列 (開始アドレス - 最終包含アドレス)
            range_str = f"{format_asm_hex(self.base_addr)} - {format_asm_hex(self.mem.last_addr)}"

            out.write("; " + "=" * 70 + "\n")
            out.write("; MSX Z80 Intelligent Disassembler Output\n")
            out.write(f"; Source: {os.path.basename(self.input_file)}\n") 
            out.write(f"; Format: {self.file_format}\n")
            out.write(f"; Range : {range_str}\n")
            if self.header_addr is not None:
                out.write(f"; Header: {format_asm_hex(self.header_addr)}\n")
            if self.entry_addr is not None:
                out.write(f"; Entry : {format_asm_hex(self.entry_addr)}\n")
            out.write("; " + "=" * 70 + "\n\n")

            # MSX BIOS およびシステムフックの EQU 出力
            if bios_symbols:
                out.write("; === MSX BIOS & System Hooks ===\n")
                for addr, name in sorted(bios_symbols, key=lambda x: x[0]):
                    out.write(f"{name:16} EQU {format_asm_hex(addr)}\n")
                out.write("\n")

            # MSX システムワークエリア (F380H～) の EQU 出力
            if system_work_symbols:
                out.write("; === System Work Area ===\n")
                for addr, name in sorted(system_work_symbols, key=lambda x: x[0]):
                    sz = self.registry.var_sizes.get(addr, 0)
                    sz_cmt = f" ; {sz} byte{'s' if sz > 1 else ''}" if sz > 0 else ""
                    out.write(f"{name:16} EQU {format_asm_hex(addr)}{sz_cmt}\n")
                out.write("\n")

            # ユーザーRAMワーク領域 (C000H～) の EQU 出力
            if user_work_symbols:
                out.write("; === User Work Area (RAM) ===\n")
                sorted_uw = sorted(user_work_symbols, key=lambda x: x[0])
                for i, (addr, name) in enumerate(sorted_uw):
                    size = self.registry.var_sizes.get(addr, 0)
                    diff = None
                    if i + 1 < len(sorted_uw):
                        diff = sorted_uw[i + 1][0] - addr
                    if size == 2: comment = "; 2 bytes (word)"
                    elif size == 1: comment = "; 1 byte"
                    elif diff and diff > 1: comment = f"; {diff} bytes"
                    else: comment = "; 1 byte"
                    out.write(f"{name:16} EQU {format_asm_hex(addr)}    {comment}\n")
                out.write("\n")

            # 外部シンボルの EQU 出力
            if external_symbols:
                out.write("; === External Symbols ===\n")
                for addr, name in sorted(external_symbols, key=lambda x: x[0]):
                    out.write(f"{name:16} EQU {format_asm_hex(addr)}\n")
                out.write("\n")

            out.write(f"    ORG {format_asm_hex(self.base_addr)}\n\n")

            pc = self.base_addr
            while pc < self.mem.end_addr:
                # MSX ROM 'AB' ヘッダ構造の整形出力 (INIT, STATEMENT, DEVICE, TEXT)
                if self.header_addr is not None and pc == self.header_addr:
                    # 'A' = 41H, 'B' = 42H のシグネチャ照合
                    if self.mem.get_byte(pc) == 0x41 and self.mem.get_byte(pc + 1) == 0x42:
                        out.write("\nROM_HEADER:\n")
                        out.write('    db  "AB"\n')
                        init_p = self.mem.get_word(pc + 2)  # 初期化ルーチンアドレス
                        stmt_p = self.mem.get_word(pc + 4)  # 拡張ステートメントハンドラアドレス
                        dev_p  = self.mem.get_word(pc + 6)  # 拡張デバイスハンドラアドレス
                        text_p = self.mem.get_word(pc + 8)  # BASICプログラムテキストアドレス

                        def get_l(a):
                            return self.registry.get_label(a) if a else "0000H"

                        out.write(f"    dw  {get_l(init_p)} ; INIT\n")
                        out.write(f"    dw  {get_l(stmt_p)} ; STATEMENT\n")
                        out.write(f"    dw  {get_l(dev_p)}  ; DEVICE\n")
                        out.write(f"    dw  {get_l(text_p)} ; TEXT\n")
                        reserved = [format_asm_hex(self.mem.get_byte(pc + 10 + i), 2) for i in range(6)]
                        out.write(f"    db  {', '.join(reserved)} ; Reserved\n\n")
                        pc += 16
                        continue

                # 行頭ラベルの出力
                if pc in self.registry.labels:
                    label_name = self.registry.labels[pc]
                    comment = " ; [Uncalled code]" if pc in self.registry.uncalled_entries else ""
                    out.write(f"\n{label_name}:{comment}\n")

                # 命令 (CODE) と静的データ (DATA / MERGE) の切り替え出力
                if self.mem.has_attribute(pc, "CODE"):
                    length, _, text, _, _, _, _ = self.decoder.decode(pc, self.registry.get_label)
                    out.write(f"    {text}\n")
                    pc += length
                else:
                    # DATA領域: 最大16バイト単位で db 文にまとめて出力
                    db_bytes = [self.mem.get_byte(pc)]
                    pc += 1
                    while pc < self.mem.end_addr and not self.mem.has_attribute(pc, "CODE"):
                        if self.header_addr is not None and pc == self.header_addr:
                            break
                        if pc in self.registry.labels:
                            break
                        if len(db_bytes) >= 16:
                            break
                        db_bytes.append(self.mem.get_byte(pc))
                        pc += 1

                    tokens = [format_asm_hex(b, 2) for b in db_bytes]
                    out.write(f"    db  {', '.join(tokens)}\n")


# =====================================================================
# メイン処理統括クラス
# =====================================================================
class MsxDisassembler:
    """バイナリの形式判定、解析コンポーネントの連携、最終レポート出力を統括するメインクラス。"""

    def __init__(self, input_file, output_file, base_addr=0x4000, header_addr=None,
                 format_override=None, extra_entries=None, extra_tables=None,
                 enable_gap_scan=False, merge_limit=2):
        """ディスアセンブラの実行パラメータを設定する。

        引数:
            input_file (str): 入力バイナリパス
            output_file (str): 出力 asm ファイルパス
            base_addr (int): 配置開始アドレス
            header_addr (int or None): ROMヘッダアドレス
            format_override (str or None): "COM", "BLOAD" などの強制指定
            extra_entries (list[int]): 手動指定エントリポイント
            extra_tables (list[tuple]): 手動指定ジャンプテーブル [(base, count), ...]
            enable_gap_scan (bool): 未参照コードブロック回収を行うか
            merge_limit (int): DATAマージ上限バイト数
        """
        self.input_file = input_file
        self.output_file = output_file
        self.log_file = os.path.splitext(output_file)[0] + ".log"
        self.base_addr = base_addr
        self.header_addr = header_addr
        self.format_override = format_override
        self.extra_entries = extra_entries or []
        self.extra_tables = extra_tables or []
        self.enable_gap_scan = enable_gap_scan
        self.merge_limit = merge_limit

        self.logger = DisasmLogger(self.log_file)
        self.file_format = "ROM"
        self.end_addr = None        # Exclusive (終端アドレス + 1)
        self.primary_entry = None

    def run(self):
        """バイナリ読み込み、フォーマット判別、フロー解析、ソース出力を一連で実行する。"""
        if not os.path.exists(self.input_file):
            print(f"[-] エラー: 入力ファイル '{self.input_file}' が存在しません。")
            sys.exit(1)

        with open(self.input_file, "rb") as f:
            raw_data = bytearray(f.read())

        file_size = len(raw_data)
        data = raw_data

        is_bload = False
        is_com = False

        # バイナリフォーマット (BLOAD, COM, ROM) の自動判別
        if self.format_override == "BLOAD":
            is_bload = True
        elif self.format_override == "COM":
            is_com = True
        else:
            _, ext = os.path.splitext(self.input_file.lower())
            if ext == ".com":
                is_com = True
            elif file_size >= 7 and raw_data[0] == 0xFE:
                # BLOAD ヘッダ (先頭バイト FEH) の構造検証
                b_start = raw_data[1] | (raw_data[2] << 8)
                b_end   = raw_data[3] | (raw_data[4] << 8)
                if b_end >= b_start and file_size == 7 + (b_end - b_start + 1):
                    is_bload = True

        # BLOAD 形式: 先頭7バイトのヘッダ (FEH, 開始アドレス, 終了アドレス, 実行開始アドレス) を解析
        if is_bload and file_size >= 7 and raw_data[0] == 0xFE:
            self.file_format = "BLOAD"
            b_start = raw_data[1] | (raw_data[2] << 8)
            b_end   = raw_data[3] | (raw_data[4] << 8)
            b_exec  = raw_data[5] | (raw_data[6] << 8)
            self.base_addr = b_start
            data = raw_data[7: 7 + (b_end - b_start + 1)]
            file_size = len(data)
            # 内部終端アドレスは Exclusive (末尾 + 1) で保持
            self.end_addr = self.base_addr + file_size
            self.primary_entry = b_exec

        # MSX-DOS COM 形式: 0100H 配置、エントリポイント 0100H 固定
        elif is_com:
            self.file_format = "COM"
            self.base_addr = 0x0100
            self.end_addr = 0x0100 + file_size
            self.primary_entry = 0x0100

        # 一般カートリッジ ROM 形式
        else:
            self.file_format = "ROM"
            self.end_addr = self.base_addr + file_size

        # 表示用のアドレス範囲 (開始アドレス - 最終包含アドレス)
        inclusive_end = self.end_addr - 1
        range_str = f"{format_asm_hex(self.base_addr)} - {format_asm_hex(inclusive_end)}"

        self.logger.log("=" * 70)
        self.logger.log(" MSX Z80 Intelligent Disassembler (msx_disasm)")
        self.logger.log("=" * 70)
        self.logger.log(f"[*] 入力ファイル    : {self.input_file} ({file_size} bytes)")
        self.logger.log(f"[*] フォーマット    : {self.file_format}")
        self.logger.log(f"[*] アドレス範囲    : {range_str}")
        self.logger.log(f"[*] 出力ファイル    : {self.output_file}")

        # メモリイメージとシンボルレジストリの生成
        mem = BinaryImage(data, self.base_addr, self.logger)
        registry = AddressRegistry(mem, self.logger)
        analyser = Z80FlowAnalyser(mem, registry, self.logger, max_merge_limit=self.merge_limit)
        # COMフォーマット時のフラグをデコーダへ伝搬
        analyser.decoder.is_com_format = (self.file_format == "COM")

        header_entries = []
        is_rom_header = False

        # MSX カートリッジ ROM の "AB" ヘッダ自動検出
        if self.file_format == "ROM":
            actual_header_addr = self.header_addr if self.header_addr is not None else self.base_addr
            hdr_offset = actual_header_addr - self.base_addr
            self.logger.log(f"[*] ROMヘッダ検査   : {format_asm_hex(actual_header_addr)} (オフセット: {format_asm_hex(hdr_offset)})")
            if 0 <= hdr_offset <= file_size - 16 and data[hdr_offset:hdr_offset+2] == b"AB":
                is_rom_header = True
                self.header_addr = actual_header_addr
                init_p = data[hdr_offset + 2] | (data[hdr_offset + 3] << 8)
                stmt_p = data[hdr_offset + 4] | (data[hdr_offset + 5] << 8)
                dev_p  = data[hdr_offset + 6] | (data[hdr_offset + 7] << 8)
                text_p = data[hdr_offset + 8] | (data[hdr_offset + 9] << 8)

                self.logger.log("[+] MSX ROMヘッダ ('AB') を検出:")
                if init_p:
                    self.logger.log(f"    - INIT ルーチン   : {format_asm_hex(init_p)}")
                    header_entries.append((init_p, "INIT"))
                    self.primary_entry = init_p
                if stmt_p:
                    self.logger.log(f"    - STATEMENT コール: {format_asm_hex(stmt_p)}")
                    header_entries.append((stmt_p, "STATEMENT"))
                if dev_p:
                    self.logger.log(f"    - DEVICE コール   : {format_asm_hex(dev_p)}")
                    header_entries.append((dev_p, "DEVICE"))
                if text_p:
                    self.logger.log(f"    - BASIC TEXT      : {format_asm_hex(text_p)}")

        # 初期エントリポイントの決定
        initial_entries = []
        if is_rom_header:
            for addr, lbl in header_entries:
                registry.labels[addr] = lbl
                initial_entries.append(addr)
        else:
            entry = self.primary_entry if self.primary_entry else self.base_addr
            initial_entries.append(entry)
            registry.labels[entry] = "START"

        # コマンドラインから追加指定されたエントリポイントの登録
        for extra in self.extra_entries:
            if mem.is_valid_address(extra):
                initial_entries.append(extra)
                registry.register_address(extra, is_code=True)

        # 手動指定されたジャンプテーブルの展開と分岐先収集
        for t_base, t_count in self.extra_tables:
            if mem.is_valid_address(t_base):
                registry.register_address(t_base)
                cur_ptr = t_base
                manual_targets = []
                for _ in range(t_count):
                    if not mem.is_valid_address(cur_ptr):
                        break
                    tgt = mem.get_word(cur_ptr)
                    if mem.is_valid_address(tgt) and tgt not in [0x0000, 0xFFFF]:
                        registry.register_address(tgt, is_code=True)
                        initial_entries.append(tgt)
                        manual_targets.append(tgt)
                    cur_ptr += 2
                if manual_targets:
                    tbl_end = cur_ptr - 1
                    min_tgt = min(manual_targets)
                    max_tgt = max(manual_targets)
                    self.logger.log(
                        f"[+] 手動指定ジャンプテーブルを展開: {format_asm_hex(t_base)} - {format_asm_hex(tbl_end)} "
                        f"({len(manual_targets)}/{t_count} エントリ回収)"
                    )
                    self.logger.log(
                        f"    - 分岐先範囲: {format_asm_hex(min_tgt)} - {format_asm_hex(max_tgt)}"
                    )

        # 実行フロー追跡の実行
        analyser.analyze_flow(initial_entries)

        # 未参照コードブロック (CODEギャップ) の走査回収
        if self.enable_gap_scan:
            self.logger.log("[*] 未到達コードブロックのスキャンを実行...")
            analyser.run_gap_sweep()

        # 命令先頭マップの構築 (命令内オフセット参照・SMCの解決用)
        registry.populate_instruction_map()

        # WORKに隣接する未参照DATAのマージ処理
        analyser.merge_unreferenced_work_data()

        # 解析結果統計レポートの出力
        self._print_report(mem)

        # アセンブリソースファイルの生成
        generator = DisassemblyOutputGenerator(
            mem, registry, self.logger,
            self.input_file, self.file_format, self.base_addr, self.end_addr,
            self.header_addr, self.primary_entry, self.output_file
        )
        generator.generate()
        self.logger.log(f"[+] 完了しました: {self.output_file}")

    def _print_report(self, mem: BinaryImage):
        """解析後の各属性 (CODE / DATA / WORK / MERGE) のバイト数総計を出力する。"""
        code_bytes = sum(1 for a in range(mem.base_addr, mem.end_addr) if mem.has_attribute(a, "CODE"))
        work_bytes = sum(1 for a in range(mem.base_addr, mem.end_addr) if mem.has_attribute(a, "WORK"))
        merge_bytes = sum(1 for a in range(mem.base_addr, mem.end_addr) if mem.has_attribute(a, "MERGE"))
        data_bytes = sum(
            1 for a in range(mem.base_addr, mem.end_addr)
            if mem.has_attribute(a, "DATA") and not mem.has_attribute(a, "CODE")
            and not mem.has_attribute(a, "WORK") and not mem.has_attribute(a, "MERGE")
        )

        self.logger.log("=" * 70)
        self.logger.log(" 解析レポート")
        self.logger.log("=" * 70)
        self.logger.log(f"    - 命令コード (CODE) サイズ総計 : {code_bytes:6} bytes ({format_asm_hex(code_bytes)})")
        self.logger.log(f"    - 静的データ (DATA) サイズ総計 : {data_bytes:6} bytes ({format_asm_hex(data_bytes)})")
        self.logger.log(f"    - ワーク領域 (WORK) サイズ総計 : {work_bytes:6} bytes ({format_asm_hex(work_bytes)})")
        if self.merge_limit > 0:
            self.logger.log(f"    - DATA統合 (MERGE) サイズ総計  : {merge_bytes:6} bytes ({format_asm_hex(merge_bytes)})")
        self.logger.log("=" * 70)


# =====================================================================
# 引数解析
# =====================================================================
def parse_hex_val(val_str):
    """コマンドラインで指定された 16 進数文字列 ('4000', '4000H', '0x4000') を整数に変換する。

    引数:
        val_str (str): 変換対象の文字列

    戻り値:
        int or None: 変換された整数値。無効な形式の場合は None
    """
    if not val_str:
        return None
    val_str = val_str.strip().rstrip("hH")
    try:
        return int(val_str, 16)
    except ValueError:
        return None


def parse_arguments():
    """コマンドライン引数を解析し、実行パラメータのタプルを返す。"""
    parser = argparse.ArgumentParser(
        description="MSX Z80 Intelligent Disassembler (msx_disasm)",
        add_help=False
    )
    parser.add_argument("file_pos", nargs="?", default=None, help="入力ファイルパス")
    parser.add_argument("-i", "--input", dest="file_opt", help="入力ファイルパス")
    parser.add_argument("-o", "--output", default=None, help="出力ファイルパス")
    parser.add_argument("-a", "--address", default="4000", help="配置開始アドレス (16進数、デフォルト: 4000)")
    parser.add_argument("-h", "--header", default=None, help="ROMヘッダアドレス (16進数)")
    parser.add_argument("-e", "--entry", action="append", default=[], help="追加エントリポイント (16進数、複数指定可)")
    parser.add_argument("-t", "--table", action="append", default=[], help="ジャンプテーブル手動指定 (書式: ADDR:COUNT 例: -t 7859H:9)")
    parser.add_argument("--gap-scan", action="store_true", help="CODEブロック間の未参照領域を追加走査する")
    parser.add_argument("--merge-limit", type=int, default=2, help="WORK末尾の無参照DATAマージ上限バイト数 (デフォルト: 2)")
    parser.add_argument("-c", "--com", action="store_true", help="COM形式指定 (0100H配置)")
    parser.add_argument("-b", "--bload", action="store_true", help="BLOAD形式指定")
    parser.add_argument("--help", action="help", help="ヘルプを表示")

    args = parser.parse_args()

    input_path = args.file_opt or args.file_pos
    if not input_path:
        parser.print_help()
        sys.exit(1)

    output_path = args.output or (os.path.splitext(input_path)[0] + ".asm")
    base_addr = parse_hex_val(args.address)
    header_addr = parse_hex_val(args.header) if args.header else None
    extra_entries = [parse_hex_val(e) for e in args.entry if parse_hex_val(e) is not None]

    extra_tables = []
    for t_str in args.table:
        if ":" in t_str:
            a_part, c_part = t_str.split(":", 1)
            t_addr = parse_hex_val(a_part)
            try:
                t_count = int(c_part, 16) if c_part.lower().endswith("h") else int(c_part, 10)
                if t_addr is not None and t_count > 0:
                    extra_tables.append((t_addr, t_count))
            except ValueError:
                pass

    format_override = None
    if args.com:
        format_override = "COM"
    elif args.bload:
        format_override = "BLOAD"

    return (input_path, output_path, base_addr, header_addr,
            format_override, extra_entries, extra_tables, args.gap_scan, args.merge_limit)


# =====================================================================
# メインエントリポイント
# =====================================================================
if __name__ == "__main__":
    (in_f, out_f, base_a, hdr_a,
     fmt_o, extra_e, extra_t, gap_scan_opt, merge_lim) = parse_arguments()

    disasm = MsxDisassembler(
        in_f, out_f,
        base_addr=base_a,
        header_addr=hdr_a,
        format_override=fmt_o,
        extra_entries=extra_e,
        extra_tables=extra_t,
        enable_gap_scan=gap_scan_opt,
        merge_limit=merge_lim
    )
    disasm.run()

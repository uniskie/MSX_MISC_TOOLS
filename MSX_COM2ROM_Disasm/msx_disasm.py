#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=====================================================================
MSX Z80 Intelligent Disassembler (msx_disasm)
=====================================================================
- ROM/COM/RAM/BLOAD バイナリのフロー解析型 逆アセンブラ
- メガROMマッパー（Konami, Konami-SCC, ASCII8, ASCII16, NORMAL）対応
- ROMヘッダ自動認識 & エントリポイント自動トレース
- MSX BASIC BLOAD (BSAVE) / MSX-DOS COM 形式対応
- Z80未定義命令 (Undocumented opcodes) のデコードと注記
- WORKエリアのアクセスサイズ（1 byte / 2 bytes等）を自動判定してEQUに注記
- msx_symbols.py 連動による BIOS / WORK エリア シンボル解決
=====================================================================
"""

import os
import sys
import argparse

# -------------------------------------------------------------------
# msx_symbols.py の読み込み (同階層にあれば使用)
# -------------------------------------------------------------------
try:
    import msx_symbols
    HAS_MSX_SYMBOLS = True
except ImportError:
    HAS_MSX_SYMBOLS = False


def format_asm_hex(val, width=4):
    """16進数をアセンブラ表記 (0FFFFH 等) に変換"""
    hex_str = f"{val:0{width}X}"
    if hex_str[0] in "ABCDEF":
        return "0" + hex_str + "H"
    return hex_str + "H"


def signed_byte(b):
    return b - 256 if b >= 128 else b


def get_symbol_name(addr):
    """msx_symbols.py から BIOS、システムワーク、フックの名前を検索 (BIOS優先)"""
    if not HAS_MSX_SYMBOLS:
        return None
    try:
        # ROM向けなので BIOS -> WORK -> HOOK の順で優先解決
        if hasattr(msx_symbols, "msx_symbols_bios"):
            b_labels = msx_symbols.msx_symbols_bios.from_address(addr)
            if b_labels:
                return b_labels[0].replace(".", "_")
        if hasattr(msx_symbols, "msx_symbols_work"):
            w_labels = msx_symbols.msx_symbols_work.from_address(addr)
            if w_labels:
                return w_labels[0].replace(".", "_")
        if hasattr(msx_symbols, "msx_symbols_hook"):
            h_labels = msx_symbols.msx_symbols_hook.from_address(addr)
            if h_labels:
                return h_labels[0].replace(".", "_")
        if hasattr(msx_symbols, "search_labels"):
            labels = msx_symbols.search_labels(addr)
            if labels:
                return labels[0].replace(".", "_")
    except Exception:
        pass
    return None


# =====================================================================
# マッパー設定
# =====================================================================
MAPPER_CONFIGS = {
    "NORMAL": {
        "name": "Standard ROM (No Mapper)",
        "bank_size": 0,
        "is_rom": True,
        "default_base": 0x4000
    },
    "KONAMI": {
        "name": "Konami 8KB (No SCC)",
        "bank_size": 0x2000,
        "page_addrs": [0x4000, 0x6000, 0x8000, 0xA000],
        "is_rom": True,
        "default_base": 0x4000
    },
    "KONAMI-SCC": {
        "name": "Konami 8KB with SCC",
        "bank_size": 0x2000,
        "page_addrs": [0x4000, 0x6000, 0x8000, 0xA000],
        "is_rom": True,
        "default_base": 0x4000
    },
    "ASCII8": {
        "name": "ASCII 8KB",
        "bank_size": 0x2000,
        "page_addrs": [0x4000, 0x6000, 0x8000, 0xA000],
        "is_rom": True,
        "default_base": 0x4000
    },
    "ASCII16": {
        "name": "ASCII 16KB",
        "bank_size": 0x4000,
        "page_addrs": [0x4000, 0x8000],
        "is_rom": True,
        "default_base": 0x4000
    },
    "NONE": {
        "name": "Flat Binary (COM / RAM)",
        "bank_size": 0,
        "is_rom": False,
        "default_base": 0x0100
    }
}

REG8 = ["b", "c", "d", "e", "h", "l", "(hl)", "a"]
REG8_IX = ["b", "c", "d", "e", "ixh", "ixl", "(ix+d)", "a"]
REG8_IY = ["b", "c", "d", "e", "iyh", "iyl", "(iy+d)", "a"]
ALU = ["add a,", "adc a,", "sub", "sbc a,", "and", "xor", "or", "cp"]
ROT = ["rlc", "rrc", "rl", "rr", "sla", "sra", "sll", "srl"]


def get_standard_len(opcode):
    if opcode in [0x01, 0x11, 0x21, 0x31, 0x32, 0x22, 0x3A, 0x2A, 0xC3, 0xCD]:
        return 3
    if opcode in [0xC2, 0xCA, 0xD2, 0xDA, 0xE2, 0xEA, 0xF2, 0xFA]:
        return 3
    if opcode in [0xC4, 0xCC, 0xD4, 0xDC, 0xE4, 0xEC, 0xF4, 0xFC]:
        return 3
    if opcode in [0x18, 0x20, 0x28, 0x30, 0x38, 0x10]:
        return 2
    if opcode in [0x06, 0x0E, 0x16, 0x1E, 0x26, 0x2E, 0x3E, 0xC6, 0xCE, 0xD6, 0xDE, 0xE6, 0xEE, 0xF6, 0xFE, 0xD3, 0xDB, 0x36]:
        return 2
    return 1


# =====================================================================
# Z80 命令デコーダ & 逆アセンブラ
# =====================================================================
class Z80InstructionDecoder:
    def __init__(self, get_byte_fn, get_word_fn):
        self.get_b = get_byte_fn
        self.get_w = get_word_fn

    def decode(self, pc, get_label_fn=None):
        """
        命令をデコードする。
        戻り値: (length, branch_targets, mnemonic, is_terminal, access_addr, access_size, imm16_val)
          - length: 命令長
          - branch_targets: 分岐先アドレスのリスト（JP/CALL/JR/RSTなど）
          - mnemonic: アセンブリ文字列
          - is_terminal: 無条件ジャンプ/リターン等で、直後の命令へフォールスルーしない場合 True
          - access_addr: メモリアドレス参照先
          - access_size: メモリアクセスサイズ (1 or 2 bytes)
          - imm16_val: 16ビット即値（ポインタ候補）
        """
        b0 = self.get_b(pc)

        def lbl(addr):
            if get_label_fn:
                return get_label_fn(addr)
            return format_asm_hex(addr)

        # ---------------- プレフィックス ED ----------------
        if b0 == 0xED:
            b1 = self.get_b(pc + 1)
            # 16-bit LD (nn), rp / LD rp, (nn)
            if b1 in [0x43, 0x53, 0x73, 0x4B, 0x5B, 0x7B]:
                target = self.get_w(pc + 2)
                reg = {0x43: "bc", 0x53: "de", 0x73: "sp", 0x4B: "bc", 0x5B: "de", 0x7B: "sp"}[b1]
                if b1 in [0x43, 0x53, 0x73]:
                    return 4, [], f"ld ({lbl(target)}), {reg}", False, target, 2, None
                else:
                    return 4, [], f"ld {reg}, ({lbl(target)})", False, target, 2, None

            # 未定義: ED 63: ld (nn), hl / ED 6B: ld hl, (nn)
            if b1 == 0x63:
                target = self.get_w(pc + 2)
                return 4, [], f"ld ({lbl(target)}), hl ; (undocumented)", False, target, 2, None
            if b1 == 0x6B:
                target = self.get_w(pc + 2)
                return 4, [], f"ld hl, ({lbl(target)}) ; (undocumented)", False, target, 2, None

            # IN / OUT (C)
            if 0x40 <= b1 <= 0x7F:
                reg_code = (b1 >> 3) & 7
                reg_name = REG8[reg_code]
                if (b1 & 7) == 0:
                    if reg_code == 6:
                        # ED 70: IN (C) / IN F, (C) 未定義
                        return 2, [], "in (c) ; (undocumented)", False, None, 0, None
                    return 2, [], f"in {reg_name}, (c)", False, None, 0, None
                elif (b1 & 7) == 1:
                    if reg_code == 6:
                        # ED 71: OUT (C), 0 未定義
                        return 2, [], "out (c), 0 ; (undocumented)", False, None, 0, None
                    return 2, [], f"out (c), {reg_name}", False, None, 0, None

            # 特殊命令 (公式)
            ed_ops = {
                0x44: "neg", 0x45: "retn", 0x4D: "reti", 0x46: "im 0", 0x56: "im 1", 0x5E: "im 2",
                0x42: "sbc hl, bc", 0x52: "sbc hl, de", 0x62: "sbc hl, hl", 0x72: "sbc hl, sp",
                0x4A: "adc hl, bc", 0x5A: "adc hl, de", 0x6A: "adc hl, hl", 0x7A: "adc hl, sp",
                0x47: "ld i, a", 0x57: "ld a, i", 0x4F: "ld r, a", 0x5F: "ld a, r",
                0x67: "rrd", 0x6F: "rld",
                0xA0: "ldi", 0xA1: "cpi", 0xA2: "ini", 0xA3: "outi",
                0xB0: "ldir", 0xB1: "cpir", 0xB2: "inir", 0xB3: "otir",
                0xA8: "ldd", 0xA9: "cpd", 0xAA: "ind", 0xAB: "outd",
                0xB8: "lddr", 0xB9: "cpdr", 0xBA: "indr", 0xBB: "otdr"
            }
            if b1 in ed_ops:
                is_ret = b1 in [0x45, 0x4D]
                return 2, [], ed_ops[b1], is_ret, None, 0, None

            # 未定義: neg, retn, reti, im
            if b1 in [0x4C, 0x54, 0x5C, 0x64, 0x6C, 0x74, 0x7C]:
                return 2, [], "neg ; (undocumented)", False, None, 0, None
            if b1 in [0x55, 0x65, 0x75]:
                return 2, [], "retn ; (undocumented)", True, None, 0, None
            if b1 in [0x5D, 0x6D, 0x7D]:
                return 2, [], "reti ; (undocumented)", True, None, 0, None
            if b1 in [0x4E, 0x66, 0x6E]:
                return 2, [], "im 0 ; (undocumented)", False, None, 0, None
            if b1 == 0x76:
                return 2, [], "im 1 ; (undocumented)", False, None, 0, None
            if b1 == 0x7E:
                return 2, [], "im 2 ; (undocumented)", False, None, 0, None

            return 2, [], f"db 0EDH, {format_asm_hex(b1, 2)}", False, None, 0, None

        # ---------------- プレフィックス CB ----------------
        if b0 == 0xCB:
            b1 = self.get_b(pc + 1)
            reg_idx = b1 & 7
            bit_idx = (b1 >> 3) & 7
            reg_str = REG8[reg_idx]

            if 0x00 <= b1 <= 0x3F:
                if bit_idx == 6:  # SLL は未定義命令
                    return 2, [], f"sll {reg_str} ; (undocumented)", False, None, 0, None
                return 2, [], f"{ROT[bit_idx]} {reg_str}", False, None, 0, None
            elif 0x40 <= b1 <= 0x7F:
                return 2, [], f"bit {bit_idx}, {reg_str}", False, None, 0, None
            elif 0x80 <= b1 <= 0xBF:
                return 2, [], f"res {bit_idx}, {reg_str}", False, None, 0, None
            elif 0xC0 <= b1 <= 0xFF:
                return 2, [], f"set {bit_idx}, {reg_str}", False, None, 0, None

        # ---------------- プレフィックス DD / FD ----------------
        if b0 in [0xDD, 0xFD]:
            pfx = "ix" if b0 == 0xDD else "iy"
            reg8_idx = REG8_IX if b0 == 0xDD else REG8_IY
            b1 = self.get_b(pc + 1)
            if b1 == 0x21:
                target = self.get_w(pc + 2)
                return 4, [], f"ld {pfx}, {lbl(target)}", False, None, 0, target
            if b1 == 0x22:
                target = self.get_w(pc + 2)
                return 4, [], f"ld ({lbl(target)}), {pfx}", False, target, 2, None
            if b1 == 0x2A:
                target = self.get_w(pc + 2)
                return 4, [], f"ld {pfx}, ({lbl(target)})", False, target, 2, None
            if b1 in [0x09, 0x19, 0x29, 0x39]:
                rp = {0x09: "bc", 0x19: "de", 0x29: pfx, 0x39: "sp"}[b1]
                return 2, [], f"add {pfx}, {rp}", False, None, 0, None
            if b1 == 0xE9:
                return 2, [], f"jp ({pfx})", True, None, 0, None
            if b1 in [0xE1, 0xE5]:
                op = "pop" if b1 == 0xE1 else "push"
                return 2, [], f"{op} {pfx}", False, None, 0, None

            # DDCB / FDCB
            if b1 == 0xCB:
                d = signed_byte(self.get_b(pc + 2))
                b3 = self.get_b(pc + 3)
                d_str = f"+{d}" if d >= 0 else f"{d}"
                bit = (b3 >> 3) & 7
                reg_code = b3 & 7
                operand = f"({pfx}{d_str})"

                if 0x00 <= b3 <= 0x3F:
                    rot = ROT[bit]
                    if reg_code == 6:
                        if bit == 6:  # sll (ix+d)
                            return 4, [], f"sll {operand} ; (undocumented)", False, None, 0, None
                        return 4, [], f"{rot} {operand}", False, None, 0, None
                    else:
                        # rot (ix+d), reg (未定義複合命令)
                        return 4, [], f"{rot} {operand}, {REG8[reg_code]} ; (undocumented)", False, None, 0, None

                elif 0x40 <= b3 <= 0x7F:
                    return 4, [], f"bit {bit}, {operand}", False, None, 0, None

                elif 0x80 <= b3 <= 0xBF:
                    if reg_code == 6:
                        return 4, [], f"res {bit}, {operand}", False, None, 0, None
                    else:
                        # res bit, (ix+d), reg (未定義複合命令)
                        return 4, [], f"res {bit}, {operand}, {REG8[reg_code]} ; (undocumented)", False, None, 0, None

                elif 0xC0 <= b3 <= 0xFF:
                    if reg_code == 6:
                        return 4, [], f"set {bit}, {operand}", False, None, 0, None
                    else:
                        # set bit, (ix+d), reg (未定義複合命令)
                        return 4, [], f"set {bit}, {operand}, {REG8[reg_code]} ; (undocumented)", False, None, 0, None

            # (IX+d) / (IY+d) 操作
            is_ind = ((b1 >> 3) & 7) == 6 or (b1 & 7) == 6
            if is_ind or b1 in [0x34, 0x35, 0x36]:
                d = signed_byte(self.get_b(pc + 2))
                d_str = f"+{d}" if d >= 0 else f"{d}"
                operand = f"({pfx}{d_str})"
                if b1 == 0x34: return 3, [], f"inc {operand}", False, None, 0, None
                if b1 == 0x35: return 3, [], f"dec {operand}", False, None, 0, None
                if b1 == 0x36:
                    val = self.get_b(pc + 3)
                    return 4, [], f"ld {operand}, {format_asm_hex(val, 2)}", False, None, 0, None
                if 0x40 <= b1 <= 0x7F and b1 != 0x76:
                    dest = operand if ((b1 >> 3) & 7) == 6 else REG8[(b1 >> 3) & 7]
                    src = operand if (b1 & 7) == 6 else REG8[b1 & 7]
                    return 3, [], f"ld {dest}, {src}", False, None, 0, None
                if 0x80 <= b1 <= 0xBF:
                    return 3, [], f"{ALU[(b1 >> 3) & 7]} {operand}", False, None, 0, None

            # 未定義: INC / DEC IXH, IXL, IYH, IYL
            if b1 in [0x24, 0x2C]:
                r = f"{pfx}h" if b1 == 0x24 else f"{pfx}l"
                return 2, [], f"inc {r} ; (undocumented)", False, None, 0, None
            if b1 in [0x25, 0x2D]:
                r = f"{pfx}h" if b1 == 0x25 else f"{pfx}l"
                return 2, [], f"dec {r} ; (undocumented)", False, None, 0, None

            # 未定義: LD IXH, n / LD IXL, n
            if b1 in [0x26, 0x2E]:
                r = f"{pfx}h" if b1 == 0x26 else f"{pfx}l"
                n = self.get_b(pc + 2)
                return 3, [], f"ld {r}, {format_asm_hex(n, 2)} ; (undocumented)", False, None, 0, None

            # 未定義: LD r, r' (IXH / IXL / IYH / IYL 関連)
            if 0x40 <= b1 <= 0x7F and b1 != 0x76:
                d_idx = (b1 >> 3) & 7
                s_idx = b1 & 7
                dest = reg8_idx[d_idx]
                src = reg8_idx[s_idx]
                if d_idx in [4, 5] or s_idx in [4, 5]:
                    return 2, [], f"ld {dest}, {src} ; (undocumented)", False, None, 0, None
                else:
                    return 2, [], f"ld {dest}, {src} ; (undocumented: prefix ignored)", False, None, 0, None

            # 未定義: ALU A, IXH / IXL / IYH / IYL
            if 0x80 <= b1 <= 0xBF:
                s_idx = b1 & 7
                src = reg8_idx[s_idx]
                if s_idx in [4, 5]:
                    return 2, [], f"{ALU[(b1 >> 3) & 7]} {src} ; (undocumented)", False, None, 0, None
                else:
                    return 2, [], f"{ALU[(b1 >> 3) & 7]} {src} ; (undocumented: prefix ignored)", False, None, 0, None

            return 2, [], f"db {format_asm_hex(b0, 2)}, {format_asm_hex(b1, 2)}", False, None, 0, None

        # ---------------- 標準命令 ----------------
        if b0 == 0xF7:  # RST 30H (MSX CALSLT)
            slot = self.get_b(pc + 1)
            target = self.get_w(pc + 2)
            return 4, [target], f"rst 30H\n    db  {format_asm_hex(slot, 2)}\n    dw  {lbl(target)}", False, None, 0, None

        if b0 == 0xC9:  # RET (無条件リターン)
            return 1, [], "ret", True, None, 0, None
        if b0 == 0xE9:  # JP (HL)
            return 1, [], "jp (hl)", True, None, 0, None
        if b0 == 0x76:  # HALT
            return 1, [], "halt", False, None, 0, None

        if b0 == 0xC3:  # JP nn
            target = self.get_w(pc + 1)
            return 3, [target], f"jp {lbl(target)}", True, None, 0, None

        if b0 == 0xCD:  # CALL nn
            target = self.get_w(pc + 1)
            return 3, [target], f"call {lbl(target)}", False, None, 0, None

        if b0 in [0xC2, 0xCA, 0xD2, 0xDA, 0xE2, 0xEA, 0xF2, 0xFA]:  # JP cc, nn
            target = self.get_w(pc + 1)
            cond = {0xC2: "nz", 0xCA: "z", 0xD2: "nc", 0xDA: "c", 0xE2: "po", 0xEA: "pe", 0xF2: "p", 0xFA: "m"}[b0]
            return 3, [target], f"jp {cond}, {lbl(target)}", False, None, 0, None

        if b0 in [0xC4, 0xCC, 0xD4, 0xDC, 0xE4, 0xEC, 0xF4, 0xFC]:  # CALL cc, nn
            target = self.get_w(pc + 1)
            cond = {0xC4: "nz", 0xCC: "z", 0xD4: "nc", 0xDC: "c", 0xE4: "po", 0xEC: "pe", 0xF4: "p", 0xFC: "m"}[b0]
            return 3, [target], f"call {cond}, {lbl(target)}", False, None, 0, None

        if b0 == 0x18:  # JR e (無条件)
            offset = self.get_b(pc + 1)
            if offset & 0x80: offset -= 256
            target = (pc + 2 + offset) & 0xFFFF
            return 2, [target], f"jr {lbl(target)}", True, None, 0, None

        if b0 in [0x20, 0x28, 0x30, 0x38]:  # JR cc, e (条件付き)
            offset = self.get_b(pc + 1)
            if offset & 0x80: offset -= 256
            target = (pc + 2 + offset) & 0xFFFF
            names = {0x20: "jr nz,", 0x28: "jr z,", 0x30: "jr nc,", 0x38: "jr c,"}
            return 2, [target], f"{names[b0]} {lbl(target)}", False, None, 0, None

        if b0 == 0x10:  # DJNZ e
            offset = self.get_b(pc + 1)
            if offset & 0x80: offset -= 256
            target = (pc + 2 + offset) & 0xFFFF
            return 2, [target], f"djnz {lbl(target)}", False, None, 0, None

        if b0 in [0x32, 0x3A]:
            target = self.get_w(pc + 1)
            if b0 == 0x32: return 3, [], f"ld ({lbl(target)}), a", False, target, 1, None
            if b0 == 0x3A: return 3, [], f"ld a, ({lbl(target)})", False, target, 1, None

        if b0 in [0x22, 0x2A]:
            target = self.get_w(pc + 1)
            if b0 == 0x22: return 3, [], f"ld ({lbl(target)}), hl", False, target, 2, None
            if b0 == 0x2A: return 3, [], f"ld hl, ({lbl(target)})", False, target, 2, None

        if b0 in [0x01, 0x11, 0x21, 0x31]:
            target = self.get_w(pc + 1)
            r = {0x01: "bc", 0x11: "de", 0x21: "hl", 0x31: "sp"}[b0]
            return 3, [], f"ld {r}, {lbl(target)}", False, None, 0, target

        # 条件付きリターン (RET cc) はフォールスルーするので is_terminal = False
        if b0 in [0xC0, 0xC8, 0xD0, 0xD8, 0xE0, 0xE8, 0xF0, 0xF8]:
            cond = {0xC0: "nz", 0xC8: "z", 0xD0: "nc", 0xD8: "c", 0xE0: "po", 0xE8: "pe", 0xF0: "p", 0xF8: "m"}[b0]
            return 1, [], f"ret {cond}", False, None, 0, None

        if b0 in [0xC5, 0xD5, 0xE5, 0xF5]:
            r = {0xC5: "bc", 0xD5: "de", 0xE5: "hl", 0xF5: "af"}[b0]
            return 1, [], f"push {r}", False, None, 0, None
        if b0 in [0xC1, 0xD1, 0xE1, 0xF1]:
            r = {0xC1: "bc", 0xD1: "de", 0xE1: "hl", 0xF1: "af"}[b0]
            return 1, [], f"pop {r}", False, None, 0, None

        if b0 in [0x06, 0x0E, 0x16, 0x1E, 0x26, 0x2E, 0x3E]:
            n = self.get_b(pc + 1)
            r = REG8[(b0 >> 3) & 7]
            return 2, [], f"ld {r}, {format_asm_hex(n, 2)}", False, None, 0, None

        if b0 in [0xC6, 0xCE, 0xD6, 0xDE, 0xE6, 0xEE, 0xF6, 0xFE]:
            n = self.get_b(pc + 1)
            op = ALU[(b0 >> 3) & 7]
            return 2, [], f"{op} {format_asm_hex(n, 2)}", False, None, 0, None

        if b0 == 0xD3:
            n = self.get_b(pc + 1)
            return 2, [], f"out ({format_asm_hex(n, 2)}), a", False, None, 0, None

        if b0 == 0xDB:
            n = self.get_b(pc + 1)
            return 2, [], f"in a, ({format_asm_hex(n, 2)})", False, None, 0, None

        if b0 == 0x36:
            n = self.get_b(pc + 1)
            return 2, [], f"ld (hl), {format_asm_hex(n, 2)}", False, None, 0, None

        if b0 in [0xC7, 0xCF, 0xD7, 0xDF, 0xE7, 0xEF, 0xFF]:
            rst_target = b0 & 0x38
            return 1, [rst_target], f"rst {format_asm_hex(rst_target, 2)}", False, None, 0, None

        if 0x40 <= b0 <= 0x7F:
            return 1, [], f"ld {REG8[(b0 >> 3) & 7]}, {REG8[b0 & 7]}", False, None, 0, None

        if 0x80 <= b0 <= 0xBF:
            return 1, [], f"{ALU[(b0 >> 3) & 7]} {REG8[b0 & 7]}", False, None, 0, None

        one_byte_ops = {
            0x00: "nop", 0x02: "ld (bc), a", 0x0A: "ld a, (bc)", 0x12: "ld (de), a", 0x1A: "ld a, (de)",
            0x03: "inc bc", 0x13: "inc de", 0x23: "inc hl", 0x33: "inc sp",
            0x0B: "dec bc", 0x1B: "dec de", 0x2B: "dec hl", 0x3B: "dec sp",
            0x04: "inc b", 0x0C: "inc c", 0x14: "inc d", 0x1C: "inc e", 0x24: "inc h", 0x2C: "inc l", 0x3C: "inc a",
            0x05: "dec b", 0x0D: "dec c", 0x15: "dec d", 0x1D: "dec e", 0x25: "dec h", 0x2D: "dec l", 0x3D: "dec a",
            0x07: "rlca", 0x0F: "rrca", 0x17: "rla", 0x1F: "rra", 0x27: "daa", 0x2F: "cpl",
            0x37: "scf", 0x3F: "ccf", 0xD9: "exx", 0xE3: "ex (sp), hl", 0xEB: "ex de, hl",
            0xF3: "di", 0xFB: "ei", 0xF9: "ld sp, hl", 0x08: "ex af, af'",
            0x09: "add hl, bc", 0x19: "add hl, de", 0x29: "add hl, hl", 0x39: "add hl, sp"
        }
        if b0 in one_byte_ops:
            return 1, [], one_byte_ops[b0], False, None, 0, None

        return 1, [], f"db {format_asm_hex(b0, 2)}", False, None, 0, None


# =====================================================================
# バンク管理クラス
# =====================================================================
class ROMBank:
    def __init__(self, bank_id, raw_bytes, base_addr, global_labels, var_sizes, logger):
        self.bank_id = bank_id
        self.raw_bytes = raw_bytes
        self.base_addr = base_addr
        self.end_addr = base_addr + len(raw_bytes)
        self.attr = ['DATA'] * len(raw_bytes)
        self.global_labels = global_labels
        self.var_sizes = var_sizes
        self.logger = logger
        self.decoder = Z80InstructionDecoder(self.get_byte, self.get_word)
        self.pointer_load_pcs = set()

    def is_in_bank(self, addr):
        return self.base_addr <= addr < self.end_addr

    def get_byte(self, pc):
        idx = pc - self.base_addr
        if 0 <= idx < len(self.raw_bytes):
            return self.raw_bytes[idx]
        return 0

    def get_word(self, pc):
        return self.get_byte(pc) | (self.get_byte(pc + 1) << 8)

    def mark_code(self, pc, length):
        for i in range(length):
            idx = (pc + i) - self.base_addr
            if 0 <= idx < len(self.attr):
                self.attr[idx] = 'CODE'

    def trace_flow(self, entry_points):
        visited = set()
        stack = list(entry_points)
        reg_tracker = {'HL': None, 'DE': None, 'BC': None, 'IX': None, 'IY': None}

        while stack:
            pc = stack.pop()
            if pc in visited or not self.is_in_bank(pc):
                continue
            visited.add(pc)

            length, branch_targets, _, is_terminal, access_addr, access_sz, imm16 = self.decoder.decode(pc)
            self.mark_code(pc, length)
            opcode = self.get_byte(pc)

            # ポインタ即値ロード (LD rp, nn) の追跡
            if imm16 is not None:
                if opcode in [0x01, 0x11, 0x21]:
                    rname = {0x01: "BC", 0x11: "DE", 0x21: "HL"}[opcode]
                    reg_tracker[rname] = (pc, imm16)
                elif opcode in [0xDD, 0xFD]:
                    rname = "IX" if opcode == 0xDD else "IY"
                    reg_tracker[rname] = (pc, imm16)

            # 間接参照 (HL) 等によるポインタ確定
            is_ind_hl = (0x40 <= opcode <= 0x7F and (opcode & 7) == 6 and opcode != 0x76) or \
                        (0x80 <= opcode <= 0xBF and (opcode & 7) == 6)
            if is_ind_hl and reg_tracker['HL']:
                src_pc, val = reg_tracker['HL']
                self.pointer_load_pcs.add(src_pc)
                self.register_symbol(val, size=1)

            # CALSLT (0x001C) 呼び出し時の IX 追跡
            if opcode == 0xCD and branch_targets and branch_targets[0] == 0x001C and reg_tracker['IX']:
                src_pc, val = reg_tracker['IX']
                self.pointer_load_pcs.add(src_pc)
                self.register_symbol(val)

            # メモリアクセスがある場合、WORK/DATAとして登録
            if access_addr is not None:
                self.register_symbol(access_addr, size=access_sz)

            # 分岐命令（JP, CALL, JR, RST）の飛び先のみをスタックに積む
            for tgt in branch_targets:
                self.register_symbol(tgt)
                if self.is_in_bank(tgt):
                    stack.append(tgt)

            # 連続するJPテーブル (JP xxxx が並んでいる場合)
            if opcode == 0xC3:
                next_pc = pc + 3
                if self.is_in_bank(next_pc) and self.get_byte(next_pc) == 0xC3:
                    stack.append(next_pc)

            # 終端命令でなければ、次の命令へ進む
            if not is_terminal:
                stack.append(pc + length)

    def register_symbol(self, addr, size=0):
        if size > 0:
            current_sz = self.var_sizes.get(addr, 0)
            if size > current_sz:
                self.var_sizes[addr] = size

        if addr not in self.global_labels:
            sym_name = get_symbol_name(addr)
            if sym_name:
                self.global_labels[addr] = sym_name
            else:
                if self.is_in_bank(addr):
                    self.global_labels[addr] = f"LABEL_{self.bank_id:02X}_{addr:04X}H"
                elif addr >= 0xC000:
                    self.global_labels[addr] = f"WORK_{addr:04X}H"
                else:
                    self.global_labels[addr] = f"EXT_{addr:04X}H"


# =====================================================================
# メインクラス
# =====================================================================
class MsxDisassembler:
    def __init__(self, input_file, output_file, base_addr=0x4000, header_addr=None, mapper="NORMAL", format_override=None):
        self.input_file = input_file
        self.output_file = output_file
        self.log_file = os.path.splitext(output_file)[0] + ".log"
        self.base_addr = base_addr
        self.header_addr = header_addr
        self.mapper = mapper.upper()
        self.format_override = format_override

        self.global_labels = {}
        self.var_sizes = {}
        self.banks = []
        self.file_format = "ROM"
        self.end_addr = None
        self.primary_entry = None

    def log(self, msg):
        print(msg)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(msg + "\n")

    def run(self):
        with open(self.log_file, "w", encoding="utf-8") as f:
            f.write(f"MSX Disassembler Log - {self.input_file}\n\n")

        with open(self.input_file, "rb") as f:
            raw_data = bytearray(f.read())

        file_size = len(raw_data)
        data = raw_data

        # ---------------- 形式判定 (BLOAD / COM / ROM) ----------------
        is_bload = False
        is_com = False

        if self.format_override == "BLOAD":
            is_bload = True
        elif self.format_override == "COM":
            is_com = True
        elif self.mapper == "NORMAL" and self.header_addr is None:
            # 自動判定
            _, ext = os.path.splitext(self.input_file.lower())
            if ext == ".com":
                is_com = True
            elif file_size >= 7 and raw_data[0] == 0xFE:
                b_start = raw_data[1] | (raw_data[2] << 8)
                b_end   = raw_data[3] | (raw_data[4] << 8)
                if b_end >= b_start and file_size == 7 + (b_end - b_start + 1):
                    is_bload = True

        if is_bload and file_size >= 7 and raw_data[0] == 0xFE:
            self.file_format = "BLOAD"
            b_start = raw_data[1] | (raw_data[2] << 8)
            b_end   = raw_data[3] | (raw_data[4] << 8)
            b_exec  = raw_data[5] | (raw_data[6] << 8)
            self.base_addr = b_start
            self.end_addr = b_end
            self.primary_entry = b_exec
            self.mapper = "NONE"
            data = raw_data[7: 7 + (b_end - b_start + 1)]
            file_size = len(data)
        elif is_com:
            self.file_format = "COM"
            self.base_addr = 0x0100
            self.end_addr = 0x0100 + file_size - 1
            self.primary_entry = 0x0100
            self.mapper = "NONE"
        else:
            self.file_format = "ROM"
            self.end_addr = self.base_addr + file_size - 1

        cfg = MAPPER_CONFIGS.get(self.mapper, MAPPER_CONFIGS["NORMAL"])
        range_str = f"{format_asm_hex(self.base_addr)} - {format_asm_hex(self.end_addr)}"

        self.log("=" * 70)
        self.log(" MSX Z80 Intelligent Disassembler (msx_disasm)")
        self.log("=" * 70)
        self.log(f"[*] 入力ファイル    : {self.input_file} ({file_size} bytes)")
        self.log(f"[*] フォーマット    : {self.file_format}")
        self.log(f"[*] アドレス範囲    : {range_str}")
        self.log(f"[*] 出力ファイル    : {self.output_file}")
        self.log(f"[*] マッパータイプ  : {cfg['name']}")

        header_entries = []
        is_rom_header = False

        if self.file_format == "ROM" and cfg["is_rom"]:
            actual_header_addr = self.header_addr if self.header_addr is not None else self.base_addr
            self.header_addr = actual_header_addr
            hdr_offset = actual_header_addr - self.base_addr
            self.log(f"[*] ROMヘッダ指定   : {format_asm_hex(actual_header_addr)} (オフセット: {format_asm_hex(hdr_offset)})")
            if 0 <= hdr_offset <= file_size - 16 and data[hdr_offset:hdr_offset+2] == b'AB':
                is_rom_header = True
                init_p = data[hdr_offset + 2] | (data[hdr_offset + 3] << 8)
                stmt_p = data[hdr_offset + 4] | (data[hdr_offset + 5] << 8)
                dev_p  = data[hdr_offset + 6] | (data[hdr_offset + 7] << 8)
                text_p = data[hdr_offset + 8] | (data[hdr_offset + 9] << 8)

                self.log("[+] MSX ROMヘッダ ('AB') を検出:")
                if init_p:
                    self.log(f"    - INIT ルーチン   : {format_asm_hex(init_p)}")
                    header_entries.append((init_p, "INIT"))
                    self.primary_entry = init_p
                if stmt_p:
                    self.log(f"    - STATEMENT コール: {format_asm_hex(stmt_p)}")
                    header_entries.append((stmt_p, "STATEMENT"))
                if dev_p:
                    self.log(f"    - DEVICE コール   : {format_asm_hex(dev_p)}")
                    header_entries.append((dev_p, "DEVICE"))
                if text_p:
                    self.log(f"    - BASIC TEXT      : {format_asm_hex(text_p)}")
            else:
                self.log(f"[-] 警告: 指定アドレス {format_asm_hex(actual_header_addr)} に'AB'ヘッダが存在しません。")
        elif self.file_format == "BLOAD":
            self.log(f"[*] BLOADヘッダ情報 : START={format_asm_hex(self.base_addr)}, END={format_asm_hex(self.end_addr)}, EXEC={format_asm_hex(self.primary_entry)}")

        # バンク構築
        bank_size = cfg["bank_size"]
        if bank_size == 0 or file_size <= bank_size:
            b = ROMBank(0, data, self.base_addr, self.global_labels, self.var_sizes, self.log)
            self.banks.append(b)
        else:
            num_banks = file_size // bank_size
            page_addrs = cfg["page_addrs"]
            self.log(f"[*] {num_banks} 個のバンクに分割します。")
            for i in range(num_banks):
                b_data = data[i * bank_size : (i + 1) * bank_size]
                b_base = page_addrs[i % len(page_addrs)]
                b = ROMBank(i, b_data, b_base, self.global_labels, self.var_sizes, self.log)
                self.banks.append(b)

        # エントリポイント設定とトレース
        for bank in self.banks:
            entries = []
            if is_rom_header and bank.is_in_bank(self.header_addr):
                for addr, label in header_entries:
                    self.global_labels[addr] = label
                    entries.append(addr)
            elif not is_rom_header and bank.bank_id == 0:
                entry = self.primary_entry if self.primary_entry else bank.base_addr
                if bank.is_in_bank(entry):
                    entries.append(entry)
                    self.global_labels[entry] = "START"
            elif not is_rom_header:
                entries.append(bank.base_addr)

            if entries:
                bank.trace_flow(entries)

        # 出力
        self.output_assembly(is_rom_header)

    def output_assembly(self, is_rom_header):
        self.log(f"[*] アセンブリソースを生成中: {self.output_file}")
        with open(self.output_file, "w", encoding="utf-8") as out:
            range_str = f"{format_asm_hex(self.base_addr)} - {format_asm_hex(self.end_addr)}"

            out.write("; " + "=" * 70 + "\n")
            out.write(f"; MSX Z80 Intelligent Disassembler Output\n")
            out.write(f"; Source: {self.input_file}\n")
            out.write(f"; Format: {self.file_format}\n")
            out.write(f"; Range : {range_str}\n")
            if is_rom_header and self.header_addr is not None:
                out.write(f"; Header: {format_asm_hex(self.header_addr)}\n")
            if self.primary_entry is not None:
                out.write(f"; Entry : {format_asm_hex(self.primary_entry)}\n")
            out.write(f"; Mapper: {MAPPER_CONFIGS.get(self.mapper, {}).get('name', self.mapper)}\n")
            out.write("; " + "=" * 70 + "\n\n")

            # 外部シンボルの分類
            bios_symbols = []
            work_symbols = []
            user_work_symbols = []
            other_symbols = []

            for addr, name in self.global_labels.items():
                if any(b.is_in_bank(addr) for b in self.banks):
                    continue

                if addr < 0x4000:
                    bios_symbols.append((addr, name))
                elif addr >= 0xF380:
                    work_symbols.append((addr, name))
                elif name.startswith("WORK_") or (0xC000 <= addr < 0xF380):
                    user_work_symbols.append((addr, name))
                else:
                    other_symbols.append((addr, name))

            # 1. BIOS シンボル
            if bios_symbols:
                out.write("; === MSX BIOS & System Hooks ===\n")
                for addr, name in sorted(bios_symbols, key=lambda x: x[0]):
                    out.write(f"{name:16} EQU {format_asm_hex(addr)}\n")
                out.write("\n")

            # 2. システムワークエリア
            if work_symbols:
                out.write("; === System Work Area ===\n")
                for addr, name in sorted(work_symbols, key=lambda x: x[0]):
                    sz = self.var_sizes.get(addr, 0)
                    sz_comment = f" ; {sz} byte{'s' if sz > 1 else ''}" if sz > 0 else ""
                    out.write(f"{name:16} EQU {format_asm_hex(addr)}{sz_comment}\n")
                out.write("\n")

            # 3. ユーザーワークエリア (RAM)
            if user_work_symbols:
                out.write("; === User Work Area (RAM) ===\n")
                sorted_user_work = sorted(user_work_symbols, key=lambda x: x[0])
                for i, (addr, name) in enumerate(sorted_user_work):
                    size = self.var_sizes.get(addr, 0)
                    diff_to_next = None
                    if i + 1 < len(sorted_user_work):
                        diff_to_next = sorted_user_work[i + 1][0] - addr

                    if size == 2:
                        comment = "; 2 bytes (word)"
                    elif size == 1:
                        comment = "; 1 byte"
                    elif diff_to_next and diff_to_next > 1:
                        comment = f"; {diff_to_next} bytes"
                    else:
                        comment = "; 1 byte"

                    out.write(f"{name:16} EQU {format_asm_hex(addr)}    {comment}\n")
                out.write("\n")

            # 4. その他の外部参照
            if other_symbols:
                out.write("; === Other External Symbols ===\n")
                for addr, name in sorted(other_symbols, key=lambda x: x[0]):
                    out.write(f"{name:16} EQU {format_asm_hex(addr)}\n")
                out.write("\n")

            # 各バンクの逆アセンブル出力
            for bank in self.banks:
                out.write("; " + "=" * 70 + "\n")
                out.write(f"; BANK {bank.bank_id:02X} (ORG {format_asm_hex(bank.base_addr)})\n")
                out.write("; " + "=" * 70 + "\n")
                out.write(f"    ORG {format_asm_hex(bank.base_addr)}\n\n")

                pc = bank.base_addr

                while pc < bank.end_addr:
                    # ROMヘッダの構造化出力 (手前に空行を入れて見やすくする)
                    if is_rom_header and pc == self.header_addr and bank.is_in_bank(self.header_addr):
                        out.write("\nROM_HEADER:\n")
                        out.write('    db  "AB"\n')
                        init_p = bank.get_word(pc + 2)
                        stmt_p = bank.get_word(pc + 4)
                        dev_p  = bank.get_word(pc + 6)
                        text_p = bank.get_word(pc + 8)

                        def get_lbl(a):
                            return self.global_labels.get(a, format_asm_hex(a))

                        out.write(f"    dw  {get_lbl(init_p)} ; INIT\n")
                        out.write(f"    dw  {get_lbl(stmt_p) if stmt_p else '0000H'} ; STATEMENT\n")
                        out.write(f"    dw  {get_lbl(dev_p)  if dev_p  else '0000H'} ; DEVICE\n")
                        out.write(f"    dw  {get_lbl(text_p) if text_p else '0000H'} ; TEXT\n")
                        reserved = [format_asm_hex(bank.get_byte(pc + 10 + i), 2) for i in range(6)]
                        out.write(f"    db  {', '.join(reserved)} ; Reserved\n\n")
                        pc += 16
                        continue

                    if pc in self.global_labels:
                        out.write(f"\n{self.global_labels[pc]}:\n")

                    idx = pc - bank.base_addr
                    if bank.attr[idx] == 'CODE':
                        def get_lbl(a):
                            return self.global_labels.get(a, format_asm_hex(a))

                        length, _, text, _, _, _, _ = bank.decoder.decode(pc, get_lbl)
                        out.write(f"    {text}\n")
                        pc += length
                    else:
                        # DATAの処理: 最低1バイトは必ず進める
                        db_bytes = [bank.get_byte(pc)]
                        pc += 1
                        while pc < bank.end_addr and bank.attr[pc - bank.base_addr] != 'CODE':
                            if is_rom_header and pc == self.header_addr:
                                break
                            if pc in self.global_labels:
                                break
                            if len(db_bytes) >= 16:
                                break
                            db_bytes.append(bank.get_byte(pc))
                            pc += 1

                        tokens = [format_asm_hex(b, 2) for b in db_bytes]
                        out.write(f"    db  {', '.join(tokens)}\n")

                out.write("\n")

        self.log(f"[+] 完了しました: {self.output_file}")


# =====================================================================
# 引数解析
# =====================================================================
def parse_hex_val(val_str):
    if not val_str:
        return None
    val_str = val_str.rstrip("hH")
    return int(val_str, 16)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="MSX Z80 Intelligent Disassembler (msx_disasm)",
        add_help=False
    )
    # 位置引数（-i なしで入力ファイル指定可能）
    parser.add_argument("file_pos", nargs="?", default=None, help="入力ファイルパス")
    parser.add_argument("-i", "--input", dest="file_opt", help="入力ファイルパス")

    parser.add_argument("-o", "--output", default=None, help="出力アセンブリファイルパス (省略時: <入力名>.asm)")
    parser.add_argument("-a", "--address", default="4000", help="ROM配置開始アドレス (16進数、デフォルト: 4000)")
    parser.add_argument("-h", "--header", default=None, help="ROMヘッダアドレス (16進数、省略時は -a と同一)")
    parser.add_argument("-m", "--mapper", default="NORMAL",
                        choices=["NORMAL", "KONAMI", "KONAMI-SCC", "ASCII8", "ASCII16", "NONE"],
                        type=str.upper,
                        help="マッパー種別 (NORMAL, KONAMI, KONAMI-SCC, ASCII8, ASCII16, NONE)")
    parser.add_argument("-c", "--com", action="store_true", help="MSX-DOS COM形式として強制処理 (ORG 0100H)")
    parser.add_argument("-b", "--bload", action="store_true", help="MSX BASIC BLOAD形式として強制処理 (7バイトヘッダ自動解析)")
    parser.add_argument("--help", action="help", help="ヘルプを表示")

    args = parser.parse_args()

    input_path = args.file_opt or args.file_pos
    if not input_path:
        parser.print_help()
        sys.exit(1)

    if args.output:
        output_path = args.output
    else:
        base_name, _ = os.path.splitext(input_path)
        output_path = base_name + ".asm"

    base_addr = parse_hex_val(args.address)
    header_addr = parse_hex_val(args.header) if args.header else None

    mapper_type = args.mapper
    format_override = None
    if args.com:
        format_override = "COM"
        mapper_type = "NONE"
    elif args.bload:
        format_override = "BLOAD"
        mapper_type = "NONE"
    elif args.header is not None and mapper_type == "NONE":
        mapper_type = "NORMAL"

    return input_path, output_path, base_addr, header_addr, mapper_type, format_override


if __name__ == "__main__":
    in_f, out_f, base_a, hdr_a, map_t, fmt_o = parse_arguments()
    disasm = MsxDisassembler(in_f, out_f, base_a, hdr_a, map_t, fmt_o)
    disasm.run()

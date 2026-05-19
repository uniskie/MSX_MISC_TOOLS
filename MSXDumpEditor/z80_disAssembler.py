import re

# ==========================================
# ヘルパー：0x表記をH表記に変更
# ==========================================
def format_asm_to_h_style(asm_str: str) -> str:
    """
    アセンブリ文字列内の '0x...' 表記を 'xxH' 表記に一括変換する。
    最上位の桁が A〜F の場合は先頭に '0' を追加する。
    例: "JP 0x8000" -> "JP 8000H", "JP 0xC000" -> "JP 0C000H"
    """
    def replacer(match):
        # 0xの後の16進数部分を取得し、大文字に揃える
        hex_val = match.group(1).upper()
        # 先頭文字がA〜Fなら0を付与
        if hex_val[0] in "ABCDEF":
            return "0" + hex_val + "H"
        return hex_val + "H"
    
    # 0xに続く1文字以上の16進数をキャプチャして置換
    return re.sub(r'0x([0-9A-Fa-f]+)', replacer, asm_str)

# ============================================================================
# z80 1ライン逆アセンブラ クラス
#
# z80disasm.decode( bytes data, int address )
# output -> [string, bytes]
# 
# 使い方：
#   from z80disasm import z80disasm
#   z80disasm = z80disasm()
#   rer_str, ret_bin = z80disasm.decode( data, address )
#
#   次の行を逆アセンブルする場合は、
#   dataとadressの位置をlen(ret_bin)分進めてdisasmを呼び出す。
#  
# 免責：
#   懐かしいC/C++コードをGemini3にコンバートさせたものなので、
#   保証と著作権はありません。
#
# ============================================================================

class z80disasm:
    # 非公式命令を許可するかどうか
    ALLOW_UNOFFICIAL_INSTRUCTION: bool = True

    # 本来は未定義の命令に警告を出すかどうか
    CAUTION_UNOFFICIAL_INSTRUCTION: bool = True

    def __init__(self):

        # メイン命令、ビット操作(CB)、拡張命令(ED)の3つの辞書を用意
        self.base_table = {}
        self.cb_table = {}
        self.ed_table = {}
        self._build_tables()

    def _build_tables(self):
        """ Z80の命令表を動的に生成 """
        # Z80のオペコードは原則として1バイト(8ビット)であり、
        # [xx] [yyy] [zzz] というビット構成（x:上位2bit, y:中位3bit, z:下位3bit）
        # のように規則的に割り当てられているため、アルゴリズムで一括生成できる。
        regs = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A']  # 8ビットレジスタ (y, zに対応)
        rp = ['BC', 'DE', 'HL', 'SP']                       # 16ビットレジスタペア1
        rp2 = ['BC', 'DE', 'HL', 'AF']                      # 16ビットレジスタペア2 (PUSH/POP用)
        alu_ops = ['ADD A,', 'ADC A,', 'SUB', 'SBC A,', 'AND', 'XOR', 'OR', 'CP'] # 算術論理演算
        cc = ['NZ', 'Z', 'NC', 'C', 'PO', 'PE', 'P', 'M']   # 条件フラグ

        # ==========================================
        # 1. ベース命令 (0x00 - 0xFF) の生成
        # ==========================================
        for i in range(256):
            # 8ビットのオペコードを x, y, z に分割
            x = (i >> 6) & 3   # 上位 2ビット (0-3): 命令グループ
            y = (i >> 3) & 7   # 中位 3ビット (0-7): 第一オペランド(dst)など
            z = i & 7          # 下位 3ビット (0-7): 第二オペランド(src)など
            
            # y をさらに分割 (16ビットレジスタ指定などで使用)
            p = y >> 1         # y の上位 2ビット (0-3)
            q = y & 1          # y の最下位 1ビット (0-1)

            if x == 0:  # グループ0: 制御命令、ロード、16ビット演算など
                if z == 0:
                    if y == 0: self.base_table[i] = "NOP"
                    elif y == 1: self.base_table[i] = "EX AF, AF'"
                    elif y == 2: self.base_table[i] = "DJNZ #r" # #r は相対ジャンプのマーカー
                    elif y == 3: self.base_table[i] = "JR #r"
                    else: self.base_table[i] = f"JR {cc[y-4]}, #r"
                elif z == 1: 
                    self.base_table[i] = f"LD {rp[p]}, #w" if q == 0 else f"ADD HL, {rp[p]}"
                elif z == 2:
                    if q == 0: self.base_table[i] = ["LD (BC), A", "LD (DE), A", "LD (#w), HL", "LD (#w), A"][p]
                    else: self.base_table[i] = ["LD A, (BC)", "LD A, (DE)", "LD HL, (#w)", "LD A, (#w)"][p]
                elif z == 3: 
                    self.base_table[i] = f"INC {rp[p]}" if q == 0 else f"DEC {rp[p]}"
                elif z == 4: self.base_table[i] = f"INC {regs[y]}"
                elif z == 5: self.base_table[i] = f"DEC {regs[y]}"
                elif z == 6: self.base_table[i] = f"LD {regs[y]}, #b" # #b は8ビット即値のマーカー
                elif z == 7: 
                    self.base_table[i] = ["RLCA", "RRCA", "RLA", "RRA", "DAA", "CPL", "SCF", "CCF"][y]

            elif x == 1:  # グループ1: 8ビットレジスタ間のロード命令 (LD r, r')
                if i == 0x76: self.base_table[i] = "HALT"
                else: self.base_table[i] = f"LD {regs[y]}, {regs[z]}"

            elif x == 2:  # グループ2: 8ビット算術論理演算 (ADD, SUB, XORなど)
                self.base_table[i] = f"{alu_ops[y]} {regs[z]}"

            elif x == 3:  # グループ3: 分岐、関数コール、I/Oなど
                if z == 0: self.base_table[i] = f"RET {cc[y]}"
                elif z == 1:
                    if q == 0: self.base_table[i] = f"POP {rp2[p]}"
                    else: self.base_table[i] = ["RET", "EXX", "JP (HL)", "LD SP, HL"][p]
                elif z == 2: self.base_table[i] = f"JP {cc[y]}, #w" # #w は16ビット即値のマーカー
                elif z == 3:
                    tbl = {0xC3: "JP #w", 0xD3: "OUT (#b), A", 0xDB: "IN A, (#b)", 
                           0xE3: "EX (SP), HL", 0xEB: "EX DE, HL", 0xF3: "DI", 0xFB: "EI"}
                    if i in tbl: self.base_table[i] = tbl[i]
                elif z == 4: self.base_table[i] = f"CALL {cc[y]}, #w"
                elif z == 5:
                    if q == 0: self.base_table[i] = f"PUSH {rp2[p]}"
                    elif p == 0: self.base_table[i] = "CALL #w"
                elif z == 6: self.base_table[i] = f"{alu_ops[y]} #b"
                elif z == 7: self.base_table[i] = f"RST {y*8:02X}H"

        # ==========================================
        # 2. CBプレフィックス (ビット操作命令) の生成
        # ==========================================
        cb_ops = ['RLC', 'RRC', 'RL', 'RR', 'SLA', 'SRA', 'SLL', 'SRL']
        for i in range(256):
            r = regs[i % 8]
            if i < 0x40:   self.cb_table[i] = f"{cb_ops[i // 8]} {r}"     # シフト・ローテート
            elif i < 0x80: self.cb_table[i] = f"BIT {(i // 8) % 8}, {r}"  # ビットテスト
            elif i < 0xC0: self.cb_table[i] = f"RES {(i // 8) % 8}, {r}"  # ビットリセット
            else:          self.cb_table[i] = f"SET {(i // 8) % 8}, {r}"  # ビットセット

        # ==========================================
        # 3. EDプレフィックス (拡張命令) の生成
        # ==========================================
        for i in range(256):
            x = (i >> 6) & 3; y = (i >> 3) & 7; z = i & 7; p = y >> 1; q = y & 1
            if x == 1:
                if z == 0: self.ed_table[i] = f"IN {regs[y]}, (C)" if y != 6 else "IN (C)"
                elif z == 1: self.ed_table[i] = f"OUT (C), {regs[y]}" if y != 6 else "OUT (C), 0"
                elif z == 2: self.ed_table[i] = f"SBC HL, {rp[p]}" if q == 0 else f"ADC HL, {rp[p]}"
                elif z == 3: self.ed_table[i] = f"LD (#w), {rp[p]}" if q == 0 else f"LD {rp[p]}, (#w)"
                elif z == 4: self.ed_table[i] = "NEG"
                elif z == 5: self.ed_table[i] = "RETI" if y == 1 else "RETN"
                elif z == 6: self.ed_table[i] = f"IM {[0, 0, 1, 2, 0, 0, 1, 2][y]}"
                elif z == 7: self.ed_table[i] = ["LD I, A", "LD R, A", "LD A, I", "LD A, R", "RRD", "RLD", "NOP", "NOP"][y]
            elif x == 2:
                block_ops = {
                    0xA0: "LDI", 0xA1: "CPI", 0xA2: "INI", 0xA3: "OUTI",
                    0xA8: "LDD", 0xA9: "CPD", 0xAA: "IND", 0xAB: "OUTD",
                    0xB0: "LDIR", 0xB1: "CPIR", 0xB2: "INIR", 0xB3: "OTIR",
                    0xB8: "LDDR", 0xB9: "CPDR", 0xBA: "INDR", 0xBB: "OTDR"
                }
                if i in block_ops: self.ed_table[i] = block_ops[i]

    def decode(self, data: bytes, address: int) -> list:
        if not data: return ["", bytes()]
        op_bytes = bytearray()
        
        # 内部関数：データを1バイト進めて取得し、消費したバイト列(op_bytes)に記録する
        def fetch_byte():
            if len(op_bytes) < len(data):
                val = data[len(op_bytes)]
                op_bytes.append(val)
                return val
            return None

        # 内部関数：非公式なプレフィックスを無効化する場合、最初の1バイトだけをDBにして返す
        def ignore_prefix():
            # フェッチ済みの後続バイトは今回のデコード結果に含めず、呼び出し元で次回処理させる
            return [f"DB 0x{op_bytes[0]:02X}", bytes([op_bytes[0]])]

        # 内部関数：必要なデータをフェッチしなかった場合、全体をDB化する
        def fetch_error():
            hex_str = ", ".join([f"0x{b:02X}" for b in op_bytes])
            return [f"DB {hex_str} ; ?", bytes(op_bytes)]

        op = fetch_byte()
        if op is None: return ["", bytes()]

        fmt = ""
        index_reg = None

        # ==========================================
        # プレフィックスの判定
        # Z80では DD は HL を IX に、FD は HL を IY に置き換えるフラグとして機能する
        # ==========================================
        if op in (0xDD, 0xFD):
            index_reg = "IX" if op == 0xDD else "IY"
            op = fetch_byte()
            if op is None: return fetch_error()

        # ==========================================
        # オペコードの分岐処理 (CB, ED, ベース命令)
        # ==========================================
        if op == 0xCB:
            if index_reg:
                # DD CB または FD CB
                # 特殊：4バイト構成になる。
                #「DD CB <オフセット> <オペコード>」
                #「FD CB <オフセット> <オペコード>」
                offset = fetch_byte()
                sub_op = fetch_byte()
                if sub_op is None: return fetch_error()
                
                # オフセットは符号付き8ビット (2の補数)
                offset_signed = offset if offset < 128 else offset - 256
                is_unofficial = (sub_op & 0x07) != 0x06 # 下位3ビットが (HL) 以外なら非公式(メモリとレジスタ双方に書き出し)
                
                if is_unofficial:
                    if not self.ALLOW_UNOFFICIAL_INSTRUCTION:
                        # DD CBの非公式命令は4バイト不可分なので、全体をDB化する
                        hex_str = ", ".join([f"0x{b:02X}" for b in op_bytes])
                        return [f"DB {hex_str}", bytes(op_bytes)]
                    
                    # 強制的に下位3ビットを 6 (HL) にしてベース命令を取得し、置換
                    sub_op_hl = (sub_op & 0xF8) | 0x06
                    fmt_hl = self.cb_table.get(sub_op_hl, f"DB CB, {sub_op_hl:02X}")
                    #fmt = fmt_hl.replace("(HL)", f"({index_reg}{offset_signed:+d})")
                    fmt = fmt_hl.replace("(HL)", f"({index_reg}" f"{'-' if offset_signed < 0 else '+'}" f"0x{abs(offset_signed):02X})")
                    
                    # BIT命令以外はメモリとレジスタ双方に書き出し
                    if not fmt.startswith("BIT"):
                        r = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A'][sub_op & 7]
                        fmt += f", {r}"
                        
                    if self.CAUTION_UNOFFICIAL_INSTRUCTION:
                        fmt += " ;*非公式：メモリとレジスタ双方に書き出し*"
                else:
                    fmt = self.cb_table.get(sub_op, f"DB CB, {sub_op:02X}")
                    # フォーマット内の (HL) を (IX+d) または (IY+d) に書き換える
                    #fmt = fmt.replace("(HL)", f"({index_reg}{offset_signed:+d})")
                    fmt = fmt.replace("(HL)", f"({index_reg}"f"{'-' if offset_signed < 0 else '+'}"f"0x{abs(offset_signed):02X})")
                
                # DD CB命令は他の即値を持たないため、ここで処理を完了して返す
                return [fmt, bytes(op_bytes)]
            else:
                # 通常のCBプレフィックス命令 (例: CB C7 -> SET 0, A)
                sub_op = fetch_byte()
                if sub_op is None: return fetch_error()
                fmt = self.cb_table.get(sub_op, f"DB CB, {sub_op:02X}")

        elif op == 0xED:
            # EDプレフィックスではDD/FDが無効なので、無効命令扱いとする
            # Z80の回路設計上、DDやFDを読み込んだ直後にEDが来ると、
            # 「HLをIX/IYに置き換える」という内部状態が強制的にリセットされてしまう。
            # 例: DD ED B0 は「LDIR (IX使用)」ではなく、ただの「LDIR (HL使用)」として動く。
            sub_op = fetch_byte()
            if sub_op is None: return fetch_error()
            
            if index_reg:
                if not self.ALLOW_UNOFFICIAL_INSTRUCTION:
                    return ignore_prefix() # プレフィックスの1バイトだけ消費する
                fmt = self.ed_table.get(sub_op, f"DB ED, {sub_op:02X}")
                if self.CAUTION_UNOFFICIAL_INSTRUCTION:
                    fmt += " ;*非公式：IX/IY指定無効*"
                # ハードウェアの挙動を再現するため、IX/IY化フラグを無効化する
                index_reg = None
            else:
                fmt = self.ed_table.get(sub_op, f"DB ED, {sub_op:02X}")

        else:
            # プレフィックスを持たない通常の命令
            fmt = self.base_table.get(op, f"DB {op:02X}")

        # ==========================================
        # IX / IY レジスタの置換
        # IX/IY用の巨大なテーブルを作らず、
        # HL用の文字列を置換してコンパクト化
        # ==========================================
        if index_reg:
            is_unofficial = False
            is_redundant = False

            if op == 0xE9:
                # JP (HL) は例外でオフセット変位を持たない
                fmt = fmt.replace("(HL)", f"({index_reg})")
            elif "(HL)" in fmt:
                # "(HL)" の場合は必ず1バイトのオフセット(変位)を伴う (例: DD 7E 05 -> LD A, (IX+0x5))
                offset = fetch_byte()
                if offset is None: return fetch_error()
                offset_signed = offset if offset < 128 else offset - 256
                #fmt = fmt.replace("(HL)", f"({index_reg}{offset_signed:+d})")
                fmt = fmt.replace("(HL)", f"({index_reg}"f"{'-' if offset_signed < 0 else '+'}"f"0x{abs(offset_signed):02X})")
            elif re.search(r'\bHL\b', fmt):
                # 公式命令: HLをIXに置換 (正規表現の単語境界を使って誤爆を防ぐ)
                fmt = re.sub(r'\bHL\b', index_reg, fmt)
            elif re.search(r'\b[HL]\b', fmt):
                # 非公式命令: HやL単独の命令にプレフィックスがついている(IXH/IXL化)
                # レジスタ自体の置換 (例: H -> IXH, L -> IXL)
                is_unofficial = True
                if not self.ALLOW_UNOFFICIAL_INSTRUCTION:
                    return ignore_prefix() # プレフィックスの1バイトだけ消費する
                fmt = re.sub(r'\bH\b', f"{index_reg}H", fmt)
                fmt = re.sub(r'\bL\b', f"{index_reg}L", fmt)
            else:
                # 冗長命令: HLもHもLも関係ない命令にプレフィックスがついている (例: DD 40 -> LD B, B)
                # (例: FD 01 05 00 -> FDプレフィックス + LD BC, 0x0005)
                is_redundant = True
                if not self.ALLOW_UNOFFICIAL_INSTRUCTION:
                    return ignore_prefix() # プレフィックスの1バイトだけ消費する
    
            if (is_unofficial or is_redundant) and self.ALLOW_UNOFFICIAL_INSTRUCTION and self.CAUTION_UNOFFICIAL_INSTRUCTION:
                if is_redundant:
                    fmt += " ;*非公式：IX/IY指定無効*" 
                else:
                    fmt += " ;*非公式*" 

        # ==========================================
        # オペランドのフォーマット処理 (マーカーの置換)
        # ==========================================
        asm = fmt
        
        # 8ビット即値 (#b)
        if "#b" in asm:
            val = fetch_byte()
            if val is not None: asm = asm.replace("#b", f"0x{val:02X}")
            else: asm = fetch_error()[0]

        # 16ビット即値 (#w) - リトルエンディアンで読み込む
        if "#w" in asm:
            lo = fetch_byte()
            hi = fetch_byte()
            if lo is not None and hi is not None:
                asm = asm.replace("#w", f"0x{(hi << 8 | lo):04X}")
            else: asm = fetch_error()[0]

        # 相対ジャンプ (#r) - 符号付きオフセットから飛び先アドレスを計算する
        if "#r" in asm:
            offset = fetch_byte()
            if offset is not None:
                offset_signed = offset if offset < 128 else offset - 256
                # 現在のアドレス + 実行中の命令の総バイト数 + オフセット
                target_addr = (address + len(op_bytes) + offset_signed) & 0xFFFF
                asm = asm.replace("#r", f"0x{target_addr:04X}")
            else: asm = fetch_error()[0]

        return [asm, bytes(op_bytes)]

    # 渡されたデータを全て逆アセンブル
    def disasm(self, data: bytes, address: int) -> list:
        if not data: return ''

        address_delim = ":"
        body_delim = ">"
        comment_delim = ";"

        def _extract_address_immidiate(str):
            if comment_delim in str:
                str = str.split(';', 1)[0]
            # (0xXXXX)
            match_indirect = re.search(r'\((0x[0-9A-Fa-f]{4})\)', str, re.IGNORECASE)
            if match_indirect:
                return match_indirect.group(1)
            # JP/JR/DJNZ/CALL
            match_jump = re.search(r'\b(JP|JR|DJNZ|CALL|)\b.*\s+(0x[0-9A-Fa-f]{4})', str, re.IGNORECASE)
            if match_jump:
                return match_jump.group(2)
            return None
        
        def _hex_label(adr):
            return f"X{adr:04X}"

        # 一旦 0xXXXX形式で すべて逆アセンブルしながら、アドレス参照リスト作成
        lines = []
        address_set = set()
        adr_imm_set = set()
        
        idx=0
        cur_address = address
        while idx < len(data):
            address_set.add(cur_address)

            # 命令を一つでコード
            asm_str, asm_bin = self.decode(data[idx:idx+4], cur_address)
            bin_len = len(asm_bin)

            # アドレス指定があれば抽出
            if (adr_imm := _extract_address_immidiate(asm_str)) is not None:
                try:
                    # アドレス一覧に登録
                    adr = int(adr_imm, 16)
                    adr_imm_set.add(adr)
                except ValueError:
                    pass

            lines.append(
                f"{cur_address:04X}{address_delim} {asm_bin.hex(' ').upper().ljust(11)}{body_delim}{asm_str}"
            )
            idx += bin_len
            cur_address += bin_len
        
        end_address = cur_address
        address_set.add(cur_address)

        # アドレスラベルの為に、命令が存在したアドレスに限定
        jump_adr_set = {addr for addr in adr_imm_set if addr in address_set}

        # 最終整形
        cur_address = address
        pre_address = address
        output = []
        for line_str in lines:

            # アドレス取得
            if address_delim in line_str:
                adr_str = line_str.split(address_delim, 1)[0]
                try:
                    cur_address = int(adr_str, 16)
                except ValueError:
                    pass

            # ラベルの出力
            label = "        "
            for a in range(pre_address, cur_address+1):
                if cur_address in jump_adr_set:
                    label = (_hex_label(cur_address)+address_delim).ljust(8)

            # コメントの分離
            if comment_delim in line_str:
                body, comment = line_str.split(comment_delim, 1)
            else:
                body = line_str
                comment = ""

            # アドレス＋HEX の分離
            if body_delim in body:
                byte_info, asm_str = body.split(body_delim, 1)
            else:
                byte_info = ""
                asm_str = line_str

            # アドレス指定からラベルへの変換
            if adr_imm := _extract_address_immidiate(asm_str):
                try:
                    # アドレス一覧にあればラベル化
                    adr = int(adr_imm, 16)
                    if adr in jump_adr_set:
                        asm_str = asm_str.replace(adr_imm, _hex_label(adr))
                except ValueError:
                    pass

            # 0XXXXH形式に変更
            asm_str = format_asm_to_h_style(asm_str)

            output.append(
                f"{label}{asm_str.ljust(28)}; {byte_info.ljust(20)} {comment}" 
            )

        # ラベルの出力(末尾)
        for a in range(cur_address, end_address+1):
            if a in jump_adr_set:
                output.append(_hex_label(a))

        return "\n".join(output) + "\n"

# ==========================================
# 実行テスト
# ==========================================
if __name__ == "__main__":
    z80 = z80disasm()

    # テストパターン
    test_code  = b"\x23"               # INC HL
    test_code += b"\xDD\x23"           # INC IX         (DDプレフィックスによるHL置換)
    test_code += b"\xED\xB0"           # LDIR           (EDプレフィックス)
    test_code += b"\xDD\xED\xB0"       # LDIR           (DDの後にEDが来たため、DDは無視される)
    test_code += b"\xCB\xC7"           # SET 0, A       (CBプレフィックス)
    test_code += b"\xDD\xCB\x05\xC6"   # SET 0, (IX+5)  (DDCBプレフィックスの特殊バイト順)
    test_code += b"\xDD\xCB\x05\x00"   # RLC (IX+5), B  (非公式: DD CB : メモリとレジスタ双方に書き出し
    test_code += b"\xDD\x44"           # LD B, IXH      (非公式: IXHアクセス)
    test_code += b"\xFD\x01\x05\x00"   # LD BC, 0x0005  (非公式: 無関係な命令にFDが付いている冗長命令)
    test_code += b"\x18\x04"           # JR +4          (相対ジャンプ)
    test_code += b"\xC3\x00\x80"       # JP 0x8000      (16ビット即値)

    address = 0x0100

    def format_str(str):
        parts= str.split(";",1)
        if len(parts) == 2:
            str = parts[0].ljust(20) + ";" + parts[1].strip()
        return str

    for allow_flag in [False, True]:
        print(f"\n[ ALLOW_UNOFFICIAL_INSTRUCTION = {allow_flag} ]")
        z80.ALLOW_UNOFFICIAL_INSTRUCTION = allow_flag
        
        for hex_conv in [False, True]:
            pos = 0
            curr_address = address
            print(f"{'Address':<8} | {'Bytes':<16} | {'Assembly'}")
            print("-" * 55)
        
            while pos < len(test_code):
                asm, consumed_bytes = z80.decode(test_code[pos:], curr_address)
                hex_bytes = " ".join([f"{b:02X}" for b in consumed_bytes])
                if hex_conv:
                    asm = format_asm_to_h_style(asm)
                asm = format_str(asm)
                print(f"{curr_address:04X}     | {hex_bytes:<16} | {asm}")
                length = len(consumed_bytes)
                curr_address += length
                pos += length

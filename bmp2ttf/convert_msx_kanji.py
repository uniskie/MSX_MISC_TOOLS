#!/usr/bin/env python3
"""
MSX 漢字ROM 形式変換スクリプト (Usage/ヘルプ拡充版)

物理ROM（32KB×4バンク）とリニア形式（1文字32BのZ字順）を相互変換します。
複合ファームウェアイメージからのオフセット切り出しにも対応しています。
"""

import sys
import argparse
from pathlib import Path

BANK_SIZE = 0x8000          # 32KB (各象限ブロックのサイズ)
LEVEL_SIZE = BANK_SIZE * 4  # 128KB (1水準分のサイズ: 0x20000)
BLOCK_SIZE = 8              # 8x8ドット = 8バイト
CHARS_PER_LEVEL = 4096

EPILOG_USAGE = """
使用例 (Examples):
  1. 単体の生ROMイメージ (128KBまたは256KB) をリニア形式に変換:
     %(prog)s raw_maskrom.bin -o KANJI.ROM

  2. 複合ファームウェア内の特定アドレスから第1+第2水準 (256KB) を切り出して変換:
     %(prog)s firmware_dump.bin -s 0x80000 -o KANJI.ROM

  3. オフセット指定かつ第1水準 (128KB) のみ抽出:
     %(prog)s firmware_dump.bin -s 0x40000 -L 1 -o KANJI1.ROM

  4. バイトサイズを明示して切り出し (例: 0x40000 = 256KB):
     %(prog)s firmware_dump.bin -s 0x100000 -l 0x40000 -o KANJI.ROM

  5. 逆変換 (エミュレータ用リニア形式 -> 物理生ROM形式・実機ROM焼き用):
     %(prog)s KANJI.ROM -r -o raw_burned.bin

補足:
  ・オフセット (-s) やサイズ (-l) は "0x80000" (16進数) または "524288" (10進数) の両方に対応。
  ・出力ファイル名 (-o) を省略した場合は、自動的にサフィックスを付与して保存します。
"""


def parse_int(val: str) -> int:
    """10進数または16進数(0x...)の文字列を整数に変換"""
    try:
        return int(val, 0)
    except ValueError:
        raise argparse.ArgumentTypeError(f"無効な数値形式です: '{val}' (例: 0x40000, 262144)")


def raw_to_linear(data: bytes) -> bytearray:
    """物理ROM形式 (32KBバンク分割) -> リニア形式 (文字ごとZ字順)"""
    num_levels = len(data) // LEVEL_SIZE
    output = bytearray(len(data))
    out_idx = 0

    for level in range(num_levels):
        base = level * LEVEL_SIZE
        bank_tl = base + 0x00000  # 左上
        bank_tr = base + 0x08000  # 右上
        bank_bl = base + 0x10000  # 左下
        bank_br = base + 0x18000  # 右下

        for n in range(CHARS_PER_LEVEL):
            offset = n * BLOCK_SIZE
            output[out_idx:out_idx + 8] = data[bank_tl + offset : bank_tl + offset + 8]
            out_idx += 8
            output[out_idx:out_idx + 8] = data[bank_tr + offset : bank_tr + offset + 8]
            out_idx += 8
            output[out_idx:out_idx + 8] = data[bank_bl + offset : bank_bl + offset + 8]
            out_idx += 8
            output[out_idx:out_idx + 8] = data[bank_br + offset : bank_br + offset + 8]
            out_idx += 8

    return output


def linear_to_raw(data: bytes) -> bytearray:
    """リニア形式 (文字ごとZ字順) -> 物理ROM形式 (32KBバンク分割)"""
    num_levels = len(data) // LEVEL_SIZE
    output = bytearray(len(data))
    in_idx = 0

    for level in range(num_levels):
        base = level * LEVEL_SIZE
        bank_tl = base + 0x00000
        bank_tr = base + 0x08000
        bank_bl = base + 0x10000
        bank_br = base + 0x18000

        for n in range(CHARS_PER_LEVEL):
            offset = n * BLOCK_SIZE
            output[bank_tl + offset : bank_tl + offset + 8] = data[in_idx : in_idx + 8]
            in_idx += 8
            output[bank_tr + offset : bank_tr + offset + 8] = data[in_idx : in_idx + 8]
            in_idx += 8
            output[bank_bl + offset : bank_bl + offset + 8] = data[in_idx : in_idx + 8]
            in_idx += 8
            output[bank_br + offset : bank_br + offset + 8] = data[in_idx : in_idx + 8]
            in_idx += 8

    return output


def main():
    parser = argparse.ArgumentParser(
        description="MSX 漢字ROM 物理生イメージ ⇔ リニア形式 相互変換ツール",
        epilog=EPILOG_USAGE,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("input", type=str, help="入力ファイルパス (ファームウェアダンプ等)")
    parser.add_argument("-o", "--output", type=str, default=None, help="出力ファイルパス (省略時は自動命名)")
    parser.add_argument("-s", "--offset", type=parse_int, default=0, help="漢字領域の開始オフセット (例: 0x80000) [デフォルト: 0x0]")
    parser.add_argument("-L", "--level", type=int, choices=[1, 2], default=None, help="水準指定 (1: 第1水準 128KB, 2: 第1+第2水準 256KB)")
    parser.add_argument("-l", "--size", type=parse_int, default=None, help="抽出サイズ (例: 0x20000, 0x40000)。--levelより優先")
    parser.add_argument("-r", "--reverse", action="store_true", help="逆変換を行う (リニア形式 -> 物理生ROM形式)")

    # 引数なしで実行された場合はUsageを表示して終了
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"エラー: 入力ファイルが見つかりません: {input_path}", file=sys.stderr)
        sys.exit(1)

    full_data = input_path.read_bytes()
    file_size = len(full_data)

    # オフセット検証
    if args.offset >= file_size:
        print(f"エラー: 開始オフセット (0x{args.offset:X}) がファイルサイズ (0x{file_size:X}) を超えています。", file=sys.stderr)
        sys.exit(1)

    remaining_size = file_size - args.offset

    # 抽出サイズ決定
    if args.size is not None:
        target_size = args.size
    elif args.level == 1:
        target_size = LEVEL_SIZE  # 128KB
    elif args.level == 2:
        target_size = LEVEL_SIZE * 2  # 256KB
    else:
        # 自動判定 (256KB以上残っていれば256KB、128KB以上あれば128KB)
        if remaining_size >= LEVEL_SIZE * 2:
            target_size = LEVEL_SIZE * 2
        elif remaining_size >= LEVEL_SIZE:
            target_size = LEVEL_SIZE
        else:
            print(f"エラー: オフセット以降の残りサイズ (0x{remaining_size:X} bytes) が128KB未満です。", file=sys.stderr)
            sys.exit(1)

    if args.offset + target_size > file_size:
        print(f"エラー: オフセット (0x{args.offset:X}) + サイズ (0x{target_size:X}) がファイル末尾を超えています。", file=sys.stderr)
        sys.exit(1)

    if target_size % LEVEL_SIZE != 0:
        print(f"エラー: 抽出サイズ (0x{target_size:X} bytes) が 128KB (0x20000) の倍数ではありません。", file=sys.stderr)
        sys.exit(1)

    # 切り出し
    data = full_data[args.offset : args.offset + target_size]

    levels_count = target_size // LEVEL_SIZE
    level_desc = "第1水準のみ (128KB)" if levels_count == 1 else "第1＋第2水準 (256KB)"

    if args.reverse:
        print("モード: リニア形式 -> 物理生ROM形式 に変換中...")
        result = linear_to_raw(data)
        default_name = f"{input_path.stem}_offset0x{args.offset:X}_raw.bin"
    else:
        print("モード: 物理生ROM形式 -> リニア形式 に補正中...")
        result = raw_to_linear(data)
        default_name = f"{input_path.stem}_offset0x{args.offset:X}_linear.rom"

    output_path = Path(args.output) if args.output else input_path.parent / default_name
    output_path.write_bytes(result)

    print(f"抽出範囲: 0x{args.offset:X} ～ 0x{args.offset + target_size - 1:X} ({level_desc})")
    print(f"保存完了: {output_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import re
import struct
import sys

# =============================================================================
# 組み込みデフォルト定義 (外部設定ファイル未指定時に使用)
# =============================================================================
DEFAULT_FONT_DEFINITIONS = [
    # [開始アドレス, 文字数, ビット形式]
    [0x2B400, 96, "8x8"],        # ASCII 20H～7FH (96文字)
    [0x2B700, 94, "16x8"],       # MSX ASCII 80H～DDH (94文字)
    [0x2BCE0, 2, "8x8x2"],       # MSX ASCII DEH～DFH (濁点・半濁点: 2文字)
    [0x2BD00, 32, "16x8"],       # MSX ASCII E0H～FFH (32文字)
    [0x7E000, 256 * 2, "16x8"],  # 漢字ブロック (512文字)
]


def parse_value(val):
    """
    数値または文字列を整数に変換するヘルパー。
    ・整数値そのまま
    ・乗算式 (例: '256*2')
    ・'H' 接尾辞の16進数 (例: '2B400H')
    ・'0x' 接頭辞の16進数 (例: '0x2B400')
    ・通常の10進数文字列
    に対応。
    """
    if isinstance(val, int):
        return val

    s = str(val).strip()

    if "*" in s:
        parts = s.split("*")
        result = 1
        for p in parts:
            result *= parse_value(p)
        return result

    if s.upper().endswith("H") and not s.upper().startswith("0X"):
        return int(s[:-1], 16)

    return int(s, 0)


def strip_trailing_commas(json_text):
    """
    文字列リテラル内部を保護しつつ、リストやオブジェクト末尾の余分なカンマを空白に置換する。
    文字長を変えずに空白置換することで、構文エラー発生時の行・桁番号のズレを防ぐ。
    """
    # group(1): 文字列リテラル ("...")
    # group(2): リスト/辞書の閉じカッコ直前にあるカンマ
    # group(3): 閉じカッコまでの空白文字
    # group(4): 閉じカッコ (] または })
    pattern = r'("(?:\\.|[^"\\])*")|(,)(\s*([\]\}]))'

    def replacer(match):
        if match.group(1) is not None:
            return match.group(1)
        # カンマを空白1文字に置換し、後ろの空白と閉じカッコをそのまま連結
        return " " + match.group(3)

    return re.sub(pattern, replacer, json_text)


def load_json_config(file_path):
    """
    JSON設定ファイルを読み込む。
    ・リスト/オブジェクト末尾の余分なカンマを許容
    ・構文エラー時に該当箇所の行・桁・ポインタを表示
    """
    if not os.path.isfile(file_path):
        print(f"エラー: 設定ファイルが見つかりません: {file_path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_content = f.read()
    except Exception as e:
        print(f"エラー: ファイルのオープンに失敗しました ({file_path}): {e}", file=sys.stderr)
        sys.exit(1)

    cleaned_content = strip_trailing_commas(raw_content)

    try:
        data = json.loads(cleaned_content)
    except json.JSONDecodeError as e:
        print(f"\nエラー: JSONの構文エラーが発生しました: {file_path}", file=sys.stderr)
        print(f"詳細: {e.msg} ({e.lineno}行目, {e.colno}文字目)", file=sys.stderr)
        print("-" * 55, file=sys.stderr)

        # エラー発生行の前後を表示
        lines = raw_content.splitlines()
        start_line = max(0, e.lineno - 2)
        end_line = min(len(lines), e.lineno + 1)

        for idx in range(start_line, end_line):
            curr_lineno = idx + 1
            line_str = lines[idx]
            prefix = f"{curr_lineno:4d} | "
            print(f"{prefix}{line_str}", file=sys.stderr)

            # エラー行の直下にキャレット (^) を表示
            if curr_lineno == e.lineno:
                caret_pos = len(prefix) + max(0, e.colno - 1)
                print(" " * caret_pos + "^", file=sys.stderr)

        print("-" * 55, file=sys.stderr)
        sys.exit(1)

    definitions = []
    if not isinstance(data, list):
        print(f"エラー: JSONのルート要素は配列(リスト)である必要があります: {file_path}", file=sys.stderr)
        sys.exit(1)

    for idx, item in enumerate(data, 1):
        try:
            if isinstance(item, (list, tuple)):
                if len(item) < 3:
                    print(f"警告: {idx}番目の要素をスキップ (要素数不足): {item}", file=sys.stderr)
                    continue
                addr = parse_value(item[0])
                count = parse_value(item[1])
                fmt = str(item[2]).strip()
            elif isinstance(item, dict):
                addr_key = next((k for k in ("address", "addr", "start") if k in item), None)
                fmt_key = next((k for k in ("format", "fmt", "type") if k in item), None)
                if not addr_key or "count" not in item or not fmt_key:
                    print(f"警告: {idx}番目の要素をスキップ (必須キー不足): {item}", file=sys.stderr)
                    continue
                addr = parse_value(item[addr_key])
                count = parse_value(item["count"])
                fmt = str(item[fmt_key]).strip()
            else:
                print(f"警告: 不明な形式の要素をスキップ: {item}", file=sys.stderr)
                continue

            definitions.append([addr, count, fmt])
        except Exception as ex:
            print(f"警告: {idx}番目の要素のパースに失敗したためスキップ: {item} ({ex})", file=sys.stderr)

    if not definitions:
        print(f"エラー: 有効なフォント定義が見つかりませんでした: {file_path}", file=sys.stderr)
        sys.exit(1)

    return definitions


def load_cfg(file_path):
    """従来の外部 .cfg ファイルからフォント定義リストを読み込む。"""
    if not os.path.isfile(file_path):
        print(f"エラー: 設定ファイルが見つかりません: {file_path}", file=sys.stderr)
        sys.exit(1)

    definitions = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                for comment_char in ("#", ";"):
                    if comment_char in line:
                        line = line.split(comment_char)[0]

                line = line.strip()
                if not line:
                    continue

                if "," in line:
                    parts = [p.strip() for p in line.split(",")]
                else:
                    parts = line.split()

                if len(parts) < 3:
                    print(
                        f"警告: {file_path}:{line_num} 行をスキップ (要素数不足): {line}",
                        file=sys.stderr,
                    )
                    continue

                addr = parse_value(parts[0])
                count = parse_value(parts[1])
                fmt = parts[2].strip()

                definitions.append([addr, count, fmt])

    except Exception as e:
        print(f"エラー: 設定ファイル ({file_path}) の読み込みに失敗しました: {e}", file=sys.stderr)
        sys.exit(1)

    if not definitions:
        print(f"エラー: 有効なフォント定義が見つかりませんでした: {file_path}", file=sys.stderr)
        sys.exit(1)

    return definitions


def load_config(file_path):
    """拡張子等に応じて JSON または CFG パーサーを振り分ける。"""
    if file_path.lower().endswith(".json"):
        return load_json_config(file_path)
    return load_cfg(file_path)


def decode_glyph(data, fmt):
    """文字バイナリを 0/1 のピクセルマトリックス (高さh, 幅w) に展開する。"""
    if fmt == "8x8":
        w, h = 8, 8
        pixels = [[(data[y] >> (7 - x)) & 1 for x in range(8)] for y in range(8)]
        return w, h, pixels

    elif fmt == "16x8":
        w, h = 16, 8
        pixels = []
        for y in range(8):
            b0, b1 = data[y * 2], data[y * 2 + 1]
            row = [(b0 >> (7 - x)) & 1 for x in range(8)] + [
                (b1 >> (7 - x)) & 1 for x in range(8)
            ]
            pixels.append(row)
        return w, h, pixels

    elif fmt == "8x8x2":
        w, h = 16, 8
        pixels = []
        for y in range(8):
            b0, b1 = data[y], data[8 + y]
            row = [(b0 >> (7 - x)) & 1 for x in range(8)] + [
                (b1 >> (7 - x)) & 1 for x in range(8)
            ]
            pixels.append(row)
        return w, h, pixels

    else:
        raise ValueError(f"未対応のビット形式です: {fmt}")


def get_char_byte_size(fmt):
    """ビット形式から1文字あたりのバイトサイズを取得する。"""
    if fmt == "8x8":
        return 8
    elif fmt in ("16x8", "8x8x2"):
        return 16
    else:
        raise ValueError(f"未対応のビット形式です: {fmt}")


def extract_fonts(rom_path, output_bmp_path, canvas_width, vscale, font_definitions, cfg_path=None):
    if not os.path.isfile(rom_path):
        print(f"エラー: ROMファイルが見つかりません: {rom_path}", file=sys.stderr)
        sys.exit(1)

    with open(rom_path, "rb") as f:
        rom_data = f.read()

    rom_size = len(rom_data)
    print(f"入力ROMファイル : {rom_path} ({rom_size:,} bytes)")
    if cfg_path:
        print(f"設定ファイル     : {cfg_path}")
    else:
        print("設定ファイル     : (組み込みデフォルト定義を使用)")
    print(f"設定画像横幅     : {canvas_width} px")
    print(f"縦拡大倍率       : {vscale}倍")
    print("-" * 55)

    canvas = []
    cur_x = 0
    cur_y = 0

    def ensure_height(target_h):
        while len(canvas) < target_h:
            canvas.append([0] * canvas_width)

    for idx, (start_addr, count, fmt) in enumerate(font_definitions, 1):
        char_bytes = get_char_byte_size(fmt)
        block_bytes = count * char_bytes
        end_addr = start_addr + block_bytes

        print(
            f"ブロック #{idx:02d}: 開始 0x{start_addr:05X} - 終了 0x{end_addr:05X} | "
            f"{count:4d}文字 | 形式: {fmt:<6s}"
        )

        if end_addr > rom_size:
            print(
                f"エラー: ROMサイズ不足です (必要: 0x{end_addr:X}, 実際: 0x{rom_size:X})",
                file=sys.stderr,
            )
            sys.exit(1)

        for c in range(count):
            offset = start_addr + c * char_bytes
            c_data = rom_data[offset : offset + char_bytes]
            char_w, char_h, glyph = decode_glyph(c_data, fmt)

            if cur_x + char_w > canvas_width:
                cur_x = 0
                cur_y += char_h

            ensure_height(cur_y + char_h)

            for gy in range(char_h):
                for gx in range(char_w):
                    canvas[cur_y + gy][cur_x + gx] = glyph[gy][gx]

            cur_x += char_w

    original_height = len(canvas)
    if original_height == 0:
        print("警告: 描画されたフォントデータがありません。", file=sys.stderr)
        return

    scaled_canvas = []
    for row in canvas:
        for _ in range(vscale):
            scaled_canvas.append(row)

    output_width = canvas_width
    output_height = len(scaled_canvas)

    row_bytes_unpadded = (output_width + 7) // 8
    row_stride = (output_width + 31) // 32 * 4
    padding_len = row_stride - row_bytes_unpadded
    image_data_size = row_stride * output_height

    file_header_size = 14
    info_header_size = 40
    palette_size = 2 * 4
    pixel_data_offset = file_header_size + info_header_size + palette_size
    total_file_size = pixel_data_offset + image_data_size

    bmp_file_header = struct.pack(
        "<2sIHHI", b"BM", total_file_size, 0, 0, pixel_data_offset
    )
    bmp_info_header = struct.pack(
        "<IiiHHIIiiII",
        info_header_size,
        output_width,
        output_height,
        1,
        1,
        0,
        image_data_size,
        0,
        0,
        2,
        0,
    )
    bmp_palette = struct.pack(
        "<BBBBBBBB",
        0, 0, 0, 0,
        255, 255, 255, 0,
    )

    pixel_data = bytearray()
    padding_bytes = b"\x00" * padding_len

    for row in reversed(scaled_canvas):
        line_bytes = bytearray(row_bytes_unpadded)
        for x in range(output_width):
            if row[x]:
                line_bytes[x // 8] |= 0x80 >> (x % 8)
        pixel_data.extend(line_bytes)
        pixel_data.extend(padding_bytes)

    with open(output_bmp_path, "wb") as f:
        f.write(bmp_file_header)
        f.write(bmp_info_header)
        f.write(bmp_palette)
        f.write(pixel_data)

    scale_text = "等倍" if vscale == 1 else f"縦{vscale}倍"

    print("-" * 55)
    print(f"出力ファイル     : {output_bmp_path}")
    print(f"形式             : 1bpp BMP (idx0: 黒, idx1: 白)")
    print(f"原寸サイズ       : {output_width} x {original_height}")
    print(f"出力画像サイズ   : {output_width} x {output_height} ({scale_text})")
    print(f"1行パディング    : {padding_len} bytes (Stride: {row_stride} bytes)")
    print(f"BMP総ファイル容量: {total_file_size:,} bytes")
    print("フォント抽出およびBMP生成が正常に完了しました。")


def main():
    parser = argparse.ArgumentParser(
        description="ROMファイルからフォントデータを抽出し、1bpp BMP画像を出力します。"
    )
    parser.add_argument("rom_file", help="入力ROMファイルパス")
    parser.add_argument("output_bmp", help="出力BMPファイルパス")
    parser.add_argument(
        "-c",
        "--config",
        dest="cfg_file",
        default=None,
        help="フォント定義ファイル (.cfg または .json)。省略時は組み込み設定を使用",
    )
    parser.add_argument(
        "-w",
        "--width",
        type=int,
        default=256,
        help="出力BMP画像の横幅ピクセル数 (デフォルト: 256)",
    )
    parser.add_argument(
        "-v",
        "--vscale",
        "--scale-y",
        dest="vscale",
        type=int,
        default=1,
        help="縦方向の拡大倍率 (整数、デフォルト: 1 (等倍))",
    )
    args = parser.parse_args()

    if args.width < 16:
        print("エラー: 横幅は16ピクセル以上を指定してください。", file=sys.stderr)
        sys.exit(1)

    if args.vscale < 1:
        print("エラー: 縦の拡大倍率は1以上の整数を指定してください。", file=sys.stderr)
        sys.exit(1)

    if args.cfg_file:
        font_definitions = load_config(args.cfg_file)
    else:
        font_definitions = DEFAULT_FONT_DEFINITIONS

    extract_fonts(
        args.rom_file,
        args.output_bmp,
        args.width,
        args.vscale,
        font_definitions,
        args.cfg_file,
    )


if __name__ == "__main__":
    main()

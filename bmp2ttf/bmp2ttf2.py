import argparse
import json
import re
import sys
from fractions import Fraction
from pathlib import Path
from typing import Iterable, List, Optional

# ライブラリのインポートチェック
try:
    from PIL import Image
except ImportError:
    print("エラー: 'Pillow' がインストールされていません。\n    pip install pillow\nを実行してください。", file=sys.stderr)
    sys.exit(1)

try:
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.transformPen import TransformPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
except ImportError:
    print("エラー: 'fonttools' がインストールされていません。\n    pip install fonttools\nを実行してください。", file=sys.stderr)
    sys.exit(1)

# ==============================================================================
# 定数定義
# ==============================================================================

DEFAULT_UNITS_PER_EM = 1024
PIXEL_BRIGHTNESS_THRESHOLD = 128
RGBA_ALPHA_INDEX = 3
RGBA_COLOR_COUNT = 4

DEFAULT_BASELINE_RATIO = "1/8"
DEFAULT_FONT_NAME = "MSX-Font"
DEFAULT_STYLE_NAME = "Regular"
DEFAULT_FONT_VERSION = "Version 1.0"
POST_IS_FIXED_PITCH_TRUE = 1
POST_IS_FIXED_PITCH_FALSE = 0
POST_TABLE_FORMAT = 2.0
OS2_PANOSE_PROPORTION_MONO = 9
OS2_PANOSE_PROPORTION_ANY = 0
OS2_CP932_BIT_OFFSET = 17

DEFAULT_CHAR_MAP_DEF = r"""; Normal chara map
; (Escape sequence'\'が有効)

+00	\u0000月火水木金土日年月日時分秒百千万
+10	π┴┬┤├┼│─┌┐└┘╳大中小
+20	 !\"#$%&'()*+,-./
+30	0123456789:;<=>?
+40	@ABCDEFGHIJKLMNO
+50	PQRSTUVWXYZ[\\]^_
+60	`abcdefghijklmno
+70	pqrstuvwxyz{|}~\u007F
+80	♠♥♣♦○●をぁぃぅぇぉゃゅょっ
+90	\u0090あいうえおかきくけこさしすせそ
+A0	\u00A0。「」、・ヲァィゥェォャュョッ
+B0	ーアイウエオカキクケコサシスセソ
+C0	タチツテトナニヌネノハヒフヘホマ
+D0	ミムメモヤユヨラリルレロワン゛゜
+E0	たちつてとなにぬねのはひふへほま
+F0	みむめもやゆよらリルレろわん\u00FE\u00FF
"""


# ==============================================================================
# 文字マップ定義 (.def) パーサー
# ==============================================================================

def parse_char_map(lines: Iterable[str]) -> List[Optional[str]]:
    """行イテレータから文字マップ配列を生成"""
    char_dict = {}

    for line in lines:
        line = line.rstrip("\r\n")

        if not line or line.startswith(";"):
            continue

        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue

        offset_str, text_raw = parts

        try:
            base_offset = int(offset_str.lstrip("+"), 16)
        except ValueError:
            continue

        decoded_text = text_raw.encode("raw_unicode_escape").decode("unicode_escape")

        for i, char in enumerate(decoded_text):
            char_dict[base_offset + i] = char

    if not char_dict:
        return []

    max_index = max(char_dict.keys())
    char_map: List[Optional[str]] = [None] * (max_index + 1)

    for idx, char in char_dict.items():
        char_map[idx] = char

    return char_map


# ==============================================================================
# ユーティリティ
# ==============================================================================

def load_json_relaxed(text: str, filepath: str = "") -> dict:
    """リストやオブジェクト末尾の余計なカンマを許容してJSONを読み込む"""
    pattern = re.compile(r'("(?:\\.|[^"\\])*")|(,)(\s*[}\]])', re.DOTALL)
    cleaned = pattern.sub(lambda m: m.group(1) if m.group(1) else m.group(3), text)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        target = f" ({filepath})" if filepath else ""
        print(f"エラー: JSONの解析に失敗しました{target}:", file=sys.stderr)
        print(f"  行 {e.lineno}, 列 {e.colno}: {e.msg}", file=sys.stderr)
        lines = text.splitlines()
        if 0 <= e.lineno - 1 < len(lines):
            err_line = lines[e.lineno - 1]
            print(f"  {e.lineno:4d} | {err_line}", file=sys.stderr)
            pointer_indent = " " * (e.colno - 1)
            print(f"       | {pointer_indent}^", file=sys.stderr)
        sys.exit(1)


def parse_code_point(val) -> int:
    """16進数文字列 (0xE000, E000, U+E000) または数値を int に変換"""
    if isinstance(val, int):
        return val
    s = str(val).strip().upper()
    if s.startswith("U+"):
        s = s[2:]
    return int(s, 16) if (s.startswith("0X") or not s.isdigit()) else int(s)


def parse_ratio(val: str | float | None) -> float:
    """割り算 ('1/8') や小数 ('0.125') を float に変換 (None や空文字は 0.0)"""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    val = str(val).strip()
    if not val:
        return 0.0
    if "/" in val:
        frac = Fraction(val)
        return float(frac)
    return float(val)


def _parse_dimension_pair(dim_str: str) -> tuple[int, int]:
    """'8x8' や '8,8' を (8, 8) に変換"""
    parts = re.split(r"[x,]", dim_str.strip().lower())
    if len(parts) != 2:
        raise ValueError(f"サイズ指定が不正です: '{dim_str}' ('8x8' または '8,8' 形式で指定してください)")
    return int(parts[0]), int(parts[1])


def parse_set_arg(arg_str: str) -> dict:
    """CLI引数のセット定義文字列をパース"""
    parts = arg_str.split(":")
    if len(parts) != 4:
        raise ValueError("セットの指定形式は '画像パス:x1,y1,x2,y2:セル間隔[/有効サイズ]:開始コードポイント' です。")

    img_path = parts[0]
    bbox_str = parts[1].strip()
    cell_str = parts[2].strip()
    cp_str = parts[3].strip()

    bbox = [int(v) for v in bbox_str.split(",")] if bbox_str else None

    if "/" in cell_str:
        step_str, glyph_str = cell_str.split("/", 1)
        step_size = _parse_dimension_pair(step_str)
        glyph_size = _parse_dimension_pair(glyph_str)
    else:
        step_size = _parse_dimension_pair(cell_str)
        glyph_size = step_size

    start_cp = parse_code_point(cp_str)

    return {
        "image": img_path,
        "bbox": bbox,
        "step_size": step_size,
        "glyph_size": glyph_size,
        "start_cp": start_cp
    }


def format_char_literal(char: str) -> str:
    """文字をJSON/C++互換のエスケープ文字列に整形"""
    if char == '"':
        return r'\"'
    if char == '\\':
        return r'\\'
    cp = ord(char)
    # 制御文字や不可視文字はUnicodeエスケープ
    if cp < 0x20 or (0x7F <= cp <= 0x9F):
        return f"\\u{cp:04X}"
    return char


# ==============================================================================
# グリフ生成処理
# ==============================================================================

def extract_horizontal_segments(pixels, char_x: int, char_y: int, w: int, h: int):
    segments = []
    for y in range(h):
        segment_start = None
        for x in range(w):
            p = pixels[char_x + x, char_y + y]
            if isinstance(p, tuple):
                is_visible = len(p) < RGBA_COLOR_COUNT or p[RGBA_ALPHA_INDEX] > 0
                is_on = (p[0] >= PIXEL_BRIGHTNESS_THRESHOLD) and is_visible
            else:
                is_on = p >= PIXEL_BRIGHTNESS_THRESHOLD

            if is_on:
                if segment_start is None:
                    segment_start = x
            else:
                if segment_start is not None:
                    segments.append((segment_start, x, y))
                    segment_start = None

        if segment_start is not None:
            segments.append((segment_start, w, y))

    return segments


def create_glyph_from_segments(segments, glyph_h: int, dot_scale: float, baseline_dots: int, shift_x: int = 0):
    pen = TTGlyphPen(None)
    if not segments:
        return pen.glyph(), 0

    min_x0 = None
    for x_start, x_end, y in segments:
        dot_y = (glyph_h - 1 - y) - baseline_dots
        y0 = round(dot_y * dot_scale)
        y1 = round((dot_y + 1) * dot_scale)
        x0 = round((x_start - shift_x) * dot_scale)
        x1 = round((x_end - shift_x) * dot_scale)

        if min_x0 is None or x0 < min_x0:
            min_x0 = x0

        pen.moveTo((x0, y0))
        pen.lineTo((x0, y1))
        pen.lineTo((x1, y1))
        pen.lineTo((x1, y0))
        pen.closePath()

    return pen.glyph(), (min_x0 if min_x0 is not None else 0)


# ==============================================================================
# フォント構築
# ==============================================================================

def build_font(
    sets_config: list[dict],
    output_path: str,
    units_per_em: int = DEFAULT_UNITS_PER_EM,
    font_name: str = DEFAULT_FONT_NAME,
    baseline_ratio_val: str | float = DEFAULT_BASELINE_RATIO,
    margin_top_val: str | float = 0.0,
    margin_bottom_val: str | float = 0.0,
    scale_copy: bool = False,
    scale_copy_src: int = 0xE000,
    scale_copy_dst: int = 0xE100,
    scale_copy_count: int = 256,
    enable_charmap: bool = False,
    charmap_file: str | None = None,
    charmap_source: int = 0xE100,
    proportional: bool = False,
    char_spacing: int = 1,
    space_width: Optional[int] = None,
):
    if not (16 <= units_per_em <= 16384):
        raise ValueError(f"unitsPerEm ({units_per_em}) は 16 から 16384 の範囲で指定してください。")

    baseline_ratio = parse_ratio(baseline_ratio_val)
    margin_top_ratio = parse_ratio(margin_top_val)
    margin_bottom_ratio = parse_ratio(margin_bottom_val)

    # units_per_em に基づくアセンダ／ディセンダの計算
    ascent = round(units_per_em * (1.0 - baseline_ratio + margin_top_ratio))
    descent = -round(units_per_em * (baseline_ratio + margin_bottom_ratio))
    
    x_height_units = round(units_per_em * (4.0 / 8.0))
    cap_height_units = round(units_per_em * (6.0 / 8.0))

    glyphs = {".notdef": TTGlyphPen(None).glyph()}
    metrics = {".notdef": (units_per_em // 2, 0)}
    cmap = {}
    glyph_order = [".notdef"]

    image_cache = {}

    # 全セット中の最小有効幅を算出（未指定時の空白送り幅として使用）
    all_glyph_widths = []
    for s in sets_config:
        step_sz = s.get("step_size") or s.get("cell_size")
        glyph_sz = s.get("glyph_size") or step_sz
        if glyph_sz:
            all_glyph_widths.append(glyph_sz[0])

    min_glyph_w = min(all_glyph_widths) if all_glyph_widths else 8
    resolved_space_width = space_width if space_width is not None else min_glyph_w

    print(f"フォント設定:")
    print(f" - unitsPerEm (EM値): {units_per_em}")
    print(f" - モード: {'プロポーショナル' if proportional else '等幅'}")
    if proportional:
        print(f"   - 字間スペース: {char_spacing} ドット")
        print(f"   - 空白文字幅: {resolved_space_width} ドット (指定なし時: 最小有効幅 {min_glyph_w})")
    print(f" - ベースライン比率: {baseline_ratio}")
    print(f" - 上余白比率: {margin_top_ratio}, 下余白比率: {margin_bottom_ratio}")
    print(f" - Ascent: {ascent}, Descent: {descent} (総行高: {ascent - descent})")

    # プロポーショナル用メタデータ記録リスト
    proportional_records = []
    global_index = 0

    # 各画像セットの読み込みとグリフ化
    for idx, s in enumerate(sets_config):
        img_path = s["image"]
        if img_path not in image_cache:
            if not Path(img_path).exists():
                raise FileNotFoundError(f"画像ファイルが見つかりません: {img_path}")
            image_cache[img_path] = Image.open(img_path).convert("RGBA")
        img = image_cache[img_path]

        step_size = s.get("step_size") or s.get("cell_size")
        glyph_size = s.get("glyph_size") or step_size

        if not step_size or not glyph_size:
            raise ValueError(f"セット #{idx+1} にサイズ定義（step_size / cell_size）がありません。")

        step_w, step_h = step_size
        glyph_w, glyph_h = glyph_size
        pad_x = step_w - glyph_w
        pad_y = step_h - glyph_h
        start_cp = parse_code_point(s["start_cp"])

        bbox = s.get("bbox")
        if bbox:
            x1, y1, x2, y2 = bbox
        else:
            x1, y1, x2, y2 = 0, 0, img.width, img.height

        region_w = x2 - x1
        region_h = y2 - y1
        cols = region_w // step_w
        rows = region_h // step_h

        dot_scale = units_per_em / glyph_h
        cell_baseline_dots = round(glyph_h * baseline_ratio)

        pixels = img.load()
        count = cols * rows

        for i in range(count):
            c = i % cols
            r = i // cols
            cx = x1 + c * step_w
            cy = y1 + r * step_h

            cp = start_cp + i
            gname = f"uni{cp:04X}"

            segments = extract_horizontal_segments(pixels, cx, cy, glyph_w, glyph_h)

            if segments:
                min_x = min(seg[0] for seg in segments)
                max_x = max(seg[1] for seg in segments)
                char_w = max_x - min_x
                offset_x = min_x
            else:
                offset_x = 0
                char_w = 0

            # グリフの生成とメトリクスの決定
            if proportional:
                if char_w > 0:
                    # ピクセルの最小Xを原点(X=0)へシフトして配置
                    glyph, lsb = create_glyph_from_segments(segments, glyph_h, dot_scale, cell_baseline_dots, shift_x=offset_x)
                    adv_w = round((char_w + char_spacing) * dot_scale)
                else:
                    # 空白（ドットなし）文字
                    glyph = TTGlyphPen(None).glyph()
                    lsb = 0
                    adv_w = round(resolved_space_width * dot_scale)
            else:
                # 等幅
                glyph, lsb = create_glyph_from_segments(segments, glyph_h, dot_scale, cell_baseline_dots)
                adv_w = round(glyph_w * dot_scale)

            glyphs[gname] = glyph
            metrics[gname] = (adv_w, lsb)
            cmap[cp] = gname
            if gname not in glyph_order:
                glyph_order.append(gname)

            # プロポーショナル用レコード（実際の切り出しオフセットと実サイズ）
            try:
                char_str = chr(cp)
            except (ValueError, OverflowError):
                char_str = "?"
            proportional_records.append({
                "index": global_index,
                "cell": [cx, cy, pad_x, pad_y],
                "offset_x": offset_x,
                "width": char_w,
                "char": char_str,
            })
            global_index += 1

        size_info = f"間隔: {step_w}x{step_h}"
        if (step_w, step_h) != (glyph_w, glyph_h):
            size_info += f", 有効: {glyph_w}x{glyph_h}"
        print(f"セット #{idx+1}: '{img_path}' ({cols}x{rows}={count}文字, {size_info}) 開始: U+{start_cp:04X}")

    # 半角スケーリングコピー (X軸50%縮小)
    if scale_copy:
        glyph_set = glyphs
        copied_count = 0
        for i in range(scale_copy_count):
            s_cp = scale_copy_src + i
            d_cp = scale_copy_dst + i
            s_gname = f"uni{s_cp:04X}"
            d_gname = f"uni{d_cp:04X}"

            if s_gname not in glyphs:
                continue

            src_glyph = glyphs[s_gname]
            orig_adv, src_lsb = metrics[s_gname]

            tt_pen = TTGlyphPen(glyph_set)
            trans_pen = TransformPen(tt_pen, (0.5, 0, 0, 1.0, 0, 0))
            src_glyph.draw(trans_pen, glyph_set)

            glyphs[d_gname] = tt_pen.glyph()
            metrics[d_gname] = (orig_adv // 2, round(src_lsb * 0.5))
            cmap[d_cp] = d_gname
            if d_gname not in glyph_order:
                glyph_order.append(d_gname)
            copied_count += 1
        print(f"半角スケーリングコピー: U+{scale_copy_src:04X} -> U+{scale_copy_dst:04X} ({copied_count} 文字)")

    # 文字マップ (.def) マッピング
    if enable_charmap:
        if charmap_file:
            cpath = Path(charmap_file)
            if not cpath.exists():
                raise FileNotFoundError(f"文字マップ定義ファイルが見つかりません: {charmap_file}")
            with open(cpath, "r", encoding="utf-8") as f:
                char_map = parse_char_map(f)
            source_label = f"'{charmap_file}'"
        else:
            char_map = parse_char_map(DEFAULT_CHAR_MAP_DEF.splitlines())
            source_label = "デフォルト定義"

        mapped_count = 0
        for i, char in enumerate(char_map):
            if char is None:
                continue
            src_cp = charmap_source + i
            src_gname = f"uni{src_cp:04X}"
            if src_gname not in glyphs:
                continue

            dst_cp = ord(char)
            cmap[dst_cp] = src_gname
            mapped_count += 1
        print(f"文字マップマッピング: {source_label} (参照元 U+{charmap_source:04X}) から {mapped_count} 文字をUnicodeへマッピング")

    # OpenTypeテーブル構築
    fb = FontBuilder(units_per_em, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ascent, descent=descent)

    name_strings = {
        "familyName": font_name,
        "styleName": DEFAULT_STYLE_NAME,
        "uniqueFontIdentifier": f"{font_name}:{DEFAULT_STYLE_NAME}",
        "fullName": font_name,
        "psName": font_name.replace(" ", ""),
        "version": DEFAULT_FONT_VERSION,
    }
    fb.setupNameTable(name_strings)

    fb.setupOS2(
        sTypoAscender=ascent,
        sTypoDescender=descent,
        sTypoLineGap=0,
        usWinAscent=ascent,
        usWinDescent=-descent,
        sxHeight=x_height_units,
        sCapHeight=cap_height_units,
    )
    fb.setupPost(formatType=POST_TABLE_FORMAT)

    font = fb.font
    # プロポーショナルと等幅でテーブルフラグを切り替え
    if proportional:
        font["OS/2"].xAvgCharWidth = round(units_per_em * (min_glyph_w / 8.0))
        font["OS/2"].panose.bProportion = OS2_PANOSE_PROPORTION_ANY
        font["post"].isFixedPitch = POST_IS_FIXED_PITCH_FALSE
    else:
        font["OS/2"].xAvgCharWidth = units_per_em // 2
        font["OS/2"].panose.bProportion = OS2_PANOSE_PROPORTION_MONO
        font["post"].isFixedPitch = POST_IS_FIXED_PITCH_TRUE

    font["OS/2"].ulCodePageRange1 = 1 << OS2_CP932_BIT_OFFSET
    font["OS/2"].ulCodePageRange2 = 0

    font.save(output_path)
    print(f"\n生成完了: '{output_path}' (総登録グリフ数: {len(glyph_order)})")

    # プロポーショナル指定時: _proportional.txt を出力
    if proportional:
        out_p = Path(output_path)
        txt_path = out_p.with_name(f"{out_p.stem}_proportional.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("// index, [cell_x, cell_y, pad_x, pad_y], offset_x, width, \"char\"\n")
            total = len(proportional_records)
            for i, rec in enumerate(proportional_records):
                comma = "," if i < total - 1 else ""
                escaped_ch = format_char_literal(rec["char"])
                cx, cy, px, py = rec["cell"]
                f.write(
                    f"[{rec['index']:4d}, [{cx:4d}, {cy:4d}, {px:2d}, {py:2d}], "
                    f"{rec['offset_x']:2d}, {rec['width']:2d}, \"{escaped_ch}\"]{comma}\n"
                )
        print(f"メトリクス書き出し完了: '{txt_path}' ({total} 文字分)")


# ==============================================================================
# エントリーポイント
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="複数画像・領域・混在セルサイズから等幅／プロポーショナル TrueType フォント (.ttf) を生成します。"
    )
    parser.add_argument("-o", "--output", default=None, help="出力TTFファイル名 (省略時は設定ファイル名 / 画像名 / フォント名から自動決定)")
    parser.add_argument("-n", "--name", default=DEFAULT_FONT_NAME, help=f"フォント名 (デフォルト: {DEFAULT_FONT_NAME})")
    parser.add_argument(
        "--em", "--units-per-em",
        dest="units_per_em",
        type=int,
        default=DEFAULT_UNITS_PER_EM,
        help=f"EM値 (unitsPerEm)。16～16384の整数 (デフォルト: {DEFAULT_UNITS_PER_EM})"
    )
    parser.add_argument(
        "-b", "--baseline",
        default=DEFAULT_BASELINE_RATIO,
        help=f"ベースライン比率 (割り算 '1/8' や小数。デフォルト: {DEFAULT_BASELINE_RATIO})"
    )

    # 上下余白
    parser.add_argument("-mt", "--margin-top", default=None, help="上余白比率 (例: '1/8', '0.125')")
    parser.add_argument("-mb", "--margin-bottom", default=None, help="下余白比率 (例: '1/8', '0.125')")
    parser.add_argument("-m", "--margin", default=None, help="上下共通の余白比率 (例: '1/8')")

    # 複数セット指定オプション
    parser.add_argument(
        "-s", "--set",
        action="append",
        dest="sets",
        help="画像セットの指定: '画像パス:x1,y1,x2,y2:間隔幅,高[/有効幅,高]:開始コードポイント' (例: 'font.bmp:0,0,128,64:8,8/4,8:0x0020')"
    )
    parser.add_argument("-c", "--config", help="設定ファイル (JSON形式) のパス")

    # プロポーショナルフォント設定
    parser.add_argument(
        "-p", "--proportional",
        action="store_true",
        help="プロポーショナルフォントとして生成し、メタデータ (出力名_proportional.txt) を出力する"
    )
    parser.add_argument(
        "--char-spacing",
        type=int,
        default=1,
        help="字間スペース (ドット数)。デフォルト: 1 (※ --proportional 指定時のみ有効)"
    )
    parser.add_argument(
        "--space-width",
        type=int,
        default=None,
        help="空白文字 (ドットなし) の送り幅 (ドット数)。指定なし時はセル切り出し設定の最小幅 (※ --proportional 指定時のみ有効)"
    )

    # 半角スケーリングコピー設定
    parser.add_argument("--scale-copy", action="store_true", help="横50%%縮小コピーグリフを生成する")
    parser.add_argument("--scale-copy-src", default="0xE000", help="縮小コピー元開始コードポイント (デフォルト: 0xE000)")
    parser.add_argument("--scale-copy-dst", default="0xE100", help="縮小コピー先開始コードポイント (デフォルト: 0xE100)")
    parser.add_argument("--scale-copy-count", type=int, default=256, help="縮小コピーする文字数 (デフォルト: 256)")

    # 文字マップ定義マッピング設定
    parser.add_argument("--enable-charmap", action="store_true", help="文字マップ定義に基づくUnicodeへのマッピングを有効化")
    parser.add_argument("-cm", "--charmap-file", default=None, help="文字マップ定義ファイル (.def) のパス (省略時はデフォルト定義)")
    parser.add_argument("--charmap-source", default="0xE100", help="文字マップが参照するグリフの開始コードポイント (デフォルト: 0xE100)")

    args = parser.parse_args()

    sets_config = []
    units_per_em = args.units_per_em
    baseline_val = args.baseline
    margin_top_val = args.margin_top if args.margin_top is not None else args.margin
    margin_bottom_val = args.margin_bottom if args.margin_bottom is not None else args.margin
    font_name = args.name
    proportional = args.proportional
    char_spacing = args.char_spacing
    space_width = args.space_width

    scale_copy = args.scale_copy
    scale_copy_src = args.scale_copy_src
    scale_copy_dst = args.scale_copy_dst
    scale_copy_count = args.scale_copy_count

    enable_charmap = args.enable_charmap
    charmap_file = args.charmap_file
    charmap_source = args.charmap_source

    # JSON設定ファイルの読み込みと上書き
    if args.config:
        cfg_path = Path(args.config)
        if not cfg_path.exists():
            print(f"エラー: 設定ファイルが見つかりません: {cfg_path}", file=sys.stderr)
            sys.exit(1)
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = load_json_relaxed(f.read(), str(cfg_path))

        if "sets" in cfg:
            sets_config.extend(cfg["sets"])
        if "name" in cfg:
            font_name = cfg["name"]
        if "em" in cfg:
            units_per_em = int(cfg["em"])
        elif "units_per_em" in cfg:
            units_per_em = int(cfg["units_per_em"])
        if "baseline" in cfg:
            baseline_val = cfg["baseline"]
        if "margin" in cfg:
            if margin_top_val is None:
                margin_top_val = cfg["margin"]
            if margin_bottom_val is None:
                margin_bottom_val = cfg["margin"]
        if "margin_top" in cfg and args.margin_top is None:
            margin_top_val = cfg["margin_top"]
        if "margin_bottom" in cfg and args.margin_bottom is None:
            margin_bottom_val = cfg["margin_bottom"]
        if "proportional" in cfg and not args.proportional:
            proportional = bool(cfg["proportional"])
        if "char_spacing" in cfg and args.char_spacing == 1:
            char_spacing = int(cfg["char_spacing"])
        if "space_width" in cfg and args.space_width is None:
            space_width = int(cfg["space_width"])
        if "scale_copy" in cfg:
            scale_copy = cfg["scale_copy"]
        if "scale_copy_src" in cfg:
            scale_copy_src = cfg["scale_copy_src"]
        if "scale_copy_dst" in cfg:
            scale_copy_dst = cfg["scale_copy_dst"]
        if "scale_copy_count" in cfg:
            scale_copy_count = cfg["scale_copy_count"]
        if "enable_charmap" in cfg:
            enable_charmap = cfg["enable_charmap"]
        if "charmap_file" in cfg and args.charmap_file is None:
            charmap_file = cfg["charmap_file"]
        if "charmap_source" in cfg:
            charmap_source = cfg["charmap_source"]

    margin_top_val = margin_top_val if margin_top_val is not None else 0.0
    margin_bottom_val = margin_bottom_val if margin_bottom_val is not None else 0.0

    # CLIの --set からの読み込み
    if args.sets:
        for s_str in args.sets:
            try:
                sets_config.append(parse_set_arg(s_str))
            except Exception as e:
                print(f"エラー: --set 引数の形式が不正です: {s_str}\n  {e}", file=sys.stderr)
                sys.exit(1)

    if not sets_config:
        print("エラー: 取り込む画像セットが指定されていません。--set または --config を指定してください。", file=sys.stderr)
        sys.exit(1)

    # 出力ファイル名の決定 (-o未指定時)
    output_path = args.output
    if not output_path:
        if args.config:
            output_path = f"{Path(args.config).stem}.ttf"
        else:
            unique_images = list(dict.fromkeys(s["image"] for s in sets_config if "image" in s))
            if len(unique_images) == 1:
                output_path = f"{Path(unique_images[0]).stem}.ttf"
            else:
                output_path = f"{font_name}.ttf"

    try:
        build_font(
            sets_config=sets_config,
            output_path=output_path,
            units_per_em=units_per_em,
            font_name=font_name,
            baseline_ratio_val=baseline_val,
            margin_top_val=margin_top_val,
            margin_bottom_val=margin_bottom_val,
            scale_copy=scale_copy,
            scale_copy_src=parse_code_point(scale_copy_src),
            scale_copy_dst=parse_code_point(scale_copy_dst),
            scale_copy_count=scale_copy_count,
            enable_charmap=enable_charmap,
            charmap_file=charmap_file,
            charmap_source=parse_code_point(charmap_source),
            proportional=proportional,
            char_spacing=char_spacing,
            space_width=space_width,
        )
    except Exception as e:
        print(f"エラー: フォント生成に失敗しました: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

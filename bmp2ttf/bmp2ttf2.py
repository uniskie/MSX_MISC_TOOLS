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
DEFAULT_STYLE_NAME = "Regular"
DEFAULT_FONT_VERSION = "Version 1.0"
POST_IS_FIXED_PITCH_TRUE = 1
POST_IS_FIXED_PITCH_FALSE = 0
POST_TABLE_FORMAT = 2.0
OS2_PANOSE_PROPORTION_MONO = 9
OS2_PANOSE_PROPORTION_ANY = 0
OS2_CP932_BIT_OFFSET = 17


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


def parse_ratio_or_dots(val: str | float | int | None, base_cell_h: int = 8) -> float:
    """
    末尾に '%' があればパーセント比率、'/' があれば分数比率、
    それ以外（単なる数値）はすべてドット数として比率に換算する。
    """
    if val is None:
        return 0.0

    s = str(val).strip()
    if not s:
        return 0.0

    # パーセント比率 (例: '12.5%', '25%')
    if s.endswith("%"):
        try:
            return float(s[:-1].strip()) / 100.0
        except ValueError:
            raise ValueError(f"パーセント指定が不正です: '{val}'")

    # 分数比率 (例: '1/8')
    if "/" in s:
        try:
            return float(Fraction(s))
        except ValueError:
            raise ValueError(f"分数比率の指定が不正です: '{val}'")

    # それ以外は整数・小数を問わずすべてドット数 (例: '1', '1.5', '0.5')
    try:
        dots = float(s)
        return dots / base_cell_h
    except ValueError:
        raise ValueError(f"値の指定が不正です: '{val}' (数値、'1/8'、または '12.5%' 形式で指定してください)")


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


def parse_scale_copy_arg(val) -> tuple[int, int, int]:
    """スケールコピー定義 (コピー元,コピー先,文字数) をパース"""
    if isinstance(val, (list, tuple)):
        if len(val) != 3:
            raise ValueError(f"スケールコピーの指定要素数が不正です: {val} (3つの値が必要です)")
        return parse_code_point(val[0]), parse_code_point(val[1]), int(val[2])
    if isinstance(val, dict):
        return parse_code_point(val["src"]), parse_code_point(val["dst"]), int(val["count"])

    parts = str(val).split(",")
    if len(parts) != 3:
        raise ValueError(f"スケールコピーの指定形式は 'コピー元,コピー先,文字数' (カンマ区切り) です: '{val}'")
    return parse_code_point(parts[0].strip()), parse_code_point(parts[1].strip()), int(parts[2].strip())


def parse_charmap_arg(val) -> tuple[str, Optional[int]]:
    """文字マップ定義 (定義ファイル[,参照元コードポイント]) をパース"""
    if isinstance(val, (list, tuple)):
        file_path = str(val[0])
        src_cp = parse_code_point(val[1]) if len(val) > 1 and val[1] is not None else None
        return file_path, src_cp
    if isinstance(val, dict):
        file_path = str(val["file"])
        src_cp = parse_code_point(val["source"]) if "source" in val and val["source"] is not None else None
        return file_path, src_cp

    parts = str(val).split(",", 1)
    file_path = parts[0].strip()
    src_cp = parse_code_point(parts[1].strip()) if len(parts) > 1 and parts[1].strip() else None
    return file_path, src_cp


def validate_bbox(bbox: list[int] | None, img_w: int, img_h: int, step_w: int, step_h: int, set_label: str) -> tuple[int, int, int, int]:
    """BBOX の妥当性を検証し、(x1, y1, x2, y2) を返す。不正時は詳細エラーを表示して中断"""
    if bbox is None:
        return 0, 0, img_w, img_h

    if len(bbox) != 4:
        print(f"エラー: BBOX の指定要素数が不正です: {bbox} (4つの数値 [x1, y1, x2, y2] が必要です)", file=sys.stderr)
        sys.exit(1)

    x1, y1, x2, y2 = bbox
    width = x2 - x1
    height = y2 - y1

    # 終点座標が始点座標以下の場合
    if width <= 0 or height <= 0:
        print(f"エラー: BBOX の終点座標が始点座標以下になっています。", file=sys.stderr)
        print(f"  対象: {set_label}", file=sys.stderr)
        print(f"  指定 BBOX : x1={x1}, y1={y1}, x2={x2}, y2={y2}", file=sys.stderr)
        print(f"  問題箇所:", file=sys.stderr)
        if width <= 0:
            print(f"    - 幅  : x2({x2}) - x1({x1}) = {width} px (幅が 0 以下です)", file=sys.stderr)
        if height <= 0:
            print(f"    - 高さ: y2({y2}) - y1({y1}) = {height} px (高さが 0 以下です)", file=sys.stderr)

        # 幅・高さ形式との混同を検知してサジェスト
        if x2 > 0 and y2 > 0:
            suggest_x2 = x1 + x2
            suggest_y2 = y1 + y2
            print(f"\n  ヒント: BBOX の形式は [x1, y1, x2, y2] (左上X, 左上Y, 右下X, 右下Y) です。", file=sys.stderr)
            print(f"          [X, Y, 幅, 高さ] 形式と混同していませんか？", file=sys.stderr)
            print(f"          幅 {x2} px, 高さ {y2} px を指定したい場合は [{x1}, {y1}, {suggest_x2}, {suggest_y2}] と指定してください。", file=sys.stderr)
        sys.exit(1)

    # 画像範囲外の検証
    out_of_bounds = []
    if x1 < 0:
        out_of_bounds.append(f"x1 ({x1}) に負の値が指定されています。")
    if y1 < 0:
        out_of_bounds.append(f"y1 ({y1}) に負の値が指定されています。")
    if x1 >= img_w:
        out_of_bounds.append(f"x1 ({x1}) が画像の幅 ({img_w}) 以上です。")
    if y1 >= img_h:
        out_of_bounds.append(f"y1 ({y1}) が画像の高さ ({img_h}) 以上です。")
    if x2 > img_w:
        out_of_bounds.append(f"x2 ({x2}) が画像の幅 ({img_w}) を {x2 - img_w} px 超過しています。")
    if y2 > img_h:
        out_of_bounds.append(f"y2 ({y2}) が画像の高さ ({img_h}) を {y2 - img_h} px 超過しています。")

    if out_of_bounds:
        print(f"エラー: BBOX (切り出し範囲) が画像サイズを超過しています。", file=sys.stderr)
        print(f"  対象: {set_label}", file=sys.stderr)
        print(f"  画像サイズ : 幅 {img_w} px × 高さ {img_h} px (有効範囲: 0, 0 〜 {img_w}, {img_h})", file=sys.stderr)
        print(f"  指定 BBOX  : [{x1}, {y1}, {x2}, {y2}]", file=sys.stderr)
        print(f"  問題箇所:", file=sys.stderr)
        for msg in out_of_bounds:
            print(f"    - {msg}", file=sys.stderr)
        sys.exit(1)

    # 領域サイズがセルサイズより小さく 0 セルになる場合
    if width < step_w or height < step_h:
        print(f"エラー: BBOX 領域サイズがセルサイズより小さいため、文字を切り出せません。", file=sys.stderr)
        print(f"  対象: {set_label}", file=sys.stderr)
        print(f"  指定 BBOX  : [{x1}, {y1}, {x2}, {y2}] (領域: 幅 {width} px × 高さ {height} px)", file=sys.stderr)
        print(f"  セル間隔   : 幅 {step_w} px × 高さ {step_h} px", file=sys.stderr)
        print(f"  問題箇所:", file=sys.stderr)
        if width < step_w:
            print(f"    - 領域の幅 ({width} px) がセル間隔 ({step_w} px) 未満です。", file=sys.stderr)
        if height < step_h:
            print(f"    - 領域の高さ ({height} px) がセル間隔 ({step_h} px) 未満です。", file=sys.stderr)
        sys.exit(1)

    return x1, y1, x2, y2


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
    font_name: str = "Font",
    family_name: str = "Font",
    baseline_ratio_val: str | float = DEFAULT_BASELINE_RATIO,
    margin_top_val: str | float = 0.0,
    margin_bottom_val: str | float = 0.0,
    scale_copy_params: Optional[tuple[int, int, int]] = None,
    charmap_params: Optional[tuple[str, Optional[int]]] = None,
    proportional: bool = False,
    char_spacing: int = 1,
    space_width: Optional[int] = None,
):
    if not (16 <= units_per_em <= 16384):
        raise ValueError(f"unitsPerEm ({units_per_em}) は 16 から 16384 の範囲で指定してください。")

    # 全セット中の最小有効幅および基準セル高さを算出
    all_glyph_widths = []
    base_h = 8
    if sets_config:
        s0 = sets_config[0]
        step_sz = s0.get("step_size") or s0.get("cell_size")
        glyph_sz = s0.get("glyph_size") or step_sz
        if glyph_sz:
            base_h = glyph_sz[1]

    for s in sets_config:
        step_sz = s.get("step_size") or s.get("cell_size")
        glyph_sz = s.get("glyph_size") or step_sz
        if glyph_sz:
            all_glyph_widths.append(glyph_sz[0])

    baseline_ratio = parse_ratio_or_dots(baseline_ratio_val, base_h)
    margin_top_ratio = parse_ratio_or_dots(margin_top_val, base_h)
    margin_bottom_ratio = parse_ratio_or_dots(margin_bottom_val, base_h)

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

    min_glyph_w = min(all_glyph_widths) if all_glyph_widths else 8
    resolved_space_width = space_width if space_width is not None else min_glyph_w

    print(f"フォント設定:")
    print(f" - unitsPerEm (EM値): {units_per_em}")
    print(f" - フォント名: {font_name} (ファミリー名: {family_name})")
    print(f" - モード: {'プロポーショナル' if proportional else '等幅'}")
    if proportional:
        print(f"   - 字間スペース: {char_spacing} ドット")
        print(f"   - 空白文字幅: {resolved_space_width} ドット (指定なし時: 最小有効幅 {min_glyph_w})")
    print(f" - ベースライン比率: {baseline_ratio:.4f}")
    print(f" - 上余白比率: {margin_top_ratio:.4f}, 下余白比率: {margin_bottom_ratio:.4f}")
    print(f" - Ascent: {ascent}, Descent: {descent} (総行高: {ascent - descent})")

    # プロポーショナル用メタデータ記録リスト
    proportional_records = []
    global_index = 0

    # 各画像セットの読み込みとグリフ化
    for idx, s in enumerate(sets_config):
        img_path = s["image"]
        set_label = f"セット #{idx+1} ('{img_path}')"
        if img_path not in image_cache:
            if not Path(img_path).exists():
                raise FileNotFoundError(f"画像ファイルが見つかりません: {img_path}")
            image_cache[img_path] = Image.open(img_path).convert("RGBA")
        img = image_cache[img_path]

        step_size = s.get("step_size") or s.get("cell_size")
        glyph_size = s.get("glyph_size") or step_size

        if not step_size or not glyph_size:
            raise ValueError(f"{set_label} にサイズ定義（step_size / cell_size）がありません。")

        step_w, step_h = step_size
        glyph_w, glyph_h = glyph_size
        pad_x = step_w - glyph_w
        pad_y = step_h - glyph_h
        start_cp = parse_code_point(s["start_cp"])

        # BBOX の検証
        x1, y1, x2, y2 = validate_bbox(s.get("bbox"), img.width, img.height, step_w, step_h, set_label)

        region_w = x2 - x1
        region_h = y2 - y1

        # 切り出し領域とセル間隔の端数（余剰ピクセル）警告
        rem_x = region_w % step_w
        rem_y = region_h % step_h
        if rem_x != 0 or rem_y != 0:
            reasons = []
            if rem_x != 0:
                reasons.append(f"右端 {rem_x} px")
            if rem_y != 0:
                reasons.append(f"下端 {rem_y} px")
            print(f"警告: {set_label}: 切り出し領域 ({region_w}x{region_h}) がセル間隔 ({step_w}x{step_h}) で割り切れません。", file=sys.stderr)
            print(f"      {' / '.join(reasons)} の余剰ピクセルは切り捨てられます。", file=sys.stderr)

        cols = region_w // step_w
        rows = region_h // step_h

        dot_scale = units_per_em / glyph_h
        cell_baseline_dots = round(glyph_h * baseline_ratio)

        pixels = img.load()
        count = cols * rows

        duplicated_cps = []

        for i in range(count):
            c = i % cols
            r = i // cols
            cx = x1 + c * step_w
            cy = y1 + r * step_h

            cp = start_cp + i
            gname = f"uni{cp:04X}"

            if cp in cmap:
                duplicated_cps.append(cp)

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
                "gname": gname,
            })
            global_index += 1

        if duplicated_cps:
            print(f"警告: {set_label}: {len(duplicated_cps)} 件のコードポイントが既存グリフと重複したため上書きされました:", file=sys.stderr)
            max_show = 10
            for d_cp in duplicated_cps[:max_show]:
                print(f"  - U+{d_cp:04X} (uni{d_cp:04X})", file=sys.stderr)
            if len(duplicated_cps) > max_show:
                print(f"  ... 他 {len(duplicated_cps) - max_show} 件", file=sys.stderr)

        size_info = f"間隔: {step_w}x{step_h}"
        if (step_w, step_h) != (glyph_w, glyph_h):
            size_info += f", 有効: {glyph_w}x{glyph_h}"
        print(f"{set_label}: ({cols}x{rows}={count}文字, {size_info}) 開始: U+{start_cp:04X}")

    # 半角スケーリングコピー (X軸50%縮小)
    glyph_origin_map = {}
    if scale_copy_params:
        scale_copy_src, scale_copy_dst, scale_copy_count = scale_copy_params
        glyph_set = glyphs
        copied_count = 0
        copy_overwrites = []

        for i in range(scale_copy_count):
            s_cp = scale_copy_src + i
            d_cp = scale_copy_dst + i
            s_gname = f"uni{s_cp:04X}"
            d_gname = f"uni{d_cp:04X}"

            if s_gname not in glyphs:
                continue

            if d_gname in glyphs:
                copy_overwrites.append(d_cp)

            glyph_origin_map[d_gname] = s_gname

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

        if copied_count == 0:
            print(f"エラー: スケールコピー元 (U+{scale_copy_src:04X} 〜 U+{scale_copy_src + scale_copy_count - 1:04X}) にコピー対象のグリフが 1 つも存在しません。", file=sys.stderr)
            sys.exit(1)
        elif copied_count < scale_copy_count:
            print(f"警告: スケールコピー対象 {scale_copy_count} 文字中、{copied_count} 文字のみコピーされました ({scale_copy_count - copied_count} 文字のコピー元グリフが存在しません)。", file=sys.stderr)

        if copy_overwrites:
            print(f"警告: スケールコピー先 (U+{scale_copy_dst:04X} 〜) で {len(copy_overwrites)} 件の既存グリフが上書きされました:", file=sys.stderr)
            max_show = 10
            for ov_cp in copy_overwrites[:max_show]:
                print(f"  - U+{ov_cp:04X} (uni{ov_cp:04X})", file=sys.stderr)
            if len(copy_overwrites) > max_show:
                print(f"  ... 他 {len(copy_overwrites) - max_show} 件", file=sys.stderr)

        print(f"半角スケーリングコピー: U+{scale_copy_src:04X} -> U+{scale_copy_dst:04X} ({copied_count} 文字)")

    # 文字マップ (.def) マッピング
    if charmap_params:
        charmap_file, charmap_source = charmap_params
        cpath = Path(charmap_file)
        if not cpath.exists():
            raise FileNotFoundError(f"文字マップ定義ファイルが見つかりません: {charmap_file}")
        with open(cpath, "r", encoding="utf-8") as f:
            char_map = parse_char_map(f)

        # 参照元コードポイントが未指定の場合、先頭セットの開始コードポイントを使用
        resolved_charmap_source = charmap_source
        if resolved_charmap_source is None:
            resolved_charmap_source = parse_code_point(sets_config[0]["start_cp"])

        mapped_count = 0
        total_defined = 0
        collisions = []

        for i, char in enumerate(char_map):
            if char is None:
                continue
            total_defined += 1
            src_cp = resolved_charmap_source + i
            src_gname = f"uni{src_cp:04X}"
            if src_gname not in glyphs:
                continue

            dst_cp = ord(char)
            if dst_cp in cmap and cmap[dst_cp] != src_gname:
                collisions.append((char, dst_cp, cmap[dst_cp], src_gname))

            cmap[dst_cp] = src_gname
            mapped_count += 1

        if mapped_count == 0:
            print(f"エラー: 文字マップの参照元 (U+{resolved_charmap_source:04X} 付近) にグリフが 1 つも存在しません。文字マッピングが 0 件のため処理を中断します。", file=sys.stderr)
            print(f"  ヒント: --charmap の参照元コードポイントが、画像取り込み開始コードポイントやスケールコピー先と一致しているか確認してください。", file=sys.stderr)
            sys.exit(1)
        elif mapped_count < total_defined:
            missing_count = total_defined - mapped_count
            print(f"警告: 文字マップ定義の {total_defined} 文字中 {missing_count} 文字は、参照元グリフが存在しないためスキップされました。({mapped_count} 文字マッピング完了)", file=sys.stderr)

        if collisions:
            print(f"警告: 文字マップ定義内で {len(collisions)} 件の文字割り当て衝突が発生し、上書きされました:", file=sys.stderr)
            max_show = 10
            for ch, dst_cp, prev_g, new_g in collisions[:max_show]:
                escaped_ch = format_char_literal(ch)
                print(f"  - '{escaped_ch}' (U+{dst_cp:04X}): {prev_g} -> {new_g} で上書き", file=sys.stderr)
            if len(collisions) > max_show:
                print(f"  ... 他 {len(collisions) - max_show} 件", file=sys.stderr)

        print(f"文字マップマッピング: '{charmap_file}' (参照元 U+{resolved_charmap_source:04X}) から {mapped_count} 文字をUnicodeへマッピング")

    # プロポーショナル出力用: 最終的な cmap からの Unicode 文字逆引き更新
    if proportional:
        glyph_to_char = {}
        for cp, gn in cmap.items():
            ch = chr(cp)
            is_pua = (0xE000 <= cp <= 0xF8FF) or (0xF0000 <= cp <= 0x10FFFF)
            if gn not in glyph_to_char:
                glyph_to_char[gn] = ch
            else:
                prev_cp = ord(glyph_to_char[gn])
                prev_is_pua = (0xE000 <= prev_cp <= 0xF8FF) or (0xF0000 <= prev_cp <= 0x10FFFF)
                if prev_is_pua and not is_pua:
                    glyph_to_char[gn] = ch

        for rec in proportional_records:
            gn = rec.get("gname")
            if not gn:
                continue

            target_ch = None
            if gn in glyph_to_char:
                c = glyph_to_char[gn]
                if not ((0xE000 <= ord(c) <= 0xF8FF) or (0xF0000 <= ord(c) <= 0x10FFFF)):
                    target_ch = c

            if target_ch is None:
                for copied_gn, src_gn in glyph_origin_map.items():
                    if src_gn == gn and copied_gn in glyph_to_char:
                        c = glyph_to_char[copied_gn]
                        if not ((0xE000 <= ord(c) <= 0xF8FF) or (0xF0000 <= ord(c) <= 0x10FFFF)):
                            target_ch = c
                            break

            if target_ch is not None:
                rec["char"] = target_ch

    # OpenTypeテーブル構築
    fb = FontBuilder(units_per_em, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ascent, descent=descent)

    name_strings = {
        "familyName": family_name,
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
    parser.add_argument("input", nargs="?", default=None, help="入力画像ファイルパス (単一画像指定用)")
    parser.add_argument("-o", "--output", default=None, help="出力TTFファイル名 (省略時は設定名 / 画像名 / フォント名から自動決定)")
    parser.add_argument("-n", "--name", default=None, help="フォント名 (省略時は --family と同じ、または設定名 / 画像名)")
    parser.add_argument("-f", "--family", "--family-name", dest="family_name", default=None, help="フォントファミリー名 (省略時は --name と同じ)")
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
        help=f"ベースライン (ドット数、割り算 '1/8'、またはパーセント '12.5%%'。デフォルト: {DEFAULT_BASELINE_RATIO})"
    )

    # 上下余白
    parser.add_argument("-mt", "--margin-top", default=None, help="上余白 (ドット数、'1/8'、または '12.5%%')")
    parser.add_argument("-mb", "--margin-bottom", default=None, help="下余白 (ドット数、'1/8'、または '12.5%%')")
    parser.add_argument("-m", "--margin", default=None, help="上下共通の余白 (ドット数、'1/8'、または '12.5%%')")

    # 単一画像向けセルサイズオプション (bmp2ttf 互換)
    parser.add_argument("-s", "--cell-size", dest="cell_size", default="8x8", help="セルサイズ (単一画像指定用。デフォルト: 8x8)")
    parser.add_argument("-cw", "--cell-width", type=int, default=None, help="セル幅 (単一画像指定用)")
    parser.add_argument("-ch", "--cell-height", type=int, default=None, help="セル高 (単一画像指定用)")

    # 複数セット指定オプション
    parser.add_argument(
        "--set",
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

    # 半角スケーリングコピー設定 (カンマ区切り一体化)
    parser.add_argument(
        "--scale-copy",
        default=None,
        help="横50%%縮小コピーグリフの生成: 'コピー元,コピー先,文字数' (例: '0xE000,0xE100,256')"
    )

    # 文字マップ定義マッピング設定 (カンマ区切り一体化)
    parser.add_argument(
        "-cm", "--charmap",
        default=None,
        help="文字マップ定義とマッピング: '定義ファイルパス[,参照元コードポイント]' (例: 'map.def,0xE000')"
    )

    args = parser.parse_args()

    sets_config = []
    units_per_em = args.units_per_em
    baseline_val = args.baseline
    margin_top_val = args.margin_top if args.margin_top is not None else args.margin
    margin_bottom_val = args.margin_bottom if args.margin_bottom is not None else args.margin
    font_name = args.name
    family_name = args.family_name
    proportional = args.proportional
    char_spacing = args.char_spacing
    space_width = args.space_width

    raw_scale_copy = args.scale_copy
    raw_charmap = args.charmap

    cfg = {}
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
        if "family" in cfg or "family_name" in cfg:
            family_name = cfg.get("family") or cfg.get("family_name")
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
        if "scale_copy" in cfg and raw_scale_copy is None:
            raw_scale_copy = cfg["scale_copy"]
        if "charmap" in cfg and raw_charmap is None:
            raw_charmap = cfg["charmap"]

    margin_top_val = margin_top_val if margin_top_val is not None else 0.0
    margin_bottom_val = margin_bottom_val if margin_bottom_val is not None else 0.0

    # スケールコピー設定のパース
    scale_copy_params = None
    if raw_scale_copy is not None:
        try:
            scale_copy_params = parse_scale_copy_arg(raw_scale_copy)
        except Exception as e:
            print(f"エラー: --scale-copy の指定が不正です: {e}", file=sys.stderr)
            sys.exit(1)
        if scale_copy_params[2] <= 0:
            print(f"エラー: スケールコピー文字数には 1 以上の整数を指定してください (指定値: {scale_copy_params[2]})", file=sys.stderr)
            sys.exit(1)

    # 文字マップ設定のパース
    charmap_params = None
    if raw_charmap is not None:
        try:
            charmap_params = parse_charmap_arg(raw_charmap)
        except Exception as e:
            print(f"エラー: --charmap の指定が不正です: {e}", file=sys.stderr)
            sys.exit(1)

    # プロポーショナル関連の検証
    proportional_args_specified = (
        args.char_spacing != 1 or
        args.space_width is not None or
        "char_spacing" in cfg or
        "space_width" in cfg
    )
    if not proportional and proportional_args_specified:
        print("警告: プロポーショナルモード (--proportional) が指定されていないため、字間 (--char-spacing) や空白幅 (--space-width) の指定は無視されます。", file=sys.stderr)

    if proportional and space_width is not None and space_width <= 0:
        print(f"エラー: 空白文字幅 (--space-width) には 1 以上の整数を指定してください (指定値: {space_width})", file=sys.stderr)
        sys.exit(1)

    # CLIの --set からの読み込み
    if args.sets:
        for s_str in args.sets:
            try:
                sets_config.append(parse_set_arg(s_str))
            except Exception as e:
                print(f"エラー: --set 引数の形式が不正です: {s_str}\n  {e}", file=sys.stderr)
                sys.exit(1)

    # CLIの位置引数 input からの単一画像取り込み
    if args.input and not sets_config:
        try:
            cw, ch = _parse_dimension_pair(args.cell_size)
        except Exception:
            print(f"エラー: --cell-size の指定形式が不正です: '{args.cell_size}'", file=sys.stderr)
            sys.exit(1)
        if args.cell_width is not None:
            cw = args.cell_width
        if args.cell_height is not None:
            ch = args.cell_height

        sets_config.append({
            "image": args.input,
            "bbox": None,
            "step_size": (cw, ch),
            "glyph_size": (cw, ch),
            "start_cp": 0xE000,
        })

    if not sets_config:
        print("エラー: 取り込む画像セットが指定されていません。入力画像パス、--set、または --config を指定してください。", file=sys.stderr)
        sys.exit(1)

    # フォント名・出力ファイル名の決定
    # 解決優先順: 指定名 (--name / --family / JSON) -> 設定ファイル名 -> 画像名
    base_name = font_name or family_name
    if not base_name:
        if args.config:
            base_name = Path(args.config).stem
        else:
            unique_images = list(dict.fromkeys(s["image"] for s in sets_config if "image" in s))
            if len(unique_images) == 1:
                base_name = Path(unique_images[0]).stem
            else:
                base_name = "Font"

    resolved_font_name = font_name or family_name or base_name
    resolved_family_name = family_name or font_name or base_name

    output_path = args.output
    if not output_path:
        output_path = f"{base_name}.ttf"

    try:
        build_font(
            sets_config=sets_config,
            output_path=output_path,
            units_per_em=units_per_em,
            font_name=resolved_font_name,
            family_name=resolved_family_name,
            baseline_ratio_val=baseline_val,
            margin_top_val=margin_top_val,
            margin_bottom_val=margin_bottom_val,
            scale_copy_params=scale_copy_params,
            charmap_params=charmap_params,
            proportional=proportional,
            char_spacing=char_spacing,
            space_width=space_width,
        )
    except Exception as e:
        print(f"エラー: フォント生成に失敗しました: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

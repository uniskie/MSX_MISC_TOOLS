import argparse
import sys
from pathlib import Path

# 1. ライブラリのインポートチェック
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

DEFAULT_CELL_WIDTH = 8
DEFAULT_CELL_HEIGHT = 8

DEFAULT_MARGIN_TOP = 0
DEFAULT_MARGIN_BOTTOM = 0

PIXEL_BRIGHTNESS_THRESHOLD = 128
RGBA_ALPHA_INDEX = 3
RGBA_COLOR_COUNT = 4

UNICODE_FULLWIDTH_BASE = 0xE000
UNICODE_HALFWIDTH_BASE = 0xE100

FONT_UNITS_PER_EM = 1024
HALFWIDTH_RATIO = 0.5

BASELINE_DOT_RATIO = 1.0 / 8.0
X_HEIGHT_RATIO = 4.0 / 8.0
CAP_HEIGHT_RATIO = 6.0 / 8.0

DEFAULT_FONT_NAME = "MSX-Font"
DEFAULT_STYLE_NAME = "Regular"
DEFAULT_FONT_VERSION = "Version 1.0"
POST_IS_FIXED_PITCH_TRUE = 1
POST_TABLE_FORMAT = 2.0
OS2_PANOSE_PROPORTION_MONO = 9
OS2_CP932_BIT_OFFSET = 17

ALTERNATIVE_MSX_CHAR_MAP = [
    # 00-1F : GRAPHIC文字
    "\u0000", "月", "火", "水", "木", "金", "土", "日", "年", "円", "時", "分", "秒", "百", "千", "万",
    "π", "┴", "┬", "┤", "├", "┼", "│", "─", "┌", "┐", "└", "┘", "╳×", "大", "中", "小",
    # 20-7F : ASCII文字
    " 　", "!！", '"”“', "#＃", "$＄", "%％", "&＆", "'’", "(（", ")）", "*＊", "+＋", ",，", "-－", ".．", "/／",
    "0０", "1１", "2２", "3３", "4４", "5５", "6６", "7７", "8８", "9９", ":：", ";；", "<＜", "=＝", ">＞", "?？",
    "@＠", "AＡ", "BＢ", "CＣ", "DＤ", "EＥ", "FＦ", "GＧ", "HＨ", "IＩ", "JＪ", "KＫ", "LＬ", "MＭ", "NＮ", "OＯ",
    "PＰ", "QＱ", "RＲ", "SＳ", "TＴ", "UＵ", "VＶ", "WＷ", "XＸ", "YＹ", "ZＺ", "[［", "\\￥", "]］", "^＾", "_＿",
    "`｀", "aａ", "bｂ", "cｃ", "dｄ", "eｅ", "fｆ", "gｇ", "hｈ", "iｉ", "jｊ", "kｋ", "lｌ", "mｍ", "nｎ", "oｏ",
    "pｐ", "qｑ", "rｒ", "sｓ", "tｔ", "uう", "vｖ", "wｗ", "xｘ", "yｙ", "zｚ", "{｛", "|｜", "}｝", "~～", "\u007F",
    # 80-9F : ひらがな1 / 記号
    "♠", "♥", "♣", "♦", "○", "●", "を", "ぁ", "ぃ", "ぅ", "ぇ", "ぉ", "ゃ", "ゅ", "ょ", "っ",
    "\u0090", "あ", "い", "う", "え", "お", "か", "き", "く", "け", "こ", "さ", "し", "す", "せ", "そ",
    # A0-DF : カタカナ
    "\u00A0", "。｡", "「｢", "」｣", "、､", "・･", "ヲｦ", "ァｧ", "ィｨ", "ゥｩ", "ェｪ", "ォｫ", "ャｬ", "ュｭ", "ョｮ", "ッｯ",
    "ーｰ", "アｱ", "イｲ", "ウｳ", "エｴ", "オｵ", "カｶ", "キｷ", "クｸ", "ケｹ", "コｺ", "サｻ", "シｼ", "スｽ", "セｾ", "ソｿ",
    "タﾀ", "チﾁ", "ツﾂ", "テﾃ", "トﾄ", "ナﾅ", "ニﾆ", "ヌﾇ", "ネﾈ", "ノﾉ", "ハﾊ", "ヒﾋ", "フﾌ", "ヘﾍ", "ホﾎ", "マﾏ",
    "ミﾐ", "ムﾑ", "メﾒ", "モﾓ", "ヤﾔ", "ユﾕ", "ヨﾖ", "ラﾗ", "リﾘ", "ルﾙ", "レﾚ", "ロﾛ", "ワﾜ", "ンﾝ", "゛ﾞ", "゜ﾟ",
    # E0-FF : ひらがな2
    "た", "ち", "つ", "て", "と", "な", "に", "ぬ", "ね", "の", "は", "ひ", "ふ", "へ", "ほ", "ま",
    "み", "む", "め", "も", "や", "ゆ", "よ", "ら", "り", "る", "れ", "ろ", "わ", "ん", "\u00FE", "\u00FF"
]


# ==============================================================================
# 引数パーサー
# ==============================================================================

class CustomArgumentParser(argparse.ArgumentParser):
    """エラー時に日本語のメッセージとヘルプのヒントを表示するパーサー"""
    def error(self, message):
        sys.stderr.write(f"引数エラー: {message}\n")
        sys.stderr.write("詳細は 'python bmp2ttf.py --help' をご確認ください。\n")
        sys.exit(2)


# ==============================================================================
# グリフ生成処理
# ==============================================================================

def extract_horizontal_segments(pixels, char_x: int, char_y: int, cell_w: int, cell_h: int):
    segments = []
    for y in range(cell_h):
        segment_start = None
        for x in range(cell_w):
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
            segments.append((segment_start, cell_w, y))

    return segments


def create_fullwidth_glyph(segments, cell_h: int, dot_scale_x: float, dot_scale_y: float, baseline_dots: int):
    pen = TTGlyphPen(None)
    if not segments:
        return pen.glyph(), 0

    min_x0 = None
    for x_start, x_end, y in segments:
        dot_y = (cell_h - 1 - y) - baseline_dots
        y0 = round(dot_y * dot_scale_y)
        y1 = round((dot_y + 1) * dot_scale_y)
        x0 = round(x_start * dot_scale_x)
        x1 = round(x_end * dot_scale_x)

        if min_x0 is None or x0 < min_x0:
            min_x0 = x0

        pen.moveTo((x0, y0))
        pen.lineTo((x0, y1))
        pen.lineTo((x1, y1))
        pen.lineTo((x1, y0))
        pen.closePath()

    glyph = pen.glyph()
    lsb = min_x0 if min_x0 is not None else 0
    return glyph, lsb


def build_font_from_image(
    image_path: str,
    output_path: str,
    cell_w: int = DEFAULT_CELL_WIDTH,
    cell_h: int = DEFAULT_CELL_HEIGHT,
    font_name: str = DEFAULT_FONT_NAME,
    baseline_dots: int | None = None,
    margin_top: int = DEFAULT_MARGIN_TOP,
    margin_bottom: int = DEFAULT_MARGIN_BOTTOM,
    units_per_em: int = FONT_UNITS_PER_EM,
    family_name: str | None = None,
):
    img = Image.open(image_path).convert("RGBA")
    img_w, img_h = img.size

    cols = img_w // cell_w
    rows = img_h // cell_h
    total_cells = cols * rows
    glyph_count = min(total_cells, len(ALTERNATIVE_MSX_CHAR_MAP))

    if cols == 0 or rows == 0:
        raise ValueError(f"画像サイズ ({img_w}x{img_h}) がセルサイズ ({cell_w}x{cell_h}) より小さいです。")

    family = family_name if family_name is not None else font_name

    full_width = units_per_em
    half_width = int(full_width * HALFWIDTH_RATIO)

    dot_scale_y = units_per_em / cell_h
    full_dot_scale_x = full_width / cell_w

    if baseline_dots is None:
        baseline_dots = round(cell_h * BASELINE_DOT_RATIO)

    x_height_units = round((cell_h * X_HEIGHT_RATIO) * dot_scale_y)
    cap_height_units = round((cell_h * CAP_HEIGHT_RATIO) * dot_scale_y)
    ascent = round((cell_h - baseline_dots + margin_top) * dot_scale_y)
    descent = -round((baseline_dots + margin_bottom) * dot_scale_y)

    pixels = img.load()

    notdef_glyph = TTGlyphPen(None).glyph()
    glyphs = {".notdef": notdef_glyph}
    metrics = {".notdef": (half_width, 0)}
    cmap = {}
    glyph_order = [".notdef"]

    # 全角グリフ生成
    for i in range(glyph_count):
        col = i % cols
        row = i // cols
        char_x = col * cell_w
        char_y = row * cell_h

        segments = extract_horizontal_segments(pixels, char_x, char_y, cell_w, cell_h)
        full_glyph, lsb = create_fullwidth_glyph(
            segments, cell_h, full_dot_scale_x, dot_scale_y, baseline_dots
        )

        full_cp = UNICODE_FULLWIDTH_BASE + i
        full_gname = f"uni{full_cp:04X}"

        glyphs[full_gname] = full_glyph
        metrics[full_gname] = (full_width, lsb)
        cmap[full_cp] = full_gname
        glyph_order.append(full_gname)

    # 半角グリフ生成
    glyph_set = glyphs
    for i in range(glyph_count):
        src_cp = UNICODE_FULLWIDTH_BASE + i
        dst_cp = UNICODE_HALFWIDTH_BASE + i
        src_gname = f"uni{src_cp:04X}"
        dst_gname = f"uni{dst_cp:04X}"

        if src_gname not in glyphs:
            continue

        src_glyph = glyphs[src_gname]
        _, src_lsb = metrics[src_gname]

        tt_pen = TTGlyphPen(glyph_set)
        trans_pen = TransformPen(tt_pen, (HALFWIDTH_RATIO, 0, 0, 1.0, 0, 0))
        src_glyph.draw(trans_pen, glyph_set)
        half_glyph = tt_pen.glyph()

        glyphs[dst_gname] = half_glyph
        new_lsb = round(src_lsb * HALFWIDTH_RATIO)
        metrics[dst_gname] = (half_width, new_lsb)
        cmap[dst_cp] = dst_gname
        glyph_order.append(dst_gname)

    # ALTERNATIVE_MSX_CHAR_MAP マッピング
    mapped_count = 0
    for i in range(glyph_count):
        s = ALTERNATIVE_MSX_CHAR_MAP[i]
        if not s:
            continue
        target_char = s[0]
        dst_cp = ord(target_char)
        src_gname = f"uni{UNICODE_HALFWIDTH_BASE + i:04X}"

        cmap[dst_cp] = src_gname
        mapped_count += 1

    # フォントテーブル構築
    fb = FontBuilder(units_per_em, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ascent, descent=descent)

    name_strings = {
        "familyName": family,
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
    os2 = font["OS/2"]
    os2.xAvgCharWidth = half_width
    os2.panose.bProportion = OS2_PANOSE_PROPORTION_MONO
    os2.ulCodePageRange1 = 1 << OS2_CP932_BIT_OFFSET
    os2.ulCodePageRange2 = 0

    font["post"].isFixedPitch = POST_IS_FIXED_PITCH_TRUE

    font.save(output_path)
    print(f"成功: '{output_path}' を生成しました。")
    print(f" - 画像サイズ: {img_w}x{img_h} ({cols}列x{rows}行, セル: {cell_w}x{cell_h})")
    print(f" - フォントファミリー名: {family}")
    print(f" - フォント名: {font_name}")
    print(f" - EMの高さ: {units_per_em}")
    print(f" - 余白: 上 {margin_top} ドット / 下 {margin_bottom} ドット")
    print(f" - ベースライン: 下端から {baseline_dots} ドット (Descent: {descent}, Ascent: {ascent})")
    print(f" - グリフ数: 全角 {glyph_count} 文字 / 半角 {glyph_count} 文字")
    print(f" - 代替文字マッピング: {mapped_count} 文字")


# ==============================================================================
# エントリーポイント
# ==============================================================================

def parse_cell_size(val: str):
    sep = "x" if "x" in val.lower() else ("," if "," in val else None)
    if sep:
        parts = val.lower().split(sep)
        return int(parts[0]), int(parts[1])
    size = int(val)
    return size, size


def main():
    parser = CustomArgumentParser(
        description="MSXフォント画像 (BMP/PNG) から等幅 TrueType フォント (.ttf) を生成します。"
    )
    parser.add_argument("input", help="入力画像ファイルパス (BMP, PNGなど)")
    parser.add_argument("-o", "--output", dest="output", help="出力TTFファイル名 (省略時は <画像名>.ttf)")
    parser.add_argument("-n", "--name", dest="name", default=DEFAULT_FONT_NAME, help=f"フォント名 (デフォルト: {DEFAULT_FONT_NAME})")
    parser.add_argument("-f", "--family", "--family-name", dest="family_name", default=None, help="フォントファミリー名 (省略時は --name と同じ)")

    parser.add_argument(
        "-s", "--cell-size",
        dest="cell_size",
        default=f"{DEFAULT_CELL_WIDTH}x{DEFAULT_CELL_HEIGHT}",
        help=f"文字のセルサイズ (例: 8x8, 16x16, 8)。デフォルト: {DEFAULT_CELL_WIDTH}x{DEFAULT_CELL_HEIGHT}"
    )
    parser.add_argument("-cw", "--cell-width", type=int, dest="cell_width", default=None, help="セル幅")
    parser.add_argument("-ch", "--cell-height", type=int, dest="cell_height", default=None, help="セル高")
    parser.add_argument(
        "-b", "--baseline",
        type=int,
        dest="baseline",
        default=None,
        help="ベースライン位置 (セル下端からのドット数/ディセンダドット数。省略時はセル高さの1/8)"
    )
    parser.add_argument(
        "-mt", "--margin-top",
        type=int,
        dest="margin_top",
        default=DEFAULT_MARGIN_TOP,
        help=f"上余白ドット数 (アセンダ側の追加余白。デフォルト: {DEFAULT_MARGIN_TOP})"
    )
    parser.add_argument(
        "-mb", "--margin-bottom",
        type=int,
        dest="margin_bottom",
        default=DEFAULT_MARGIN_BOTTOM,
        help=f"下余白ドット数 (ディセンダ側の追加余白。デフォルト: {DEFAULT_MARGIN_BOTTOM})"
    )
    parser.add_argument(
        "-e", "--em", "--units-per-em",
        type=int,
        dest="units_per_em",
        default=FONT_UNITS_PER_EM,
        help=f"EMの高さ (Units per em。デフォルト: {FONT_UNITS_PER_EM})"
    )

    args = parser.parse_args()

    # --- 引数のバリデーション ---
    
    # 1. 入力ファイルの存在確認
    in_path = Path(args.input)
    if not in_path.exists():
        print(f"エラー: 入力画像ファイルが見つかりません: {in_path}", file=sys.stderr)
        sys.exit(1)

    # 2. セルサイズの形式・数値チェック
    try:
        cell_w, cell_h = parse_cell_size(args.cell_size)
    except Exception:
        print(f"エラー: --cell-size の指定形式が不正です: '{args.cell_size}' (例: 8x8, 16x16)", file=sys.stderr)
        sys.exit(1)

    if args.cell_width is not None:
        cell_w = args.cell_width
    if args.cell_height is not None:
        cell_h = args.cell_height

    if cell_w <= 0 or cell_h <= 0:
        print(f"エラー: セルサイズには 1 以上の正の整数を指定してください (指定値: 幅={cell_w}, 高={cell_h})", file=sys.stderr)
        sys.exit(1)

    # 3. ベースラインの範囲チェック
    if args.baseline is not None:
        if args.baseline < 0 or args.baseline > cell_h:
            print(
                f"エラー: --baseline には 0 以上 セル高さ({cell_h}) 以下の値を指定してください。(指定値: {args.baseline})",
                file=sys.stderr
            )
            sys.exit(1)

    # 4. 余白の数値チェック
    if args.margin_top < 0 or args.margin_bottom < 0:
        print("エラー: --margin-top および --margin-bottom には 0 以上の整数を指定してください。", file=sys.stderr)
        sys.exit(1)

    # 5. EMの高さチェック
    if args.units_per_em < 16 or args.units_per_em > 16384:
        print(
            f"エラー: --em には TrueType 仕様に準拠した 16 以上 16384 以下の整数を指定してください。(指定値: {args.units_per_em})",
            file=sys.stderr
        )
        sys.exit(1)

    # フォント名・ファミリー名の連動処理
    font_name = args.name
    family_name = args.family_name
    if family_name is not None and font_name == DEFAULT_FONT_NAME:
        font_name = family_name

    out_path = Path(args.output) if args.output else in_path.with_suffix(".ttf")
    
    try:
        build_font_from_image(
            str(in_path),
            str(out_path),
            cell_w=cell_w,
            cell_h=cell_h,
            font_name=font_name,
            baseline_dots=args.baseline,
            margin_top=args.margin_top,
            margin_bottom=args.margin_bottom,
            units_per_em=args.units_per_em,
            family_name=family_name,
        )
    except Exception as e:
        print(f"エラー: フォント生成に失敗しました: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

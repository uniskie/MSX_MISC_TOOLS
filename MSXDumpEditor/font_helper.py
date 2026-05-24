import os
import sys
import tkinter as tk
from tkinter import font as tkfont

FONT_DEBUG = True

TK_DEFAULT_FONT_LINESPACE = 10

tk_root = None
font_name_ui      = ""
font_name_sans    = ""
font_name_mono    = ""
font_name_program = ""
font_pt = 10


#--------------------------------------------------------------------------
# Font helper
#--------------------------------------------------------------------------

# 余白の扱いが近いフォントをなるべく採用するようにしたい

# 日本語 プログラム向け等幅フォント優先順
jp_programming_fonts = [
    'HackGen', 
    'UDEV Gothic',
    'VL Gothic',
    'VL ゴシック',
    'BIZ UDGothic',
    'osaka mono', 
    'Osaka－等幅',
    'MS Gothic',
    'ＭＳ ゴシック',
    'monotype',
    'monospace '
]
# 日本語 テキスト向け等幅フォント優先順
jp_mono_fonts = [
    'UDEV Gothic',
    'HackGen', 
    'VL Gothic',
    'VL ゴシック',
    'osaka mono',
    'Osaka－等幅',
    'BIZ UDGothic', 
    'BIZ UDゴシック', 
    'MS Gothic',
    'ＭＳ ゴシック',
    'monotype',
    'monospace '
]
# 日本語 テキスト向けプロポーショナルフォント優先順
jp_sans_fonts = [
    'VL PGothic',
    'VL Pゴシック',
    'Osaka-UI',
    'osaka unicode',
    'osaka',
    'YU Gothic',
    '游ゴシック',
    'Meiryo',
    'MS UI Gothic',
    'MS PGothic',
    'ＭＳ Ｐゴシック',
    'BIZ UDPGothic',
    'BIZ UDPゴシック',
    'sans',
    'sansserif',
    'sans-serif'
]
# 日本語 UI向けプロポーショナルフォント優先順
jp_sans_ui_fonts = [
    'VL PGothic',
    'VL Pゴシック',
    'meiryo',
    'メイリオ',
    'Yu Gothic UI',
    'YU Gothic',
    '游ゴシック',
    'MS UI Gothic',
    'Osaka-UI',
    'osaka unicode',
    'BIZ UDPGothic', 
    'BIZ UDPゴシック', 
    'MS PGothic',
    'ＭＳ Ｐゴシック',
    'osaka'
    'sans',
    'sansserif',
    'sans-serif'
]

# Tk 標準フォント名
tk_font_names = [
    'TkDefaultFont',           # 特に指定がない限り、項目はデフォルト値となります。
    'TkTextFont',              # 入力ウィジェット、リストボックスなどに使用されます。
    'TkFixedFont',             # 標準的な固定幅フォント。
    'TkMenuFont',              # メニュー項目に使用されるフォント。
    'TkHeadingFont',           # リストや表の列見出しに使用するフォント。
    'TkCaptionFont',           # ウィンドウやダイアログのキャプションバーに使用するフォント。
    'TkSmallCaptionFont',      # ツールダイアログのキャプションフォントを小さくします。
    'TkIconFont',              # アイコンのキャプションに使用するフォント。
    'TkTooltipFont'            # ツールチップ用のフォント。
]

# 指定した高さ(px)に一番近くてそれ以下のサイズのフォントを得る
# OSごとにずれるので非推奨
def get_font_with_pixel_height(target_height: int, font_family: str = 'TkDefaultFont'):

    # Linuxは上下余白が広い説
    if os.name == 'posix' and sys.platform != 'darwin':
        target_height += 1

    if font_family in tkfont.names():
        test_font = tkfont.Font(font=font_family)
    else:
        test_font = tkfont.Font(family=font_family)

    # サイズ指定がマイナス：ピクセル指定（高精度）
    # 探索範囲を設定（フォントサイズはマイナス値）
    low = - (target_height * 4)  # 念のため探索範囲を大きめに
    high = -1
    best_size = high

    min_diff = float('inf') # 最小誤差を記録

    while low <= high:
        mid = (low + high) // 2
        
        test_font.configure(size=mid)
        #current_height = test_font.metrics('linespace') # OS差がある
        current_height = test_font.metrics('ascent') + test_font.metrics('descent')


        diff = abs(current_height - target_height)

        # 純粋に誤差が最小のものを記録
        if diff < min_diff:
            min_diff = diff
            best_size = mid

            if diff == 0:
                break
        
        # 二分探索の方向制御：
        # Tkinterではサイズが負のとき、値が小さいほど文字が大きい
        if current_height > target_height:
            # 現在の高さが目標より高い ＝ 文字が大きすぎる
            # ＝ フォントサイズを小さくしたい ＝ 値を0に近づけたい（大きくしたい）
            low = mid + 1
        else:
            # 現在の高さが目標より低い ＝ 文字が小さすぎる
            # ＝ フォントサイズを大きくしたい ＝ 値をマイナス方向に遠ざけたい（小さくしたい）
            high = mid - 1
            
    if font_family in tkfont.names():
        return tkfont.Font(font=font_family, size=best_size)
    else:
        return tkfont.Font(family=font_family, size=best_size)

# フォントを名前で探してフォント設定を返す
def get_font_config(font_name):
    if tk_root is None:
        root = tk.Tk()
        root.withdraw()

    if font_name in tkfont.names():
        result = tkfont.nametofont(font_name).configure()
    else:
        font_list = tkfont.families()
        result =  font_name in font_list

    if tk_root is None:
        root.destroy()
    return result

# フォント名リストの中から最初に見つかったフォント名を返す
def find_font_first(list):
    if tk_root is None:
        root = tk.Tk()
        root.withdraw()

    # 小文字で比較用リスト作成
    available = [f.lower() for f in tkfont.families()]
    candidates = [f.lower() for f in list]

    font_name = ""
    for c in candidates:
        if c in available:
            font_name = tkfont.families()[available.index(c)]
            break

    if tk_root is None:
        root.destroy()
    
    return font_name

# リストを渡して存在するフォントを見つける
def search_font_list(font_list):
    for f in font_list:
        if get_font_config(f):
            return f
    return None

#
def setup_default_font(root, font_size=0):
    global tk_root
    global font_name_ui, font_name_sans, font_name_mono, font_name_program
    global font_pt

    tk_root = root

    if font_size:
        font_pt = font_size
    else:
        font_pt = TK_DEFAULT_FONT_LINESPACE

    font_name_ui      = find_font_first(jp_sans_ui_fonts)
    font_name_sans    = find_font_first(jp_sans_fonts)
    font_name_mono    = find_font_first(jp_mono_fonts)
    font_name_program = find_font_first(jp_programming_fonts)

    tkfont.nametofont('TkDefaultFont').configure(family=font_name_sans, size=font_pt, weight='bold')
    tkfont.nametofont('TkMenuFont'   ).configure(family=font_name_ui,   size=font_pt, weight='bold')
    tkfont.nametofont('TkHeadingFont').configure(family=font_name_ui,   size=font_pt, weight='bold')
    tkfont.nametofont('TkCaptionFont').configure(family=font_name_ui,   size=font_pt)
    tkfont.nametofont('TkTextFont'   ).configure(family=font_name_mono, size=font_pt)
    tkfont.nametofont('TkFixedFont'  ).configure(family=font_name_mono, size=font_pt)
    
    default_font = tkfont.nametofont('TkDefaultFont')

    root.option_add('*TCombobox*Listbox.font', default_font)
    root.option_add('*Button.font', default_font)
    root.option_add('*Entry.font', default_font)
    root.option_add('*Label.font', default_font)
    root.option_add('*Text.font', default_font)
    
    # デバッグ表示
    if FONT_DEBUG:
        print_tkfont_info()
        print(f"font_name_ui:       {font_name_ui}")
        print(f"font_name_sans:     {font_name_sans}")
        print(f"font_name_mono:     {font_name_mono}")
        print(f"font_name_program:  {font_name_program}")

    return

#--------------------------------------------------------------------------
# Test
#--------------------------------------------------------------------------
def print_all_fonts():
    print("=== Installed Fonts ".ljust(40,'='))
    font_count = 0
    for f in tkfont.families():
        print( f, end=", " )
        font_count+=1
    print("")
    print(f"=== {font_count} fonts installed ".ljust(40,'='))
    print("\n")

def print_tkfont_info():

    for font_name in tk_font_names:
        print(f"=== {font_name} ".ljust(40, '='))

        font = tkfont.nametofont(font_name)
        if font is None:
            print( " * not exists.")
            pass

        font_info = font.actual()
        print(f"ファミリー名         : {font_info['family']}")
        print(f"サイズ               : {font_info['size']}")
        print(f"太さ                 : {font_info['weight']}")

        font_metrics = font.metrics()
        print(f"文字全体の高さ       : {font_metrics['linespace']} px")
        print(f"ベースライン上の高さ : {font_metrics['ascent']} px")
        print(f"ベースライン下の深さ : {font_metrics['descent']} px")
        print(f"等幅                 : {font_metrics['fixed']}")

        test_text = ['Test', 'テスト', '012', ' ']
        width_result = f"文字列の横幅         : "
        for c in (test_text):
            width_result += f"'{c}'={font.measure(c)} "
        print(width_result)

        print("\n")

if __name__ == "__main__":
    tk_root = tk.Tk()
    tk_root.withdraw()

    print_all_fonts()
    print_tkfont_info()

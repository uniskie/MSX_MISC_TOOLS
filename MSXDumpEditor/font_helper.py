import sys
import tkinter as tk
from tkinter import font, ttk

FONT_DEBUG = False

tk_root = None
font_name_ui      = ""
font_name_sans    = ""
font_name_mono    = ""
font_name_program = ""
font_pt = 10


#--------------------------------------------------------------------------
# Font helper
#--------------------------------------------------------------------------

# 日本語 プログラム向け等幅フォント優先順
jp_programming_fonts = [
    'hackgen', 
    'vl gothic',
    'vl ゴシック',
    'biz udgothic',
    'osaka mono', 
    'ms gothic',
    'ｍｓ ゴシック',
    'monotype',
    'monospace '
]
# 日本語 テキスト向け等幅フォント優先順
jp_mono_fonts = [
    'vl gothic',
    'vl ゴシック',
    'biz udgothic', 
    'ms gothic',
    'ｍｓ ゴシック',
    'osaka mono',
    'monotype',
    'monospace '
]
# 日本語 テキスト向けプロポーショナルフォント優先順
jp_sans_fonts = [
    'biz udpgothic', 
    'vl pゴシック',
    'vl pgothic',
    'yu gothic',
    'meiryo',
    'ms ui gothic',
    'ms pgothic',
    'osaka ui',
    'osaka',
    'sans',
    'sansserif',
    'sans-serif'
]
# 日本語 UI向けプロポーショナルフォント優先順
jp_sans_ui_fonts = [
    'vl pgothic',
    'vl pゴシック',
    'biz udpgothic', 
    'yu gothic ui',
    'meiryo',
    'ms ui gothic',
    'ms pgothic',
    'osaka ui',
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

# setup_default_fontで調査される、デフォルトフォントの高さ(px)
TK_DEFAULT_FONT_LINESPACE = 12 # 仮の値

# 指定した高さ(px)に一番近くてそれ以下のサイズのフォントを得る
# OSごとにずれるので非推奨
def get_font_for_pixel_height(target_height:int, font_family:str='TkDefaultFont'):

    low = 1
    high = target_height * 2
    best_size = low
    
    if font_family in tk.font.names():
        # Tk***Font
        base_options = tk.font.nametofont(font_family).configure()
    else:
        base_options = {'family': font_family}

    while low <= high:
        mid = (low + high) // 2
        current_options = base_options.copy()
        current_options['size'] = mid
        test_font = tk.font.Font(**current_options)
        
        current_height = test_font.metrics('linespace')
        
        if current_height <= target_height:
            best_size = mid
            low = mid + 1
        else:
            high = mid - 1
            
    final_options = base_options.copy()
    final_options['size'] = best_size
    #print(f'{font_family} : family={final_options["family"]} size={best_size}')
    return tk.font.Font(**final_options)

# フォントを名前で探してフォント設定を返す
def get_font_config(font_name):
    if tk_root is None:
        root = tk.Tk()
        root.withdraw()

    if font_name in tk.font.names():
        result = tk.font.nametofont(font_name).configure()
    else:
        font_list = tk.font.families()
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
    available = [f.lower() for f in tk.font.families()]
    candidates = [f.lower() for f in list]

    font_name = ""
    for c in candidates:
        if c in available:
            font_name = tk.font.families()[available.index(c)]
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
def setup_default_font(root:tk):
    global tk_root
    global font_name_ui, font_name_sans, font_name_mono, font_name_program
    global font_pt

    if tk_root is not None:
        tk_root.destroy()
    tk_root = root

    font_pt = 10

    font_name_ui      = find_font_first(jp_sans_ui_fonts)
    font_name_sans    = find_font_first(jp_sans_fonts)
    font_name_mono    = find_font_first(jp_mono_fonts)
    font_name_program = find_font_first(jp_programming_fonts)

    tk.font.nametofont('TkDefaultFont').configure(family=font_name_mono, size=font_pt)
    tk.font.nametofont('TkMenuFont'   ).configure(family=font_name_ui,   size=font_pt)
    tk.font.nametofont('TkHeadingFont').configure(family=font_name_ui,   size=font_pt)
    tk.font.nametofont('TkCaptionFont').configure(family=font_name_ui,   size=font_pt)
    tk.font.nametofont('TkTextFont'   ).configure(family=font_name_mono, size=font_pt)
    tk.font.nametofont('TkFixedFont'  ).configure(family=font_name_mono, size=font_pt)
    
    default_font = tk.font.nametofont('TkDefaultFont')

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
    for f in tk.font.families():
        print( f, end=", " )
        font_count+=1
    print("")
    print(f"=== {font_count} fonts installed ".ljust(40,'='))
    print("\n")

def print_tkfont_info():

    for font_name in tk_font_names:
        print(f"=== {font_name} ".ljust(40, '='))

        font = tk.font.nametofont(font_name)
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

    print_all_fonts()
    print_tkfont_info()

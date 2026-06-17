#==========================================================================
# MSX Dump Editor
#--------------------------------------------------------------------------
# need python modlue: tkinterdnd2
# need font: MSX-FONT, MSX-FONT-Wide
#==========================================================================
import tkinter
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
import re
import sys
import os

APP_NAME = "MSX Dump Editor"
VERSION = "0.8.7"

IS_TEST = True # ダミーデータの有無

IS_MAC = (sys.platform == "darwin")
IS_WIN = (sys.platform == "win32")
IS_LINUX = (sys.platform == "linux")

#--------------------------------------------------------------------------
# ドラッグ＆ドロップ対応ライブラリの読み込み
DND_HELP = """
 ファイルのドラッグアンドドロップに対応するには
 tkinterdnd2 が必要です。
 インストールはコマンドコンソールから
 > pip install tkinterdnd2
"""
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False

#--------------------------------------------------------------------------
# ワンラインZ80逆アセンブラの組み込み
import z80_disAssembler as z80disAssembler
HAS_Z80DIS = True
z80disasm = z80disAssembler.z80disasm()
ASM_DELIM = ">"

#--------------------------------------------------------------------------
# フォントヘルパーの組み込み
import font_helper as fh

#--------------------------------------------------------------------------
# アセンブリビューの組み込み
import asm_view as av
from asm_view import DisAsmWindow

# HEX/ASIIエディット：フォントの高さ(px)
# フォントとサイズの組み合わせによっては機種で誤差が出る
EDIT_FONT_HEIGHT    = 16

#--------------------------------------------------------------------------
# MSX-FONTがインストールされているか調べる
MSX_FONT_HELP = """
 bugfireさんのDumpListEditorに同梱されている、
 "MSX-FONT.tff"や"MSX-FONT-Wide.tff"がインストールされていれば、
 文字表示欄がMSXフォントで表示されます。
   URL: https://bugfire2009.ojaru.jp/download.html
"""
MSX_FONT_LIST = [
    "MSX-FONT-Wide",
    "MSX-FONT"
]
MSX_FONT        = ""            # check_msx_fontで更新
HAS_MSX_FONT    = False         # check_msx_fontで更新
def check_msx_font():
    global HAS_MSX_FONT, MSX_FONT
    MSX_FONT = fh.find_font_first(MSX_FONT_LIST)
    HAS_MSX_FONT = (len(MSX_FONT) > 0)

#--------------------------------------------------------------------------
# MSX文字コード変換テーブル
# 一文字目が表示用 (for MSX-FONT.ttf by DumpListEditor)
# 2文字目以降はMSX文字コードへの変換用
ALTERNATIVE_MSX_CHAR_MAP = [
	# 00-1F : GRAPHIC文字 （╳ は SJISにない）
	"." ,"月","火","水","木","金","土","日",    "年","円","時","分","秒","百","千","万",
	"π","┴","┬","┤","├","┼","│","─",	"┌","┐","└","┘","╳×","大","中","小",
	# 20-7F : ASCII文字
	" 　","!！",'"”“',"#＃","$＄","%％","&＆","'’",	"(（",")）","*＊","+＋",",，" ,"-－",".．","/／",
	"0０","1１","2２"  ,"3３","4４","5５","6６","7７",	"8８","9９",":：",";；","<＜" ,"=＝",">＞","?？",
	"@＠","AＡ","BＢ"  ,"CＣ","DＤ","EＥ","FＦ","GＧ",	"HＨ","IＩ","JＪ","KＫ","LＬ" ,"MＭ","NＮ","OＯ",
	"PＰ","QＱ","RＲ"  ,"SＳ","TＴ","UＵ","VＶ","WＷ",	"XＸ","YＹ","ZＺ","[［","\\￥","]］","^＾","_＿",
	"`｀","aａ","bｂ"  ,"cｃ","dｄ","eｅ","fｆ","gｇ",	"hｈ","iｉ","jｊ","kｋ","lｌ" ,"mｍ","nｎ","oｏ",
	"pｐ","qｑ","rｒ"  ,"sｓ","tｔ","uｕ","vｖ","wｗ",	"xｘ","yｙ","zｚ","{｛","|｜" ,"}｝","~～","\u007F",
    
	# 80-9F ひらがな1 （トランプマーク♠♥♣♦はSJISにない）
	"♠","♥","♣","♦","○","●","を","ぁ",	"ぃ","ぅ","ぇ","ぉ","ゃ","ゅ","ょ","っ",
	"\u0090","あ","い","う","え","お","か","き",	"く","け","こ","さ","し","す","せ","そ",
	# A0-DF : カタカナ
	"\u00A0","。｡","「｢","」｣","、､","・･","ヲｦ","ァｧ",	"ィｨ","ゥｩ","ェｪ","ォｫ","ャｬ","ュｭ","ョｮ","ッｯ",
	"ーｰ"   ,"アｱ","イｲ","ウｳ","エｴ","オｵ","カｶ","キｷ",	"クｸ","ケｹ","コｺ","サｻ","シｼ","スｽ","セｾ","ソｿ",
	"タﾀ"   ,"チﾁ","ツﾂ","テﾃ","トﾄ","ナﾅ","ニﾆ","ヌﾇ",	"ネﾈ","ノﾉ","ハﾊ","ヒﾋ","フﾌ","ヘﾍ","ホﾎ","マﾏ",
	"ミﾐ"   ,"ムﾑ","メﾒ","モﾓ","ヤﾔ","ユﾕ","ヨﾖ","ラﾗ",	"リﾘ","ルﾙ","レﾚ","ロﾛ","ワﾜ","ンﾝ","゛ﾞ","゜ﾟ",
	# E0-FF ひらがな2
	"た","ち","つ","て","と","な","に","ぬ",	"ね","の","は","ひ","ふ","へ","ほ","ま",
	"み","む","め","も","や","ゆ","よ","ら",	"り","る","れ","ろ","わ","ん","\u00FE","\u00FF"
]
if not (len(ALTERNATIVE_MSX_CHAR_MAP) == 256):
    raise ValueError("ALTERNATIVE_MSX_CHAR_MAP is not 256 entries.")

# ユニコード文字からMSX文字コードを引く辞書
UNICODE_TO_MSX_DIC = {}
for i,chars in enumerate(ALTERNATIVE_MSX_CHAR_MAP):
    for c in chars:
        UNICODE_TO_MSX_DIC[c] = i

# 1文字ずつALTERNATIVE_MSX_CHAR_MAPのインデックスに変換し、bytesストリーム（バイト列）を生成
def convert_str_to_msx_characters(input_text):
    # （見つからない文字は飛ばす）
    return bytes(
        idx for char in input_text
        if (idx := UNICODE_TO_MSX_DIC.get(char)) is not None
    )

# 検索コマンド（先頭の一文字）
PRE_FIND_GO  = '>' # アドレスジャンプ >xxxxxx
PRE_FIND_BIN = '#' # バイナリサーチ   #xx xx xx
PRE_FIND_STR = '"' # 文字列サーチ     "？？？？？？
FIND_PLACEHOLDER = f"{PRE_FIND_BIN}xx xx :BIN / {PRE_FIND_STR}? :STR / {PRE_FIND_GO}xxxxx :GO"
FIND_HELP = (
    f"文字検索  ：      {PRE_FIND_STR}で始める。\n"
    f"                  例） {PRE_FIND_STR}なんのこと？\n"
    f"16進数検索：      {PRE_FIND_BIN}で始める。\n"
    f"                  16進数2文字ずつスペースで区切る。\n"
    f"                  例） {PRE_FIND_BIN}CD 24 00\n"
    f"アドレスジャンプ: {PRE_FIND_GO}で始める。\n"
    f"                  16進数（最大8文字）で指定する。\n"
    f"                  例） {PRE_FIND_GO}003FFF\n"
)


#--------------------------------------------------------------------------
# Hex Dump Editor
#--------------------------------------------------------------------------
class HexDumpEditor:
    BASE_TITLE = APP_NAME

    ADDRESS_PAD1   = 1                            # アドレスのあとの余白
    ADDRESS_DIGITS = 8                            # アドレス部の桁数
    ADDRESS_FMT    = f"0{ADDRESS_DIGITS}X"        # アドレス表示文字列フォーマット
    ADDRESS_PAD2   = 2                            # アドレスのあとの余白
    LINE_BYTES     = 16                           # 1行に表示するバイト数
    BYTES_PAD      = 1                            # バイトデータのあとの余白

    HEADER_LINES       = 1                        # ヘッダ部の行数
    EDIT_LINES_DEFAULT = 32                       # 初期表示の行数
    EDIT_LINES_MIN     = 16                       # 最小表示の行数

    COL_S_HEX      = ADDRESS_PAD1 + ADDRESS_DIGITS + ADDRESS_PAD2  # バイトデータ開始位置 (1+8+2=10)
    COL_E_HEX      = COL_S_HEX + LINE_BYTES * 3   # バイトデータ終端位置+1 (10+16*3=10+48=58)
    COL_S_ASCII    = COL_E_HEX + BYTES_PAD        # アスキー文字データ開始位置 (58+余白2=60)
    COL_E_ASCII    = COL_S_ASCII + LINE_BYTES     # アスキー文字データ終端位置+1 (60+16=76)

    BIT_FG_COLOR = "white"
    BIT_BG_COLOR = "black"
    HEX_HEADER_FG_COLOR      = "#444444"
    HEX_HEADER_BG_COLOR      = "#bbcccc"
    HEX_ADDRESS_FG_COLOR     = "#ffffff"
    HEX_ADDRESS_BG_COLOR     = "#445566"
    INSERT_MODE_FG_COLOR     = ["#ffe2b0", "#fff8f0", "#6a4423"]
    INSERT_MODE_BG_COLOR     = ["#914423", "#9a5938", "#efd2b0"]
    OVERWRITE_MODE_FG_COLOR  = ["#d0ffd0", "#d9ffe2", "#23428a"]
    OVERWRITE_MODE_BG_COLOR  = ["#2342aa", "#4060b0", "#c0d5ef"]
    INACTIVE_CURSOR_FG_COLOR = "#338833"
    INACTIVE_CURSOR_BG_COLOR = "#aabbaa"
    HEX_SELECTION_FG_COLOR   = "#000000"
    HEX_SELECTION_BG_COLOR   = "#b0e8f4"
    ASCII_CHR_FG_COLOR       = "#363f32"
    ASCII_CHR_BG_COLOR       = "#e0e0e0"
    HEX_FG_COLOR             = "#000000"
    HEX_BG_COLOR             = "#ffffff"

    DISASM_BAR_BG            = "#384440"
    DISASM_BAR_FG            = "#F0FFF0"
    NEXT_INST_HELP_FG        = "#485550"
    NEXT_INST_HELP_BG        = "#D0DDD0"


    def __init__(self, root, load_path = None):
        self.root = root

        # 画面への表示を抑制
        root.withdraw()
        
        self.current_file_path = None
        self.current_file_name = None
        
        if IS_TEST:
            self.data = bytearray(i % 256 for i in range(0x100))
        else:
            self.data = bytearray()
        
        self.APP_NAME = APP_NAME

        # 状態管理
        self.cursor           = 0     # 現在のカーソル位置
        self.anchor           = 0     # 範囲選択時のアンカー位置
        self.insert_mode      = False # 挿入モード
        self.input_mode_ascii = False # ASCII入力モード
        self.half_byte        = None  # HEX入力時、2文字中1文字目かどうか
        self.auto_scroll_id   = None  # ドラッグスクロール用タイマー
        self.drag_widget      = None  # ドラッグ中のウィジェットを保持
        self.cursor_flash     = False # カーソル点滅状態
        self.cursor_blink_id  = None  # カーソル点滅タイマーID

        # UNDO/REDP管理
        self.undo_stack = []
        self.redo_stack = []
        
        # ナビゲーション履歴
        self.nav_history = []
        self.nav_index = -1
        
        # 仮想スクロール（ページング）管理
        self.top_line = 0           # 現在Textの1行目に表示されているデータの行番号
        self.page_lines = 20        # 現在のウィンドウ高さで表示可能な行数
        self.line_height = 16       # フォントの高さ(ピクセル)

        # 子ウィンドウ
        self.log_window = None      # ログ表示ウィンドウ

        # デフォルトフォントの高さ(px)
        self.line_space = tkfont.nametofont('TkDefaultFont').metrics()['linespace'] 

        # 描画物セットアップ
        self.build_menu()
        self.build_ui()
        self.setup_text_edit_events()
        
        self.set_file_path(None)    # 初期タイトルの設定
        
        self.adjust_top_line()
        self.render()

        # 起動時引数があればロード
        if load_path:
            self.load_bin_from_path( load_path )

        self.root.update_idletasks()

        # リサイズ最小制限
        self.keep_width = self.root.winfo_width()
        self.init_height = self.root.winfo_height()
        self.root.wm_minsize(width=self.keep_width, height=self.init_height)
        self.root.wm_maxsize(width=self.keep_width, height=root.winfo_screenheight())

        raw_font = self.text_editor.cget("font")
        text_font = tkfont.Font(font=raw_font)
        default_height = self.init_height + (self.EDIT_LINES_DEFAULT-self.EDIT_LINES_MIN) * text_font.metrics("linespace")
        self.root.geometry(f"{self.keep_width}x{default_height}")

        # 左右リサイズを禁止
        self.root.resizable(False, True)

        # 表示開始
        self.root.deiconify()

        # withdraw -> deiconify でコントロールからフォーカスが外れているので
        # HEXエディットに強制フォーカス
        # focus_set() は起動・再表示直後は機能しないため focus_force()
        self.text_editor.focus_force()

        self.root.bind("<Configure>", self._force_reload_constraints)

    def _force_reload_constraints(self, event):
        """位置を動かさず、Linuxにサイズ制限を強制的に思い出させる"""
        # （ちらつくけど、有効なのはこの妥協案ぐらいしか見つからなかった）
        if event.widget == self.root:
            # 横幅が指定値から外れようとした瞬間だけ実行
            if event.width != self.keep_width or event.height < self.init_height:
                # 一瞬だけ全面リサイズ禁止に切り替える
                self.root.resizable(False, False)
                # Linuxのウィンドウマネージャに即座にルールを再計算させる
                self.root.update_idletasks()
                # 本来の設定に戻す
                self.root.resizable(False, True)

    def set_file_path(self, path):
        """ファイルパスを設定し、タイトルバーとステータスバーの表示を更新する"""
        self.current_file_path = path
        self.current_file_name = os.path.basename(path) if path else None
        
        base_title = self.BASE_TITLE
        
        if self.current_file_name:
            self.root.title(f"{base_title} - {self.current_file_name}")
        else:
            self.root.title(f"{base_title}")
            
        self.update_status()

    def build_menu(self):
        menubar = tkinter.Menu(self.root)
        
        # プラットフォーム別メニューショートカット名表示切り替え
        cmd_key_label = "Cmd+" if IS_MAC else "Ctrl+"
        quit_key_label = "Cmd+Q" if IS_MAC else "Alt+F4"
        back_key_label = "Cmd+[" if IS_MAC else "Alt+Left"
        fwd_key_label = "Cmd+]" if IS_MAC else "Alt+Right"

        # File Menu
        file_menu = tkinter.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load BIN", accelerator=f"{cmd_key_label}O", command=self.load_bin, underline=0)
        file_menu.add_command(label="Save BIN", accelerator=f"{cmd_key_label}S", command=self.save_bin, underline=0)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", accelerator=quit_key_label, command=self.quit_app, underline=0)
        menubar.add_cascade(label="File", menu=file_menu, underline=0)
        
        # Search Menu
        search_menu = tkinter.Menu(menubar, tearoff=0)
        search_menu.add_command(label="Find", accelerator=f"{cmd_key_label}F", command=self.focus_search, underline=0)
        search_menu.add_command(label="Search Current Data", accelerator=f"{cmd_key_label}F3", command=self.search_current, underline=7)
        search_menu.add_command(label="Search Next", accelerator="F3", command=self.search_next, underline=7)
        search_menu.add_command(label="Search Prev", accelerator="Shift+F3", command=self.search_prev, underline=7)
        search_menu.add_separator()
        search_menu.add_command(label="Go Address", accelerator=f"{cmd_key_label}G", command=self.focus_search_go, underline=0)
        search_menu.add_command(label="History Go Back", accelerator=back_key_label, command=self.nav_back, underline=11)
        search_menu.add_command(label="History Go Forward", accelerator=fwd_key_label, command=self.nav_forward, underline=14)
        search_menu.add_separator()
        search_menu.add_command(label="Next Z80 Instruction", accelerator="F4", command=self.next_z80inst, underline=5)
        search_menu.add_command(label="Disassemble Selection", accelerator=f"{cmd_key_label}Return", command=self.disasm_selection, underline=0)
        search_menu.add_separator()
        search_menu.add_command(label="Toggle Input (Hex/Ascii)", accelerator="F2", command=self.toggle_input_area, underline=0)

        menubar.add_cascade(label="Search", menu=search_menu, underline=0)
        
        # Help Menu
        help_menu = tkinter.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about, underline=0)
        menubar.add_cascade(label="Help", menu=help_menu, underline=0)
        
        self.root.config(menu=menubar)

    def quit_app(self, event=None):
        self.root.destroy()
        
    def show_about(self, event=None):
        title = f"About {self.BASE_TITLE}"
        message = (
            f"{self.BASE_TITLE}\n"
            f"Version {VERSION}\n"
            "\n"
            "Developed with Python & Tkinter.\n"
        )
        if HAS_DND:
            message += (
            "With optional tkinterdnd2 support.\n"
            )
        else:
            message += (
                "\n"
                "---------------------------------------------------\n"
                "[ File Drag & Drop is not Supported ]\n"
                "---------------------------------------------------"
                f"{DND_HELP}"
            )
        if HAS_MSX_FONT:
            message += (
            "\n"
            "Fonts used: ""MSX-FONT.ttf"" and ""MSX-FONT-Wide.ttf""\n"
            "provided with bugfire's DumpListEditor.\n"
            "URL: https://bugfire2009.ojaru.jp/download.html"
            )
        else:
            message += (
                "\n"
                "---------------------------------------------------\n"
                "[ MSX-FONT is not Installed ]\n"
                "---------------------------------------------------"
                f"{MSX_FONT_HELP}"
            )

        messagebox.showinfo(title, message)

    def build_ui(self):

        # フォントの定義
        # フォント本体のサイズを合わせる為、linuxではOSが追加する余白を考慮
        sans_font_name  = fh.font_name_sans
        fixed_font_name = fh.font_name_program
        if IS_WIN:
            font_style_fix = fh.get_font_with_pixel_height(self.line_space - 1, fixed_font_name)
            font_style_sans= fh.get_font_with_pixel_height(self.line_space, sans_font_name )
        else:
            font_style_fix = fh.get_font_with_pixel_height(self.line_space + 2, fixed_font_name)
            font_style_sans= fh.get_font_with_pixel_height(self.line_space - 1, sans_font_name )

        font_px_size = EDIT_FONT_HEIGHT
        if IS_WIN:
            hex_font_style = fh.get_font_with_pixel_height(font_px_size + 2, fh.font_name_program)
        else:
            hex_font_style = fh.get_font_with_pixel_height(font_px_size + 2, fh.font_name_program)
        if HAS_MSX_FONT:
            if IS_WIN:
                msx_font_style = fh.get_font_with_pixel_height(font_px_size + 0, MSX_FONT)
            else:
                msx_font_style = fh.get_font_with_pixel_height(font_px_size + 0, MSX_FONT)
        else:
            msx_font_style = hex_font_style


        #----------------------------------------
        # ツールバー
        #----------------------------------------
        toolbar = tkinter.Frame(self.root)
        toolbar.pack(side=tkinter.TOP, fill=tkinter.X, padx=5, pady=5)
        tkinter.Button(toolbar, text="Load", command=self.load_bin).pack(side=tkinter.LEFT, padx=2)
        tkinter.Button(toolbar, text="Save", command=self.save_bin).pack(side=tkinter.LEFT, padx=2)

        #----------------------------------------
        # ベースアドレス コンボボックス
        #----------------------------------------
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.map(
            "Normal.TCombobox", 
            fieldbackground=[("", "white"), ("active", "white")],
            foreground=[("", "black"), ("active", "black")],
            selectbackground=[("!focus", "white"), ("focus", "#4466AA")],
            selectforeground=[("!focus", "black"), ("focus", "white")],
        )
        self.style.map(
           "Error.TCombobox",
            fieldbackground=[("", "#ffcccc"), ("active", "#ffcccc")],
            foreground=[("", "black"), ("active", "black")],
            selectbackground=[("!focus", "#ffcccc"), ("focus", "#AA4466")],
            selectforeground=[("!focus", "black"), ("focus", "white")],
        )

        baseofs_options = [f"0x{addr:06X}" for addr in range(0, 4 * 1024 * 1024, 0x4000)]
        baseofs_max_length = len(max(baseofs_options, key=len))

        tkinter.Label(toolbar, text="Data Offset:").pack(side=tkinter.LEFT, padx=(6, 2))
        self.baseofs_combo = ttk.Combobox(toolbar
            , values=baseofs_options, state="normal"
            , width=baseofs_max_length
            , style="Normal.TCombobox"
        )
        self.baseofs_combo.pack(side=tkinter.LEFT)
        self.baseofs_combo.current(0) # 0x0000
        self.baseofs_combo.bind("<FocusOut>", self.on_baseofs_combo_focus_out)
        self.baseofs_combo.bind("<<ComboboxSelected>>", self.on_baseofs_combo_change)
        self.baseofs_combo.bind("<KeyRelease>", self.on_baseofs_combo_change)
        self.baseofs_combo.bind("<Map>", self.change_dropdown_font)

        asmbase_options = ["0x100", "0x0000", "0x4000", "0x8000", "0xC000"]
        asmbase_max_length = len(max(asmbase_options, key=len))

        tkinter.Label(toolbar, text="-> Asm:").pack(side=tkinter.LEFT, padx=(2, 2))
        self.asmbase_combo = ttk.Combobox(toolbar
            , values=asmbase_options, state="normal"
            , width=asmbase_max_length
            , style="Normal.TCombobox"
        )
        self.asmbase_combo.pack(side=tkinter.LEFT)
        self.asmbase_combo.current(2) # 0x4000
        self.asmbase_combo.bind("<FocusOut>", self.on_asmbase_combo_focus_out)
        self.asmbase_combo.bind("<<ComboboxSelected>>", self.on_asmbase_combo_change)
        self.asmbase_combo.bind("<KeyRelease>", self.on_asmbase_combo_change)
        self.asmbase_combo.bind("<Map>", self.change_dropdown_font)

        #----------------------------------------
        # 検索ボックス
        #----------------------------------------
        search_frame = tkinter.Frame(toolbar)
        search_frame.pack(side=tkinter.RIGHT, padx=5)
        tkinter.Label(search_frame, text="Search:").pack(side=tkinter.LEFT, padx=(6, 2))
        
        self.search_var = tkinter.StringVar()
        self.search_entry = tkinter.Entry(search_frame, textvariable=self.search_var, width=35, font=font_style_fix)
        self.search_entry.pack(side=tkinter.LEFT)
        self.search_entry.bind("<Return>", self.search_decide)
        self.search_entry.bind("<Shift-Return>", self.search_decide)
        self.search_entry.bind("<Escape>", self.focus_set_editor)
        
        # プレースホルダーの設定
        self.placeholder_text = FIND_PLACEHOLDER
        self.default_fg_color = self.search_entry.cget("fg")
        self.search_entry.insert(0, self.placeholder_text)
        self.search_entry.config(fg="gray")
        self.search_entry.bind("<FocusIn>", self.on_search_focus_in)
        self.search_entry.bind("<FocusOut>", self.on_search_focus_out)
        
        #----------------------------------------
        # HEXビュー
        #----------------------------------------
        # ヘッダー
        header_str_address = "Address:"
        header_str_bytes   = "".join([f"+{i:X} " for i in range(self.LINE_BYTES)])
        #                    "+0 +1 +2 +3 +4 +5 +6 +7 +8 +9 +A +B +C +D +E +F "
        header_str_ascii   = MSX_FONT if HAS_MSX_FONT else "Ascii"
        
        header_str = (
            f"{' ' * self.ADDRESS_PAD1}{header_str_address}"
            f"{' ' * self.ADDRESS_PAD2}{header_str_bytes}"
            f"{' ' * self.BYTES_PAD}{header_str_ascii}"
        )
        
        ascii_width = msx_font_style.measure("0" * (self.LINE_BYTES))
        hex_font_base = hex_font_style.measure("0")
        text_edit_width = self.COL_S_ASCII + ((ascii_width + hex_font_base - 1) // hex_font_base)

        editor_parent = tkinter.Frame(self.root, bd=2, relief=tkinter.SUNKEN)
        editor_parent.pack(side=tkinter.TOP, fill=tkinter.Y, expand=True, padx=5, pady=0)

        self.header = tkinter.Label(editor_parent
            , font=hex_font_style
            , width=text_edit_width
            , height=1
            , bd=0, highlightthickness=0
            , bg=self.HEX_HEADER_BG_COLOR #self.root.cget('bg')
            , fg=self.HEX_HEADER_FG_COLOR
            , text=header_str
            , anchor="w"
            , pady=2
        )
        self.header.grid(row=0, column=0, sticky="ew", padx=2, pady=0)

        # ビュー設定 (HexとASCIIを1つのTextで表示)
        self.line_height = hex_font_style.metrics("linespace") # フォントの実際の高さを記憶
        self.text_editor = tkinter.Text(editor_parent
            , font=hex_font_style
            , width=text_edit_width
            , height=self.EDIT_LINES_MIN
            , bd=0, highlightthickness=0
            , undo=False
            , exportselection=False
            , wrap=tkinter.NONE
            , bg=self.HEX_BG_COLOR
            , fg=self.HEX_FG_COLOR
            , pady=0
        )
        self.text_editor.grid(row=1, column=0, sticky="nsew", padx=2, pady=(0,2))
        
        # 仮想スクロールバー
        # Textコントロールにデータをすべて入れると重すぎるので
        # 見えている範囲だけレンダリングする方式
        def virtual_scroll(*args):
            total_lines = (len(self.data) // self.LINE_BYTES) + 1
            if args[0] == "moveto":
                self.top_line = int(float(args[1]) * total_lines)
            elif args[0] == "scroll":
                delta = int(args[1])
                if args[2] == "units":
                    self.top_line += delta
                elif args[2] == "pages":
                    self.top_line += delta * max(1, self.page_lines - 1)
            self.top_line = max(0, min(self.top_line, total_lines - 1))
            self.render()

        self.scrollbar = tkinter.Scrollbar(editor_parent, command=virtual_scroll, takefocus=False)
        self.scrollbar.grid(row=1, column=1, sticky="ns")
        
        editor_parent.columnconfigure(0, weight=1)
        editor_parent.columnconfigure(1, weight=0)
        editor_parent.rowconfigure(1, weight=1)
        
        # タグ設定 (システム予約の"sel"を捨てて独自タグを使用)
        self.text_editor.tag_configure("hex_selection", background=self.HEX_SELECTION_BG_COLOR, foreground=self.HEX_SELECTION_FG_COLOR)
        self.text_editor.tag_configure("hex_cursor", background=self.OVERWRITE_MODE_BG_COLOR[0], foreground=self.OVERWRITE_MODE_FG_COLOR[0])
        self.text_editor.tag_configure("ascii_cursor", background=self.INACTIVE_CURSOR_BG_COLOR, foreground=self.INACTIVE_CURSOR_FG_COLOR)
        # ASCII文字部分に対するMSXフォントタグ
        self.text_editor.tag_configure("msx_font", font=msx_font_style, background=self.ASCII_CHR_BG_COLOR, foreground=self.ASCII_CHR_FG_COLOR)
        # アドレス表示部の色指定タグ
        self.text_editor.tag_configure("address", background=self.HEX_ADDRESS_BG_COLOR, foreground=self.HEX_ADDRESS_FG_COLOR)
        
        # 重なり順の指定 (後からraiseされたものが優先)
        self.text_editor.tag_raise("address")
        self.text_editor.tag_raise("msx_font")
        self.text_editor.tag_raise("hex_selection")
        self.text_editor.tag_raise("hex_cursor")
        self.text_editor.tag_raise("ascii_cursor")
        
        #----------------------------------------
        # ステータスバー
        #----------------------------------------
        status_frame = tkinter.Frame(self.root)
        status_frame.pack(side=tkinter.BOTTOM, fill=tkinter.X)

        # 左側
        left_frame = tkinter.Frame(status_frame)
        left_frame.pack(side=tkinter.LEFT, padx=2, pady=1, fill=tkinter.X, expand=True)

        # 左側の上から1つ目：コンテナ
        status_bar_frame = tkinter.Frame(left_frame, bd=0)
        status_bar_frame.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True, pady=0, padx=2)

        # 左側の上から1つ目 の 左から1つ目：位置
        self.status_pos_var = tkinter.StringVar()
        status_pos_label = tkinter.Label(status_bar_frame, textvariable=self.status_pos_var
            , width=28 ,anchor=tkinter.W, justify=tkinter.LEFT, bd=1, relief=tkinter.GROOVE, font=font_style_fix)
        status_pos_label.pack(side=tkinter.LEFT, fill=tkinter.BOTH, pady=0, padx=0)

        # 左側の上から1つ目 の 左から2つ目：選択範囲
        self.status_sel_var = tkinter.StringVar()
        status_sel_label = tkinter.Label(status_bar_frame, textvariable=self.status_sel_var
            , width=18 ,anchor=tkinter.W, justify=tkinter.LEFT, bd=1, relief=tkinter.GROOVE, font=font_style_sans)
        status_sel_label.pack(side=tkinter.LEFT, fill=tkinter.BOTH, pady=0, padx=0)

        # 左側の上から1つ目 の 右から1つ目：上書き/挿入/入力モード
        self.status_mode_var = tkinter.StringVar()
        status_mode_label = tkinter.Label(status_bar_frame, textvariable=self.status_mode_var
            , width=14 ,anchor=tkinter.CENTER, justify=tkinter.CENTER, bd=1, relief=tkinter.GROOVE, font=font_style_sans)
        status_mode_label.pack(side=tkinter.RIGHT, fill=tkinter.BOTH, pady=0, padx=0)

        # 左側の上から1つ目 の 右から2つ目：合計サイズ
        self.status_total_var = tkinter.StringVar()
        status_total_label = tkinter.Label(status_bar_frame, textvariable=self.status_total_var
            , width=18 ,anchor=tkinter.W, justify=tkinter.LEFT, bd=1, relief=tkinter.GROOVE, font=font_style_sans)
        status_total_label.pack(side=tkinter.RIGHT, fill=tkinter.BOTH, pady=0, padx=0)

        # 左側の上から2つ目：逆アセンブラ
        disasm_bar_frame = tkinter.Frame(left_frame, bd=0)
        disasm_bar_frame.pack(side=tkinter.TOP, fill=tkinter.X, expand=True, pady=0, padx=0)
        self.disasm_var = tkinter.StringVar()
        self.disasm_label = tkinter.Entry(disasm_bar_frame, textvariable=self.disasm_var
            , width=5+8+2+(2*4+3)+3+23+12
            , bd=1, relief=tkinter.GROOVE
            , font=font_style_fix
            , highlightthickness=0
            , exportselection=False
            , state="readonly"
            , takefocus=False
            , readonlybackground=self.DISASM_BAR_BG, fg=self.DISASM_BAR_FG
        )
        self.disasm_label.pack(side=tkinter.LEFT,  anchor=tkinter.W
            , fill=tkinter.X, expand=True
            , pady=0, padx=0
        )
        #self.disasm_label.bind("<FocusIn>", self.block_focus)
        tkinter.Label(disasm_bar_frame, text=" [Enter]/[F4]:次の命令へ "
            , fg=self.NEXT_INST_HELP_FG, bg=self.NEXT_INST_HELP_BG
            , bd=1, relief=tkinter.GROOVE, font=font_style_sans
        ).pack(side=tkinter.LEFT, pady=0, padx=(0, 2))

        # 左側の上から3つ目：ファイルパス
        self.info_var = tkinter.StringVar()
        self.info_label = tkinter.Label(left_frame, textvariable=self.info_var, anchor=tkinter.W, justify=tkinter.LEFT
            , bd=1, relief=tkinter.GROOVE, font=font_style_sans)
        self.info_label.pack(side=tkinter.TOP, fill=tkinter.X, expand=True, pady=(0,2), padx=2)

        # 16x16 ビットパターン表示用 Canvas（1ドット=3x3ピクセルで描画）
        self.bit_cell_size = 3
        canvas_size = 16 * self.bit_cell_size
        self.bit_canvas = tkinter.Canvas(status_frame, width=canvas_size, height=canvas_size, bg="white", highlightthickness=0)
        self.bit_canvas.pack(side=tkinter.RIGHT, padx=6, pady=(0,4))
        
        # スプライトビュー
        # 16x16の矩形オブジェクトをあらかじめ作成しておく
        self.bit_rects = []
        for row in range(16):
            row_rects = []
            for col in range(16):
                x1 = col * self.bit_cell_size
                y1 = row * self.bit_cell_size
                x2 = x1 + self.bit_cell_size
                y2 = y1 + self.bit_cell_size
                # 枠線(outline)なしで塗りつぶしのみ
                r = self.bit_canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="")
                row_rects.append(r)
            self.bit_rects.append(row_rects)
        
        self.text_editor.focus_set()
        self.text_editor.config(state=tkinter.DISABLED)

    # ドロップダウンリストのフォント変更
    def change_dropdown_font(self, event):
        font = event.widget.cget('font')
        popdown = self.root.tk.eval(f"ttk::combobox::PopdownWindow {event.widget}")
        self.root.tk.call(f"{popdown}.f.l", "configure", "-font", font)
        
    ## takefocus=Falseをすり抜ける現象対策
    #def block_focus(self, event):
    #    if event.state & 4: # Shift key
    #        event.widget.tk_focusPrev().focus_set()
    #    else:
    #        event.widget.tk_focusNext().focus_set()
    #    return "break"

    def set_input_mode(self, is_ascii):
        """HEX入力とASCII入力のフォーカスを切り替える"""
        if self.input_mode_ascii != is_ascii:
            self.commit_half_byte_if_needed()
            self.input_mode_ascii = is_ascii
            self.blink_cursor_stop()
            self.set_cursor_color()
            self.update_status()
            self.blink_cursor()

    def get_baseofs(self):
        user_input = self.baseofs_combo.get()
        try:
            address_int = int(user_input, 16)
            self.baseofs_combo.config(style="Normal.TCombobox")
        except ValueError:
            self.baseofs_combo.config(style="Error.TCombobox")
            address_int = 0
        return address_int

    def on_baseofs_combo_focus_out(self, event=None):
        self.get_baseofs()
        self.update_status()

    def on_baseofs_combo_change(self, event=None):
        self.get_baseofs()
        self.update_status()

    def get_asmbase(self):
        """ asmbase_combo からベースアドレス（16進数）を取得する """
        user_input = self.asmbase_combo.get()
        try:
            address_int = int(user_input, 16)
            self.asmbase_combo.config(style="Normal.TCombobox")
        except ValueError:
            self.asmbase_combo.config(style="Error.TCombobox")
            address_int = 0
        return address_int

    def on_asmbase_combo_focus_out(self, event=None):
        self.get_asmbase()
        self.update_status()

    def on_asmbase_combo_change(self, event=None):
        self.get_asmbase()
        self.update_status()

    def set_placeholder(self):
        """検索ボックスからフォーカスが外れた時、空ならプレースホルダーを表示する"""
        if not self.search_var.get():
            self.search_entry.insert(0, self.placeholder_text)
            self.search_entry.config(fg="gray")
            self.search_entry.icursor(0)

    def off_placeholder(self):
        """検索ボックスのプレースホルダーを消す"""
        if self.search_var.get() == self.placeholder_text:
            self.search_entry.delete(0, tkinter.END)
            self.search_entry.config(fg=self.default_fg_color)

    def on_search_focus_in(self, event):
        """検索ボックスにフォーカスが当たった時、プレースホルダーを消す"""
        self.off_placeholder()

    def on_search_focus_out(self, event):
        """検索ボックスからフォーカスが外れた時、空ならプレースホルダーを表示する"""
        self.set_placeholder()

    def focus_search_go(self, event=None):
        """検索ボックスにフォーカスを移動してPRE_FIND_GOを入力"""
        self.search_entry.focus_set()
        self.off_placeholder()

        str = PRE_FIND_GO
        maxpos = len(self.data) - 1
        hex_str = ""
        if abs(min(maxpos, self.cursor) - min(maxpos, self.anchor)) == 1:
            # 2バイト選択状態ならその値をセット
            hex = self.get_selected_hex().split(" ", 1)
            if len(hex) == 2:
                hex_str = f"{hex[1]}{hex[0]}"
        else:
            # 逆アセンブラ欄に16進数文字列があればそれもセット
            disasm_parts = self.disasm_var.get().split(ASM_DELIM,1)
            if len(disasm_parts) == 2:
                if adr_str := re.search(r"([0-9A-Fa-f]{4,})H", disasm_parts[1]):
                    hex_str = adr_str.group(1)
        if len(hex_str):
            adr = int(hex_str, 16)
            adr -= self.get_address_offset()
            if 0 <= adr: # < len(self.data) :
                str += f"{adr:08X}"

        self.search_var.set(str)
        self.search_entry.icursor(tkinter.END)
    
    def focus_set_editor(self, event=None):
        self.text_editor.focus_set()

    def focus_search(self, event=None):
        """検索ボックスにフォーカスを移動"""
        self.search_entry.focus_set()
        str = self.search_var.get()
        # プレースホルダーでなければ
        if str != self.placeholder_text:
            # ジャンプモードならクリアする
            if str[:1] == PRE_FIND_GO:
                self.search_entry.delete(0, tkinter.END)
            # 文字列があれば全選択する
            else:
                self.search_entry.select_range(0, tkinter.END)

    def search_current(self, event=None):
        """現在位置の値を拾って次の結果を検索"""
        hex = self.get_selected_hex()
        if len(hex) == 0:
            return "break" # 範囲外

        self.search_entry.focus_set()
        self.off_placeholder()

        self.search_var.set("#" + hex)
        self.search_entry.icursor(tkinter.END)
        if event:
            shift = (event.state & 0x0001) != 0
            if shift:
                return self._execute_search(forward=False)
        return self._execute_search(forward=True)

    def search_decide(self, event=None):
        # 入力が空ならHEXエディットへフォーカス遷移
        if len(self.search_var.get()) == 0:
            self.text_editor.focus_set()
            return "break"
        return self.search_next(event)

    def search_next(self, event=None):
        """現在位置から次の結果を検索"""
        # 検索エディットがプレースホルダーであれば現在の選択データを検索
        if self.search_var.get() == self.placeholder_text:
            return self.search_current(event)
        return self._execute_search(forward=True)

    def search_prev(self, event=None):
        """現在位置から前の結果を検索"""
        return self._execute_search(forward=False)

    def _execute_search(self, forward=True):
        """検索のコア処理（forward=Trueで順方向、Falseで逆方向）"""
        query = self.search_var.get()

        # 未入力またはプレースホルダー状態の場合は検索しない
        if not query or query == self.placeholder_text:
            return "break"
        
        search_bytes = None
        ascii_search = False
        show_find_help = False

        try:
            if query.startswith(PRE_FIND_GO):
                # 2文字以上で1文字目がPRE_FIND_GOの場合はアドレスジャンプ
                hex_str = query[1:].strip()
                if hex_str:
                    jump_addr = int(hex_str, 16)
                    
                    # アドレスの範囲をデータサイズ内に制限
                    if jump_addr < 0:
                        jump_addr = 0
                    elif jump_addr > len(self.data):
                        jump_addr = len(self.data)
                        
                    self.commit_half_byte_if_needed()
                    
                    # ナビゲーション履歴の保存（ジャンプ前）
                    self.save_nav_history_before_jump()
                    self.cursor = self.anchor = jump_addr
                    
                    # 画面をスクロールしてカーソル位置を更新
                    if not self.ensure_cursor_visible():
                        self.update_cursor_display()
                        
                    # ナビゲーション履歴の保存（ジャンプ後）
                    self.save_nav_history_after_jump()
                    
                    # HEXエディットにフォーカスを移動
                    self.text_editor.focus_set()
                    return "break"
                #else:
                #    #ascii_search = True
                #    show_find_help = True

            elif query.startswith(PRE_FIND_BIN):
                # 2文字以上で1文字目が{PRE_FIND_BIN}の場合は16進数バイナリ検索（スペース区切り）
                hex_str = query[1:].strip()
                if hex_str:
                    search_bytes = bytearray(int(x, 16) for x in hex_str.split())
                #else:
                #    #ascii_search = True
                #    show_find_help = True

            elif query.startswith(PRE_FIND_STR):
                # 2文字以上で1文字目が{PRE_FIND_STR}の場合は文字検索
                query = query[1:]
                ascii_search = True

            else: 
                #ascii_search = True
                show_find_help = True

        except ValueError:
            if query.startswith(PRE_FIND_GO):
                #messagebox.showwarning("ジャンプエラー", "アドレス指定にエラーがあります。\n例） {PRE_FIND_GO}01FA")
                pass
            elif query.startswith(PRE_FIND_BIN):
                #messagebox.showwarning("検索エラー", f"バイトデータ指定にエラーがあります\n例） {PRE_FIND_BIN}1A 2B 3C")
                pass
            #ascii_search = True
            show_find_help = True

        if ascii_search:
            # ASCII文字列検索
            search_bytes = convert_str_to_msx_characters( query )
            if len(search_bytes) != len(query):
            #try:
            #    search_bytes = query.encode('ascii')
            #except (ValueError, UnicodeEncodeError):
                messagebox.showwarning("検索エラー", "検索に使用できない文字があります。")
                return "break"
            
        if show_find_help:
            messagebox.showinfo("検索ガイド", FIND_HELP)
            return "break"
        
        if not search_bytes:
            return "break"
            
        self.commit_half_byte_if_needed()
        
        # 検索開始位置の設定
        start_pos = min(self.cursor, self.anchor)
        sel_len = abs(self.cursor - self.anchor) + 1
        
        hit_pos = -1

        if forward:
            # === 順方向検索 (Next) ===
            # 現在選択している部分が検索文字列と一致する場合、その次から検索を開始する
            if sel_len == len(search_bytes):
                if self.data[start_pos:start_pos+sel_len] == search_bytes:
                    start_pos += 1
                    
            hit_pos = self.data.find(search_bytes, start_pos)
            if hit_pos == -1:
                # 見つからなかった場合は先頭からラップアラウンド検索
                hit_pos = self.data.find(search_bytes, 0)
        else:
            # === 逆方向検索 (Prev) ===
            # 現在の選択開始位置より「前」を検索対象とする
            hit_pos = self.data.rfind(search_bytes, 0, start_pos)
            if hit_pos == -1:
                # 見つからなかった場合は末尾からラップアラウンド検索
                hit_pos = self.data.rfind(search_bytes)

        # 検索結果の判定とUI更新
        if hit_pos == -1:
            messagebox.showinfo("Search", "Not found.")
            return "break"
                
        # ヒットした領域を選択状態にする
        self.save_nav_history_before_jump()
        self.anchor = hit_pos
        self.cursor = hit_pos + len(search_bytes) - 1
        if not self.ensure_cursor_visible():
            self.update_cursor_display()
        self.save_nav_history_after_jump()

        # HEXエディットにフォーカスを移動
        self.text_editor.focus_set()
        return "break"

    def next_z80inst(self):
        self.navigate("F4", False, False)
        return "break"

    def setup_text_edit_events(self):
        """Textウィジェットのデフォルト動作をすべて排除して自前でコントロールする"""
        bindtags = list(self.text_editor.bindtags())
        if "Text" in bindtags:
            bindtags.remove("Text")
        self.text_editor.bindtags(tuple(bindtags))

        # フォーカスイベント
        self.text_editor.bind("<FocusIn>", self.on_text_editor_focus_in)
        self.text_editor.bind("<FocusOut>", self.on_text_editor_focus_out)

        # マウスイベントを直接バインド
        self.text_editor.bind("<Button-1>", self.on_text_editor_click)
        self.text_editor.bind("<Shift-Button-1>", self.on_text_editor_shift_click)
        self.text_editor.bind("<B1-Motion>", self.on_text_editor_drag)
        self.text_editor.bind("<ButtonRelease-1>", self.on_text_editor_btn_release)
        
        # クラスバインディングを消したため、マウスホイールも自前でバインド
        self.text_editor.bind("<MouseWheel>", self.on_text_editor_mouse_whee)
        self.text_editor.bind("<Button-4>", self.on_text_editor_mouse_whee)
        self.text_editor.bind("<Button-5>", self.on_text_editor_mouse_whee)
        
         # ウィンドウリサイズ時の行数再計算
        self.text_editor.bind("<Configure>", self.on_text_editor_resize)

        # TAB でのHEX編集←→ASCII編集遷移の為
        self.text_editor.bind("<Tab>", self.handle_tab)
        self.text_editor.bind("<Shift-Tab>", self.handle_shift_tab)
        self.text_editor.bind("<Shift-ISO_Left_Tab>", self.handle_shift_tab)
            
        self.root.bind("<Key>", self.dispatch_key_event)
        
        # プラットフォームに合わせたシステムレベル終了キーバインド
        if IS_MAC:
            self.root.bind("<Command-q>", self.quit_app)
            self.root.bind("<Command-w>", self.quit_app)
        else:
            self.root.bind("<Alt-F4>", self.quit_app)

        # ドラッグ＆ドロップイベントのバインド
        if HAS_DND:
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.on_file_drop)

    def on_text_editor_resize(self, event):
        """ウィンドウリサイズ時に、1画面に表示可能な行数を計算し直す"""
        if self.line_height > 0:
            new_page_lines = max(1, event.height // self.line_height)
            if new_page_lines != self.page_lines:
                self.page_lines = new_page_lines
                self.adjust_top_line()
                self.render()

    def on_file_drop(self, event):
        """ファイルがドロップされたときの処理"""
        # tkinterdnd2 は複数ファイルの場合にスペース等で区切って返すため、Tk の splitlist で安全に分割
        files = self.root.tk.splitlist(event.data)
        if files:
            # ドロップされたファイルのうち、最初の1ファイルをバイナリとして読み込む
            self.load_bin_from_path(files[0])

    def get_index_from_mouse(self, widget, x, y):
        """座標からデータの絶対インデックスを逆算"""
        pos = widget.index(f"@{x},{y}")
        text_line, col = map(int, pos.split('.'))
        
        # Text上の行番号に、現在見えている先頭行(top_line)のオフセットを足す
        data_line = self.top_line + text_line - 1
        addr = data_line * self.LINE_BYTES
        
        # 列位置からオフセットを計算
        if col < self.COL_S_HEX:             
            offset = 0
        elif self.COL_S_HEX <= col < self.COL_E_HEX:         
            offset = (col - self.COL_S_HEX) // 3
        elif self.COL_E_HEX <= col < self.COL_S_ASCII:
            offset = 15 # HexとASCIIの間の隙間をクリックした場合は末尾のバイトへ
        elif self.COL_S_ASCII <= col < self.COL_E_ASCII:       
            offset = col - self.COL_S_ASCII
        else:
            offset = 15
            
        new_pos = addr + offset
        return max(0, min(len(self.data), new_pos))

    def on_text_editor_focus_in(self, event):
        self.blink_cursor()
        self.text_editor.config(state=tkinter.DISABLED)

    def on_text_editor_focus_out(self, event):
        self.blink_cursor_stop()
        if self.commit_half_byte_if_needed(): self.render()
        self.text_editor.config(state=tkinter.NORMAL)

    # --- マウス操作と自前の自動スクロール制御 ---
    #     (組み込みの自動スクロールを回避)
    def on_text_editor_click(self, event):
        event.widget.focus_set()
        self.stop_auto_scroll()
        
        # クリック位置から列を特定して入力フォーカスモードを切り替え
        pos = event.widget.index(f"@{event.x},{event.y}")
        _, col = map(int, pos.split('.'))
        if self.COL_S_ASCII <= col < self.COL_E_ASCII:
            self.set_input_mode(True)
        elif self.COL_S_HEX <= col < self.COL_E_HEX:
            self.set_input_mode(False)

        if self.commit_half_byte_if_needed():
            self.render()
        new_pos = self.get_index_from_mouse(event.widget, event.x, event.y)
        self.cursor = self.anchor = new_pos
        self.drag_widget = event.widget
        if not self.ensure_cursor_visible():
            self.update_cursor_display()
        return "break"

    def on_text_editor_shift_click(self, event):
        event.widget.focus_set()
        self.stop_auto_scroll()
        
        # クリック位置から列を特定して入力フォーカスモードを切り替え
        pos = event.widget.index(f"@{event.x},{event.y}")
        _, col = map(int, pos.split('.'))
        if self.COL_S_ASCII <= col < self.COL_E_ASCII:
            self.set_input_mode(True)
        elif self.COL_S_HEX <= col < self.COL_E_HEX:
            self.set_input_mode(False)

        if self.commit_half_byte_if_needed():
            self.render()
        self.drag_widget = event.widget
        self.cursor = self.get_index_from_mouse(event.widget, event.x, event.y)
        if not self.ensure_cursor_visible():
            self.update_cursor_display()
        return "break"

    def on_text_editor_drag(self, event):
        self.drag_widget = event.widget
        self.update_drag_selection(event.widget, event.x, event.y)
        self.check_auto_scroll(event.y)
        return "break"

    def on_text_editor_btn_release(self, event):
        self.stop_auto_scroll()
        self.drag_widget = None
        return "break"

    def update_drag_selection(self, widget, x, y):
        new_pos = self.get_index_from_mouse(widget, x, y)
        if self.cursor != new_pos:
            self.cursor = new_pos
            if not self.ensure_cursor_visible():
                self.update_cursor_display()

    def check_auto_scroll(self, y):
        self.stop_auto_scroll()
        if not self.drag_widget: return
        if y < 0:
            self.auto_scroll(-1, y)
        elif y > self.drag_widget.winfo_height():
            self.auto_scroll(1, y)

    def auto_scroll(self, direction, y):
        """画面外にドラッグした際、選択範囲を更新しながら自前でスクロールし続ける"""
        if not self.drag_widget: return
        
        old_top = self.top_line
        self.top_line += direction
        total_lines = (len(self.data) // self.LINE_BYTES) + 1
        self.top_line = max(0, min(self.top_line, total_lines - 1))
        
        x = self.drag_widget.winfo_pointerx() - self.drag_widget.winfo_rootx()
        self.update_drag_selection(self.drag_widget, x, y)
        
        if self.top_line != old_top:
            self.render()
            
        self.auto_scroll_id = self.root.after(50, self.auto_scroll, direction, y)

    def stop_auto_scroll(self):
        if self.auto_scroll_id:
            self.root.after_cancel(self.auto_scroll_id)
            self.auto_scroll_id = None

    def on_text_editor_mouse_whee(self, event):
        # Linux (event.num が 4 または 5 として届く)
        if hasattr(event, 'num') and event.num != '??':
            delta = -1 if event.num == 4 else 1
            scroll_lines = 3
            
        # macOS (MouseWheel)
        elif IS_MAC:
            raw_delta = event.delta
            delta = -1 if raw_delta > 0 else 1
            scroll_lines = max(1, int(abs(raw_delta)))
            
        # Windows (MouseWheel)
        else:
            raw_delta = event.delta
            delta = -1 if raw_delta > 0 else 1
            scroll_lines = max(1, int(abs(raw_delta) / 40))
                                
        # 仮想スクロール位置を更新
        self.top_line += delta * scroll_lines
        total_lines = (len(self.data) // self.LINE_BYTES) + 1
        self.top_line = max(0, min(self.top_line, total_lines - 1))
        self.render()
        return "break"

    def update_cursor_display(self):
        self.apply_tags()
        self.update_status()

    def adjust_top_line(self):
        """カーソル位置が含まれるように top_line を調整する"""
        data_line = self.cursor // self.LINE_BYTES
        if data_line < self.top_line:
            self.top_line = data_line
        elif data_line >= self.top_line + max(1, self.page_lines - 1):
            self.top_line = data_line - max(1, self.page_lines - 1) + 1

    def ensure_cursor_visible(self):
        """カーソルが見える位置までビューを移動(必要なら再描画してTrueを返す)"""
        old_top = self.top_line
        self.adjust_top_line()
        if old_top != self.top_line:
            self.render()
            return True
        return False

    def set_cursor_color(self, is_focus = None):
        if is_focus is None:
            is_focus = bool(self.root.focus_get() != self.text_editor)

        i = 1 if self.cursor_flash else 0
        if self.insert_mode: 
            fg_color = self.INSERT_MODE_FG_COLOR[i] 
            bg_color = self.INSERT_MODE_BG_COLOR[i]
        else:
            fg_color = self.OVERWRITE_MODE_FG_COLOR[i]
            bg_color = self.OVERWRITE_MODE_BG_COLOR[i]
            
        inactive_fg = self.INACTIVE_CURSOR_FG_COLOR
        inactive_bg = self.INACTIVE_CURSOR_BG_COLOR

        if not is_focus:
            self.text_editor.tag_configure("ascii_cursor", background=inactive_bg, foreground=inactive_fg)
            self.text_editor.tag_configure("hex_cursor", background=inactive_bg, foreground=inactive_fg)
        elif self.input_mode_ascii:
            self.text_editor.tag_configure("ascii_cursor", background=bg_color, foreground=fg_color)
            self.text_editor.tag_configure("hex_cursor", background=inactive_bg, foreground=inactive_fg)
        else:
            self.text_editor.tag_configure("hex_cursor", background=bg_color, foreground=fg_color)
            self.text_editor.tag_configure("ascii_cursor", background=inactive_bg, foreground=inactive_fg)

    def blink_cursor(self):
        self.cursor_flash = not self.cursor_flash
        self.set_cursor_color( True )

        interval = 1000 if self.cursor_flash else 500
        self.cursor_blink_id = self.root.after(interval, self.blink_cursor)

    def blink_cursor_stop(self):
        if self.cursor_blink_id is not None:
            self.root.after_cancel(self.cursor_blink_id)
            self.cursor_blink_id = None
            self.cursor_flash = False

        self.set_cursor_color( False )

    def render(self):
        # アドレスやASCII文字列付きDumpリストの表示 (仮想スクロール用)
        total_lines = (len(self.data) // self.LINE_BYTES) + 1
        
        # データが削除されるなどして top_line が範囲外になった場合の補正
        if self.top_line >= total_lines:
            self.top_line = total_lines - 1

        start_line = self.top_line
        end_line = min(total_lines, self.top_line + self.page_lines)

        self.text_editor.config(state=tkinter.NORMAL)
        self.text_editor.delete("1.0", tkinter.END)
        
        content = []
        
        # 必要な行（画面に見える数十行）だけをループして文字列構築
        for row in range(start_line, end_line):
            addr = row * self.LINE_BYTES
            row_hex = ""
            row_ascii = ""
            for col in range(self.LINE_BYTES):
                idx = addr + col
                if idx < len(self.data):
                    if idx == self.cursor and self.half_byte is not None:
                        row_hex += f"{self.half_byte}  "
                    else:
                        row_hex += f"{self.data[idx]:02X} "
                    c = self.data[idx]
                    if HAS_MSX_FONT:
                        row_ascii += ALTERNATIVE_MSX_CHAR_MAP[c][0]
                    else:
                        row_ascii += chr(c) if 0x20 <= c <= 0x7E else "."
                elif idx == len(self.data):
                    row_hex += f"{self.half_byte}  " if idx == self.cursor and self.half_byte is not None else "?? "
                    row_ascii += " "
                else:
                    row_hex += "   "
                    row_ascii += " "
                    
            content.append(
                f"{' ' * self.ADDRESS_PAD1}{addr:{self.ADDRESS_FMT}}"
                f"{' ' * self.ADDRESS_PAD2}{row_hex}"
                f"{' ' * self.BYTES_PAD}{row_ascii}"
            )
            
        self.text_editor.insert("1.0", "\n".join(content))
        if self.root.focus_get() == self.text_editor: 
            self.text_editor.config(state=tkinter.DISABLED)

        # 仮想スクロールバーのノブ位置更新
        first = start_line / total_lines
        last = min(1.0, (start_line + self.page_lines) / total_lines)
        self.scrollbar.set(first, last)

        # 色付け・MSXフォントタグ付与など
        self.apply_tags(end_line - start_line)

        # ステータスバー更新
        self.update_status()

    def apply_tags(self, visible_lines_count=None):
        """
         テキストの色処理およびMSXフォント適用 ：
        【ちらつき抑制描画】PythonからTclへスクリプトを一括送信し瞬時切り替える
        """
        start, end = min(self.cursor, self.anchor), max(self.cursor, self.anchor)
        data_len = len(self.data)

        # 選択範囲の色付け
        sel_ranges = []
        
        visible_start_idx = self.top_line * self.LINE_BYTES
        visible_end_idx = (self.top_line + self.page_lines) * self.LINE_BYTES - 1
        
        # 画面に見えている範囲のみタグ計算する
        draw_start = max(start, visible_start_idx)
        draw_end = min(end, visible_end_idx, data_len)

        hex_sel_size = 3
        for i in range(draw_start, draw_end + 1):
            data_line = i // self.LINE_BYTES
            text_line = data_line - self.top_line + 1 # Text上の行番号(1～)
            if text_line < 1: continue
            
            col_hex = self.COL_S_HEX + (i % self.LINE_BYTES) * 3
            col_ascii = self.COL_S_ASCII + (i % self.LINE_BYTES)
            
            if draw_end <= i: hex_sel_size = 2
            sel_ranges.extend([
                f"{text_line}.{col_hex}", f"{text_line}.{col_hex+hex_sel_size}"
            ])
            if i < data_len:
                sel_ranges.extend([
                    f"{text_line}.{col_ascii}", f"{text_line}.{col_ascii+1}"
                ])

        # カーソル位置の色付け
        hex_cursor_ranges = []
        ascii_cursor_ranges = []
        if visible_start_idx <= self.cursor <= visible_end_idx:
            data_line = self.cursor // self.LINE_BYTES
            text_line = data_line - self.top_line + 1
            col_hex = self.COL_S_HEX + (self.cursor % self.LINE_BYTES) * 3
            col_ascii = self.COL_S_ASCII + (self.cursor % self.LINE_BYTES)
            
            if self.cursor <= data_len:
                hex_cursor_ranges.extend([f"{text_line}.{col_hex}", f"{text_line}.{col_hex+2}"])
            if self.cursor <= data_len:
                ascii_cursor_ranges.extend([f"{text_line}.{col_ascii}", f"{text_line}.{col_ascii+1}"])

        # アドレス適用範囲
        address_ranges = []
        # MSXフォント適用範囲（文字列部全体）
        msx_ranges = []
        if visible_lines_count is None:
            # 引数なしで呼ばれた場合は画面全体の行数分とみなす
            visible_lines_count = self.page_lines
            
        for text_line in range(1, visible_lines_count + 1):
            msx_ranges.extend([f"{text_line}.{self.COL_S_ASCII}", f"{text_line}.{self.COL_E_ASCII}"])
            address_ranges.extend([f"{text_line}.0", f"{text_line}.{self.COL_S_HEX-1}"])

        # Tclスクリプトの組み立て: 既存タグの削除と追加を一括処理
        w = self.text_editor._w # type: ignore
        tcl_script = [
             f"{w} tag remove address 1.0 end"
            ,f"{w} tag remove msx_font 1.0 end"
            ,f"{w} tag remove hex_selection 1.0 end"
            ,f"{w} tag remove hex_cursor 1.0 end"
            ,f"{w} tag remove ascii_cursor 1.0 end"
        ]

        if address_ranges:
            chunk_size = 4000
            for i in range(0, len(address_ranges), chunk_size):
                tcl_script.append(f"{w} tag add address {' '.join(address_ranges[i:i+chunk_size])}")

        if msx_ranges:
            chunk_size = 4000
            for i in range(0, len(msx_ranges), chunk_size):
                tcl_script.append(f"{w} tag add msx_font {' '.join(msx_ranges[i:i+chunk_size])}")

        if sel_ranges:
            chunk_size = 4000
            for i in range(0, len(sel_ranges), chunk_size):
                tcl_script.append(f"{w} tag add hex_selection {' '.join(sel_ranges[i:i+chunk_size])}")
                
        if hex_cursor_ranges:
            tcl_script.append(f"{w} tag add hex_cursor {' '.join(hex_cursor_ranges)}")
            
        if ascii_cursor_ranges:
            tcl_script.append(f"{w} tag add ascii_cursor {' '.join(ascii_cursor_ranges)}")
            
        # Tcl/Tkインタプリタで直接一括評価（画面の描画更新が割り込めないようにする）
        self.text_editor.tk.eval("\n".join(tcl_script))

    def update_status(self):
        """ ステータスバーの更新 """

        # 基本情報
        insert_str = "挿入" if self.insert_mode else "上書き"
        focus_str = "[ASCII]" if self.input_mode_ascii else "[HEX]"
        mode_str = f"{focus_str}{insert_str}"
        
        sel_size = abs(self.cursor - self.anchor) + 1 if self.cursor != self.anchor else 1
        bd = self.data[self.cursor] if self.cursor < len(self.data) else 0
        
        self.status_pos_var.set  (f"位置: {self.cursor:08X} = 0x{bd:02X} ({bd})")
        self.status_sel_var.set  (f"選択: {sel_size} Bytes")
        self.status_total_var.set(f"Total: {len(self.data)} Bytes")
        self.status_mode_var.set (f"{mode_str}")

        # 1命令逆アセンブル
        self.update_status_disasm()

        # ファイル情報
        self.update_status_file()
        self.update_1bpp_image()

    def update_status_disasm(self):
        """ ステータスバー：逆アセンブル更新 """
        if HAS_Z80DIS:
            address = self.get_asm_address()
            asm_str, asm_bin = self.disasm_one(self.cursor, address)
            delim = ";"
            if delim in asm_str:
                body, comment = asm_str.split(delim,1)
                asm_str = body.ljust(20) + ";" + comment.strip()
            asm_info = f"{address:08X}:{asm_bin.hex(' ').upper().ljust(11)}{ASM_DELIM} {asm_str} " 
        else:
            asm_info = "(Z80逆アセンブラ無効：z80disAssembler.pyが必要)"
        self.disasm_var.set(asm_info)

    def update_status_file(self):
        """ ステータスバー：ファイル情報更新 """
        if self.current_file_path:
            file_info = f"File: {self.current_file_path}"
            self.info_var.set(file_info)
            self.info_label.config(bg=self.root.cget("background"))
        else:
            drag_and_drop_enabled = "" #" (Drag & Drop Supported)"
            if not HAS_DND:
                drag_and_drop_enabled = "(ファイルのD&D非対応：tkinterdnd2が必要)"
            msx_font_enabled = ""
            if not HAS_MSX_FONT:
                msx_font_enabled = "(MSX-FONTが無い：bugfireさんのDumpListEditorに添付)" 
            var_str = f"File:-{drag_and_drop_enabled} {msx_font_enabled}"
            self.info_var.set(var_str)
            if not (HAS_DND and HAS_MSX_FONT):
                self.info_label.config(bg="#ffcccc")
            else:
                self.info_label.config(bg=self.root.cget("background"))

    def get_address_offset(self):
        """ 逆アセンブラ用アドレスオフセットを計算 """
        ofs = -self.get_baseofs()
        ofs += self.get_asmbase()
        return ofs

    def get_asm_address(self, address=None):
        """ 逆アセンブラ用アドレスの計算 """
        if address is None:
            address = self.cursor
        ofs = self.get_address_offset()
        return (address + ofs if -ofs < address else address) & 0xFFFF

    def disasm_one(self, idx, address):
        if HAS_Z80DIS:
            src_bytes = bytes([
                    self.data[i] if i < len(self.data) else 0 
                    for i in range(idx, idx + 4)
                ])
            inst, code_bytes = z80disasm.decode(src_bytes, address)
            return [z80disAssembler.format_asm_to_h_style(inst),code_bytes]
        else:
            return "", bytes()

    def disasm_selection(self, head_use_symbol=False):
        if self.cursor != self.anchor:
            start, end = min(self.cursor, self.anchor), max(self.cursor, self.anchor)
        else:
            start = self.cursor
            end = min(self.cursor + 0x1000 , len(self.data) - 1)
        if (end - start) > 0x2000:
            messagebox.showwarning(
                title="サイズが大きい逆アセンブルの実行",
                message="処理時間が重いので、フリーズしたかのように感じるかもしれません。"
            )
        
        asm_address = self.get_asm_address(start)
        disasm_list = z80disasm.disasm(self.data[start:end + 1], asm_address, head_use_symbol)

        if 0 < len(disasm_list):
            if (self.log_window is None) or (not self.log_window.is_alive()):
                self.log_window  = DisAsmWindow(self.root, APP_NAME, self.current_file_name)
                assert self.log_window.window is not None
                self.log_window.window.lift()
                self.log_window.window.focus_force()

            head = (
                 ';-----------------------------------------------\n'
                f'; File:"{self.current_file_name}"\n'
                f';   Offset: 0x{start:06X}\n'
                f';   Address:0x{asm_address:04X}\n'
                 ';-----------------------------------------------\n'
            )
            self.log_window.put(head + disasm_list)

    def update_1bpp_image(self):
        # 動的Canvasを用いた 16x16 ビットパターンの描画更新 (32バイト分)
        # 8x8を1ブロックとしたMSXスプライト的な2x2ブロック (左上:1, 左下:2, 右上:3, 右下:4)
        for i in range(32):
            idx = self.cursor + i
            val = self.data[idx] if idx < len(self.data) else 0
            
            b = i // 8           # ブロック番号 0:左上, 1:左下, 2:右上, 3:右下
            r_in_block = i % 8   # ブロック内の行インデックス 0〜7
            
            # ブロックの配置に合わせてキャンバス上の行・列を算出
            # b=0(左上), b=1(左下), b=2(右上), b=3(右下)
            row = (b % 2) * 8 + r_in_block
            col_start = (b // 2) * 8
            
            for bit in range(8):
                col = col_start + bit
                # 最上位ビット(MSB)から順に描画
                bit_on = (val & (0x80 >> bit)) != 0
                color = self.BIT_FG_COLOR if bit_on else self.BIT_BG_COLOR
                self.bit_canvas.itemconfig(self.bit_rects[row][col], fill=color)

    def handle_tab(self, event):
        if not self.input_mode_ascii:
            self.set_input_mode(not self.input_mode_ascii)
            return "break"

        # 標準のTAB処理へ

    def handle_shift_tab(self, event):
        if self.input_mode_ascii:
            self.set_input_mode(not self.input_mode_ascii)
            return "break"
        
        # 標準のShift+TAB処理へ

    def toggle_input_area(self):
            self.set_input_mode(not self.input_mode_ascii)
            return "break"

    def dispatch_key_event(self, event):
        keysym, state, char = event.keysym, event.state, event.char
        is_win = IS_WIN
        shift = (state & 1) != 0
        
        # プラットフォーム別にCommandキーとControlキーを別判定
        if IS_MAC:
            # macOSのCommandキーは state の 0x8 (Mod2) または 0x10 (Mod1)、環境によっては 0x100 などのビットが立つ
            ctrl_cmd = bool(state & (0x8 | 0x10 | 0x100 | 0x1000))
        else:
            # Win/LinuxのControlキーは state の 0x4
            ctrl_cmd = bool(state & 4)
            
        is_alt = (
            "Alt" in keysym or 
            "Option" in keysym or 
            (is_win and bool(state & 0x20000)) or  # Windows
            #is_lnx and bool(state & 0x0008)) or   # Linux -> tkInterのバグで他の要因で立ちっぱなしになる
            (IS_MAC and bool(state & 0x0010))      # Mac
        )

        # グローバルショートカットの判定 (フォーカス位置に関係なく動作させる)
        if keysym == 'F2':
            self.toggle_input_area()
            return "break"
        if keysym == 'F3':
            if ctrl_cmd:
                self.search_current(event)
            elif shift:
                self.search_prev(event)
            else:
                self.search_next(event)
            return "break"
        if keysym == 'F4':
            self.navigate( keysym, shift, ctrl_cmd)
            return "break"
            
        if ctrl_cmd:
            sym_lower = keysym.lower()
            if sym_lower == 's':
                self.save_bin()
                return "break"
            elif sym_lower == 'o':
                self.load_bin()
                return "break"
            elif sym_lower == 'f':
                self.focus_search()
                return "break"
            elif sym_lower == 'g':
                self.focus_search_go()
                return "break"
            elif IS_MAC:
                if sym_lower == 'bracketleft':
                    self.nav_back()
                    return "break"
                elif sym_lower == 'bracketright':
                    self.nav_forward()
                    return "break"
                
        # ALTナビゲーション（グローバル）
        if is_alt and not IS_MAC:
            if keysym == 'Left':
                self.nav_back()
                return "break"
            elif keysym == 'Right':
                self.nav_forward()
                return "break"

        # TabキーはTkinterの標準フォーカス移動に任せるためスルーする
        # （ISO_Left_Tab は Shift + Tab の判定用）
        if keysym in ('Tab', 'ISO_Left_Tab'):
            return

        # 以下のキー操作はエディタ本体にフォーカスがある時のみ処理する
        if self.root.focus_get() != self.text_editor: 
            return

        # ファンクションキーは別で処理
        if re.match(r'^F[1-9][0-9]?$', keysym): return
        
        # ALT/CMD+キーは別で処理
        if is_alt: return
        
        shift = (state & 1) != 0
        
        if ctrl_cmd:
            sym_lower = keysym.lower()
            if sym_lower == 'c': self.copy(); return "break"
            elif sym_lower == 'v': self.paste(); return "break"
            elif sym_lower == 'z': self.undo(); return "break"
            elif sym_lower == 'y': self.redo(); return "break"
            elif sym_lower == 'a': self.select_all(); return "break"
            elif keysym == 'Up': 
                self.top_line = max(0, self.top_line - 1)
                self.render()
                return "break"
            elif keysym == 'Down': 
                total_lines = (len(self.data) // self.LINE_BYTES) + 1
                self.top_line = min(max(0, total_lines - 1), self.top_line + 1)
                self.render()
                return "break"
            elif keysym in ('Home', 'End'): pass # スルーしてnavigateの実行へ
            elif keysym == 'Return': self.disasm_selection(shift); return "break"
            else: return
                
        nav_keys = {'Up', 'Down', 'Left', 'Right', 'Home', 'End', 'Prior', 'Next', 'Return'}
        if keysym in nav_keys:
            if self.commit_half_byte_if_needed(): self.render()
            self.navigate(keysym, shift, ctrl_cmd)
            return "break"
            
        if keysym == 'Insert':
            if self.commit_half_byte_if_needed(): self.render()
            self.insert_mode = not self.insert_mode
            self.blink_cursor_stop()
            self.set_cursor_color()
            self.blink_cursor()
            self.update_status()
            return "break"
        elif keysym in ('Delete', 'BackSpace'):
            self.delete_data(keysym)
            return "break"
            
        if char:
            if self.input_mode_ascii:
                self.handle_ascii_input(char)
                return "break"
            elif char.upper() in '0123456789ABCDEF':
                self.handle_hex_input(char.upper())
                return "break"
            
        if keysym in ("Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Meta_L", "Meta_R"):
            return "break"
        return "break"

    def navigate(self, keysym, shift, ctrl_cmd):
        new_pos = self.cursor
        if ctrl_cmd:
            if keysym == 'Home': new_pos = 0
            elif keysym == 'End': new_pos = len(self.data)
        else:
            if keysym == 'Up': new_pos = self.cursor - self.LINE_BYTES
            elif keysym == 'Down': new_pos = self.cursor + self.LINE_BYTES
            elif keysym == 'Left': new_pos = self.cursor - 1
            elif keysym == 'Right': new_pos = self.cursor + 1
            elif keysym == 'Home': new_pos = self.cursor - (self.cursor % self.LINE_BYTES)
            elif keysym == 'End': new_pos = min(self.cursor - (self.cursor % self.LINE_BYTES) + self.LINE_BYTES - 1, len(self.data))
            elif keysym == 'Prior': new_pos = self.cursor - max(1, self.page_lines - 1) * self.LINE_BYTES
            elif keysym == 'Next': new_pos = self.cursor + max(1, self.page_lines - 1) * self.LINE_BYTES
            elif keysym in ['F4', 'Return']: new_pos = self.cursor + len(self.disasm_one(self.cursor, self.get_asm_address())[1])
            
        self.cursor = max(0, min(len(self.data), new_pos))
        if not shift: self.anchor = self.cursor
            
        if not self.ensure_cursor_visible():
            self.update_cursor_display()

    def handle_hex_input(self, char):
        if self.cursor > len(self.data):
            self.cursor = self.anchor = len(self.data)
            
        if self.half_byte is None:
            self.save_history()

            # 範囲選択されていた場合は削除
            if self.cursor != self.anchor:
                start, end = min(self.cursor, self.anchor), max(self.cursor, self.anchor)
                del self.data[start:min(end, len(self.data)-1)+1]
                self.cursor = self.anchor = start
    
            self.half_byte = char
        else:
            val = int(self.half_byte + char, 16)

            if self.cursor < len(self.data):
                if not self.insert_mode:
                    self.data[self.cursor] = val
                else:
                    self.data.insert(self.cursor, val)
            else:
                self.data.append(val)

            self.half_byte = None
            self.cursor = self.anchor = self.cursor + 1
            
        self.adjust_top_line()
        self.render()

    def handle_ascii_input(self, char):
        # MSX文字コードに変換
        if (val := UNICODE_TO_MSX_DIC.get( char )) is None:
            return  # MSX文字コードマップに存在しない文字は無視

        if self.cursor > len(self.data):
            self.cursor = self.anchor = len(self.data)
            
        self.save_history()
        
        # 範囲選択されていた場合は削除
        if self.cursor != self.anchor:
            start, end = min(self.cursor, self.anchor), max(self.cursor, self.anchor)
            del self.data[start:min(end, len(self.data)-1)+1]
            self.cursor = self.anchor = start

        if self.cursor < len(self.data):
            if not self.insert_mode: 
                self.data[self.cursor] = val
            else: 
                self.data.insert(self.cursor, val)
        else:
            self.data.append(val)
            
        self.cursor = self.anchor = self.cursor + 1
        self.adjust_top_line()
        self.render()

    def commit_half_byte_if_needed(self):
        if self.half_byte is not None:
            val = int("0" + self.half_byte, 16)
            if self.cursor < len(self.data):
                if not self.insert_mode: self.data[self.cursor] = val
                else: self.data.insert(self.cursor, val)
            else:
                self.data.append(val)
            self.half_byte = None
            return True
        return False

    def delete_data(self, keysym):
        if self.half_byte is not None:
            self.half_byte = None
            self.render()
            return
            
        start, end = min(self.cursor, self.anchor), min(max(self.cursor, self.anchor), len(self.data)-1)
        if self.cursor != self.anchor:
            self.save_history()
            del self.data[start:end+1]
            self.cursor = self.anchor = start
        else:
            if keysym == 'Delete' and self.cursor < len(self.data):
                self.save_history()
                del self.data[self.cursor]
            elif keysym == 'BackSpace' and self.cursor > 0:
                self.save_history()
                del self.data[self.cursor - 1]
                self.cursor = self.anchor = self.cursor - 1
                    
        self.adjust_top_line()
        self.render()

    def get_selected_hex(self):
        start, end = min(self.cursor, self.anchor), min(max(self.cursor, self.anchor), len(self.data)-1)
        if start <= end:
            return " ".join(f"{b:02X}" for b in self.data[start:end+1])
        return ""

    def get_selected_bin(self):
        start, end = min(self.cursor, self.anchor), min(max(self.cursor, self.anchor), len(self.data)-1)
        if start <= end:
            return self.data[start:end+1]
        return bytes()

    def copy(self):
        start, end = min(self.cursor, self.anchor), min(max(self.cursor, self.anchor), len(self.data)-1)
        if start <= end:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.get_selected_hex())

    def paste(self):
        try: text = self.root.clipboard_get()
        except tkinter.TclError: return
            
        text = re.sub(r'[^0-9a-fA-F]', '', text)
        if not text: return
        if len(text) % 2 != 0: text = text[:-1]
            
        paste_data = bytearray.fromhex(text)
        if not paste_data: return
            
        self.commit_half_byte_if_needed()
        self.save_history()
        
        # まずは選択範囲のデータを削除
        start = min(self.cursor, self.anchor)
        if self.cursor != self.anchor:
            end = min(max(self.cursor, self.anchor), len(self.data)-1)
            del self.data[start:end+1]
            self.cursor = self.anchor = start
        
        if not self.insert_mode:
            # 上書き時は末尾を超えた分を追加
            end_over = start + len(paste_data)
            if end_over > len(self.data):
                self.data[start:len(self.data)] = paste_data[:len(self.data)-start]
                self.data.extend(paste_data[len(self.data)-start:])
            else:
                self.data[start:end_over] = paste_data
        else:
            self.data[start:start] = paste_data
            
        self.cursor = self.anchor = start + len(paste_data)
        self.adjust_top_line()
        self.render()

    def select_all(self):
        if self.commit_half_byte_if_needed(): self.render()
        if len(self.data) > 0:
            self.anchor, self.cursor = 0, len(self.data) - 1
            if not self.ensure_cursor_visible():
                self.update_cursor_display()

    def clear_history(self):
        self.undo_stack = []
        self.redo_stack = []
        self.nav_history = []
        self.nav_index = -1

    def save_history(self):
        self.undo_stack.append({"data": bytearray(self.data), "cursor": self.cursor, "anchor": self.anchor, "top_line": self.top_line})
        if len(self.undo_stack) > 1000: self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self):
        self.commit_half_byte_if_needed()
        if not self.undo_stack: return
        self.redo_stack.append({"data": bytearray(self.data), "cursor": self.cursor, "anchor": self.anchor, "top_line": self.top_line})
        self.restore_state(self.undo_stack.pop())

    def redo(self):
        self.commit_half_byte_if_needed()
        if not self.redo_stack: return
        self.undo_stack.append({"data": bytearray(self.data), "cursor": self.cursor, "anchor": self.anchor, "top_line": self.top_line})
        self.restore_state(self.redo_stack.pop())

    def restore_state(self, state):
        self.data, self.cursor, self.anchor = state["data"], state["cursor"], state["anchor"]
        self.top_line = state.get("top_line", 0)
        self.render()
        if not self.ensure_cursor_visible():
            self.update_cursor_display()

    # ----------------------------------------------------------------------
    # ナビゲーション履歴 (History Back / Forward)
    # ----------------------------------------------------------------------
    def get_nav_state(self):
        return {
            "cursor": self.cursor,
            "anchor": self.anchor,
            "top_line": self.top_line
        }

    def save_nav_history_before_jump(self):
        current = self.get_nav_state()
        if not self.nav_history:
            self.nav_history = [current]
            self.nav_index = 0
        else:
            self.nav_history[self.nav_index] = current
            self.nav_history = self.nav_history[:self.nav_index + 1]

    def save_nav_history_after_jump(self):
        current = self.get_nav_state()
        if self.nav_history and self.nav_history[-1]["cursor"] == current["cursor"]:
            self.nav_history[-1] = current
        else:
            self.nav_history.append(current)
            if len(self.nav_history) > 100:
                self.nav_history.pop(0)
            self.nav_index = len(self.nav_history) - 1

    def nav_back(self, event=None):
        if not self.nav_history: return
        
        self.nav_history[self.nav_index] = self.get_nav_state()
        if self.nav_index > 0:
            self.nav_index -= 1
            self.restore_nav_state(self.nav_history[self.nav_index])

    def nav_forward(self, event=None):
        if not self.nav_history: return
        
        self.nav_history[self.nav_index] = self.get_nav_state()
        if self.nav_index < len(self.nav_history) - 1:
            self.nav_index += 1
            self.restore_nav_state(self.nav_history[self.nav_index])

    def restore_nav_state(self, state):
        self.commit_half_byte_if_needed()
        self.cursor = state["cursor"]
        self.anchor = state["anchor"]
        self.top_line = state["top_line"]
        self.render()
        if not self.ensure_cursor_visible():
            self.update_cursor_display()
        self.text_editor.focus_set()

    # ----------------------------------------------------------------------
    # ファイル操作
    # ----------------------------------------------------------------------
    def load_bin(self):
        path = filedialog.askopenfilename()
        if not path: return
        self.load_bin_from_path(path)

    def load_bin_from_path(self, path):
        self.commit_half_byte_if_needed()
        self.clear_history()
        try:
            with open(path, "rb") as f: self.data = bytearray(f.read())
            self.cursor = self.anchor = 0
            self.top_line = 0
            self.set_file_path(path)
            self.render()
            self.update_cursor_display() # ロード直後にステータス表示等を更新
        except Exception as e: 
            messagebox.showerror("Error", str(e))

    def save_bin(self):
        path = filedialog.asksaveasfilename()
        if not path: return
        if self.commit_half_byte_if_needed(): self.render()
        try:
            with open(path, "wb") as f: f.write(self.data)
            self.set_file_path(path)
            messagebox.showinfo("Success", "Saved.")
        except Exception as e: messagebox.showerror("Error", str(e))

#--------------------------------------------------------------------------
# main
#--------------------------------------------------------------------------
if __name__ == "__main__":
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tkinter.Tk()

    # TkinterのベースDPIを全OS共通で96 DPI（標準解像度）に統一する
    # 96 DPI のとき、Tcl/Tkの内部スケール値は「96 / 72 = 1.3333...」
    tcl_scaling_factor = 96.0 / 72.0
    try:
        root.tk.call('tk', 'scaling', tcl_scaling_factor)
    except tkinter.TclError:
        pass
        
    fh.setup_default_font(root)
    check_msx_font()
   
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        app = HexDumpEditor(root, file_path)
    else:
        app = HexDumpEditor(root)
    root.mainloop()
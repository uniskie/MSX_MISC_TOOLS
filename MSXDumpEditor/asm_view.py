import tkinter as tk
from tkinter import filedialog, messagebox, font, ttk
import re
import sys

# ワンラインZ80逆アセンブラの組み込み
from z80_disAssembler import z80disasm

# フォントヘルパーの組み込み
import font_helper as fh

FONT_HEIGHT = 18

#--------------------------------------------------------------------------
# Log Window
#--------------------------------------------------------------------------
class DisasmWindow:
    def __init__(self, parent, APP_NAME):

        # Toplevelで新しいウィンドウを作成
        self.window = tk.Toplevel(parent)
        self.window.title(APP_NAME + ": DisAssemble View")
        self.window.geometry(f"+{parent.winfo_x()}+{parent.winfo_y()}")

        if sys.platform == "win32":
            self.window.attributes("-toolwindow", True)
        else:
            # Linuxで "-type utility" はフォーカス喪失やフリーズの原因になるため "dialog" または設定なしが安全
            try:
                self.window.attributes("-type", "dialog")
            except Exception:
                pass

        container = tk.Frame(self.window)
        container.pack(expand=True, fill='both', padx=2, pady=2)

        v_scroll = tk.Scrollbar(container, orient=tk.VERTICAL)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        h_scroll = tk.Scrollbar(container, orient=tk.HORIZONTAL)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        # ESCキーでも閉じる
        self.window.bind("<Escape>", self.on_close)

        #font_px_size = tk.font.nametofont("TkDefaultFont").metrics('linespace')
        asm_font_style = fh.get_font_with_pixel_height(FONT_HEIGHT, fh.font_name_program)

        #コントロールの配置
        self.log_text = tk.Text(container 
            , exportselection=False
            , wrap='none'  # 自動改行なし
            , yscrollcommand=v_scroll.set # 縦スクロールを連動
            , xscrollcommand=h_scroll.set  # 横スクロールを連動
            , font=asm_font_style
            , width=80
            , height=40
        )
        self.log_text.configure(tabs=(self.log_text.tk.call('font', 'measure', self.log_text.cget('font'), '0') * 8))
        self.log_text.pack(expand=True, fill='both', side=tk.LEFT)

        ################################################################################
        # タグで色を付けるとカーソルでのスクロールデフォルト処理が重いので処理を乗っ取る
        # 移動、選択範囲変更を自前処理
        # 選択範囲の操作は、SHFIFT+(カーソル、ページアップダウン、マウス)
        # SHIFTなしでのマウスドラッグ（新規選択）
        ################################################################################
        self._select_start_index = None

        # 移動・選択キー操作の一括バインド
        for key in [
            "<Up>", "<Down>", "<Shift-Up>", "<Shift-Down>",
            "<Left>", "<Right>", "<Shift-Left>", "<Shift-Right>",
            "<Control-Left>", "<Control-Right>", "<Control-Shift-Left>", "<Control-Shift-Right>",
            "<Shift-Control-Left>", "<Shift-Control-Right>",
            "<Prior>", "<Next>", "<Shift-Prior>", "<Shift-Next>",
            "<Home>", "<End>", "<Shift-Home>", "<Shift-End>",
            "<Control-Home>", "<Control-End>", "<Control-Shift-Home>", "<Control-Shift-End>",
            "<Shift-Control-Home>", "<Shift-Control-End>"
        ]:
            self.log_text.bind(key, self._on_key_move_or_select)

        # マウス操作
        self.log_text.bind("<Button-1>", self._on_mouse_click)
        self.log_text.bind("<Shift-Button-1>", self._on_shift_mouse_click)
        self.log_text.bind("<ButtonPress-1>", self._on_mouse_press)
        self.log_text.bind("<B1-Motion>", self._on_mouse_drag)
        ################################################################################

        # 書き換え不能に
        self.log_text.bind("<Key>", self.block_input)
        self.log_text.bind("<BackSpace>", lambda e: "break")
        self.log_text.bind("<Delete>", lambda e: "break")

        v_scroll.config(command=self.log_text.yview)
        h_scroll.config(command=self.log_text.xview)

        self.setup_asm_color_tags()
        self.apply_color_tags()

    def setup_asm_color_tags(self):

        # 選択範囲の色
        self.log_text.tag_configure("sel", background="#e0f0e0", foreground="#001100")
        
        # Z80 ASM 構文色分け
        self.log_text.tag_configure("comment",  foreground="#b00000")   # コメント
        self.log_text.tag_configure("label",    foreground="#843683")   # ラベル
        self.log_text.tag_configure("opcode",   foreground="#565ca6")   # 命令
        self.log_text.tag_configure("register", foreground="#908222")   # レジスタ
        self.log_text.tag_configure("number",   foreground="#234623")   # 数値

        # 色分け優先度 （低→高）
        self.log_text.tag_raise("sel")      # 選択範囲
        self.log_text.tag_raise("register") # レジスタ
        self.log_text.tag_raise("opcode")   # 命令
        self.log_text.tag_raise("number")   # 数値
        self.log_text.tag_raise("label")    # ラベル
        self.log_text.tag_raise("comment")  # コメント

        self.rules = [
            ("comment",  r";.*"),                                                # ; から始まるコメント
            ("label",    r"^[a-zA-Z_.][a-zA-Z0-9_.]*:?"),                        # 行頭のラベル
            ("opcode",   r"\b(ld|add|sub|adc|sbc|and|or|xor|cp|inc|dec|inc_dec|bit|set|res|jp|jr|call|ret|rst|push|pop|in|out|nop|halt|di|ei|ex|exx)\b"), # 命令
            ("register", r"\b(a|f|b|c|d|e|h|l|af|bc|de|hl|ix|iy|sp|pc|i|r)\b"),  # レジスタ
            ("number",   r"\b(\d+[hH]?|[0-9a-fA-F]+[hH]|\$[0-9a-fA-F]+)\b")       # 16進数($FF, 0FFh)や10進数
        ]

    def apply_color_tags(self):

        tag_positions = {
            "comment": [],
            "label": [],
            "opcode": [],
            "register": [],
            "number": []
        }

        #タグ消し
        for tag_name in tag_positions.keys():
                self.log_text.tag_remove(tag_name, "1.0", "end")

        end_index = self.log_text.index("end-1c")
        num_lines = int(end_index.split(".")[0])

        for line_num in range(1, num_lines + 1):
            line_text = self.log_text.get(f"{line_num}.0", f"{line_num}.end")
            
            for tag_name, pattern in self.rules:
                for match in re.finditer(pattern, line_text, re.IGNORECASE):
                    s_col, e_col = match.span()
                    tag_positions[tag_name].append(f"{line_num}.{s_col}")
                    tag_positions[tag_name].append(f"{line_num}.{e_col}")

        for tag_name, positions in tag_positions.items():
            if positions:
                self.log_text.tag_add(tag_name, *positions)

    ################################################################################
    # タグで色を付けるとカーソルでのスクロールデフォルト処理が重いので処理を乗っ取る
    # 移動、選択範囲変更を自前処理
    # 選択範囲の操作は、SHFIFT+(カーソル、ページアップダウン、マウス)
    # SHIFTなしでのマウスドラッグ（新規選択）
    ################################################################################
    def _on_key_move_or_select(self, event):
        """あらゆる移動・選択キー入力を一元管理する共通ハンドラ"""
        try:
            # 押されたキーから、移動の「方向」「単位」「Shift状態」をデータとして展開
            keysym = event.keysym
            state = event.state
            
            has_shift = bool(state & 0x0001) or "Shift" in keysym
            has_ctrl = bool(state & 0x0004) or "Control" in keysym
            
            # 各キーごとの移動仕様マッピング
            direction = -1 if keysym in ["Up", "Left", "Prior", "Home"] else 1
            op = "+" if direction > 0 else "-"
            
            if keysym in ["Up", "Down"]:
                modifier = f"insert {op} 1 lines"
            elif keysym in ["Left", "Right"]:
                unit = "words" if has_ctrl else "chars"
                modifier = f"insert {op} 1 {unit}"
            elif keysym in ["Prior", "Next"]:
                text_height = int(self.log_text.cget("height"))
                move_lines = text_height if text_height > 0 else 40
                modifier = f"insert {op} {move_lines} lines"
            elif keysym == "Home":
                modifier = "1.0" if has_ctrl else "insert linestart"
            elif keysym == "End":
                modifier = "end-1c" if has_ctrl else "insert lineend"
            else:
                return "break"

            # 選択起点の管理（Shift状態のチェック）
            current_index = self.log_text.index("insert")
            if has_shift:
                if self._select_start_index is None:
                    self._select_start_index = current_index
            else:
                self._select_start_index = None
                self.log_text.tag_remove("sel", "1.0", "end")

            # インデックスを絶対座標（行.桁）に変えてから適用
            # （行は1開始、桁は0開始）
            new_index = self.log_text.index(modifier)
            self.log_text.mark_set("insert", new_index)
            self.log_text.see("insert")

            # 選択ハイライト引き直し
            if has_shift and self._select_start_index is not None:
                if self.log_text.compare(self._select_start_index, "<", new_index):
                    start, end = self._select_start_index, new_index
                else:
                    start, end = new_index, self._select_start_index

                self.log_text.tag_remove("sel", "1.0", "end")
                self.log_text.tag_add("sel", start, end)

        except Exception:
            pass

        return "break"

    def _clear_select_start(self, event):
        """Shiftキー解放時の起点インデックス破棄処理"""
        self._select_start_index = None

    def _on_mouse_press(self, event):
        """マウスドラッグ開始時の起点インデックス記録処理"""
        self._select_start_index = self.log_text.index(f"@{event.x},{event.y}")

    def _on_mouse_drag(self, event):
        """マウスクリックからドラッグ移動中の選択範囲更新処理"""
        try:
            if self._select_start_index is not None:
                current_index = self.log_text.index(f"@{event.x},{event.y}")
                self.log_text.mark_set("insert", current_index)
                
                if self.log_text.compare(self._select_start_index, "<", current_index):
                    start, end = self._select_start_index, current_index
                else:
                    start, end = current_index, self._select_start_index
                    
                self.log_text.tag_remove("sel", "1.0", "end")
                self.log_text.tag_add("sel", start, end)
        except Exception:
            pass
        return "break"

    def _on_mouse_click(self, event):
        """マウスクリック時の選択範囲および起点インデックスの消去処理"""
        self.log_text.tag_remove("sel", "1.0", "end")
        self._select_start_index = None

    def _on_shift_mouse_click(self, event):
        """Shift+マウスクリック時の選択範囲の拡張・縮小処理"""
        try:
            if self._select_start_index is None:
                self._select_start_index = self.log_text.index("insert")

            click_index = self.log_text.index(f"@{event.x},{event.y}")
            self.log_text.mark_set("insert", click_index)
            self.log_text.see("insert")

            if self.log_text.compare(self._select_start_index, "<", click_index):
                start, end = self._select_start_index, click_index
            else:
                start, end = click_index, self._select_start_index
                
            self.log_text.tag_remove("sel", "1.0", "end")
            self.log_text.tag_add("sel", start, end)
        except Exception:
            pass
        return "break"
    ################################################################################

    def is_alive(self):
        return (self.window is not None) and tk.Toplevel.winfo_exists(self.window)

    def on_close(self, event=None):
        if self.window:
            #self.window.destroy()
            self.window.withdraw() 
            self.window.after(1, self.window.destroy)
            self.window = None

    def block_input(self, event):
        # 矢印キー、Home、End、PageUp/Down、Ctrlキーなどは通過させる（カーソル移動やコピーを許可）
        if event.keysym in [
            'Left', 'Right', 'Up', 'Down', 
            'Home', 'End', 'Prior', 'Next', 
            'Control_L', 'Control_R',
            'Escape','F4'
        ]:
            return None # 通常の挙動（移動）を許可
            
        # Ctrl+C (コピー) や Ctrl+A (全選択) も許可
        if event.state & 0x0004: # Ctrlキーが押されている状態
            if event.keysym.lower() in ['c', 'a','f4','w']:
                return None # 許可

        # それ以外の文字入力、BackSpace、Delete、Enterなどはすべてブロック（書き換え禁止）
        return "break"

    def put(self, message):
        """すべて書き換え"""
        if not self.is_alive(): return
        self.log_text.delete("1.0", tk.END)
        self.log_text.insert(tk.END, message + "\n")
        #self.set_asm_text(message)
        self.log_text.mark_set("insert", "1.0")
        self.log_text.see("1.0")

        self.apply_color_tags()
        
        self.log_text.focus_set()

    def log(self, message):
        """末尾に追加"""
        if not self.is_alive(): return
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

        self.apply_color_tags()

        self.log_text.focus_set()


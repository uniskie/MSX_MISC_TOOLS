import tkinter as tk
#from tkinter import filedialog, messagebox, font, ttk
import re
import sys

# ワンラインZ80逆アセンブラの組み込み
#from z80_disAssembler import z80disasm
import z80_disAssembler as z80disAssembler

# フォントヘルパーの組み込み
import font_helper as fh

FONT_HEIGHT = 16
IS_MAC = (sys.platform == "darwin")
IS_WIN = (sys.platform == "win32")
IS_LINUX = (sys.platform == "linux")

#--------------------------------------------------------------------------
# Log Window
#--------------------------------------------------------------------------
class DisAsmWindow:
    def __init__(self, parent, APP_NAME, file_name):

        # Toplevelで新しいウィンドウを作成
        self.window : tk.Toplevel | None = tk.Toplevel(parent)
        self.window.title(APP_NAME 
                          + ": DisAssemble View"
                          + (f" - {file_name}" if file_name is not None else ""))
        self.window.geometry(f"+{parent.winfo_x()}+{parent.winfo_y()}")

        #if IS_WIN:
        #    self.window.attributes("-toolwindow", True)
        #elif IS_LINUX:
        #    try:
        #        self.window.attributes("-type", "dialog")
        #    except Exception:
        #        pass

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
        keys_to_bind = [
            "<Up>", "<Down>", "<Shift-Up>", "<Shift-Down>",
            "<Left>", "<Right>", "<Shift-Left>", "<Shift-Right>",
            "<Prior>", "<Next>", "<Shift-Prior>", "<Shift-Next>",
            "<Home>", "<End>", "<Shift-Home>", "<Shift-End>",
            "<Control-Home>", "<Control-End>", "<Control-Shift-Home>", "<Control-Shift-End>",
            "<Shift-Control-Home>", "<Shift-Control-End>"
        ]
        
        if IS_MAC:
            # Macでの単語単位の移動 (Option + 矢印キー)
            keys_to_bind.extend([
                "<Option-Left>", "<Option-Right>",
                "<Shift-Option-Left>", "<Shift-Option-Right>"
            ])
        else:
            # Windows/Linuxでの単語単位の移動 (Control + 矢印キー)
            keys_to_bind.extend([
                "<Control-Left>", "<Control-Right>",
                "<Control-Shift-Left>", "<Control-Shift-Right>",
                "<Shift-Control-Left>", "<Shift-Control-Right>"
            ])

        for key in keys_to_bind:
            self.log_text.bind(key, self._on_key_move_or_select)

        # マウス操作
        self.log_text.bind("<Button-1>", self._on_mouse_press) # click
        # self.log_text.bind("<ButtonPress-1>", self._on_mouse_press) # ButtonPressはBurronのエイリアスらしい
        self.log_text.bind("<Shift-Button-1>", self._on_shift_mouse_click)
        self.log_text.bind("<B1-Motion>", self._on_mouse_drag)

        # ジャンプ機能と履歴移動のキーバインド
        self.log_text.bind("G", self.cmd_jump_to_address)
        self.log_text.bind("g", self.cmd_jump_to_address)
        self.log_text.bind("<F4>", self.cmd_jump_to_address)
        self.log_text.bind("B", self.cmd_history_back)
        self.log_text.bind("b", self.cmd_history_back)
        self.log_text.bind("F", self.cmd_history_forward)
        self.log_text.bind("f", self.cmd_history_forward)
        
        if IS_MAC:
            # macOS 標準の進む・戻る (Cmd+[ , Cmd+]) および ジャンプ (Cmd+G)
            self.log_text.bind("<Command-bracketleft>", self.cmd_history_back)
            self.log_text.bind("<Command-bracketright>", self.cmd_history_forward)
            self.log_text.bind("<Command-g>", self.cmd_jump_to_address)
        else:
            self.log_text.bind("<Control-g>", self.cmd_jump_to_address)
            self.log_text.bind("<Alt-Left>", self.cmd_history_back)
            self.log_text.bind("<Alt-Right>", self.cmd_history_forward)
        
        # ジャンプ履歴管理用変数
        self.history = []
        self.history_index = -1
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
        # カーソル行の背景色
        self.log_text.tag_configure("current_line", background="#fff0e0")

        # 選択範囲の色
        self.log_text.tag_configure("sel", background="#e0f0e0", foreground="#001100")

        # Z80 ASM 構文色分け
        self.log_text.tag_configure("comment",   foreground="#b00000")   # コメント
        self.log_text.tag_configure("label",     foreground="#843683")   # ラベル
        self.log_text.tag_configure("opcode",    foreground="#565ca6")   # 命令
        self.log_text.tag_configure("directive", foreground="#a656a6")   # 疑似命令
        self.log_text.tag_configure("register",  foreground="#908222")   # レジスタ
        self.log_text.tag_configure("number",    foreground="#234623")   # 数値

        # 色分け優先度 （低→高）
        self.log_text.tag_raise("current_line") # カーソル行
        self.log_text.tag_raise("sel")          # 選択範囲
        self.log_text.tag_raise("register")     # レジスタ
        self.log_text.tag_raise("opcode")       # 命令
        self.log_text.tag_raise("directive")    # 疑似命令
        self.log_text.tag_raise("number")       # 数値
        self.log_text.tag_raise("label")        # ラベル
        self.log_text.tag_raise("comment")      # コメント

        self.rules = [
            ("comment",  fr"{z80disAssembler.COMMENT_DELIM}.*"),                               # ; から始まるコメント
            ("label",    fr"^[a-zA-Z_.][a-zA-Z0-9_.]*{z80disAssembler.ADDRESS_DELIM}?"),       # 行頭のラベル
            ("opcode",   r"\b(adc|add|and|bit|call|ccf|cp|cpd|cpdr|cpi|cpir|cpl|daa|dec|di|djnz|ei|ex|exx|halt|im|in|inc|ind|indir|ini|inir|jp|jr|ld|ldd|lddr|ldi|ldir|neg|nop|or|otdr|otir|out|outd|outi|pop|push|res|ret|reti|retn|rl|rla|rlc|rlca|rld|rr|rra|rrc|rrca|rrd|rst|sbc|scf|set|sla|sll|sra|srl|sub|xor)\b"), # 命令
            ("register", r"\b(a|f|b|c|d|e|h|l|af|bc|de|hl|ix|ixh|ixliy|iyh|iyl|sp|pc|i|r)\b"), # レジスタ
            ("number",   r"\b(\d+[hH]?|[0-9a-fA-F]+[hH]|\$[0-9a-fA-F]+)\b"),                   # 16進数($FF, 0FFh)や10進数
            ("directive", r"\b(db|dm|ds|dw|defb|defm|defs|defm|macro|if|endif|else|elif)\b"),  # 疑似命令
        ]

    def apply_color_tags(self):

        tag_positions = {
            "comment": [],
            "label": [],
            "opcode": [],
            "register": [],
            "number": [],
            "directive": [],
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

    def highlight_current_line(self, event=None):
        """現在のカーソル行の背景色をハイライトする"""
        if not self.is_alive(): return
        
        # 一旦全体のハイライトを消去
        self.log_text.tag_remove("current_line", "1.0", tk.END)
        
        # カーソル行の先頭から、行末の改行文字(+1c)までハイライトを適用
        # （改行文字を含めると右端まで色が塗られる）
        self.log_text.tag_add("current_line", "insert linestart", "insert lineend + 1c")

    ################################################################################
    # 入力制御・移動・選択処理
    ################################################################################
    def get_current_line_info(self):
        """カーソル位置の行番号、桁(列番号)、1行のテキストを取得する"""
        if not self.is_alive(): 
            return 0, 0, ""
            
        current_index = self.log_text.index("insert")
        line_str, col_str = current_index.split(".")
        line_num, col_num = int(line_str), int(col_str)
        line_text = self.log_text.get("insert linestart", "insert lineend")
        
        return line_num, col_num, line_text

    ################################################################################
    # タグで色を付けるとカーソルでのスクロールデフォルト処理が重いので処理を乗っ取る
    # 移動、選択範囲変更を自前処理
    # 選択範囲の操作は、SHFIFT+(カーソル、ページアップダウン、マウス)
    # SHIFTなしでのマウスドラッグ（新規選択）
    ################################################################################
    def _on_key_move_or_select(self, event):
        try:
            keysym = event.keysym
            state = event.state
            
            has_shift = bool(state & 0x0001) or "Shift" in keysym
            
            # プラットフォーム別に単語移動用の修飾キーとCommandキーを特定する
            if IS_MAC:
                has_word_modifier = bool(state & 0x0010) or "Option" in keysym
                has_ctrl = bool(state & (0x8 | 0x100 | 0x1000))
            else:
                has_word_modifier = bool(state & 0x0004) or "Control" in keysym
                has_ctrl = has_word_modifier
            
            # 各キーごとの移動仕様マッピング
            direction = -1 if keysym in ["Up", "Left", "Prior", "Home"] else 1
            op = "+" if direction > 0 else "-"

            #new_index = None
            modifier = None
            
            if keysym in ["Up", "Down"]:
                modifier = f"insert {op} 1 lines"
            elif keysym in ["Left", "Right"]:
                if not has_word_modifier:
                    modifier = f"insert {op} 1 chars"
                else:
                    current_idx = self.log_text.index("insert")
                    line, char = map(int, current_idx.split('.'))
                    line_text = self.log_text.get(f"{line}.0", f"{line}.end")
                    
                    is_right = (keysym == "Right")
                    target_char = self._get_next_word_char_pos(line_text, char, is_right)
                    
                    if target_char == -1:
                        modifier = "insert + 1 lines linestart" if is_right else "insert - 1 lines lineend"
                    else:
                        modifier = f"{line}.{target_char}"
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
            if modifier is not None:
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

        self.highlight_current_line()

        return "break"

    # 単語単位でのカーソル移動
    # 組み込みだと上手く動作しない為
    # 英数字記号のみ対応だがこちらの方がまだマシかもしれない
    def _get_next_word_char_pos(self, text, start_char, is_right):
        text_len = len(text)
        
        def get_type(c):
            return 0 if c in " \t" else (1 if (c.isalnum() or c == "_") else 2)
            
        if is_right:
            if start_char >= text_len:
                return -1
                
            pos = start_char
            current_type = get_type(text[pos])
            
            if current_type != 0:
                while pos < text_len and get_type(text[pos]) == current_type:
                    pos += 1
                return pos
            else:
                while pos < text_len and get_type(text[pos]) == 0:
                    pos += 1
                return pos if pos < text_len else text_len
        else:
            if start_char <= 0:
                return -1
                
            pos = start_char - 1
            if get_type(text[pos]) == 0:
                while pos >= 0 and get_type(text[pos]) == 0:
                    pos -= 1
                return pos + 1
            else:
                current_type = get_type(text[pos])
                while pos >= 0 and get_type(text[pos]) == current_type:
                    pos -= 1
                return pos + 1

    def _on_mouse_press(self, event):
        """マウスドラッグ開始時の起点インデックス記録処理"""
        self._select_start_index = self.log_text.index(f"@{event.x},{event.y}")

        self.log_text.mark_set("insert", self._select_start_index)
        self.highlight_current_line()

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

        self.highlight_current_line()
        return "break"

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

        self.highlight_current_line()
        return "break"

    ################################################################################
    # ジャンプと履歴管理機能 (Ctrl+G / F4 / Alt+Left / Alt+Right)
    ################################################################################
    def cmd_jump_to_address(self, event=None):
        """カーソル行のラベルを抽出してジャンプする"""
        if not self.is_alive(): return "break"
        
        line_num, col_num, text = self.get_current_line_info()
        
        # モジュールからラベルを抽出
        
        labels = z80disAssembler.extract_all_addresses_from_label(text)
        if not labels:
            return "break"

        target_address = None
        
        for address, start_col, end_col in labels:
            # 行頭はラベル定義なので除外
            if start_col == 0:
                continue
            target_address = address
            break

        if target_address is not None:
            self.execute_jump(target_address)
        return "break"

    def execute_jump(self, address):
        """指定アドレスを検索して履歴に登録しつつ移動する"""
        label_str = f"{z80disAssembler.to_hex_label(address)}"
        
        dest_index = self.log_text.search(label_str + ":", "1.0", tk.END)
        if not dest_index:
            return

        current_index = self.log_text.index("insert")

        # --- 履歴の更新 ---
        if self.history_index == -1:
            self._add_to_history(current_index)
        else:
            hist_line = self.history[self.history_index].split(".")[0]
            curr_line = current_index.split(".")[0]
            if hist_line != curr_line:
                self._add_to_history(current_index)
            else:
                self.history[self.history_index] = current_index

        # 移動先を履歴に登録
        self._add_to_history(dest_index)
        
        # 実際の移動
        self._go_to_index(dest_index)

    def _add_to_history(self, index_str):
        """履歴リストの現在位置以降を切り捨てて、新しい位置を追加する"""
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
            
        if not self.history or self.history[-1] != index_str:
            self.history.append(index_str)
            self.history_index = len(self.history) - 1

    def cmd_history_back(self, event=None):
        """履歴を戻る"""
        if self.history_index >= 0:
            self.history_index -= 1
            if self.history_index >= 0:
                self._go_to_index(self.history[self.history_index])
        return "break"

    def cmd_history_forward(self, event=None):
        """履歴を進む"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self._go_to_index(self.history[self.history_index])
        return "break"

    def _go_to_index(self, index_str):
        """指定のインデックスへカーソルを移動してフォーカスする"""
        self.log_text.mark_set("insert", index_str)
        self.log_text.see("insert")
        # 選択範囲があれば解除する
        self.log_text.tag_remove("sel", "1.0", tk.END)
        self._select_start_index = None

        self.highlight_current_line()

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
        # 矢印キー、Home、End、PageUp/Down、修飾キーなどは通過させる（カーソル移動を許可）
        if event.keysym in [
            'Left', 'Right', 'Up', 'Down', 
            'Home', 'End', 'Prior', 'Next', 
            'Control_L', 'Control_R', 'Meta_L', 'Meta_R',
            'Escape','F4'
        ]:
            return None # 通常の挙動（移動）を許可
            
        state = event.state
        
        # Command(Mac) または Control(Win/Linux) のキー修飾判定
        if IS_MAC:
            ctrl_cmd = bool(state & (0x8 | 0x10 | 0x100 | 0x1000))
        else:
            ctrl_cmd = bool(state & 0x0004)

        # コピー、全選択、終了などのショートカット許可
        if ctrl_cmd:
            if event.keysym.lower() in ['c', 'a', 'f4', 'w', 'g', 'Left', 'Right', 'bracketleft', 'bracketright']:
                return None # 許可

        # Alt (Option) キーの操作
        is_alt = bool(state & 0x0010) if IS_MAC else bool(state & (0x0008 | 0x20000))
        if is_alt:
            if event.keysym in ['Left', 'Right']:
                return None

        # キー単体（大文字・小文字両方）の履歴・ジャンプショートカット入力を許可する
        if event.keysym.lower() in ['g', 'b', 'f']:
            return None

        # それ以外の文字入力、BackSpace、Delete、Enterなどはすべてブロック（書き換え禁止）
        return "break"

    #############################################
    def put(self, message):
        """すべて書き換え"""
        if not self.is_alive(): return
        self.log_text.delete("1.0", tk.END)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.mark_set("insert", "1.0")
        self.log_text.see("1.0")

        self.apply_color_tags()
        
        # 新しいテキストになったら履歴をクリア
        self.history.clear()
        self.history_index = -1
        
        self.log_text.focus_set()

        self.highlight_current_line()

    #############################################
    def log(self, message):
        """末尾に追加"""
        if not self.is_alive(): return
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

        self.apply_color_tags()
        self.log_text.focus_set()

        self.highlight_current_line()

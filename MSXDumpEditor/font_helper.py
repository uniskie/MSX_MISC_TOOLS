import tkinter as tk
from tkinter import font

#--------------------------------------------------------------------------
# Font helper
#--------------------------------------------------------------------------
# 指定した高さ(px)に一番近くてそれ以下のサイズのフォントを得る
def get_font_for_pixel_height(target_height, font_family="TkDefaultFont"):
    low = 1
    high = target_height * 2
    best_size = low
    
    if font_family in tk.font.names():
        # Tk***Font
        base_options = tk.font.nametofont(font_family).configure()
    else:
        base_options = {"family": font_family}

    while low <= high:
        mid = (low + high) // 2
        current_options = base_options.copy()
        current_options["size"] = mid
        test_font = tk.font.Font(**current_options)
        
        current_height = test_font.metrics("linespace")
        
        if current_height <= target_height:
            best_size = mid
            low = mid + 1
        else:
            high = mid - 1
            
    final_options = base_options.copy()
    final_options["size"] = best_size
    return tk.font.Font(**final_options)

# フォントを名前で探す
def has_font(font_name):
    root = tk.Tk()
    root.withdraw()
    if font_name in tk.font.names():
        result = tk.font.nametofont(font_name).configure()
    else:
        font_list = tk.font.families()
        result =  font_name in font_list
    root.destroy()
    return result

# リストを渡して存在するフォントを見つける
def search_font_list(font_list):
    for f in font_list:
        if result := has_font(f):
            return f
    return None

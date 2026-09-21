import os
import sys
from PIL import Image

def generate_multi_size_ico(base_name):
    # 16pxから256pxまでの一般的なICO対応サイズ
    target_sizes = [16, 32, 48, 256]
    
    existing_images = {}
    
    # 1. 存在するファイルをチェックして読み込む
    for size in target_sizes:
        filename = f"{base_name}_{size}.bmp"
        if os.path.exists(filename):
            try:
                # 透過色などを扱えるようにRGBAモードで読み込み
                img = Image.open(filename).convert("RGBA")
                existing_images[size] = img
                print(f"【発見】: {filename} を読み込みました。")
            except Exception as e:
                print(f"【エラー】: {filename} の読み込みに失敗しました: {e}")
                
    if not existing_images:
        print(f"【エラー】: 「{base_name}_[サイズ].bmp」に一致するファイルがカレントディレクトリに見つかりません。")
        sys.exit(1)

    # 2. 不足しているサイズを「最も近いサイズ」から自動生成
    final_images = {}
    for size in target_sizes:
        if size in existing_images:
            final_images[size] = existing_images[size]
        else:
            # 存在するサイズの中から、絶対値の差が最も小さい（近い）サイズを見つける
            closest_size = min(existing_images.keys(), key=lambda x: abs(x - size))
            source_img = existing_images[closest_size]
            
            # ドット絵がボケないように Image.NEAREST (最近傍法) でリサイズ
            resized_img = source_img.resize((size, size), resample=Image.NEAREST)
            final_images[size] = resized_img
            print(f"【自動生成】: {base_name}_{size}.bmp がないため、{closest_size}px からスケールしました。")

    # 3. マルチサイズICOとして保存（降順で並び替えて一番大きいサイズをベースにする）
    sorted_sizes = sorted(target_sizes, reverse=True)
    base_size = sorted_sizes[0]
    base_image = final_images[base_size]
    
    append_images = [final_images[s] for s in sorted_sizes[1:]]
    ico_sizes = [(s, s) for s in sorted_sizes]
    
    output_filename = f"{base_name}.ico"
    base_image.save(
        output_filename,
        format="ICO",
        sizes=ico_sizes,
        append_images=append_images
    )
    print(f"\n【成功】: マルチサイズアイコン '{output_filename}' が完成しました！")

if __name__ == "__main__":
    # 引数が正しく与えられているかチェック
    if len(sys.argv) < 2:
        print("【使用方法】: python スクリプト名.py [ベースファイル名]")
        print("【例】      : python convert_ico.py my_icon")
        sys.exit(1)
        
    # 第1引数をベースファイル名として取得
    target_base_name = sys.argv[1]
    generate_multi_size_ico(target_base_name)

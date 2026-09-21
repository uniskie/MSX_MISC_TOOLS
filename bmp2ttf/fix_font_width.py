import argparse
import sys
from pathlib import Path
from fontTools.ttLib import TTFont

def main():
    parser = argparse.ArgumentParser(
        description="FontForge等で出力した等幅フォントの xAvgCharWidth (平均横幅) を修復するツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""【使用例】
  # 1. 元のフォントから正しい幅をコピーして別名保存
  py fix_font.py target.ttf -r original.ttf -o fixed.ttf

  # 2. 幅の数値を直接指定して修正
  py fix_font.py target.ttf -w 1024 -o fixed.ttf

  # 3. 出力先 (-o) を省略（target_fixed.ttf が自動生成されます）
  py fix_font.py target.ttf -r original.ttf

  # 4. 元のファイルを直接上書き保存 (--overwrite)
  py fix_font.py target.ttf -r original.ttf --overwrite
"""
    )

    # 必須の位置引数
    parser.add_argument(
        "target",
        type=Path,
        help="修正対象のフォントファイル (.ttf / .otf)"
    )

    # 幅の取得方法（-r か -w のどちらか必須）
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-r", "--ref",
        type=Path,
        dest="ref_font",
        help="参照する元フォントファイル（このフォントの xAvgCharWidth をコピーします）"
    )
    group.add_argument(
        "-w", "--width",
        type=int,
        dest="width_val",
        help="設定したい xAvgCharWidth の数値（例: 1024, 500 など）"
    )

    # 出力先の設定
    out_group = parser.add_mutually_exclusive_group()
    out_group.add_argument(
        "-o", "--output",
        type=Path,
        dest="output",
        help="出力ファイル名（省略時は [元ファイル名]_fixed.ttf）"
    )
    out_group.add_argument(
        "--overwrite",
        action="store_true",
        help="修正対象ファイルを直接上書きする"
    )

    # 引数なしで実行された場合はヘルプを表示
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    # 対象ファイルの存在チェック
    if not args.target.is_file():
        print(f"エラー: 対象ファイルが見つかりません: {args.target}", file=sys.stderr)
        sys.exit(1)

    # 目標とする幅の決定
    target_width = None
    if args.ref_font:
        if not args.ref_font.is_file():
            print(f"エラー: 参照フォントが見つかりません: {args.ref_font}", file=sys.stderr)
            sys.exit(1)
        try:
            ref_font = TTFont(args.ref_font)
            target_width = ref_font["OS/2"].xAvgCharWidth
            print(f"[参照元] {args.ref_font.name} の xAvgCharWidth: {target_width}")
        except Exception as e:
            print(f"エラー: 参照フォントの読み込みに失敗しました: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        target_width = args.width_val

    # 出力ファイル名の決定
    if args.overwrite:
        output_path = args.target
    elif args.output:
        output_path = args.output
    else:
        output_path = args.target.with_name(f"{args.target.stem}_fixed{args.target.suffix}")

    # フォント修正・保存処理
    try:
        font = TTFont(args.target)
        if "OS/2" not in font:
            print("エラー: 対象フォントに OS/2 テーブルが存在しません。", file=sys.stderr)
            sys.exit(1)

        current_width = font["OS/2"].xAvgCharWidth
        print(f"[修正前] {args.target.name} の xAvgCharWidth: {current_width}")

        # 値の書き換え
        font["OS/2"].xAvgCharWidth = target_width
        font.save(output_path)

        print(f"[修正後] xAvgCharWidth を {target_width} に設定しました。")
        print(f"-> 保存先: {output_path}")

    except Exception as e:
        print(f"エラー: フォントの処理中にエラーが発生しました: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

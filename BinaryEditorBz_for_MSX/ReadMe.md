#  Binary Editor Bz 1.9.9.1 for MSX

Binary Editor Bzは
構造体表示機能や分割画面と比較、メモリのビットマップ表示機能があります。 

Binary Editor Bz for MSX は、MSX向けビットマップビュー拡張改造版です。

  - インストーラ―版 [BzEditor-1.9.9.1-for-msx.exe](BzEditor-1.9.9.1-for-msx.exe)
  - ポータブル版 [Bz1991Portable-for-MSX.zip](Bz1991Portable-for-MSX.zip)
  - 改変版ソースコードリポジトリ   
    https://gitlab.com/uniskie/binaryeditorbz-for-msx

- 追加機能以外の使い方ヘルプ  
  https://devil-tamachan.github.io/BZDoc/


### ビットマップ表示の追加機能

ビットマップビューにMSX向けの機能を追加拡張しました。  
他に、ビットマップビュー周りのバグを修正しています。


![1bit color 8x8 tile](../img/BzEditor_for_msx.png)

- 1bit color 8x8 （フォントやキャラ用） ... SCREEN 0,1,2,4 / SPRITE / FONT
- 2bit color ... SCREEN 6,9
- 4bit color ... SCREEN 5,7
- 8bit coolor YJK ... SCREEN 10,11
- 8bit coolor YJK/RGB ... SCREEN 12
- width 512
- MSX16 (パレット)
- MSX256 (パレット)
- MSX_logo (パレット)

実験で以下のモードも追加しました。

- 2bit color FC
- 2bit color GB
- 4BIT color SFC/PCE
- 8BIT color SFC

1bit color 8x8 モードではカーソル位置とアドレスの関係もそれっぽくしています。  

### ビットマップ表示 指定例

ビットマップ表示： 表示(V)→ビットマップ表示(B)

（Address Tooltipは意外と邪魔な時があるので、イラっとしたらOFFにすると良いです）

![8bit color YJK](../img/BzEditor_for_msx_2.png)

| カラー形式 | カラーパレット | 表示幅 | 表示用途 |
|---|---|---|---|
| tile/1bit color 8x8   | ---      | width 256 | SCREEN 0/1/2/4、SPRITE、FONT等 8x8ドットキャラ表示 |
| tile/1bit color 8x16  | ---      | width 256 | 16x16 SPRITE等 |
| tile/1bit color 16x16 | ---      | width 256 | 漢字ROM等 |
| 2bit color            | MSX_logo |width 512 | SCREEN 6/9、MSX起動ロゴ等 |
| 4bit color            | MSX16    | width 256 | SCREEN 5 |
| 4bit color            | MSX16    | width 512 | SCREEN 7 |
| 8bit color            | MSX256   | width 256 | SCREEN 8 |
| 8bit color YJK/RGB    | MSX16    | width 256 | SCREEN 10/11 |
| 8bit color YJK         | ---     | width 256 | SCREEN 12 |


### おまけ：特殊タイルモード
![Hierarchical menu](../img/BzEditor_for_msx_4.png)

| カラー形式 | カラーパレット | 変換処理 | 表示用途 |
|---|---|---|---|
| tile/2bit color 8x8   (FC)      | GB_GRAY/GB_GREEN/GRAY4等 | 8x8 pixel (1bpp 8byte) x2プレーン | ファミコン BG/スプライト |
| tile/2bit color 8x16  (FC)      | GB_GRAY/GB_GREEN/GRAY4等 | 8x8 pixel (1bpp 8byte) x2プレーン | ファミコン BG/スプライト |
| tile/2bit color 16x16 (FC)      | GB_GRAY/GB_GREEN/GRAY4等 | (1bitx2) 8x8 pixel x2プレーン | ファミコン BG/スプライト |
| tile/2bit color 8x8   (GB)      | GB_GRAY/GB_GREEN/GRAY4等 | 行インターレース(1 line = 8bit x2) | ゲームボーイ BG/スプライト |
| tile/2bit color 8x16  (GB)      | GB_GRAY/GB_GREEN/GRAY4等 | 行インターレース(1 line = 8bit x2) | ゲームボーイ BG/スプライト |
| tile/2bit color 16x16 (GB)      | GB_GRAY/GB_GREEN/GRAY4等 | 行インターレース(1 line = 8bit x2) | ゲームボーイ BG/スプライト |
| tile/4bit color 8x8             | MSX16/MIO/GRAY4等 | 2bpp 8x8 tile | メガドライブ等 BG/スプライト |
| tile/4bit color 8x16            | MSX16/MIO/GRAY4等 | 2bpp 8x8 tile | メガドライブ等 BG/スプライト |
| tile/4bit color 16x16           | MSX16/MIO/GRAY4等 | 2bpp 8x8 tile | メガドライブ等 BG/スプライト |
| tile/4bit color 8x8   (SFC/PCE) | MSX16/MIO/GRAY4等 | 行インターレース(1 line = 8bit x2) x 8x8 pixel x2プレーン | スーパーファミコン/PCエンジン BG/スプライト |
| tile/4bit color 8x16  (SFC/PCE) | MSX16/MIO/GRAY4等 | 行インターレース(1 line = 8bit x2) x 8x8 pixel x2プレーン | スーパーファミコン/PCエンジン BG/スプライト |
| tile/4bit color 16x16 (SFC/PCE) | MSX16/MIO/GRAY4等 | 行インターレース(1 line = 8bit x2) x 8x8 pixel x2プレーン | スーパーファミコン/PCエンジン BG/スプライト |
| tile/8bit color 8x8   (SFC)     | MSX16/MIO/GRAY4等 | 行インターレース(1 line = 8bit x2) x 8x8 pixel x2プレーン | スーパーファミコン BG/スプライト |
| tile/8bit color 8x16  (SFC)     | MSX16/MIO/GRAY4等 | 行インターレース(1 line = 8bit x2) x 8x8 pixel x2プレーン | スーパーファミコン BG/スプライト |
| tile/8bit color 16x16 (SFC)     | MSX16/MIO/GRAY4等 | 行インターレース(1 line = 8bit x2) x 8x8 pixel x2プレーン | スーパーファミコン BG/スプライト |

![GB 8x8 preview](../img/BzEditor_for_msx_3.png)

### ビットマップ表示の表示更新について

バイナリデータの編集時、ビットマップビューがリアルタイムで更新されるようにしました。
重い場合はビットマップビューを閉じて編集してください。

### パレットの編集

メニューの「ツール(T)」→「カスタムパレットの編集」  
で開くフォルダーにあるテキストファイル が、  
カラーパレット定義ファイルです。

（置いてあるファイル名がBITMAPビューの右クリックメニューから選べます。）

MSX向けに`MSX16.txt`、`MSX256.txt`、`MSX_logo.txt`を用意しましたが、
各自お好きな定義ファイルをを追加してください。

![](../img/BZ_MSX_PALETTE.png)

[追加パレットのみのセット](BZPalettes-for-MSX.zip)

### おまけ：パレット変換ツール

[ブラウザで実行](../docs/BzTool/palette.html)

[ソースファイルまたはオフライン実行](./palette.html)

javascript対応ブラウザで使用してください。  
ちゃんとテストしてません。  

変換方法は
- SFC16bit(RGB555)パレット
- MSX16bit(RGB333)パレット
- MSX8bitx2パレット（バイトの並びが逆順）
が選べます。

## 変更履歴

- 2025/08/02  
  - パレット変換ツールを適当に作ったので追加

- 2025/05/27  
  - ビットマップビューにSFC用8bitタイル形式追加
  - カラータイプのタイル形式をサブメニューに移動
  - 4bit SFCタイル形式はPCEと共通なので文言変更
  - パレット定義ファイル名変更・追加
    - GRAY_GB → GB_GRAY
    - GREEN_GB → GB_GREEN
    - GRAY_2bit → GRAY4
    - GRAY_4bit → GRAY16
    - 新規追加 → GRAY256
    - 新規追加 → MIO

- 2025/05/25  
  - ビットマップビューにFC/GB/SFC/MD向け表示追加
  - カラーパレットフォルダ名をPalletsからPalettesに変更
  - ビットマップビューリアルタイム更新に変更  
    重い場合はビットマップビューを閉じて編集してください

- 2025/05/20  
  - ビットマップビューに 2bit color を追加  
  - カラーパレットに MSX_logoを追加  

- 2025/05/19  
  元からあったビットマップビューのバグを一通り修正  
  - アドレス←→スクロール位置変換式が相互に機能するように書き直し
  - データの取得でキャッシュヒットチェックが正常に機能していないのを修正
  - 元データが表示必要サイズに足りない場合に空きを足す処理を追加
  - モード切替での位置引継ぎとドキュメント読み込み時のリセットの使い分け

- 2025/05/18  
  MSX向け改造版公開  
  - 1bit color 8x8 （フォントやキャラ用）
  - 2bit color
  - 8bit coolor YJK
  - 8bit coolor YJK/RGB
  - width 512
  - パレットにMSX16、MSX256を追加

## 謝辞

元ソースコードはご厚意によって公開されている物です。  
使用ライセンスは以下の通りです。

Binary Editor BZ - original version -  
[Binary Editor BZ 1.6.2 Win](http://www.vcraft.jp/soft/bz.html) (New BSD License) --- Copyright (c) 1996-2004 [c.mos](https://www.vcraft.jp/index.html)

Binary Editor BZ - 改造版 -  
[Binary Editor BZ 1.9.8 Win](https://gitlab.com/devill.tamachan/binaryeditorbz/) (New BSD License) --- modify 1996-2004, 2012-2022 [tamachan](https://devil-tamachan.github.io/BZDoc/)

私が変更した部分のソースコードについては一切の責任を持ちません。
改変は自由です。（私の名前は記載も不要です）




#  Binary Editor Bz 1.9.8.9 for MSX

Binary Editor Bzは
構造体表示機能や分割画面と比較、メモリのビットマップ表示機能があります。 

Binary Editor Bz for MSX は、MSX向けビットマップビュー拡張改造版です。

  - インストーラ―版 [BzEditor-1.9.8.9-for-msx.exe](BzEditor-1.9.8.9-for-msx.exe)
  - ポータブル版 [Bz1989Portable-for-MSX.zip](Bz1987Portable-for-MSX.zip)
  - 改変版ソースコードリポジトリ   
    https://gitlab.com/uniskie/binaryeditorbz-for-msx

- 追加機能以外の使い方ヘルプ  
  https://devil-tamachan.github.io/BZDoc/


### ビットマップ表示の追加機能

ビットマップビューにMSX向けの機能を追加拡張しました。  
他に、ビットマップビュー周りのバグを修正しています。

- 1bit color 8x8 （フォントやキャラ用） ... SCREEN 0,1,2,4 / SPRITE / FONT
- 2bit color ... SCREEN 6,9
- 4bit color ... SCREEN 5,7
- 8bit coolor YJK ... SCREEN 10,11
- 8bit coolor YJK/RGB ... SCREEN 12
- width 512
- MSX16 (パレット)
- MSX256 (パレット)
- MSX_logo (パレット)

1bit color 8x8 tile  
![](../img/BzEditor_for_msx.png)

8bit color YJK  
![](../img/BzEditor_for_msx_2.png)

1bit color 8x8 モードではカーソル位置とアドレスの関係もそれっぽくしています。  

### ビットマップ表示 指定例

ビットマップ表示： 表示(V)→ビットマップ表示(B)

（Address Tooltipは意外と邪魔な時があるので、イラっとしたらOFFにすると良いです）

| カラー形式 | カラーパレット | 表示幅 | 表示用途 |
|---|---|---|---|
| 1bit color 8x8 tile | --- | width 256 | SCREEN 0/1/2/4、SPRITE、FONT等 8x8ドットキャラ表示 |
| 2bit color | MSX_logo 等 |width 512 | SCREEN 6/9、MSX起動ロゴ等 |
| 4bit color | MSX16 等 | width 256 | SCREEN 5 |
| 4bit color | MSX16 等 | width 512 | SCREEN 7 |
| 8bit color | MSX256 | width 256 | SCREEN 8 |
| 8bit color YJK/RGB | MSX16 等 | width 256 | SCREEN 10/11 |
| 8bit color YJK | --- | width 256 | SCREEN 12 |

### ビットマップ表示の表示更新について

ビットマップビューはリアルタイムでは更新されません。

バイナリを変更した場合は、ビットマップビューを右クリックして何か設定を選ぶと更新されます。
（現在と同じもので可）

ビットマップ表示をOFF→ONとしたり、保存して再度開いたりした場合、更新と同時に表示位置が先頭に戻ります。

### パレットの編集

メニューの「ツール(T)」→「カスタムパレットの編集」  
で開くフォルダーにあるテキストファイル が、  
カラーパレット定義ファイルです。

（置いてあるファイル名がBITMAPビューの右クリックメニューから選べます。）

MSX向けに`MSX16.txt`、`MSX256.txt`、`MSX_logo.txt`を用意しましたが、
各自お好きな定義ファイルをを追加してください。

![](../img/BZ_MSX_PALETTE.png)

[追加パレットのみのセット](BZPallets-for-MSX.zip)


## 変更履歴

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




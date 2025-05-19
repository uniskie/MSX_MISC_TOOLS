# Binary Editor Bz 1.9.8.8 for MSX

Binary Editor Bzは
構造体表示機能や分割画面と比較、メモリのビットマップ表示機能があります。 

## MSX向けビットマップビュー拡張版

ビットマップビューにMSX向けの機能を追加拡張しました。  
他に、ビットマップビュー周りのバグを修正しています。

- 1bit color 8x8 （フォントやキャラ用）
- 1bit color
- 8bit coolor YJK
- 8bit coolor YJK/RGB
- width 512

- パレットにMSX16、MSX256を追加

1bit color 8x8 モードではカーソル位置とアドレスの関係もそれっぽくしています。  
8bit coolor YJK/RGB モードではパレットも指定してください。  

- インストーラ―版 [BzEditor-1.9.8.7-for-msx.exe](BzEditor-1.9.8.7-for-msx.exe)
- ポータブル版 [Bz1987Portable-for-MSX.zip](Bz1987Portable-for-MSX.zip)
- 改変版ソースコードリポジトリ   
  https://gitlab.com/uniskie/binaryeditorbz-for-msx

- オリジナル版  
  https://devil-tamachan.github.io/BZDoc/ 

- 1bit color 8x8 tile  
  ![](../img/BzEditor_for_msx.png)

- 8bit color YJK  
  ![](../img/BzEditor_for_msx_2.png)

### 変更履歴

- 2025/05/19  
  元からあったビットマップビューのバグを一通り修正  
  - アドレス←→スクロール位置変換式が相互に機能するように書き直し
  - データの取得でキャッシュヒットチェックが正常に機能していないのを修正
  - 元データが表示必要サイズに足りない場合に空きを足す処理を追加
  - モード切替での位置引継ぎとドキュメント読み込み時のリセットの使い分け

- 2025/05/18  
  MSX向け改造版公開  
  - 1bit color 8x8 （フォントやキャラ用）
  - 1bit color
  - 8bit coolor YJK
  - 8bit coolor YJK/RGB
  - width 512
  - パレットにMSX16、MSX256を追加

## 追加MSXパレット

[BZPallets-for-MSX.zip](BZPallets-for-MSX.zip)

追加パレットのセットです。

### 使い方

Bz Editorのメニューの  
ツール→カスタムパレットの編集  
で開くフォルダーに、
MSX16.txt と MSX256.txt を入れて再起動してみてください。 

（Bz for MSX改造版には最初から入っています。）

![](../img/BZ_MSX_PALETTE.png)



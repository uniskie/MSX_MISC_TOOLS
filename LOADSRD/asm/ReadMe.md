## ASM

[TNIASM](http://www.tni.nl/products/tniasm.html) を使用します。

### LOADSRD.BIN の作成

```tniasm LOADSRD.ASM```

### SRX.BIN の作成

```tniasm SRX.ASM```

### SRX2.BIN の作成

```tniasm SRX2.ASM```

### 各ファイル説明

メインのソースファイル

| ファイル名 | 説明 
|---|---|
| [LOADSRD.ASM](LOADSRD.ASM) | LOADSRD.BINのソース
| [SRX.ASM](SRX.ASM) | SRX.BINのソース
| [SRX2.ASM](SRX2.ASM) | SRX2.BINのソース

機能別ファイル（INCLUDEされるもの）

| ファイル名 | LOADSRD | SRX | SRX2 | 説明 
|---|---|---|---|--|
| [GSF_LOAD.ASM](GSF_LOAD.ASM) | ● | ● | ● | 1) *.SC?/*.SR? のロード&VRAM書き込み<BR> 2) VDPへパレットセット                             
| [VDPCOMAN.ASM](VDPCOMAN.ASM) | × | ● | ● | VDPコマンドの実行、VDPコマンドの終了待ち
| [SPRCLOCK.ASM](SPRCLOCK.ASM) | × | ● | × | スプライト#0-7のパターンへ現在の時間を書き込む<br>(HH:MM:SS形式)(16x16モード用=パターン番号はの4倍数)
| [SPRCLOC2.ASM](SPRCLOC2.ASM) | × | ● | ● | 渡した8バイト配列にHH:MM:SS形式で時刻を返す<BR>0=" "(空白)、1～10=数字の0～9、11=":"(区切り文字)
| [SPR_SET.ASM ](SPR_SET.ASM ) | × | × | ● | 符号付16ビット*4でワンセット(Y、X、パターン番号、フラグ)が32個並んだ配列を渡してスプライトを表示する。<BR>優先度シャッフル、自動アニメ、左見切れ対策等あり<BR>座標は15.1固定小数点数。実際に表示される位置は(X/2,Y/2)

その他ファイル(共有ルーチン等)

| ファイル名 | 説明 
|---|---|
| [USR_FUNC.ASM](USR_FUNC.ASM) | USR()関数で呼び出されたときに使う処理
| [VRAM.ASM    ](VRAM.ASM    ) | VRAM書き込み開始やスプライトアトリビュートテーブルの設定など


## ASM

[TNIASM](http://www.tni.nl/products/tniasm.html) を使用します。

### LOADSRD.BIN の作成

```tniasm LOADSRD.ASM```

### SRX.BIN の作成

```tniasm SRX.ASM```

### 各ファイル説明

メインのソースファイル

| ファイル名 | 説明 
|---|---|
| [LOADSRD.ASM](LOADSRD.ASM) | LOADSRD.BINのソース
| [SRX.ASM](SRX.ASM) | SRX.BINのソース

機能別ファイル（INCLUDEされるもの）

| ファイル名 | LOADSRD | SRX | 説明 
|---|---|
| [GSF_LOAD.ASM](GSF_LOAD.ASM) | ● | ● | 1) *.SC?/*.SR? のロード&VRAM書き込み<BR>2) VDPへパレットセット
| [VDPCOMAN.ASM](VDPCOMAN.ASM) | × | ● | VDPコマンドの実行、VDPコマンドの終了待ち
| [SPRCLOCK.ASM](SPRCLOCK.ASM) | × | ● | スプライト#0-7のパターンへ現在の時間を書き込む (HH:MM:SS形式)(16x16モード用=パターン番号はの4倍数)



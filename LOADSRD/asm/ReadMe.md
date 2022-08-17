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


### SRX.BIN エントリー
|宣言例 |呼び出し例 | アドレス | ラベル | ソースファイル | 内容 |
|---|---|---|---|---|---|
| DEFUSR1=&HD000 ' LOAD_SRD             | U$=USR1("FILENAME.EXT")| $D000 | LOAD_SRD | GSF_LOAD.ASM | GS/BSAVEファイルをロード。 ファイル名は```"8文字.3文字"```であること
| DEFUSR2=&HD003 ' SET_PAL              | U=USR2(VARPTR(PL(0)))  | $D003 | SET_PLT  | GSF_LOAD.ASM | PLT配列を使ってパレット反映。<BR>INT配列なら```DIM PL(15):COPY"PALETTE.PLT"TO PL```など
| DEFUSR3=&HD006 ' TIMER SPRITE         | U=USR3(VARPTR(SR(0)))  | $D006 | SPR_TIME | SPRCLOC2.ASM | INTスプライト配列(8個)のパターン番号に時刻を反映。0=”"、1～10=数字の"0"～"9"、11=":"
| DEFUSR4=&HD009 ' VDP COMMAND          | U=USR4(VARPTR(CM(0)))  | $D009 | VDPCMD   | VDPCOMAN.ASM | VDPコマンドを実行。配列の中身はVDPコマンドリファレンス参照。（NX、NYがマイナスの場合や範囲外などの自動補正あり）
| DEFUSR5=&HD00C ' VDP COMMAND WAIT     | U=USR5(0)              | $D00C | WAITVDPC | VDPCOMAN.ASM | VDPコマンドの実行終了まで待つ
| DEFUSR6=&HD00F ' SET SPRITE           | U=USR6(VARPTR(SR(0)))  | $D00F | SPR_SET  | SPR_SET.ASM  | INTスプライト配列32セット(8バイト*32個)を渡してスプライトを表示する。<BR>パターン番号に対応するカラーデータの自動設定、ダブルバッファによる画面乱れ対策、画面左見切れ対策、上下左右ループ表示なし、自動アニメ、優先度対策の並び替えちらつき表示 など
| DEFUSR7=&HD012 ' SET SPRITE COLOR     | U=USR7(VARPTR(SC(0)))  | $D012 | SPC_SET  | SPR_SET.ASM  | パターン番号に対応するスプライトカラー配列。16バイト*64個
| DEFUSR8=&HD015 ' SET SPRITE INTERRUPT | U=USR8(-1)<BR>U=USR8(1)<BR>U=USR8(2) | $D015 | SPR_INT  | SPR_SET.ASM  | スプライトの優先順位対策の並び替えをvsyncで自動実行。<BR>-1を指定すると解除***(終了時に解除を忘れずに)***<BR>重くなるので基本的に使わない



# ASM

[TNIASM](http://www.tni.nl/products/tniasm.html) を使用します。

## LOADSRD.BIN の作成

```tniasm LOADSRD.ASM```

## SRX.BIN の作成

```tniasm SRX.ASM```

## SRX2.BIN の作成

```tniasm SRX2.ASM```

## 各ファイル説明

メインのソースファイル

| ファイル名 | 説明 
|---|---|
| [LOADSRD.ASM](LOADSRD.ASM) | LOADSRD.BINのソース
| [SRX.ASM](SRX.ASM) | SRX.BINのソース
| [SRX2.ASM](SRX2.ASM) | SRX2.BINのソース

### 機能別ファイル（INCLUDEされるもの）

| ファイル名 | LOADSRD | SRX | SRX2 | 説明 
|---|---|---|---|--|
| [GSF_LOAD.ASM](GSF_LOAD.ASM) | ● | ● | ● | 1) *.SC?/*.SR? のロード&VRAM書き込み<BR> 2) VDPへパレットセット                             
| [VDPCOMAN.ASM](VDPCOMAN.ASM) | × | ● | ● | VDPコマンドの実行、VDPコマンドの終了待ち
| [SPRCLOCK.ASM](SPRCLOCK.ASM) | × | ● | × | スプライト#0-7のパターンへ現在の時間を書き込む<br>(HH:MM:SS形式)(16x16モード用=パターン番号はの4倍数)
| [SPRCLOC2.ASM](SPRCLOC2.ASM) | × | ● | ● | 渡した8バイト配列にHH:MM:SS形式で時刻を返す<BR>0=" "(空白)、1～10=数字の0～9、11=":"(区切り文字)
| [SPR_SET.ASM ](SPR_SET.ASM ) | × | × | ● | 符号付16ビット*4でワンセット(Y、X、パターン番号、フラグ)が32個並んだ配列を渡してスプライトを表示する。<BR>優先度シャッフル、自動アニメ、左見切れ対策等あり<BR>座標は15.1固定小数点数。実際に表示される位置は(X/2,Y/2)

### その他ファイル(共有ルーチン等)

| ファイル名 | 説明 
|---|---|
| [USR_FUNC.ASM](USR_FUNC.ASM) | USR()関数で呼び出されたときに使う処理
| [VRAM.ASM    ](VRAM.ASM    ) | VRAM書き込み開始やスプライトアトリビュートテーブルの設定など

## SRX.BIN エントリー
|宣言例 |呼び出し例 | アドレス | ラベル | ソースファイル | 内容 |
|---|---|---|---|---|---|
| DEFUSR1=&HD000 ' LOAD_SRD             | U$=USR1("FILENAME.EXT")| $D000 | LOAD_SRD | GSF_LOAD.ASM | GS/BSAVEファイルをロード。 ファイル名は```"8文字.3文字"```であること
| DEFUSR2=&HD003 ' SET_PAL              | U=USR2(VARPTR(PL(0)))  | $D003 | SET_PLT  | GSF_LOAD.ASM | PLT配列を使ってパレット反映。<BR>INT配列なら```DIM PL(15):COPY"PALETTE.PLT"TO PL```など
| DEFUSR3=&HD006 ' TIMER SPRITE         | U=USR3(VARPTR(SR(0)))  | $D006 | SPR_TIME | SPRCLOC2.ASM | INTスプライト配列(8個)のパターン番号に時刻を反映。0=”"、1～10=数字の"0"～"9"、11=":"
| DEFUSR4=&HD009 ' VDP COMMAND          | U=USR4(VARPTR(CM(0)))  | $D009 | VDPCMD   | VDPCOMAN.ASM | VDPコマンドを実行。配列の中身はVDPコマンドリファレンス参照。（NX、NYがマイナスの場合や範囲外などの自動補正あり）
| DEFUSR5=&HD00C ' VDP COMMAND WAIT     | U=USR5(0)              | $D00C | WAITVDPC | VDPCOMAN.ASM | VDPコマンドの実行終了まで待つ
| DEFUSR6=&HD00F ' SET SPRITE           | U=USR6(VARPTR(SR(0)))  | $D00F | SPR_SET  | SPR_SET.ASM  | [スプライト管理配列](#スプライト管理配列)を渡してスプライトを表示する。 (```PUT SPRITE```より便利な機能多数)
| DEFUSR7=&HD012 ' SET SPRITE COLOR     | U=USR7(VARPTR(SC(0)))  | $D012 | SPC_SET  | SPR_SET.ASM  | スプライトパターン番号に対応するカラー配列を登録。(```16バイト*64個```の配列)
| DEFUSR8=&HD015 ' SET SPRITE INTERRUPT | U=USR8(-1)<BR>U=USR8(1)<BR>U=USR8(2) | $D015 | SPR_INT  | SPR_SET.ASM  | スプライトの優先順位対策の並び替えをvsyncで自動実行。<BR>-1を指定すると解除<br> ***(終了時に解除を忘れずに)***<BR>重くなるので基本的に使わない

## ```SRX2.BIN``` スプライト管理機能

1) 16x16サイズスプライトモード専用
2) 実質2枚重ね合わせスプライト専用
2) SCREEN5以上対応 [^対応画面]
3) 8枚以上並んだら点滅表示 [^点滅モード]
4) 座標は画面座標の2倍で管理 [^固定小数点座標]
5) パターン番号はPUT SPRITE準拠。0～63で指定。[^パターン番号とジェネレータアドレス]
6) マイナスや画面範囲以上の座標もOK。[^表示範囲]
7) 自動アニメーション機能。[^アニメーション機能] [^アニメーションとパターン番号]
8) パターンに紐づけされたカラーテーブルを指定する。パターンに合わせたカラーを自動転送。 [^カラーテーブル]

[^対応画面]:  SCREEN4はダブルバッファが確保しづらいので保留。

[^点滅モード]: VSYNC併用の並び替えモードは実用にならないので廃止予定。

[^固定小数点座標]: ```疑似固定小数点数15:1``` = 0.5単位。

[^パターン番号とジェネレータアドレス]: 参照するパターンジェネレータアドレスは```パターン番号*8*4```の位置。

[^表示範囲]: Xがマイナスの場合も左端から少しずつ見える。急に現れたり、画面反対側にワープしたりしない。

[^アニメーション機能]: ウェイト、2パターン or 4パターンアニメから選択。

[^アニメーションとパターン番号]: 2枚重ね合わせスプライトが前提になっているので、パターン番号+0、+2、+4、+6を使用する

[^カラーテーブル]: 16x16スプライトモード専用なので、```16バイト*64個```のデータ

## ```SRX2.BIN``` スプライト管理配列

```DIM SR(3,31)```または```DIM SR(8*32-1)```のように宣言

|位置|内容|
|---|---|
|SR(0,n)|SPRITE #n の Y座標 (**画面座標を2倍した値**)|
|SR(1,n)|SPRITE #n の X座標 (**画面座標を2倍した値**)|
|SR(2,n)|SPRITE #n の パターン番号 (**PUTSPRITE同様に**)|
|SR(3,n)|SPRITE #n の 特殊フラグ|

### 特殊フラグの内容 (スプライト管理配列)

```SR(3,n)```の特殊フラグの内容

|位置|内容|
|---|---|
|bit 15|非表示フラグ。-1を指定すると分かりやすい|
|bit 3-0|アニメーションウェイト。1～15を指定すると自動アニメーション有効。指定した間隔で変化。単位はメインループ数|
|bit 4  |アニメーションパターン数。0なら2パターン。1なら4パターン。|
|bit 11-8|内部管理(アニメーションワークエリア) 現在のウェイトカウント|
|bit 13-12|内部管理(アニメーションワークエリア) 現在のアニメパターン番号オフセット|


#### 特殊フラグ 例
|値|動作
|---|---
| -1 |非表示
|&H02|メインループ2回ごとにアニメ（2パターンアニメ）
|&h14|メインループ4回ごとにアニメ（4パターンアニメ）

具体的な使い方は [TESTN.BAS](../samples/.sensitive/KUONAI/TESTN.BAS)、[TESTV1.BAS](../samples/.sensitive/KUONAI/TESTV1.BAS)、[TESTV2.BAS](../samples/.sensitive/KUONAI/TESTV2.BAS) を参照



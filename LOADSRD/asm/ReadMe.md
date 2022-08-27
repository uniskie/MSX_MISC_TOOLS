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
| [SRX.ASM](SRX.ASM)         | SRX.BINのソース
| [SRX2.ASM](SRX2.ASM)       | SRX2.BINのソース

### 機能別ファイル（INCLUDEされるもの）

| ファイル名 | LOADSRD | SRX | SRX2 | 説明 |
|---|---|---|---|--|
| [GSF_LOAD.ASM](GSF_LOAD.ASM) | ● | ● | ● | 1) *.SC?/*.SR? のロード&VRAM書き込み<BR> 2) VDPへパレットセット |
| [VDPCOMAN.ASM](VDPCOMAN.ASM) | × | ● | ● | VDPコマンドの実行、VDPコマンドの終了待ち |
| [SPRCLOCK.ASM](SPRCLOCK.ASM) | × | ● | × | スプライト#0-7のパターンへ現在の時間を書き込む<br>(HH:MM:SS形式)(16x16モード用=パターン番号はの4倍数) |
| [SPRCLOC2.ASM](SPRCLOC2.ASM) | × | × | ● | 渡した8バイト配列にHH:MM:SS形式で時刻を返す<BR>0=" "(空白)、1～10=数字の0～9、11=":"(区切り文字) |
| [SPR_SET.ASM](SPR_SET.ASM)   | × | × | ● | 符号付16ビット*4でワンセット(Y、X、パターン番号、フラグ)が32個並んだ配列を渡してスプライトを表示する。<BR>優先度シャッフル、自動アニメ、左見切れ対策等あり<BR>座標は15.1固定小数点数。実際に表示される位置は(X/2,Y/2) |
| [BGM.ASM](BGM.ASM)           | × | × | ● | HRA BGM DRIVER |

### その他ファイル(共有ルーチン等)

| ファイル名 | 説明 |
|---|---|
| [USR_FUNC.ASM](USR_FUNC.ASM) | USR()関数で呼び出されたときに使う処理 |
| [VRAM.ASM](VRAM.ASM)         | VRAM書き込み開始やスプライトアトリビュートテーブルの設定など |
| [BGMDRV.ASM](BGMDRV.ASM)     | hra!さんのPSG用BGMドライバー 本体 |
| [BGMDRV_D.ASM](BGMDRV_D.ASM) | hra!さんのPSG用BGMドライバー 定義など |

## LOADSRD.BINエントリー

> **Warning** 使用上の注意
>
> ***&hB000～&hCFFFを画像ロード時のディスクバッファとして使用します。***  
>
> プログラム本体は&D000～&hDFFFを使用します。  
> 環境によってはメモリが足りないケースが多いかもしれません。   
> 漢字BASICモードではまず暴走すると思います。
>
> 使用する際は、```CLEAR 100,&hB000``` 等で初期化をしてください。   
> また、フリーエリアはリセット直後に```HIMEM.BAS```などで確認してください。   

|宣言例 |呼び出し例 |アドレス | ラベル | ソースファイル | 内容 |
|---|---|---|---|---|---|
| DEFUSR1=&HD000| U$=USR1("FILENAME.EXT")|$D000| LOAD_SRD | GSF_LOAD.ASM | GS/BSAVEファイルをロード。 ファイル名は```"8文字.3文字"```であること
| DEFUSR2=&HD003| U=USR2(VARPTR(PL(0)))  |$D003| SET_PLT  | GSF_LOAD.ASM | PLT配列を使ってパレット反映。<BR>INT配列なら```DIM PL(15):COPY"PALETTE.PLT"TO PL```など

## SRX.BINエントリー

> **Warning** 使用上の注意
>
> ***&hB000～&hCFFFを画像ロード時のディスクバッファとして使用します。***  
>
> プログラム本体は&D000～&hDFFFを使用します。  
> 環境によってはメモリが足りないケースが多いかもしれません。   
> 漢字BASICモードではまず暴走すると思います。
>
> 使用する際は、```CLEAR 100,&hB000``` 等で初期化をしてください。   
> また、フリーエリアはリセット直後に```HIMEM.BAS```などで確認してください。   

|宣言例 |呼び出し例 |アドレス | ラベル | ソースファイル | 内容 |
|---|---|---|---|---|---|
| DEFUSR1=&HD000| U$=USR1("FILENAME.EXT")|$D000| LOAD_SRD | GSF_LOAD.ASM | GS/BSAVEファイルをロード。 ファイル名は```"8文字.3文字"```であること
| DEFUSR2=&HD003| U=USR2(VARPTR(PL(0)))  |$D003| SET_PLT  | GSF_LOAD.ASM | PLT配列を使ってパレット反映。<BR>INT配列なら```DIM PL(15):COPY"PALETTE.PLT"TO PL```など
| DEFUSR3=&HD006| U=USR3(VARPTR(SR(0)))  |$D006| SPR_TIME | SPRCLOCK.ASM | スプライト#0-7のパターンへ現在の時間を書き込む<br>(HH:MM:SS形式)(16x16モード用=パターン番号はの4倍数)

## SRX2.BINエントリー

簡易スプライトエンジンやBGM DRIVERを組み込んであるため、機械語プログラムの先頭は$D000ではなく$COOOからになります。

> **Warning** 使用上の注意
>
> ***&hB000～&hBFFFを画像ロード時のディスクバッファとして使用します。***  
>
> プログラム本体は&D000～&hDFFFを使用します。  
> 環境によってはメモリが足りないケースが多いかもしれません。   
> 漢字BASICモードではまず暴走すると思います。
>
> 使用する際は、```CLEAR 100,&hB000``` 等で初期化をしてください。   
> また、フリーエリアはリセット直後に```HIMEM.BAS```などで確認してください。   

|宣言例 |呼び出し例 |アドレス | ラベル | ソースファイル | 内容 |
|---|---|---|---|---|---|
| DEFUSR1=&HC000| U$=USR1("FILENAME.EXT")|$C000| LOAD_SRD    | GSF_LOAD.ASM | GS/BSAVEファイルをロード。 ファイル名は```"8文字.3文字"```であること
| DEFUSR2=&HC003| U=USR2(VARPTR(PL(0)))  |$C003| SET_PLT     | GSF_LOAD.ASM | PLT配列を使ってパレット反映。<BR>INT配列なら```DIM PL(15):COPY"PALETTE.PLT"TO PL```など
| DEFUSR3=&HC006| U=USR3(VARPTR(SR(0)))  |$C006| SPR_TIME    | SPRCLOC2.ASM | INTスプライト配列(8個)のパターン番号に時刻を反映。0=”"、1～10=数字の"0"～"9"、11=":"
| DEFUSR4=&HC009| U=USR4(VARPTR(CM(0)))  |$D009| VDPCMD      | VDPCOMAN.ASM | VDPコマンドを実行。配列の中身はVDPコマンドリファレンス参照。（NX、NYがマイナスの場合や範囲外などの自動補正あり）
| DEFUSR5=&HC00C| U=USR5(0)              |$D00C| WAITVDPC    | VDPCOMAN.ASM | VDPコマンドの実行終了まで待つ
| DEFUSR6=&HC00F| U=USR6(VARPTR(SR(0)))  |$D00F| SPR_SET     | SPR_SET.ASM  | [スプライト管理配列](#SRX2.BINスプライト管理配列)を渡してスプライトを表示する。 (```PUT SPRITE```より便利な機能多数)
| DEFUSR7=&HC012| U=USR7(VARPTR(SC(0)))  |$D012| SPC_SET     | SPR_SET.ASM  | スプライトパターン番号に対応するカラー配列を登録。(```16バイト*64個```の配列)
| DEFUSR8=&HC015| U=USR8(-1)             |$D015| SPR_INT     | SPR_SET.ASM  | スプライト並び替えをVSYNC割り込みで実行。<BR>-1を指定すると解除。
| DEFUSR9=&HC018| U=USR9(1)              |$C018| BGM_INIT    | BGM.ASM      | HRA BGM DRIVER 初期化/終了。パラメータが1なら開始（割り込み開始）、それ以外なら終了（割り込み開放）
| DEFUSR9=&HC01B| U=USR9(&HB000)         |$C01B| BGM_PLAY    | BGM.ASM      | HRA BGM DRIVER 指定したアドレスのBGMデータを演奏する
| DEFUSR9=&HC01E| U=USR9(0)              |$C01E| BGM_STOP    | BGM.ASM      | HRA BGM DRIVER BGMの演奏を停止する
| DEFUSR9=&HC021| U=USR9(&HBF00)         |$C021| BGM_SE      | BGM.ASM      | HRA BGM DRIVER 指定したアドレスの効果音を再生する
| DEFUSR9=&HC024| U=USR9(10)             |$C024| BGM_FADEOUT | BGM.ASM      | HRA BGM DRIVER フェードアウト開始。1～255を指定する。指定した値*15フレームでフェードアウトが終わる
| DEFUSR9=&HC027| U=USR9(0)              |$C027| BGM_IS_PLAY | BGM.ASM      | HRA BGM DRIVER 演奏中なら0以外が返ってくる

> **Warning**  
> $D015(```U=USR8(1)```や```U=USR8(2)```)でVSYNCモードを使用した場合は、
> プログラム終了時に開放を忘れないでください。  
> タイマーフック```H.TIMI```を使用しますので機械語領域が破損した場合に暴走します。


## ```SRX2.BIN```スプライト管理機能

1) 16x16サイズスプライトモード専用
2) 実質2枚重ね合わせスプライト専用
2) SCREEN5以上対応 [^1]
3) 8枚以上並んだら点滅表示 [^2]
4) 座標は画面座標の2倍で管理 [^3]
5) パターン番号はPUT SPRITE準拠。0～63で指定。[^4]
6) マイナスや画面範囲以上の座標もOK。[^5]
7) 自動アニメーション機能。 [^6] [^7]
8) パターンに紐づけされたカラーテーブルを指定する。パターンに合わせたカラーを自動転送。 [^8]

[^1]:  SCREEN4はダブルバッファが確保しづらいので保留。

[^2]: VSYNC併用の並び替えモードは実用にならないので廃止予定。

[^3]: ```疑似固定小数点数15:1``` = 0.5単位。

[^4]: 参照するパターンジェネレータアドレスは```パターン番号*8*4```の位置。

[^5]: Xがマイナスの場合も左端から少しずつ見える。急に現れたり、画面反対側にワープしたりしない。

[^6]: ウェイト、2パターン or 4パターンアニメから選択。

[^7]: 2枚重ね合わせスプライトが前提になっているので、パターン番号+0、+2、+4、+6を使用する

[^8]: 16x16スプライトモード専用なので、```16バイト*64個```のデータ


## ```SRX2.BIN```スプライト管理配列

```DIM SR(3,31)```または```DIM SR(8*32-1)```のように宣言

|位置|内容|
|---|---|
|SR(0,n)|SPRITE #n の Y座標 (**画面座標を2倍した値**)|
|SR(1,n)|SPRITE #n の X座標 (**画面座標を2倍した値**)|
|SR(2,n)|SPRITE #n の パターン番号 (**PUTSPRITE同様に**)|
|SR(3,n)|SPRITE #n の 特殊フラグ|

### スプライト管理配列：特殊フラグの内容

```SR(3,n)```：特殊フラグ

|bit| 15| 14| 13| 12| 11| 10|  9|  8|  7|  6|  5|  4|  3|  2|  1|  0| 
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| -- | h | . | o |  o| c | c | c | c | . | . | . | p | w | w | w | w | 

|位置|ビット名|内容|
|---|---|---|
|bit 3-0|wwww|アニメーションウェイト。<br>1～15を指定すると自動アニメーション有効。<br>指定した間隔で変化。単位はメインループ数|
|bit 4  |p|アニメーションパターン数。0なら2パターン。1なら4パターン。|
|bit 15|h|非表示フラグ。-1を指定すると分かりやすい|
| - | - | -
|bit 11-8|cccc| ※内部管理 (アニメーションワークエリア) 現在のウェイトカウント|
|bit 13-12|oo| ※内部管理 (アニメーションワークエリア) 現在のアニメパターン番号オフセット|


#### 特殊フラグ 例
|値|動作
|---|---
| -1 |非表示
|&H02|メインループ2回ごとにアニメ（2パターンアニメ）
|&h14|メインループ4回ごとにアニメ（4パターンアニメ）

具体的な使い方は [TESTN.BAS](../samples/.sensitive/KUONAI/TESTN.BAS)、[TESTV1.BAS](../samples/.sensitive/KUONAI/TESTV1.BAS)、[TESTV2.BAS](../samples/.sensitive/KUONAI/TESTV2.BAS) を参照



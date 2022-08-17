# **Sensitive Contents**

ここは少しセンシティブなデータがあります。

取り扱いにはご注意ください。

There is some sensitive data here.

Please handle with care.

## TESTN.BAS / KUONAIV.BAS

スプライトが8個以上並んだ時に点滅表示させるサンプルを兼ねています。

32個のスプライトエントリを一括管理しています。  
VRAMへの書き込みはターボRのVDPウェイトが原因でVBLANK期間に収まらない為、ダブルバッファを使用して書き込んだ後に表示をスワップしています。

1) TESTN.BASはメインループで点滅並び替え実行
2) KUANNAIV.BASはVSYNCで点滅並び替え実行、メインループからも書き込み
3) KUANNAIV.BASはVSYNCで点滅並び替え実行、1フレーム表示が遅れるがメインループからは書き込まない

1は点滅が粗い代わりに軽いです。  
2は点滅が細かい代わりに重いです。(メインループとVSYNCで並び替え&書き込みを行うため)
3は1フレーム遅れる代わりに2よりも速度が少し早くなります。

BASICでの処理の遅さ対策で作った2ですが、デメリットが多いので、1を使用した方が良さそうです。  
また、管理するスプライトの範囲を32個全部ではなく、半分などにすればもっと軽くなりそうです。  

### 実行ファイル

|FILE|DESC   |
|---|---|
| [TESTN.BAS](TESTN.BAS)| FLICK SPRITE IMMIDIATE MODE (Blinking is rough but light) |
| [TESTV1.BAS](TESTV1.BAS)| FLICK SPRITE H.TIMI MODE 1 (Blinking is fine but very heavy) |
| [TESTV2.BAS](TESTV2.BAS)| FLICK SPRITE H.TIMI MODE 2 (Blinking is fine but heavy) |
| [SRX2.BIN](../../../asm)| [../../../asm/SRX2.ASM](../../../asm/SRX2.ASM) がソースファイル |

### SRX.BIN エントリー
|宣言例 |呼び出し例 | アドレス | ラベル | ソースファイル | 内容 |
|---|---|---|---|---|---|
| DEFUSR1=&HD000 ' LOAD_SRD             | U$=USR1("FILENAME.EXT")| $D000 | LOAD_SRD | GSF_LOAD.ASM | GS/BSAVEファイルをロード。 ファイル名は```"8文字.3文字"```であること
| DEFUSR2=&HD003 ' SET_PAL              | U=USR2(VARPTR(PL(0)))  | $D003 | SET_PLT  | GSF_LOAD.ASM | PLT配列を使ってパレット反映。<BR>INT配列なら```DIM PL(15):COPY"PALETTE.PLT"TO PL```など
| DEFUSR3=&HD006 ' TIMER SPRITE         | U=USR3(VARPTR(SR(0)))  | $D006 | SPR_TIME | SPRCLOC2.ASM | INTスプライト配列(8個)のパターン番号に時刻を反映。0=”"、1～10=数字の"0"～"9"、11=":"
| DEFUSR4=&HD009 ' VDP COMMAND          | U=USR4(VARPTR(CM(0)))  | $D009 | VDPCMD   | VDPCOMAN.ASM | VDPコマンドを実行。配列の中身はVDPコマンドリファレンス参照。（NX、NYがマイナスの場合や範囲外などの自動補正あり）
| DEFUSR5=&HD00C ' VDP COMMAND WAIT     | U=USR5(0)              | $D00C | WAITVDPC | VDPCOMAN.ASM | VDPコマンドの実行終了まで待つ
| DEFUSR6=&HD00F ' SET SPRITE           | U=USR6(VARPTR(SR(0)))  | $D00F | SPR_SET  | SPR_SET.ASM  | ***16x16スプライト専用***<BR>INTスプライト配列32セット(8バイト*32個)を渡してスプライトを表示する。<BR>パターン番号に対応するカラーデータの自動設定、ダブルバッファによる画面乱れ対策、画面左見切れ対策、上下左右ループ表示なし、自動アニメ、優先度対策の並び替えちらつき表示 など
| DEFUSR7=&HD012 ' SET SPRITE COLOR     | U=USR7(VARPTR(SC(0)))  | $D012 | SPC_SET  | SPR_SET.ASM  | ***16x16スプライト専用***<BR>パターン番号に対応するスプライトカラー配列を登録。16バイト*64個
| DEFUSR8=&HD015 ' SET SPRITE INTERRUPT | U=USR8(-1)<BR>U=USR8(1)<BR>U=USR8(2) | $D015 | SPR_INT  | SPR_SET.ASM  | スプライトの優先順位対策の並び替えをvsyncで自動実行。<BR>-1を指定すると解除 ***(終了時に解除を忘れずに)***<BR>重くなるので基本的に使わない

### スプライト管理機能

1) 16X16サイズスプライトモード専用
2) 実質2枚重ね合わせスプライト専用
2) SCREEN5以上対応 (SCREEN4はダブルバッファが確保しづらいので保留)
3) VSYNC併用の並び替えモードは実用にならないので廃止予定
4) 座標は画面座標の2倍で管理(疑似固定小数点数/0.5単位)
5) パターン番号はPUT SPRITE準拠。0～63で指定。参照するパターンジェネレータアドレスは 番号*8*4 の位置。
6) マイナスや画面範囲以上の座標もOK。左端で急に現れたり、画面反対側にワープしたりしない
7) 自動アニメーション機能。1～15のアニメーション間隔指定、2パターンアニメ、4パターンアニメから選択<BR>2枚重ね合わせスプライト前提のためパターン番号+0、+2、+4、+6のパターンを表示する。
8) パターンに紐づけされたカラーテーブルを指定することで、パターンに合わせたカラーを自動転送<br>16x16前提なので、16バイト*64個の配列

### スプライト管理配列

DIM SR(3,31)などと定義

|位置|内容|
|---|---|
|SR(0,n)|SPRITE #n の Y座標 (**画面座標を2倍した値**)|
|SR(1,n)|SPRITE #n の X座標 (**画面座標を2倍した値**)|
|SR(2,n)|SPRITE #n の パターン番号 (**PUTSPRITE同様に**)|
|SR(3,n)|SPRITE #n の 特殊フラグ|

### 特殊フラグの内容

SR(3,n)の特殊フラグの内容

|位置|内容|
|---|---|
|bit 15|非表示フラグ。-1を指定すると分かりやすい|
|bit 3-0|アニメーションウェイト。1～15を指定すると自動アニメーション有効。指定した間隔で変化。単位はメインループ数|
|bit 4  |アニメーションパターン数。0なら2パターン。1なら4パターン。|
|bit 11-8|内部管理(アニメーションワークエリア) 現在のウェイトカウント|
|bit 13-12|内部管理(アニメーションワークエリア) 現在のアニメパターン番号オフセット|


特殊フラグ 例)
|値|動作
|---|---
| -1 |非表示
|&H02|メインループ2回ごとにアニメ（2パターンアニメ）
|&h14|メインループ4回ごとにアニメ（4パターンアニメ）

具体的な使い方は [TESTN.BAS](TESTN.BAS)、[TESTV1.BAS](TESTV1.BAS)、[TESTV2.BAS](TESTV2.BAS) を参照


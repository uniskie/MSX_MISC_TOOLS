## ASM

バックアップ活用テクニック PART16掲載。POCO氏制作 MSX2用「アセンブルシステム」
を使用します。

MSX2ASM.BAS
MSX2ASM.BIN
は各自ご用意ください。
(無ければtniasm用のソースファイルをご使用ください)

### 準備

```RUN"MSX2ASM.BAS"```
でリセット後、ASM命令が拡張されたらOK。

### LOADSRD.BOF の作成

```_ASM("LOADSRD")```

### SRX.BOF の作成

```_ASM("SRX")```

### SRX2.BOF の作成

```_ASM("SRX2")```

```RENAME *.BOF *.BIN```

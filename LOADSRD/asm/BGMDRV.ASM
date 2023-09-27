;TAB 4
; Port for tniasm By Uniske
; -----------------------------------------------------------------------------
;	PSG BGM DRIVER
; -----------------------------------------------------------------------------
;	Copyright (c) 2020 Takayuki Hara
;	http://hraroom.s602.xrea.com/msx/software/index.html
;
;	Permission is hereby granted, free of charge, to any person obtaining a
;	copy of this software and associated documentation files (the
;	"Software"), to deal in the Software without restriction, including
;	without limitation the rights to use, copy, modify, merge, publish,
;	distribute, sublicense, and/or sell copies of the Software, and to
;	permit persons to whom the Software is furnished to do so, subject to
;	the following conditions:
;
;	The above copyright notice and this permission notice shall be
;	included in all copies or substantial portions of the Software.
;
;	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
;	EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
;	MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
;	NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
;	LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
;	OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
;	WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
; =============================================================================
;	2009/09/30	t.hara
;	2019/07/15	t.hara	Modified for ZMA
;	2021/11/21	t.hara	Modified initialize of PSG registers
; -----------------------------------------------------------------------------

include "BGMDRV_D.ASM"

; -----------------------------------------------------------------------------
;	AY-3-8910 [PSG] レジスタ定義
; -----------------------------------------------------------------------------
PSG_REG_ADR:		EQU	0xA0	; アドレスラッチ
PSG_REG_WRT:		EQU	0xA1	; データライト

; -----------------------------------------------------------------------------
;	BIOS関連
; -----------------------------------------------------------------------------
BASE_SLOT:		EQU	0xA8	; 基本スロット指定ポート
EXT_SLOT:		EQU	0xFFFF	; 拡張スロット指定ポート

; -----------------------------------------------------------------------------
;	演奏タスク情報構造体オフセット定義
;	INFO_*
; -----------------------------------------------------------------------------
INFO_PLAY_ADR_L:	EQU	0	; 演奏中アドレス [0なら停止中]
INFO_PLAY_ADR_H:	EQU	1	; 〃
INFO_WAIT_COUNT_L:	EQU	2	; 待機時間
INFO_WAIT_COUNT_H:	EQU	3	; 〃
INFO_EFF_FREQ_L:	EQU	4	; 実効周波数
INFO_EFF_FREQ_H:	EQU	5	; 〃
INFO_TONE_FREQ_L:	EQU	6	; 設定周波数
INFO_TONE_FREQ_H:	EQU	7	; 〃
INFO_EFF_VOL:		EQU	8	; 実効音量
INFO_TONE_VOL:		EQU	9	; 設定音量
INFO_VIB_WAIT:		EQU	10	; ビブラート遅延時間
INFO_ENV_STATE:		EQU	11	; エンベロープステート
INFO_ENV_VOL:		EQU	12	; エンベロープ音量
INFO_VIB_INDEX:		EQU	13	; ビブラートインデックス
INFO_SOUND_FONT_L:	EQU	14	; 再生中の音色データのアドレス
INFO_SOUND_FONT_H:	EQU	15	; 〃
INFO_NOISE_FREQ:	EQU	16	; ノイズ周波数
INFO_SEL_SFONT_L:	EQU	17	; 音色データのアドレス
INFO_SEL_SFONT_H:	EQU	18	; 音色データのアドレス
INFO_SIZE:		EQU	19	; INFO構造体のサイズ

; -----------------------------------------------------------------------------
;	音色データ構造体オフセット定義
;	SFONT_*
; -----------------------------------------------------------------------------
SFONT_VIB_WAVE:		EQU	0	; ビブラート波形
SFONT_AR:		EQU	32	; エンベロープの AR
SFONT_DR:		EQU	33	; エンベロープの DR
SFONT_SL:		EQU	34	; エンベロープの SL
SFONT_SR:		EQU	35	; エンベロープの SR
SFONT_RR:		EQU	36	; エンベロープの RR
SFONT_VIB_WAIT:		EQU	37	; ビブラート遅延時間
SFONT_NOISE:		EQU	38	; ノイズ周波数 [SFONT_VIB_WAIT + 1 であることが前提]
SFONT_FREQ_L:		EQU	39	; ドラム用基準周波数[L]
SFONT_FREQ_H:		EQU	40	; ドラム用基準周波数[H]

; -----------------------------------------------------------------------------
;	初期化処理
;	input:
;	なし
;	output
;	なし
;	break
;	a, b, c, d, e, f, h, l
;	comment
;	なし
; -----------------------------------------------------------------------------
bgmdriver_initialize:
	ld	hl, play_info_ch0
	ld	de, play_info_ch0 + 1
	ld	bc, INFO_SIZE * 3 - 1
	xor	a, a
	ld	[hl], a
	ldir
	ret

; -----------------------------------------------------------------------------
;	演奏開始処理
;	input:
;	hl	...	BGMデータのアドレス
;	output
;	なし
;	break
;	a, b, c, d, e, f, h, l, ix
;	comment
;	なし
; -----------------------------------------------------------------------------
bgmdriver_play:
	; まず現状の演奏を停止する
	push	hl
	call	bgmdriver_stop
	; 演奏開始のための初期化処理を実施する
	pop	hl
	di
	; BGMデータのアドレスを保存
	ld	[play_bgm_data_adr], hl
	ld	ix, [play_bgm_data_adr]
	; ch0 の演奏データアドレスを取得
	ld	e, [ix + 0]
	ld	d, [ix + 1]
	add	hl, de
	ld	[play_info_ch0 + INFO_PLAY_ADR_L], hl
	; ch1 の演奏データアドレスを取得
	ld	hl, [play_bgm_data_adr]
	ld	e, [ix + 2]
	ld	d, [ix + 3]
	add	hl, de
	ld	[play_info_ch1 + INFO_PLAY_ADR_L], hl
	; ch2 の演奏データアドレスを取得
	ld	hl, [play_bgm_data_adr]
	ld	e, [ix + 4]
	ld	d, [ix + 5]
	add	hl, de
	ld	[play_info_ch2 + INFO_PLAY_ADR_L], hl
	; フェードアウト中ならフェードアウトを停止する
	xor	a, a
	ld	[play_master_volume_speed], a
	ld	[play_master_volume_wait], a
	ld	[play_master_volume], a
	ei
	ret

; -----------------------------------------------------------------------------
;	演奏停止処理
;	input:
;	なし
;	output
;	なし
;	break
;	a, b, c, d, e, f, h, l
;	comment
;	なし
; -----------------------------------------------------------------------------
bgmdriver_stop:
	; 停止処理の途中で割り込まれて挙動不審にならないように割禁
	di
	; 停止処理
	ld	hl, play_info_ch0
	call	bgmdriver_init_play_info
	ld	hl, play_info_ch1
	call	bgmdriver_init_play_info
	ld	hl, play_info_ch2
	call	bgmdriver_init_play_info
	; 割禁解除
	ei
	ret

; -----------------------------------------------------------------------------
;	演奏中チェック
;	input:
;	なし
;	output
;	Zフラグ ... 1 なら停止中, 0 なら演奏中
;	break
;	a, f, ix
;	comment
;	なし
; -----------------------------------------------------------------------------
bgmdriver_check_playing:
	di
	ld	ix, play_info_ch0
	ld	a, [ix + INFO_PLAY_ADR_L]
	or	a, [ix + INFO_PLAY_ADR_H]
	ld	ix, play_info_ch1
	or	a, [ix + INFO_PLAY_ADR_L]
	or	a, [ix + INFO_PLAY_ADR_H]
	ld	ix, play_info_ch2
	or	a, [ix + INFO_PLAY_ADR_L]
	or	a, [ix + INFO_PLAY_ADR_H]
	ei
	ret

; -----------------------------------------------------------------------------
;	フェードアウト処理
;	input:
;	a	...	フェードアウト速度[1～255]
;	output
;	なし
;	break
;	a
;	comment
;	なし
; -----------------------------------------------------------------------------
bgmdriver_fadeout:
	; 停止処理の途中で割り込まれて挙動不審にならないように割禁
	di
	ld	[play_master_volume_speed], a
	xor	a, a
	ld	[play_master_volume_wait], a
	ld	[play_master_volume], a
	ei
	ret

; -----------------------------------------------------------------------------
;	音停止処理
;	input:
;	なし
;	output
;	なし
;	break
;	a, b, c, d, e, f, h, l
;	comment
;	なし
; -----------------------------------------------------------------------------
bgmdriver_mute_psg:
	di
	ld	d, 0
	ld	hl, bgmpdriver_init_data
	ld	c, PSG_REG_ADR
	ld	b, 16

bgmdriver_mute_psg_loop:
	out	[c], d			; FOR b=0 TO 15:SOUND b, 0:NEXT
	inc	d
	ld	a, [hl]
	out	[PSG_REG_WRT], a
	inc	hl
	djnz	bgmdriver_mute_psg_loop
	ei
	ret

bgmpdriver_init_data:
	;	0  1  2  3  4  5  6  7            8  9 10 11 12 13 14 15
	db	0, 0, 0, 0, 0, 0, 0, 0x80 + 0x3F, 0, 0, 0, 0, 0, 0, 0, 0

; -----------------------------------------------------------------------------
;	効果音開始処理
;	input:
;	hl	...	効果音データのアドレス
;	output
;	なし
;	break
;	a
;	comment
;	なし
; -----------------------------------------------------------------------------
bgmdriver_play_sound_effect:
	; 効果音開始のための初期化処理を実施する
	push	hl
	di
	ld	a, [play_sound_effect_priority]		; 再生中の効果音よりプライオリティが高いか？
	cp	a, [hl]
	jp	c, bgmdriver_play_sound_effect_skip	; 低ければ再生しない
	ld	a, [hl]
	ld	[play_sound_effect_priority], a		; プライオリティを更新
	inc	hl
	ld	[play_sound_effect_adr], hl		; 効果音データのアドレス
	xor	a, a
	ld	[play_sound_effect_wait_count], a	; 待機時間 0
	ld	[play_sound_effect_freq+0], a		; 再生周波数 0
	ld	[play_sound_effect_freq+1], a
	ld	[play_sound_effect_noise_freq], a	; ノイズ周波数 0
	ld	[play_sound_effect_volume], a		; 音量 0
	inc	a
	ld	[play_sound_effect_active], a		; 効果音再生開始
bgmdriver_play_sound_effect_skip:
	pop	hl
	ei
	ret

; -----------------------------------------------------------------------------
;	演奏タスク情報を初期化する[内部]
;	input:
;	hl	...	初期化する演奏タスク情報のアドレス
;	output
;	なし
;	break
;	a, b, c, d, e, h, l
;	comment
;	なし
; -----------------------------------------------------------------------------
bgmdriver_init_play_info:
	ld	e, l
	ld	d, h
	inc	de
	ld	bc, INFO_SIZE - 1
	xor	a, a
	ld	[hl], a
	ldir
	ret

; -----------------------------------------------------------------------------
;	演奏処理ルーチン
;	input:
;	なし
;	output
;	なし
;	break
;	なし
;	comment
;	1/60秒間隔で call されることを期待しているルーチンであり、通常は
;	H_TIMI をフックしたルーチンから呼び出す。
;	割り込み処理を想定しているため、レジスタは破壊しない。
; -----------------------------------------------------------------------------
bgmdriver_interrupt_handler:
	; 演奏ルーチン呼び出し
	ld	ix, play_info_ch0
	call	bgmdriver_play_ch
	ld	ix, play_info_ch1
	call	bgmdriver_play_ch
	ld	ix, play_info_ch2
	call	bgmdriver_play_ch
	; 効果音処理ルーチン呼び出し
	call	bgmdriver_sound_effect
	; フェードアウト処理
	call	bgmdriver_fadeout_proc
	; ミキサールーチン呼び出し
	call	bgmdriver_mixer
	ret

; -----------------------------------------------------------------------------
;	演奏処理ルーチン[1ch分] [内部]
;	input:
;	ix	...	演奏処理を実施する演奏タスク情報のアドレス
;	output
;	なし
;	break
;	a, b, c, d, e, f, h, l
;	comment
;	なし
; -----------------------------------------------------------------------------
bgmdriver_play_ch:
	; 演奏中であるか調べる
	ld	a, [ix + INFO_PLAY_ADR_L]
	or	a, [ix + INFO_PLAY_ADR_H]
	ret	z				; 演奏中でなければ何もせずに脱ける
	; 待機時間であるか調べる
	ld	l, [ix + INFO_WAIT_COUNT_L]
	ld	h, [ix + INFO_WAIT_COUNT_H]
	ld	a, l
	or	a, h
	jr	z, bgmdriver_check_next_data
	; 待機時間を更新
	dec	hl
	ld	[ix + INFO_WAIT_COUNT_L], l
	ld	[ix + INFO_WAIT_COUNT_H], h
	jp	bgmdriver_update_vibrato
	; 次の演奏データを読み取る
bgmdriver_check_next_data:
	ld	l, [ix + INFO_PLAY_ADR_L]
	ld	h, [ix + INFO_PLAY_ADR_H]
	ld	a, [hl]
	inc	hl
	; 演奏データをデコード
	cp	a, 96
	jp	c, bgmdriver_keyon		; 0～95 は KeyOn メッセージ
	cp	a, 101
	jp	c, bgmdriver_drum_keyon		; 96～100 は KeyOn メッセージ
	jp	z, bgmdriver_keyoff		; 101 は KeyOff メッセージ
	cp	a, 103
	jp	c, bgmdriver_rest		; 102 は 休符メッセージ
	jp	z, bgmdriver_volume		; 103 は 音量設定メッセージ
	cp	a, 105
	jp	c, bgmdriver_sound_font		; 104 は 音色設定メッセージ
	jp	z, bgmdriver_jump		; 105 は アドレスジャンプメッセージ
	cp	a, 107
	jp	c, bgmdriver_play_end		; 106 は 演奏停止メッセージ
	jp	z, bgmdriver_drum1_font		; 107 は ドラム１音色設定メッセージ
	cp	a, 109
	jp	c, bgmdriver_drum2_font		; 108 は ドラム２音色設定メッセージ
	jp	z, bgmdriver_drum3_font		; 109 は ドラム３音色設定メッセージ
	cp	a, 111
	jp	c, bgmdriver_drum4_font		; 110 は ドラム４音色設定メッセージ
	jp	z, bgmdriver_drum5_font		; 111 は ドラム５音色設定メッセージ
	ret

	; KeyOn処理 -----------------------------------------------------------
bgmdriver_keyon:
	ld	c, a				; 破壊されないレジスタにバックアップ
	call	bgmdriver_get_wait_time
	ld	[ix + INFO_WAIT_COUNT_L], e	; 待ち時間更新
	ld	[ix + INFO_WAIT_COUNT_H], d
	ld	[ix + INFO_PLAY_ADR_L], l	; 演奏データを次へ
	ld	[ix + INFO_PLAY_ADR_H], h
	ld	a, c				; 復元
	; 音階を周波数に変換する
	rlca
	ld	l, a
	ld	h, 0
	ld	de, freq_data
	add	hl, de				; hl ← freq_data + a * 2
	ld	e, [hl]
	inc	hl
	ld	d, [hl]
	; 音色データを取得する
	ld	l, [ix + INFO_SEL_SFONT_L]
	ld	h, [ix + INFO_SEL_SFONT_H]
	; 設定周波数を更新する
bgmdriver_set_freq:
	ld	[ix + INFO_TONE_FREQ_L], e
	ld	[ix + INFO_TONE_FREQ_H], d
	; 各種初期化する
	xor	a, a
	ld	[ix + INFO_ENV_STATE], a
	ld	[ix + INFO_ENV_VOL], a
	; ビブラートを初期化する
	ld	[ix + INFO_VIB_INDEX], a
	ld	[ix + INFO_SOUND_FONT_L], l
	ld	[ix + INFO_SOUND_FONT_H], h
	ld	de, SFONT_VIB_WAIT
	add	hl, de
	ld	a, [hl]
	ld	[ix + INFO_VIB_WAIT], a
	; ノイズ周波数を初期化する
	inc	hl
	ld	a, [hl]
	ld	[ix + INFO_NOISE_FREQ], a
	jp	bgmdriver_update_vibrato

	; DRUM KeyOn処理 -------------------------------------------------------
bgmdriver_drum_keyon:
	ld	c, a				; 破壊されないレジスタにバックアップ
	call	bgmdriver_get_wait_time
	ld	[ix + INFO_WAIT_COUNT_L], e	; 待ち時間更新
	ld	[ix + INFO_WAIT_COUNT_H], d
	ld	[ix + INFO_PLAY_ADR_L], l	; 演奏データを次へ
	ld	[ix + INFO_PLAY_ADR_H], h
	ld	a, c				; 復元
	; 音色情報を取得する
	sub	a, 96				; hl ← [a - 96] * 2 + play_drum_font1
	rlca
	ld	hl, play_drum_font1
	add	a, l
	ld	l, a				; ※フラグ不変
	ld	a, 0				; ※フラグ不変
	adc	a, h
	ld	h, a				; hl にドラム音色のアドレスの入っているアドレス
	ld	e, [hl]
	inc	hl
	ld	d, [hl]
	ex	de, hl				; hl にドラム音色のアドレス
	push	hl
	ld	de, SFONT_FREQ_L
	add	hl, de
	ld	e, [hl]
	inc	hl
	ld	d, [hl]				; de にドラム用再生周波数
	pop	hl				; hl にドラム音色のアドレス
	jp	bgmdriver_set_freq

	; KeyOff処理 -----------------------------------------------------------
bgmdriver_keyoff:
	call	bgmdriver_get_wait_time
	ld	[ix + INFO_WAIT_COUNT_L], e	; 待ち時間更新
	ld	[ix + INFO_WAIT_COUNT_H], d
	ld	[ix + INFO_PLAY_ADR_L], l	; 演奏データを次へ
	ld	[ix + INFO_PLAY_ADR_H], h
	; エンベロープをリリース状態に変更する
	ld	a, [ix + INFO_ENV_STATE]
	cp	a, 3
	jp	nc, bgmdriver_update_vibrato
	ld	[ix + INFO_ENV_STATE], 3
	jp	bgmdriver_update_vibrato

	; 休符の処理 ----------------------------------------------------------
bgmdriver_rest:
	call	bgmdriver_get_wait_time
	ld	[ix + INFO_WAIT_COUNT_L], e	; 待ち時間更新
	ld	[ix + INFO_WAIT_COUNT_H], d
	ld	[ix + INFO_PLAY_ADR_L], l	; 演奏データを次へ
	ld	[ix + INFO_PLAY_ADR_H], h
	ld	[ix + INFO_ENV_STATE], 4
	ld	[ix + INFO_ENV_VOL], 0
	jp	bgmdriver_update_vibrato

	; 音量設定 ------------------------------------------------------------
bgmdriver_volume:
	ld	a, [hl]				; 音量取得
	inc	hl
	ld	[ix + INFO_PLAY_ADR_L], l	; 演奏データを次へ
	ld	[ix + INFO_PLAY_ADR_H], h
	ld	[ix + INFO_TONE_VOL], a		; 設定音量更新
	jp	bgmdriver_check_next_data	; 続けて次のデータを処理する

	; 音色設定 ------------------------------------------------------------
bgmdriver_sound_font:
	ld	e, [hl]				; 音色データのアドレスを取得
	inc	hl
	ld	d, [hl]
	inc	hl
	ld	[ix + INFO_PLAY_ADR_L], l	; 演奏データを次へ
	ld	[ix + INFO_PLAY_ADR_H], h
	ld	hl, [play_bgm_data_adr]		; 演奏データの先頭アドレス
	add	hl, de
	ld	[ix + INFO_SEL_SFONT_L], l	; 音色データアドレスを更新
	ld	[ix + INFO_SEL_SFONT_H], h
	xor	a, a					; 各種初期化
	ld	[ix + INFO_VIB_WAIT], a
	ld	[ix + INFO_ENV_STATE], a
	ld	[ix + INFO_ENV_VOL], a
	ld	[ix + INFO_VIB_INDEX], a
	jp	bgmdriver_check_next_data	; 続けて次のデータを処理する

	; ドラム１音色設定設定 ------------------------------------------------
bgmdriver_drum1_font:
	ld	e, [hl]				; 音色データのアドレスを取得
	inc	hl
	ld	d, [hl]
	inc	hl
	ld	[ix + INFO_PLAY_ADR_L], l	; 演奏データを次へ
	ld	[ix + INFO_PLAY_ADR_H], h
	ld	hl, [play_bgm_data_adr]		; 演奏データの先頭アドレス
	add	hl, de
	ld	[play_drum_font1], hl		; 音色データアドレスを更新
	xor	a, a					; 各種初期化
	ld	[ix + INFO_VIB_WAIT], a
	ld	[ix + INFO_ENV_STATE], a
	ld	[ix + INFO_ENV_VOL], a
	ld	[ix + INFO_VIB_INDEX], a
	jp	bgmdriver_check_next_data	; 続けて次のデータを処理する

	; ドラム２音色設定設定 ------------------------------------------------
bgmdriver_drum2_font:
	ld	e, [hl]				; 音色データのアドレスを取得
	inc	hl
	ld	d, [hl]
	inc	hl
	ld	[ix + INFO_PLAY_ADR_L], l	; 演奏データを次へ
	ld	[ix + INFO_PLAY_ADR_H], h
	ld	hl, [play_bgm_data_adr]		; 演奏データの先頭アドレス
	add	hl, de
	ld	[play_drum_font2], hl		; 音色データアドレスを更新
	xor	a, a					; 各種初期化
	ld	[ix + INFO_VIB_WAIT], a
	ld	[ix + INFO_ENV_STATE], a
	ld	[ix + INFO_ENV_VOL], a
	ld	[ix + INFO_VIB_INDEX], a
	jp	bgmdriver_check_next_data	; 続けて次のデータを処理する

	; ドラム３音色設定設定 ------------------------------------------------
bgmdriver_drum3_font:
	ld	e, [hl]				; 音色データのアドレスを取得
	inc	hl
	ld	d, [hl]
	inc	hl
	ld	[ix + INFO_PLAY_ADR_L], l		; 演奏データを次へ
	ld	[ix + INFO_PLAY_ADR_H], h
	ld	hl, [play_bgm_data_adr]		; 演奏データの先頭アドレス
	add	hl, de
	ld	[play_drum_font3], hl		; 音色データアドレスを更新
	xor	a, a					; 各種初期化
	ld	[ix + INFO_VIB_WAIT], a
	ld	[ix + INFO_ENV_STATE], a
	ld	[ix + INFO_ENV_VOL], a
	ld	[ix + INFO_VIB_INDEX], a
	jp	bgmdriver_check_next_data	; 続けて次のデータを処理する

	; ドラム４音色設定設定 ------------------------------------------------
bgmdriver_drum4_font:
	ld	e, [hl]				; 音色データのアドレスを取得
	inc	hl
	ld	d, [hl]
	inc	hl
	ld	[ix + INFO_PLAY_ADR_L], l	; 演奏データを次へ
	ld	[ix + INFO_PLAY_ADR_H], h
	ld	hl, [play_bgm_data_adr]		; 演奏データの先頭アドレス
	add	hl, de
	ld	[play_drum_font4], hl		; 音色データアドレスを更新
	xor	a, a					; 各種初期化
	ld	[ix + INFO_VIB_WAIT], a
	ld	[ix + INFO_ENV_STATE], a
	ld	[ix + INFO_ENV_VOL], a
	ld	[ix + INFO_VIB_INDEX], a
	jp	bgmdriver_check_next_data	; 続けて次のデータを処理する

	; ドラム５音色設定設定 ------------------------------------------------
bgmdriver_drum5_font:
	ld	e, [hl]				; 音色データのアドレスを取得
	inc	hl
	ld	d, [hl]
	inc	hl
	ld	[ix + INFO_PLAY_ADR_L], l	; 演奏データを次へ
	ld	[ix + INFO_PLAY_ADR_H], h
	ld	hl, [play_bgm_data_adr]		; 演奏データの先頭アドレス
	add	hl, de
	ld	[play_drum_font5], hl		; 音色データアドレスを更新
	xor	a, a					; 各種初期化
	ld	[ix + INFO_VIB_WAIT], a
	ld	[ix + INFO_ENV_STATE], a
	ld	[ix + INFO_ENV_VOL], a
	ld	[ix + INFO_VIB_INDEX], a
	jp	bgmdriver_check_next_data	; 続けて次のデータを処理する

	; アドレスジャンプ ----------------------------------------------------
bgmdriver_jump:
	ld	e, [hl]				; 飛び先アドレス取得
	inc	hl
	ld	d, [hl]
	ld	hl, [play_bgm_data_adr]		; 演奏データの先頭アドレス
	add	hl, de
	ld	[ix + INFO_PLAY_ADR_L], l	; 演奏データを次へ
	ld	[ix + INFO_PLAY_ADR_H], h
	jp	bgmdriver_check_next_data	; 続けて次のデータを処理する

	; 演奏停止 ------------------------------------------------------------
bgmdriver_play_end:
	xor	a, a
	ld	[ix + INFO_PLAY_ADR_L], a	; 演奏停止
	ld	[ix + INFO_PLAY_ADR_H], a
	ld	[ix + INFO_TONE_VOL], a
	ld	[ix + INFO_ENV_STATE], a
	ld	[ix + INFO_ENV_VOL], a
	jp	bgmdriver_envelope_end		; 停止したのでビブラートやエンベロープ処理はスキップ

	; ビブラートの処理 ----------------------------------------------------
bgmdriver_update_vibrato:
	; ビブラート遅延時間の最中であるか調べる
	ld	a, [ix + INFO_VIB_WAIT]
	or	a, a
	jr	z, bgmdriver_vibrato_active
	; ビブラート遅延時間の最中の場合
	dec	a
	ld	[ix + INFO_VIB_WAIT], a		; 遅延時間1カウント経過
	; 設定周波数を取得
	ld	l, [ix + INFO_TONE_FREQ_L]
	ld	h, [ix + INFO_TONE_FREQ_H]
	jp	bgmdriver_update_freq
	; ビブラート遅延時間を脱している場合
bgmdriver_vibrato_active:
	; ビブラート位相位置を取得
	ld	a, [ix + INFO_VIB_INDEX]
	ld	e, a
	inc	a
	and	a, 31
	ld	[ix + INFO_VIB_INDEX], a	; 次の位相へ進めておく
	; 位相位置に対応するビブラート波形を取得
	ld	d, 0
	ld	l, [ix + INFO_SOUND_FONT_L]
	ld	h, [ix + INFO_SOUND_FONT_H]
	add	hl, de
	ld	a, [hl]				; a ← INFO_SOUND_FONT->SFONT_VIB_WAVE[ INFO_VIB_INDEX ]
	; 設定周波数を取得
	ld	l, [ix + INFO_TONE_FREQ_L]
	ld	h, [ix + INFO_TONE_FREQ_H]
	; ビブラート波形を加算
	or	a, a
	jp	p, bgmdriver_vibrato_active_skip
	ld	d, 255
bgmdriver_vibrato_active_skip:
	ld	e, a
	add	hl, de
	; PSGに設定される周波数情報を更新
bgmdriver_update_freq:
	ld	[ix + INFO_EFF_FREQ_L], l
	ld	[ix + INFO_EFF_FREQ_H], h

	; エンベロープの処理 --------------------------------------------------
	ld	l, [ix + INFO_SOUND_FONT_L]
	ld	h, [ix + INFO_SOUND_FONT_H]
	ld	d, 0
	ld	a, [ix + INFO_ENV_STATE]	; 0: AR, 1: DR, 2: SR, 3: RR, 4: 停止中
	sub	a, 1
	jr	c, bgmdriver_envelope_ar
	jr	z, bgmdriver_envelope_dr
	sub	a, 2
	jr	c, bgmdriver_envelope_sr
	jr	z, bgmdriver_envelope_rr
	jp	bgmdriver_envelope_end
	; リリースレイトの処理
bgmdriver_envelope_rr:
	ld	a, [ix + INFO_ENV_VOL]
	ld	e, SFONT_RR
	add	hl, de
	ld	b, [hl]
	sub	a, b
	ld	[ix + INFO_ENV_VOL], a		; ※フラグ不変
	jr	nc, bgmdriver_envelope_end
	ld	[ix + INFO_ENV_VOL], 0
	ld	[ix + INFO_ENV_STATE], 4	; 停止中に移行
	jp	bgmdriver_envelope_end
	; サスティンレイトの処理
bgmdriver_envelope_sr:
	ld	a, [ix + INFO_ENV_VOL]
	ld	e, SFONT_SR
	add	hl, de
	ld	b, [hl]
	sub	a, b
	ld	[ix + INFO_ENV_VOL], a			; ※フラグ不変
	jr	nc, bgmdriver_envelope_end
	ld	[ix + INFO_ENV_VOL], 0
	ld	[ix + INFO_ENV_STATE], 4		; 停止中に移行
	jp	bgmdriver_envelope_end
	; ディケイレイトの処理
bgmdriver_envelope_dr:
	ld	a, [ix + INFO_ENV_VOL]
	ld	e, SFONT_DR
	add	hl, de
	ld	b, [hl]				; SFONT_DR
	inc	hl
	ld	c, [hl]				; SFONT_SL
	sub	a, b
	ld	[ix + INFO_ENV_VOL], a			; ※フラグ不変
	cp	a, c
	jr	nc, bgmdriver_envelope_end
	ld	[ix + INFO_ENV_VOL], c
	ld	[ix + INFO_ENV_STATE], 2		; SR に移行
	jp	bgmdriver_envelope_end
	; アタックレイトの処理
bgmdriver_envelope_ar:
	ld	a, [ix + INFO_ENV_VOL]
	ld	e, SFONT_AR
	add	hl, de
	ld	b, [hl]
	add	a, b
	ld	[ix + INFO_ENV_VOL], a			; ※フラグ不変
	jr	nc, bgmdriver_envelope_end
	ld	[ix + INFO_ENV_VOL], 255
	ld	[ix + INFO_ENV_STATE], 1		; DR に移行
	jp	bgmdriver_envelope_end
bgmdriver_envelope_end:

	; 実効音量を計算 ------------------------------------------------------
	ld	a, [ix + INFO_TONE_VOL]
	xor	a, 15
	ld	b, a
	ld	a, [ix + INFO_ENV_VOL]
	srl	a
	srl	a
	srl	a
	srl	a
	sub	a, b
	jr	nc, bgmdriver_calc_eff_vol
	xor	a, a
bgmdriver_calc_eff_vol:
	ld	[ix + INFO_EFF_VOL], a
	ret

; -----------------------------------------------------------------------------
;	待ち時間読み取り処理 [内部]
;	input:
;	hl	...	待ち時間が記録されているメモリのアドレス
;	output
;	hl	...	待ち時間の次のアドレス
;	de	...	読み取った待ち時間
;	break
;	a, f, d, e, h, l
;	comment
;	なし
; -----------------------------------------------------------------------------
bgmdriver_get_wait_time:
	ld	de, 0
bgmdriver_get_wait_time_loop:
	ld	a, [hl]
	inc	hl
	inc	a
	jr	nz, bgmdriver_get_wait_time_exit
	dec	a
	add	a, e
	jr	nc, bgmdriver_get_wait_time_loop
	inc	d
	jr	bgmdriver_get_wait_time_loop
bgmdriver_get_wait_time_exit:
	dec	a
	add	a, e
	ld	e, a
	jr	nc, bgmdriver_get_wait_time_skip
	inc	d
bgmdriver_get_wait_time_skip:
	ret

; -----------------------------------------------------------------------------
;	フェードアウト処理 [内部]
;	input:
;	なし
;	output
;	なし
;	break
;
;	comment
;	なし
; -----------------------------------------------------------------------------
bgmdriver_fadeout_proc:
	; フェードアウト処理動作中か判断
	ld	a, [play_master_volume_speed]
	or	a, a
	ret	z

	; 待機中か判断
	ld	a, [play_master_volume_wait]
	or	a, a
	jr	z, bgmdriver_fadeout_skip1
	; 待機中なら待ち時間減
	dec	a
	ld	[play_master_volume_wait], a
	ret
	; 待機中でない
bgmdriver_fadeout_skip1:
	; 次の待ち時間を設定
	ld	a, [play_master_volume_speed]
	ld	[play_master_volume_wait], a
	; 音量減
	ld	a, [play_master_volume]
	inc	a				; 0が最大音量, 15が無音なので、inc a で音量減
	ld	[play_master_volume], a
	cp	a, 15
	ret	nz
	; 無音になったらフェードアウトを停止する
	xor	a, a
	ld	[play_master_volume_speed], a
	; マスター音量も最大に戻す
	ld	[play_master_volume], a
	; 演奏も停止する
	ld	hl, play_info_ch0
	call	bgmdriver_init_play_info
	ld	hl, play_info_ch1
	call	bgmdriver_init_play_info
	ld	hl, play_info_ch2
	call	bgmdriver_init_play_info
	ret

; -----------------------------------------------------------------------------
;	効果音処理 [内部]
;	input:
;	なし
;	output
;	なし
;	break
;
;	comment
;	なし
; -----------------------------------------------------------------------------
bgmdriver_sound_effect:
	; 効果音再生中か判断
	ld	a, [play_sound_effect_active]
	or	a, a
	ret	z

	; 待機時間中か判断
	ld	a, [play_sound_effect_wait_count]
	or	a, a
	jr	z, bgmdriver_sound_effect_proc
	; 待機時間経過
	dec	a
	ld	[play_sound_effect_wait_count], a
	ret

	; 効果音処理
bgmdriver_sound_effect_proc:
	ld	hl, [play_sound_effect_adr]
bgmdriver_sound_effect_loop:
	ld	a, [hl]
	inc	hl
	ld	[play_sound_effect_adr], hl		; 次のアドレス

	; 処理コードの解析
	cp	a, BGM_SE_VOL
	jp	c, bgmdriver_sound_effect_freq_proc
	jp	z, bgmdriver_sound_effect_volume_proc
	cp	a, BGM_SE_WAIT
	jp	c, bgmdriver_sound_effect_noise_freq_proc
	jp	z, bgmdriver_sound_effect_wait_proc
	jp	bgmdriver_sound_effect_end_proc

	; 効果音の周波数設定
bgmdriver_sound_effect_freq_proc:
	ld	e, [hl]
	inc	hl
	ld	d, [hl]
	inc	hl
	ld	[play_sound_effect_adr], hl		; 次のアドレス
	ld	[play_sound_effect_freq], de		; 周波数を更新
	jp	bgmdriver_sound_effect_loop

	; 効果音の音量設定
bgmdriver_sound_effect_volume_proc:
	ld	a, [hl]					; 音量を取得する
	inc	hl
	ld	[play_sound_effect_volume], a		; 音量を更新
	jp	bgmdriver_sound_effect_loop

	; 効果音のノイズ周波数設定
bgmdriver_sound_effect_noise_freq_proc:
	ld	a, [hl]					; ノイズ周波数を取得する
	inc	hl
	ld	[play_sound_effect_noise_freq], a	; ノイズ周波数を更新
	jp	bgmdriver_sound_effect_loop

	; 単純待機
bgmdriver_sound_effect_wait_proc:
	ld	a, [hl]					; 待機時間を取得する
	inc	hl
	ld	[play_sound_effect_adr], hl		; 次のアドレス
	ld	[play_sound_effect_wait_count], a	; 待機時間を更新
	ret

	; 効果音停止
bgmdriver_sound_effect_end_proc:
	xor	a, a
	ld	[play_sound_effect_active], a
	dec	a
	ld	[play_sound_effect_priority], a		; 最低プライオリティに更新
	ret

; -----------------------------------------------------------------------------
;	ミキサー処理 [内部]
;	input:
;	なし
;	output
;	なし
;	break
;	a, b, c, d, e, f, h, l, ix
;	comment
;	なし
; -----------------------------------------------------------------------------
bgmdriver_mixer:
	ld	b, 0				; tone の on/off フラグ [1 で on]
	ld	e, 0				; noise の on/off フラグ [1 で on]
	ld	c, PSG_REG_ADR

	; ch0 周波数設定
	ld	d, 0
	ld	ix, play_info_ch0
	ld	a, [ix + INFO_EFF_FREQ_L]	; SOUND 0, [ix + INFO_EFF_FREQ_L]
	out	[c], d
	inc	d
	out	[PSG_REG_WRT], a
	ld	a, [ix + INFO_EFF_FREQ_H]	; SOUND 1, [ix + INFO_EFF_FREQ_H]
	out	[c], d
	inc	d
	out	[PSG_REG_WRT], a
	; ch0 の種類判定
	and	a, 0x80
	jr	nz, bgmdriver_mixer_skip1_ch0	; トーンoff ならスキップ
	inc	b				; ch0 のトーンon を保持
bgmdriver_mixer_skip1_ch0:
	ld	a, [ix + INFO_NOISE_FREQ]
	bit	7, a
	jr	z, bgmdriver_mixer_skip2_ch0	; ノイズoff ならスキップ
	and	a, 31
	ld	[play_noise_freq], a		; ノイズ周波数を覚えておく
	ld	e, 8				; ch0 のノイズon を保持
bgmdriver_mixer_skip2_ch0:

	; ch1 周波数設定
	ld	ix, play_info_ch1
	ld	a, [ix + INFO_EFF_FREQ_L]	; SOUND 2, [ix + INFO_EFF_FREQ_L]
	out	[c], d
	inc	d
	out	[PSG_REG_WRT], a
	ld	a, [ix + INFO_EFF_FREQ_H]	; SOUND 3, [ix + INFO_EFF_FREQ_H]
	out	[c], d
	inc	d
	out	[PSG_REG_WRT], a
	; ch1 の種類判定
	and	a, 0x80
	jr	nz, bgmdriver_mixer_skip1_ch1	; トーンoff ならスキップ
	inc	b				; ch0 のトーンon を保持
	inc	b
bgmdriver_mixer_skip1_ch1:
	ld	a, [ix + INFO_NOISE_FREQ]
	bit	7, a
	jr	z, bgmdriver_mixer_skip2_ch1	; ノイズoff ならスキップ
	and	a, 31
	ld	[play_noise_freq], a		; ノイズ周波数を覚えておく
	ld	a, 16				; ch1 のノイズon を保持
	add	a, e
	ld	e, a
bgmdriver_mixer_skip2_ch1:

	; ch2 は BGMか 効果音か
	ld	a, [play_sound_effect_active]
	or	a, a
	jr	z, bgmdriver_mixer_tone_ch2

	; ch2 効果音の周波数設定
	ld	hl, [play_sound_effect_freq]
	ld	a, l				; SOUND 4, l
	out	[c], d
	inc	d
	out	[PSG_REG_WRT], a
	ld	a, h				; SOUND 5, h
	out	[c], d
	inc	d
	out	[PSG_REG_WRT], a
	; ch2 効果音のトーン発生判定
	and	a, 0x80
	jr	nz, bgmdriver_mixer_skip0_ch2	; トーンoff ならスキップ
	inc	b
	inc	b
	inc	b
	inc	b

bgmdriver_mixer_skip0_ch2:
	; ch2 効果音のノイズ周波数設定
	ld	a, [play_sound_effect_noise_freq]
	bit	7, a
	jp	z, bgmdriver_mixer_noise_freq
	and	a, 0x3F
	out	[c], d				; SOUND 6, play_sound_effect_noise_freq
	inc	d
	out	[PSG_REG_WRT], a
	ld	a, 32				; ch1 のノイズon を保持
	add	a, e
	ld	e, a
	jp	bgmdriver_mixer_mix

bgmdriver_mixer_tone_ch2:
	; ch2 周波数設定
	ld	ix, play_info_ch2
	ld	a, [ix + INFO_EFF_FREQ_L]	; SOUND 4, [ix + INFO_EFF_FREQ_L]
	out	[c], d
	inc	d
	out	[PSG_REG_WRT], a
	ld	a, [ix + INFO_EFF_FREQ_H]	; SOUND 5, [ix + INFO_EFF_FREQ_H]
	out	[c], d
	inc	d
	out	[PSG_REG_WRT], a
	; ch2 の種類判定
	and	a, 0x80
	jr	nz, bgmdriver_mixer_skip1_ch2	; トーンoff ならスキップ
	inc	b
	inc	b
	inc	b
	inc	b
bgmdriver_mixer_skip1_ch2:
	ld	a, [ix + INFO_NOISE_FREQ]
	bit	7, a
	jr	z, bgmdriver_mixer_skip2_ch2	; ノイズoff ならスキップ
	and	a, 31
	ld	[play_noise_freq], a		; ノイズ周波数を覚えておく
	ld	a, 32				; ch1 のノイズon を保持
	add	a, e
	ld	e, a
bgmdriver_mixer_skip2_ch2:

bgmdriver_mixer_noise_freq:
	; ノイズ周波数
	out	[c], d				; SOUND 6, play_noise_freq
	inc	d
	ld	a, [play_noise_freq]
	out	[PSG_REG_WRT], a

bgmdriver_mixer_mix:
	; ミキサー
	ld	hl, play_master_volume
	out	[c], d				; SOUND 7, [b | e | 0x80] ^ 0x3F
	inc	d
	ld	a, e
	or	a, b
	or	a, 0x80
	xor	a, 0x3F
	out	[PSG_REG_WRT], a

	; ch0 音量設定
	ld	ix, play_info_ch0		; SOUND 8, [ix + INFO_EFF_VOL]
	ld	a, [ix + INFO_EFF_VOL]
	sub	a, [hl]
	jp	nc, bgmdriver_mixer_mix_skip1
	xor	a, a
bgmdriver_mixer_mix_skip1:
	out	[c], d
	inc	d
	out	[PSG_REG_WRT], a

	; ch1 音量設定
	ld	ix, play_info_ch1		; SOUND 9, [ix + INFO_EFF_VOL]
	ld	a, [ix + INFO_EFF_VOL]
	sub	a, [hl]
	jp	nc, bgmdriver_mixer_mix_skip2
	xor	a, a
bgmdriver_mixer_mix_skip2:
	out	[c], d
	inc	d
	out	[PSG_REG_WRT], a

	; ch2 は BGMか 効果音か
	ld	a, [play_sound_effect_active]
	or	a, a
	jr	z, bgmdriver_mixer_volume_ch2
	ld	a, [play_sound_effect_volume]
	jp	bgmdriver_mixer_volume_ch2_skip1
bgmdriver_mixer_volume_ch2:
	; ch2 音量設定
	ld	ix, play_info_ch2		; SOUND 10, [ix + INFO_EFF_VOL]
	ld	a, [ix + INFO_EFF_VOL]
	sub	a, [hl]
	jp	nc, bgmdriver_mixer_mix_skip3
	xor	a, a
bgmdriver_mixer_mix_skip3:

bgmdriver_mixer_volume_ch2_skip1:
	out	[c], d
	inc	d
	out	[PSG_REG_WRT], a

	ret

; -----------------------------------------------------------------------------
;	データエリア
; -----------------------------------------------------------------------------
freq_data:
	dw	3420, 3228, 3047, 2876, 2714, 2562, 2418, 2282, 2154, 2033, 1919, 1811
	dw	1710, 1614, 1523, 1438, 1357, 1281, 1209, 1141, 1077, 1016,  959,  905
	dw	 855,  807,  761,  719,  678,  640,  604,  570,  538,  508,  479,  452
	dw	 427,  403,  380,  359,  339,  320,  302,  285,  269,  254,  239,  226
	dw	 213,  201,  190,  179,  169,  160,  151,  142,  134,  127,  119,  113
	dw	 106,  100,   95,   89,   84,   80,   75,   71,   67,   63,   59,   56
	dw	  53,   50,   47,   44,   42,   40,   37,   35,   33,   31,   29,   28
	dw	  26,   25,   23,   22,   21,   20,   18,   17,   16,   15,   14,   14

; -----------------------------------------------------------------------------
;	ワークエリア
; -----------------------------------------------------------------------------
play_sound_effect_active:
	db	0		; 効果音再生中は 1
play_sound_effect_wait_count:
	db	0		; 効果音の待機時間
play_sound_effect_freq:
	dw	0		; 効果音の再生周波数
play_sound_effect_noise_freq:
	db	0		; 効果音のノイズ周波数
play_sound_effect_volume:
	db	0		; 効果音の音量
play_sound_effect_adr:
	dw	0		; 再生中の効果音データのアドレス
play_sound_effect_priority:
	db	255		; 再生中の効果音のプライオリティ [0が最高]

play_noise_freq:
	db	0		; 実際に再生するノイズ周波数決定用作業変数

play_bgm_data_adr:
	dw	0		; 再生中の BGMデータ先頭アドレス

play_master_volume_wait:
	db	0		; フェードアウト用待機時間
play_master_volume_speed:
	db	0		; フェードアウト用待機時間初期値[0はフェードアウト停止中]
play_master_volume:
	db	0		; マスター音量[0が最大音量, 15が無音]

play_drum_font1:
	dw	0		; ドラム音１の音色データアドレス
play_drum_font2:
	dw	0		; ドラム音２の音色データアドレス
play_drum_font3:
	dw	0		; ドラム音３の音色データアドレス
play_drum_font4:
	dw	0		; ドラム音４の音色データアドレス
play_drum_font5:
	dw	0		; ドラム音５の音色データアドレス

play_info_ch0:
        ds  INFO_SIZE, 0
;	repeat i, INFO_SIZE
;	db	0		; ch0 の演奏データ情報
;	endr
play_info_ch1:
        ds  INFO_SIZE, 0
;	repeat i, INFO_SIZE
;	db	0		; ch1 の演奏データ情報
;	endr
play_info_ch2:
        ds  INFO_SIZE, 0
;	repeat i, INFO_SIZE
;	db	0		; ch2 の演奏データ情報
;	endr

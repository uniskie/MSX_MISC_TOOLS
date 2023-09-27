;-*- tab-width: 8 -*-
; Port for tniasm By Uniske
; -----------------------------------------------------------------------------
;	PSG BGM DRIVER DEFINE HEADER
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
; -----------------------------------------------------------------------------

BGM_TONE_C1:		EQU	0
BGM_TONE_CS1:		EQU	1
BGM_TONE_D1:		EQU	2
BGM_TONE_DS1:		EQU	3
BGM_TONE_E1:		EQU	4
BGM_TONE_F1:		EQU	5
BGM_TONE_FS1:		EQU	6
BGM_TONE_G1:		EQU	7
BGM_TONE_GS1:		EQU	8
BGM_TONE_A1:		EQU	9
BGM_TONE_AS1:		EQU	10
BGM_TONE_B1:		EQU	11

BGM_TONE_C2:		EQU	0  + 12
BGM_TONE_CS2:		EQU	1  + 12
BGM_TONE_D2:		EQU	2  + 12
BGM_TONE_DS2:		EQU	3  + 12
BGM_TONE_E2:		EQU	4  + 12
BGM_TONE_F2:		EQU	5  + 12
BGM_TONE_FS2:		EQU	6  + 12
BGM_TONE_G2:		EQU	7  + 12
BGM_TONE_GS2:		EQU	8  + 12
BGM_TONE_A2:		EQU	9  + 12
BGM_TONE_AS2:		EQU	10 + 12
BGM_TONE_B2:		EQU	11 + 12

BGM_TONE_C3:		EQU	0  + 24
BGM_TONE_CS3:		EQU	1  + 24
BGM_TONE_D3:		EQU	2  + 24
BGM_TONE_DS3:		EQU	3  + 24
BGM_TONE_E3:		EQU	4  + 24
BGM_TONE_F3:		EQU	5  + 24
BGM_TONE_FS3:		EQU	6  + 24
BGM_TONE_G3:		EQU	7  + 24
BGM_TONE_GS3:		EQU	8  + 24
BGM_TONE_A3:		EQU	9  + 24
BGM_TONE_AS3:		EQU	10 + 24
BGM_TONE_B3:		EQU	11 + 24

BGM_TONE_C4:		EQU	0  + 36
BGM_TONE_CS4:		EQU	1  + 36
BGM_TONE_D4:		EQU	2  + 36
BGM_TONE_DS4:		EQU	3  + 36
BGM_TONE_E4:		EQU	4  + 36
BGM_TONE_F4:		EQU	5  + 36
BGM_TONE_FS4:		EQU	6  + 36
BGM_TONE_G4:		EQU	7  + 36
BGM_TONE_GS4:		EQU	8  + 36
BGM_TONE_A4:		EQU	9  + 36
BGM_TONE_AS4:		EQU	10 + 36
BGM_TONE_B4:		EQU	11 + 36

BGM_TONE_C5:		EQU	0  + 48
BGM_TONE_CS5:		EQU	1  + 48
BGM_TONE_D5:		EQU	2  + 48
BGM_TONE_DS5:		EQU	3  + 48
BGM_TONE_E5:		EQU	4  + 48
BGM_TONE_F5:		EQU	5  + 48
BGM_TONE_FS5:		EQU	6  + 48
BGM_TONE_G5:		EQU	7  + 48
BGM_TONE_GS5:		EQU	8  + 48
BGM_TONE_A5:		EQU	9  + 48
BGM_TONE_AS5:		EQU	10 + 48
BGM_TONE_B5:		EQU	11 + 48

BGM_TONE_C6:		EQU	0  + 60
BGM_TONE_CS6:		EQU	1  + 60
BGM_TONE_D6:		EQU	2  + 60
BGM_TONE_DS6:		EQU	3  + 60
BGM_TONE_E6:		EQU	4  + 60
BGM_TONE_F6:		EQU	5  + 60
BGM_TONE_FS6:		EQU	6  + 60
BGM_TONE_G6:		EQU	7  + 60
BGM_TONE_GS6:		EQU	8  + 60
BGM_TONE_A6:		EQU	9  + 60
BGM_TONE_AS6:		EQU	10 + 60
BGM_TONE_B6:		EQU	11 + 60

BGM_TONE_C7:		EQU	0  + 72
BGM_TONE_CS7:		EQU	1  + 72
BGM_TONE_D7:		EQU	2  + 72
BGM_TONE_DS7:		EQU	3  + 72
BGM_TONE_E7:		EQU	4  + 72
BGM_TONE_F7:		EQU	5  + 72
BGM_TONE_FS7:		EQU	6  + 72
BGM_TONE_G7:		EQU	7  + 72
BGM_TONE_GS7:		EQU	8  + 72
BGM_TONE_A7:		EQU	9  + 72
BGM_TONE_AS7:		EQU	10 + 72
BGM_TONE_B7:		EQU	11 + 72

BGM_TONE_C8:		EQU	0  + 84
BGM_TONE_CS8:		EQU	1  + 84
BGM_TONE_D8:		EQU	2  + 84
BGM_TONE_DS8:		EQU	3  + 84
BGM_TONE_E8:		EQU	4  + 84
BGM_TONE_F8:		EQU	5  + 84
BGM_TONE_FS8:		EQU	6  + 84
BGM_TONE_G8:		EQU	7  + 84
BGM_TONE_GS8:		EQU	8  + 84
BGM_TONE_A8:		EQU	9  + 84
BGM_TONE_AS8:		EQU	10 + 84
BGM_TONE_B8:		EQU	11 + 84

BGM_DRUM_1:		EQU	96
BGM_DRUM_2:		EQU	97
BGM_DRUM_3:		EQU	98
BGM_DRUM_4:		EQU	99
BGM_DRUM_5:		EQU	100

BGM_KEYOFF:		EQU	101
BGM_REST:		EQU	102
BGM_VOL:		EQU	103
BGM_SOUND_FONT:		EQU	104
BGM_JUMP:		EQU	105
BGM_PLAY_END:		EQU	106
BGM_DRUM1_FONT:		EQU	107
BGM_DRUM2_FONT:		EQU	108
BGM_DRUM3_FONT:		EQU	109
BGM_DRUM4_FONT:		EQU	110
BGM_DRUM5_FONT:		EQU	111
; -----------------------------------------------------------------------------
BGM_SE_FREQ:		EQU	0
BGM_SE_VOL:		EQU	1
BGM_SE_NOISE_FREQ:	EQU	2
BGM_SE_WAIT:		EQU	3
BGM_SE_END:		EQU	4

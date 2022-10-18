#ifndef __OPLDRV_INST_DATA2_H__
#define __OPLDRV_INST_DATA2_H__

#include "opldrv_data.h"

//===============================================
// 本体内蔵ROM版 ROM音色データ
//===============================================
namespace OPLDRV {
// MSX-MUSIC BIOS (A1GT)
const OplDrvData::ExtraVoiceSet
msxmusic_extention_voice = {
    "Built-in rom",
/* 00 */ 0x11,0x11,0x20,0x20,0xFF,0xB2,0xF4,0xF4, "Piano 1",  "Piano 1*",
/* 01 */ 0x30,0x10,0x20,0x20,0xFB,0xB2,0xF3,0xF3, "Piano 2",  "Piano 2",
/* 02 */ 0x61,0x61,0x20,0x20,0xB4,0x56,0x17,0x17, "Violin",   "Violin*",
/* 03 */ 0x31,0x31,0x20,0x20,0x43,0x43,0x26,0x26, "Flute",    "Flute 1*",
/* 04 */ 0xA2,0x30,0x20,0x20,0x88,0x54,0x06,0x06, "Clarinet", "Clarinet*",
/* 05 */ 0x31,0x34,0x20,0x20,0x72,0x56,0x1C,0x1C, "Oboe",     "Oboe*",
/* 06 */ 0x71,0x71,0x20,0x20,0x53,0x52,0x24,0x24, "Trumpet",  "Trumpet*",
/* 07 */ 0x34,0x30,0x20,0x20,0x50,0x30,0x06,0x06, "PipeOrgn", "Pipe Organ 1",
/* 08 */ 0xFF,0x52,0x20,0x20,0xD9,0xD9,0x24,0x24, "Xylophon", "Xylophone",
/* 09 */ 0x63,0x63,0x20,0x20,0xFC,0xF8,0x29,0x29, "Organ",    "Organ*",
/* 10 */ 0x41,0x41,0x20,0x20,0xA3,0xA3,0x05,0x05, "Guitar",   "Guitar*",
/* 11 */ 0x53,0x53,0x20,0x20,0xF5,0xF5,0x03,0x03, "Santool",  "Santool 1",
/* 12 */ 0x23,0x43,0x29,0x20,0xBF,0xBF,0x05,0x05, "Elecpian", "Electric Piano 1*",
/* 13 */ 0x03,0x09,0x20,0x20,0xD2,0xB4,0xF5,0xF5, "Clavicod", "Clavicode 1",
/* 14 */ 0x01,0x00,0x20,0x20,0xA3,0xE2,0xF4,0xF4, "Harpsicd", "Harpsicode 1*",
/* 15 */ 0x01,0x01,0x20,0x20,0xC0,0xB4,0xF6,0xF6, "Harpscd2", "Harpsicode 2",
/* 16 */ 0xF1,0xF1,0x20,0x20,0xD1,0xD1,0xF2,0xF2, "Vibraphn", "Vibraphone*",
/* 17 */ 0x11,0x11,0x20,0x20,0xFC,0xD2,0x83,0x83, "Koto",     "Koto 1",
/* 18 */ 0x01,0x10,0x20,0x20,0xCA,0xE6,0x24,0x24, "Taiko",    "Taiko",
/* 19 */ 0xE0,0xF4,0x20,0x20,0xF1,0xF0,0x08,0x08, "Engine",   "Engine 1",
/* 20 */ 0xFF,0x70,0x20,0x20,0x1F,0x1F,0x01,0x01, "UFO",      "UFO",
/* 21 */ 0x11,0x11,0x20,0x20,0xFA,0xF2,0xF4,0xF4, "SynBell",  "Synthesizer bell",
/* 22 */ 0xA6,0x42,0x20,0x20,0xB9,0xB9,0x02,0x02, "Chime",    "Chime",
/* 23 */ 0x31,0x31,0x20,0x20,0xF9,0xF9,0x04,0x04, "SynBass",  "Synthesizer bass*",
/* 24 */ 0x42,0x44,0x20,0x20,0x94,0xB0,0xF6,0xF6, "Synthsiz", "Synthesizer*",
/* 25 */ 0x03,0x03,0x20,0x20,0xD9,0xD9,0x06,0x06, "SynPercu", "Synthesizer Percussion", 
/* 26 */ 0x40,0x00,0x20,0x20,0xD9,0xD9,0x04,0x04, "SynRhyth", "Synthesizer Rhythm",
/* 27 */ 0x03,0x03,0x20,0x20,0xFF,0xFF,0x06,0x06, "HarmDrum", "Harm Drum",
/* 28 */ 0x18,0x11,0x20,0x20,0xF5,0xF5,0x26,0x26, "Cowbell",  "Cowbell",
/* 29 */ 0x0B,0x04,0x20,0x20,0xF5,0xF5,0x27,0x27, "ClseHiht", "Close Hi-hat",
/* 30 */ 0x40,0x40,0x20,0x20,0xD0,0xD6,0x27,0x27, "SnareDrm", "Snare Drum",
/* 31 */ 0x00,0x01,0x20,0x20,0xE3,0xE3,0x25,0x25, "BassDrum", "Bass Drum",
/* 32 */ 0x11,0x11,0x08,0x20,0xFA,0xB2,0xF4,0xF4, "Piano 3",  "Piano 3",
/* 33 */ 0x11,0x11,0xBD,0x20,0xC0,0xB2,0xF4,0xF4, "Elecpia2", "Electric Piano 2*",
/* 34 */ 0x19,0x53,0xFF,0x20,0xE7,0x95,0x03,0x03, "Santool2", "Santool 2",
/* 35 */ 0x30,0x70,0xFF,0x20,0x42,0x62,0x24,0x24, "Brass",    "Brass",
/* 36 */ 0x62,0x71,0x25,0x20,0x64,0x43,0x26,0x26, "Flute 2",  "Flute 2",
/* 37 */ 0x21,0x03,0x2B,0x20,0x90,0xD4,0xF5,0xF5, "Clavicd2", "Clavicode 2",
/* 38 */ 0x01,0x03,0x0A,0x20,0x90,0xA4,0xF5,0xF5, "Clavicd3", "Clavicode 3",
/* 39 */ 0x43,0x53,0x0E,0x20,0xB5,0xE9,0x84,0x04, "Koto 2",   "Koto 2",
/* 40 */ 0x34,0x30,0x20,0x20,0x50,0x30,0x06,0x06, "PipeOrg2", "Pipe Organ 2",
/* 41 */ 0x33,0x33,0x20,0x20,0xF5,0xF5,0x15,0x15, "PohdsPLA", "PohdsPLA",
/* 42 */ 0x13,0x13,0x34,0x20,0xF5,0xF5,0x03,0x03, "PohdsPRA", "RohdsPRA",
/* 43 */ 0x61,0x21,0x20,0x20,0x76,0x54,0x06,0x06, "Orch L",   "Orch L",
/* 44 */ 0x63,0x70,0x20,0x20,0x4B,0x4B,0x15,0x15, "Orch R",   "Orch R",
/* 45 */ 0xA1,0xA1,0x20,0x20,0x76,0x54,0x07,0x07, "SynViol",  "Synthesizer Violin",
/* 46 */ 0x61,0x78,0x20,0x20,0x85,0xF2,0x03,0x03, "SynOrgan", "Synthesizer Organ",
/* 47 */ 0x31,0x71,0x35,0x20,0xB6,0xF9,0x26,0x26, "SynBrass", "Synthesizer Brass",
/* 48 */ 0x61,0x71,0xAD,0x20,0x75,0xF2,0x03,0x03, "Tube",     "Tube*",
/* 49 */ 0x03,0x0C,0x14,0x20,0xA7,0xFC,0x15,0x15, "Shamisen", "Shamisen",
/* 50 */ 0x13,0x32,0x20,0x20,0x20,0x85,0xAF,0xAF, "Magical",  "Magical",
/* 51 */ 0xF1,0x31,0xFF,0x20,0x23,0x40,0x09,0x09, "Huwawa",   "Huwawa",
/* 52 */ 0xF0,0x74,0xB7,0x20,0x5A,0x43,0xFC,0xFC, "WnderFlt", "Wander Flat",
/* 53 */ 0x20,0x71,0x20,0x20,0xD5,0xD5,0x06,0x06, "Hardrock", "Hardrock",
/* 54 */ 0x30,0x32,0x20,0x20,0x40,0x40,0x74,0x74, "Machine",  "Machine",
/* 55 */ 0x30,0x32,0x20,0x20,0x40,0x40,0x74,0x74, "MachineV", "Machine V",
/* 56 */ 0x01,0x08,0x20,0x20,0x78,0xF8,0xF9,0xF9, "Comic",    "Comic",
/* 57 */ 0xC8,0xC0,0x20,0x20,0xF7,0xF7,0xF9,0xF9, "SE-Comic", "SE-Comic",
/* 58 */ 0x49,0x40,0x29,0x20,0xF9,0xF9,0x05,0x05, "SE-Laser", "SE-Laser",
/* 59 */ 0xCD,0x42,0x20,0x20,0xA2,0xF0,0x01,0x01, "SE-Noise", "SE-Noise",
/* 60 */ 0x51,0x42,0x20,0x20,0x13,0x10,0x01,0x01, "SE-Star",  "SE-Star 1",
/* 61 */ 0x51,0x42,0x20,0x20,0x13,0x10,0x01,0x01, "SE-Star2", "SE-Star 2",
/* 62 */ 0x30,0x34,0x20,0x20,0x23,0x70,0x02,0x02, "Engine 2", "Engine 2",
/* 63 */ 0x00,0x00,0x20,0x20,0x00,0x00,0xFF,0xFF, "Silence",  "Silence",
};
}//namespace OPLDRV
//===============================================

#endif //#ifndef __OPLDRV_INST_DATA2_H__

/* 

;===MML for MGSDRV ===

@v16 = { ; (Built-in rom #0) Piano 1*
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  15,15,15, 4, 0, 1, 0, 0, 0, 1, 0,
  11, 2,15, 4, 0, 1, 0, 0, 0, 1, 0 }


@v16 = { ; (Built-in rom #1) Piano 2
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  15,11,15, 3, 0, 0, 0, 0, 1, 1, 0,
  11, 2,15, 3, 0, 0, 0, 0, 0, 1, 0 }


@v16 = { ; (Built-in rom #2) Violin*
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  11, 4, 1, 7, 0, 1, 0, 1, 1, 0, 0,
   5, 6, 1, 7, 0, 1, 0, 1, 1, 0, 0 }


@v16 = { ; (Built-in rom #3) Flute 1*
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
   4, 3, 2, 6, 0, 1, 0, 0, 1, 1, 0,
   4, 3, 2, 6, 0, 1, 0, 0, 1, 1, 0 }


@v16 = { ; (Built-in rom #4) Clarinet*
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
   8, 8, 0, 6, 0, 2, 1, 0, 1, 0, 0,
   5, 4, 0, 6, 0, 0, 0, 0, 1, 1, 0 }


@v16 = { ; (Built-in rom #5) Oboe*
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
   7, 2, 1,12, 0, 1, 0, 0, 1, 1, 0,
   5, 6, 1,12, 0, 4, 0, 0, 1, 1, 0 }


@v16 = { ; (Built-in rom #6) Trumpet*
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
   5, 3, 2, 4, 0, 1, 0, 1, 1, 1, 0,
   5, 2, 2, 4, 0, 1, 0, 1, 1, 1, 0 }


@v16 = { ; (Built-in rom #7) Pipe Organ 1
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
   5, 0, 0, 6, 0, 4, 0, 0, 1, 1, 0,
   3, 0, 0, 6, 0, 0, 0, 0, 1, 1, 0 }


@v16 = { ; (Built-in rom #8) Xylophone
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  13, 9, 2, 4, 0,15, 1, 1, 1, 1, 0,
  13, 9, 2, 4, 0, 2, 0, 1, 0, 1, 0 }


@v16 = { ; (Built-in rom #9) Organ*
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  15,12, 2, 9, 0, 3, 0, 1, 1, 0, 0,
  15, 8, 2, 9, 0, 3, 0, 1, 1, 0, 0 }


@v16 = { ; (Built-in rom #10) Guitar*
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  10, 3, 0, 5, 0, 1, 0, 1, 0, 0, 0,
  10, 3, 0, 5, 0, 1, 0, 1, 0, 0, 0 }


@v16 = { ; (Built-in rom #11) Santool 1
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  15, 5, 0, 3, 0, 3, 0, 1, 0, 1, 0,
  15, 5, 0, 3, 0, 3, 0, 1, 0, 1, 0 }


@v16 = { ; (Built-in rom #12) Electric Piano 1*
;       TL FB
        41, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  11,15, 0, 5, 0, 3, 0, 0, 1, 0, 0,
  11,15, 0, 5, 0, 3, 0, 1, 0, 0, 0 }


@v16 = { ; (Built-in rom #13) Clavicode 1
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  13, 2,15, 5, 0, 3, 0, 0, 0, 0, 0,
  11, 4,15, 5, 0, 9, 0, 0, 0, 0, 0 }


@v16 = { ; (Built-in rom #14) Harpsicode 1*
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  10, 3,15, 4, 0, 1, 0, 0, 0, 0, 0,
  14, 2,15, 4, 0, 0, 0, 0, 0, 0, 0 }


@v16 = { ; (Built-in rom #15) Harpsicode 2
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  12, 0,15, 6, 0, 1, 0, 0, 0, 0, 0,
  11, 4,15, 6, 0, 1, 0, 0, 0, 0, 0 }


@v16 = { ; (Built-in rom #16) Vibraphone*
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  13, 1,15, 2, 0, 1, 1, 1, 1, 1, 0,
  13, 1,15, 2, 0, 1, 1, 1, 1, 1, 0 }


@v16 = { ; (Built-in rom #17) Koto 1
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  15,12, 8, 3, 0, 1, 0, 0, 0, 1, 0,
  13, 2, 8, 3, 0, 1, 0, 0, 0, 1, 0 }


@v16 = { ; (Built-in rom #18) Taiko
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  12,10, 2, 4, 0, 1, 0, 0, 0, 0, 0,
  14, 6, 2, 4, 0, 0, 0, 0, 0, 1, 0 }


@v16 = { ; (Built-in rom #19) Engine 1
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  15, 1, 0, 8, 0, 0, 1, 1, 1, 0, 0,
  15, 0, 0, 8, 0, 4, 1, 1, 1, 1, 0 }


@v16 = { ; (Built-in rom #20) UFO
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
   1,15, 0, 1, 0,15, 1, 1, 1, 1, 0,
   1,15, 0, 1, 0, 0, 0, 1, 1, 1, 0 }


@v16 = { ; (Built-in rom #21) Synthesizer bell
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  15,10,15, 4, 0, 1, 0, 0, 0, 1, 0,
  15, 2,15, 4, 0, 1, 0, 0, 0, 1, 0 }


@v16 = { ; (Built-in rom #22) Chime
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  11, 9, 0, 2, 0, 6, 1, 0, 1, 0, 0,
  11, 9, 0, 2, 0, 2, 0, 1, 0, 0, 0 }


@v16 = { ; (Built-in rom #23) Synthesizer bass*
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  15, 9, 0, 4, 0, 1, 0, 0, 1, 1, 0,
  15, 9, 0, 4, 0, 1, 0, 0, 1, 1, 0 }


@v16 = { ; (Built-in rom #24) Synthesizer*
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
   9, 4,15, 6, 0, 2, 0, 1, 0, 0, 0,
  11, 0,15, 6, 0, 4, 0, 1, 0, 0, 0 }


@v16 = { ; (Built-in rom #25) Synthesizer Percussion
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  13, 9, 0, 6, 0, 3, 0, 0, 0, 0, 0,
  13, 9, 0, 6, 0, 3, 0, 0, 0, 0, 0 }


@v16 = { ; (Built-in rom #26) Synthesizer Rhythm
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  13, 9, 0, 4, 0, 0, 0, 1, 0, 0, 0,
  13, 9, 0, 4, 0, 0, 0, 0, 0, 0, 0 }


@v16 = { ; (Built-in rom #27) Harm Drum
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  15,15, 0, 6, 0, 3, 0, 0, 0, 0, 0,
  15,15, 0, 6, 0, 3, 0, 0, 0, 0, 0 }


@v16 = { ; (Built-in rom #28) Cowbell
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  15, 5, 2, 6, 0, 8, 0, 0, 0, 1, 0,
  15, 5, 2, 6, 0, 1, 0, 0, 0, 1, 0 }


@v16 = { ; (Built-in rom #29) Close Hi-hat
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  15, 5, 2, 7, 0,11, 0, 0, 0, 0, 0,
  15, 5, 2, 7, 0, 4, 0, 0, 0, 0, 0 }


@v16 = { ; (Built-in rom #30) Snare Drum
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  13, 0, 2, 7, 0, 0, 0, 1, 0, 0, 0,
  13, 6, 2, 7, 0, 0, 0, 1, 0, 0, 0 }


@v16 = { ; (Built-in rom #31) Bass Drum
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  14, 3, 2, 5, 0, 0, 0, 0, 0, 0, 0,
  14, 3, 2, 5, 0, 1, 0, 0, 0, 0, 0 }


@v16 = { ; (Built-in rom #32) Piano 3
;       TL FB
         8, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  15,10,15, 4, 0, 1, 0, 0, 0, 1, 0,
  11, 2,15, 4, 0, 1, 0, 0, 0, 1, 0 }


@v16 = { ; (Built-in rom #33) Electric Piano 2*
;       TL FB
        61, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  12, 0,15, 4, 2, 1, 0, 0, 0, 1, 0,
  11, 2,15, 4, 0, 1, 0, 0, 0, 1, 0 }


@v16 = { ; (Built-in rom #34) Santool 2
;       TL FB
        63, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  14, 7, 0, 3, 3, 9, 0, 0, 0, 1, 0,
   9, 5, 0, 3, 0, 3, 0, 1, 0, 1, 0 }


@v16 = { ; (Built-in rom #35) Brass
;       TL FB
        63, 0,
; AR DR SL RR KL MT AM VB EG KR DT
   4, 2, 2, 4, 3, 0, 0, 0, 1, 1, 0,
   6, 2, 2, 4, 0, 0, 0, 1, 1, 1, 0 }


@v16 = { ; (Built-in rom #36) Flute 2
;       TL FB
        37, 0,
; AR DR SL RR KL MT AM VB EG KR DT
   6, 4, 2, 6, 0, 2, 0, 1, 1, 0, 0,
   4, 3, 2, 6, 0, 1, 0, 1, 1, 1, 0 }


@v16 = { ; (Built-in rom #37) Clavicode 2
;       TL FB
        43, 0,
; AR DR SL RR KL MT AM VB EG KR DT
   9, 0,15, 5, 0, 1, 0, 0, 1, 0, 0,
  13, 4,15, 5, 0, 3, 0, 0, 0, 0, 0 }


@v16 = { ; (Built-in rom #38) Clavicode 3
;       TL FB
        10, 0,
; AR DR SL RR KL MT AM VB EG KR DT
   9, 0,15, 5, 0, 1, 0, 0, 0, 0, 0,
  10, 4,15, 5, 0, 3, 0, 0, 0, 0, 0 }


@v16 = { ; (Built-in rom #39) Koto 2
;       TL FB
        14, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  11, 5, 8, 4, 0, 3, 0, 1, 0, 0, 0,
  14, 9, 0, 4, 0, 3, 0, 1, 0, 1, 0 }


@v16 = { ; (Built-in rom #40) Pipe Organ 2
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
   5, 0, 0, 6, 0, 4, 0, 0, 1, 1, 0,
   3, 0, 0, 6, 0, 0, 0, 0, 1, 1, 0 }


@v16 = { ; (Built-in rom #41) PohdsPLA
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  15, 5, 1, 5, 0, 3, 0, 0, 1, 1, 0,
  15, 5, 1, 5, 0, 3, 0, 0, 1, 1, 0 }


@v16 = { ; (Built-in rom #42) RohdsPRA
;       TL FB
        52, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  15, 5, 0, 3, 0, 3, 0, 0, 0, 1, 0,
  15, 5, 0, 3, 0, 3, 0, 0, 0, 1, 0 }


@v16 = { ; (Built-in rom #43) Orch L
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
   7, 6, 0, 6, 0, 1, 0, 1, 1, 0, 0,
   5, 4, 0, 6, 0, 1, 0, 0, 1, 0, 0 }


@v16 = { ; (Built-in rom #44) Orch R
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
   4,11, 1, 5, 0, 3, 0, 1, 1, 0, 0,
   4,11, 1, 5, 0, 0, 0, 1, 1, 1, 0 }


@v16 = { ; (Built-in rom #45) Synthesizer Violin
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
   7, 6, 0, 7, 0, 1, 1, 0, 1, 0, 0,
   5, 4, 0, 7, 0, 1, 1, 0, 1, 0, 0 }


@v16 = { ; (Built-in rom #46) Synthesizer Organ
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
   8, 5, 0, 3, 0, 1, 0, 1, 1, 0, 0,
  15, 2, 0, 3, 0, 8, 0, 1, 1, 1, 0 }


@v16 = { ; (Built-in rom #47) Synthesizer Brass
;       TL FB
        53, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  11, 6, 2, 6, 0, 1, 0, 0, 1, 1, 0,
  15, 9, 2, 6, 0, 1, 0, 1, 1, 1, 0 }


@v16 = { ; (Built-in rom #48) Tube*
;       TL FB
        45, 0,
; AR DR SL RR KL MT AM VB EG KR DT
   7, 5, 0, 3, 2, 1, 0, 1, 1, 0, 0,
  15, 2, 0, 3, 0, 1, 0, 1, 1, 1, 0 }


@v16 = { ; (Built-in rom #49) Shamisen
;       TL FB
        20, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  10, 7, 1, 5, 0, 3, 0, 0, 0, 0, 0,
  15,12, 1, 5, 0,12, 0, 0, 0, 0, 0 }


@v16 = { ; (Built-in rom #50) Magical
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
   2, 0,10,15, 0, 3, 0, 0, 0, 1, 0,
   8, 5,10,15, 0, 2, 0, 0, 1, 1, 0 }


@v16 = { ; (Built-in rom #51) Huwawa
;       TL FB
        63, 0,
; AR DR SL RR KL MT AM VB EG KR DT
   2, 3, 0, 9, 3, 1, 1, 1, 1, 1, 0,
   4, 0, 0, 9, 0, 1, 0, 0, 1, 1, 0 }


@v16 = { ; (Built-in rom #52) Wander Flat
;       TL FB
        55, 0,
; AR DR SL RR KL MT AM VB EG KR DT
   5,10,15,12, 2, 0, 1, 1, 1, 1, 0,
   4, 3,15,12, 0, 4, 0, 1, 1, 1, 0 }


@v16 = { ; (Built-in rom #53) Hardrock
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  13, 5, 0, 6, 0, 0, 0, 0, 1, 0, 0,
  13, 5, 0, 6, 0, 1, 0, 1, 1, 1, 0 }


@v16 = { ; (Built-in rom #54) Machine
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
   4, 0, 7, 4, 0, 0, 0, 0, 1, 1, 0,
   4, 0, 7, 4, 0, 2, 0, 0, 1, 1, 0 }


@v16 = { ; (Built-in rom #55) Machine V
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
   4, 0, 7, 4, 0, 0, 0, 0, 1, 1, 0,
   4, 0, 7, 4, 0, 2, 0, 0, 1, 1, 0 }


@v16 = { ; (Built-in rom #56) Comic
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
   7, 8,15, 9, 0, 1, 0, 0, 0, 0, 0,
  15, 8,15, 9, 0, 8, 0, 0, 0, 0, 0 }


@v16 = { ; (Built-in rom #57) SE-Comic
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  15, 7,15, 9, 0, 8, 1, 1, 0, 0, 0,
  15, 7,15, 9, 0, 0, 1, 1, 0, 0, 0 }


@v16 = { ; (Built-in rom #58) SE-Laser
;       TL FB
        41, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  15, 9, 0, 5, 0, 9, 0, 1, 0, 0, 0,
  15, 9, 0, 5, 0, 0, 0, 1, 0, 0, 0 }


@v16 = { ; (Built-in rom #59) SE-Noise
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
  10, 2, 0, 1, 0,13, 1, 1, 0, 0, 0,
  15, 0, 0, 1, 0, 2, 0, 1, 0, 0, 0 }


@v16 = { ; (Built-in rom #60) SE-Star 1
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
   1, 3, 0, 1, 0, 1, 0, 1, 0, 1, 0,
   1, 0, 0, 1, 0, 2, 0, 1, 0, 0, 0 }


@v16 = { ; (Built-in rom #61) SE-Star 2
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
   1, 3, 0, 1, 0, 1, 0, 1, 0, 1, 0,
   1, 0, 0, 1, 0, 2, 0, 1, 0, 0, 0 }


@v16 = { ; (Built-in rom #62) Engine 2
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
   2, 3, 0, 2, 0, 0, 0, 0, 1, 1, 0,
   7, 0, 0, 2, 0, 4, 0, 0, 1, 1, 0 }


@v16 = { ; (Built-in rom #63) Silence
;       TL FB
        32, 0,
; AR DR SL RR KL MT AM VB EG KR DT
   0, 0,15,15, 0, 0, 0, 0, 0, 0, 0,
   0, 0,15,15, 0, 0, 0, 0, 0, 0, 0 }

*/
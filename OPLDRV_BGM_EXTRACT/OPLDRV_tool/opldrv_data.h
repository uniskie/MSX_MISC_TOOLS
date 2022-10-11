
#ifndef __OPLDRV_DATA_H__
#define __OPLDRV_DATA_H__

#include <vector>
#include <map>
#include "uni_common.h"


namespace OPLDRV {

class OplDrvData
{
public:
	class Header;
	class Command;

	/*
	# FM-BIOS MUSIC DATA

	## メロディ6音+リズム構成のヘッダ

	| adr. | value             | size    | desc.
	|------|-------------------|---------|-------|
	| +00H | rhythm オフセット | 2バイト | 000EH
	| +02H | CH1 オフセット    | 2バイト |
	| +04H | CH2 オフセット    | 2バイト |
	| +06H | CH3 オフセット    | 2バイト |
	| +08H | CH4 オフセット    | 2バイト |
	| +0AH | CH5 オフセット    | 2バイト |
	| +0CH | CH6 オフセット    | 2バイト |
	| +0EH | データ本体        |         |


	## メロディ9音構成のヘッダ

	| adr. | value          | size    | desc.
	|------|----------------|---------|-------|
	| +00H | CH1 オフセット | 2バイト | 0012H
	| +02H | CH2 オフセット | 2バイト |
	| +04H | CH3 オフセット | 2バイト |
	| +06H | CH4 オフセット | 2バイト |
	| +08H | CH5 オフセット | 2バイト |
	| +0AH | CH6 オフセット | 2バイト |
	| +0CH | CH7 オフセット | 2バイト |
	| +0EH | CH8 オフセット | 2バイト |
	| +10H | CH1 オフセット | 2バイト |
	| +14H | データ本体     |         |
	*/
public:
	//--------------------------------------------------
	//! OPLDRV データのヘッダー部
	//--------------------------------------------------
	class Header
	{
	public:
		enum {
			mode_r      = 0x000e,	// rhyhm mode (melody 6ch + rhythm)
			ch_count_r  = 7,		// rhyhm mode (melody 6ch + rhythm 1ch)
			ch_count_rm = 6,		// rhyhm mode melody part (6ch) only
			mode_m      = 0x0012,	// melody mode (melody 9ch)
			ch_count_m  = 9,		// melody mode (9ch)
		};

	public:
		Header();
		Header(const u8* data_ptr, const u8* end_ptr);

		bool isRhythmMode() const;
		int getMelodyChCount() const { return isRhythmMode() ? ch_count_rm : ch_count_m; }
		int getChannelCount() const { return isRhythmMode() ? ch_count_r : ch_count_m; }

		void from_binary(const u8* data_ptr, const u8* end_ptr);
		void clear();

		u16 get_melody_binary_offset(u8 ch);
		u16 get_rhythm_binary_offset();

		u16	offset[ch_count_m];
	};

	/*
	## データ本体

	### メロディ部(FM部)

	| value      | 意味         | 補足
	|------------|--------------|----------------------------------------------------------------------|
	|  00H       | 休符         | 続く1バイトが音長。<br> 音長が0FFHのときはさらに続く1バイトも音長に加算。
	|  01H～ 5FH | 音程         | 続く1バイトが音長。<br> 音長が0FFHのときはさらに続く1バイトも音長に加算。
	|  60H～ 6FH | 音量         | この値から60Hを引いた値が、音量として使用される。
	|  70H～ 7FH | 音色         | この値から70Hを引いた値が、音色番号として使用される。
	|  80H, 81H  | サスティン   | 80HでサスティンOFF。81HでサスティンON。
	|  82H       | 拡張音色     | 続く1バイトの値(0～63)がROMの内蔵音色番号。(音色データは4C00H)
	|  83H       | ユーザー音色 | 続く2バイトの値が音色データ先頭アドレス。（絶対アドレス）
	|  84H       | レガートオフ | 音を音符毎に切る。
	|  85H       | レガートオン | 音を切らずにつなぐ。
	|  86H       | Q指定        | 続く1バイト(1～8)で指定。（レガートオン時は、Q指定を無視）
	|  87H～0FEH | 未使用       |
	|  0FFH      | 終了         | チャンネル毎のデータの終了コード。

	### 音程データ表

	00H～5FHが音程コマンドだが、00HHは休符となる為、
	使用できる音程はo1cから08a#まで。
	o8bは使用できない。

	|   | C   | C#  | D   | D#  | E   | F   | F#  | G   | G#  | A   | A#  | B   |
	|:-:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:----:|
	| 1 | 01H | 02H | 03H | 04H | 05H | 06H | 07H | 08H | 09H | 0AH | 0BH | 0CH |
	| 2 | 0DH | 0EH | 0FH | 10H | 11H | 12H | 13H | 14H | 15H | 16H | 17H | 18H |
	| 3 | 19H | 0AH | 1BH | 1CH | 1DH | 1EH | 1FH | 20H | 21H | 22H | 23H | 24H |
	| 4 | 25H | 26H | 27H | 28H | 29H | 2AH | 2BH | 2CH | 2DH | 2EH | 2FH | 30H |
	| 5 | 31H | 32H | 33H | 34H | 35H | 36H | 37H | 38H | 39H | 3AH | 3BH | 3CH |
	| 6 | 3DH | 3EH | 3FH | 40H | 41H | 42H | 43H | 44H | 45H | 46H | 47H | 48H |
	| 7 | 49H | 4AH | 4BH | 4CH | 4DH | 4EH | 4FH | 50H | 51H | 52H | 53H | 54H |
	| 8 | 55H | 56H | 57H | 58H | 59H | 5AH | 5BH | 5CH | 5DH | 5EH | 5FH | --- |

	### リズム部

	```
	 BIT |  7  |  6  |  5  |  4  |  3  |  2  |  1  |  0  |
	---- |-----|-----|-----|-----|-----|-----|-----|-----|
		 |  V  |  0  |  1  |  B  |  S  |  T  |  C  |  H  |
	```

	参考：OPLL R#0E リズムレジスタ
	```
	 BIT |  7  |  6  |  5  |  4  |  3  |  2  |  1  |  0  |
	---- |-----|-----|-----|-----|-----|-----|-----|-----|
		 |  0  |  0  |  R  |  B  |  S  |  T  |  C  |  H  |
	R = Rhytm Mode
	```


	| ビット    | 意味
	|-----------|------|
	| B,S,T,C,H | 各ビットが1なら、そのビットに対応した楽器が選択される。
	| V         | 0 = リズム発声。続くデータが音長データ。<br> （読み出し方はメロディ部の音長の場合と同じ）
	|           | 1 = 音量を指定します。続く1バイトが音量データ(0～15)。
	| 0FFH      | リズム部のデータの最終コード。
*/

public:
	//--------------------------------------------------
	//! OPLDRVコマンド
	//--------------------------------------------------
	class Command
	{
	public:
		enum ModeID
		{
			MODE_NONE	= -1,
			MODE_MELODY	= 0,
			MODE_RHYTHM	= 1,
		};
		enum CommandID
		{
			CMD_NONE		= -1,	// no command
			CMD_NOTE		= 0x00,	// note					0x00 - 0x5f + u8(0 - 255) * n
			CMD_VOL			= 0x60,	// volume				0x60 - 0x6f
			CMD_VOICE		= 0x70,	// voice no.			0x70 - 0x7f
			CMD_SUSTAIN		= 0x80,	// sustain off/on		0x80, 0x81
			CMD_ROM_VOICE	= 0x82,	// ROM voice			0x82 + u8(0 - 63)
			CMD_USER_VOICE	= 0x83,	// user defined voice	0x83 + u16(address)
			CMD_LEGATO		= 0x84,	// legato off/on		0x84, 0x85
			CMD_QUANTIZE	= 0x86,	// Q					0x86 + u8(1 - 8)
			CMD_END			= 0xff,	// end mark				0xff

			CMD_R_NOTE		= 0x20,	// note			0x20 - 0x3f + u8(0 - 255) * n
			CMD_R_VOL		= 0xa0,	// volume		0x80 - 0xbf + u8(0 - 15)

			CMD_R_MASK		= 0xe0,	// other than rhythm bit = 0b11100000	
			RHYTHM_BITS		= 0x1f,	//            rhythm bit = 0b00011111
		};
		enum RhythmBit
		{
			BIT_BASS_DRUM	= 0x10,
			BIT_SNARE_DRUM	= 0x08,
			BIT_TOM_TOM		= 0x04,
			BIT_CYMBAL		= 0x02,
			BIT_HI_HUT		= 0x01,
		};

	public:
		int		m_mode;
		int		m_cmd;
		u8		m_opt;
		u64		m_param;

		const u64 time_max = u64(-1);

	public:
		Command() 
			: m_mode(MODE_NONE)
			, m_cmd(CMD_NONE)
			, m_opt(0)
			, m_param(0)
		{}
		virtual ~Command() {}

		void clear();

		const u8* read_time(u64& time, const u8* data_ptr, const u8* end_ptr);
		const u8* read_melody(const u8* data_ptr, const u8* end_ptr);
		const u8* read_rhythm(const u8* data_ptr, const u8* end_ptr);

		u8* write_time(u64 time, u8* data_ptr, const u8* end_ptr) const;
		u8* write_melody(u8* data_ptr, const u8* end_ptr) const;
		u8* write_rhythm(u8* data_ptr, const u8* end_ptr) const;

		string getCmdInfo() const;

		static string getCmdName(int cmd);
		static string getOctaveName(int param);
		static string getNoteName(int param);
		static string getRhythmName(int param, bool use_space = false);
	};


	
/*
	## ユーザー音色データ

	```
		 |  7  |  6  |  5  |  4  |  3  |  2  |  1  |  0  |
	====||=====|=====|=====|=====|=====|=====|=====|=====||=====|
	 +0 || AM  | VIB | EG  | KSR |        MULTIPLE       || (M) |
	----||-----+-----+-----+-----+-----------------------||-----|
	 +1 || AM  | VIB | EG  | KSR |        MULTIPLE       || (C) |
	----||-----+-----+-----+-----+-----------------------||-----|
	 +2 ||   KSL(M)  |     TOTAL LEVEL (MODULATOR)       || (M) |
	----||-----------+-----+-----+-----+-----------------||-----|
	 +3 ||   KSL(C)  | --  | DC  | DM  |    FEEDBACK     ||(C/M)|
	----||-----------+-----+-----|-----+-----------------||-----|
	 +4 ||      Attack Rate      |       Decay Rate      || (M) |
	----||-----------------------|-----------------------||-----|
	 +5 ||      Attack Rate      |       Decay Rate      || (C) |
	----||-----------------------|-----------------------||-----|
	 +6 ||     Sustain Level     |      Release Rate     || (C) |
	----||-----------------------|-----------------------||-----|
	 +7 ||     Sustain Level     |      Release Rate     || (C) |
	----||-----------------------|-----------------------||-----|
	```
	*/
public:
	struct VoiceRaw
	{
		enum {
			data_size = 8,
		};
		u8 data[data_size];
	};
	struct ExtraVoiceSet
	{
		enum {
			voice_count = 64,
		};
		VoiceRaw list[voice_count];
	};

	class VoiceData
	{
	public:
		VoiceData()
			: offset(0)
		{
			std::fill(m_data.data, m_data.data + countof(m_data.data), 0);
		}
	public:
		VoiceRaw m_data;
		u16 offset;
	};

public:

	OplDrvData();
	OplDrvData(const u8* data_ptr, const u8* end_ptr, u16 base_address);
	~OplDrvData() {};

	void clear();
	bool from_binary(const u8* data_ptr, const u8* end_ptr, u16 base_address);

	bool convert_voice_rom_to_user(int romtype);

	bool make_binary(std::vector<u8>& outb, u16 base_address);

public:
	Header	m_header;
	std::vector<Command> m_melody_ch[Header::ch_count_m];
	std::vector<Command> m_rhythm_ch;

	std::map<u16, VoiceData> m_voice;

	std::vector<u8> binary_data;

public:
	static bool trace_mode;
};

} //namespace OPLDRV

#endif	//#ifndef __OPLDRV_DATA_H__

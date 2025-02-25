
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

	## �����f�B6��+���Y���\���̃w�b�_

	| adr. | value             | size    | desc.
	|------|-------------------|---------|-------|
	| +00H | rhythm �I�t�Z�b�g | 2�o�C�g | 000EH
	| +02H | CH1 �I�t�Z�b�g    | 2�o�C�g |
	| +04H | CH2 �I�t�Z�b�g    | 2�o�C�g |
	| +06H | CH3 �I�t�Z�b�g    | 2�o�C�g |
	| +08H | CH4 �I�t�Z�b�g    | 2�o�C�g |
	| +0AH | CH5 �I�t�Z�b�g    | 2�o�C�g |
	| +0CH | CH6 �I�t�Z�b�g    | 2�o�C�g |
	| +0EH | �f�[�^�{��        |         |


	## �����f�B9���\���̃w�b�_

	| adr. | value          | size    | desc.
	|------|----------------|---------|-------|
	| +00H | CH1 �I�t�Z�b�g | 2�o�C�g | 0012H
	| +02H | CH2 �I�t�Z�b�g | 2�o�C�g |
	| +04H | CH3 �I�t�Z�b�g | 2�o�C�g |
	| +06H | CH4 �I�t�Z�b�g | 2�o�C�g |
	| +08H | CH5 �I�t�Z�b�g | 2�o�C�g |
	| +0AH | CH6 �I�t�Z�b�g | 2�o�C�g |
	| +0CH | CH7 �I�t�Z�b�g | 2�o�C�g |
	| +0EH | CH8 �I�t�Z�b�g | 2�o�C�g |
	| +10H | CH1 �I�t�Z�b�g | 2�o�C�g |
	| +14H | �f�[�^�{��     |         |
	*/
public:
	//--------------------------------------------------
	//! OPLDRV �f�[�^�̃w�b�_�[��
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
	## �f�[�^�{��

	### �����f�B��(FM��)

	| value      | �Ӗ�         | �⑫
	|------------|--------------|----------------------------------------------------------------------|
	|  00H       | �x��         | ����1�o�C�g�������B<br> ������0FFH�̂Ƃ��͂���ɑ���1�o�C�g�������ɉ��Z�B
	|  01H�` 5FH | ����         | ����1�o�C�g�������B<br> ������0FFH�̂Ƃ��͂���ɑ���1�o�C�g�������ɉ��Z�B
	|  60H�` 6FH | ����         | ���̒l����60H���������l���A���ʂƂ��Ďg�p�����B
	|  70H�` 7FH | ���F         | ���̒l����70H���������l���A���F�ԍ��Ƃ��Ďg�p�����B
	|  80H, 81H  | �T�X�e�B��   | 80H�ŃT�X�e�B��OFF�B81H�ŃT�X�e�B��ON�B
	|  82H       | �g�����F     | ����1�o�C�g�̒l(0�`63)��ROM�̓������F�ԍ��B(���F�f�[�^��4C00H)
	|  83H       | ���[�U�[���F | ����2�o�C�g�̒l�����F�f�[�^�擪�A�h���X�B�i��΃A�h���X�j
	|  84H       | ���K�[�g�I�t | �����������ɐ؂�B
	|  85H       | ���K�[�g�I�� | ����؂炸�ɂȂ��B
	|  86H       | Q�w��        | ����1�o�C�g(1�`8)�Ŏw��B�i���K�[�g�I�����́AQ�w��𖳎��j
	|  87H�`0FEH | ���g�p       |
	|  0FFH      | �I��         | �`�����l�����̃f�[�^�̏I���R�[�h�B

	### �����f�[�^�\

	00H�`5FH�������R�}���h�����A00HH�͋x���ƂȂ�ׁA
	�g�p�ł��鉹����o1c����08a#�܂ŁB
	o8b�͎g�p�ł��Ȃ��B

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

	### ���Y����

	```
	 BIT |  7  |  6  |  5  |  4  |  3  |  2  |  1  |  0  |
	---- |-----|-----|-----|-----|-----|-----|-----|-----|
		 |  V  |  0  |  1  |  B  |  S  |  T  |  C  |  H  |
	```

	�Q�l�FOPLL R#0E ���Y�����W�X�^
	```
	 BIT |  7  |  6  |  5  |  4  |  3  |  2  |  1  |  0  |
	---- |-----|-----|-----|-----|-----|-----|-----|-----|
		 |  0  |  0  |  R  |  B  |  S  |  T  |  C  |  H  |
	R = Rhytm Mode
	```


	| �r�b�g    | �Ӗ�
	|-----------|------|
	| B,S,T,C,H | �e�r�b�g��1�Ȃ�A���̃r�b�g�ɑΉ������y�킪�I�������B
	| V         | 0 = ���Y�������B�����f�[�^�������f�[�^�B<br> �i�ǂݏo�����̓����f�B���̉����̏ꍇ�Ɠ����j
	|           | 1 = ���ʂ��w�肵�܂��B����1�o�C�g�����ʃf�[�^(0�`15)�B
	| 0FFH      | ���Y�����̃f�[�^�̍ŏI�R�[�h�B
*/

public:
	//--------------------------------------------------
	//! OPLDRV�R�}���h
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
		enum {
			RHYTHM_INST_NUM = 5,
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

		static int getOctave(int param);
		static string getCmdName(int cmd);
		static string getOctaveName(int param);
		static string getNoteName(int param);
		static string getRhythmName(int param, bool use_space = false);


	};


	
/*
	## ���[�U�[���F�f�[�^

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
		u8 reg[data_size];
		string name;
		string long_name;
	};
	struct ExtraVoiceSet
	{
		enum {
			voice_count = 64,
		};
		string name;
		VoiceRaw list[voice_count];
	};

	class VoiceData
	{
	public:
		VoiceData()
			: offset(0)
			, voice_no(0)
		{
			std::fill(m_data.reg, m_data.reg + countof(m_data.reg), 0);
			m_data.name = "";
			m_data.long_name = "";
		}
	public:
		VoiceRaw m_data;
		u16 offset;
		u8 voice_no;
	public:
		u8 get_TL() const { return m_data.reg[2] & 63; }
		u8 get_FB() const { return m_data.reg[3] & 7; }
		u8 get_AR(int o) const { return m_data.reg[4 + o] >> 4; }
		u8 get_DR(int o) const { return m_data.reg[4 + o] & 15; }
		u8 get_SL(int o) const { return m_data.reg[6 + o] >> 4; }
		u8 get_RR(int o) const { return m_data.reg[6 + o] & 15; }
		u8 get_KL(int o) const { return m_data.reg[2 + o] >> 6; }
		u8 get_MT(int o) const { return m_data.reg[0 + o] & 15; }
		u8 get_AM(int o) const { return m_data.reg[0 + o] >> 7; }
		u8 get_VB(int o) const { return (m_data.reg[0 + o] >> 6) & 1; }
		u8 get_EG(int o) const { return (m_data.reg[0 + o] >> 5) & 1; }
		u8 get_KR(int o) const { return (m_data.reg[0 + o] >> 4) & 1; }
		u8 get_DT(int o) const { return (m_data.reg[3] >> (3 + o)) & 1; }

		string make_mgs_mml();
	};

public:

	OplDrvData();
	OplDrvData(const u8* data_ptr, const u8* end_ptr, u16 base_address, u16 music_address);
	~OplDrvData() {};

	void clear();
	bool from_binary(const u8* data_ptr, const u8* end_ptr, u16 base_address, u16 music_address);

	bool convert_voice_rom_to_user(int romtype);
	int modify_volume(int volume_change);

	bool make_binary(std::vector<u8>& outbuffer, u16 base_address);

	bool make_mgs_mml(
		std::string& outbuffer, 
		float tempo, 
		bool mml_loop, 
		bool mml_rel_volume, 
		int def_len, 
		string title, 
		int time_signiture_d8
	);

	double calc_max_ch_time();

public:
	Header	m_header;
	std::vector<Command> m_melody_ch[Header::ch_count_m];
	std::vector<Command> m_rhythm_ch;

	std::map<u16, VoiceData> m_voice;

	std::vector<u8> binary_data;

public:
	static bool trace_mode;


	enum {
		FPS = 60,
	};
	/// TEMPO����n��������tick���v�Z
	static float tempo2tick(float tempo, int n)
	{
		return float(FPS) * 60.f * 4.f / tempo / n;
	}
	/// 4��������tick����TEMPO���v�Z
	static float l4tick2tempo(float quarter_note_tick)
	{
		return float(FPS) * 60.f / quarter_note_tick;
	}

public:
	float m_tempo;
	std::map<u8, float> m_note_length;
	void set_tempo(float tempo);
	void add_note_length(int n, float tempo);
	int get_note_length(float tick, float& note_tick);
	int compare_note_length(float tick, int n);

public:
	static const ExtraVoiceSet* getExtraVoiceSet(int rom_type);
	static string make_ex_voice_mgs_mml(int mgs_voice_no, int rom_voice_no, int rom_type);
};

} //namespace OPLDRV

#endif	//#ifndef __OPLDRV_DATA_H__

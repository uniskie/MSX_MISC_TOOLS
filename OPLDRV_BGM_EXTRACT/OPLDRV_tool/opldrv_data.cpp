#include "uni_common.h"
#include "opldrv_data.h"
#include <deque>


using namespace OPLDRV;
using namespace uni_common;

#include"opldrv_inst_data.h"	// FMPAC版 拡張音色
#include"opldrv_inst_data2.h"	// A1GT版 拡張音色

//==================================================
//
// class OplDrvData::VoiceData
// 
//==================================================

//--------------------------------------------------
//! OplDrvData::VoiceData
//! 音色定義MMLを返す（MGSDRV）
//--------------------------------------------------
string OplDrvData::VoiceData::make_mgs_mml()
{
	std::stringstream mml;
	mml
		<< "@v" << std::dec << int(voice_no)
		<< " = {"
		//<< " ; 0x" << hex(i->first, 4)
		<< " ; " << m_data.long_name
		<< std::endl
		<< ";       TL FB" << std::endl
		<< "        "
		<< dec(get_TL(), 2) << ","
		<< dec(get_FB(), 2) << "," << std::endl
		<< "; AR DR SL RR KL MT AM VB EG KR DT" << std::endl;
	for (int o = 0; o < 2; ++o)
	{
		mml
			<< "  "
			<< dec(get_AR(o), 2) << ","
			<< dec(get_DR(o), 2) << ","
			<< dec(get_SL(o), 2) << ","
			<< dec(get_RR(o), 2) << ","
			<< dec(get_KL(o), 2) << ","
			<< dec(get_MT(o), 2) << ","
			<< dec(get_AM(o), 2) << ","
			<< dec(get_VB(o), 2) << ","
			<< dec(get_EG(o), 2) << ","
			<< dec(get_KR(o), 2) << ","
			<< dec(get_DT(o), 2) << (o ? " }" : ",")
			<< std::endl;
	}
	mml << std::endl;
	return mml.str();
}

//==================================================
//
// class OplDrvData::Header
// 
//==================================================
#ifdef _DEBUG
bool OplDrvData::trace_mode = true;
#else
bool OplDrvData::trace_mode = true;
#endif

#if 0
#define MML_TRACE(S)	TRACE(S)
#else
#define MML_TRACE(...)	
#endif

//--------------------------------------------------
//! OplDrvData::Header
//! コンストラクタ
//--------------------------------------------------
OplDrvData::Header::Header()
{
	clear();
}

//--------------------------------------------------
//! OplDrvData::Header
//! コンストラクタ
//--------------------------------------------------
OplDrvData::Header::Header(const u8* data_ptr, const u8* end_ptr)
{
	clear();
	from_binary(data_ptr, end_ptr);
}

//--------------------------------------------------
//! OplDrvData::Header
//! リズムモードかどうか返す
//--------------------------------------------------
bool OplDrvData::Header::isRhythmMode() const
{
	return (offset[0] == mode_r);
}

//--------------------------------------------------
//! OplDrvData::Header
//! メロディチャンネルのデータオフセットを返す
//! 範囲外なら0
//--------------------------------------------------
u16 OplDrvData::Header::get_melody_binary_offset(u8 ch)
{
	if (isRhythmMode())
	{
		ASSERT(ch < ch_count_rm);
		if (ch < ch_count_rm)
		{
			return offset[ch + 1];
		}
	}
	else
	{
		ASSERT(ch < ch_count_m);
		if (ch < ch_count_m)
		{
			return offset[ch];
		}
	}
	return 0;	// error
}

//--------------------------------------------------
//! OplDrvData::Header
//! リズムチャンネルのデータオフセットを返す
//--------------------------------------------------
//! リズムモードでなければ0
u16 OplDrvData::Header::get_rhythm_binary_offset()
{
	if (isRhythmMode())
	{
		return offset[0];
	}
	return 0;	// not rhythm mode
}

//--------------------------------------------------
//! OplDrvData::Header
//! データをクリアする
//--------------------------------------------------
void OplDrvData::Header::clear()
{
	std::fill(offset, offset + countof(offset), 0);
}

//--------------------------------------------------
//! OplDrvData::Header
//! データをセットする
//--------------------------------------------------
void OplDrvData::Header::from_binary(const u8* data_ptr, const u8* end_ptr)
{
	const u16* p = reinterpret_cast<const u16*>(data_ptr);
	ASSERT(p);
	if (!p)
	{
		return;
	}

	int i = 0;
	for (; i < countof(offset); ++i)
	{
		if (getChannelCount() <= i)
		{
			// end of header
			break;
		}
		if (intptr_t(end_ptr) <= intptr_t(p))
		{
			print_error(string("[ERROR] not enough buffer to Header."));
			ASSERT(0);
			break;
		}
		offset[i] = *(p++);
	}
	ASSERT(getChannelCount() == i);
}

//==================================================
//
//	class OplDrvData::Command
//
//==================================================


//--------------------------------------------------
//! OplDrvData::Command
//! コマンド名取得
//--------------------------------------------------
string OplDrvData::Command::getCmdName(int cmd)
{
	switch (cmd)
	{
	case CMD_NONE:			return "NONE";
	case CMD_NOTE:			return "NOTE";
	case CMD_VOL:			return "VOL";
	case CMD_VOICE:			return "VOICE";
	case CMD_SUSTAIN:		return "SUSTAIN";
	case CMD_ROM_VOICE:		return "ROM_VOICE";
	case CMD_USER_VOICE:	return "USER_VOICE";
	case CMD_LEGATO:		return "LEGATO";
	case CMD_QUANTIZE:		return "QUANTIZE";
	case CMD_END:			return "END";
	case CMD_R_NOTE:		return "R_NOTE";
	case CMD_R_VOL:			return "R_VOL";
	}
	ASSERT(0);
	return "";
}

//--------------------------------------------------
//! OplDrvData::Command
//! オクターブ名取得
//--------------------------------------------------
string OplDrvData::Command::getOctaveName(int param)
{
	return string("O") + dec(getOctave(param));
}
//--------------------------------------------------
//! OplDrvData::Command
//! オクターブ取得
//--------------------------------------------------
int OplDrvData::Command::getOctave(int param)
{
	return int((param-1) / 12) + 1;
}

//--------------------------------------------------
//! OplDrvData::Command
//! 音階名取得
//--------------------------------------------------
string OplDrvData::Command::getNoteName(int n)
{
	if (n)
	{
		const string note[12] = {
			"C","C+","D","D+","E","F","F+","G","G+","A","A+","B",
		};
		return note[(n-1) % 12];
	}
	return "R";
}

//--------------------------------------------------
//! OplDrvData::Command
//! リズム楽器名取得
//--------------------------------------------------
string OplDrvData::Command::getRhythmName(int param, bool use_space)
{
	if (0 == (param & RHYTHM_BITS))
	{
		return use_space ? "R    " : "R";
	}

	const string inst[5] = {
		"B","S","M","C","H"
	};
	string r = "";
	for (int i = 0; i < 5; ++i)
	{
		if (param & 0x10)
		{
			r += inst[i];
		}
		else if (use_space)
		{
			r += " ";
		}
		param <<= 1;
	}
	return r;
}

//--------------------------------------------------
//! OplDrvData::Command
//! クリア
//--------------------------------------------------
void OplDrvData::Command::clear()
{
	m_mode = MODE_NONE;
	m_cmd = CMD_NONE;
	m_opt = 0;
	m_param = 0;
}

//--------------------------------------------------
//! OplDrvData::Command
//! 時間指定を読み込む
//--------------------------------------------------
const u8* OplDrvData::Command::read_time(u64& time, const u8* data_ptr, const u8* end_ptr)
{
	time = 0;
	auto p = data_ptr;

	while (p < end_ptr)
	{
		auto c = *p++;

		ASSERT(c < (time_max - time));
		if ((time_max - time) < c)
		{
			print_error(string("[CAUTION] time value over than ") + dec(time_max));
			time = time_max;
		}
		else
		{
			time += c;
		}
		if (c < 255)
		{
			return p;	// 正常終了
		}
	}
	print_error(string("[ERROR] not enough read buffer in read_time."));
	ASSERT(0);
	return p;
}

//--------------------------------------------------
//! OplDrvData::Command
//! メロディーデータを読み込む
//--------------------------------------------------
const u8* OplDrvData::Command::read_melody(const u8* data_ptr, const u8* end_ptr)
{
	clear();
	m_mode = MODE_MELODY;

	auto p = data_ptr;

	while (p < end_ptr)
	{
		auto c = *p++;
		if ((CMD_NOTE <= c) && (c <CMD_VOL))
		{
			m_cmd = CMD_NOTE;
			m_opt = c - m_cmd;
			if (end_ptr <= p)
			{
				print_error(string("[ERROR] not enough read buffer in CMD_REST."));
				ASSERT(0);
				break;
			}
			p = read_time(m_param, p, end_ptr);
			break;
		}
		else
		if ((CMD_VOL <= c) && (c < CMD_VOICE))
		{
			m_cmd = CMD_VOL;
			m_opt = c - m_cmd;
			break;
		}
		else
		if ((CMD_VOICE <= c) && (c < CMD_SUSTAIN))
		{
			m_cmd = CMD_VOICE;
			m_opt = c - m_cmd;
			break;
		}
		else
		if ((CMD_SUSTAIN <= c) && (c < CMD_ROM_VOICE))
		{
			m_cmd = CMD_SUSTAIN;
			m_opt = c - m_cmd;
			break;
		}
		else
		if (CMD_ROM_VOICE == c)
		{
			m_cmd = CMD_ROM_VOICE;
			m_opt = c - m_cmd;
			if (end_ptr <= p)
			{
				print_error(string("[ERROR] not enough read buffer in CMD_ROM_VOICE."));
				ASSERT(0);
				break;
			}
			m_param = *p++;
			ASSERT((0 <= m_param) && (m_param <63));
			break;
		}
		else
		if (CMD_USER_VOICE == c)
		{
			m_cmd = CMD_USER_VOICE;
			m_opt = c - m_cmd;
			if (end_ptr <= (p + 1))
			{
				print_error(string("[ERROR] not enough read buffer in CMD_USER_VOICE."));
				ASSERT(0);
				break;
			}
			m_param = *p++;
			m_param += (*p++) * 0x100;
			break;
		}
		else
		if ((CMD_LEGATO <= c) && (c < CMD_QUANTIZE))
		{
			m_cmd = CMD_LEGATO;
			m_opt = c - m_cmd;
			break;
		}
		else
		if (CMD_QUANTIZE == c)
		{
			m_cmd = CMD_QUANTIZE;
			m_opt = c - m_cmd;
			if (end_ptr <= p)
			{
				print_error(string("[ERROR] not enough read buffer in CMD_Q."));
				ASSERT(0);
				break;
			}
			m_param = *p++;
			break;
		}
		else
		if (CMD_END == c)
		{
			m_cmd = CMD_END;
			m_opt = c - m_cmd;
			break;
		}
		else
		{
			print_error(string("[ERROR] unknown melody command. 0x") + hex(c,2,"0"));
			ASSERT(0);
			break;
		}
		break;
	}

	return p;
}

//--------------------------------------------------
//! OplDrvData::Command
//! リズムデータを読み込む
//--------------------------------------------------
const u8* OplDrvData::Command::read_rhythm(const u8* data_ptr, const u8* end_ptr)
{
	clear();
	m_mode = MODE_RHYTHM;

	auto p = data_ptr;

	while (p < end_ptr)
	{
		auto c = *p++;
		auto cmd = c & CMD_R_MASK;
		if (CMD_R_NOTE == cmd)
		{
			m_cmd = CMD_R_NOTE;
			m_opt = c - m_cmd;
			if (end_ptr <= p)
			{
				print_error(string("[ERROR] not enough read buffer in CMD_R_NOTE."));
				ASSERT(0);
				break;
			}
			p = read_time(m_param, p, end_ptr);
			break;
		}
		else
		if (CMD_R_VOL == cmd)
		{
			m_cmd = CMD_R_VOL;
			m_opt = c - m_cmd;
			if (end_ptr <= p)
			{
				print_error(string("[ERROR] not enough read buffer in CMD_R_VOL."));
				ASSERT(0);
				break;
			}
			m_param = *p++;
			break;
		}
		else
		if (CMD_END == c)
		{
			m_cmd = CMD_END;
			m_opt = c - m_cmd;
			break;
		}
		else
		{
			print_error(string("[ERROR] unknown rhythm command. 0x") + hex(c,2,"0"));
			ASSERT(0);
		}
		break;
	}

	return p;
}

//--------------------------------------------------
//! OplDrvData::Command
//! 時間指定を書き込む
//--------------------------------------------------
u8* OplDrvData::Command::write_time(u64 time, u8* data_ptr, const u8* end_ptr) const
{
	auto p = data_ptr;

	while (p < end_ptr)
	{
		if (0xff < time)
		{
			*p++ = 0xff;
			time -= 0xff;
		}
		else
		{
			*p++ = u8(time);
			return p; // success
		}
	}
	print_error(string("[ERROR] not enough write buffer in write_time."));
	return 0;
}


//--------------------------------------------------
//! OplDrvData::Command
//! メロディーデータを書き込む
//--------------------------------------------------
u8* OplDrvData::Command::write_melody(u8* data_ptr, const u8* end_ptr) const
{
	auto p = data_ptr;
	while (p && (p < end_ptr))
	{
		switch (m_cmd)
		{
		case CMD_NOTE:
		{
			*p++ = m_cmd + m_opt;
			if (end_ptr <= p)
			{
				print_error(string("[ERROR] not enough write buffer in CMD_REST."));
				ASSERT(0);
				break;
			}
			p = write_time(m_param, p, end_ptr);
			break;
		}
		case CMD_VOL:
		{
			*p++ = m_cmd + m_opt;
			break;
		}
		case CMD_VOICE:
		{
			*p++ = m_cmd + m_opt;
			break;
		}
		case CMD_SUSTAIN:
		{
			*p++ = m_cmd + m_opt;
			break;
		}
		case CMD_ROM_VOICE:
		{
			*p++ = m_cmd + m_opt;
			if (end_ptr <= p)
			{
				print_error(string("[ERROR] not enough write buffer in CMD_ROM_VOICE."));
				ASSERT(0);
				p = 0;	// error
				break;
			}
			*p++ = u8(m_param);
			break;
		}
		case CMD_USER_VOICE:
		{
			*p++ = m_cmd + m_opt;
			if (end_ptr <= (p + 1))
			{
				print_error(string("[ERROR] not enough write buffer in CMD_USER_VOICE."));
				ASSERT(0);
				p = 0;	// error
				break;
			}
			*p++ = u8(m_param & 0xff);
			*p++ = u8(m_param >> 8);
			break;
		}
		case CMD_LEGATO:
		{
			*p++ = m_cmd + m_opt;
			break;
		}
		case CMD_QUANTIZE:
		{
			*p++ = m_cmd + m_opt;
			if (end_ptr <= p)
			{
				print_error(string("[ERROR] not enough write buffer in CMD_Q."));
				ASSERT(0);
				p = 0;	// error
				break;
			}
			*p++ = u8(m_param);
			break;
		}
		case CMD_END:
		{
			*p++ = m_cmd + m_opt;
			return p; // success
		}
		default:
		{
			print_error(string("[ERROR] unknown melody command. 0x") + hex(m_cmd,2,"0"));
			ASSERT(0);
			p = 0;	// error
			break;
		}
		}
		break;
	}

	return p;
}

//--------------------------------------------------
//! OplDrvData::Command
//! リズムデータを書き込む
//--------------------------------------------------
u8* OplDrvData::Command::write_rhythm(u8* data_ptr, const u8* end_ptr) const
{
	auto p = data_ptr;
	while (p && (p < end_ptr))
	{
		switch(m_cmd)
		{
		case CMD_R_NOTE:
		{
			*p++ = m_cmd + m_opt;
			if (end_ptr <= p)
			{
				print_error(string("[ERROR] not enough write buffer in CMD_R_NOTE."));
				ASSERT(0);
				p = 0;	// error
				break;
			}
			p = write_time(m_param, p, end_ptr);
			break;
		}
		case CMD_R_VOL:
		{
			*p++ = m_cmd + m_opt;
			if (end_ptr <= p)
			{
				print_error(string("[ERROR] not enough read buffer in CMD_R_VOL."));
				ASSERT(0);
				p = 0;	// error
				break;
			}
			*p++ = u8(m_param);
			break;
		}
		case CMD_END:
		{
			*p++ = m_cmd + m_opt;
			return p; // success
		}
		default:
		{
			print_error(string("[ERROR] unknown rhythm command. 0x") + hex(m_cmd,2,"0"));
			ASSERT(0);
			p = 0;	// error
			break;
		}
		}
		break;
	}

	return p;
}

//--------------------------------------------------
//! OplDrvData::Command
//! コマンド情報文字列を取得
//--------------------------------------------------
string OplDrvData::Command::getCmdInfo() const
{
	string s;

	if (m_mode == MODE_MELODY)
	{
		s = getCmdName(m_cmd);
		switch (m_cmd)
		{
		case CMD_NOTE:
		{
			if (m_opt)
			{
				s += " " + getOctaveName(m_opt)
					+ " " + align_left(getNoteName(m_opt), 2);
			}
			else
			{
				s += " -- R ";
			}
			s += " TIME=" + dec(m_param);
			break;
		}
		case CMD_VOL:
		{
			s += " " + dec(m_opt);
			break;
		}
		case CMD_VOICE:
		{
			s += " " + dec(m_opt);
			break;
		}
		case CMD_SUSTAIN:
		{
			s += m_opt ? " ON" : " OFF";
			break;
		}
		case CMD_ROM_VOICE:
		{
			s += " " + dec(m_param);
			break;
		}
		case CMD_USER_VOICE:
		{
			s += " 0x" + hex(m_param,4,"0");
			break;
		}
		case CMD_LEGATO:
		{
			s += m_opt ? " ON" : " OFF";
			break;
		}
		case CMD_QUANTIZE:
		{
			s += " " + dec(m_param);
			break;
		}
		case CMD_END:
		{
			break;
		}
		default:
		{
			ASSERT(0);
			break;
		}
		}
	}
	else if (m_mode == MODE_RHYTHM)
	{
		s = getCmdName(m_cmd);
		switch (m_cmd)
		{
		case CMD_R_NOTE:
		{
			s += " " + align_left(getRhythmName(m_opt), 5)
				+ " TIME=" + dec(m_param);
			break;
		}
		case CMD_R_VOL:
		{
			s += " " + align_left(getRhythmName(m_opt), 5)
				+ " " + dec(m_param);
			break;
		}
		case CMD_END:
		{
			break;
		}
		default:
		{
			ASSERT(0);
			break;
		}
		}
	}
	else
	{
		// unkown
		s = "[UNKNOWN]";
		ASSERT(0);
	}
	return s;
}

//==================================================
//
// class OplDrvData
// 
//==================================================

//--------------------------------------------------
//! OplDrvData
//! コンストラクタ
//--------------------------------------------------
OplDrvData::OplDrvData()
{
	clear();
}

//--------------------------------------------------
//! OplDrvData
//! コンストラクタ
//--------------------------------------------------
OplDrvData::OplDrvData(const u8* data_ptr, const u8* end_ptr, u16 base_address)
{
	clear();
	from_binary(data_ptr, end_ptr, base_address);
}

//--------------------------------------------------
//! OplDrvData
//! データをクリアする
//--------------------------------------------------
void OplDrvData::clear()
{
	m_header.clear();
	m_rhythm_ch.clear();
	for (int i=0; i<countof(m_melody_ch); ++i)
	{
		m_melody_ch[i].clear();
	}
	m_voice.clear();
	binary_data.clear();
}

//--------------------------------------------------
//! OplDrvData::Header
//! バイナリデータからデータを作成する
//--------------------------------------------------
bool OplDrvData::from_binary(const u8* data_ptr, const u8* end_ptr, u16 base_address)
{
	size_t data_size = end_ptr - data_ptr;

	// header
	m_header.from_binary(data_ptr, end_ptr);

	// リズムチャンネル
	if (m_header.isRhythmMode())
	{
		auto offset = m_header.get_rhythm_binary_offset();
		const u8* p = data_ptr + offset;
		m_rhythm_ch.reserve(0x1000); // 適当に予約

		if (trace_mode)
		{
			print_log("[CH. RHYTHM]");
		}

		u16 i = 0;
		if (0 == offset)
		{
			// NO DATA -> SKIP
			print_log("* NO DATA *");
		}
		else
		while (p < end_ptr)
		{
			OplDrvData::Command cmd;
			p = cmd.read_rhythm(p, end_ptr);

			if (trace_mode)
			{
				print_log(cmd.getCmdInfo());
			}

			if (cmd.m_cmd == OplDrvData::Command::CMD_NONE)
			{
				// error
				ASSERT(0);
				//clear();
				return false;
			}

			m_rhythm_ch.push_back(cmd);

			// 終端
			if (cmd.m_cmd == OplDrvData::Command::CMD_END)
			{
				// end
				break;
			}
		}
	}
	
	// メロディチャンネル
	for (int ch = 0; ch < m_header.getMelodyChCount(); ++ch)
	{
		auto offset = m_header.get_melody_binary_offset(ch);
		const u8* p = data_ptr + offset;

		m_melody_ch[ch].reserve(0x1000); // 適当に予約

		if (trace_mode)
		{
			print_log("[CH. MELODY #" + dec(ch) + "]");
		}

		u16 i = 0;
		if (0 == offset)
		{
			// NO DATA -> SKIP
			print_log("* NO DATA *");
		}
		else
		while (p < end_ptr)
		{
			OplDrvData::Command cmd;
			p = cmd.read_melody(p, end_ptr);

			if (trace_mode)
			{
				print_log(cmd.getCmdInfo());
			}

			// ユーザー定義音色
			if (cmd.m_cmd == OplDrvData::Command::CMD_USER_VOICE)
			{
				// user voice data
				if (intptr_t(end_ptr - p)  < VoiceRaw::data_size)
				{
					print_error("[ERROR] VOICE DATA is not contained in buffer.");
					ASSERT(0);
				}
				else
				{
					u16 voice_idx = u16(cmd.m_param);
					u16 voice_offset = u16(cmd.m_param) - base_address;
					
					// 未設定ならデータを取り込む
					if (!m_voice.count(voice_idx))
					{
						auto& voice = m_voice[voice_idx];
						const u8* voice_ptr = data_ptr + voice_offset;
						std::copy(voice_ptr, voice_ptr + VoiceRaw::data_size, voice.m_data.reg);
						voice.m_data.name = "0x" + hex(u16(cmd.m_param));
						voice.m_data.long_name = "(user) 0x" + voice.m_data.name;
					}
				}
			}

			// 終端
			if (cmd.m_cmd == OplDrvData::Command::CMD_NONE)
			{
				// error
				ASSERT(0);
				//clear();
				return false;
			}

			m_melody_ch[ch].push_back(cmd);

			if (cmd.m_cmd == OplDrvData::Command::CMD_END)
			{
				// end
				break;
			}
		}
	}

	if (trace_mode)
	{
		for (auto i = m_voice.begin(); i != m_voice.end(); ++i)
		{
			auto& voice = i->second;
			string s = "VOICE: 0x" + hex(i->first,4,"0") + " :";
			for (int i = 0; i < voice.m_data.data_size; ++i)
			{
				s += " " + hex(voice.m_data.reg[i], 2);
			}
			s += " : " + voice.m_data.long_name;
			print_log(s);
		}
	}

	return true;
}

//--------------------------------------------------
//! OplDrvData
//! ROM内蔵拡張音色定義テーブルを取得
//--------------------------------------------------
const OplDrvData::ExtraVoiceSet* OplDrvData::getExtraVoiceSet(int rom_type)
{
	const OplDrvData::ExtraVoiceSet* voice_table = nullptr;
	string table_name;
	switch (rom_type)
	{
	case 1:	voice_table = &fmpac_extention_voice;   break;
	case 2:	voice_table = &msxmusic_extention_voice; break;
	}

	if (!voice_table)
	{
		print_error("[ERROR] unknown voice romtype. " + dec(rom_type));
		ASSERT(0);
	}
	return voice_table;
}

//--------------------------------------------------
//! OplDrvData
//! ROM内蔵拡張音色定義MMLを作成(MGSDRV)
//--------------------------------------------------
string OplDrvData::make_ex_voice_mgs_mml(int mgs_voice_no, int rom_voice_no, int rom_type)
{
	const OplDrvData::ExtraVoiceSet* voice_table = getExtraVoiceSet(rom_type);
	if (!voice_table)
	{
		return "";
	}

	ASSERT((0 <= rom_voice_no) && (rom_voice_no < voice_table->voice_count));
	if ((0 <= rom_voice_no) && (rom_voice_no < voice_table->voice_count))
	{
		VoiceData voice;
		auto& src = voice_table->list[rom_voice_no];
		voice.m_data = src;
		voice.m_data.long_name =
			"(" + voice_table->name + " #" + dec(rom_voice_no) + ") " + voice.m_data.long_name;
		voice.voice_no = mgs_voice_no; // 固定
		return voice.make_mgs_mml();
	}

	return "";
}

//--------------------------------------------------
//! OplDrvData::Header
//! ROM内蔵拡張音色コマンドをユーザー音色に変換する
//--------------------------------------------------
bool OplDrvData::convert_voice_rom_to_user(int rom_type)
{
	const OplDrvData::ExtraVoiceSet* voice_table = getExtraVoiceSet(rom_type);
	if (!voice_table)
	{
		return false;
	}

	// メロディチャンネル
	for (int ch = 0; ch < m_header.getMelodyChCount(); ++ch)
	{
		auto& melody_ch = m_melody_ch[ch];

		for (auto i = melody_ch.begin(); i != melody_ch.end(); ++i)
		{
			if (i->m_cmd == OplDrvData::Command::CMD_ROM_VOICE)
			{
				// ROM内蔵拡張音色コマンドをユーザー音色に変換する

				// 内蔵音色データをユーザー音色リストへ登録
				u16 n = u16(i->m_param);
				ASSERT((0 <= n) && (n <= 63));
				if (!((0 <= n) && (n <= 63)))
				{
					print_error("[ERROR] out of range ROM_VOICE No. " + dec(n));
					ASSERT(0);
					return false;
				}
				u16 idx = 0xff80 + n;
				VoiceData& voice = m_voice[idx];	// 0xff80 to 0xffff
				auto& src = voice_table->list[n];
				voice.m_data = src;
				voice.m_data.long_name =
					"(" + voice_table->name + " #" + dec(n) + ") " + voice.m_data.long_name;

				// USER_VOICE コマンド へ 変更
				i->m_cmd = OplDrvData::Command::CMD_USER_VOICE;
				i->m_param = idx; // new voice index

				print("[INFO] melody ch.#" + dec(ch) + " : change ROM Voice " + dec(n) + " to USER VOICE.");
			}

			if (i->m_cmd == OplDrvData::Command::CMD_END)
			{
				// end
				break;
			}
		}
	}

	return true;
}

//--------------------------------------------------
//! OplDrvData::Header
//! 音量を増減する
//! @return オーバーフローしたコマンド数
//--------------------------------------------------
int OplDrvData::modify_volume(int volume_change)
{
	int overflow_count = 0;

	print("[INFO] volume modify " + dec(volume_change));
	// リズムチャンネル
	if (m_rhythm_ch.size())
	{
		int cmd_num = 0;
		for (auto i = m_rhythm_ch.begin();
			 i != m_rhythm_ch.end();
			++i,++cmd_num)
		{
			if (i->m_cmd == OplDrvData::Command::CMD_R_VOL)
			{
				int v = int(i->m_param);
				v += volume_change;
				if ((v < 0) || (15 < v))
				{
					print("[CAUTION] volume over flow."
						+ dec(i->m_param) + " -> " + dec(v)
					);
					v = (v < 0) ? 0 : 15;
					++overflow_count;
				}
				print("[INFO]"
					"Rhythm ch."
					" cmd[" + dec(cmd_num) + "]:"
					" change vol. "
					+ dec(i->m_param) + " -> " + dec(v)
				);
				i->m_param = v;
			}
		}
	}
	// メロディーチャンネル
	for (int ch = 0; ch < countof(m_melody_ch); ++ch)
	{
		if (m_melody_ch[ch].size())
		{
			int cmd_num = 0;
			for (auto i = m_melody_ch[ch].begin();
				 i != m_melody_ch[ch].end();
				++i,++cmd_num)
			{
				if (i->m_cmd == OplDrvData::Command::CMD_VOL)
				{
					int v = i->m_opt;
					v += volume_change;
					if ((v < 0) || (15 < v))
					{
						print("[CAUTION] volume over flow. "
							+ dec(i->m_opt) + " -> " + dec(v)
						);
						v = (v < 0) ? 0 : 15;
						++overflow_count;
					}
					print("[INFO]"
						" Melody ch.#" + dec(ch) +
						" cmd[" + dec(cmd_num) + "]:"
						" change vol. "
						+ dec(i->m_opt) + " -> " + dec(v)
					);
					i->m_opt = v;
				}
			}
		}
	}
	if (overflow_count)
	{
		print("[INFO] total volume overflow count " + dec(overflow_count));
	}
	return overflow_count;
}

//--------------------------------------------------
//! OplDrvData::Header
//! バイナリデータを作成する.
//! @param	outbuffer		このvector<u8>にバイナリデータが出力される.
//! @param	base_address	ユーザー音色データを使用する場合データの先頭アドレスが必要
//--------------------------------------------------
bool OplDrvData::make_binary(std::vector<u8>& outbuffer, u16 base_address)
{
	// ワークバッファ 256 bytes
	std::vector<u8>	temp(256);
	u8* temp_start = &temp[0];
	const u8* temp_end = temp_start + temp.size();

	// トラック番号
	int tr = 0;

	// トラック先頭オフセット
	u16 header_size = m_header.isRhythmMode() ? 
		OplDrvData::Header::mode_r :
		OplDrvData::Header::mode_m ;

	// 出力バッファ (ヘッダサイズ)+(reserve 64K Bytes)
	outbuffer.clear();
	outbuffer.reserve(0x10000);
	for (int i=0; i < header_size; ++i)
	{
		outbuffer.push_back(0);
	}

	// ユーザー音色使用位置リスト
	std::deque<u16> voice_adr_list;
	
	// リズムチャンネル
	if (m_header.isRhythmMode())
	{
		if (0 == m_rhythm_ch.size())
		{
			// なし
			m_header.offset[tr++] = 0;
		}
		else
		{
			u16 offset = u16(outbuffer.size());
			outbuffer[size_t(tr) * 2 + 0] = u8(offset & 0xff);
			outbuffer[size_t(tr) * 2 + 1] = u8(offset >> 8);
			m_header.offset[tr++] = offset;

			ASSERT(outbuffer.size() < 0x10000);

			for (auto i = m_rhythm_ch.begin(); i != m_rhythm_ch.end(); i++)
			{
				auto p = i->write_rhythm( temp_start, temp_end);
				
				if (!p)
				{
					// エラーがあった
					return false;
				}

				for (auto t = temp_start; t < p; ++t)
				{
					outbuffer.push_back(*t);
				}

				if (i->m_cmd == OplDrvData::Command::CMD_END)
				{
					// end
					break;
				}
			}
		}
	}

	// メロディチャンネル
	for (int ch = 0; ch < m_header.getMelodyChCount(); ++ch)
	{
		auto& melody_ch = m_melody_ch[ch];

		if (0 == melody_ch.size())
		{
			// なし
			m_header.offset[tr++] = 0;
		}
		else
		{
			u16 offset = u16(outbuffer.size());
			outbuffer[ size_t(tr) * 2 + 0] = u8(offset & 0xff);
			outbuffer[ size_t(tr) * 2 + 1] = u8(offset >> 8);
			m_header.offset[tr++] = offset;

			ASSERT(outbuffer.size() < 0x10000);

			for (auto i = melody_ch.begin(); i != melody_ch.end(); ++i)
			{
				auto p = i->write_melody(temp_start, temp_end);

				if (!p)
				{
					// エラーがあった
					return false;
				}

				for (auto t = temp_start; t < p; ++t)
				{
					outbuffer.push_back(*t);
				}

				if (i->m_cmd == OplDrvData::Command::CMD_USER_VOICE)
				{
					// ユーザー定義音色のアドレスを後から書き換える
					voice_adr_list.push_back( u16(outbuffer.size() - 2) ); // アドレスがあるオフセットの登録
					ASSERT(outbuffer.size() > 2 + size_t(m_header.offset[0]));	// 一応検査
				}

				if (i->m_cmd == OplDrvData::Command::CMD_END)
				{
					// end
					break;
				}
			}
		}
	}

	// ユーザー音色データ
	if (m_voice.size())
	{
		// 出力バイナリへ追加
		for (auto v = m_voice.begin(); v != m_voice.end(); ++v)
		{
			auto& voice = v->second;
			auto offset = outbuffer.size();
			for (int i = 0; i < voice.m_data.data_size; ++i)
			{
				outbuffer.push_back(voice.m_data.reg[i]);
			}
			ASSERT(offset < 0x10000);
			voice.offset = u16(offset);
		}
		// 使用箇所の音色データアドレス値を変更
		for (auto i = voice_adr_list.begin(); i != voice_adr_list.end(); ++i)
		{
			size_t pos = *i;
			u16 idx = u16(outbuffer[pos + 0]) + u16(outbuffer[pos + 1]) * 0x100;

			// 音色データ情報取得
			auto& voice = m_voice[idx];
			ASSERT(voice.offset);

			// 新しい値を書き込む
			auto new_addr = base_address + size_t(voice.offset);
			outbuffer[pos + 0] = u8(new_addr & 0xff);
			outbuffer[pos + 1] = u8(new_addr >> 8);
		}
	}

	return true;
}

//--------------------------------------------------
//! OplDrvData::Header
//! MML出力用のTEMPOセットアップ
//--------------------------------------------------
void OplDrvData::set_tempo(float tempo)
{
	// 音長 tickリスト
	add_note_length(1, tempo);
	add_note_length(2, tempo);
	add_note_length(3, tempo);
	add_note_length(4, tempo);
	add_note_length(6, tempo);
	add_note_length(8, tempo);
	add_note_length(12, tempo);
	add_note_length(16, tempo);
	add_note_length(24, tempo);
	add_note_length(32, tempo);
	add_note_length(48, tempo);
	add_note_length(64, tempo);
	add_note_length(96, tempo);

	print("[Note Length] tempo = " + dec(int(tempo)));
	for (auto i = m_note_length.begin(); i != m_note_length.end(); ++i)
	{
		print("[Note Length] L" + dec(i->first) + " = " + float_str(i->second));
	}
}

//--------------------------------------------------
//! OplDrvData::Header
//! MML出力用：音長リスト追加
//--------------------------------------------------
void OplDrvData::add_note_length(int n, float tempo)
{
	m_note_length[n] = tempo2tick(tempo, n);
}

//--------------------------------------------------
//! OplDrvData::Header
//! MML出力用：音長比較
//! @return 0=一致 -1=tickが小さい +1=tickが大きい
//--------------------------------------------------
int OplDrvData::compare_note_length(float tick, int n)
{
	auto diff = tick - m_note_length[n];
	if (abs(diff) <= FLT_EPSILON)
	{
		return 0;	// equal
	}

	// データ側が整数なので切り捨てと切り上げも検査
	auto ft = floor(tick);
	auto fn = floor(m_note_length[n]); // 切り捨て
	auto cn = ceil(m_note_length[n]); // 切り上げ
	if ((ft==fn) || (ft==cn))
	{
		return 0;	// equal
	}

	if (diff < 0.f)
	{
		return -1;	// tick < note_length[n]
	}
	return 1;	// tick > note_length[n]
}

//--------------------------------------------------
//! OplDrvData::Header
//! MML出力用：音長リスト追加
//--------------------------------------------------
int OplDrvData::get_note_length(float tick, float& note_tick)
{
	note_tick = tick;

	// 一致を優先
	for (auto i = m_note_length.begin(); i != m_note_length.end(); ++i)
	{
		if (0 == compare_note_length(tick, i->first))
		{
			return i->first;
		}
	}
	// 端数のある場合
	for (auto i = m_note_length.begin(); i != m_note_length.end(); ++i)
	{
		if (i->second <= tick)
		{
			if (i->first == 2) // L2の時
			{
				if (0 == compare_note_length(tick - m_note_length[3], 3))
				{
					note_tick = m_note_length[3];
					return 3; // 3+3なら3をまず返す
				}
			}
			if (0 == (i->first % 3)) // L3の倍数の時
			{
				auto n = i->first * 2;
				if (0 == compare_note_length(tick - m_note_length[n], i->first))
				{
					note_tick = i->second;
					return i->first;
				}
				continue; // 3の倍数の組み合わせでなければスキップ
			}
			note_tick = i->second;
			return i->first;
		}
	}
	return 0;
}


class mml_buffer
{
public:
	std::stringstream mml;		// 出力先
	std::stringstream buff;		// 一時出力先
	size_t line_size;			// 行の長さ
	size_t line_limit;			// 1行の長さ
	float sum_tick;				// 発音長合計
	float measure_tick;			// 1小節
	int measure_count;			// 小節数
	bool measure_1st;			// 小節の最初かどうか
	int line_measure_count;		// この小節ごとに改行
	string line_head;			// 行の先頭
public:
	mml_buffer()
		: line_size(0)
		, line_limit(80)
		, sum_tick(0.f)
		, measure_tick(0.f)
		, measure_count(0)
		, measure_1st(true)
		, line_measure_count(0)
		, line_head("")
	{}
	void init( int _line_limit, float _measure_tick, int _line_measure_count)
	{
		mml.str("");
		mml.clear(0);
		buff.str("");
		buff.clear(0);
		line_size = 0;
		line_limit = _line_limit;
		sum_tick = 0.f;
		measure_tick = _measure_tick;
		measure_count = 0;
		measure_1st = true;
		line_measure_count = _line_measure_count;
		line_head = "";
	}

	enum FlushType
	{
		flush_nomal = 0,
		flush_line = 1,
		flush_ch = 2,
	};
	void flush(FlushType flush_type = flush_nomal)
	{
		size_t s = buff.tellp();
		if (s)
		{
			mml << buff.str();
			buff.str("");
		}
		buff.clear();
		if (flush_type != flush_nomal)
		{
			string cr = "\n";
			const string &ss = mml.str();
			if (ss.substr(ss.size() - cr.size()) != cr)
			{
				mml << std::endl;
			}
			measure_count = 0;
			measure_1st = true;
			line_size = 0;
		}
		if (flush_type == flush_ch)
		{
			sum_tick = 0.f;
		}
	}
	void add(const string s)
	{
		if (0 == line_size)
		{
			buff << line_head;
			line_size += line_head.size();
		}
		buff << s;
		line_size += s.size();
		measure_1st = false;
	}
	void add_cmd(const string s, float tick = 0.f, bool no_cr = false)
	{
		sum_tick += tick;

		size_t next_line_size = line_size + s.size();
		if (0 == line_size)
		{
			next_line_size += line_head.size(); // ラインヘッダを考慮
		}
		if (1 < measure_count)
		{
			next_line_size += 1; // 小節の間のスペース分
		}

		if (line_limit <= next_line_size)
		{
			MML_TRACE("1行の文字数指定をオーバー\n");
			MML_TRACE(buff.str().c_str()); MML_TRACE("\n");
			if (0 < measure_count)
			{
				MML_TRACE("2小節目以降は小節間に改行を挿入\n");
				mml << std::endl;
				line_size = size_t(buff.tellp());
				line_size += line_head.size();
				if (line_size)
				{
					MML_TRACE("小節の一文字目ではないのでラインヘッダも挿入\n");
					mml << line_head;
					measure_1st = false;
				}
				else
				{
					MML_TRACE("小節の先一文字目なのでフラグを立てる（この後のaddでline_headは追加される）\n");
					measure_1st = true;
				}
				measure_count = 0;
			}
			else
			if (!no_cr)
			{
				MML_TRACE("1小節目は途中改行してから追加\n");
				if (1 < measure_count)
				{
					MML_TRACE("空白を追加\n");
					mml << " ";
					line_size += 1;
				}
				flush(flush_line);
			}
		}
		add(s);

		// 1小節
		if ((0.f < measure_tick) && (0.f < tick)
			&& (measure_tick <= sum_tick))
		{
			sum_tick -= measure_tick;
			++measure_count;

			measure_1st = true; // 次のコマンドが小節の頭

			MML_TRACE("1小節の区切り\n");
			MML_TRACE(buff.str().c_str()); MML_TRACE("\n");

			if (line_measure_count <= measure_count)
			{
				MML_TRACE("規定小節数を超えたので追加して改行\n");
				if (1 < measure_count)
				{
					MML_TRACE("小節間に空白を追加\n");
					mml << " ";
					line_size += 1;
				}
				flush(flush_line);
			}
			else
			{
				if (1 < measure_count)
				{
					//if ((line_size + 1) < line_limit)
					//{
						MML_TRACE("小節間に空白を追加\n");
						mml << " ";
						line_size += 1;
					//}
					//else
					//{ // → 事前に桁あふれ処理済みなので不要
					//	MML_TRACE("制限文字数を超えるので改行を挿入\n");
					//	mml << std::endl;
					//	mml << line_head;
					//	line_size = size_t(buff.tellp());
					//	line_size += line_head.size();
					//	measure_count = 1;
					//}
				}
				flush();
			}
		}
	}
};

//--------------------------------------------------
//! OplDrvData::Header
//! 最も長いチャンネルの演奏時間を取得する (tick)
//--------------------------------------------------
double OplDrvData::calc_max_ch_time()
{
	double max_tick = 0.;
	if (m_header.isRhythmMode())
	{
		double tick = 0.;
		for (auto i = m_rhythm_ch.begin(); i != m_rhythm_ch.end(); ++i)
		{
			if (i->m_cmd == Command::CMD_R_NOTE)
			{
				tick += i->m_param;
			}
		}
		max_tick = std::max(max_tick, tick);
	}
	for (int ch = 0; ch < m_header.getMelodyChCount(); ++ch)
	{
		auto melody_ch = m_melody_ch[ch];
		double tick = 0.;
		for (auto i = melody_ch.begin(); i != melody_ch.end(); ++i)
		{
			if (i->m_cmd == Command::CMD_NOTE)
			{
				tick += i->m_param;
			}
		}
		max_tick = std::max(max_tick,tick);
	}
	return max_tick;
}

//--------------------------------------------------
//! OplDrvData::Header
//! MMLを作成する.
//! @param	outbuffer		バイナリデータ出力を受け取る
//! @param	tempo			テンポを指定
//! @param	mml_loop		MMLにループ指定
//! @param	mml_rel_volume	相対音量で出力
//! @param	def_len			省略時音長 L?
//! @param	title			タイトル
//! @param	time_signiture_d8	8分の何拍子か指定
//--------------------------------------------------
bool OplDrvData::make_mgs_mml(
		std::string& outbuffer,
		float tempo,
		bool mml_loop,
		bool mml_rel_volume,
		int def_len,
		string title,
		int time_signiture_d8
)
{
	const int default_volume = 12;		// OPLDRVボリューム初期値

	set_tempo(tempo);

	mml_buffer buffer;					// 出力バッファ

	float signiture_time = m_note_length[1];
	if (time_signiture_d8 != 8)
	{
		// n/8拍子
		signiture_time = m_note_length[8] * time_signiture_d8;
	}

	// 最大桁80、または ?/4小節
	buffer.init( 80, signiture_time, 4);

	int def_note_length = 0;			// 省略時音長

	// 使用チャンネルリスト文字列
	string all_ch = "";
	if (m_rhythm_ch.size())
	{
		all_ch += "F";
	}
	for (int i = 0; i < m_header.getMelodyChCount(); ++i)
	{
		if (m_melody_ch[i].size())
		{
			all_ch += string("9ABCDEFGH").at(i);
		}
	}

	// MSXPLAY header
	buffer.mml
		<< ";[gain=1.0 name=" << title << " duration=300s fade=5s cpu=0 lpf=1]"	<< std::endl 
		<< "; The line above defines extra options, works only on msxplay.com"	<< std::endl 
		<< "; name    : Name of mml, use as the base download filename."		<< std::endl
		<< "; gain    : Volume gain. (default: 1.0)"							<< std::endl
		<< "; duration: Length of the song. (default: 300s)"					<< std::endl
		<< "; fade    : Time of fading out. (default: 5s)"						<< std::endl
		<< "; cpu     : CPU speed ratio. 0:auto, 1:3.58MHz (default: 0)"		<< std::endl
		<< "; lpf     : Low-pass filter. 0:off, 1:on (default: 0)"				<< std::endl;

	// MGSDRV header
	buffer.mml
		<< "#opll_mode " << (m_header.isRhythmMode() ? "1" : "0")	<< std::endl
		<< "#tempo " << std::dec << int(tempo)						<< std::endl
		<< "#title { \"" << title << "\" }"							<< std::endl
		<< "#alloc { ";
	for (auto i = all_ch.begin(); i != all_ch.end(); ++i)
	{
		if (i != all_ch.begin())
		{
			buffer.mml << ",";
		}
		buffer.mml << *i << "=1400";
	}
	buffer.mml
		<< " }"  << std::endl
		<< std::endl;

	// ユーザー音色
	/*
	@v15 = { ; E - Guiter
	;       TL FB
			 7, 3,
	; AR DR SL RR KL MT AM VB EG KR DT
	  15, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0,
	  15, 7, 0, 7, 0, 8, 0, 0, 1, 0, 1 }
	 */
	u8 cur_user_voice = 16;	// ユーザー音色番号
	for (auto i = m_voice.begin(); i != m_voice.end(); ++i)
	{
		auto& voice = i->second;
		voice.voice_no = cur_user_voice++;

		buffer.mml << voice.make_mgs_mml();
		buffer.mml << std::endl;
	}

	// 最大演奏時間
	double max_tick = calc_max_ch_time();
	print("[INFO] max ch. time : " + double_str(max_tick));

	// ループ
	if (mml_loop && all_ch.size())
	{
		buffer.mml << all_ch << " [0" << std::endl << std::endl;
	}

	// リズムチャンネル
	if (m_rhythm_ch.size() && m_header.isRhythmMode())
	{
		buffer.mml << ";--- Rhythm ---" << std::endl;
		buffer.line_head = "F ";

		double total_tick = 0.;

		// default note length L?
		if (def_len)
		{
			buffer.add_cmd("L" + dec(def_len));
		}

		// 初回はボリューム初期値指定
		buffer.add_cmd("V" + dec(default_volume));
		int volume[Command::RHYTHM_INST_NUM];
		std::fill(volume, volume + Command::RHYTHM_INST_NUM, -1);

		for (auto i = m_rhythm_ch.begin(); i != m_rhythm_ch.end(); ++i)
		{
			switch (i->m_cmd)
			{
			case Command::CMD_R_NOTE:
			{
				float tick = float(i->m_param);
				total_tick += tick;
				float note_tick = tick;
				int n = get_note_length(tick, note_tick);
				if (!n) break;
				tick -= note_tick;

				if (def_len && (n== def_len))
				{
					// 音長省略
					buffer.add_cmd(Command::getRhythmName(i->m_opt) + ":", note_tick);
				}
				else
				{
					buffer.add_cmd(	Command::getRhythmName(i->m_opt) + dec(n), note_tick);
				}

				while (0.f < tick)
				{
					auto old_n = n;
					note_tick = tick;
					n = get_note_length(tick, note_tick);
					if (!n) break;
					tick -= note_tick;

					if (!buffer.measure_1st && (old_n > 1) && (n == old_n * 2))
					{
						buffer.add_cmd(".", note_tick, true);
					}
					else
					{
						// [暫定] リズム音源は&がないので休符で残りを指定
						if (def_len && (n == def_len))
						{
							// 音長省略
							buffer.add_cmd("R:", note_tick);
						}
						else
						{
							buffer.add_cmd("R" + dec(n), note_tick);
						}
					}
				}
				break;
			}
			case Command::CMD_R_VOL:
			{
				if (i->m_opt)
				{
					u8 mask = u8(Command::BIT_BASS_DRUM);
					u8 n = countof(volume) -1;
					while (mask)
					{
						if (i->m_opt & mask)
						{
							int v = 15 - u8(i->m_param);
							if (mml_rel_volume && (0 <= volume[n]))
							{
								buffer.add_cmd(
									"V" + Command::getRhythmName(i->m_opt & mask)
									+ (v > volume[n] ? "+" : "-") + dec(abs(v - volume[n]))
								);
							}
							else
							{
								buffer.add_cmd(
									"V" + Command::getRhythmName(i->m_opt & mask)
									+ dec(v)
									);
							}
							volume[n] = v;
						}
						mask >>= 1;
						n--;
					}
				}
				else
				{
					buffer.add_cmd("V" + dec(15 - i->m_param));
				}
				break;
			}
			case Command::CMD_END:
			{
				break;
			}
			default:
			{
				ASSERT(0);
				break;
			}
			}
		}
		buffer.flush(buffer.flush_line);
		print("[INFO] Rhythm ch. time : " + double_str(total_tick));
		if (total_tick < max_tick)
		{
			buffer.mml << "; * time adjustment *" << std::endl;
			auto diff = max_tick - total_tick;
			while (0. < diff)
			{
				float tick = diff < FLT_MAX ? float(diff) : FLT_MAX;
				float note_tick = tick;
				int n = get_note_length(tick, note_tick);
				diff -= note_tick;
				buffer.add_cmd("R" + dec(n));
			}
		}
		buffer.flush(buffer.flush_ch);
		buffer.mml << std::endl;
	}

	// メロディーチャンネル
	for (int ch = 0; ch < m_header.getChannelCount(); ++ch)
	{
		auto& melody_ch = m_melody_ch[ch];

		if (melody_ch.size())
		{
			buffer.mml << ";--- Melody #" << std::dec << ch << " ---" << std::endl;
			buffer.line_head = string("9ABCDEFGH").at(ch) + string(" ");

			bool legato = false;

			int octave = -1;				// 現在のオクターブ
			int volume = -1;				// 現在のボリューム
			int user_voice = 15;			// 現在のユーザー音色(15は未定義)
			bool req_user_voice = false;	// ユーザー音色コマンドが必要

			double total_tick = 0.;

			// default note length L?
			if (def_len)
			{
				buffer.add_cmd("l" + dec(def_len));
			}

			for (auto i = melody_ch.begin(); i != melody_ch.end(); ++i)
			{
				switch (i->m_cmd) 
				{
				case Command::CMD_NOTE:
				{
					float tick = float(i->m_param);
					total_tick += tick;
					float note_tick = tick;
					int n = get_note_length(tick, note_tick);
					if (!n) break;
					tick -= note_tick;

					// ボリューム未設定
					if (volume < 0)
					{
						volume = default_volume;
						buffer.add_cmd("v" + dec(volume));
					}

					// ユーザー音色未設定
					if (req_user_voice)
					{
						buffer.add_cmd("@" + dec(user_voice));
						req_user_voice = false;
					}

					// オクターブ
					if (i->m_opt)
					{
						int o = Command::getOctave(i->m_opt);
						if (octave < 0)
						{
							octave = o;
							buffer.add_cmd("o" + dec(o));
						}
						else
						{
							while (o < octave)
							{
								buffer.add_cmd("<");
								--octave;
							}
							while (o > octave)
							{
								buffer.add_cmd(">");
								++octave;
							}
						}
					}

					float note_total = note_tick;

					if (legato && i->m_opt) // 休符はの時はスラー不要
					{
						// レガートON
						buffer.add_cmd("&");
					}
					if (def_len && (n == def_len))
					{
						// 音長省略
						buffer.add_cmd(
							get_lower(Command::getNoteName(i->m_opt))
							, note_tick);
					}
					else
					{
						buffer.add_cmd(
							get_lower(Command::getNoteName(i->m_opt))
							+ dec(n), note_tick);
					}

					while (0.f < tick)
					{
						int old_n = n;
						note_tick = tick;
						n = get_note_length(tick, note_tick);
						if (!n) break;
						tick -= note_tick;
						note_total += note_tick;

						if (!buffer.measure_1st && (old_n > 1) && (n == old_n * 2))
						{
							// 半分なら.
							buffer.add_cmd(".", note_tick, true);
						}
						else
						{
							if (!buffer.measure_1st && (note_total <= m_note_length[1]))
							{
								// 全音符以内なら^で音長だけ繋げる
								buffer.add_cmd("^" + dec(n), note_tick, true);
								ASSERT(n > 1);
							}
							else
							{
								// スラーで繋げる
								note_total = note_tick;
								if (i->m_opt) // 休符はの時はスラー不要
								{
									buffer.add_cmd("&");
								}
								if (def_len && (n == def_len))
								{
									// 音長省略
									buffer.add_cmd(
										get_lower(Command::getNoteName(i->m_opt))
										, note_tick);
								}
								else
								{
									buffer.add_cmd(
										get_lower(Command::getNoteName(i->m_opt))
										+ dec(n), note_tick);
								}
							}
						}
					}
					break;
				}
				case Command::CMD_VOL:
				{
					auto v = int(15 - i->m_opt);
					auto adv = abs(v - volume);
					if (mml_rel_volume && (-1 < volume))
					{
						if (adv < 3)
						{
							while (v < volume)
							{
								buffer.add_cmd("(");
								--volume;
							}
							while (v > volume)
							{
								buffer.add_cmd(")");
								++volume;
							}
						}
						else
						{
							if (v < volume)
							{
								buffer.add("v-" + dec(adv));
							}
							else
							{
								buffer.add("v+" + dec(adv));
							}
						}
					}
					else
					{
						buffer.add_cmd("v" + dec(v));
					}
					volume = v;
					break;
				}
				case Command::CMD_VOICE:
				{
					//	音色番号    ROM音色番号    音色名
					//		0        1	   バイオリン
					//		1        2	   ギター
					//		2		 3	   ピアノ
					//		3		 4	   フルート
					//		4		 5	   クラリネット
					//		5		 6	   オーボエ
					//		6		 7	   トランペット
					//		7		 8	   オルガン
					//		8		 9	   ホルン
					//		9		10	   シンセ
					//		10		11	   ハープシコード
					//		11		12	   ビブラフォン
					//		12		13	   シンセベース
					//		13		14	   ウッドベース
					//		14		15	   エレキベース
					//		15		 0
					//		: : オリジナル音色
					//		31		 0
					int voice = int(i->m_opt - 1);
					if (voice < 0)
					{
						req_user_voice = true;	// ユーザー音色指定予約
					}
					else
					{
						buffer.add_cmd("@" + dec(voice));
					}
					break;
				}
				case Command::CMD_SUSTAIN:
				{
					buffer.add_cmd(string("s") + (i->m_opt ? " o" : " f"));
					break;
				}
				case Command::CMD_ROM_VOICE:
				{
					buffer.add_cmd(";@x" + hex(i->m_param) + "\n");
					buffer.flush(buffer.flush_line);
					print_error("[ERROR] CMD_ROM_VOICE not support at MGSDRV.");
					ASSERT(0);
					break;
				}
				case Command::CMD_USER_VOICE:
				{
					auto voice = m_voice[u16(i->m_param)];
					buffer.add_cmd("@"  + dec(voice.voice_no));
					if (!voice.voice_no)
					{
						print_error("[ERROR] USER_VOICE 0x" + hex(i->m_param,4,"0") + "not asigned at MGSDRV.");
						ASSERT(voice.voice_no);
					}
					user_voice = voice.voice_no;
					req_user_voice = false;	// ユーザー音色指定予約解除
					break;
				}
				case Command::CMD_LEGATO:
				{
					legato = (i->m_opt ? true : false);
					break;
				}
				case Command::CMD_QUANTIZE:
				{
					buffer.add_cmd("q" + dec(i->m_param));
					break;
				}
				case Command::CMD_END:
				{
					if (i == melody_ch.begin())
					{
						// MGSDRVはチャンネルに発音か休符がないとバグる
						auto n = def_len ? def_len : 16;
						buffer.add_cmd("R" + dec(n),m_note_length[n]);
						total_tick += m_note_length[n];
					}
					break;
				}
				default:
				{
					ASSERT(0);
					break;
				}
				}
			}
			buffer.flush(buffer.flush_line);
			print("[INFO] Melody ch.#" + dec(ch) + " time : " + double_str(total_tick));
			if (total_tick < max_tick)
			{
				buffer.mml << "; * time adjustment *" << std::endl;
				auto diff = max_tick - total_tick;
				while (0. < diff)
				{
					float tick = diff < FLT_MAX ? float(diff) : FLT_MAX;
					float note_tick = tick;
					int n = get_note_length(tick, note_tick);
					diff -= note_tick;
					if (def_len == n)
					{
						buffer.add_cmd("r");
					}
					else
					{
						buffer.add_cmd("r" + dec(n));
					}
				}
			}
			buffer.flush(buffer.flush_ch);
			buffer.mml << std::endl;
		}
	}

	// ループ
	if (mml_loop && all_ch.size())
	{
		buffer.mml << all_ch << " ]" << std::endl;
	}

	outbuffer = buffer.mml.str();
	return true;
}
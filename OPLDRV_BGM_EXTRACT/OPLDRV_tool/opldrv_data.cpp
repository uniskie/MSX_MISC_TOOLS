#include "uni_common.h"
#include "opldrv_data.h"
#include <deque>


using namespace OPLDRV;

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
//! 音階名取得
//--------------------------------------------------
string OplDrvData::Command::getOctaveName(int param)
{
	return string("O") + decimal(param / 12);
}

//--------------------------------------------------
//! OplDrvData::Command
//! 音階名取得
//--------------------------------------------------
string OplDrvData::Command::getNoteName(int n)
{
	const string note[12] = {
		"C","C+","D","D+","E","F","F+","G","G+","A","A+","B",
	};
	return note[n % 12];
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
			print_error(string("[CAUTION] time value over than ") + decimal(time_max));
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
			print_error(string("[ERROR] unknown melody command. 0x") + hex(c));
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
			print_error(string("[ERROR] unknown rhythm command. 0x") + hex(c));
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
			*p++ += u8(m_param >> 8);
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
			print_error(string("[ERROR] unknown melody command. 0x") + hex(m_cmd));
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
			print_error(string("[ERROR] unknown rhythm command. 0x") + hex(m_cmd));
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
				auto n = m_opt - 1;
				s += " " + getOctaveName(n)
					+ " " + align_left(getNoteName(n), 2);
			}
			else
			{
				s += " -- R ";
			}
			s += " TIME=" + decimal(m_param);
			break;
		}
		case CMD_VOL:
		{
			s += " " + decimal(m_opt);
			break;
		}
		case CMD_VOICE:
		{
			s += " " + decimal(m_opt);
			break;
		}
		case CMD_SUSTAIN:
		{
			s += m_opt ? " ON" : " OFF";
			break;
		}
		case CMD_ROM_VOICE:
		{
			s += " " + decimal(m_param);
			break;
		}
		case CMD_USER_VOICE:
		{
			s += " 0x" + hex(m_param);
			break;
		}
		case CMD_LEGATO:
		{
			s += m_opt ? " ON" : " OFF";
			break;
		}
		case CMD_QUANTIZE:
		{
			s += " " + decimal(m_param);
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
				+ " TIME=" + decimal(m_param);
			break;
		}
		case CMD_R_VOL:
		{
			s += " " + align_left(getRhythmName(m_opt), 5)
				+ " " + decimal(m_param);
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
			print_log("[CH. MELODY #" + decimal(ch) + "]");
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
				if (intptr_t(end_ptr - p)  < VoiceData::data_size)
				{
					print_error("[ERROR] VOICE DATA is not contained in buffer.");
					ASSERT(0);
				}
				else
				{
					u16 voice_idx = u16(cmd.m_param);
					u16 voice_offset = u16(cmd.m_param) - base_address;

					auto& voice = m_voice[voice_idx];
					const u8* voice_ptr = data_ptr + voice_offset;
					std::copy(voice_ptr, voice_ptr + VoiceData::data_size, voice.m_data);
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
		auto i = m_voice.begin();
		auto e = m_voice.end();
		for (; i != e; ++i)
		{
			auto& voice = i->second;
			string s = "VOICE: 0x" + hex(i->first) + " :";
			for (int i = 0; i < voice.data_size; ++i)
			{
				s += " " + hex(voice.m_data[i]);
			}
			print_log(s);
		}
	}

	return true;
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
					voice_adr_list.push_back( u16(outbuffer.size() - 2) );
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
		for (auto i = m_voice.begin(); i != m_voice.end(); ++i)
		{
			auto& voice = i->second;
			auto offset = outbuffer.size();
			for (int i = 0; i < voice.data_size; ++i)
			{
				outbuffer.push_back(voice.m_data[i]);
			}
			ASSERT(offset < 0x10000);
			voice.offset = u16(offset);
		}
		// 使用箇所の音色データアドレス値を変更
		for (auto i = voice_adr_list.begin(); i != voice_adr_list.end();)
		{
			size_t pos = *i;
			i++;
			i++;
			u16 idx = u16(outbuffer[pos + 0]) + u16(outbuffer[pos + 1]) * 0x100;

			// 音色データ情報取得
			auto& voice = m_voice[idx];
			ASSERT(voice.offset);

			// 新しい値を書き込む
			auto new_offset = base_address + size_t(voice.offset);
			outbuffer[pos + 0] = u8(new_offset & 0xff);
			outbuffer[pos + 1] = u8(new_offset >> 8);
		}
	}

	return true;
}

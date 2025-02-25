#include "uni_common.h"
#include "opldrv_data.h"
#include <deque>


using namespace OPLDRV;
using namespace uni_common;

#include"opldrv_inst_data.h"	// FMPAC�� �g�����F
#include"opldrv_inst_data2.h"	// A1GT�� �g�����F

//==================================================
//
// class OplDrvData::VoiceData
// 
//==================================================

//--------------------------------------------------
//! OplDrvData::VoiceData
//! ���F��`MML��Ԃ��iMGSDRV�j
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
//! �R���X�g���N�^
//--------------------------------------------------
OplDrvData::Header::Header()
{
	clear();
}

//--------------------------------------------------
//! OplDrvData::Header
//! �R���X�g���N�^
//--------------------------------------------------
OplDrvData::Header::Header(const u8* data_ptr, const u8* end_ptr)
{
	clear();
	from_binary(data_ptr, end_ptr);
}

//--------------------------------------------------
//! OplDrvData::Header
//! ���Y�����[�h���ǂ����Ԃ�
//--------------------------------------------------
bool OplDrvData::Header::isRhythmMode() const
{
	return (offset[0] == mode_r);
}

//--------------------------------------------------
//! OplDrvData::Header
//! �����f�B�`�����l���̃f�[�^�I�t�Z�b�g��Ԃ�
//! �͈͊O�Ȃ�0
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
//! ���Y���`�����l���̃f�[�^�I�t�Z�b�g��Ԃ�
//--------------------------------------------------
//! ���Y�����[�h�łȂ����0
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
//! �f�[�^���N���A����
//--------------------------------------------------
void OplDrvData::Header::clear()
{
	std::fill(offset, offset + countof(offset), 0);
}

//--------------------------------------------------
//! OplDrvData::Header
//! �f�[�^���Z�b�g����
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
//! �R�}���h���擾
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
//! �I�N�^�[�u���擾
//--------------------------------------------------
string OplDrvData::Command::getOctaveName(int param)
{
	return string("O") + dec(getOctave(param));
}
//--------------------------------------------------
//! OplDrvData::Command
//! �I�N�^�[�u�擾
//--------------------------------------------------
int OplDrvData::Command::getOctave(int param)
{
	return int((param-1) / 12) + 1;
}

//--------------------------------------------------
//! OplDrvData::Command
//! ���K���擾
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
//! ���Y���y�햼�擾
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
//! �N���A
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
//! ���Ԏw���ǂݍ���
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
			return p;	// ����I��
		}
	}
	print_error(string("[ERROR] not enough read buffer in read_time."));
	ASSERT(0);
	return p;
}

//--------------------------------------------------
//! OplDrvData::Command
//! �����f�B�[�f�[�^��ǂݍ���
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
//! ���Y���f�[�^��ǂݍ���
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
//! ���Ԏw�����������
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
//! �����f�B�[�f�[�^����������
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
//! ���Y���f�[�^����������
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
//! �R�}���h��񕶎�����擾
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
//! �R���X�g���N�^
//--------------------------------------------------
OplDrvData::OplDrvData()
{
	clear();
}

//--------------------------------------------------
//! OplDrvData
//! �R���X�g���N�^
//--------------------------------------------------
OplDrvData::OplDrvData(const u8* data_ptr, const u8* end_ptr, u16 base_address, u16 music_address)
{
	clear();
	from_binary(data_ptr, end_ptr, base_address, music_address);
}

//--------------------------------------------------
//! OplDrvData
//! �f�[�^���N���A����
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
//! �o�C�i���f�[�^����f�[�^���쐬����
//--------------------------------------------------
bool OplDrvData::from_binary(const u8* data_ptr, const u8* end_ptr, u16 base_address, u16 music_address)
{
	auto music_ptr = data_ptr + (music_address - base_address);

	// header
	m_header.from_binary(music_ptr, end_ptr);

	// ���Y���`�����l��
	if (m_header.isRhythmMode())
	{
		auto offset = m_header.get_rhythm_binary_offset();
		auto p = music_ptr + offset;
		m_rhythm_ch.reserve(0x1000); // �K���ɗ\��

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

			// �I�[
			if (cmd.m_cmd == OplDrvData::Command::CMD_END)
			{
				// end
				break;
			}
		}
	}
	
	// �����f�B�`�����l��
	for (int ch = 0; ch < m_header.getMelodyChCount(); ++ch)
	{
		auto offset = m_header.get_melody_binary_offset(ch);
		auto p = music_ptr + offset;

		m_melody_ch[ch].reserve(0x1000); // �K���ɗ\��

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

			// ���[�U�[��`���F
			if (cmd.m_cmd == OplDrvData::Command::CMD_USER_VOICE)
			{
				// user voice data
				{
					u16 voice_idx = u16(cmd.m_param);
					u16 voice_offset = u16(cmd.m_param) - base_address;
					
					// ���ݒ�Ȃ�f�[�^����荞��
					if (!m_voice.count(voice_idx))
					{
						auto voice_ptr = data_ptr + voice_offset;
						if (intptr_t(end_ptr - voice_ptr)  < VoiceRaw::data_size)
						{
							print_error("[ERROR] VOICE DATA is not contained in buffer.");
							ASSERT(0);
						}
						else
						{
							auto& voice = m_voice[voice_idx];
							std::copy(voice_ptr, voice_ptr + VoiceRaw::data_size, voice.m_data.reg);
							voice.m_data.name = "0x" + hex(u16(cmd.m_param));
							voice.m_data.long_name = "(user) 0x" + voice.m_data.name;
						}
					}
				}
			}

			// �I�[
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
//! ROM�����g�����F��`�e�[�u�����擾
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
//! ROM�����g�����F��`MML���쐬(MGSDRV)
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
		voice.voice_no = mgs_voice_no; // �Œ�
		return voice.make_mgs_mml();
	}

	return "";
}

//--------------------------------------------------
//! OplDrvData::Header
//! ROM�����g�����F�R�}���h�����[�U�[���F�ɕϊ�����
//--------------------------------------------------
bool OplDrvData::convert_voice_rom_to_user(int rom_type)
{
	const OplDrvData::ExtraVoiceSet* voice_table = getExtraVoiceSet(rom_type);
	if (!voice_table)
	{
		return false;
	}

	// �����f�B�`�����l��
	for (int ch = 0; ch < m_header.getMelodyChCount(); ++ch)
	{
		auto& melody_ch = m_melody_ch[ch];

		for (auto i = melody_ch.begin(); i != melody_ch.end(); ++i)
		{
			if (i->m_cmd == OplDrvData::Command::CMD_ROM_VOICE)
			{
				// ROM�����g�����F�R�}���h�����[�U�[���F�ɕϊ�����

				// �������F�f�[�^�����[�U�[���F���X�g�֓o�^
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

				// USER_VOICE �R�}���h �� �ύX
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
//! ���ʂ𑝌�����
//! @return �I�[�o�[�t���[�����R�}���h��
//--------------------------------------------------
int OplDrvData::modify_volume(int volume_change)
{
	int overflow_count = 0;

	print("[INFO] volume modify " + dec(volume_change));
	// ���Y���`�����l��
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
	// �����f�B�[�`�����l��
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
//! �o�C�i���f�[�^���쐬����.
//! @param	outbuffer		����vector<u8>�Ƀo�C�i���f�[�^���o�͂����.
//! @param	base_address	���[�U�[���F�f�[�^���g�p����ꍇ�f�[�^�̐擪�A�h���X���K�v
//--------------------------------------------------
bool OplDrvData::make_binary(std::vector<u8>& outbuffer, u16 base_address)
{
	// ���[�N�o�b�t�@ 256 bytes
	std::vector<u8>	temp(256);
	u8* temp_start = &temp[0];
	const u8* temp_end = temp_start + temp.size();

	// �g���b�N�ԍ�
	int tr = 0;

	// �g���b�N�擪�I�t�Z�b�g
	u16 header_size = m_header.isRhythmMode() ? 
		OplDrvData::Header::mode_r :
		OplDrvData::Header::mode_m ;

	// �o�̓o�b�t�@ (�w�b�_�T�C�Y)+(reserve 64K Bytes)
	outbuffer.clear();
	outbuffer.reserve(0x10000);
	for (int i=0; i < header_size; ++i)
	{
		outbuffer.push_back(0);
	}

	// ���[�U�[���F�g�p�ʒu���X�g
	std::deque<u16> voice_adr_list;
	
	// ���Y���`�����l��
	if (m_header.isRhythmMode())
	{
		if (0 == m_rhythm_ch.size())
		{
			// �Ȃ�
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
					// �G���[��������
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

	// �����f�B�`�����l��
	for (int ch = 0; ch < m_header.getMelodyChCount(); ++ch)
	{
		auto& melody_ch = m_melody_ch[ch];

		if (0 == melody_ch.size())
		{
			// �Ȃ�
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
					// �G���[��������
					return false;
				}

				for (auto t = temp_start; t < p; ++t)
				{
					outbuffer.push_back(*t);
				}

				if (i->m_cmd == OplDrvData::Command::CMD_USER_VOICE)
				{
					// ���[�U�[��`���F�̃A�h���X���ォ�珑��������
					voice_adr_list.push_back( u16(outbuffer.size() - 2) ); // �A�h���X������I�t�Z�b�g�̓o�^
					ASSERT(outbuffer.size() > 2 + size_t(m_header.offset[0]));	// �ꉞ����
				}

				if (i->m_cmd == OplDrvData::Command::CMD_END)
				{
					// end
					break;
				}
			}
		}
	}

	// ���[�U�[���F�f�[�^
	if (m_voice.size())
	{
		// �o�̓o�C�i���֒ǉ�
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
		// �g�p�ӏ��̉��F�f�[�^�A�h���X�l��ύX
		for (auto i = voice_adr_list.begin(); i != voice_adr_list.end(); ++i)
		{
			size_t pos = *i;
			u16 idx = u16(outbuffer[pos + 0]) + u16(outbuffer[pos + 1]) * 0x100;

			// ���F�f�[�^���擾
			auto& voice = m_voice[idx];
			ASSERT(voice.offset);

			// �V�����l����������
			auto new_addr = base_address + size_t(voice.offset);
			outbuffer[pos + 0] = u8(new_addr & 0xff);
			outbuffer[pos + 1] = u8(new_addr >> 8);
		}
	}

	return true;
}

//--------------------------------------------------
//! OplDrvData::Header
//! MML�o�͗p��TEMPO�Z�b�g�A�b�v
//--------------------------------------------------
void OplDrvData::set_tempo(float tempo)
{
	// ���� tick���X�g
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
//! MML�o�͗p�F�������X�g�ǉ�
//--------------------------------------------------
void OplDrvData::add_note_length(int n, float tempo)
{
	m_note_length[n] = tempo2tick(tempo, n);
}

//--------------------------------------------------
//! OplDrvData::Header
//! MML�o�͗p�F������r
//! @return 0=��v -1=tick�������� +1=tick���傫��
//--------------------------------------------------
int OplDrvData::compare_note_length(float tick, int n)
{
	auto diff = tick - m_note_length[n];
	if (abs(diff) <= FLT_EPSILON)
	{
		return 0;	// equal
	}

	// �f�[�^���������Ȃ̂Ő؂�̂ĂƐ؂�グ������
	auto ft = floor(tick);
	auto fn = floor(m_note_length[n]); // �؂�̂�
	auto cn = ceil(m_note_length[n]); // �؂�グ
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
//! MML�o�͗p�F�������X�g�ǉ�
//--------------------------------------------------
int OplDrvData::get_note_length(float tick, float& note_tick)
{
	note_tick = tick;

	// ��v��D��
	for (auto i = m_note_length.begin(); i != m_note_length.end(); ++i)
	{
		if (0 == compare_note_length(tick, i->first))
		{
			return i->first;
		}
	}
	// �[���̂���ꍇ
	for (auto i = m_note_length.begin(); i != m_note_length.end(); ++i)
	{
		if (i->second <= tick)
		{
			if (i->first == 2) // L2�̎�
			{
				if (0 == compare_note_length(tick - m_note_length[3], 3))
				{
					note_tick = m_note_length[3];
					return 3; // 3+3�Ȃ�3���܂��Ԃ�
				}
			}
			if (0 == (i->first % 3)) // L3�̔{���̎�
			{
				auto n = i->first * 2;
				if (0 == compare_note_length(tick - m_note_length[n], i->first))
				{
					note_tick = i->second;
					return i->first;
				}
				continue; // 3�̔{���̑g�ݍ��킹�łȂ���΃X�L�b�v
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
	std::stringstream mml;		// �o�͐�
	std::stringstream buff;		// �ꎞ�o�͐�
	size_t line_size;			// �s�̒���
	size_t line_limit;			// 1�s�̒���
	float sum_tick;				// ���������v
	float measure_tick;			// 1����
	int measure_count;			// ���ߐ�
	bool measure_1st;			// ���߂̍ŏ����ǂ���
	int line_measure_count;		// ���̏��߂��Ƃɉ��s
	string line_head;			// �s�̐擪
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
			next_line_size += line_head.size(); // ���C���w�b�_���l��
		}
		if (1 < measure_count)
		{
			next_line_size += 1; // ���߂̊Ԃ̃X�y�[�X��
		}

		if (line_limit <= next_line_size)
		{
			MML_TRACE("1�s�̕������w����I�[�o�[\n");
			MML_TRACE(buff.str().c_str()); MML_TRACE("\n");
			if (0 < measure_count)
			{
				MML_TRACE("2���ߖڈȍ~�͏��ߊԂɉ��s��}��\n");
				mml << std::endl;
				line_size = size_t(buff.tellp());
				line_size += line_head.size();
				if (line_size)
				{
					MML_TRACE("���߂̈ꕶ���ڂł͂Ȃ��̂Ń��C���w�b�_���}��\n");
					mml << line_head;
					measure_1st = false;
				}
				else
				{
					MML_TRACE("���߂̐�ꕶ���ڂȂ̂Ńt���O�𗧂Ă�i���̌��add��line_head�͒ǉ������j\n");
					measure_1st = true;
				}
				measure_count = 0;
			}
			else
			if (!no_cr)
			{
				MML_TRACE("1���ߖڂ͓r�����s���Ă���ǉ�\n");
				if (1 < measure_count)
				{
					MML_TRACE("�󔒂�ǉ�\n");
					mml << " ";
					line_size += 1;
				}
				flush(flush_line);
			}
		}
		add(s);

		// 1����
		if ((0.f < measure_tick) && (0.f < tick)
			&& (measure_tick <= sum_tick))
		{
			sum_tick -= measure_tick;
			++measure_count;

			measure_1st = true; // ���̃R�}���h�����߂̓�

			MML_TRACE("1���߂̋�؂�\n");
			MML_TRACE(buff.str().c_str()); MML_TRACE("\n");

			if (line_measure_count <= measure_count)
			{
				MML_TRACE("�K�菬�ߐ��𒴂����̂Œǉ����ĉ��s\n");
				if (1 < measure_count)
				{
					MML_TRACE("���ߊԂɋ󔒂�ǉ�\n");
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
						MML_TRACE("���ߊԂɋ󔒂�ǉ�\n");
						mml << " ";
						line_size += 1;
					//}
					//else
					//{ // �� ���O�Ɍ����ӂꏈ���ς݂Ȃ̂ŕs�v
					//	MML_TRACE("�����������𒴂���̂ŉ��s��}��\n");
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
//! �ł������`�����l���̉��t���Ԃ��擾���� (tick)
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
//! MML���쐬����.
//! @param	outbuffer		�o�C�i���f�[�^�o�͂��󂯎��
//! @param	tempo			�e���|���w��
//! @param	mml_loop		MML�Ƀ��[�v�w��
//! @param	mml_rel_volume	���Ή��ʂŏo��
//! @param	def_len			�ȗ������� L?
//! @param	title			�^�C�g��
//! @param	time_signiture_d8	8���̉����q���w��
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
	const int default_volume = 12;		// OPLDRV�{�����[�������l

	set_tempo(tempo);

	mml_buffer buffer;					// �o�̓o�b�t�@

	float signiture_time = m_note_length[1];
	if (time_signiture_d8 != 8)
	{
		// n/8���q
		signiture_time = m_note_length[8] * time_signiture_d8;
	}

	// �ő包80�A�܂��� ?/4����
	buffer.init( 80, signiture_time, 4);

	int def_note_length = 0;			// �ȗ�������

	// �g�p�`�����l�����X�g������
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

	// ���[�U�[���F
	/*
	@v15 = { ; E - Guiter
	;       TL FB
			 7, 3,
	; AR DR SL RR KL MT AM VB EG KR DT
	  15, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0,
	  15, 7, 0, 7, 0, 8, 0, 0, 1, 0, 1 }
	 */
	u8 cur_user_voice = 16;	// ���[�U�[���F�ԍ�
	for (auto i = m_voice.begin(); i != m_voice.end(); ++i)
	{
		auto& voice = i->second;
		voice.voice_no = cur_user_voice++;

		buffer.mml << voice.make_mgs_mml();
		buffer.mml << std::endl;
	}

	// �ő剉�t����
	double max_tick = calc_max_ch_time();
	print("[INFO] max ch. time : " + double_str(max_tick));

	// ���[�v
	if (mml_loop && all_ch.size())
	{
		buffer.mml << all_ch << " [0" << std::endl << std::endl;
	}

	// ���Y���`�����l��
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

		// ����̓{�����[�������l�w��
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
					// �����ȗ�
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
						// [�b��] ���Y��������&���Ȃ��̂ŋx���Ŏc����w��
						if (def_len && (n == def_len))
						{
							// �����ȗ�
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

	// �����f�B�[�`�����l��
	for (int ch = 0; ch < m_header.getChannelCount(); ++ch)
	{
		auto& melody_ch = m_melody_ch[ch];

		if (melody_ch.size())
		{
			buffer.mml << ";--- Melody #" << std::dec << ch << " ---" << std::endl;
			buffer.line_head = string("9ABCDEFGH").at(ch) + string(" ");

			bool legato = false;

			int octave = -1;				// ���݂̃I�N�^�[�u
			int volume = -1;				// ���݂̃{�����[��
			int user_voice = 15;			// ���݂̃��[�U�[���F(15�͖���`)
			bool req_user_voice = false;	// ���[�U�[���F�R�}���h���K�v

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

					// �{�����[�����ݒ�
					if (volume < 0)
					{
						volume = default_volume;
						buffer.add_cmd("v" + dec(volume));
					}

					// ���[�U�[���F���ݒ�
					if (req_user_voice)
					{
						buffer.add_cmd("@" + dec(user_voice));
						req_user_voice = false;
					}

					// �I�N�^�[�u
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

					if (legato && i->m_opt) // �x���͂̎��̓X���[�s�v
					{
						// ���K�[�gON
						buffer.add_cmd("&");
					}
					if (def_len && (n == def_len))
					{
						// �����ȗ�
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
							// �����Ȃ�.
							buffer.add_cmd(".", note_tick, true);
						}
						else
						{
							if (!buffer.measure_1st && (note_total <= m_note_length[1]))
							{
								// �S�����ȓ��Ȃ�^�ŉ��������q����
								buffer.add_cmd("^" + dec(n), note_tick, true);
								ASSERT(n > 1);
							}
							else
							{
								// �X���[�Ōq����
								note_total = note_tick;
								if (i->m_opt) // �x���͂̎��̓X���[�s�v
								{
									buffer.add_cmd("&");
								}
								if (def_len && (n == def_len))
								{
									// �����ȗ�
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
					//	���F�ԍ�    ROM���F�ԍ�    ���F��
					//		0        1	   �o�C�I����
					//		1        2	   �M�^�[
					//		2		 3	   �s�A�m
					//		3		 4	   �t���[�g
					//		4		 5	   �N�����l�b�g
					//		5		 6	   �I�[�{�G
					//		6		 7	   �g�����y�b�g
					//		7		 8	   �I���K��
					//		8		 9	   �z����
					//		9		10	   �V���Z
					//		10		11	   �n�[�v�V�R�[�h
					//		11		12	   �r�u���t�H��
					//		12		13	   �V���Z�x�[�X
					//		13		14	   �E�b�h�x�[�X
					//		14		15	   �G���L�x�[�X
					//		15		 0
					//		: : �I���W�i�����F
					//		31		 0
					int voice = int(i->m_opt - 1);
					if ((voice < 0) || (14 < voice))
					{
						req_user_voice = true;	// ���[�U�[���F�w��\��
					}
					else
					{
						buffer.add_cmd("@" + dec(voice));
					}
					break;
				}
				case Command::CMD_SUSTAIN:
				{
					buffer.add_cmd(string("s") + (i->m_opt ? "o " : "f "));
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
					req_user_voice = false;	// ���[�U�[���F�w��\�����
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
						// MGSDRV�̓`�����l���ɔ������x�����Ȃ��ƃo�O��
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

	// ���[�v
	if (mml_loop && all_ch.size())
	{
		buffer.mml << all_ch << " ]" << std::endl;
	}

	outbuffer = buffer.mml.str();
	return true;
}

#include "uni_common.h"
#include "opldrv_data.h"

#include <vector>

#define DEFAULT_INPUTFILENAME ""
#if defined(_DEBUG)
    #undef DEFAULT_INPUTFILENAME 
    #define DEFAULT_INPUTFILENAME "../fmpac01.opl"
#endif

#define USE_OUT_FILE_NAME_OPTION	1

//===============================================
// show help
//===============================================
void showHelp()
{
	print(
		"OPLDRV TOOL"
		"\n\n"
		"OPLDRV_tool [/l:filename][/b:address)][/r:address)] [INPUT FILENAME]"
#if USE_OUT_FILE_NAME_OPTION
		" [/o:OUTPUT FILENAME]"
#endif
		"\n"
		"/l:filename  Log text output to file.\n"
		"/a:address   set base address for RAW file.\n"
		"             (Required for data using user voice.)\n"
		"/r:address   relocate to address.\n"
		"             (Required for data using user voice.)\n"
		"/b           add BSAVE header to output.\n"
		"/-b          RAW output. (remove BSAVE header)\n"
		"\n"
		"/cv:fmpac    convert ex-voice to user-voice. (use FMPAC ver.)\n"
		"/cv:music    convert ex-voice to user-voice. (use A1GT ver.)\n"
		"             (same as /cv:a1gt)\n"
		"\n"
		"/v:volume    modify volume (-15 ~ +15)"
		"\n\n"
		"*1 [address] is hexadecimal.\n"
		"   (e.g. 0000, a000, C000) \n"
		"*2 take care address when use \"user-voice\".\n"
		"   (\"user-voice\" use absolute address) \n"
		"\n"
	);
}

//===============================================
// main
//===============================================
int main(int argc, char* argv[])
{
	using OPLDRV::OplDrvData;

	//-------------------------------------
	//  parse args
	//-------------------------------------
	string inFileName = DEFAULT_INPUTFILENAME;
    string outFileNameReq = "";
	string out_ext = ".out";

	bool silent_mode = false;			//!< キー入力待ちをしない
	bool protect_infile = false;		//!< 元ファイルへの上書きを禁止する

	u16 in_base_address = 0;
	u16 out_base_address = 0;			//!< 出力データの先頭アドレス（ユーザ音色使用時に必要）

	bool use_bsave_header = false;		//!< BSAVEヘッダを付与する（元がBSAVEファイルならtrue）
	bool force_bsave_header = false;	//!< 必ずBSAVEヘッダを付与する
	bool remove_bsave_header = false;	//!< 必ずBSAVEヘッダを削除する

	string logFileName = "";

	int convert_rom_voice = 0;			//!< 拡張音色をユーザー定義音色コマンドに変更
										//!< 1=FMPAC拡張音色/2=A1GT拡張音色

	int volume_change = 0;				//!< 音量変更 マイナスなら音が大きくなる

    //-- parse arguments
    int argi = 1;
    int  filename_arg_step = 0;
	bool req_out_base_address = false;

    bool arg_error = false;

    while (argi < argc)
    {
        string arg(argv[argi]);
        if (arg.size())
        {
            string l = get_lower(arg);
			//-- arg: output use BSAVE HEADER (BSAVE)
			if (l == "/b")
			{
				print(string("arg: add BSAVE header: ") + arg);
				force_bsave_header = true;
				remove_bsave_header = false;
			}
			else
			//-- arg: output don't use BSAVE HEADER (RAW)
			if (l == "/-b")
			{
				print(string("arg: remove BSAVE header: ") + arg);
				force_bsave_header = false;
				remove_bsave_header = true;
			}
			else
			//-- arg: output log file
			if (l.substr(0, 3) == "/l:")
			{
				logFileName = arg.substr(3);
				print(string("arg: logFileName : ") + arg);
				OplDrvData::trace_mode = true; // 解析出力を有効化
			}
			else
			//-- arg: input base address
			if (l.substr(0, 3) == "/a:")
			{
				std::istringstream(arg.substr(3)) >> std::hex >> in_base_address;
				print(string("arg: base address : ") + hex(in_base_address, 4));
				if (!req_out_base_address)
				{
					out_base_address = in_base_address;
				}
			}
			else
			//-- arg: relocate
			if (l.substr(0, 3) == "/r:")
			{
				std::istringstream(arg.substr(3)) >> std::hex >> out_base_address;
				print(string("arg: relocate to address : ") + hex(out_base_address, 4));
				req_out_base_address = true;
			}
			else
			//-- arg: convert extention voice
			if (l.substr(0, 4) == "/cv:")
			{
				string romtype = get_lower(arg.substr(4));
				print(string("arg: convert ex-voice cmd to user-voice cmd: ") + romtype);
				if (romtype == "fmpac")
				{
					convert_rom_voice = 1;
				}
				else
				if (romtype == "music")
				{
					convert_rom_voice = 2;
				}
				else
				if (romtype == "a1gt")
				{
					convert_rom_voice = 2;
				}
				else
				{
					print_error("unknown voice rom type name: " + romtype);
					ASSERT(0);
					arg_error = true;
				}
			}
			else
			//-- arg: modify volume
			if (l.substr(0, 3) == "/v:")
			{
				std::istringstream(arg.substr(3)) >> std::dec >> volume_change;
				print(string("arg: modify volume : ") + decimal(volume_change));
			}
			else
			//-- arg: inFileName
			if (filename_arg_step == 0)
			{
				inFileName = arg;
				print(string("arg: inFIlename : ") + arg);
				filename_arg_step += 1;
			}
#if USE_OUT_FILE_NAME_OPTION
			else
			//-- arg: outFilename
			if (l.substr(0, 3) == "/o:")
			{
				if (filename_arg_step == 1)
				{
					outFileNameReq = arg.substr(3);
					print(string("arg: outFileName : ") + arg);
					filename_arg_step += 1;
				}
				else
				{
					print(string("arg: outFileName already specified. ") + arg);
					arg_error = true;
				}
			}
#endif
			else
			{
				print(string("arg: [unknown arg] : ") + arg);
				arg_error = true;
			}
		}
		argi += 1;
	}

	//-------------------------------------
	// need help?
	if (arg_error || !inFileName.size())
	{
		if (arg_error)
		{
			print_error(string("[ERROR] argument error."));
		}
		showHelp();
		if (!silent_mode)   std::cin.get();
		return 1; // error end
	}

	//-------------------------------------
	// set log file
	if (logFileName.size())
	{
		FILE* logfile;
		errno_t err_no = fopen_s(&logfile, logFileName.c_str(), "w");
		if (err_no != 0)
		{
			print_error(string("[ERROR] can not open file. \"") + logFileName + "\"");
			if (!silent_mode)   std::cin.get();
			return 1; // error end
		}
		set_log_file( logfile );
	}

	//-------------------------------------
	//-- decide input file path
	print(string("inFileName:") + inFileName);
	fs::path inPath(inFileName);
	string ext = inPath.extension().generic_string();
	
	//-------------------------------------
	//-- decide output file path
#ifdef _DEBUG
	fs::path outPath(inFileName);
	outPath.replace_extension(out_ext);
	string outFileName = outPath.generic_string();
#else
	string outFileName = "";
#endif

#if USE_OUT_FILE_NAME_OPTION
	if (outFileNameReq.size())
	{
		outFileName = outFileNameReq;
	}
#endif
	print(string("outFileName:") + outFileName);
	print(string("fs::current_path():") + fs::current_path().generic_string());

	//-------------------------------------
	// 上書きかどうか調べる
	if (inFileName == outFileName)
	{
		print(string("[overwrite source file] ") + outFileName + " -> " + outFileName);
		if (protect_infile)
		{
			// 上書き禁止
			print_error(string("[ERROR] Overwriting the original file is prohibited."));
			if (!silent_mode)   std::cin.get();
			return 1; // error end
		}
	}

	//-------------------------------------
	// ファイルオープン
	FILE* inFile;
	errno_t err_no = fopen_s(&inFile, inFileName.c_str(), "rb");
	if (err_no != 0)
	{
		print_error(string("[ERROR] can not open file. \"") + inFileName + "\"");
		if (!silent_mode)   std::cin.get();
		return 1; // error end
	}
	// get file size
	std::error_code ec{};
	auto inFileSize = fs::file_size(inFileName, ec);
	if (!ec)
	{
		// OK
	}
	else
	{
		print_error(string("[ERROR] can not get file size. \"") + inFileName + "\"");
		if (!silent_mode)   std::cin.get();
		return 1; // error end
	}
	print(string("in_file size = ") + std::to_string(inFileSize));

	//-------------------------------------
	// ファイル読み込み
	std::vector<u8> data(inFileSize);
	size_t rsize = fread(&data[0], 1, inFileSize, inFile);
	if (rsize != inFileSize)
	{
		print_error(string("[ERROR] file read error."));
		if (!silent_mode)   std::cin.get();
		return 1; // error end
	}
	fclose(inFile);
	inFile = nullptr;

	//-------------------------------------
	// コマンドデータ解析
	OplDrvData opldata;
	const u8* p = &data[0];
	size_t offset = 0;

	u8 bsave_header[7] = { 0xfe, 0,0, 0,0, 0,0 };

	if (*p == bsave_header[0])
	{
		print(string("[INFO] input file is BSAVE file."));

		// skip BSAVE header.
		offset  = countof(bsave_header);

		// get start_address from BSAVE header.
		in_base_address = u16(p[1]) + u16(p[2]) * 0x100;

		use_bsave_header = true;
		if (!req_out_base_address)
		{
			out_base_address = in_base_address;
		}
	}
	bool result = opldata.from_binary( p + offset, p + data.size(), in_base_address );
	if (!result)
	{
		if (!silent_mode)   std::cin.get();
		return 1;
	}

	//-------------------------------------
	// 音量修正
	if (volume_change)
	{
		print_log("[INFO] volume modify " + decimal(volume_change));
		// リズムチャンネル
		if (opldata.m_rhythm_ch.size())
		{
			for (auto i= opldata.m_rhythm_ch.begin();
				 i != opldata.m_rhythm_ch.end();
				++i)
			{
				if (i->m_cmd == OplDrvData::Command::CMD_R_VOL)
				{
					int v = int(i->m_param);
					v += volume_change;
					if ((v < 0) || (15 < v))
					{
						print_log("[CAUTION] volume over flow. " 
							+ decimal(i->m_param) + " -> " + decimal(v));
						v = (v < 0) ? 0 : 15;
					}
					i->m_param = v;
				}
			}
		}
		// メロディーチャンネル
		for (int ch = 0; ch < countof(opldata.m_melody_ch); ++ch)
		{
			if (opldata.m_melody_ch[ch].size())
			{
				for (auto i = opldata.m_melody_ch[ch].begin();
					 i != opldata.m_melody_ch[ch].end();
					++i)
				{
					if (i->m_cmd == OplDrvData::Command::CMD_VOL)
					{
						int v = i->m_opt;
						v += volume_change;
						if ((v < 0) || (15 < v))
						{
							print_log("[CAUTION] volume over flow. "
								+ decimal(i->m_opt) + " -> " + decimal(v));
							v = (v < 0) ? 0 : 15;
						}
						i->m_opt = v;
					}
				}
			}
		}
	}

	//-------------------------------------
	// ROM拡張音色コマンドをユーザー音色コマンドに変換
	if (convert_rom_voice)
	{
		if (!opldata.convert_voice_rom_to_user(convert_rom_voice))
		{
			if (!silent_mode)   std::cin.get();
			return 1;
		}
	}

	//-------------------------------------
	// 出力
	if (outFileName.size())
	{
		std::vector<u8> output_buffer;
		if (opldata.make_binary( output_buffer, out_base_address ))
		{
			FILE* outFile;
			errno_t err_no = fopen_s(&outFile, outFileName.c_str(), "wb");
			if (err_no != 0)
			{
				print_error(string("[ERROR] can not open file. \"") + inFileName + "\"");
				if (!silent_mode)   std::cin.get();
				return 1; // error end
			}
			if (!remove_bsave_header && (use_bsave_header || force_bsave_header))
			{
				bsave_header[0] = 0xfe; // BSAVE ID
				bsave_header[1] = u8(out_base_address & 0xff);
				bsave_header[2] = u8(out_base_address >> 8);
				auto end_address = out_base_address + output_buffer.size() - 1;
				bsave_header[3] = u8(end_address & 0xff);
				bsave_header[4] = u8(end_address >> 8);
				bsave_header[5] = bsave_header[1];
				bsave_header[6] = bsave_header[2];

				print("[INFO] output BSAVE file.");
				print("       start = 0x" + hex(out_base_address, 4));
				print("       end   = 0x" + hex(end_address, 4));
				print("       size  = 0x" + hex(output_buffer.size(), 4));
				print("       total = 0x" + hex(output_buffer.size() + countof(bsave_header), 4));

				auto out_size = fwrite(&bsave_header[0], 1, countof(bsave_header), outFile);
				if (!out_size)
				{
					print_error(string("[ERROR] can not write file. \"") + inFileName + "\"");
					if (!silent_mode)   std::cin.get();
					return 1; // error end
				}
			}
			else
			{
				print("[INFO] output RAW file.");
				print("       start = 0x" + hex(out_base_address, 4));
				print("       end   = 0x" + hex(out_base_address + output_buffer.size() - 1, 4));
				print("       size  = 0x" + hex(output_buffer.size(), 4));
				print("       total = 0x" + hex(output_buffer.size(), 4));

			}
			auto out_size = fwrite( &output_buffer[0], 1, output_buffer.size(), outFile);
			if (!out_size)
			{
				print_error(string("[ERROR] can not write file. \"") + inFileName + "\"");
				if (!silent_mode)   std::cin.get();
				return 1; // error end
			}
		}
	}

	return 0;
}

#include <string>
#include <sstream>
#include <stdio.h>
#include <iostream>
//#include <fstream>
#include <filesystem>	// need c++17
#include <algorithm>
	
// GRAPH SAURUS"S COMPRESSION (GS RLE)
//

#define DEFAULT_INPUTFILENAME ""
#if defined(_DEBUG)
	#undef DEFAULT_INPUTFILENAME 
	//#define DEFAULT_INPUTFILENAME "../test/TEST.SC7"
	#define DEFAULT_INPUTFILENAME "../test/RYUJO256.SC7"
	//#define DEFAULT_INPUTFILENAME "../test/JTHUNDER.SRC"
#endif

// 
#define USE_OUT_FILE_NAME_OPTION	1

// cheat
#define countof(x) (sizeof(x)/sizeof(x[0]))
namespace fs = std::filesystem;
typedef std::string     string;
typedef uint32_t        u32;
typedef uint16_t        u16;
typedef uint8_t         u8;

string hex(int i)
{
	std::stringstream ss;
	ss << std::hex << i;
	return ss.str();
}
int print( string s )
{
	return printf((s + "\n").c_str());
}

string get_lower(const string& s)
{
	string d;
	d.resize( s.size() );
	std::transform(s.begin(), s.end(), d.begin(), tolower);
	return d;
}
string get_upper(const string& s)
{
	string d;
	d.resize( s.size() );
	std::transform(s.begin(), s.end(), d.begin(), toupper);
	return d;
}

//===============================================
// show help
//===============================================
void showHelp()
{
	print(
		"GRAPH SAURUS like RLE ENCODER"
		"\n\n"
		"GSRLE [/np][/l][/cp][/256][/212][/s][INPUT FILENAME]"
#if USE_OUT_FILE_NAME_OPTION
		"[/o:OUTPUT FILENAME]"
#endif
		"\n\n"
		"/s      Slient mode. (no input wait)\n"
		"/bh     Use BSAVE header address range."
		"        (Default : use file size)"
		"/cp     Force output size : to palette table.\n"
		"/212    Force output size : to line 212.\n"
		"/256    Force output size : to line 256.\n"
		"/org    Force output size : to original size.\n"
		"/auto   Auto output size : compress: pixel only\n"
		"                           BSAVE:    origin size.\n"
		"        (Default : px)"
		"/np     No output palette(pl?) file.\n"
		"/fp     Force output palette(pl?) file\n"
		"        (at over 256 line data).\n"
		"/l      Do not overwrite input file.\n"
		"\n"
	);
}

namespace gsrle {

//===============================================
// BSAVE/GS FILE HEADER
//===============================================
#pragma pack(1)
struct BsaveHeader
{
	u8  type_id;
	u16 start_address;
	u16 end_address;
	u16 run_address;
};
#pragma pack()
const int HEADER_SIZE = 7;
const int HEAD_ID_LINEAR   = 0xFE; // BSAVE/GS LINEAR
const int HEAD_ID_COMPRESS = 0xFD; // #GS RLE COMPLESS

// BSAVE END END ADDRESS LIMIT
const int BSAVE_END_LIMIT = 0xFFFE;
const int HEAD_END_LIMIT = 0xFFFF;
int cap_bsave_address(int adr)
{
	if (adr > BSAVE_END_LIMIT)
		adr = BSAVE_END_LIMIT;
	return adr;
}

//===============================================
// FILE EXTENSION INFO
//===============================================
struct ExtInfo
{
	const char* ext;        //拡張子
	int         screen_no;  //スクリーンモード
	bool        interlace;  //インターレースモード
	bool        gs_type;    //グラフサウルス形式（パレットファイル別、最終アドレスはアドレスではなくサイズ)
	const char* bsave_ext;  //BSAVE拡張子
	const char* gs_ext;     //GRAPH SAURUS拡張子
};
const ExtInfo EXT_INFO_LIST[] = {
	// BSAVE
	{".SC2", 2,0,0,".SC2",".SR2"},
	{".SC3", 3,0,0,".SC3",".SR3"},
	{".SC4", 4,0,0,".SC4",".SR4"},
	{".SC5", 5,0,0,".SC5",".SR5"},
	{".SC7", 7,0,0,".SC7",".SR7"},
	{".SC8", 8,0,0,".SC8",".SR8"},
	{".S10",10,0,0,".S10",".SRA"},
	{".S12",12,0,0,".S12",".SRC"},
	// BSAVE interlace
	{".S50", 5,1,0,".S50",".R50"},  {".S51", 5,1,0,".S51",".R51"},
	{".S70", 7,1,0,".S70",".R70"},  {".S71", 7,1,0,".S71",".R71"},
	{".S80", 8,1,0,".S80",".R80"},  {".S81", 8,1,0,".S81",".R81"},
	{".SA0",10,1,0,".SA0",".RA0"},  {".SA1",10,1,0,".SA1",".RA1"},
	{".SC0",12,1,0,".SC0",".RC0"},  {".SC1",12,1,0,".SC1",".RC1"},
	// GRAPH SAURUS
	{".SR2", 2,0,1,".SC2",".SR2"},
	{".SR3", 3,0,1,".SC3",".SR3"},
	{".SR4", 4,0,1,".SC4",".SR4"},
	{".SR5", 5,0,1,".SC5",".SR5"},
	{".SR7", 7,0,1,".SC7",".SR7"},
	{".SR8", 8,0,1,".SC8",".SR8"},
	{".SRA",10,0,0,".S10",".SRA"},
	{".SRC",12,0,0,".S12",".SRC"},
	{".SRS",12,0,1,".S12",".SRS"},
	// GRAPH SAURUS interlace
	{".R50", 5,1,1,".S50",".R50"},  {".R51", 5,1,1,".S51",".R51"},
	{".R70", 7,1,1,".S70",".R70"},  {".R71", 7,1,1,".S71",".R71"},
	{".R80", 8,1,1,".S80",".R80"},  {".R81", 8,1,1,".S81",".R81"},
	{".RA0",10,1,1,".SA0",".RA0"},  {".RA1",10,1,1,".SA1",".RA1"},
	{".RC0",12,1,1,".SC0",".RC0"},  {".RC1",12,1,1,".SC1",".RC1"},
};
const ExtInfo* get_ext_data(const string& org_path)
{
	fs::path p = org_path;
	string ex = p.extension().generic_string();

	if (ex.size())
	{
		string e = get_upper(ex);
		for (int i = 0; i < countof(EXT_INFO_LIST); ++i)
		{
			const ExtInfo* d = EXT_INFO_LIST + i;
			if (e == d->ext)
			{
				return d;
			}
		}
	}
	return nullptr;
}

//===============================================
// VRAM PALETTE TABLE ADDRESS
//===============================================
const int PAL_TABLE_LIST[] = {
	//SCREEN0:WIDTH40,SCREEN0:WIDTH80,SCREEN1,SCREEN2,SCREEN3,
	0x0400,0x0F00,0x2020,0x1B80,0x2020,
	//SCREEN4,SCREEN5,SCREEN6,SCREEN7,SCREEN8,
	0x1B80,0x7680,0x7680,0xFA80,0xFA80,
	//SCREEN9,SCREEN10,SCREEN11,SCREEN12
	0x7680,0xFA80,0xFA80,0xFA80
};
int get_pal_table(int screen_no)
{
	int s = screen_no + ((screen_no>0) ? 1 : 0);
	if ((s<-1) || (s>=countof(PAL_TABLE_LIST)))
	{
		return -1;
	}
	return PAL_TABLE_LIST[s];
}
//===============================================
// SCREEN VRAM END ADDRESS
//===============================================
const int END_ADDRESS_LIST_WITH_PALETTE[] = {
	//SCREEN0:WIDTH40,SCREEN0:WIDTH80,SCREEN1,SCREEN2,SCREEN3,
	0x0FFF,0x17FF,0x37FF,0x37FF,0x203F,
	//SCREEN4,SCREEN5,SCREEN6,SCREEN7,SCREEN8,
	0x37FF,0x769F,0x769F,0xFA9F,0xFA9F,
	//SCREEN9,SCREEN10,SCREEN11,SCREEN12
	0x769F,0xFA9F,0xFA9F,0xFA9F
};
const int END_ADDRESS_LIST_PIXEL[] = {
	//SCREEN0:WIDTH40,SCREEN0:WIDTH80,SCREEN1,SCREEN2,SCREEN3,
	0x0FFF,0x17FF,0x37FF,0x37FF,0x37FF,
	//SCREEN4,SCREEN5,SCREEN6,SCREEN7,SCREEN8,
	0x37FF,0x69FF,0x69FF,0xD3FF,0xD3FF,
	//SCREEN9,SCREEN10,SCREEN11,SCREEN12
	0x69FF,0xD3FF,0xD3FF,0xD3FF
};
const int END_ADDRESS_LIST_PIXEL_MAX[] = {
	//SCREEN0:WIDTH40,SCREEN0:WIDTH80,SCREEN1,SCREEN2,SCREEN3,
	0x0FFF,0x17FF,0x37FF,0x37FF,0x37FF,
	//SCREEN4,SCREEN5,SCREEN6,SCREEN7,SCREEN8,
	0x37FF,0x7FFF,0x7FFF,0xFFFF,0xFFFF,
	//SCREEN9,SCREEN10,SCREEN11,SCREEN12
	0x7FFF,0xFFFF,0xFFFF,0xFFFF
};
int get_end_address_with_pal(int screen_no)
{
	int s = screen_no + ((screen_no>0) ? 1 : 0);
	if ((s<0) || (s>=countof(END_ADDRESS_LIST_WITH_PALETTE)))
	{
		return -1;
	}
	return END_ADDRESS_LIST_WITH_PALETTE[s];
}
int get_end_address_y212(int screen_no)
{
	int s = screen_no + ((screen_no>0) ? 1 : 0);
	if ((s<0) || (s>=countof(END_ADDRESS_LIST_PIXEL)))
	{
		return -1;
	}
	return END_ADDRESS_LIST_PIXEL[s];
}
int get_end_address_y256(int screen_no)
{
	int s = screen_no + ((screen_no>0) ? 1 : 0);
	if ((s<0) || (s>=countof(END_ADDRESS_LIST_PIXEL_MAX)))
	{
		return -1;
	}
	return END_ADDRESS_LIST_PIXEL_MAX[s];
}

//===============================================
// Run Length Encode
//===============================================
const u8* rleNext(const u8* p, const u8* e, int& n, u8& v)
{
	n = 0;
	while (p < e)
	{
		v = *(p++);
		++n;
		if (v != *p)
		{
			return p;
		}
	}
	return p;
}

u8* rleAppend(u8 v, u8* dst, u8* dst_end)
{
	if (dst && (dst < dst_end))
	{
		*dst = v;
		return dst + 1;
	}
	return nullptr;
}

const u8* rleEncode(const u8* src, const u8* src_end, u8* dst, u8* dst_end)
{
	int n;
	u8 v;
	while (src < src_end)
	{
		src = rleNext(src, src_end, n, v);
		while (n > 0)
		{
			if (n>255)
			{
				dst = rleAppend(0  ,   dst, dst_end);
				dst = rleAppend(255,   dst, dst_end);
				dst = rleAppend(v  ,   dst, dst_end);
				n-=255;
			}
			else if(n >= 16)
			{
				dst = rleAppend(0  ,   dst, dst_end);
				dst = rleAppend(n  ,   dst, dst_end);
				dst = rleAppend(v  ,   dst, dst_end);
				n-=n;
			}
			else if ((n > 2) || (v < 16))
			{
				dst = rleAppend(n  ,   dst, dst_end);
				dst = rleAppend(v  ,   dst, dst_end);
				n-=n;
			}
			else
			{
				dst = rleAppend(v  ,   dst, dst_end);
				n-=1;
			}
			if (!dst) break;
		}
		if (!dst) break;
	}
	return dst;
}

} //namespace gsrle

//===============================================
// main
//===============================================
int main(int argc, char *argv[])
{
	// setting
	enum OutputPixelMode {
		origin = 0,		// 元のバイナリヘッダで指定されたサイズでVRAMを出力する
		autoSize,		// 圧縮ならピクセルデータのみ。BSAVEなら元ファイルの範囲
		toPalette,		// パレットテーブルまでのVRAMを出力する
		line212,		// 212ラインまでのVRAMを出力する
		line256,		// 256ラインまでのVRAMを出力する

	};
	OutputPixelMode output_pixel_mode = OutputPixelMode::autoSize;
	int output_pixel_height = 0;	// 指定したラインまでのVRAMを出力する
	bool output_gs_file = true; // GRAPH SAURUS形式で書き出す
	bool silent_mode = false; //!< キー入力待ちをしない
	bool protect_infile = false; //!< 元ファイルへの上書きを禁止する
	bool output_pal_file = true; //!< パレットファイルを出力する(条件を満たす場合)
	bool force_output_pal_file = false; //!< パレットファイルを強制出力
	bool use_bsave_header_address = false; //!< BSAVEヘッダの開始アドレス～終了アドレスの範囲を対象にする

	string inFileName = DEFAULT_INPUTFILENAME;
	string outFileNameReq = "";

	//// parse arguments
	int argi = 1;
	int  filename_arg_step = 0;

	bool arg_error = false;

	while (argi < argc)
	{
		string arg(argv[argi]);
		if (arg.size())
		{
			string l = get_lower(arg);

			//// arg: no output palette
			if (l == "/np")
			{
				output_pal_file = false;
				print(string("arg: no output pal file: ") + arg);
			}
			else
			//// arg: force output palette
			if (l == "/fp")
			{
				force_output_pal_file = true;
				print(string("arg: force output pal file: ") + arg);
			}
			else
			//// arg: protect input file
			if (l == "/l")
			{
				protect_infile = true;
				print(string("arg: protect input file : ") + arg);
			}
			else
			//// arg: force include palette
			if (l == "/cp")
			{
				output_pixel_mode = OutputPixelMode::toPalette;
				print(string("arg: clip size = force include palette : ") + arg);
			}
			else
			//// arg: force 255 line
			if (l == "/256")
			{
				output_pixel_mode = OutputPixelMode::line256;
				print(string("arg: clip size = force 256 line : ") + arg);
			}
			else
			//// arg: force 212 line
			if (l == "/212")
			{
				output_pixel_mode = OutputPixelMode::line212;
				print(string("arg: clip size = force 212 line : ") + arg);
			}
			else
			//// arg: force include palette
			if (l == "/org")
			{
				output_pixel_mode = OutputPixelMode::origin;
				print(string("arg: clip size = binary original size : ") + arg);
			}
			else
			//// arg: force include palette
			if (l == "/auto")
			{
				output_pixel_mode = OutputPixelMode::autoSize;
				print(string("arg: clip size = gs: pixel only / bsave: original size : ") + arg);
			}
			else
			//// arg: use BSABE header address
			if (l == "/bh")
			{
				use_bsave_header_address = true;
				print(string("arg: Use BSAVE header size specification : ") + arg);
			}
			else
			//// arg: silent mode
			if (l == "/s")
			{
				silent_mode = true;
				print(string("arg: silent mode : ") + arg);
			}
			else
			//// arg: inFileName
			if (filename_arg_step == 0)
			{
				inFileName = arg;
				print(string("arg: inFIlename : ") + arg);
				filename_arg_step += 1;
			}
#if USE_OUT_FILE_NAME_OPTION
			else
			//// arg: outFilename
			if (l.substr(0,3) == "/o:")
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

	if (arg_error || !inFileName.size())
	{
		if (arg_error)
		{
			print(string("[ERROR] argument error."));
		}
		showHelp();
		if (!silent_mode)   std::cin.get();
		return 1; // error end
	}

	print(string("inFileName:") + inFileName);
	fs::path inPath(inFileName);
	string ext = inPath.extension().generic_string();

	auto extd = gsrle::get_ext_data(inFileName);
	if (!extd || extd->screen_no == 0)
	{
		print(string("[ERROR] This file is not support type \"") + ext + "\"");
		if (!silent_mode)   std::cin.get();
		return 1; // error end
	}
	print(string("screen no: ") + std::to_string(extd->screen_no));

	int pal_adr = gsrle::get_pal_table(extd->screen_no);
	print(string("palette table address: ") + hex(pal_adr));

	size_t pixel_end_212 = gsrle::get_end_address_y212(extd->screen_no);
	size_t pixel_end_256 = gsrle::get_end_address_y256(extd->screen_no);
	size_t pixel_end_with_pal = gsrle::get_end_address_with_pal(extd->screen_no);
	print(string("pixel end address (line 212)    : ") + hex(pixel_end_212));
	print(string("pixel end address (line 256)    : ") + hex(pixel_end_256));
	print(string("pixel end address (with palette): ") + hex(pixel_end_with_pal));

	//// decide output file path
	fs::path outPath(inFileName);
	outPath.replace_extension(extd->gs_ext);
	string outFileName = outPath.generic_string();
#if USE_OUT_FILE_NAME_OPTION
	if (outFileNameReq.size())
	{
		outFileName = outFileNameReq;
	}
#endif
	print(string("outFileName") + outFileName);
	print(string("fs::current_path():") + fs::current_path().generic_string());

	// 上書きかどうか調べる
	if (inFileName == outFileName)
	{
		print(string("[overwrite source file] ") + outFileName + " -> " + outFileName);
		if (protect_infile)
		{
			// 上書き禁止
			print(string("[ERROR] Overwriting the original file is prohibited."));
			if (!silent_mode)   std::cin.get();
			return 1; // error end
		}
	}

	//// read file

	FILE* inFile;
	errno_t err_no = fopen_s(&inFile, inFileName.c_str(), "rb");
	if (err_no != 0)
	{
		print(string("[ERROR] can not open file. \"") + inFileName + "\"");
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
		print(string("[ERROR] can not get file size. \"") + inFileName + "\"");
		if (!silent_mode)   std::cin.get();
		return 1; // error end
	}
	print(string("in_file size = ") + std::to_string(inFileSize));

	// read file
	std::vector<u8> data( inFileSize );
	size_t rsize = fread( &data[0], 1, inFileSize, inFile );
	if (rsize != inFileSize)
	{
		print(string("[ERROR] file read error."));
		if (!silent_mode)   std::cin.get();
		return 1; // error end
	}
	fclose(inFile);
	inFile = nullptr;

	//// get file Header infomation
	gsrle::BsaveHeader header;
	header.type_id = data[0];
	header.start_address = data[1] + data[2] * 256;
	header.end_address   = data[3] + data[4] * 256;
	header.run_address   = data[5] + data[6] * 256;
	print(string("--- source file ---"));
	print(string("type_id = ") + hex(header.type_id));
	print(string("start_address = ") + hex(header.start_address));
	print(string("end_address = ") + hex(header.end_address));
	print(string("run_address = ") + hex(header.run_address));
	print(string("----------------"));

	// ピクセルデータサイズ
	//  = ヘッダ以降のサイズ
	size_t org_size = data.size() - gsrle::HEADER_SIZE;

	// ピクセルデータサイズをファイルサイズからではなくヘッダから決定する
	//  色々ややこしいので使わない方がいい。
	if (!use_bsave_header_address)
	{
		print(string("data_size (from file size) : ") + std::to_string(org_size) + " (0x" + hex(org_size) + ")");
	}
	else
	{
		// 0の場合は0x10000とみなす
		org_size = (header.end_address) ? header.end_address : 0x10000;
		if (header.type_id == gsrle::HEAD_ID_COMPRESS)
		{
			// GS COMPRESS type
			// GS圧縮形式は
			// 開始アドレス, データサイズ, 0

			// そのまま
		}
		else
		{
			// BSAVE形式は
			// 開始アドレス, 終了アドレス, 0
			// GSベタ形式は
			// 開始アドレス, データサイズ, 0
			// 
			// 中身が判定できないので簡易的に偶数丸め込み。
			//
			// ※ GSベタの場合は開始0固定前提で処理するため、
			//    もし、開始アドレスが0以外のデータがあっても非対応。
			//    (見たことはない)

			// BSAVE制限ぎりぎりであれば0xFFFFとして扱う
			if (org_size == (gsrle::BSAVE_END_LIMIT))
			{
				org_size = gsrle::HEAD_END_LIMIT;
			}

			org_size = org_size - header.start_address + 1; //BSAVE type
			org_size &= SIZE_MAX ^ 1; // 偶数丸め込み 0xFFFFFFFF xor 1
		}
		print(string("data_size (from HEADER): ") + std::to_string(org_size) + " (0x" + hex(org_size) + ")");
	}

	if ((org_size < 1) || (header.type_id != gsrle::HEAD_ID_LINEAR))
	{
		print(string("not support type. (already compressed, or missing type)"));
		if (!silent_mode)   std::cin.get();
		return 1;
	}

	//// 圧縮対象のサイズを決定
	size_t pixel_size = 0;
	switch (output_pixel_mode) {
	case OutputPixelMode::line212:
		pixel_size = pixel_end_212 + 1;
		break;
	case OutputPixelMode::line256:
		pixel_size = pixel_end_256 + 1;
		break;
	case OutputPixelMode::toPalette:
		pixel_size = pixel_end_with_pal + 1;
		break;
	case OutputPixelMode::origin:
		pixel_size = org_size;
		break;
	case OutputPixelMode::autoSize:
	default:
		if (output_gs_file)
		{
			// ピクセル範囲判定
			if (org_size <= (pixel_end_with_pal + 1))
			{
				pixel_size = pixel_end_212 + 1;
			}
			else
			{
				pixel_size = pixel_end_256 + 1;
			}
		}
		else
		{
			pixel_size = org_size;
		}
		break;
	}
	print(string("need_pixel_size: ") + std::to_string(pixel_size) + " (0x" + hex(pixel_size) + ")");

	// expand data to pixelsize
	auto file_body_size = data.size() - gsrle::HEADER_SIZE;
	if (pixel_size > file_body_size)
	{
		auto old_size = data.size();
		data.resize(pixel_size + gsrle::HEADER_SIZE);
		std::fill( &data[0] + old_size, &data[0] + pixel_size, 0);
		file_body_size = data.size() - gsrle::HEADER_SIZE;
		if (file_body_size < pixel_size)
		{
			print(string("[innner error] file_body_size < pixel_size"));
			if (!silent_mode)   std::cin.get();
			return 1; // error end
		}
		print(string("(expand source pixel to ") + std::to_string(pixel_size) + " (0x" + hex(pixel_size) + ")");
	}

	size_t use_size = std::min(pixel_size, file_body_size);
	print(string("use_size: ") + std::to_string(use_size) + " (0x" + hex(use_size) + ")");

	//// RLE encode
	std::vector<u8> outdata(gsrle::HEADER_SIZE + use_size * 2); // double size
	const u8* dst_end = gsrle::rleEncode(
		 &data[0] + gsrle::HEADER_SIZE, &data[0] + gsrle::HEADER_SIZE + use_size,
		 &outdata[0] + gsrle::HEADER_SIZE, &outdata[0] + gsrle::HEADER_SIZE + use_size);
	size_t encoded_size = dst_end ? dst_end - &outdata[gsrle::HEADER_SIZE] : 0;
	print(string("encoded size: ") + std::to_string(encoded_size));

	// 圧縮後の方が大きくなったら元のベタデータを書き出す
	bool use_compressed =  (encoded_size && (encoded_size < use_size));
	if (!use_compressed)
	{
		print(string("[CAUTION] original size < compressed size "));
		print(string("--> use no compressed data. "));
	}

	//// set outdata
	gsrle::BsaveHeader outHeader = header;
	if (use_compressed)
	{
		// compressed graph saurus image
		output_gs_file = true;
		outHeader.type_id = gsrle::HEAD_ID_COMPRESS;
		outHeader.end_address = encoded_size; // this entry is size (not end-address)
	}
	else
	if (output_gs_file) // graph saurus file
	{
		// non-compressed graph saurus image
		outHeader.type_id = gsrle::HEAD_ID_LINEAR;
		outHeader.end_address = use_size; // this entry is size (not end-address)
	}
	outdata[0] = outHeader.type_id;
	outdata[1] = outHeader.start_address & 255;
	outdata[2] = outHeader.start_address >> 8;
	outdata[3] = outHeader.end_address & 255;
	outdata[4] = outHeader.end_address >> 8;
	outdata[5] = outHeader.run_address & 255;
	outdata[6] = outHeader.run_address >> 8;

	print(string("--- out file ---"));
	print(string("type_id = ") + hex(outHeader.type_id));
	print(string("start_address = ") + hex(outHeader.start_address));
	if (output_gs_file) // graph saurus file
	{
		print(string("data_size = ") + hex(outHeader.end_address));
	}
	else
	{
		print(string("end_address = ") + hex(outHeader.end_address));
	}
	print(string("run_address = ") + hex(outHeader.run_address));
	print(string("----------------"));

	if (!use_compressed)
	{
		// writeback original pixels
		std::copy( 
			data.begin() + gsrle::HEADER_SIZE,
			data.begin() + std::min(data.size(), outdata.size()),
			outdata.begin() + gsrle::HEADER_SIZE
			);
	}
	else
	{
		outdata.resize(encoded_size + gsrle::HEADER_SIZE);
	}
	print(string("in_file size = ") + std::to_string(data.size()));
	print(string("out_file size = ") + std::to_string(outdata.size()));

	//// write outfile
	FILE* outfile;
	err_no = fopen_s( &outfile, outFileName.c_str(), "wb");
	if (err_no != 0)
	{
		print(string("[ERROR] file can not open. \"") + outFileName + "\"");
		if (!silent_mode)   std::cin.get();
		return 1; // error end
	}
	size_t w = fwrite( &outdata[0], 1, outdata.size(), outfile);
	if (w != outdata.size())
	{
		print(string("[ERROR] file can not open. \"") + outFileName + "\"");
		if (!silent_mode)   std::cin.get();
		return 1; // error end
	}
	fclose(outfile);
	outfile = nullptr;

	//// write palette file
	if (output_pal_file)// && (!extd->gs_type) && (extd->screen_no < 8))
	{
		if (pixel_end_with_pal >= org_size)
		{
			print(string("[CAUTION] can't output palette file. (not enough data size)"));
			output_pal_file = false;
		}
		if ((!force_output_pal_file) && (pixel_size > pixel_end_256))
		{
			print(string("[INFO] skip output palette file. (It seems over 256line data)"));
			output_pal_file = false;
		}
	}
	if (output_pal_file)
	{
		print(string("---------------------"));
		print(string("-- palette file --"));
		fs::path pltPath(outFileName);
		pltPath.replace_extension(".PL"+hex(extd->screen_no));
		string plt_outFileName = pltPath.generic_string();
		print(string("output: ") + plt_outFileName);

		int pal_ofs = pal_adr + gsrle::HEADER_SIZE;
		
		const int plt_entry = 2;
		const int plt_num = 16;
		const int plt_track_num = 8;
		std::vector<u8> paldata(plt_track_num * plt_num * plt_entry);

		for (int i = 0; i < plt_track_num; ++i)
		{
			std::copy(
				data.begin() + pal_ofs,
				data.begin() + pal_ofs + plt_num * plt_entry,
				paldata.begin() + i * plt_num * plt_entry);
		}
		//// write palette outfile
		FILE* palfile;
		errno_t err_no = fopen_s( &palfile, plt_outFileName.c_str(), "wb");
		if (err_no != 0)
		{
			print(string("[ERROR] file can not open. \"") + plt_outFileName + "\"");
			if (!silent_mode)   std::cin.get();
			return 1; // error end
		}
		size_t w = fwrite( &paldata[0], 1, paldata.size(), palfile);
		if (w != paldata.size())
		{
			print(string("[ERROR] file can not open. \"") + plt_outFileName + "\"");
			if (!silent_mode)   std::cin.get();
			return 1; // error end
		}
		fclose(palfile);
		palfile = nullptr;
	}
	//// end
	print(string("-- end --"));
	if (!silent_mode) 
	{
		print(string("hit enter key"));
		std::cin.get();
	}
	return 0;;
}

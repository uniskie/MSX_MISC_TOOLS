#ifndef __UNI_COMMON_H__
#define __UNI_COMMON_H__

#include <sstream>
#include <stdio.h>
#include <iostream>
//#include <fstream>
#include <string>
#include <filesystem> // need c++17
#include <algorithm>

//===============================================
// cheat
// common.h
#define countof(x) (sizeof(x)/sizeof(x[0]))
namespace fs = std::filesystem;
typedef std::string     string;
typedef std::wstring    wstring;
typedef uint64_t        u64;
typedef uint32_t        u32;
typedef uint16_t        u16;
typedef uint8_t         u8;
typedef int64_t         s64;
typedef int32_t         s32;
typedef int16_t         s16;
typedef int8_t          s8;

#ifdef _DEBUG
#define ASSERT      _ASSERT
//#define TRACE(...)  fprintf(stderr,__VA_ARGS__)
#define TRACE(S)	  print_error(S, false);
#else
#define ASSERT(...) 
#define TRACE(...)  
#endif

namespace uni_common {
string align_right(string s, u64 i);
string align_left(string s, u64 i);
string float_str(float i, int align = 0, int precision = 0, string space = " ");
string dec(s64 i, int align = 0, string space = " ");
string hex(u64 i, int align = 0, string space = "0");
string get_lower(const string& s);
string get_upper(const string& s);

int print(string s, bool add_cr = true);
int print_log(string s, bool add_cr = true);
int print_error(string s, bool add_cr = true);

FILE* set_log_file(FILE* f);
int close_log_file();
} // namespace uni_common
//===============================================

#endif //#ifndef __UNI_COMMON_H__

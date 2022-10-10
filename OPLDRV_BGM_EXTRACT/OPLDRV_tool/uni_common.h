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
#define TRACE(...)  fprintf(stderr,__VA_ARGS__)
#else
#define ASSERT(...) 
#define TRACE(...)  
#endif

string align_right(string s, u64 i);
string align_left(string s, u64 i);
string decimal(u64 i);
string hex(u64 i);
string get_lower(const string& s);
string get_upper(const string& s);

int print(string s);
int print_log(string s);
int print_error(string s);

FILE* set_log_file(FILE* f);

//===============================================

#endif //#ifndef __UNI_COMMON_H__

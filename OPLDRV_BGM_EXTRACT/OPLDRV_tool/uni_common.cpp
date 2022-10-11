#include "uni_common.h"

string align_right(string s, u64 i)
{
    std::stringstream ss;
    ss << std::setw(i) << s;
    return ss.str();
}
string align_left(string s, u64 i)
{
    std::stringstream ss;
    ss << std::left << std::setw(i) << s;
    return ss.str();
}
string decimal(s64 i, int align, string space)
{
    std::stringstream ss;
    if (0 == align)
    {
        ss << std::dec << i;
    }
    else
    {
        ss << std::right << std::setw(align) << std::setfill(space.at(0))
            << std::dec << i;
    }
    return ss.str();
}
string hex(u64 i, int align, string space)
{
    std::stringstream ss;
    if (0 == align)
    {
        ss << std::hex << i;
    }
    else
    {
        ss << std::right << std::setw(align) << std::setfill(space.at(0))
            << std::hex << i;
    }
    return ss.str();
}

string get_lower(const string& s)
{
    string d;
    d.resize(s.size());
    std::transform(s.begin(), s.end(), d.begin(), tolower);
    return d;
}

string get_upper(const string& s)
{
    string d;
    d.resize(s.size());
    std::transform(s.begin(), s.end(), d.begin(), toupper);
    return d;
}

FILE* log_file = nullptr;

int print(string s)
{
    if (log_file)
    {
        fprintf(log_file, (s + "\n").c_str());
    }
    return printf((s + "\n").c_str());
}
FILE* set_log_file(FILE* f)
{
    auto old = log_file;
    log_file = f;
    return old;
}

int print_log(string s)
{
    if (log_file)
    {
        return fprintf(log_file, (s + "\n").c_str());
    }
    return printf((s + "\n").c_str());
}

int print_error(string s)
{
    if (log_file)
    {
        fprintf(log_file, (s + "\n").c_str());
    }
    return fprintf(stderr, (s + "\n").c_str());
}


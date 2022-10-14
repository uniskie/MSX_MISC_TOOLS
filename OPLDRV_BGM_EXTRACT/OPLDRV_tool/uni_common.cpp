#include "uni_common.h"

namespace uni_common {

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
string double_str(double i, int align, int precision, string space)
{
    std::stringstream ss;
    if (0 == align)
    {
        ss << i;
    }
    else
    {
        ss << std::right << std::setw(align)
            << std::setfill(space.at(0))
            << std::fixed << std::setprecision(precision)
            << i;
    }
    return ss.str();
}
string float_str(float i, int align, int precision, string space)
{
    std::stringstream ss;
    if (0 == align)
    {
        ss << i;
    }
    else
    {
        ss << std::right << std::setw(align)
            << std::setfill(space.at(0))
            << std::fixed << std::setprecision(precision)
            << i;
    }
    return ss.str();
}
string dec(s64 i, int align, string space)
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
std::stringstream log_stream;

FILE* set_log_file(FILE* f)
{
    auto old = log_file;
    log_file = f;
    if (f)
    {
        size_t size = log_stream.tellp();
        if (0 < size)
        {
            fprintf(log_file, log_stream.str().c_str());
            log_stream.clear();
        }
    }
    return old;
}
int close_log_file()
{
    if (log_file)
    {
        return fclose(log_file);
    }
    return 0;
}

int print(string s, bool add_cr)
{
    if (add_cr) s += "\n";
    if (log_file)
    {
        fprintf(log_file, s.c_str());
    }
    else
    {
        log_stream << s;
    }
    return printf(s.c_str());
}

int print_log(string s, bool add_cr)
{
    if (add_cr) s += "\n";
    if (log_file)
    {
        return fprintf(log_file, s.c_str());
    }
    else
    {
        log_stream << s;
    }
    return printf(s.c_str());
}

int print_error(string s, bool add_cr)
{
    if (add_cr) s += "\n";
    if (log_file)
    {
        fprintf(log_file, s.c_str());
    }
    else
    {
        log_stream << s;
    }
    return fprintf(stderr, s.c_str());
}

} //namespace uni_common 

#!env python
import sys
import array
import os
#import Enum

# for Python 3.4.5
# 
# extract files in MSX cas file
#

infilename = 'test.cas' # sys.argv[1]
if (len(sys.argv) > 1):
    if (len(sys.argv[1]) > 0):
        infilename = sys.argv[1]
        print(sys.argv[1])
outdir = os.path.splitext(os.path.basename(infilename))[0] + os.path.sep # sys.argv[2]
if (len(sys.argv) > 2):
    if (len(sys.argv[2]) > 0):
        outdir = sys.argv[2]
        print(sys.argv[2])
outfilename = outdir
print(outdir)
print(os.getcwd())
#i=input()

os.makedirs(outdir, exist_ok=True)

seek_header=b'\x1F\xA6\xDE\xBA\xCC\x13\x7D\x74'
bas_header=b'\xD3\xD3\xD3\xD3\xD3\xD3\xD3\xD3\xD3\xD3'
bin_header=b'\xD0\xD0\xD0\xD0\xD0\xD0\xD0\xD0\xD0\xD0'
asc_header=b'\xEA\xEA\xEA\xEA\xEA\xEA\xEA\xEA\xEA\xEA'
bas_footer=b'\xFF\x00\x00\x00\x00\x00\x00\x00'
bin_footer=b'\xFE\x00\x00\x00\x00\x00\x00\x00'
class DType: # (Enum)
    UNKNOWN = 0
    BAS = 1
    BIN = 2
    ASC = 3
    CUSTOM = 4
dtype_name = ['UNKNOWN', 'BASIC ', 'BINARY', 'ASCII ', 'CUSTOM']
dtype_str = ['UNKNOWN', 'BAS', 'BIN', 'ASC', 'DAT']

def read_block(data, f, outbuf):
    f = data.find(seek_header, f)
    if (f < 0):
        return 0
    f = f + len(seek_header)
    n = data.find(seek_header, f)
    if (n < 0):
        n = len(data)
    outbuf[:] = data[f:n]
    #print(str(f) + ' - ' + str(n))
    return n-f

infile = open(infilename, 'rb')
data = infile.read()
print('in_file size = ' + str(len(data)))

is_loop = True
f = 0
fhpos = 0
file_no = 0
custom_no = 0

while is_loop:
    fhpos = f

    dtype = DType.UNKNOWN
    headdata = bytearray()
    s = read_block(data, f, headdata)
    if (s < 1):
        break
    f = f + s + len(seek_header)

    outname = ''
    #outname = str(file_no) + '_'
    outdata = bytearray()
    print(s)
    if (s == 24):
        #print('s==24')
        #print('footer:' + ''.join(r'%02X' % x for x in headdata[16:24]))
        if ((headdata[0:10] == bas_header) and (headdata[16:24] == bas_footer)):
            #print('header:' + ''.join(r'%02X' % x for x in headdata[0:10]))
            outname = headdata[10:16].decode('sjis', 'replace')
            dtype = DType.BAS
            outdata.extend(b'\xFF') # File Header for DISK
        elif ((headdata[0:10] == bin_header) and (headdata[16:24] == bin_footer)):
            #print('header:' + ''.join(r'%02X' % x for x in headdata[0:10]))
            outname = headdata[10:16].decode('sjis', 'replace')
            dtype = DType.BIN
            outdata.extend(b'\xFE') # File Header for DISK
    elif (s == 16):
        if (headdata[0:10] == bas_header):
            #print('header:' + ''.join(r'%02X' % x for x in headdata[0:10]))
            outname = headdata[10:16].decode('sjis', 'replace')
            dtype = DType.BAS
            outdata.extend(b'\xFF') # File Header for DISK
        elif (headdata[0:10] == bin_header):
            #print('header:' + ''.join(r'%02X' % x for x in headdata[0:10]))
            outname = headdata[10:16].decode('sjis', 'replace')
            dtype = DType.BIN
            outdata.extend(b'\xFE') # File Header for DISK
        elif (headdata[0:10] == asc_header):
            #print('header:' + ''.join(r'%02X' % x for x in headdata[0:10]))
            outname = headdata[10:16].decode('sjis', 'replace')
            dtype = DType.ASC
    if (dtype == DType.UNKNOWN):
        dtype = DType.CUSTOM
        outname = 'custom_' + str(custom_no)
        custom_no = custom_no + 1

    outname_t = outname + '.' + dtype_str[dtype]
    f_num = 1
    while (os.path.isfile(outfilename + outname_t)):
    	outname_t = outname + '_#{:04X}.'.format(f_num) + dtype_str[dtype]
    	f_num = f_num + 1
    outname = outname_t

    #print(str(fhpos) + ': ', end='')
    print(format(fhpos, '08x') + ': ', end='')
    print(format(file_no, '02d') + ': ' + dtype_name[dtype] + ': ', end='')
    print('"' + outname + '"', end='')
    
    if (dtype == DType.UNKNOWN):
        print('[error]')
        continue
    if (dtype == DType.CUSTOM):
        outdata.extend(headdata)
        eofpos = f
    else:
        while True:
            tmpdata = bytearray()
            s = read_block(data, f, tmpdata)
            f = f + s + len(seek_header)
            if (dtype == DType.BAS):
                outdata.extend(tmpdata)
                eofpos = f
                break
            elif (dtype == DType.BIN):
                sp = int.from_bytes(tmpdata[0:2], byteorder='little')
                ep = int.from_bytes(tmpdata[2:4], byteorder='little')
                xp = int.from_bytes(tmpdata[4:6], byteorder='little')
                rsize = ep - sp + 6 + 1 # add bin header size
                print(' START=' + format(sp, '04X'), end='')
                print('/END=' + format(ep, '04X'), end='')
                print('/EXEC=' + format(xp, '04X'), end='')
                outdata.extend(tmpdata[0:rsize])
                eofpos = (f - s) + rsize
                break
            eofpos = tmpdata.find(b'\x1A')
            if (eofpos >= 0):
                eofpos = eofpos + 1 # add eof
                outdata.extend(tmpdata[0:eofpos])
                eofpos = (f - s) + eofpos;
                break
            outdata.extend(tmpdata)
    print(' (size = ' + str(eofpos - fhpos) + ')')
    outfile = open(outfilename + outname, 'wb')
    outfile.write(outdata)
    outfile.close()

    file_no = file_no + 1

    if (file_no > 20):
        break

infile.close()

print('-- end -- hit enter key') 
i=input()


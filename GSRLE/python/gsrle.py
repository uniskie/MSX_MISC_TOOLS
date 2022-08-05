#!env python
from ast import Bytes
from itertools import groupby
import sys
import os
import struct

#DEFAULT_INPUTFILENAME = '../test/TEST.SC7'
#DEFAULT_INPUTFILENAME = '../test/BIKINI.SC8'
DEFAULT_INPUTFILENAME = '../test/JTHUNDER.SRC'


# for Python 3.4.5
# 
# GRAPH SAURUS'S COMPRESSION (GS RLE)
#

#===============================================
# CONSTAMTS
#===============================================
HEAD_ID_LINEAR   = 0xFE # BSAVE/GS LINEAR
HEAD_ID_COMPRESS = 0xFD #GS RLE COMPLESS
HEAD_FORMAT = '<BHHH'
BSAVE_LIMIT = 65535

## BSAVE END END ADDRESS LIMIT
def cap_bsave_address(adr :int):
    if (adr > BSAVE_LIMIT):
        adr = BSAVE_LIMIT
    return adr

#===============================================
# FILE EXTENSION INFO
#===============================================
class ExtInfo:
    def __init__(self, screen_no: int, interlace: int, gs_type: int, bsave_ext: str, gs_ext: str):
        self.screen_no = screen_no  #スクリーンモード
        self.interlace = interlace  #インターレースモード
        self.gs_type   = gs_type    #グラフサウルス形式（パレットファイル別、最終アドレスはアドレスではなくサイズ)
        self.bsave_ext = bsave_ext  #BSAVE拡張子
        self.gs_ext    = gs_ext     #GRAPH SAURUS拡張子
EXT_INFO_LIST = {
    '.SC2': ExtInfo( 2,0,0,'.SC2','.SR2'),  '.SR2': ExtInfo( 2,0,1,'.SC2','.SR2'),
    '.SC3': ExtInfo( 3,0,0,'.SC3','.SR4'),  '.SR4': ExtInfo( 3,0,1,'.SC3','.SR4'),
    '.SC4': ExtInfo( 4,0,0,'.SC4','.SR3'),  '.SR3': ExtInfo( 4,0,1,'.SC4','.SR3'),
    '.SC5': ExtInfo( 5,0,0,'.SC5','.SR5'),  '.SR5': ExtInfo( 5,0,1,'.SC5','.SR5'),
    '.SC7': ExtInfo( 7,0,0,'.SC7','.SR7'),  '.SR7': ExtInfo( 7,0,1,'.SC7','.SR7'),
    '.SC8': ExtInfo( 8,0,0,'.SC8','.SR8'),  '.SR8': ExtInfo( 8,0,1,'.SC8','.SR8'),
    '.S10': ExtInfo(10,0,0,'.S10','.SRA'),  '.SRA': ExtInfo(10,0,0,'.S10','.SRA'),
    '.S12': ExtInfo(12,0,0,'.S12','.SRC'),  '.SRC': ExtInfo(12,0,0,'.S12','.SRC'),
                                            '.SRS': ExtInfo(12,0,1,'.S12','.SRS'),

    '.S50': ExtInfo( 5,3,0,'.S50','.R50'),  '.S51': ExtInfo( 5,3,0,'.S51','.R51'),
    '.S70': ExtInfo( 7,3,0,'.S70','.R70'),  '.S71': ExtInfo( 7,3,0,'.S71','.R71'),
    '.S80': ExtInfo( 8,3,0,'.S80','.R80'),  '.S81': ExtInfo( 8,3,0,'.S81','.R81'),
    '.SA0': ExtInfo(10,3,0,'.SA0','.RA0'),  '.SA1': ExtInfo(10,3,0,'.SA1','.RA1'),
    '.SC0': ExtInfo(12,3,0,'.SC0','.RC0'),  '.SC1': ExtInfo(12,3,0,'.SC1','.RC1'),

    '.R50': ExtInfo( 5,3,1,'.S50','.R50'),  '.R51': ExtInfo( 5,3,1,'.S51','.R51'),
    '.R70': ExtInfo( 7,3,1,'.S70','.R70'),  '.R71': ExtInfo( 7,3,1,'.S71','.R71'),
    '.R80': ExtInfo( 8,3,1,'.S80','.R80'),  '.R81': ExtInfo( 8,3,1,'.S81','.R81'),
    '.RA0': ExtInfo(10,3,1,'.SA0','.RA0'),  '.RA1': ExtInfo(10,3,1,'.SA1','.RA1'),
    '.RC0': ExtInfo(12,3,1,'.SC0','.RC0'),  '.RC1': ExtInfo(12,3,1,'.SC1','.RC1'),
}
def get_ext_data(org_path: str):
    bname,ext= os.path.splitext(org_path)
    if ext:
        return ext, EXT_INFO_LIST[ext.upper()]
    return ext, ExtInfo(0,0,0,'')

#===============================================
# VRAM PALETTE TABLE ADDRESS
#===============================================
PAL_TABLE_LIST = [
    #SCREEN0:WIDTH40,SCREEN0:WIDTH80,SCREEN1,SCREEN2,SCREEN3,
    0x0400,0x0F00,0x2020,0x1B80,0x2020,
    #SCREEN4,SCREEN5,SCREEN6,SCREEN7,SCREEN8,
    0x1B80,0x7680,0x7680,0xFA80,0xFA80,
    #SCREEN9,SCREEN10,SCREEN11,SCREEN12
    0x7680,0xFA80,0xFA80,0xFA80
]
def get_pal_table(screen_no: int):
    s = screen_no + 1
    if ((s<-1) or (s>=len(PAL_TABLE_LIST))):
        return -1
    return PAL_TABLE_LIST[s]

#===============================================
# SCREEN VRAM END ADDRESS
#===============================================
END_ADDRESS_LIST_WITH_PALETTE = [
    #SCREEN0:WIDTH40,SCREEN0:WIDTH80,SCREEN1,SCREEN2,SCREEN3,
    0x0FFF,0x17FF,0x37FF,0x37FF,0x203F,
    #SCREEN4,SCREEN5,SCREEN6,SCREEN7,SCREEN8,
    0x37FF,0x769F,0x769F,0xFA9F,0xFA9F,
    #SCREEN9,SCREEN10,SCREEN11,SCREEN12
    0x769F,0xFA9F,0xFA9F,0xFA9F
]
END_ADDRESS_LIST_PIXEL = [
    #SCREEN0:WIDTH40,SCREEN0:WIDTH80,SCREEN1,SCREEN2,SCREEN3,
    0x0FFF,0x17FF,0x37FF,0x37FF,0x37FF,
    #SCREEN4,SCREEN5,SCREEN6,SCREEN7,SCREEN8,
    0x37FF,0x69FF,0x69FF,0xD3FF,0xD3FF,
    #SCREEN9,SCREEN10,SCREEN11,SCREEN12
    0x69FF,0xD3FF,0xD3FF,0xD3FF
]
END_ADDRESS_LIST_PIXEL_MAX = [
    #SCREEN0:WIDTH40,SCREEN0:WIDTH80,SCREEN1,SCREEN2,SCREEN3,
    0x0FFF,0x17FF,0x37FF,0x37FF,0x37FF,
    #SCREEN4,SCREEN5,SCREEN6,SCREEN7,SCREEN8,
    0x37FF,0x7FFF,0x7FFF,0xFFFF,0xFFFF,
    #SCREEN9,SCREEN10,SCREEN11,SCREEN12
    0x7FFF,0xFFFF,0xFFFF,0xFFFF
]
def get_end_address_with_pal(screen_no: int):
    s = screen_no+1
    table = END_ADDRESS_LIST_WITH_PALETTE
    if ((s<0) or (s>=len(table))):
        return -1
    return table[s]
def get_end_address_y212(screen_no: int):
    s = screen_no+1
    table = END_ADDRESS_LIST_PIXEL
    if ((s<0) or (s>=len(table))):
        return -1
    return table[s]
def get_end_address_y255(screen_no: int):
    s = screen_no+1
    table = END_ADDRESS_LIST_PIXEL_MAX
    if ((s<0) or (s>=len(table))):
        return -1
    return table[s]

#===============================================
# Run Length Encode
#===============================================
def rle_tupple(dat: bytes) -> "list[tuple(bytes, int)]":
    grouped = groupby(dat)
    res = []
    for b, l in grouped:
        #print('"' + str(b) + '" * ' + str(len(list(l))))
        res.append((b, int(len(list(l)))))
    return res

def rleEncode(dat: bytes) -> "bytearray":
    compressed = rle_tupple(dat)
    res = bytearray()
    res = []
    for b, n in compressed:
        while (n > 0):
            if (n>255):
                res.append(0)
                res.append(255)
                res.append(b)
                n-=255
            elif(n >= 16):
                res.append(0)
                res.append(n)
                res.append(b)
                n-=n;
            elif (n > 2) or (b < 16):
                res.append(n)
                res.append(b)
                n-=n;
            else:
                res.append(b)
                n-=1;
    return res

#===============================================
# main
#===============================================

## setting
output_gs_file = True # output GRAPH SAURUS FILE
output_pixel_height = 212
silent_mode = False

## parse arguments
argi = 1

## silent mode ?
if (len(sys.argv) > argi):
    if (len(sys.argv[argi]) > 0):
        if (sys.argv[argi].lower()=='/s'):
            silent_mode = True
            print('silent option: ' + sys.argv[argi])
            argi += 1

## decide input file path
inFileName = DEFAULT_INPUTFILENAME # sys.argv[1]
if (len(sys.argv) > argi):
    if (len(sys.argv[argi]) > 0):
        inFileName = sys.argv[argi]
        print('arg:' + sys.argv[argi])
        argi += 1

print('inFileName:' + inFileName)

ext, d = get_ext_data(inFileName)
print('screen no: ' + str(d.screen_no))

## decide output file path
outFileName = os.path.splitext(inFileName)[0] + d.gs_ext # sys.argv[2]

if (d.screen_no == 0):
    print('[ERROR] This file is not support type "' + ext + '"')
    print(d)
    if not silent_mode:
        i=input()
    sys.exit(1) # error end

#if (len(sys.argv) > argi):
#    if (len(sys.argv[argi]) > 0):
#        outFileName = sys.argv[argi]
#        print('outFineName arg: ' + sys.argv[argi])
#        argi += 1

print('outFileName' + outFileName)
print('os.getcwd():' + os.getcwd())
#i=input()

## read file

infile = open(inFileName, 'rb')
data = infile.read()
infile.close()
print('in_file size = ' + str(len(data)))

## get file Header infomation
head_size = len(struct.pack(HEAD_FORMAT,0,0,0,0))
body_size = len(data) - head_size;
if (body_size < 0):
    print('[ERROR] Not enough file size.')
    if not silent_mode:
        i=input()
    sys.exit(1) # error end

type_id, start_address, end_address, run_address = struct.unpack(HEAD_FORMAT, data[0:head_size])
print('--- source file ---')
print('type_id = ' + hex(type_id))
print('start_address = ' + hex(start_address))
print('end_address = ' + hex(end_address))
print('run_address = ' + hex(run_address))
print('----------------')

org_size = end_address - start_address + 1
#if (d.gs_type):
#    org_size = end_address - start_address
if (body_size < org_size):
    org_size = body_size
    end_address = org_size - start_address - 1
    print('*modify end_address = ' + hex(end_address))
print('data_size: ' + str(org_size))

if ((org_size<1) or (type_id != HEAD_ID_LINEAR)):
    print('not support type. (already compressed, or missing type)')
    if not silent_mode:
        i=input()
    sys.exit(1)
print('----------------')

## calc size to be compressed 
# get pixel size
if (output_pixel_height==212):
    pixel_size = get_end_address_y212(d.screen_no)
elif (output_pixel_height==255):
    pixel_size = get_end_address_y255(d.screen_no)
else:
    pixel_size = get_end_address_with_pal(d.screen_no)
pixel_size += 1
print('need_pixel_size: ' + str(pixel_size))

# expand data to pixelsize
if (pixel_size > org_size):
    data2 = bytearray(data) + b'\x00' * (pixel_size+org_size)
    data = bytes(data2)
    org_size = body_size
    print('(expand source pixel to ' + str(pixel_size))

use_size = min(pixel_size, org_size)
print('use_size: ' + str(use_size))

## RLE encode
compressed = rleEncode(data[head_size:head_size + use_size])
encoded_size = len(compressed)
print('encoded size: ' + str(encoded_size))

## If the size after compression is large,
#  use the data before compression
use_compressed =  (encoded_size < use_size)
if (not use_compressed):
    print('[CAUTION] original size < compressed size ')
    print('--> use no compressed data. ')
print('----------------')

## set outdata
outdata = bytearray()
if (use_compressed):
    type_id = HEAD_ID_COMPRESS
    end_address = start_address + encoded_size - 1
if (output_gs_file and (not d.gs_type)): # BSAVE -> graph saurus file
    end_address+=1 # this entry is size (not end-address)
limited_end_address = cap_bsave_address(end_address)
outdata[:] = struct.pack(HEAD_FORMAT, type_id, start_address, limited_end_address, run_address)

print('--- out file ---')
print('type_id = ' + hex(type_id))
print('start_address = ' + hex(start_address))
if (output_gs_file): # graph saurus file
    print('data_size = ' + hex(end_address))
else:
    print('end_address = ' + hex(end_address))
if (limited_end_address != end_address):
    print('*limited_end_address = ' + hex(limited_end_address))
print('run_address = ' + hex(run_address))
print('----------------')

if (use_compressed):
    outdata[head_size:]=compressed
else:
    outdata[head_size:]=data[head_size:head_size + use_size]

print('in_file size = ' + str(len(data)))
print('out_file size = ' + str(len(outdata)))

## write outfile
outfile = open( outFileName, 'wb')
outfile.write(outdata)
outfile.close()

## palette file
if (not d.gs_type) and (d.screen_no < 8):
    print('---------------------')
    print('-- palette file --')
    plt_outFileName = os.path.splitext(outFileName)[0] + '.PL'+str(d.screen_no)
    print('output: ' + plt_outFileName)

    pal_adr = get_pal_table(d.screen_no)
    print('palette table address: ' + hex(pal_adr))
    pal_ofs = pal_adr + head_size

    plt = bytearray()
    plt[:] = data[pal_ofs:pal_ofs+32] * 8

    ## write palette outfile
    palOutfile = open( plt_outFileName, 'wb')
    palOutfile.write(plt)
    palOutfile.close()
    print('----------------')

## end
print('-- end --')
if not silent_mode:
    print('hit enter key') 
    i=input()

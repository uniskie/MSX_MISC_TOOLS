#!env python
from ast import Bytes
from itertools import groupby
import sys
import os
import struct

#DEFAULT_INPUTFILENAME = '../test/TEST.SC7'
#DEFAULT_INPUTFILENAME = '../test/BIKINI.SC8'
#DEFAULT_INPUTFILENAME = '../test/JTHUNDER.SRC'
#DEFAULT_INPUTFILENAME = "../test/RYUJO256.SC7"
DEFAULT_INPUTFILENAME = ''

# for Python 3.4.5
# 
# GRAPH SAURUS'S COMPRESSION (GS RLE)
#

#===============================================
# show help
#===============================================
def showHelp():
    print("GRAPH SAURUS like RLE ENCODER")
    print("")
    print("GSRLE [/np][/l][/cp][/256][/212][/s][INPUT FILENAME]")
    print("[/o:OUTPUT FILENAME]")
    print("")
    print("/s      Slient mode. (no input wait)")
    print("/bh     Use BSAVE header address range.")
    print("        (Default : use file size)")
    print("/cp     Force output size : to palette table.")
    print("/212    Force output size : to line 212.")
    print("/256    Force output size : to line 256.")
    print("/np     No output palette(pl?) file.")
    print("/fp     Force output palette(pl?) file")
    print("        (at over 256 line data).")
    print("/fp     Force output palette(pl?) file.")
    print("/l      Do not overwrite input file.")
    print("")

#===============================================
# CONSTAMTS
#===============================================
HEAD_ID_LINEAR   = 0xFE # BSAVE/GS LINEAR
HEAD_ID_COMPRESS = 0xFD # GS RLE COMPLESS
HEAD_FORMAT = '<BHHH'
BSAVE_END_LIMIT = 0xFFFE
HEAD_END_LIMIT = 0xFFFF

## BSAVE END END ADDRESS LIMIT
def cap_bsave_address(adr :int):
    if (adr > BSAVE_END_LIMIT):
        adr = BSAVE_END_LIMIT
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
def get_end_address_y256(screen_no: int):
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
                n-=n
            elif (n > 2) or (b < 16):
                res.append(n)
                res.append(b)
                n-=n
            else:
                res.append(b)
                n-=1
    return res

#===============================================
# main
#===============================================

## setting
output_pixel_height = 0	# 指定したラインまでのVRAMを出力する
out_put_pixel_to_vram_pal_table = False	# パレットテーブルの位置までのVRAMを出力する
output_gs_file = True # GRAPH SAURUS形式で書き出す
silent_mode = False #!< キー入力待ちをしない
protect_infile = False #!< 元ファイルへの上書きを禁止する
output_pal_file = True #!< パレットファイルを出力する(条件を満たす場合)
force_output_pal_file = False #!< パレットファイルを強制出力
use_bsave_header_address = False #!< BSAVEヘッダの開始アドレス～終了アドレスの範囲を対象にする

inFileName = DEFAULT_INPUTFILENAME
outFileNameReq = ""

## parse arguments
argi = 1
filename_arg_step = 0

arg_error = False

while (argi < len(sys.argv)):
    arg = sys.argv[argi]
    if (len(arg)):
        l = arg.lower()

        ## arg: no output pal file
        if (l == "/np"):
            output_pal_file = False
            print("arg: no output pal file: " + arg)
        ## arg: force output pal file
        elif (l == "/fp"):
            force_output_pal_file = True
            print("arg: force output pal file: " + arg)
        ## arg: protect input file
        elif (l == "/l"):
            protect_infile = True
            print("arg: protect input file : " + arg)
        ## arg: force include palette
        elif (l == "/cp"):
            out_put_pixel_to_vram_pal_table = True
            print("arg: clip size = force include palette : " + arg)
        ## arg: force 255 line
        elif (l == "/256"):
            output_pixel_height = 256
            print("arg: clip size = force 256 line : " + arg)
        ## arg: force 212 line
        elif (l == "/212"):
            output_pixel_height =212
            print("arg: clip size = force 212 line : " + arg)
        ## arg: use BSABE header address
        elif (l == "/bh"):
            use_bsave_header_address = True
            print("arg: Use BSAVE header size specification : " + arg)
        ## arg: silent mode
        elif (l == "/s"):
            silent_mode = True
            print("arg: silent mode : " + arg)
        ## arg: inFileName
        elif (filename_arg_step == 0):
            inFileName = arg
            print("arg: inFIlename : " + arg)
            filename_arg_step += 1
        ## arg: outFilename
        elif (l.substr(0,3) == "/o:"):
            if (filename_arg_step == 1):
                outFileNameReq = arg.substr(3)
                print("arg: outFileName : " + arg)
                filename_arg_step += 1
            else:
                print("arg: outFileName already specified. " + arg)
                arg_error = True
        else:
            print("arg: [unknown arg] : " + arg)
            arg_error = True
    argi += 1

if (arg_error or (not len(inFileName))):
    if (arg_error):
        print("[ERROR] argument error.")
    showHelp()
    if not silent_mode:
        i=input()
    sys.exit(1) # error end

print('inFileName:' + inFileName)
ext, extd = get_ext_data(inFileName)
if (extd.screen_no == 0):
    print('[ERROR] This file is not support type "' + ext + '"')
    if not silent_mode:
        i=input()
    sys.exit(1) # error end
print('screen no: ' + str(extd.screen_no))

pal_adr = get_pal_table(extd.screen_no)
print("palette table address: " + hex(pal_adr))

pixel_end_212 = get_end_address_y212(extd.screen_no)
pixel_end_256 = get_end_address_y256(extd.screen_no)
pixel_end_with_pal = get_end_address_with_pal(extd.screen_no)
print("pixel end address (line 212)    : " + hex(pixel_end_212))
print("pixel end address (line 256)    : " + hex(pixel_end_256))
print("pixel end address (with palette): " + hex(pixel_end_with_pal))

## decide output file path
outFileName = os.path.splitext(inFileName)[0] + extd.gs_ext # sys.argv[2]
if (len(outFileNameReq)):
    outFileName = outFileNameReq
print('outFileName' + outFileName)
print('os.getcwd():' + os.getcwd())
#i=input()

# 上書きかどうか調べる
if (inFileName == outFileName):
    print("[overwrite source file] " + outFileName + " -> " + outFileName)
    if (protect_infile):
        # 上書き禁止
        print("[ERROR] Overwriting the original file is prohibited.")
        if not silent_mode:
            i=input()
        sys.exit(1) # error end

## read file

infile = open(inFileName, 'rb')
data = infile.read()
infile.close()
print('in_file size = ' + str(len(data)))

## get file Header infomation
HEADER_SIZE = len(struct.pack(HEAD_FORMAT,0,0,0,0))
body_size = len(data) - HEADER_SIZE
if (body_size < 0):
    print('[ERROR] Not enough file size.')
    if not silent_mode:
        i=input()
    sys.exit(1) # error end

## get file Header infomation
type_id, start_address, end_address, run_address = struct.unpack(HEAD_FORMAT, data[0:HEADER_SIZE])
print('--- source file ---')
print('type_id = ' + hex(type_id))
print('start_address = ' + hex(start_address))
print('end_address = ' + hex(end_address))
print('run_address = ' + hex(run_address))
print('----------------')

# ピクセルデータサイズ
#  = ヘッダ以降のサイズ
org_size = body_size
if (not use_bsave_header_address):
    print("data_size (from file size) : " + str(org_size))
else:
    # ピクセルデータサイズをファイルサイズからではなくヘッダから決定する
    #  色々ややこしいので使わない方がいい。
    # ピクセルデータサイズ
    # 0の場合は0x10000とみなす
    if (end_address):
        org_size = end_address
    else:
        org_size = 0x10000
    if (type_id == HEAD_ID_COMPRESS):
        # GS COMPRESS type
        # GS圧縮形式は
        # 開始アドレス, データサイズ, 0

        # そのまま
        org_size = org_size
    else:
        # BSAVE形式は
        # 開始アドレス, 終了アドレス, 0
        # GSベタ形式は
        # 開始アドレス, データサイズ, 0
        # 
        # 中身が判定できないので簡易的に偶数丸め込み。
        #
        # ※ GSベタの場合は開始0固定前提で処理するため、
        #    もし、開始アドレスが0以外のデータがあっても非対応。
        #    (見たことはない)

        # BSAVE制限ぎりぎりであれば0xFFFFとして扱う
        if (org_size == (BSAVE_END_LIMIT)):
            org_size = HEAD_END_LIMIT

        org_size = org_size - start_address + 1 #BSAVE type
        org_size &= 0xFFFFFFe #偶数丸め込み
    
    print("data_size (from Header): " + str(org_size))


if ((org_size < 1) or (type_id != HEAD_ID_LINEAR)):
    print('not support type. (already compressed, or missing type)')
    if not silent_mode:
        i=input()
    sys.exit(1)
print('----------------')

## 圧縮対象のサイズを決定
pixel_size = 0
if (output_pixel_height==212):
    pixel_size = pixel_end_212 + 1
elif (output_pixel_height==256):
    pixel_size = pixel_end_256 + 1
elif (out_put_pixel_to_vram_pal_table):
    pixel_size = pixel_end_with_pal + 1
else: # そのまま
    pixel_size = org_size
print("need_pixel_size: " + str(pixel_size))

# expand data to pixelsize
file_body_size = len(data) - HEADER_SIZE
if (pixel_size > file_body_size):
    data2 = bytearray(data) + b'\x00' * (pixel_size-file_body_size)
    data = bytes(data2)
    file_body_size = len(data) - HEADER_SIZE
    if (file_body_size < pixel_size):
        print("[innner error] file_body_size < pixel_size")
        if not silent_mode:
            i=input()
        sys.exit(1)
    print("(expand source pixel to " + str(file_body_size))

use_size = min(pixel_size, file_body_size)
print('use_size: ' + str(use_size))

## RLE encode
compressed = rleEncode(data[HEADER_SIZE:HEADER_SIZE + use_size])
encoded_size = len(compressed)
print('encoded size: ' + str(encoded_size))

   # 圧縮後の方が大きくなったら元のベタデータを書き出す
use_compressed =  (encoded_size < use_size)
if (not use_compressed):
    print('[CAUTION] original size < compressed size ')
    print('--> use no compressed data. ')
print('----------------')

## set outdata
outdata = bytearray()
if (use_compressed):
    output_gs_file = True
    type_id = HEAD_ID_COMPRESS
    end_address = encoded_size # this entry is size (not end-address)
    limited_end_address = end_address
elif (output_gs_file): # graph saurus file
    # non-compressed graph saurus image
    type_id = HEAD_ID_LINEAR
    end_address = use_size # this entry is size (not end-address)
    limited_end_address = end_address
else:
    limited_end_address = cap_bsave_address(end_address)
outdata[:] = struct.pack(HEAD_FORMAT, type_id, start_address, end_address, run_address)

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
    outdata[HEADER_SIZE:]=compressed
else:
    outdata[HEADER_SIZE:]=data[HEADER_SIZE:HEADER_SIZE + use_size]

print('in_file size = ' + str(len(data)))
print('out_file size = ' + str(len(outdata)))

## write outfile
outfile = open( outFileName, 'wb')
outfile.write(outdata)
outfile.close()

## palette file
if (output_pal_file):
	if (pixel_end_with_pal >= org_size):
		print("[CAUTION] can't output palette file. (not enough data size)")
		output_pal_file = False
	if ((not force_output_pal_file) and (pixel_size > pixel_end_256)):
		print("[INFO] skip output palette file. (It seems over 256line data)")
		output_pal_file = False
if (output_pal_file):
    print('---------------------')
    print('-- palette file --')
    plt_outFileName = os.path.splitext(outFileName)[0] + '.PL'+str(extd.screen_no)
    print('output: ' + plt_outFileName)

    pal_adr = get_pal_table(extd.screen_no)
    print('palette table address: ' + hex(pal_adr))
    pal_ofs = pal_adr + HEADER_SIZE

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

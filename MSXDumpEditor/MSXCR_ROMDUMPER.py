# -*- coding: utf-8 -*-
# MSXCR_ROMDumper.py - MSX Game Catridge Reader Program
# for MSXPLAYer Game Cartridge Adapter
# Purpose: Read ROM data from MSX cartridges via serial communication
# Supports: MegaROM mappers detection and ROM dump
# Copyright @v9938 (Ported to Python by @uniskie with gemini3.5 flash pro)

import os
import sys
import time
import datetime
import hashlib
import csv
import html
import serial
import serial.tools.list_ports

# ============================================================================
# Constants and Defines
# ============================================================================

MIN_FIRMWARE_DATE = 20260531        # SlotAdapterのFirmware要求Version

BANK_SIZE        = 0x2000   # 8K bank size
SLOT_ADDR_BASE   = 0x4000   # Slot base address
HASH_SIZE        = 0x1000   # Hash calculation size
# HASH_SIZE       = 0x1f00  # Hash calculation size
MAX_RESPONSE_LEN = 256
TIMEOUT_MS       = 5000
SRAM_THRESHOLD   = 8        # Number of identical banks to detect SRAM
# DISPLAY_HASH    = True     # Display HASH (C++の #define DISPLAY_HASH 相当)

# MegaROM Mapper Types
MAPPER_UNKNOWN       = 0
MAPPER_ASCII_16K     = 1    # ASCII 16K
MAPPER_ASCII_8K      = 2    # ASCII 8K
MAPPER_KONAMI_8K     = 3    # Konami 8K
MAPPER_KONAMI_SCC    = 4    # Konami SCC
MAPPER_GENERIC_16K   = 5    # Generic 16K
MAPPER_GENERIC_8K    = 6    # Generic 8K
MAPPER_RTYPE         = 7    # R-Type
MAPPER_CROSSBLAM     = 8    # CROSS BLAM
MAPPER_HARRYFOX      = 9    # HARRY FOX
MAPPER_FMPAC         = 10   # FMPAC
MAPPER_HALNOTE       = 11   # Hal Note
MAPPER_NO_MAPPER_8K  = 12   # 8KB no mapper
MAPPER_NO_MAPPER_16K = 13   # 16KB no mapper
MAPPER_NO_MAPPER_32K = 14   # 32KB no mapper
MAPPER_NO_MAPPER_48K = 15   # 48KB no mapper
MAPPER_NO_MAPPER_64K = 16   # 64KB no mapper
MAPPER_TYPE_COUNT    = 17

MEMWAIT = 0             # Memory Read/Write後のWait時間 (n x 10ns)    初期値 0
RDWAIT  = 100           # Memory Read時の/RD信号幅 (n x 10ns)         初期値 100

# ============================================================================
# Utility Functions
# ============================================================================

def GetDirectoryFromPath(path: str) -> str:
    pos = max(path.rfind("\\"), path.rfind("/"))
    if pos == -1:
        return "."
    return path[:pos]


def JoinPath(directory: str, file: str) -> str:
    if not directory:
        return file
    last = directory[-1]
    if last == '\\' or last == '/':
        return directory + file
    return directory + "\\" + file


def DecodeXmlEntities(s: str) -> str:
    # Python標準のhtml.unescapeは&amp;, &lt;, &gt;, &quot;, &apos;や数値参照に対応しています
    return html.unescape(s)


def SanitizeFileName(name: str) -> str:
    out = list(name)
    invalid_chars = "<>:\"/\\|?*"

    for i in range(len(out)):
        if out[i] in invalid_chars or ord(out[i]) < 32:
            out[i] = '_'

    out_str = "".join(out)
    while out_str and (out_str[-1] == ' ' or out_str[-1] == '.'):
        out_str = out_str[:-1]

    if not out_str:
        out_str = "unknown"

    return out_str


# ============================================================================
# SHA-1
# ============================================================================

def CalcSHA1Hex(data: bytes) -> str:
    # Python標準のhashlibを使用し高速かつ確実に計算を行います
    return hashlib.sha1(data).hexdigest()


# ============================================================================
# XML DB Search
# ============================================================================

def ExtractFirstElement(block: str, tag: str) -> str:
    open_tag = "<" + tag
    open_pos = block.find(open_tag)
    if open_pos == -1:
        return ""

    gt_pos = block.find('>', open_pos)
    if gt_pos == -1:
        return ""

    close_tag = "</" + tag + ">"
    close_pos = block.find(close_tag, gt_pos + 1)
    if close_pos == -1:
        return ""

    value = block[gt_pos + 1:close_pos]
    return DecodeXmlEntities(value.strip())


def ExtractSha1FromDumpBlock(dump_block: str) -> str:
    hash_pos = dump_block.find("<hash")
    while hash_pos != -1:
        gt_pos = dump_block.find('>', hash_pos)
        if gt_pos == -1:
            return ""

        close_pos = dump_block.find("</hash>", gt_pos + 1)
        if close_pos == -1:
            return ""

        hash_value = dump_block[gt_pos + 1:close_pos].strip()
        if len(hash_value) == 40:
            return hash_value.lower()

        hash_pos = dump_block.find("<hash", close_pos + 7)

    return ""


def FindROMInfoBySha1(xml_path: str, target_sha1: str) -> dict:
    info = {"found": False, "title": "", "system": "", "company": "", "year": "", "sha1": ""}
    try:
        with open(xml_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
            xml_text = f.read()
    except Exception:
        return info

    target = target_sha1.lower()
    pos = 0
    while True:
        start = xml_text.find("<software>", pos)
        if start == -1:
            break

        end = xml_text.find("</software>", start)
        if end == -1:
            break

        software_block = xml_text[start:end]

        title = ExtractFirstElement(software_block, "title")
        system = ExtractFirstElement(software_block, "system")
        company = ExtractFirstElement(software_block, "company")
        year = ExtractFirstElement(software_block, "year")

        dump_pos = 0
        while True:
            dump_start = software_block.find("<dump>", dump_pos)
            if dump_start == -1:
                break

            dump_end = software_block.find("</dump>", dump_start)
            if dump_end == -1:
                break

            dump_block = software_block[dump_start:dump_end]
            sha1 = ExtractSha1FromDumpBlock(dump_block)
            if sha1:
                if sha1 == target:
                    info["title"] = title
                    info["system"] = system
                    info["company"] = company
                    info["year"] = year
                    info["sha1"] = sha1
                    info["found"] = True
                    return info

            dump_pos = dump_end + 7

        pos = end + 11

    info["found"] = False
    return info


# ============================================================================
# Serial Communication Functions
# ============================================================================

def SendCommand(ser: serial.Serial, command: str) -> bool:
    try:
        tmpstr = f"{command}\r\n".encode('ascii')
        ser.write(tmpstr)
        ser.flush()
        return True
    except Exception:
        return False


def RecvResponse(ser: serial.Serial, maxlen: int, timeout_ms: int) -> tuple[bool, str]:
    response = bytearray()
    start_time = time.time()
    
    #ser.timeout = 0.05 #タイムアウトを変更すると通信が不安定になる

    while True:
        try:
            ch = ser.read(1)
        except Exception:
            return False, ""

        if not ch:
            current_time = time.time()
            if timeout_ms > 0 and (current_time - start_time) * 1000 >= timeout_ms:
                print("Response timeout")
                return False, ""
            continue

        start_time = time.time()

        if len(response) < maxlen - 1:
            response.extend(ch)
        else:
            response = response[1:] + ch

        try:
            resp_str = response.decode('ascii', errors='ignore')
        except Exception:
            resp_str = ""

        if "OK\n" in resp_str:
            return True, resp_str

        if "FAIL\n" in resp_str:
            return False, resp_str


def RecvBinaryBlock(ser: serial.Serial, recvsize: int) -> tuple[bool, bytearray]:
    #ser.timeout = timeout  #タイムアウトを変更すると通信が不安定になる

    buffer = bytearray()

    while len(buffer) < recvsize:
        to_read = recvsize - len(buffer)
        try:
            chunk = ser.read(to_read)
        except Exception:
            return False, bytearray()
        if not chunk:
            break
        buffer.extend(chunk)

    return len(buffer) == recvsize, buffer


def SendBinary(ser: serial.Serial, data: bytes) -> bool:
    try:
        sent_size = ser.write(data)
        ser.flush()
        return sent_size == len(data)
    except Exception:
        return False


# ============================================================================
# Cartridge Control Functions
# ============================================================================

def GetFirmwareVersionDate(ser: serial.Serial) -> tuple[bool, int]:
    if not SendCommand(ser, "HVER"):
        return False, 0

    success, response = RecvResponse(ser, 1024, TIMEOUT_MS)
    if not success:
        return False, 0

    # --------------------------------------------------------------------
    # Format 2:
    # HARDWARE NAME : ILF ROM Cassette Reader V2
    # HARDWARE VER : REV_B2
    # FIRMWARE VER : 202605310157
    # --------------------------------------------------------------------
    key = "FIRMWARE VER :"
    pos = response.find(key)
    if pos != -1:
        val_part = response[pos + len(key):].strip()
        # 数字のみを抽出
        fwver = ""
        for char in val_part:
            if char.isdigit():
                fwver += char
            else:
                break
        if len(fwver) == 12:
            try:
                return True, int(fwver)
            except ValueError:
                pass

    # --------------------------------------------------------------------
    # Format 1:
    # ILF ROM Cassette Reader V2
    # REV_B2
    # FIRMWARE DATE
    # May 28 2026
    #
    # -> return YYYYMMDD0000
    # --------------------------------------------------------------------
    key = "FIRMWARE DATE"
    pos = response.find(key)
    if pos != -1:
        lines = response[pos + len(key):].strip().split('\n')
        if lines:
            parts = lines[0].strip().split()
            if len(parts) == 3:
                month_str, day_str, year_str = parts[0], parts[1], parts[2]
                month_map = {
                    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
                    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
                }
                month = month_map.get(month_str.title()[:3], 0)
                if month > 0:
                    try:
                        day = int(day_str)
                        year = int(year_str)
                        yyyymmddhhmm = (year * 100000000) + (month * 1000000) + (day * 10000)
                        return True, yyyymmddhhmm
                    except ValueError:
                        pass

    return False, 0


def FirmwareVersionCheck(ser: serial.Serial) -> bool:
    success, fw_date_time = GetFirmwareVersionDate(ser)
    if not success:
        print("Failed to get firmware version date")
        return False
    
    fw_date = fw_date_time // 10000
    
    if fw_date < MIN_FIRMWARE_DATE:
        print(f"Firmware version is too old: {fw_date} (required: {MIN_FIRMWARE_DATE} or later)")
        return False
    
    print("Firmware version check... OK")
    return True


def SlotCheck(ser: serial.Serial) -> bool:
    print("Checking cartridge insertion...")

    if not SendCommand(ser, "SCHK"):
        print("Failed to send SCHK command")
        return False

    success, response = RecvResponse(ser, MAX_RESPONSE_LEN, TIMEOUT_MS)
    if not success:
        print("Failed to receive SCHK response")
        return False

    if "0010" in response:
        print("Cartridge is properly inserted")
        return True

    return False


def SlotPowerOn(ser: serial.Serial) -> bool:
    print("Turning on slot power...")

    if not SendCommand(ser, "SPON"):
        print("Failed to send SPON command")
        return False

    success, response = RecvResponse(ser, MAX_RESPONSE_LEN, TIMEOUT_MS)
    if not success:
        print("Failed to receive SPON response")
        return False

    if "OK" in response:
        print("Slot power turned on successfully")
        return True

    return False


def SlotPowerOff(ser: serial.Serial) -> bool:
    print("Turning off slot power...")

    if not SendCommand(ser, "SPOFF"):
        print("Failed to send SPOFF command")
        return False

    success, response = RecvResponse(ser, MAX_RESPONSE_LEN, TIMEOUT_MS)
    if not success:
        print("Failed to receive SPOFF response")
        return False

    if "OK\n" in response:
        print("Slot power turned off successfully")
        return True

    print("ERROR: Failed to turn off slot power")
    return False


def SlotReset(ser: serial.Serial) -> bool:
    if not SendCommand(ser, "SRST"):
        print("Failed to send SRST command")
        return False

    success, response = RecvResponse(ser, MAX_RESPONSE_LEN, TIMEOUT_MS)
    if not success:
        print("Failed to receive SRST response")
        return False

    if "OK\n" in response:
        return True

    print("ERROR: Failed to turn off slot power")
    return False


# ============================================================================
# Slot Access Functions
# ============================================================================

def slotWrite(ser: serial.Serial, address: int, data: int) -> bool:
    command = f"SMWR,{address:04X},{data:02X}"

    if not SendCommand(ser, command):
        return False

    success, _ = RecvResponse(ser, MAX_RESPONSE_LEN, TIMEOUT_MS)
    return success


def slotRead(ser: serial.Serial, address: int) -> tuple[bool, int]:
    command = f"SMRD,{address:04X}"

    if not SendCommand(ser, command):
        return False, 0

    success, response = RecvResponse(ser, MAX_RESPONSE_LEN, TIMEOUT_MS)
    if not success:
        return False, 0

    # sscanf_s(response, "%*x : %02hhX", data) の解析処理
    try:
        parts = response.split(':')
        if len(parts) >= 2:
            data_str = parts[1].strip()
            # 16進数文字を最大2桁切り出し
            hex_part = ""
            for char in data_str:
                if char.upper() in '0123456789ABCDEF':
                    hex_part += char
                else:
                    break
            if hex_part:
                return True, int(hex_part, 16)
    except Exception:
        pass

    return False, 0


def slotDump(ser: serial.Serial, address: int, length: int) -> tuple[bool, bytes]:
    command = f"SMTR,{address:04X},{length:04X}\r\nBSND,0,{length:04X}"

    if not SendCommand(ser, command):
        return False, b""

    success, _ = RecvResponse(ser, MAX_RESPONSE_LEN, TIMEOUT_MS)
    if not success:
        return False, b""

    success, data = RecvBinaryBlock(ser, length)
    if not success:
        return False, b""

    success, _ = RecvResponse(ser, MAX_RESPONSE_LEN, TIMEOUT_MS)
    if not success:
        return False, b""

    return True, data


def slotReadHash(ser: serial.Serial, address: int, length: int) -> tuple[bool, int]:
    command = f"SMTH,{address:04X},{length:04X}"

    if not SendCommand(ser, command):
        return False, 0

    success, response = RecvResponse(ser, MAX_RESPONSE_LEN, TIMEOUT_MS)
    if not success:
        return False, 0

    # sscanf_s(response, "%*x : %x", &tmp) の解析
    try:
        parts = response.split(':')
        if len(parts) >= 2:
            hash_str = parts[1].strip()
            hex_part = ""
            for char in hash_str:
                if char.upper() in '0123456789ABCDEF':
                    hex_part += char
                else:
                    break
            if hex_part:
                return True, int(hex_part, 16)
    except Exception:
        pass

    return False, 0


def hardwareSetting(ser: serial.Serial, address: int, data: int) -> bool:
    command = f"HSET,{address:04X},{data:X}"

    if not SendCommand(ser, command):
        return False

    success, _ = RecvResponse(ser, MAX_RESPONSE_LEN, TIMEOUT_MS)
    return success


# {"RMSET", cmd_romMapperSet},	    // RMSET,[Mapper Selecter Address],[Bank Address],[Bank size]   (追加 V1.40～) Mega ROM Mapperの設定//
# { "RMRD", cmd_romMapperRead }	        // RMRD,[Mapper Start],[Mapper End](,[Slot])                    (追加 V1.40～) Mega ROMの一括Read
def setMegaROMconfig(ser: serial.Serial, selecterAddress: int, readAddress: int, bankSize: int) -> bool:
    command = f"RMSET,{selecterAddress:04X},{readAddress:04X},{bankSize:04X}"

    if not SendCommand(ser, command):
        return False

    success, _ = RecvResponse(ser, MAX_RESPONSE_LEN, TIMEOUT_MS)
    return success


def slotMegaROMdump(ser: serial.Serial, bankSize: int, startBank: int, endBank: int, out_data: bytearray) -> bool:
    command = f"RMRD,{startBank:X},{endBank:X}"
    if not SendCommand(ser, command):
        return False

    bankCnt = endBank - startBank
    totalSize = bankCnt * bankSize
    out_data[:] = b'\x00'*totalSize

    offset = 0
    for bank in range(startBank, endBank):
        print(f"Saved bank {bank} (0x{bank * bankSize:04X} - 0x{bankSize * (bank + 1) - 1:04X})")
        success, block = RecvBinaryBlock(ser, bankSize)
        if not success:
            return False
        # bytearray内の該当バンク位置に代入
        out_data[offset:offset+bankSize] = block
        offset += bankSize

    success, _ = RecvResponse(ser, MAX_RESPONSE_LEN, TIMEOUT_MS)

    return success

# ============================================================================
# Hash Calculation
# ============================================================================

def Hash7936(data: bytes, address: int) -> int:
    # 32bit符号なし整数(DWORD)相当の計算維持のため & 0xFFFFFFFF を挟みます
    hash_val = 0x5381

    for i in range(HASH_SIZE):
        hash_val = ((((hash_val << 5) + hash_val) & 0xFFFFFFFF) ^ data[address + i]) & 0xFFFFFFFF

    return hash_val


def HashFilledFF(length: int) -> int:
    hash_val = 0x5381

    for _ in range(length):
        hash_val = ((((hash_val << 5) + hash_val) & 0xFFFFFFFF) ^ 0xff) & 0xFFFFFFFF

    return hash_val


# ============================================================================
# ROM ACCESS Timing Setting
# ============================================================================

def ReadHash5Match(ser: serial.Serial) -> bool:
    filledFFHash = HashFilledFF(HASH_SIZE)

    for retry in range(2):
        addr = 0x4000 if retry == 0 else 0x8000
        h = [0] * 5

        for i in range(5):
            # if (i == 1) 
            #     Sleep(1500);      //SLTまたはRD信号にコンデンサーが付いているカセット対策

            success, val = slotReadHash(ser, addr, HASH_SIZE)
            if not success:
                print(f"slotReadHash failed at try {i + 1}")
                return False
            h[i] = val

        # DISPLAY_HASH用
        # if globals().get('DISPLAY_HASH', False):
        #     print(f"Hash(addr={addr:04X}) = {h[0]:08X}, {h[1]:08X}, {h[2]:08X}, {h[3]:08X}, {h[4]:08X}")

        # 5回すべて一致しているか
        if not (h[0] == h[1] == h[2] == h[3] == h[4]):
            # print("Hash mismatch")
            return False

        # 0x4000 で全て filledFFHash の場合のみ、0x8000 で再試行
        if h[0] == filledFFHash:
            if retry == 0:
                continue
            # 0x8000 側でも無効値だった
            return False

        return True

    return False


# address 0 を 100(1us) ずつ 1000(10us) まで変更しながら hash 一致を確認
def SweepAddress0AndCheck(ser: serial.Serial) -> bool:
    for d in range(100, 1001, 100):
        print(f"HardwareSetting (wait {d // 100} us) ... ")

        if not hardwareSetting(ser, 0, d + MEMWAIT):
            return False
        if not hardwareSetting(ser, 1, d + RDWAIT):
            return False

        if ReadHash5Match(ser):
            print(f"PASSED {d // 100}us")
            return True

    return False


# hash の安定化確認
def CheckHashWithRetry(ser: serial.Serial) -> bool:
    print("Read Timing Check.")

    # default設定値
    if not hardwareSetting(ser, 0, MEMWAIT):
        return False
    if not hardwareSetting(ser, 1, RDWAIT):
        return False

    print("Checking default setting... ", end="", flush=True)
    if ReadHash5Match(ser):
        print("PASS")
        return True
    print("FAILED")
    
    print("Checking Read setting ... ")
    # 1us 刻みで 100us まで変更しながら確認
    if SweepAddress0AndCheck(ser):
        return True

    print("FAILED")
    print("Hash did not stabilize")
    return False


# ============================================================================
# Mapper Detection / Read Functions
# ============================================================================

def DetectASCII8K(ser: serial.Serial, romInfo: dict) -> bool:
    print("--- Testing ASCII 8K ---")

    hashA = [0] * 4
    hashB = [0] * 4
    filledFFHash = HashFilledFF(HASH_SIZE)
    bankSteps = [0, 4, 8, 16, 32, 64, 128, 256]

    romInfo['hasSRAM'] = False

    if not slotWrite(ser, 0x6000, 0): return False
    if not slotWrite(ser, 0x6800, 1): return False
    if not slotWrite(ser, 0x7000, 2): return False
    if not slotWrite(ser, 0x7800, 3): return False

    success, hashA[0] = slotReadHash(ser, 0x4000, HASH_SIZE)
    if not success: return False
    success, hashA[1] = slotReadHash(ser, 0x6000, HASH_SIZE)
    if not success: return False
    success, hashA[2] = slotReadHash(ser, 0x8000, HASH_SIZE)
    if not success: return False
    success, hashA[3] = slotReadHash(ser, 0xA000, HASH_SIZE)
    if not success: return False

    # hashが同一値の場合は除外
    if hashA[1] == hashA[0] and hashA[2] == hashA[0] and hashA[3] == hashA[0]:
        return False

    # KONAMI8K check
    if not slotWrite(ser, 0x8000, 0): return False
    if not slotWrite(ser, 0xA000, 0): return False
    success, hashB[2] = slotReadHash(ser, 0x8000, HASH_SIZE)
    if not success: return False
    success, hashB[3] = slotReadHash(ser, 0xA000, HASH_SIZE)
    if not success: return False

    if hashA[2] != hashB[2] or hashA[3] != hashB[3]:
        return False

    foundPattern = False
    last_bank_num = 0

    for bankNum in bankSteps:
        last_bank_num = bankNum
        if not slotWrite(ser, 0x6000, (bankNum + 3) & 0xFF): return False
        if not slotWrite(ser, 0x6800, (bankNum + 2) & 0xFF): return False
        if not slotWrite(ser, 0x7000, (bankNum + 1) & 0xFF): return False
        if not slotWrite(ser, 0x7800, (bankNum + 0) & 0xFF): return False

        success, hashB[0] = slotReadHash(ser, 0x4000, HASH_SIZE)
        if not success: return False
        success, hashB[1] = slotReadHash(ser, 0x6000, HASH_SIZE)
        if not success: return False
        success, hashB[2] = slotReadHash(ser, 0x8000, HASH_SIZE)
        if not success: return False
        success, hashB[3] = slotReadHash(ser, 0xA000, HASH_SIZE)
        if not success: return False

        # Bankが切り替わっていない場合は、別タイプ
        if bankNum == 0 and (hashA[0] == hashB[0] or hashA[1] == hashB[1] or hashA[2] == hashB[2] or hashA[3] == hashB[3]):
            break

        # Patternが一致の場合
        if hashB[0] == hashA[3] and hashB[1] == hashA[2] and hashB[2] == hashA[1] and hashB[3] == hashA[0]:
            if bankNum != 0:
                break
            foundPattern = True

        # PatternがFFの場合
        if filledFFHash == hashB[0] and filledFFHash == hashB[1] and filledFFHash == hashB[2] and filledFFHash == hashB[3]:
            break

        # SRAM Check
        success, sramOrgData0 = slotRead(ser, 0xA000)
        if not success: return False
        success, sramOrgData2 = slotRead(ser, 0xB000)
        if not success: return False

        if not slotWrite(ser, 0xA000, (~sramOrgData0) & 0xFF): return False
        if not slotWrite(ser, 0xB000, (~sramOrgData2) & 0xFF): return False

        success, sramData0 = slotRead(ser, 0xA000)
        if not success: return False
        success, sramData2 = slotRead(ser, 0xB000)
        if not success: return False

        if sramData0 == (sramOrgData0 ^ 0xff) or sramData2 == (sramOrgData2 ^ 0xff):
            if not slotWrite(ser, 0xA000, sramOrgData0): return False
            if not slotWrite(ser, 0xB000, sramOrgData2): return False
            romInfo['hasSRAM'] = True
            foundPattern = True
            break

        if not foundPattern:
            break

    if foundPattern:
        print("\n=== ASCII 8K Detected ===")

        romInfo['mapperType'] = MAPPER_ASCII_8K
        if romInfo['hasSRAM']:
            romInfo['mapperName'] = "ASCII 8K(+SRAM)"
        else:
            romInfo['mapperName'] = "ASCII 8K"
        romInfo['bankCount'] = last_bank_num
        romInfo['romSize'] = romInfo['bankCount'] * 0x2000
        romInfo['mapperAddress'] = 0x7000
        romInfo['readBankSize'] = 0x2000
        romInfo['readAreaStart'] = 0x8000
        romInfo['readAreaSize'] = 0x2000
        print(f"Bank count: {romInfo['bankCount']}, ROM size: {romInfo['romSize']} (0x{romInfo['romSize']:X})")
        return True

    return False


def DetectASCII16K(ser: serial.Serial, romInfo: dict) -> bool:
    print("--- Testing ASCII 16K ---")

    hashA = [0] * 4
    hashB = [0] * 4
    filledFFHash = HashFilledFF(HASH_SIZE)
    bankSteps = [0, 2, 4, 8, 16, 32, 64, 128]

    romInfo['hasSRAM'] = False

    if not slotWrite(ser, 0x6000, 0): return False
    if not slotWrite(ser, 0x6800, 0): return False
    if not slotWrite(ser, 0x7000, 1): return False
    if not slotWrite(ser, 0x7800, 1): return False

    success, hashA[0] = slotReadHash(ser, 0x4000, HASH_SIZE)
    if not success: return False
    success, hashA[1] = slotReadHash(ser, 0x6000, HASH_SIZE)
    if not success: return False
    success, hashA[2] = slotReadHash(ser, 0x8000, HASH_SIZE)
    if not success: return False
    success, hashA[3] = slotReadHash(ser, 0xA000, HASH_SIZE)
    if not success: return False

    # hashが同一値の場合は除外
    if hashA[1] == hashA[0] and hashA[2] == hashA[0] and hashA[3] == hashA[0]:
        return False
    # 16k mirror ROMも除外
    if hashA[2] == hashA[0] and hashA[3] == hashA[1]:
        return False

    # KONAMI8K check
    if not slotWrite(ser, 0x8000, 0): return False
    if not slotWrite(ser, 0xA000, 0): return False
    success, hashB[2] = slotReadHash(ser, 0x8000, HASH_SIZE)
    if not success: return False
    success, hashB[3] = slotReadHash(ser, 0xA000, HASH_SIZE)
    if not success: return False

    if hashA[2] != hashB[2] or hashA[3] != hashB[3]:
        return False

    foundPattern = False
    last_bank_num = 0

    for bankNum in bankSteps:
        last_bank_num = bankNum

        if not slotWrite(ser, 0x6000, (bankNum + 1) & 0xFF): return False
        if not slotWrite(ser, 0x7000, (bankNum + 0) & 0xFF): return False

        success, hashB[0] = slotReadHash(ser, 0x4000, HASH_SIZE)
        if not success: return False
        success, hashB[1] = slotReadHash(ser, 0x6000, HASH_SIZE)
        if not success: return False
        success, hashB[2] = slotReadHash(ser, 0x8000, HASH_SIZE)
        if not success: return False
        success, hashB[3] = slotReadHash(ser, 0xA000, HASH_SIZE)
        if not success: return False

        # Bankが切り替わっていない場合は、別タイプ
        if bankNum == 0 and (hashA[0] == hashB[0] or hashA[1] == hashB[1] or hashA[2] == hashB[2] or hashA[3] == hashB[3]):
            break

        # Patternが一致の場合
        if hashB[0] == hashA[2] and hashB[1] == hashA[3] and hashB[2] == hashA[0] and hashB[3] == hashA[1]:
            if bankNum != 0:
                break
            foundPattern = True

        # PatternがFFの場合
        if filledFFHash == hashB[0] and filledFFHash == hashB[1] and filledFFHash == hashB[2] and filledFFHash == hashB[3]:
            break

        # SRAM Check
        success, sramOrgData0 = slotRead(ser, 0x8000)
        if not success: return False
        success, sramOrgData2 = slotRead(ser, 0xA000)
        if not success: return False

        if not slotWrite(ser, 0x8000, (~sramOrgData0) & 0xFF): return False
        if not slotWrite(ser, 0xA000, (~sramOrgData2) & 0xFF): return False

        success, sramData0 = slotRead(ser, 0x8000)
        if not success: return False
        success, sramData2 = slotRead(ser, 0xA000)
        if not success: return False

        if sramData0 == (sramOrgData0 ^ 0xff) or sramData2 == (sramOrgData2 ^ 0xff):
            if not slotWrite(ser, 0x8000, sramOrgData0): return False
            if not slotWrite(ser, 0xA000, sramOrgData2): return False

            romInfo['hasSRAM'] = True
            foundPattern = True
            break

        if not foundPattern:
            break

    if foundPattern:
        print("\n=== ASCII 16K Detected ===")

        romInfo['mapperType'] = MAPPER_ASCII_16K
        if romInfo['hasSRAM']:
            romInfo['mapperName'] = "ASCII 16K(+SRAM)"
        else:
            romInfo['mapperName'] = "ASCII 16K"
        romInfo['bankCount'] = last_bank_num
        romInfo['romSize'] = romInfo['bankCount'] * 0x4000
        romInfo['mapperAddress'] = 0x7000
        romInfo['readBankSize'] = 0x4000
        romInfo['readAreaStart'] = 0x8000
        romInfo['readAreaSize'] = 0x4000
        print(f"Bank count: {romInfo['bankCount']}, ROM size: {romInfo['romSize']} (0x{romInfo['romSize']:X})")
        return True

    return False


def DetectKONAMI8K(ser: serial.Serial, romInfo: dict) -> bool:
    print("--- Testing KONAMI 8K ---")

    hashA = [0] * 4
    hashB = [0] * 4
    hashC = [0] * 4
    filledFFHash = HashFilledFF(HASH_SIZE)
    bankSteps = [0, 4, 8, 16, 32]

    romInfo['hasSRAM'] = False

    if not slotWrite(ser, 0x4000, 3): return False
    if not slotWrite(ser, 0x6000, 0): return False
    if not slotWrite(ser, 0x8000, 1): return False
    if not slotWrite(ser, 0xA000, 2): return False

    success, hashA[0] = slotReadHash(ser, 0x4000, HASH_SIZE)
    if not success: return False
    success, hashA[1] = slotReadHash(ser, 0x6000, HASH_SIZE)
    if not success: return False
    success, hashA[2] = slotReadHash(ser, 0x8000, HASH_SIZE)
    if not success: return False
    success, hashA[3] = slotReadHash(ser, 0xA000, HASH_SIZE)
    if not success: return False

    # hashが同一値の場合は除外
    if hashA[1] == hashA[0] and hashA[2] == hashA[0] and hashA[3] == hashA[0]:
        return False

    foundPattern = False
    last_bank_num = 0

    for bankNum in bankSteps:
        last_bank_num = bankNum
        if not slotWrite(ser, 0x4000, (bankNum + 2) & 0xFF): return False
        if not slotWrite(ser, 0x6000, (bankNum + 2) & 0xFF): return False
        if not slotWrite(ser, 0x8000, (bankNum + 0) & 0xFF): return False
        if not slotWrite(ser, 0xA000, (bankNum + 1) & 0xFF): return False

        success, hashB[0] = slotReadHash(ser, 0x4000, HASH_SIZE)
        if not success: return False
        success, hashB[1] = slotReadHash(ser, 0x6000, HASH_SIZE)
        if not success: return False
        success, hashB[2] = slotReadHash(ser, 0x8000, HASH_SIZE)
        if not success: return False
        success, hashB[3] = slotReadHash(ser, 0xA000, HASH_SIZE)
        if not success: return False

        # Patternが一致の場合
        if hashB[0] == hashA[0] and hashB[1] == hashA[3] and hashB[2] == hashA[1] and hashB[3] == hashA[2]:
            if bankNum != 0:
                break
            foundPattern = True

        if filledFFHash == hashB[1] and filledFFHash == hashB[2] and filledFFHash == hashB[3]:
            break

        # 新10倍カートリッジのチェック SRAMは4KBx2pageなので同じデータが連続する
        if bankNum == 0x10:
            success, hashC[0] = slotReadHash(ser, 0x8000, 0x1000)
            if not success: return False
            success, hashC[1] = slotReadHash(ser, 0x9000, 0x1000)
            if not success: return False
            if hashC[0] == hashC[1]:
                romInfo['hasSRAM'] = True
                foundPattern = True
                break

        if bankNum == 0x00 and (hashA[1] == hashB[1] or hashA[2] == hashB[2] or hashA[3] == hashB[3]):
            break

        if not foundPattern:
            break

    if foundPattern:
        print("\n=== KONAMI 8K Detected ===")
        romInfo['mapperType'] = MAPPER_KONAMI_8K
        romInfo['mapperName'] = "KONAMI 8K (+SRAM)" if romInfo['hasSRAM'] else "KONAMI 8K"
        romInfo['bankCount'] = last_bank_num
        romInfo['romSize'] = romInfo['bankCount'] * 0x2000
        romInfo['mapperAddress'] = 0x8000
        romInfo['readBankSize'] = 0x2000
        romInfo['readAreaStart'] = 0x8000
        romInfo['readAreaSize'] = 0x2000
        print(f"Bank count: {romInfo['bankCount']}, ROM size: {romInfo['romSize']} (0x{romInfo['romSize']:X})")
        return True

    return False


def DetectKONAMI_SCC(ser: serial.Serial, romInfo: dict) -> bool:
    print("--- Testing KONAMI 8K ---")

    hashA = [0] * 4
    hashB = [0] * 4
    filledFFHash = HashFilledFF(HASH_SIZE)
    bankSteps = [0, 4, 8, 16, 32, 64, 128, 256]

    romInfo['hasSRAM'] = False

    if not slotWrite(ser, 0x5000, 0): return False
    if not slotWrite(ser, 0x7000, 1): return False
    if not slotWrite(ser, 0x9000, 2): return False
    if not slotWrite(ser, 0xB000, 3): return False
    if not slotWrite(ser, 0x5800, 0): return False
    if not slotWrite(ser, 0x7800, 1): return False
    if not slotWrite(ser, 0x9800, 2): return False
    if not slotWrite(ser, 0xB800, 3): return False

    success, hashA[0] = slotReadHash(ser, 0x4000, HASH_SIZE)
    if not success: return False
    success, hashA[1] = slotReadHash(ser, 0x6000, HASH_SIZE)
    if not success: return False
    success, hashA[2] = slotReadHash(ser, 0x8000, HASH_SIZE)
    if not success: return False
    success, hashA[3] = slotReadHash(ser, 0xA000, HASH_SIZE)
    if not success: return False

    # hashが同一値の場合は除外
    if hashA[1] == hashA[0] and hashA[2] == hashA[0] and hashA[3] == hashA[0]:
        return False

    foundPattern = False
    last_bank_num = 0

    for bankNum in bankSteps:
        last_bank_num = bankNum
        if not slotWrite(ser, 0x5000, (bankNum + 3) & 0xFF): return False
        if not slotWrite(ser, 0x7000, (bankNum + 2) & 0xFF): return False
        if not slotWrite(ser, 0x9000, (bankNum + 1) & 0xFF): return False
        if not slotWrite(ser, 0xB000, (bankNum + 0) & 0xFF): return False

        success, hashB[0] = slotReadHash(ser, 0x4000, HASH_SIZE)
        if not success: return False
        success, hashB[1] = slotReadHash(ser, 0x6000, HASH_SIZE)
        if not success: return False
        success, hashB[2] = slotReadHash(ser, 0x8000, HASH_SIZE)
        if not success: return False
        success, hashB[3] = slotReadHash(ser, 0xA000, HASH_SIZE)
        if not success: return False

        # Patternが一致の場合
        if hashB[3] == hashA[0] and hashB[2] == hashA[1] and hashB[1] == hashA[2] and hashB[0] == hashA[3]:
            if bankNum != 0:
                break
            foundPattern = True

        if filledFFHash == hashB[1] and filledFFHash == hashB[2] and filledFFHash == hashB[3]:
            break

        if bankNum == 0x00 and (hashA[0] == hashB[0] or hashA[1] == hashB[1] or hashA[2] == hashB[2] or hashA[3] == hashB[3]):
            break

        if not foundPattern:
            break

    if foundPattern:
        print("\n=== KONAMI SCC Detected ===")
        romInfo['mapperType'] = MAPPER_KONAMI_SCC
        romInfo['mapperName'] = "KONAMI SCC"
        romInfo['bankCount'] = last_bank_num
        romInfo['romSize'] = romInfo['bankCount'] * 0x2000
        romInfo['mapperAddress'] = 0x9000
        romInfo['readBankSize'] = 0x2000
        romInfo['readAreaStart'] = 0x8000
        romInfo['readAreaSize'] = 0x2000
        print(f"Bank count: {romInfo['bankCount']}, ROM size: {romInfo['romSize']} (0x{romInfo['romSize']:X})")
        return True

    return False


def DetectGeneric16K(ser: serial.Serial, romInfo: dict) -> bool:
    print("--- Testing Generic 16K ---")

    hashA = [0] * 4
    hashB = [0] * 4
    prevHashA = [0] * 4
    filledFFHash = HashFilledFF(HASH_SIZE)

    if not slotWrite(ser, 0x4000, 0): return False
    if not slotWrite(ser, 0x6000, 0): return False
    if not slotWrite(ser, 0x8000, 1): return False
    if not slotWrite(ser, 0xA000, 1): return False

    success, hashA[0] = slotReadHash(ser, 0x4000, HASH_SIZE)
    if not success: return False
    success, hashA[1] = slotReadHash(ser, 0x6000, HASH_SIZE)
    if not success: return False
    success, hashA[2] = slotReadHash(ser, 0x8000, HASH_SIZE)
    if not success: return False
    success, hashA[3] = slotReadHash(ser, 0xA000, HASH_SIZE)
    if not success: return False

    prevHashA = list(hashA)
    maxBank = 0
    foundPattern = False

    for bankNum in range(1, 0x100):
        if not slotWrite(ser, 0x4000, bankNum & 0xFF): return False
        if not slotWrite(ser, 0x6000, 0): return False
        if not slotWrite(ser, 0x8000, (bankNum + 1) & 0xFF): return False
        if not slotWrite(ser, 0x7800, 1): return False

        success, hashB[0] = slotReadHash(ser, 0x4000, HASH_SIZE)
        if not success: return False
        success, hashB[1] = slotReadHash(ser, 0x6000, HASH_SIZE)
        if not success: return False
        success, hashB[2] = slotReadHash(ser, 0x8000, HASH_SIZE)
        if not success: return False
        success, hashB[3] = slotReadHash(ser, 0xA000, HASH_SIZE)
        if not success: return False

        if (bankNum % 4 == 0) and (filledFFHash == hashB[0] and filledFFHash == hashB[1] and filledFFHash == hashB[2] and filledFFHash == hashB[3]):
            break

        if prevHashA[0] == hashB[0] and prevHashA[1] == hashB[1] and prevHashA[2] == hashB[2] and prevHashA[3] == hashB[3]:
            break

        if hashA[2] == hashB[0] and hashA[3] == hashB[1]:
            maxBank = bankNum
            foundPattern = True

        hashA = list(hashB)
        if not foundPattern:
            break

    if foundPattern and maxBank > 0:
        print("\n=== Generic 16K Detected ===")
        romInfo['mapperType'] = MAPPER_GENERIC_16K
        romInfo['mapperName'] = "Generic 16K"
        romInfo['bankCount'] = maxBank + 1
        romInfo['romSize'] = romInfo['bankCount'] * 0x4000
        romInfo['readBankSize'] = 0x4000
        romInfo['readAreaStart'] = 0x8000
        romInfo['readAreaSize'] = 0x4000
        print(f"Bank count: {romInfo['bankCount']}, ROM size: {romInfo['romSize']} (0x{romInfo['romSize']:X})")
        return True

    return False


def DetectGeneric8K(ser: serial.Serial, romInfo: dict) -> bool:
    print("--- Testing Generic 8K ---")
    hashA = [0] * 4
    hashB = [0] * 4
    prevHashA = [0] * 4
    filledFFHash = HashFilledFF(HASH_SIZE)

    if not slotWrite(ser, 0x4000, 0): return False
    if not slotWrite(ser, 0x6000, 1): return False
    if not slotWrite(ser, 0x8000, 2): return False
    if not slotWrite(ser, 0xA000, 3): return False

    success, hashA[0] = slotReadHash(ser, 0x4000, HASH_SIZE)
    if not success: return False
    success, hashA[1] = slotReadHash(ser, 0x6000, HASH_SIZE)
    if not success: return False
    success, hashA[2] = slotReadHash(ser, 0x8000, HASH_SIZE)
    if not success: return False
    success, hashA[3] = slotReadHash(ser, 0xA000, HASH_SIZE)
    if not success: return False

    prevHashA = list(hashA)
    maxBank = 0
    foundPattern = False

    for bankNum in range(1, 0x100):
        if not slotWrite(ser, 0x4000, bankNum & 0xFF): return False
        if not slotWrite(ser, 0x6000, (bankNum + 1) & 0xFF): return False
        if not slotWrite(ser, 0x8000, (bankNum + 2) & 0xFF): return False
        if not slotWrite(ser, 0xA000, (bankNum + 3) & 0xFF): return False

        success, hashB[0] = slotReadHash(ser, 0x4000, HASH_SIZE)
        if not success: return False
        success, hashB[1] = slotReadHash(ser, 0x6000, HASH_SIZE)
        if not success: return False
        success, hashB[2] = slotReadHash(ser, 0x8000, HASH_SIZE)
        if not success: return False
        success, hashB[3] = slotReadHash(ser, 0xA000, HASH_SIZE)
        if not success: return False

        if (bankNum % 8 == 0) and (filledFFHash == hashB[0] and filledFFHash == hashB[1] and filledFFHash == hashB[2] and filledFFHash == hashB[3]):
            break

        if prevHashA[0] == hashB[0] and prevHashA[1] == hashB[1] and prevHashA[2] == hashB[2] and prevHashA[3] == hashB[3]:
            break

        if hashA[2] == hashB[0] and hashA[3] == hashB[1]:
            maxBank = bankNum
            foundPattern = True

        hashA = list(hashB)
        if not foundPattern:
            break

    if foundPattern and maxBank > 0:
        print("\n=== Generic 8K Detected ===")
        romInfo['mapperType'] = MAPPER_GENERIC_8K
        romInfo['mapperName'] = "Generic 8K"
        romInfo['bankCount'] = maxBank + 1
        romInfo['romSize'] = romInfo['bankCount'] * 0x2000
        romInfo['readBankSize'] = 0x2000
        romInfo['readAreaStart'] = 0x8000
        romInfo['readAreaSize'] = 0x2000
        print(f"Bank count: {romInfo['bankCount']}, ROM size: {romInfo['romSize']} (0x{romInfo['romSize']:X})")
        return True

    return False


def DetectRType(ser: serial.Serial, romInfo: dict) -> bool:
    print("--- Testing R-Type ---")

    hashA = [0] * 4
    hashB = [0] * 4

    if not slotWrite(ser, 0x7000, 0x0f): return False

    success, hashA[0] = slotReadHash(ser, 0x4000, HASH_SIZE)
    if not success: return False
    success, hashA[1] = slotReadHash(ser, 0x6000, HASH_SIZE)
    if not success: return False
    success, hashA[2] = slotReadHash(ser, 0x8000, HASH_SIZE)
    if not success: return False
    success, hashA[3] = slotReadHash(ser, 0xA000, HASH_SIZE)
    if not success: return False

    # ページ2バンク0x0Fがページ1と同じ内容であることを確認
    if hashA[0] != hashA[2] or hashA[1] != hashA[3]:
        return False

    if not slotWrite(ser, 0x6000, 0x01): return False
    if not slotWrite(ser, 0x7800, 0x1f): return False

    success, hashB[0] = slotReadHash(ser, 0x4000, HASH_SIZE)
    if not success: return False
    success, hashB[1] = slotReadHash(ser, 0x6000, HASH_SIZE)
    if not success: return False
    success, hashB[2] = slotReadHash(ser, 0x8000, HASH_SIZE)
    if not success: return False
    success, hashB[3] = slotReadHash(ser, 0xA000, HASH_SIZE)
    if not success: return False

    # ページ1は固定で、ページ2の0x0Fと0x1Fと同じ内容であることを確認
    if hashA[0] != hashB[0] or hashA[1] != hashB[1] or hashA[2] != hashB[2] or hashA[3] != hashB[3]:
        return False

    if not slotWrite(ser, 0x6800, 0x00): return False
    if not slotWrite(ser, 0x7800, 0x00): return False

    success, hashB[0] = slotReadHash(ser, 0x4000, HASH_SIZE)
    if not success: return False
    success, hashB[1] = slotReadHash(ser, 0x6000, HASH_SIZE)
    if not success: return False
    success, hashB[2] = slotReadHash(ser, 0x8000, HASH_SIZE)
    if not success: return False
    success, hashB[3] = slotReadHash(ser, 0xA000, HASH_SIZE)
    if not success: return False

    if hashA[0] == hashB[0] and hashA[1] == hashB[1] and hashA[2] != hashB[2] and hashA[3] != hashB[3]:
        print("\n=== R-Type Detected ===")
        romInfo['mapperType'] = MAPPER_RTYPE
        romInfo['mapperName'] = "R-TYPE"
        romInfo['bankCount'] = 0x18
        romInfo['romSize'] = romInfo['bankCount'] * 0x4000
        romInfo['mapperAddress'] = 0x7000
        romInfo['readBankSize'] = 0x4000
        romInfo['readAreaStart'] = 0x8000
        romInfo['readAreaSize'] = 0x4000
        print(f"Bank count: {romInfo['bankCount']}, ROM size: {romInfo['romSize']} (0x{romInfo['romSize']:X})")
        return True

    return False


def DetectCrossBlam(ser: serial.Serial, romInfo: dict) -> bool:
    print("--- Testing Cross Blam ---")

    hashA = [0] * 4
    hashB = [0] * 4
    hashC = [0] * 4

    if not slotWrite(ser, 0x6000, 0x00): return False
    if not slotWrite(ser, 0x7000, 0x01): return False

    success, hashA[0] = slotReadHash(ser, 0x4000, HASH_SIZE)
    if not success: return False
    success, hashA[1] = slotReadHash(ser, 0x6000, HASH_SIZE)
    if not success: return False
    success, hashA[2] = slotReadHash(ser, 0x8000, HASH_SIZE)
    if not success: return False
    success, hashA[3] = slotReadHash(ser, 0xA000, HASH_SIZE)
    if not success: return False

    if not slotWrite(ser, 0x6000, 0x02): return False
    if not slotWrite(ser, 0x7000, 0x02): return False

    success, hashB[0] = slotReadHash(ser, 0x4000, HASH_SIZE)
    if not success: return False
    success, hashB[1] = slotReadHash(ser, 0x6000, HASH_SIZE)
    if not success: return False
    success, hashB[2] = slotReadHash(ser, 0x8000, HASH_SIZE)
    if not success: return False
    success, hashB[3] = slotReadHash(ser, 0xA000, HASH_SIZE)
    if not success: return False

    if hashA[0] != hashB[0] or hashA[1] != hashB[1] or hashA[2] == hashB[2] or hashA[3] == hashB[3]:
        return False

    if not slotWrite(ser, 0x6000, 0x01): return False
    if not slotWrite(ser, 0x7000, 0x03): return False

    success, hashC[0] = slotReadHash(ser, 0x4000, HASH_SIZE)
    if not success: return False
    success, hashC[1] = slotReadHash(ser, 0x6000, HASH_SIZE)
    if not success: return False
    success, hashC[2] = slotReadHash(ser, 0x8000, HASH_SIZE)
    if not success: return False
    success, hashC[3] = slotReadHash(ser, 0xA000, HASH_SIZE)
    if not success: return False

    if hashA[0] != hashC[0] or hashA[1] != hashC[1] or hashB[2] == hashC[2] or hashB[3] == hashC[3]:
        return False

    expectedHash = [
        [hashA[2], hashA[3]],
        [hashA[2], hashA[3]],
        [hashB[2], hashB[3]],
        [hashC[2], hashC[3]]
    ]

    for bank in range(8):
        if not slotWrite(ser, 0x7FFF, bank & 0xFF): return False

        success, h2 = slotReadHash(ser, 0x8000, HASH_SIZE)
        if not success: return False
        success, h3 = slotReadHash(ser, 0xA000, HASH_SIZE)
        if not success: return False

        idx = bank % 4
        if h2 != expectedHash[idx][0] or h3 != expectedHash[idx][1]:
            return False

    print("\n=== Cross Blam ROM Detected ===")
    romInfo['mapperType'] = MAPPER_CROSSBLAM
    romInfo['mapperName'] = "CROSS BLAM"
    romInfo['bankCount'] = 0x4
    romInfo['romSize'] = romInfo['bankCount'] * 0x4000
    romInfo['readBankSize'] = 0x4000
    romInfo['readAreaStart'] = 0x4000
    romInfo['readAreaSize'] = 0x8000
    print(f"Bank count: {romInfo['bankCount']}, ROM size: {romInfo['romSize']} (0x{romInfo['romSize']:X})")
    return True


def DetectHarryFox(ser: serial.Serial, romInfo: dict) -> bool:
    print("--- Testing HarryFox ---")

    hash_val = [0] * 4
    prevHashA = [0] * 4
    prevHashB = [0] * 4

    # 基準パターンA取得
    if not slotWrite(ser, 0x6000, 0x00): return False
    if not slotWrite(ser, 0x7000, 0x00): return False

    success, prevHashA[0] = slotReadHash(ser, 0x4000, HASH_SIZE)
    if not success: return False
    success, prevHashA[1] = slotReadHash(ser, 0x6000, HASH_SIZE)
    if not success: return False
    success, prevHashA[2] = slotReadHash(ser, 0x8000, HASH_SIZE)
    if not success: return False
    success, prevHashA[3] = slotReadHash(ser, 0xA000, HASH_SIZE)
    if not success: return False

    # 基準パターンB取得
    if not slotWrite(ser, 0x6000, 0x01): return False
    if not slotWrite(ser, 0x7000, 0x01): return False

    success, prevHashB[0] = slotReadHash(ser, 0x4000, HASH_SIZE)
    if not success: return False
    success, prevHashB[1] = slotReadHash(ser, 0x6000, HASH_SIZE)
    if not success: return False
    success, prevHashB[2] = slotReadHash(ser, 0x8000, HASH_SIZE)
    if not success: return False
    success, prevHashB[3] = slotReadHash(ser, 0xA000, HASH_SIZE)
    if not success: return False

    if prevHashA[0] == prevHashB[0] or prevHashA[1] == prevHashB[1] or prevHashA[2] == prevHashB[2] or prevHashA[3] == prevHashB[3]:
        return False
 
    # i = 0～7 を検査
    for i in range(8):
        expectedHash = prevHashA if (i % 2 == 0) else prevHashB

        if not slotWrite(ser, 0x6fff, i): return False
        if not slotWrite(ser, 0x7fff, i): return False

        success, hash_val[0] = slotReadHash(ser, 0x4000, HASH_SIZE)
        if not success: return False
        success, hash_val[1] = slotReadHash(ser, 0x6000, HASH_SIZE)
        if not success: return False
        success, hash_val[2] = slotReadHash(ser, 0x8000, HASH_SIZE)
        if not success: return False
        success, hash_val[3] = slotReadHash(ser, 0xA000, HASH_SIZE)
        if not success: return False

        if hash_val[0] != expectedHash[0] or hash_val[1] != expectedHash[1] or hash_val[2] != expectedHash[2] or hash_val[3] != expectedHash[3]:
            return False

    print("\n=== Harry Fox ROM Detected ===")
    romInfo['mapperType'] = MAPPER_HARRYFOX
    romInfo['mapperName'] = "HARRY FOX"
    romInfo['bankCount'] = 0x2
    romInfo['romSize'] = romInfo['bankCount'] * 0x8000
    romInfo['readBankSize'] = 0x8000
    romInfo['readAreaStart'] = 0x4000
    romInfo['readAreaSize'] = 0x8000
    print(f"Bank count: {romInfo['bankCount']}, ROM size: {romInfo['romSize']} (0x{romInfo['romSize']:X})")
    return True


def DetectHalnote(ser: serial.Serial, romInfo: dict) -> bool:
    print("--- Testing HALNOTE ---")

    prevHashA = [0] * 4
    prevHashB = [0] * 4

    # 基準パターンA取得
    if not slotWrite(ser, 0x4FFF, 0x00): return False
    if not slotWrite(ser, 0x6FFF, 0x00): return False
    if not slotWrite(ser, 0x8FFF, 0x00): return False
    if not slotWrite(ser, 0xAFFF, 0x00): return False

    # Main Mapper
    success, prevHashA[0] = slotReadHash(ser, 0x4000, HASH_SIZE)
    if not success: return False
    success, prevHashA[1] = slotReadHash(ser, 0x6000, HASH_SIZE)
    if not success: return False
    success, prevHashA[2] = slotReadHash(ser, 0x8000, HASH_SIZE)
    if not success: return False
    success, prevHashA[3] = slotReadHash(ser, 0xA000, HASH_SIZE)
    if not success: return False

    if prevHashA[0] != prevHashA[1] or prevHashA[1] != prevHashA[2] or prevHashA[2] != prevHashA[3]:
        return False

    success, hash_6c00 = slotReadHash(ser, 0x6C00, 0x0800)
    if not success: return False
    prevHashA[1] = hash_6c00

    if not slotWrite(ser, 0x4FFF, 0x00): return False
    if not slotWrite(ser, 0x6FFF, 0x01): return False
    if not slotWrite(ser, 0x8FFF, 0x02): return False
    if not slotWrite(ser, 0xAFFF, 0x00): return False

    # Main Mapper
    success, prevHashB[0] = slotReadHash(ser, 0x4000, HASH_SIZE)
    if not success: return False
    success, prevHashB[1] = slotReadHash(ser, 0x6000, HASH_SIZE)
    if not success: return False
    success, prevHashB[2] = slotReadHash(ser, 0x8000, HASH_SIZE)
    if not success: return False
    success, prevHashB[3] = slotReadHash(ser, 0xA000, HASH_SIZE)
    if not success: return False

    if prevHashA[0] == prevHashB[1] or prevHashA[0] == prevHashB[2] or prevHashB[0] != prevHashB[3]:
        return False

    # Sub Mapper
    if not slotWrite(ser, 0x4FFF, 0x40): return False
    if not slotWrite(ser, 0x6FFF, 0x80): return False

    success, prevHashB[0] = slotReadHash(ser, 0x4000, HASH_SIZE)
    if not success: return False
    success, prevHashB[1] = slotReadHash(ser, 0x6C00, 0x0800)
    if not success: return False
    success, prevHashB[2] = slotReadHash(ser, 0x4000, 0x0800)
    if not success: return False
    success, prevHashB[3] = slotReadHash(ser, 0x7000, 0x0800)
    if not success: return False

    if prevHashA[0] == prevHashB[1] or prevHashA[0] == prevHashB[1] or prevHashB[2] != prevHashB[3]:
        return False

    print("\n=== HALNOTE ROM Detected ===")
    romInfo['mapperType'] = MAPPER_HALNOTE
    romInfo['mapperName'] = "HALNOTE"
    romInfo['bankCount'] = 0x80
    romInfo['romSize'] = romInfo['bankCount'] * 0x2000
    romInfo['readBankSize'] = 0x2000
    romInfo['readAreaStart'] = 0x6000
    romInfo['readAreaSize'] = 0x2000
    print(f"Bank count: {romInfo['bankCount']}, ROM size: {romInfo['romSize']} (0x{romInfo['romSize']:X})")
    return True


def DetectStandardROM(ser: serial.Serial, romInfo: dict) -> bool:
    filledFFHash = HashFilledFF(HASH_SIZE)

    print("\n=== Testing Standard ROM Type ===")
    print("Reading 0x0000-0xFFFF...", end="", flush=True)
    success, fullDataBuffer = slotDump(ser, 0x0000, 0x10000)
    if not success:
        print("Failed to read full ROM")
        return False
    print(" Done")

    hash0 = Hash7936(fullDataBuffer, 0x0000)
    hash2 = Hash7936(fullDataBuffer, 0x2000)
    hash4 = Hash7936(fullDataBuffer, 0x4000)
    hash6 = Hash7936(fullDataBuffer, 0x6000)
    hash8 = Hash7936(fullDataBuffer, 0x8000)
    hashA = Hash7936(fullDataBuffer, 0xA000)
    hashC = Hash7936(fullDataBuffer, 0xC000)
    hashE = Hash7936(fullDataBuffer, 0xE000)
    
    # DAWN PATROL (64KB ROM)
    if hashC != filledFFHash or hashE != filledFFHash:
        if hashC != hash0 and hashC != hash4 and hashC != hash8:
            if hashE != hash2 and hashE != hash6 and hashC != hashA:
                print("\n=== 64KB(0000H) ROM Detected ===")
                romInfo['mapperType'] = MAPPER_NO_MAPPER_64K
                romInfo['mapperName'] = "64KB ROM"
                romInfo['romSize'] = 0x10000
                romInfo['validDataStart'] = 0x0000
                romInfo['validDataSize'] = 0x10000
                return True

    if (hash0 == filledFFHash) and (hash2 == filledFFHash) and (hash4 != filledFFHash) and (hash4 == hash6) and (hash8 == filledFFHash) and (hashA == filledFFHash):
        print("\n=== 8KB(4000H) Mirrored ROM Detected ===")
        romInfo['mapperType'] = MAPPER_NO_MAPPER_8K
        romInfo['mapperName'] = "8KB ROM"
        romInfo['romSize'] = 0x2000
        romInfo['validDataStart'] = 0x4000
        romInfo['validDataSize'] = 0x2000
        return True

    if (hash0 == filledFFHash) and (hash2 == filledFFHash) and (hash4 == filledFFHash) and (hash6 == filledFFHash) and (hash8 != filledFFHash) and (hash8 == hashA):
        print("\n=== 8KB(8000H) Mirrored ROM Detected ===")
        romInfo['mapperType'] = MAPPER_NO_MAPPER_8K
        romInfo['mapperName'] = "8KB ROM"
        romInfo['romSize'] = 0x2000
        romInfo['validDataStart'] = 0x8000
        romInfo['validDataSize'] = 0x2000
        return True

    if (hash0 == filledFFHash) and (hash2 == filledFFHash) and (hash4 != filledFFHash) and (hash6 == filledFFHash) and (hash8 == filledFFHash) and (hashA == filledFFHash):
        print("\n=== 8KB(4000H) Standard ROM Detected ===")
        romInfo['mapperType'] = MAPPER_NO_MAPPER_8K
        romInfo['mapperName'] = "8KB ROM"
        romInfo['romSize'] = 0x2000
        romInfo['validDataStart'] = 0x4000
        romInfo['validDataSize'] = 0x2000
        return True

    if (hash0 == filledFFHash) and (hash2 == filledFFHash) and (hash4 != filledFFHash) and (hash6 != filledFFHash) and (hash8 == filledFFHash) and (hashA == filledFFHash):
        print("\n=== 16KB(4000H) Standard ROM Detected ===")
        romInfo['mapperType'] = MAPPER_NO_MAPPER_16K
        romInfo['mapperName'] = "16KB ROM"
        romInfo['romSize'] = 0x4000
        romInfo['validDataStart'] = 0x4000
        romInfo['validDataSize'] = 0x4000
        return True

    if (hash0 == filledFFHash) and (hash2 == filledFFHash) and (hash4 == filledFFHash) and (hash6 == filledFFHash) and (hash8 != filledFFHash) and (hashA != filledFFHash):
        print("\n=== 16KB(8000H) Standard ROM Detected ===")
        romInfo['mapperType'] = MAPPER_NO_MAPPER_16K
        romInfo['mapperName'] = "16KB ROM"
        romInfo['romSize'] = 0x4000
        romInfo['validDataStart'] = 0x8000
        romInfo['validDataSize'] = 0x4000
        return True

    if hash0 == hash4 and hash2 == hash6 and hash4 == hash8 and hash6 == hashA:
        print("\n=== 16KB(4000H) Standard ROM Detected ===")
        romInfo['mapperType'] = MAPPER_NO_MAPPER_16K
        romInfo['mapperName'] = "16KB ROM"
        romInfo['romSize'] = 0x4000
        romInfo['validDataStart'] = 0x4000
        romInfo['validDataSize'] = 0x4000
        return True

    if (hash0 == filledFFHash) and (hash2 == filledFFHash) and hash4 == hash8 and hash6 == hashA:
        print("\n=== 16KB(4000H) Standard ROM Detected ===")
        romInfo['mapperType'] = MAPPER_NO_MAPPER_16K
        romInfo['mapperName'] = "16KB ROM"
        romInfo['romSize'] = 0x4000
        romInfo['validDataStart'] = 0x4000
        romInfo['validDataSize'] = 0x4000
        return True

    if (hash0 == filledFFHash) and (hash2 == filledFFHash) and hash4 != hash8 and hash6 != hashA:
        print("\n=== 32KB(4000H) Standard ROM Detected ===")
        romInfo['mapperType'] = MAPPER_NO_MAPPER_32K
        romInfo['mapperName'] = "32KB ROM"
        romInfo['romSize'] = 0x8000
        romInfo['validDataStart'] = 0x4000
        romInfo['validDataSize'] = 0x8000
        return True

    if hash0 == hash4 and hash2 == hash6 and hash4 != hash8 and hash6 != hashA:
        print("\n=== 32KB(4000H) Standard ROM Detected ===")
        romInfo['mapperType'] = MAPPER_NO_MAPPER_32K
        romInfo['mapperName'] = "32KB ROM"
        romInfo['romSize'] = 0x8000
        romInfo['validDataStart'] = 0x4000
        romInfo['validDataSize'] = 0x8000
        return True

    if hash0 == hash8 and hash2 == hashA and hash4 != hash8 and hash6 != hashA:
        print("\n=== 32KB(4000H) Standard ROM Detected ===")
        romInfo['mapperType'] = MAPPER_NO_MAPPER_32K
        romInfo['mapperName'] = "32KB ROM"
        romInfo['romSize'] = 0x8000
        romInfo['validDataStart'] = 0x4000
        romInfo['validDataSize'] = 0x8000
        return True

    if hash8 == filledFFHash and hashA == filledFFHash and hash4 != hash0 and hash6 != hash2:
        print("\n=== 32KB(0000H) Standard ROM Detected ===")
        romInfo['mapperType'] = MAPPER_NO_MAPPER_32K
        romInfo['mapperName'] = "32KB ROM"
        romInfo['romSize'] = 0x8000
        romInfo['validDataStart'] = 0x0000
        romInfo['validDataSize'] = 0x8000
        return True

    print("\n=== 48KB(0000H) Standard ROM Detected ===")
    romInfo['mapperType'] = MAPPER_NO_MAPPER_48K
    romInfo['mapperName'] = "48KB ROM"
    romInfo['romSize'] = 0xC000
    romInfo['validDataStart'] = 0x0000
    romInfo['validDataSize'] = 0xC000
    return True


def ReadMegaROM(ser: serial.Serial, romInfo: dict, outData: bytearray) -> bool:
    print(f"=== Reading {romInfo['mapperName']} ROM ===")
    if not setMegaROMconfig(ser, romInfo['mapperAddress'], romInfo['readAreaStart'], romInfo['readAreaSize']):
        return False
    if not slotMegaROMdump(ser, romInfo['readBankSize'], 0, romInfo['bankCount'], outData):
        print("Failed to read bank")
        return False

    print(f"\nTotal bytes read: {romInfo['bankCount'] * romInfo['readBankSize']} (0x{romInfo['bankCount'] * romInfo['readBankSize']:X})")
    return True


def ReadGeneric16K(ser: serial.Serial, romInfo: dict, outData: bytearray) -> bool:
    print("=== Reading Generic 16K ROM ===\n")

    bytesWritten = 0

    for bank in range(romInfo['bankCount']):
        if not slotWrite(ser, 0x4000, bank & 0xFF): return False
        if not slotWrite(ser, 0x8000, (bank + 1) & 0xFF): return False

        success, buffer = slotDump(ser, romInfo['readAreaStart'], romInfo['readAreaSize'])
        if not success:
            print(f"Failed to read bank {bank}")
            return False

        outData[bytesWritten:bytesWritten + romInfo['readBankSize']] = buffer[:romInfo['readBankSize']]
        bytesWritten += romInfo['readBankSize']

        print(f"Saved bank {bank} (0x{bytesWritten - romInfo['readBankSize']:04X} - 0x{bytesWritten - 1:04X})")

    print(f"\nTotal bytes read: {bytesWritten} (0x{bytesWritten:X})")
    return True


def ReadGeneric8K(ser: serial.Serial, romInfo: dict, outData: bytearray) -> bool:
    print("=== Reading Generic 8K ROM ===\n")

    bytesWritten = 0

    for bank in range(romInfo['bankCount']):
        if not slotWrite(ser, 0x4000, bank & 0xFF): return False
        if not slotWrite(ser, 0x6000, (bank + 1) & 0xFF): return False
        if not slotWrite(ser, 0x8000, (bank + 2) & 0xFF): return False
        if not slotWrite(ser, 0xA000, (bank + 3) & 0xFF): return False

        success, buffer = slotDump(ser, romInfo['readAreaStart'], romInfo['readAreaSize'])
        if not success:
            print(f"Failed to read bank {bank}")
            return False

        outData[bytesWritten:bytesWritten + romInfo['readBankSize']] = buffer[:romInfo['readBankSize']]
        bytesWritten += romInfo['readBankSize']

        print(f"Saved bank {bank} (0x{bytesWritten - romInfo['readBankSize']:04X} - 0x{bytesWritten - 1:04X})")

    print(f"\nTotal bytes read: {bytesWritten} (0x{bytesWritten:X})")
    return True


def ReadRType(ser: serial.Serial, romInfo: dict, outData: bytearray) -> bool:
    print("=== Reading R-TYPE ROM ===\n")

    bytesWritten = 0

    for bank in range(romInfo['bankCount']):
        if not slotWrite(ser, 0x7000, bank & 0xFF): return False

        success, buffer = slotDump(ser, romInfo['readAreaStart'], romInfo['readAreaSize'])
        if not success:
            print(f"Failed to read bank {bank}")
            return False

        outData[bytesWritten:bytesWritten + romInfo['readBankSize']] = buffer[:romInfo['readBankSize']]
        bytesWritten += romInfo['readBankSize']

        print(f"Saved bank {bank} (0x{bytesWritten - romInfo['readBankSize']:04X} - 0x{bytesWritten - 1:04X})")

    print(f"\nTotal bytes read: {bytesWritten} (0x{bytesWritten:X})")
    return True


def ReadCrossBlam(ser: serial.Serial, romInfo: dict, outData: bytearray) -> bool:
    print("=== Reading Cross Blam ROM ===\n")

    bytesWritten = 0
    fixedSize = romInfo['readAreaSize'] - romInfo['readBankSize']

    for bank in range(romInfo['bankCount']):
        if not slotWrite(ser, 0x7000, bank & 0xFF): return False

        readAreaStart = romInfo['readAreaStart']
        readAreaSize = fixedSize

        if bank != 0:
            readAreaStart += fixedSize
            readAreaSize = romInfo['readBankSize']

        success, buffer = slotDump(ser, readAreaStart, readAreaSize)
        if not success:
            print(f"Failed to read bank {bank}")
            return False

        outData[bytesWritten:bytesWritten + readAreaSize] = buffer[:readAreaSize]
        bytesWritten += readAreaSize

        print(f"Saved bank {bank} (0x{bytesWritten - readAreaSize:04X} - 0x{bytesWritten - 1:04X})")

    print(f"\nTotal bytes read: {bytesWritten} (0x{bytesWritten:X})")
    return True


def ReadHarryFox(ser: serial.Serial, romInfo: dict, outData: bytearray) -> bool:
    print("=== Reading Harry Fox -Yuki no Maou- ROM ===\n")

    bytesWritten = 0

    for bank in range(romInfo['bankCount']):
        if not slotWrite(ser, 0x6000, bank & 0xFF): return False
        if not slotWrite(ser, 0x7000, bank & 0xFF): return False

        success, buffer = slotDump(ser, romInfo['readAreaStart'], romInfo['readAreaSize'])
        if not success:
            print(f"Failed to read bank {bank}")
            return False

        outData[bytesWritten:bytesWritten + romInfo['readBankSize']] = buffer[:romInfo['readBankSize']]
        bytesWritten += romInfo['readBankSize']

        print(f"Saved bank {bank} (0x{bytesWritten - romInfo['readBankSize']:04X} - 0x{bytesWritten - 1:04X})")

    print(f"\nTotal bytes read: {bytesWritten} (0x{bytesWritten:X})")
    return True


def ReadHalNote(ser: serial.Serial, romInfo: dict, outData: bytearray) -> bool:
    print("=== Reading HALNOTE ROM ===\n")

    bytesWritten = 0

    if not slotWrite(ser, 0xC000, 0x03): return False

    for bank in range(romInfo['bankCount']):
        if not slotWrite(ser, 0x6FFF, bank & 0xFF): return False

        success, buffer = slotDump(ser, romInfo['readAreaStart'], romInfo['readAreaSize'])
        if not success:
            print(f"Failed to read bank {bank}")
            return False

        outData[bytesWritten:bytesWritten + romInfo['readBankSize']] = buffer[:romInfo['readBankSize']]
        bytesWritten += romInfo['readBankSize']

        print(f"Saved bank {bank} (0x{bytesWritten - romInfo['readBankSize']:04X} - 0x{bytesWritten - 1:04X})")

    print(f"\nTotal bytes read: {bytesWritten} (0x{bytesWritten:X})")
    return True


def ReadStandardROM(ser: serial.Serial, romInfo: dict, outData: bytearray) -> bool:
    print("=== Reading Standard ROM ===")

    print(f"Reading standard ROM: 0x{romInfo['validDataStart']:04X} - 0x{romInfo['validDataStart'] + romInfo['validDataSize'] - 1:04X} ({romInfo['validDataSize']} bytes)")

    # 一部の遅いROMやSLTSELにコンデンサが付いているソフト対策で速度を遅く設定
    if not hardwareSetting(ser, 0, 200):  return False
    if not hardwareSetting(ser, 1, 200 + 100):  return False

    success, buffer = slotDump(ser, romInfo['validDataStart'], romInfo['validDataSize'])
    if not success:
        print("Failed to read ROM")
        return False

    outData[0:romInfo['validDataSize']] = buffer

    print(f"\nTotal bytes read: {romInfo['validDataSize']} (0x{romInfo['validDataSize']:X})")
    return True


def ReadCompleteROM(ser: serial.Serial, romInfo: dict, outData: bytearray) -> bool:
    print("\n========== READING ROM DATA ==========")

    mtype = romInfo['mapperType']

    # ReadASCII16K(hSerial, romInfo, outData);
    if mtype in (MAPPER_ASCII_16K, MAPPER_ASCII_8K, MAPPER_KONAMI_8K, MAPPER_KONAMI_SCC, MAPPER_RTYPE):
        return ReadMegaROM(ser, romInfo, outData)
    elif mtype == MAPPER_GENERIC_16K:
        return ReadGeneric16K(ser, romInfo, outData)
    elif mtype == MAPPER_GENERIC_8K:
        return ReadGeneric8K(ser, romInfo, outData)
    # elif mtype == MAPPER_RTYPE:
    #     return ReadRType(ser, romInfo, outData)
    elif mtype == MAPPER_CROSSBLAM:
        return ReadCrossBlam(ser, romInfo, outData)
    elif mtype == MAPPER_HARRYFOX:
        return ReadHarryFox(ser, romInfo, outData)
    elif mtype == MAPPER_HALNOTE:
        return ReadHalNote(ser, romInfo, outData)
    elif mtype in (MAPPER_NO_MAPPER_8K, MAPPER_NO_MAPPER_16K, MAPPER_NO_MAPPER_32K, MAPPER_NO_MAPPER_48K, MAPPER_NO_MAPPER_64K):
        return ReadStandardROM(ser, romInfo, outData)
    else:
        print("Unknown mapper type")
        return False


def SaveROMToFile(filename: str, data: bytes) -> bool:
    print("\n=== Saving ROM to File ===\n")

    try:
        with open(filename, "wb") as f:
            f.write(data)
        print(f"ROM saved successfully: {filename} ({len(data)} bytes)")
        return True
    except Exception as e:
        print(f"Failed to create output file: {filename}")
        print(f"Error details: {e}")
        return False


# ============================================================================
# Main Mapper Detection
# ============================================================================

def DetectMapper(ser: serial.Serial, romInfo: dict) -> bool:
    print("\n========== ROM DETECTION START ==========")

    print("\n=== Testing MegaROM Mappers ===")

    if DetectASCII16K(ser, romInfo):
        return True
    if DetectASCII8K(ser, romInfo):
        return True
    if DetectKONAMI8K(ser, romInfo):
        return True
    if DetectKONAMI_SCC(ser, romInfo):
        return True
    if DetectGeneric16K(ser, romInfo):
        return True
    if DetectGeneric8K(ser, romInfo):
        return True
    if DetectRType(ser, romInfo):
        return True
    if DetectCrossBlam(ser, romInfo):
        return True
    if DetectHarryFox(ser, romInfo):
        return True
    if DetectHalnote(ser, romInfo):
        return True
    if DetectStandardROM(ser, romInfo):
        return True

    print("\nROM detection failed")
    return False


# ============================================================================
# Main Processing
# ============================================================================

def GetFileNameFromPath(path: str) -> str:
    pos = max(path.rfind("\\"), path.rfind("/"))
    if pos == -1:
        return path
    return path[pos + 1:]


def SanitizeMapperNameForFileName(mapperName: str) -> str:
    if not mapperName:
        return "UnknownMapper"

    result = []
    for ch in mapperName:
        if ch in "\\/:*?\"<>|":
            result.append('_')
        elif ch.isspace():
            result.append('_')
        else:
            result.append(ch)

    res_str = "".join(result)
    if not res_str:
        res_str = "UnknownMapper"

    return res_str


def ContainsABorCDAtOffset(romData: bytes, offset: int) -> bool:
    if not romData:
        return False

    if offset + 1 >= len(romData):
        return False

    val_0 = chr(romData[offset])
    val_1 = chr(romData[offset + 1])

    return (val_0 == 'A' and val_1 == 'B') or (val_0 == 'C' and val_1 == 'D')


def IsSuccessfulROMImage(romData: bytes) -> bool:
    return (ContainsABorCDAtOffset(romData, 0x0000) or
            ContainsABorCDAtOffset(romData, 0x4000) or
            ContainsABorCDAtOffset(romData, 0x8000) or
            ContainsABorCDAtOffset(romData, 0x3C000))


def EscapeCsvField(s: str) -> str:
    # 内部のダブルクォーテーションをエスケープ
    return s.replace('"', '""')


def GetCurrentDateTimeString() -> str:
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


def AppendDumpListLogCsv(outputDir: str, dbStatus: str, romFileStatus: str, status: str,
                           title: str, company: str, year: str, system: str, remark: str,
                           romType: str, romSize: int, sha1: str, dumpDateTime: str) -> bool:
    
    csvPath = JoinPath(outputDir if outputDir else ".", "dump_list_log.csv")
    needHeader = not os.path.exists(csvPath)

    try:
        with open(csvPath, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            if needHeader:
                writer.writerow([
                    "DBステータス", "ROMファイルの状態", "ステータス", "タイトル",
                    "メーカ", "年", "システム", "備考", "ROMタイプ", "容量", "SHA1値", "ダンプ日時"
                ])
            writer.writerow([
                dbStatus, romFileStatus, status, title, company, year,
                system, remark, romType, str(romSize), sha1, dumpDateTime
            ])
        return True
    except Exception as e:
        print(f"CSV write error: {e}")
        return False


def CalcFileSHA1Hex(filePath: str) -> tuple[bool, str]:
    if not os.path.exists(filePath):
        return False, ""

    try:
        with open(filePath, "rb") as f:
            data = f.read()
        return True, CalcSHA1Hex(data)
    except Exception:
        return False, ""


def FindXMLAttributeValue(text: str, key: str) -> tuple[bool, str]:
    pattern = key + "=\""
    pos = text.find(pattern)
    if pos == -1:
        return False, ""

    pos += len(pattern)
    end = text.find("\"", pos)
    if end == -1:
        return False, ""

    val = DecodeXmlEntities(text[pos:end])
    return True, val


def FindROMInfoBySha1FromSoftwareDB(xmlPath: str, sha1: str) -> dict:
    dbInfo = {
        "found": False, "title": "", "system": "", "company": "", "year": "",
        "status": "", "remark": "", "has_different_system_duplicate": False
    }

    try:
        with open(xmlPath, 'r', encoding='utf-8-sig', errors='ignore') as f:
            xml = f.read()
    except Exception:
        return dbInfo

    matchedTitle = ""
    matchedSystem = ""
    searchPos = 0

    while True:
        softwareStart = xml.find("<software ", searchPos)
        if softwareStart == -1:
            break

        softwareTagEnd = xml.find(">", softwareStart)
        if softwareTagEnd == -1:
            break

        softwareEnd = xml.find("</software>", softwareTagEnd)
        if softwareEnd == -1:
            break

        softwareTag = xml[softwareStart:softwareTagEnd + 1]
        softwareBody = xml[softwareTagEnd + 1:softwareEnd]

        romSearchPos = 0
        while True:
            romStart = softwareBody.find("<rom ", romSearchPos)
            if romStart == -1:
                break

            romEnd = softwareBody.find("/>", romStart)
            if romEnd == -1:
                break

            romTag = softwareBody[romStart:romEnd + 2]

            success, romSha1 = FindXMLAttributeValue(romTag, "sha1")
            if success:
                if romSha1.lower() == sha1.lower():
                    dbInfo["found"] = True
                    _, dbInfo["title"] = FindXMLAttributeValue(softwareTag, "title")
                    _, dbInfo["system"] = FindXMLAttributeValue(softwareTag, "system")
                    _, dbInfo["company"] = FindXMLAttributeValue(softwareTag, "company")
                    _, dbInfo["year"] = FindXMLAttributeValue(softwareTag, "year")
                    _, dbInfo["status"] = FindXMLAttributeValue(romTag, "status")
                    _, dbInfo["remark"] = FindXMLAttributeValue(romTag, "remark")
                    
                    matchedTitle = dbInfo["title"]
                    matchedSystem = dbInfo["system"]
                    break

            romSearchPos = romEnd + 2

        if dbInfo["found"]:
            break

        searchPos = softwareEnd + 11

    # 同じタイトルで異なる機種のデータが存在するかをチェック
    if dbInfo["found"] and matchedTitle and matchedSystem:
        searchPos = 0
        while True:
            softwareStart = xml.find("<software ", searchPos)
            if softwareStart == -1:
                break

            softwareTagEnd = xml.find(">", softwareStart)
            if softwareTagEnd == -1:
                break

            softwareEnd = xml.find("</software>", softwareTagEnd)
            if softwareEnd == -1:
                break

            softwareTag = xml[softwareStart:softwareTagEnd + 1]

            _, title = FindXMLAttributeValue(softwareTag, "title")
            _, system = FindXMLAttributeValue(softwareTag, "system")

            if title and system:
                if title.lower() == matchedTitle.lower() and system.lower() != matchedSystem.lower():
                    dbInfo["has_different_system_duplicate"] = True
                    break

            searchPos = softwareEnd + 11

    return dbInfo


def FindROMInfoWithPriority(sha1: str) -> tuple[dict, str]:
    dbInfo = {
        "found": False, "title": "", "system": "", "company": "", "year": "",
        "status": "", "remark": "", "has_different_system_duplicate": False
    }
    usedXmlPath = ""

    softwareDbPath = "softwaredb.xml"
    softwareDbExists = os.path.isfile(softwareDbPath)

    msxRomDbPath = "msxromdb.xml"
    msxRomDbExists = os.path.isfile(msxRomDbPath)

    if softwareDbExists:
        usedXmlPath = softwareDbPath
        return FindROMInfoBySha1FromSoftwareDB(softwareDbPath, sha1), usedXmlPath

    if msxRomDbExists:
        usedXmlPath = msxRomDbPath
        oldInfo = FindROMInfoBySha1(msxRomDbPath, sha1)

        dbInfo["found"] = oldInfo["found"]
        dbInfo["title"] = oldInfo["title"]
        dbInfo["system"] = oldInfo["system"]
        dbInfo["company"] = oldInfo["company"]
        dbInfo["year"] = oldInfo["year"]
        dbInfo["status"] = ""
        dbInfo["remark"] = ""
        return dbInfo, usedXmlPath

    return dbInfo, usedXmlPath


def IsIgnorableTagValue(value: str) -> bool:
    if not value:
        return True
    val_lower = value.lower()
    if val_lower in ("unknown", "n/a", "none", "-"):
        return True
    return False


def BuildAutoFileName(dbInfo: dict) -> str:
    titleW = SanitizeFileName(dbInfo["title"])
    systemW = SanitizeFileName(dbInfo["system"])
    companyW = SanitizeFileName(dbInfo["company"])
    yearW = SanitizeFileName(dbInfo["year"])
    statusW = SanitizeFileName(dbInfo["status"])
    remarkW = SanitizeFileName(dbInfo["remark"])

    # タイトルが同じゲームで機種が異なる重複データがDBに存在する時だけシステム名をファイル名に追加
    if dbInfo.get("has_different_system_duplicate", False):
        renamedFile = f"{titleW}({systemW})-{companyW}({yearW})"
    else:
        # 重複がなければシステム名無し
        renamedFile = f"{titleW}-{companyW}({yearW})"

    if not IsIgnorableTagValue(statusW):
        renamedFile += f"[{statusW}]"

    if not IsIgnorableTagValue(remarkW):
        renamedFile += f"[{remarkW}]"

    renamedFile += ".rom"
    return renamedFile


def ProcessROMRead(outputFileArg: str, autoFileNameMode: bool, logMode: bool) -> int:
    # COMポート一覧を取得
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("Failed to get device info")
        return 1

    # outputFileArg == None の場合は、自動ファイル名モードと同じ動作にする
    if outputFileArg is None:
        autoFileNameMode = True

    requestedOutputPath = outputFileArg if outputFileArg else ""
    outputDir = "."

    if autoFileNameMode:
        # 自動ファイル名モード時は outputFileArg を出力先ディレクトリとして扱う
        if requestedOutputPath:
            outputDir = requestedOutputPath
    else:
        # 通常モード時は outputFileArg を出力ファイル名として扱う
        if requestedOutputPath:
            outputDir = GetDirectoryFromPath(requestedOutputPath)

    foundDevice = False

    for port in ports:
        devdesc = port.hwid.upper()
        # USB接続に限定 (C++の wcsncmp(L"USB\\", devdesc, 4) == 0 の再現)
        if not ("USB" in devdesc or "VID" in devdesc):
            continue

        print(f"Found USB COM port: {port.device}\n")

        try:
            # 115200bps, 8bit, None parity, 1 stopbit でオープン
            ser = serial.Serial(
                port=port.device,
                baudrate=115200,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.5,
                write_timeout=0.5
            )
        except Exception:
            print("Failed to open COM port")
            continue

        ser.reset_input_buffer()
        ser.reset_output_buffer()

        print(f"Connected to {port.device}\n")

        if not FirmwareVersionCheck(ser):
            print("ERROR: Firmware version check failed\n")
            ser.close()
            continue

        if not SlotCheck(ser):
            print("ERROR: Cartridge is not properly inserted\n")
            ser.close()
            continue

        startTime = int(time.time() * 1000)

        if not SlotPowerOn(ser):
            print("ERROR: Failed to power on slot\n")
            ser.close()
            continue

        if not SlotReset(ser):
            print("ERROR: Failed to reset on slot\n")
            SlotPowerOff(ser)
            ser.close()
            continue

        if not CheckHashWithRetry(ser):
            print("ERROR: Failed to ROM Read :-( on slot\n")
            SlotPowerOff(ser)
            ser.close()
            continue

        romInfo = {'mapperType': MAPPER_UNKNOWN, 'mapperName': "", 'bankCount': 0, 'romSize': 0}
        if not DetectMapper(ser, romInfo):
            print("Mapper detection failed\n")
            SlotPowerOff(ser)
            ser.close()
            continue

        if not SlotReset(ser):
            print("ERROR: Failed to reset on slot\n")
            SlotPowerOff(ser)
            ser.close()
            continue

        print("\n========== DETECTION RESULT ==========")
        print(f"Detected: {romInfo['mapperName']}")
        print(f"Bank Count: {romInfo['bankCount']}")
        print(f"ROM Size: {romInfo['romSize']} bytes (0x{romInfo['romSize']:X})")

        romData = bytearray(romInfo['romSize'])

        if not ReadCompleteROM(ser, romInfo, romData):
            print("ROM reading failed")
            SlotPowerOff(ser)
            ser.close()
            continue

        sha1 = CalcSHA1Hex(bytes(romData))
        print("\n========== SHA1 ==========")
        print(sha1)

        savePath = ""
        decidedSavePath = False
        romFileStatus = "New"

        dbInfo, usedXmlPath = FindROMInfoWithPriority(sha1)

        if usedXmlPath:
            if dbInfo["found"]:
                print("\n========== DB MATCH ==========")
                print(f"Title  : {dbInfo['title']}")
                print(f"System : {dbInfo['system']}")
                print(f"Company: {dbInfo['company']}")
                print(f"Year   : {dbInfo['year']}")

                if dbInfo["status"]:
                    print(f"Status : {dbInfo['status']}")
                if dbInfo["remark"]:
                    print(f"Remark : {dbInfo['remark']}")

                renamedFile = BuildAutoFileName(dbInfo)
                savePath = JoinPath(outputDir, renamedFile)
                decidedSavePath = True
            else:
                print(f"\n========== DB MATCH ==========")
                print(f"No match found in {usedXmlPath}")

                if not autoFileNameMode and requestedOutputPath:
                    print("Saving with specified output file name.")
                    savePath = requestedOutputPath
                    decidedSavePath = True
                else:
                    print("Saving with auto-generated file name.")
                    mapperW = SanitizeMapperNameForFileName(romInfo['mapperName'])
                    renamedFile = f"Unknown_{sha1}[{mapperW}].rom"
                    savePath = JoinPath(outputDir, renamedFile)
                    decidedSavePath = True
        else:
            print("\nXML database not found: softwaredb.xml / msxromdb.xml")

            if not autoFileNameMode and requestedOutputPath:
                print("Saving with specified output file name.")
                savePath = requestedOutputPath
                decidedSavePath = True
            else:
                print("Saving with auto-generated file name.")
                mapperW = SanitizeMapperNameForFileName(romInfo['mapperName'])
                renamedFile = f"Unknown_{sha1}[{mapperW}].rom"
                savePath = JoinPath(outputDir, renamedFile)
                decidedSavePath = True

        if not decidedSavePath or not savePath:
            print("Failed to determine output file name.")
            SlotPowerOff(ser)
            ser.close()
            continue

        finalDir = GetDirectoryFromPath(savePath)
        finalName = GetFileNameFromPath(savePath)

        if not IsSuccessfulROMImage(bytes(romData)):
            finalName = "[unsuccessful]" + finalName
            romFileStatus = "Unsuccessful"

        finalOutputPath = JoinPath(finalDir, finalName)

        if os.path.exists(finalOutputPath):
            success, existingSha1 = CalcFileSHA1Hex(finalOutputPath)
            if success:
                print("\n========== EXISTING FILE SHA1 ==========")
                print(existingSha1)

                if existingSha1 == sha1:
                    finalName = "[same]" + finalName
                    romFileStatus = "Same"
                else:
                    finalName = f"[other_{sha1}]" + finalName
                    romFileStatus = "Other"
            else:
                print("\n========== EXISTING FILE SHA1 ==========")
                print("Failed to calculate SHA1 of existing file")
                finalName = "[same]" + finalName

            finalOutputPath = JoinPath(finalDir, finalName)
        else:
            if not IsSuccessfulROMImage(bytes(romData)):
                romFileStatus = "Unsuccessful"

        if not SaveROMToFile(finalOutputPath, bytes(romData)):
            print("[ERROR] File save failed")
            SlotPowerOff(ser)
            ser.close()
            continue

        if logMode:
            dbStatus = "MATCH" if dbInfo["found"] else "Unknown"
            title = dbInfo["title"]
            company = dbInfo["company"]
            year = dbInfo["year"]
            system = dbInfo["system"]
            romType = romInfo['mapperName'] if romInfo['mapperName'] else "Unknown"
            dumpDateTime = GetCurrentDateTimeString()
            status = dbInfo["status"]
            remark = dbInfo["remark"]

            if not AppendDumpListLogCsv(
                outputDir,
                dbStatus,
                romFileStatus,
                status,
                title,
                company,
                year,
                system,
                remark,
                romType,
                romInfo['romSize'],
                sha1,
                dumpDateTime
            ):
                print("WARNING: Failed to append dump_list_log.csv")

        print(f"\nSaved output: {finalOutputPath}")
        print("\nROM read and save completed successfully!\n")

        SlotPowerOff(ser)
        ser.close()

        endTime = int(time.time() * 1000)
        print(f"Execution time: {endTime - startTime} ms")

        foundDevice = True
        break

    if not foundDevice:
        print("No suitable device found")
        return 1

    return 0


# ============================================================================
# Entry Point
# ============================================================================

def main():
    print("MSX Game Adapter ROM Dumper (Python Port)")
    print("Copyright @v9938")
    # Pythonでの日付表示
    print(f"Run Date: {datetime.datetime.now().strftime('%b %d %Y %H:%M:%S')}")
    print()

    autoFileNameMode = False
    logMode = False
    outputFileArg = None

    args = sys.argv[1:]
    
    for arg in args:
        if arg.lower() == "/auto":
            autoFileNameMode = True
        elif arg.lower() == "/log":
            logMode = True
        else:
            outputFileArg = arg

    # 通常モード時は出力ファイル名必須
    # /auto 時は引数省略ならカレントディレクトリを使う
    if not autoFileNameMode and outputFileArg is None:
        prog_name = os.path.basename(sys.argv[0]) # ファイル名のみを抽出
        print(f"Usage: python {prog_name} <output_file_path> [/auto] [/log]")
        print()
        print("Normal mode:")
        print(f"  python {prog_name} <output_file_path> [/log]")
        print("    Save ROM using the specified output file path.")
        print()
        print("    /log option appends dump information to dump_list_log.csv.")
        print()
        print("Auto file name mode:")
        print(f"  python {prog_name} /auto [output_directory]  [/log]")
        print("    Save ROM using an automatically generated file name.")
        print("    If [output_directory] is omitted, the current directory is used.")
        print()
        print("    /log option appends dump information to dump_list_log.csv.")
        print()
        print("Notes:")
        print("  softwaredb.xml is used if present.")
        print("  If softwaredb.xml is not present, msxromdb.xml is used.")
        sys.exit(1)

    result = ProcessROMRead(outputFileArg, autoFileNameMode, logMode)
    print("Done.")
    sys.exit(result)


if __name__ == '__main__':
    main()

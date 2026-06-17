#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Based on the following program ->
#  MSXROMReader.c - MSX ROM Reader Program
#  Purpose: Read ROM data from MSX cartridges via serial communication
#  Supports: MegaROM mappers detection and ROM dump
#  Copyright @v9938
#  https://github.com/v9938/MSXPLAYer_GameAdapter/tree/main/SOFTWARE/MSXCR_ROMDUMPER_FW260519

import sys
import os
import time
import re
import hashlib
import xml.etree.ElementTree as ET
from enum import Enum
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

DISPLAY_CMD         = False # Display CMD
DISPLAY_HASH        = False # Display HASH

# ============================================================================
# Constants and Defines
# ============================================================================

BANK_SIZE           = 0x2000  # 8K bank size
SLOT_ADDR_BASE      = 0x4000  # Slot base address
HASH_SIZE           = 0x1000  # Hash calculation size
#HASH_SIZE           = 0x1F00  # Hash calculation size
TIMEOUT_MS          = 5000
SRAM_THRESHOLD      = 8       # Number of identical banks to detect SRAM

BAUDRATE = 115200           # USBシリアルインターフェースの通信速度
SERIAL_TIMEOUT = 0.5        # 読み込みのタイムアウト時間（秒）

# MegaROM Mapper Types
class MapperType(Enum):
    UNKNOWN         = 0
    ASCII_16K       = 1     # ASCII 16K
    ASCII_8K        = 2     # ASCII 8K
    KONAMI_8K       = 3     # Konami 8K
    KONAMI_SCC      = 4     # Konami SCC
    GENERIC_16K     = 5     # Generic 16K
    GENERIC_8K      = 6     # Generic 8K
    RTYPE           = 7     # R-Type
    HARRYFOX        = 8     # HARRY FOX
    FMPAC           = 9     # FMPAC
    HALNOTE         = 10    # Hal Note
    NO_MAPPER_16K   = 11    # 16KB no mapper
    NO_MAPPER_32K   = 12    # 32KB no mapper
    NO_MAPPER_48K   = 13    # 48KB no mapper

# 基本的なマッパー表示名の定義リスト
MAPPER_DEFINITIONS = {
    MapperType.UNKNOWN:         "Unknown",
    MapperType.ASCII_16K:       "ASCII 16K",
    MapperType.ASCII_8K:        "ASCII 8K",
    MapperType.KONAMI_8K:       "KONAMI 8K",
    MapperType.KONAMI_SCC:      "KONAMI SCC",
    MapperType.GENERIC_16K:     "Generic 16K",
    MapperType.GENERIC_8K:      "Generic 8K",
    MapperType.RTYPE:           "R-Type",
    MapperType.HARRYFOX:        "HARRY FOX",
    MapperType.FMPAC:           "FMPAC",
    MapperType.HALNOTE:         "HALNOTE",
    MapperType.NO_MAPPER_16K:   "16KB Standard ROM",
    MapperType.NO_MAPPER_32K:   "32KB Standard ROM",
    MapperType.NO_MAPPER_48K:   "48KB Standard ROM"
}

def get_supported_mappers() -> list:
    """定義済みマッパー一覧リスト"""
    return [name for mtype, name in MAPPER_DEFINITIONS.items() if mtype != MapperType.UNKNOWN]

# ROM Information Structure
@dataclass
class ROM_INFO:
    mapperType: MapperType = MapperType.UNKNOWN
    mapperName:     str  = ""
    romSize:        int  = 0        # in bytes
    bankCount:      int  = 0        # number of banks
    hasSRAM:        bool = False    # has SRAM
    validDataStart: int  = 0        # start of valid data
    validDataSize:  int  = 0        # size of valid data
    readBankSize:   int  = 0        # size per bank read
    readAreaStart:  int  = 0        # start address for reading
    readAreaSize:   int  = 0        # size of read area

# ============================================================================
# Utility Functions
# ============================================================================

def sanitize_file_name(name: str) -> str:
    invalid_chars = '<>:"/\\|?*'
    out = name
    for char in invalid_chars:
        out = out.replace(char, '_')
    out = "".join([c for c in out if ord(c) >= 32])
    out = out.strip().rstrip('.')
    return out if out else "unknown"

def sanitize_mapper_name_for_file_name(mapper_name: str) -> str:
    if not mapper_name:
        return "UnknownMapper"
    invalid_chars = '\\/:*?"<>|'
    out = mapper_name
    for char in invalid_chars:
        out = out.replace(char, '_')
    return out.replace(' ', '_')

# ============================================================================
# SHA-1 (Pythonの hashlibで全代替、Hash7936のみ手動計算)
# ============================================================================

# ============================================================================
# Hash Calculation
# ============================================================================

def hash_7936(data: bytes, address: int) -> int:
    hash_val = 0x5381
    if address + HASH_SIZE > len(data):
        return 0
    
    for i in range(HASH_SIZE):
        # 32ビット符号なし整数とするために0xFFFFFFFFでマスク
        hash_val = (((hash_val << 5) + hash_val) & 0xFFFFFFFF) ^ data[address + i]
    return hash_val

def hash_filled_ff(length: int) -> int:
    hash_val = 0x5381
    
    for _ in range(length):
        # DJB2アルゴリズムの変形処理と0xFFのXOR操作
        hash_val = ((hash_val << 5) + hash_val) ^ 0xff
        # 32ビット符号なし整数とするために0xFFFFFFFFでマスク
        hash_val &= 0xFFFFFFFF
        
    return hash_val

# ============================================================================
# XML DB Search
# ============================================================================

def get_software_basic_info(software: ET.Element, is_msxromdb: bool) -> Tuple[str, str, str, str]:
    """XML形式（softwaredb または msxromdb）を判別し、ゲーム情報を抽出します。"""
    if not is_msxromdb:
        # softwaredb.xml: 属性値（attribute）から抽出。
        title   = software.get('title') or ""
        company = software.get('company') or ""
        year    = software.get('year') or ""
        system  = software.get('system') or ""
        return title.strip(), company.strip(), year.strip(), system.strip()
    else:
        # msxromdb.xml: 子要素から抽出。
        title_el   = software.find('title')
        company_el = software.find('company')
        year_el    = software.find('year')
        system_el  = software.find('system')
        
        title   = title_el.text.strip() if (title_el is not None and title_el.text) else ""
        company = company_el.text.strip() if (company_el is not None and company_el.text) else ""
        year    = year_el.text.strip() if (year_el is not None and year_el.text) else ""
        system  = system_el.text.strip() if (system_el is not None and system_el.text) else ""
        
        return title.strip(), company.strip(), year.strip(), system.strip()

def parse_xml_db(xml_path: str, target_sha1: str) -> Dict[str, Any]:
    result = {
        "found":   False, 
        "title":   "", 
        "company": "", 
        "year":    "", 
        "system":  "", 
        "status":  "", 
        "remark":  "", 
        "has_different_system_duplicate": False
    }
    if not os.path.exists(xml_path):
        return result

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # ファイル名から msxromdb.xml であるか自動判定
        is_msxromdb = (os.path.basename(xml_path).lower() == "msxromdb.xml")
        
        matched_software = None
        matched_rom_or_dump = None
        
        # XMLツリー全体から再帰的に <software> 要素を縦断探索
        for software in root.iter('software'):
            if not is_msxromdb:
                # softwaredb.xml 形式の検査 (<rom>タグのアトリビュートを走査)
                roms = list(software.iter('rom'))
                for rom in roms:
                    sha1_val = rom.get('sha1')
                    if sha1_val and sha1_val.strip().lower() == target_sha1.lower():
                        matched_software = software
                        matched_rom_or_dump = rom
                        break
            else:
                # msxromdb.xml 形式の検査 (<dump><hash>タグの要素テキストを走査)
                dumps = list(software.findall('dump'))
                for dump in dumps:
                    hash_elem = dump.find('.//hash') # rom または megaromの子要素
                    if hash_elem is not None and hash_elem.text:
                        sha1_val = hash_elem.text.strip()
                        if sha1_val.lower() == target_sha1.lower():
                            matched_software = software
                            matched_rom_or_dump = dump
                            break
            if matched_software is not None:
                break

        # データが見つかった場合の処理
        if matched_software is not None:
            title, company, year, system = get_software_basic_info(matched_software, is_msxromdb)
            
            # softwaredb.xml の場合は rom タグから status と remark を抽出
            status = ""
            remark = ""
            if not is_msxromdb and matched_rom_or_dump is not None and matched_rom_or_dump.tag == 'rom':
                status = (matched_rom_or_dump.get('status') or "").strip()
                remark = (matched_rom_or_dump.get('remark') or "").strip()
                
            result.update({
                "found":   True,
                "title":   title,
                "company": company,
                "year":    year,
                "system":  system,
                "status":  status,
                "remark":  remark,
                "has_different_system_duplicate": False
            })
            
            # 同一ゲームタイトルで機種名が異なるデータを存在チェック
            # softwaredb が 複数機種で出ているゲームをタイトルで識別出来ない為
            has_different_system_duplicate = False
            target_title_lower = title.lower()
            target_system_lower = system.lower()
            
            for software in root.iter('software'):
                s_title, s_company, s_year, s_system = get_software_basic_info(software, is_msxromdb)
                if (s_title.lower() == target_title_lower and
                    s_system.lower() != target_system_lower):
                    has_different_system_duplicate = True
                    break
                    
            result["has_different_system_duplicate"] = has_different_system_duplicate
            return result
                            
    except Exception as e:
        print(f"XML parse error in {xml_path}: {e}")
        
    return result

def find_rom_info_with_priority(sha1: str) -> Tuple[Dict[str, Any], Optional[str]]:
    paths = ["softwaredb.xml", "msxromdb.xml"]
    for path in paths:
        if os.path.exists(path):
            res = parse_xml_db(path, sha1)
            if res["found"]:
                return res, path
            else:
                return res, path
    return {"found": False}, None

def is_ignorable_tag_value(val: str) -> bool:
    return not val or val.lower() in ["unknown", "n/a", "none", "-"]

def build_auto_file_name(db_info: Dict[str, Any]) -> str:
    title   = sanitize_file_name(db_info.get("title", "unknown"))
    company = sanitize_file_name(db_info.get("company", "unknown"))
    year    = sanitize_file_name(db_info.get("year", "unknown"))
    system  = sanitize_file_name(db_info.get("system", "unknown"))
    status  = sanitize_file_name(db_info.get("status", ""))
    remark  = sanitize_file_name(db_info.get("remark", ""))

    # タイトルが同じゲームで機種が異なる重複データがDBに存在する時だけシステム名をファイル名に追加
    if db_info.get("has_different_system_duplicate", False):
        renamed = f"{title}({system})-{company}({year})"
    else:
        # 重複がなければシステム名無し
        renamed = f"{title}-{company}({year})"

    if not is_ignorable_tag_value(status):
        renamed += f"[{status}]"
    if not is_ignorable_tag_value(remark):
        renamed += f"[{remark}]"
    return renamed + ".rom"

def is_successful_rom_image(rom_data: bytes) -> bool:
    offsets = [0x0000, 0x4000, 0x8000, 0x3C000]
    for offset in offsets:
        if offset + 1 < len(rom_data):
            header = rom_data[offset:offset+2]
            if header in [b'AB', b'CD']:
                return True
    return False

# ============================================================================
# Serial Communication Functions
# ============================================================================

def find_com_port() -> Optional[str]:
    try:
        from serial.tools import list_ports
        ports = list_ports.comports()
        for port in ports:
            if "USB" in (port.hwid or "").upper() or "USB" in (port.device or "").upper():
                return port.device
    except ImportError:
        pass
    return None

def send_command(ser: Any, command: str) -> bool:
    try:
        tmpstr = f"{command}\r\n".encode('ascii')
        if DISPLAY_CMD: print(f"cmd:{command}")
        ser.write(tmpstr)
        ser.flush()
        return True
    except Exception as e:
        print(f"SendCommand error: {e}")
        return False

def recv_response(ser: Any, timeout_ms: int = TIMEOUT_MS) -> Tuple[bool, str]:
    response_buf = bytearray()
    start_time = time.time() * 1000

    while True:
        if ser.in_waiting > 0:
            ch = ser.read(1)
            if not ch:
                continue
            response_buf.extend(ch)
            start_time = time.time() * 1000
            
            try:
                resp_str = response_buf.decode('ascii', errors='ignore')
                if "OK\n" in resp_str:
                    return True, resp_str
                if "FAIL\n" in resp_str:
                    return False, resp_str
            except Exception:
                pass
        else:
            current_time = time.time() * 1000
            if current_time - start_time >= timeout_ms:
                print("Response timeout")
                return False, ""
            time.sleep(0.001)

def recv_binary_block(ser: Any, length: int) -> Optional[bytes]:
    recv_buf = bytearray()
    start_time = time.time()
    
    timeout = (length / 10000.0) + 2.0
    
    while len(recv_buf) < length:
        to_read = length - len(recv_buf)
        data = ser.read(to_read)
        if data:
            recv_buf.extend(data)
            start_time = time.time()
        else:
            if time.time() - start_time > timeout:
                print("RecvBinaryBlock timeout")
                break
    
    if len(recv_buf) == length:
        return bytes(recv_buf)
    return None

# ============================================================================
# Slot Access Functions
# ============================================================================

def slot_write(ser: Any, address: int, data: int) -> bool:
    cmd = f"SMWR,{address:04X},{data:02X}"
    if not send_command(ser, cmd):
        return False
    ok, _ = recv_response(ser)
    return ok

def slot_read(ser: Any, address: int) -> Tuple[bool, int]:
    cmd = f"SMRD,{address:04X}"
    if not send_command(ser, cmd):
        return False, 0
    ok, resp = recv_response(ser)
    if ok:
        match = re.search(r'[0-9A-Fa-f]+\s*:\s*([0-9A-Fa-f]{2})', resp)
        if match:
            return True, int(match.group(1), 16)
    return False, 0

def slot_dump(ser: Any, address: int, length: int) -> Optional[bytes]:
    cmd = f"SMTR,{address:04X},{length:04X}\r\nBSND,0,{length:04X}"
    if not send_command(ser, cmd):
        return None
    
    ok, _ = recv_response(ser)
    if not ok:
        return None
    
    data = recv_binary_block(ser, length)
    if data is None:
        return None
        
    ok, _ = recv_response(ser)
    if not ok:
        return None
        
    return data

def slot_read_hash(ser: Any, address: int, length: int) -> Tuple[bool, int]:
    cmd = f"SMTH,{address:04X},{length:04X}"
    if not send_command(ser, cmd):
        return False, 0
    ok, resp = recv_response(ser)
    if ok:
        match = re.search(r'[0-9A-Fa-f]+\s*:\s*([0-9A-Fa-f]+)', resp)
        if match:
            return True, int(match.group(1), 16)
    return False, 0

def hardware_setting(ser: Any, address: int, data: int) -> bool:
    cmd = f"HSET,{address:04X},{data:X}"
    if not send_command(ser, cmd):
        return False
    ok, _ = recv_response(ser)
    return ok

# ============================================================================
# Cartridge Control Functions
# ============================================================================

def slot_check(ser: Any) -> bool:
    print("Checking cartridge insertion...")
    if not send_command(ser, "SCHK"):
        print("Failed to send SCHK command")
        return False
    ok, resp = recv_response(ser)
    if not ok:
        print("Failed to receive SCHK response")
        return False
    if "0010" in resp:
        print("Cartridge is properly inserted")
        return True
    return False

def slot_power_on(ser: Any) -> bool:
    print("Turning on slot power...")
    if not send_command(ser, "SPON"):
        print("Failed to send SPON command")
        return False
    ok, resp = recv_response(ser)
    if not ok:
        print("Failed to receive SPON response")
        return False
    if "OK" in resp:
        print("Slot power turned on successfully")
        return True
    return False

def slot_power_off(ser: Any) -> bool:
    print("Turning off slot power...")
    if not send_command(ser, "SPOFF"):
        print("Failed to send SPOFF command")
        return False
    ok, resp = recv_response(ser)
    if not ok:
        print("Failed to receive SPOFF response")
        return False
    if "OK\n" in resp:
        print("Slot power turned off successfully")
        return True
    print("ERROR: Failed to turn off slot power")
    return False

def slot_reset(ser: Any) -> bool:
    #    print("Slot reset.\n")
    if not send_command(ser, "SRST"):
        print("Failed to send SRST command")
        return False
    ok, resp = recv_response(ser)
    if not ok:
        print("Failed to receive SRST response")
        return False
    if "OK\n" in resp:
        return True
    print("ERROR: Failed to turn off slot power")
    return False

# ============================================================================
# ROM ACCESS Timing Setting
# ============================================================================

def read_hash_5_match(ser: Any) -> Tuple[bool, int]:
    filled_ff_hash = hash_filled_ff(HASH_SIZE)

    for retry in range(2):
        addr = 0x4000 if retry == 0 else 0x8000
        hashes = []
        for i in range(5):
            ok, h_val = slot_read_hash(ser, addr, HASH_SIZE)
            if not ok:
                print(f"slotReadHash failed at try {i + 1}")
                return False, 0
            hashes.append(h_val)
            
        if DISPLAY_HASH:
            print(f"Hash(addr={addr:04X}) = {hashes[0]:08X}, {hashes[1]:08X}, {hashes[2]:08X}, {hashes[3]:08X}, {hashes[4]:08X}")

        # 5回すべて一致しているか
        if not (hashes[0] == hashes[1] and hashes[0] == hashes[2] and hashes[0] == hashes[3] and hashes[0] == hashes[4]):
            #            print("Hash mismatch")
            return False, 0

        # 0x4000 で全て filledFFHash の場合のみ、0x8000 で再試行
        if hashes[0] == filled_ff_hash:
            if retry == 0:
                continue
            # 0x8000 側でも無効値だった
            return False, 0

        return True, hashes[0]
            
    return False, 0

# address 0 を 100(1us) ずつ 1000(10us) まで変更しながら hash 一致を確認
def sweep_address_0_and_check(ser: Any) -> bool:
    for d in range(100, 1100, 100):
        print(f"HardwareSetting (wait {d//100} us)")
        if not hardware_setting(ser, 0, d):
            return False
        ok, _ = read_hash_5_match(ser)
        if ok:
            print(f"{d//100}us PASS")
            return True
    return False

# hash の安定化確認
def check_hash_with_retry(ser: Any) -> bool:
    print("Read Timing Check.")
    # default設定値
    if not hardware_setting(ser, 0, 0): return False
    if not hardware_setting(ser, 0, 100): return False

    print("Checking default setting... ", end="")
    ok, _ = read_hash_5_match(ser)
    if ok:
        print("PASS")
        return True
    print("FAILED")

    print("Phase 1: Checking setting1 ... (/rd = 1us) ")
    # Phase 1:
    # address 0 を 1us 刻みで 100us まで変更しながら確認
    if sweep_address_0_and_check(ser):
        return True
    print("FAILED")

    # Phase 2:
    # address 0 を 0 に戻し、address 1 を 200(2us) に設定して再試行
    print("Phase 2: Checking setting2 ... (/rd = 2us) ")
    if not hardware_setting(ser, 0, 0):
        print("hardwareSetting failed: address=0, data=0")
        return False
    if not hardware_setting(ser, 1, 200):
        print("hardwareSetting failed: address=1, data=200")
        return False

    # address 1 設定直後の状態を一度確認
    print("Checking after address 1 setting...")
    ok, _ = read_hash_5_match(ser)
    if ok:
        return True

    # その後、再度 address 0 を sweep
    print("Phase 2 retry: sweep address 0 again")
    if sweep_address_0_and_check(ser):
        return True

    print("FAILED")
    print("Hash did not stabilize")
    return False

# ============================================================================
# Mapper Detection / Read Functions
# ============================================================================

def detect_ascii_16k(ser: Any, rom_info: ROM_INFO) -> bool:
    print("--- Testing ASCII 16K ---")
    rom_info.hasSRAM = False
    filled_ff_hash = hash_filled_ff(HASH_SIZE)
    
    if not slot_write(ser, 0x6000, 0): return False
    if not slot_write(ser, 0x6800, 0): return False
    if not slot_write(ser, 0x7000, 1): return False
    if not slot_write(ser, 0x7800, 1): return False

    ok0, hA0 = slot_read_hash(ser, 0x4000, HASH_SIZE)
    if not ok0: return False
    ok1, hA1 = slot_read_hash(ser, 0x6000, HASH_SIZE)
    if not ok1: return False
    ok2, hA2 = slot_read_hash(ser, 0x8000, HASH_SIZE)
    if not ok2: return False
    ok3, hA3 = slot_read_hash(ser, 0xA000, HASH_SIZE)
    if not ok3: return False
    hashA = [hA0, hA1, hA2, hA3]

    if DISPLAY_HASH:
        print(f"Bank 0: Hash[0x4000]={hashA[0]:08X}, Hash[0x6000]={hashA[1]:08X}, Hash[0x8000]={hashA[2]:08X}, Hash[0xA000]={hashA[3]:08X}")

    prevHashA = list(hashA)
    max_bank = 0
    found_pattern = False

    for bank_num in range(1, 0x100):
        if not slot_write(ser, 0x6000, bank_num): return False
        if not slot_write(ser, 0x6800, 0): return False
        if not slot_write(ser, 0x7000, bank_num + 1): return False
        if not slot_write(ser, 0x7800, 1): return False

        ok0, hB0 = slot_read_hash(ser, 0x4000, HASH_SIZE)
        if not ok0: return False
        ok1, hB1 = slot_read_hash(ser, 0x6000, HASH_SIZE)
        if not ok1: return False
        ok2, hB2 = slot_read_hash(ser, 0x8000, HASH_SIZE)
        if not ok2: return False
        ok3, hB3 = slot_read_hash(ser, 0xA000, HASH_SIZE)
        if not ok3: return False
        hashB = [hB0, hB1, hB2, hB3]

        # BS6101対策(ROMANCIA/YoungSherlock etc)
        if (bank_num == 1) and (hashB[0] == prevHashA[0]) and (hashB[1] == prevHashA[1]):
            break

        if (bank_num % 4 == 0) and (filled_ff_hash == hashB[0]) and (filled_ff_hash == hashB[1]) and (filled_ff_hash == hashB[2]) and (filled_ff_hash == hashB[3]):
            break

        if (prevHashA[0] == hashB[0]) and (prevHashA[1] == hashB[1]) and (prevHashA[2] == hashB[2]) and (prevHashA[3] == hashB[3]):
            break

        if (hashA[2] == hashB[0]) and (hashA[3] == hashB[1]):
            max_bank = bank_num
            found_pattern = True

        #SRAM Check
        ok_r0, org0 = slot_read(ser, 0x8000)
        if not ok_r0: return False
        ok_r2, org2 = slot_read(ser, 0xA000)
        if not ok_r2: return False

        if not slot_write(ser, 0x8000, org0 ^ 0xFF): return False
        if not slot_write(ser, 0xA000, org2 ^ 0xFF): return False

        ok_r10, data0 = slot_read(ser, 0x8000)
        if not ok_r10: return False
        ok_r12, data2 = slot_read(ser, 0xA000)
        if not ok_r12: return False

        if (data0 == (org0 ^ 0xFF)) or (data2 == (org2 ^ 0xFF)):
            if not slot_write(ser, 0x8000, org0): return False
            if not slot_write(ser, 0xA000, org2): return False
            max_bank = bank_num
            rom_info.hasSRAM = True
            found_pattern = True
            break

        if DISPLAY_HASH:
            print(f"Bank {bank_num}: Hash[0x4000]={hashB[0]:08X}, Hash[0x6000]={hashB[1]:08X}, Hash[0x8000]={hashB[2]:08X}, Hash[0xA000]={hashB[3]:08X}")

        hashA = list(hashB)
        if not found_pattern:
            break

    if found_pattern and max_bank > 0:
        print("\n=== ASCII 16K Detected ===")
        rom_info.mapperType = MapperType.ASCII_16K
        if rom_info.hasSRAM: rom_info.mapperName = "ASCII 16K(+SRAM)"
        else: rom_info.mapperName = "ASCII 16K"

        rom_info.mapperName = "ASCII 16K"
        rom_info.bankCount = max_bank + 1
        rom_info.romSize = rom_info.bankCount * 0x4000
        rom_info.readBankSize = 0x4000
        rom_info.readAreaStart = 0x8000
        rom_info.readAreaSize = 0x4000
        print(f"Bank count: {rom_info.bankCount}, ROM size: {rom_info.romSize} (0x{rom_info.romSize:X})")
        return True
    return False

def detect_ascii_8k(ser: Any, rom_info: ROM_INFO) -> bool:
    print("--- Testing ASCII 8K ---")
    rom_info.hasSRAM = False
    filled_ff_hash = hash_filled_ff(HASH_SIZE)

    if not slot_write(ser, 0x6000, 0): return False
    if not slot_write(ser, 0x6800, 1): return False
    if not slot_write(ser, 0x7000, 2): return False
    if not slot_write(ser, 0x7800, 3): return False

    ok0, hA0 = slot_read_hash(ser, 0x4000, HASH_SIZE)
    if not ok0: return False
    ok1, hA1 = slot_read_hash(ser, 0x6000, HASH_SIZE)
    if not ok1: return False
    ok2, hA2 = slot_read_hash(ser, 0x8000, HASH_SIZE)
    if not ok2: return False
    ok3, hA3 = slot_read_hash(ser, 0xA000, HASH_SIZE)
    if not ok3: return False
    hashA = [hA0, hA1, hA2, hA3]

    #KONAMI8K check
    if not slot_write(ser, 0x8000, 0): return False
    if not slot_write(ser, 0xA000, 0): return False
    ok_chk2, hB2_check = slot_read_hash(ser, 0x8000, HASH_SIZE)
    if not ok_chk2: return False
    ok_chk3, hB3_check = slot_read_hash(ser, 0xA000, HASH_SIZE)
    if not ok_chk3: return False

    if (hashA[2] != hB2_check) or (hashA[3] != hB3_check):
        return False

    prevHashA = list(hashA)
    
    if DISPLAY_HASH:
        print(f"Bank 0: Hash[0x4000]={hashA[0]:08X}, Hash[0x6000]={hashA[1]:08X}, Hash[0x8000]={hashA[2]:08X}, Hash[0xA000]={hashA[3]:08X}")

    max_bank = 0
    found_pattern = False

    for bank_num in range(1, 0x100):
        if not slot_write(ser, 0x6000, bank_num): return False
        if not slot_write(ser, 0x6800, bank_num + 1): return False
        if not slot_write(ser, 0x7000, bank_num + 2): return False
        if not slot_write(ser, 0x7800, bank_num + 3): return False

        ok0, hB0 = slot_read_hash(ser, 0x4000, HASH_SIZE)
        if not ok0: return False
        ok1, hB1 = slot_read_hash(ser, 0x6000, HASH_SIZE)
        if not ok1: return False
        ok2, hB2 = slot_read_hash(ser, 0x8000, HASH_SIZE)
        if not ok2: return False
        ok3, hB3 = slot_read_hash(ser, 0xA000, HASH_SIZE)
        if not ok3: return False
        hashB = [hB0, hB1, hB2, hB3]

        # BS6101対策(ROMANCIA/YoungSherlock etc)
        if (bank_num == 1) and (hashB[0] == prevHashA[0]):
            break

        if (bank_num % 8 == 0) and (filled_ff_hash == hashB[0]) and (filled_ff_hash == hashB[1]) and (filled_ff_hash == hashB[2]) and (filled_ff_hash == hashB[3]):
            break

        if (prevHashA[0] == hashB[0]) and (prevHashA[1] == hashB[1]) and (prevHashA[2] == hashB[2]) and (prevHashA[3] == hashB[3]):
            break

        if (hashA[1] == hashB[0]) and (hashA[2] == hashB[1]) and (hashA[3] == hashB[2]):
            max_bank = bank_num
            found_pattern = True

        #SRAM Check
        ok_r0, org0 = slot_read(ser, 0xA000)
        if not ok_r0: return False
        ok_r2, org2 = slot_read(ser, 0xB000)
        if not ok_r2: return False

        if not slot_write(ser, 0xA000, org0 ^ 0xFF): return False
        if not slot_write(ser, 0xB000, org2 ^ 0xFF): return False

        ok_r10, data0 = slot_read(ser, 0xA000)
        if not ok_r10: return False
        ok_r12, data2 = slot_read(ser, 0xB000)
        if not ok_r12: return False

        if (data0 == (org0 ^ 0xFF)) or (data2 == (org2 ^ 0xFF)):
            if not slot_write(ser, 0xA000, org0): return False
            if not slot_write(ser, 0xB000, org2): return False
            max_bank = bank_num + 2
            rom_info.hasSRAM = True
            found_pattern = True
            break

        if DISPLAY_HASH:
            print(f"Bank {bank_num}: Hash[0x4000]={hashB[0]:08X}, Hash[0x6000]={hashB[1]:08X}, Hash[0x8000]={hashB[2]:08X}, Hash[0xA000]={hashB[3]:08X}")

        hashA = list(hashB)
        if not found_pattern:
            break

    if found_pattern and max_bank > 0:
        print("\n=== ASCII 8K Detected ===")
        rom_info.mapperType = MapperType.ASCII_8K
        if rom_info.hasSRAM: rom_info.mapperName = "ASCII 8K(+SRAM)"
        else: rom_info.mapperName = "ASCII 8K"
        rom_info.bankCount = max_bank + 1
        rom_info.romSize = rom_info.bankCount * 0x2000
        rom_info.readBankSize = 0x2000
        rom_info.readAreaStart = 0x8000
        rom_info.readAreaSize = 0x2000
        print(f"Bank count: {rom_info.bankCount}, ROM size: {rom_info.romSize} (0x{rom_info.romSize:X})")
        return True
    return False

def detect_konami_8k(ser: Any, rom_info: ROM_INFO) -> bool:
    print("--- Testing KONAMI 8K ---")
    rom_info.hasSRAM = False
    filled_ff_hash = hash_filled_ff(HASH_SIZE)

    if not slot_write(ser, 0x4000, 3): return False
    if not slot_write(ser, 0x6000, 0): return False
    if not slot_write(ser, 0x8000, 1): return False
    if not slot_write(ser, 0xA000, 2): return False

    ok0, hA0 = slot_read_hash(ser, 0x4000, HASH_SIZE)
    if not ok0: return False
    ok1, hA1 = slot_read_hash(ser, 0x6000, HASH_SIZE)
    if not ok1: return False
    ok2, hA2 = slot_read_hash(ser, 0x8000, HASH_SIZE)
    if not ok2: return False
    ok3, hA3 = slot_read_hash(ser, 0xA000, HASH_SIZE)
    if not ok3: return False
    hashA = [hA0, hA1, hA2, hA3]

    prevHashA = list(hashA)
    found_pattern = False

    for bank_num in range(1, 0x20):
        if not slot_write(ser, 0x4000, bank_num + 2): return False
        if not slot_write(ser, 0x6000, bank_num + 0): return False
        if not slot_write(ser, 0x8000, bank_num + 1): return False
        if not slot_write(ser, 0xA000, bank_num + 2): return False

        ok0, hB0 = slot_read_hash(ser, 0x4000, HASH_SIZE)
        if not ok0: return False
        ok1, hB1 = slot_read_hash(ser, 0x6000, HASH_SIZE)
        if not ok1: return False
        ok2, hB2 = slot_read_hash(ser, 0x8000, HASH_SIZE)
        if not ok2: return False
        ok3, hB3 = slot_read_hash(ser, 0xA000, HASH_SIZE)
        if not ok3: return False
        hashB = [hB0, hB1, hB2, hB3]

        if (bank_num % 8 == 0) and (filled_ff_hash == hashB[1]) and (filled_ff_hash == hashB[2]) and (filled_ff_hash == hashB[3]):
            break

        #新10倍カートリッジのチェック SRAMは4KBx2pageなので同じデータが連続する
        if (bank_num + 1) == 0x10:
            ok_c0, hC0 = slot_read_hash(ser, 0x8000, 0x1000)
            if not ok_c0: return False
            ok_c1, hC1 = slot_read_hash(ser, 0x9000, 0x1000)
            if not ok_c1: return False
            if hC0 == hC1:
                max_bank = bank_num
                rom_info.hasSRAM = True
                found_pattern = True
                break

        if (prevHashA[0] == hashB[0]) and (prevHashA[1] == hashB[1]) and (prevHashA[2] == hashB[2]) and (prevHashA[3] == hashB[3]):
            break

        if (hashA[0] == hashB[0]) and (hashA[2] == hashB[1]) and (hashA[3] == hashB[2]):
            max_bank = bank_num
            found_pattern = True

        hashA = list(hashB)   
        if not found_pattern:
            break

    if found_pattern and max_bank > 0:
        print("\n=== KONAMI 8K Detected ===")
        rom_info.mapperType = MapperType.KONAMI_8K
        rom_info.mapperName = "KONAMI 8K (+SRAM)" if rom_info.hasSRAM else "KONAMI 8K"
        rom_info.bankCount = max_bank + 1
        rom_info.romSize = rom_info.bankCount * 0x2000
        rom_info.readBankSize = 0x2000
        rom_info.readAreaStart = 0x8000
        rom_info.readAreaSize = 0x2000
        print(f"Bank count: {rom_info.bankCount}, ROM size: {rom_info.romSize} (0x{rom_info.romSize:X})")
        return True
    return False

def detect_konami_scc(ser: Any, rom_info: ROM_INFO) -> bool:
    print("--- Testing KONAMI SCC ---")
    filled_ff_hash = hash_filled_ff(HASH_SIZE)

    if not slot_write(ser, 0x5000, 0): return False
    if not slot_write(ser, 0x7000, 1): return False
    if not slot_write(ser, 0x9000, 2): return False
    if not slot_write(ser, 0xB000, 3): return False
    if not slot_write(ser, 0x5800, 0): return False
    if not slot_write(ser, 0x7800, 1): return False
    if not slot_write(ser, 0x9800, 2): return False
    if not slot_write(ser, 0xB800, 3): return False

    ok0, hA0 = slot_read_hash(ser, 0x4000, HASH_SIZE)
    if not ok0: return False
    ok1, hA1 = slot_read_hash(ser, 0x6000, HASH_SIZE)
    if not ok1: return False
    ok2, hA2 = slot_read_hash(ser, 0x8000, HASH_SIZE)
    if not ok2: return False
    ok3, hA3 = slot_read_hash(ser, 0xA000, HASH_SIZE)
    if not ok3: return False
    hashA = [hA0, hA1, hA2, hA3]

    prevHashA = list(hashA)
    found_pattern = False

    for bank_num in range(1, 0x3F):
        if not slot_write(ser, 0x5000, bank_num): return False
        if not slot_write(ser, 0x7000, (bank_num + 1)): return False
        if not slot_write(ser, 0x9000, (bank_num + 2)): return False
        if not slot_write(ser, 0xB000, (bank_num + 3)): return False
        if not slot_write(ser, 0x5800, 0): return False
        if not slot_write(ser, 0x7800, 1): return False
        if not slot_write(ser, 0x9800, 2): return False
        if not slot_write(ser, 0xB800, 3): return False

        ok0, hB0 = slot_read_hash(ser, 0x4000, HASH_SIZE)
        if not ok0: return False
        ok1, hB1 = slot_read_hash(ser, 0x6000, HASH_SIZE)
        if not ok1: return False
        ok2, hB2 = slot_read_hash(ser, 0x8000, HASH_SIZE)
        if not ok2: return False
        ok3, hB3 = slot_read_hash(ser, 0xA000, HASH_SIZE)
        if not ok3: return False
        hashB = [hB0, hB1, hB2, hB3]

        if (bank_num % 8 == 0) and (filled_ff_hash == hashB[1]) and (filled_ff_hash == hashB[2]) and (filled_ff_hash == hashB[3]):
            break

        if (prevHashA[0] == hashB[0]) and (prevHashA[1] == hashB[1]) and (prevHashA[2] == hashB[2]) and (prevHashA[3] == hashB[3]):
            break

        if (hashA[1] == hashB[0]) and (hashA[2] == hashB[1]) and (hashA[3] == hashB[2]):
            max_bank = bank_num
            found_pattern = True

        hashA = list(hashB)
        if not found_pattern:
            break

    if found_pattern and max_bank > 0:
        print("\n=== KONAMI SCC Detected ===")
        rom_info.mapperType = MapperType.KONAMI_SCC
        rom_info.mapperName = "KONAMI SCC"
        rom_info.bankCount = max_bank + 1
        rom_info.romSize = rom_info.bankCount * 0x2000
        rom_info.readBankSize = 0x2000
        rom_info.readAreaStart = 0x8000
        rom_info.readAreaSize = 0x2000
        print(f"Bank count: {rom_info.bankCount}, ROM size: {rom_info.romSize} (0x{rom_info.romSize:X})")
        return True
    return False

def detect_generic_16k(ser: Any, rom_info: ROM_INFO) -> bool:
    print("--- Testing Generic 16K ---")
    filled_ff_hash = hash_filled_ff(HASH_SIZE)

    if not slot_write(ser, 0x4000, 0): return False
    if not slot_write(ser, 0x6000, 0): return False
    if not slot_write(ser, 0x8000, 1): return False
    if not slot_write(ser, 0xA000, 1): return False

    ok0, hA0 = slot_read_hash(ser, 0x4000, HASH_SIZE)
    if not ok0: return False
    ok1, hA1 = slot_read_hash(ser, 0x6000, HASH_SIZE)
    if not ok1: return False
    ok2, hA2 = slot_read_hash(ser, 0x8000, HASH_SIZE)
    if not ok2: return False
    ok3, hA3 = slot_read_hash(ser, 0xA000, HASH_SIZE)
    if not ok3: return False
    hashA = [hA0, hA1, hA2, hA3]

    prevHashA = list(hashA)
    found_pattern = False

    for bank_num in range(1, 0x100):
        if not slot_write(ser, 0x4000, bank_num): return False
        if not slot_write(ser, 0x6000, 0): return False
        if not slot_write(ser, 0x8000, (bank_num + 1)): return False
        if not slot_write(ser, 0x7800, 1): return False

        ok0, hB0 = slot_read_hash(ser, 0x4000, HASH_SIZE)
        if not ok0: return False
        ok1, hB1 = slot_read_hash(ser, 0x6000, HASH_SIZE)
        if not ok1: return False
        ok2, hB2 = slot_read_hash(ser, 0x8000, HASH_SIZE)
        if not ok2: return False
        ok3, hB3 = slot_read_hash(ser, 0xA000, HASH_SIZE)
        if not ok3: return False
        hashB = [hB0, hB1, hB2, hB3]

        if (bank_num % 4 == 0) and (filled_ff_hash == hashB[0]) and (filled_ff_hash == hashB[1]) and (filled_ff_hash == hashB[2]) and (filled_ff_hash == hashB[3]):
            break

        if (prevHashA[0] == hashB[0]) and (prevHashA[1] == hashB[1]) and (prevHashA[2] == hashB[2]) and (prevHashA[3] == hashB[3]):
            break

        if (hashA[2] == hashB[0]) and (hashA[3] == hashB[1]):
            max_bank = bank_num
            found_pattern = True

        hashA = list(hashB)
        if not found_pattern:
            break

    if found_pattern and max_bank > 0:
        print("\n=== Generic 16K Detected ===")
        rom_info.mapperType = MapperType.GENERIC_16K
        rom_info.mapperName = "Generic 16K"
        rom_info.bankCount = max_bank + 1
        rom_info.romSize = rom_info.bankCount * 0x4000
        rom_info.readBankSize = 0x4000
        rom_info.readAreaStart = 0x8000
        rom_info.readAreaSize = 0x4000
        print(f"Bank count: {rom_info.bankCount}, ROM size: {rom_info.romSize} (0x{rom_info.romSize:X})")
        return True
    return False

def detect_generic_8k(ser: Any, rom_info: ROM_INFO) -> bool:
    print("--- Testing Generic 8K ---")
    filled_ff_hash = hash_filled_ff(HASH_SIZE)

    if not slot_write(ser, 0x4000, 0): return False
    if not slot_write(ser, 0x6000, 1): return False
    if not slot_write(ser, 0x8000, 2): return False
    if not slot_write(ser, 0xA000, 3): return False

    ok0, hA0 = slot_read_hash(ser, 0x4000, HASH_SIZE)
    if not ok0: return False
    ok1, hA1 = slot_read_hash(ser, 0x6000, HASH_SIZE)
    if not ok1: return False
    ok2, hA2 = slot_read_hash(ser, 0x8000, HASH_SIZE)
    if not ok2: return False
    ok3, hA3 = slot_read_hash(ser, 0xA000, HASH_SIZE)
    if not ok3: return False
    hashA = [hA0, hA1, hA2, hA3]

    prevHashA = list(hashA)
    found_pattern = False

    for bank_num in range(1, 0x100):
        if not slot_write(ser, 0x4000, bank_num): return False
        if not slot_write(ser, 0x6000, (bank_num + 1)): return False
        if not slot_write(ser, 0x8000, (bank_num + 2)): return False
        if not slot_write(ser, 0xA000, (bank_num + 3)): return False

        ok0, hB0 = slot_read_hash(ser, 0x4000, HASH_SIZE)
        if not ok0: return False
        ok1, hB1 = slot_read_hash(ser, 0x6000, HASH_SIZE)
        if not ok1: return False
        ok2, hB2 = slot_read_hash(ser, 0x8000, HASH_SIZE)
        if not ok2: return False
        ok3, hB3 = slot_read_hash(ser, 0xA000, HASH_SIZE)
        if not ok3: return False
        hashB = [hB0, hB1, hB2, hB3]

        if (bank_num % 8 == 0) and (filled_ff_hash == hashB[0]) and (filled_ff_hash == hashB[1]) and (filled_ff_hash == hashB[2]) and (filled_ff_hash == hashB[3]):
            break

        if (prevHashA[0] == hashB[0]) and (prevHashA[1] == hashB[1]) and (prevHashA[2] == hashB[2]) and (prevHashA[3] == hashB[3]):
            break

        if (hashA[2] == hashB[0]) and (hashA[3] == hashB[1]):
            max_bank = bank_num
            found_pattern = True

        hashA = list(hashB)
        if not found_pattern:
            break

    if found_pattern and max_bank > 0:
        print("\n=== Generic 8K Detected ===")
        rom_info.mapperType = MapperType.GENERIC_8K
        rom_info.mapperName = "Generic 8K"
        rom_info.bankCount = max_bank + 1
        rom_info.romSize = rom_info.bankCount * 0x2000
        rom_info.readBankSize = 0x2000
        rom_info.readAreaStart = 0x8000
        rom_info.readAreaSize = 0x2000
        print(f"Bank count: {rom_info.bankCount}, ROM size: {rom_info.romSize} (0x{rom_info.romSize:X})")
        return True
    return False

def detect_rtype(ser: Any, rom_info: ROM_INFO) -> bool:
    print("--- Testing R-Type ---")

    # R-TYPE
    #基板:     MSX-004
    #メガコン: IREM TAM-S1 (28pin)
    #ROM:      LH532163 (32pin:2M) + LH2309HB (28pin:1M)

    # ページ1：固定
    # ページ2：バンクセレクタ0x4000～0x7FFF
    #          バンク0x0Fがページ1と同じ内容
    #          バンク0x10～0x15は一つ置きに内容が変わる
    #          バンク0x16以降は 0x0E～0x15の繰り返しミラー
    #          バンク0x20単位で繰り返しミラー

    # ページ2(0x8000～0xBFFF) のパターン：
    # 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F
    # 10 10 12 12 14 14 0E 0F 10 10 12 12 14 14 0E 0F
    # 以下繰り返し

    # ROMデータベースではROMチップ構成から3MBByte(0x00～0x17)
    # 実際には0x00～0x15のイメージがあれば十分

    if not slot_write(ser, 0x7000, 0x0f): return False

    ok0, hA0 = slot_read_hash(ser, 0x4000, HASH_SIZE)
    if not ok0: return False
    ok1, hA1 = slot_read_hash(ser, 0x6000, HASH_SIZE)
    if not ok1: return False
    ok2, hA2 = slot_read_hash(ser, 0x8000, HASH_SIZE)
    if not ok2: return False
    ok3, hA3 = slot_read_hash(ser, 0xA000, HASH_SIZE)
    if not ok3: return False
    hashA = [hA0, hA1, hA2, hA3]

    if not slot_write(ser, 0x6000, 0x01): return False
    if not slot_write(ser, 0x7800, 0x1f): return False

    ok0, hB0 = slot_read_hash(ser, 0x4000, HASH_SIZE)
    if not ok0: return False
    ok1, hB1 = slot_read_hash(ser, 0x6000, HASH_SIZE)
    if not ok1: return False
    ok2, hB2 = slot_read_hash(ser, 0x8000, HASH_SIZE)
    if not ok2: return False
    ok3, hB3 = slot_read_hash(ser, 0xA000, HASH_SIZE)
    if not ok3: return False
    hashB = [hB0, hB1, hB2, hB3]

    # ページ2バンク0x0Fがページ1と同じ内容
    if (hashA[0] != hashA(2)) or (hashA[1] != hashA[3]):
        return False

    # ページ1は固定で、ページ2の0x0Fと0x1Fと同じ内容
    if (hashA[0] != hashB[0]) or (hashA[1] != hashB[1]) or (hashA[2] != hashB[2]) or (hashA[3] != hashB[3]):
        return False

    if not slot_write(ser, 0x6800, 0x00): return False
    if not slot_write(ser, 0x7800, 0x00): return False

    ok0, hB0 = slot_read_hash(ser, 0x4000, HASH_SIZE)
    if not ok0: return False
    ok1, hB1 = slot_read_hash(ser, 0x6000, HASH_SIZE)
    if not ok1: return False
    ok2, hB2 = slot_read_hash(ser, 0x8000, HASH_SIZE)
    if not ok2: return False
    ok3, hB3 = slot_read_hash(ser, 0xA000, HASH_SIZE)
    if not ok3: return False
    hashB = [hB0, hB1, hB2, hB3]

    if (hashA[0] == hashB[0]) and (hashA[1] == hashB[1]) and (hashA[2] != hashB[2]) and (hashA[3] != hashB[3]):
        print("\n=== R-Type Detected ===")
        rom_info.mapperType = MapperType.RTYPE
        rom_info.mapperName = "R-TYPE"
        rom_info.bankCount = 0x18
        rom_info.romSize = rom_info.bankCount * 0x4000
        rom_info.readBankSize = 0x4000
        rom_info.readAreaStart = 0x8000
        rom_info.readAreaSize = 0x4000
        print(f"Bank count: {rom_info.bankCount}, ROM size: {rom_info.romSize} (0x{rom_info.romSize:X})")
        return True

    return False

def detect_harry_fox(ser: Any, rom_info: ROM_INFO) -> bool:
    print("--- Testing HarryFox ---")

    # /* 基準パターンA取得 */
    if not slot_write(ser, 0x6000, 0x00): return False
    if not slot_write(ser, 0x7000, 0x00): return False

    ok0, hA0 = slot_read_hash(ser, 0x4000, HASH_SIZE)
    if not ok0: return False
    ok1, hA1 = slot_read_hash(ser, 0x6000, HASH_SIZE)
    if not ok1: return False
    ok2, hA2 = slot_read_hash(ser, 0x8000, HASH_SIZE)
    if not ok2: return False
    ok3, hA3 = slot_read_hash(ser, 0xA000, HASH_SIZE)
    if not ok3: return False
    prevHashA = [hA0, hA1, hA2, hA3]

    # /* 基準パターンB取得 */
    if not slot_write(ser, 0x6000, 0x01): return False
    if not slot_write(ser, 0x7000, 0x01): return False

    ok0, hB0 = slot_read_hash(ser, 0x4000, HASH_SIZE)
    if not ok0: return False
    ok1, hB1 = slot_read_hash(ser, 0x6000, HASH_SIZE)
    if not ok1: return False
    ok2, hB2 = slot_read_hash(ser, 0x8000, HASH_SIZE)
    if not ok2: return False
    ok3, hB3 = slot_read_hash(ser, 0xA000, HASH_SIZE)
    if not ok3: return False
    prevHashB = [hB0, hB1, hB2, hB3]

    if (prevHashA[0] == prevHashB[0]) or (prevHashA[1] == prevHashB[1]) or (prevHashA[2] == prevHashB[2]) or (prevHashA[3] == prevHashB[3]):
        return False
 
    # /* i = 0～8 を検査 */
    for i in range(8):
        expected_hash = prevHashA if (i % 2 == 0) else prevHashB

        if not slot_write(ser, 0x6fff, i): return False
        if not slot_write(ser, 0x7fff, i): return False

        ok0, h0 = slot_read_hash(ser, 0x4000, HASH_SIZE)
        if not ok0: return False
        ok1, h1 = slot_read_hash(ser, 0x6000, HASH_SIZE)
        if not ok1: return False
        ok2, h2 = slot_read_hash(ser, 0x8000, HASH_SIZE)
        if not ok2: return False
        ok3, h3 = slot_read_hash(ser, 0xA000, HASH_SIZE)
        if not ok3: return False
        current_hash = [h0, h1, h2, h3]

        if (current_hash[0] != expected_hash[0]) or \
           (current_hash[1] != expected_hash[1]) or \
           (current_hash[2] != expected_hash[2]) or \
           (current_hash[3] != expected_hash[3]):
            return False

    print("\n=== Harry Fox ROM Detected ===")
    rom_info.mapperType = MapperType.HARRYFOX
    rom_info.mapperName = "HARRY FOX"
    rom_info.bankCount = 0x2
    rom_info.romSize = rom_info.bankCount * 0x8000
    rom_info.readBankSize = 0x8000
    rom_info.readAreaStart = 0x4000
    rom_info.readAreaSize = 0x8000
    print(f"Bank count: {rom_info.bankCount}, ROM size: {rom_info.romSize} (0x{rom_info.romSize:X})")

    return True

def detect_halnote(ser: Any, rom_info: ROM_INFO) -> bool:
    print("--- Testing HALNOTE ---")

    # /* 基準パターンA取得 */
    if not slot_write(ser, 0x4FFF, 0x00): return False
    if not slot_write(ser, 0x6FFF, 0x00): return False
    if not slot_write(ser, 0x8FFF, 0x00): return False
    if not slot_write(ser, 0xAFFF, 0x00): return False

    # // Main Mapper
    ok0, hA0 = slot_read_hash(ser, 0x4000, HASH_SIZE)
    if not ok0: return False
    ok1, hA1 = slot_read_hash(ser, 0x6000, HASH_SIZE)
    if not ok1: return False
    ok2, hA2 = slot_read_hash(ser, 0x8000, HASH_SIZE)
    if not ok2: return False
    ok3, hA3 = slot_read_hash(ser, 0xA000, HASH_SIZE)
    if not ok3: return False
    prevHashA = [hA0, hA1, hA2, hA3]

    if (prevHashA[0] != prevHashA[1]) or (prevHashA[1] != prevHashA[2]) or (prevHashA[2] != prevHashA[3]):
        return False

    ok_sub1, hA1_sub = slot_read_hash(ser, 0x6C00, 0x0800)
    if not ok_sub1: return False
    prevHashA[1] = hA1_sub

    if not slot_write(ser, 0x4FFF, 0x00): return False
    if not slot_write(ser, 0x6FFF, 0x01): return False
    if not slot_write(ser, 0x8FFF, 0x02): return False
    if not slot_write(ser, 0xAFFF, 0x00): return False

    # // Main Mapper
    ok0, hB0 = slot_read_hash(ser, 0x4000, HASH_SIZE)
    if not ok0: return False
    ok1, hB1 = slot_read_hash(ser, 0x6000, HASH_SIZE)
    if not ok1: return False
    ok2, hB2 = slot_read_hash(ser, 0x8000, HASH_SIZE)
    if not ok2: return False
    ok3, hB3 = slot_read_hash(ser, 0xA000, HASH_SIZE)
    if not ok3: return False
    prevHashB = [hB0, hB1, hB2, hB3]

    if (prevHashA[0] == prevHashB[1]) or (prevHashA[0] == prevHashB[2]) or (prevHashB[0] != prevHashB[3]):
        return False

    # // Sub Mapper
    if not slot_write(ser, 0x4FFF, 0x40): return False
    if not slot_write(ser, 0x6FFF, 0x80): return False

    ok0, hB0_sub = slot_read_hash(ser, 0x4000, HASH_SIZE)
    if not ok0: return False
    ok1, hB1_sub = slot_read_hash(ser, 0x6C00, 0x0800)
    if not ok1: return False
    ok2, hB2_sub = slot_read_hash(ser, 0x4000, 0x0800)
    if not ok2: return False
    ok3, hB3_sub = slot_read_hash(ser, 0x7000, 0x0800)
    if not ok3: return False
    prevHashB_sub = [hB0_sub, hB1_sub, hB2_sub, hB3_sub]

    if (prevHashA[0] == prevHashB_sub[1]) or (prevHashA[0] == prevHashB_sub[1]) or (prevHashB_sub[2] != prevHashB_sub[3]):
        return False

    print("\n=== HALNOTE ROM Detected ===")
    rom_info.mapperType = MapperType.HALNOTE
    rom_info.mapperName = "HALNOTE"
    rom_info.bankCount = 0x80
    rom_info.romSize = rom_info.bankCount * 0x2000
    rom_info.readBankSize = 0x2000
    rom_info.readAreaStart = 0x6000
    rom_info.readAreaSize = 0x2000
    print(f"Bank count: {rom_info.bankCount}, ROM size: {rom_info.romSize} (0x{rom_info.romSize:X})")

    return True

def detect_standard_rom(ser: Any, rom_info: ROM_INFO) -> bool:
    filled_ff_hash = hash_filled_ff(HASH_SIZE)

    print("=== Detecting Standard ROM Type ===")

    print("Reading 0x0000-0xBFFF...")
    full_data = slot_dump(ser, 0x0000, 0xC000)
    if not full_data:
        print("Failed to read full ROM")
        return False

    hash0 = hash_7936(full_data, 0x0000)
    hash2 = hash_7936(full_data, 0x2000)
    hash4 = hash_7936(full_data, 0x4000)
    hash6 = hash_7936(full_data, 0x6000)
    hash8 = hash_7936(full_data, 0x8000)
    hashA = hash_7936(full_data, 0xA000)

    if (hash0 == filled_ff_hash) and (hash2 == filled_ff_hash) and (hash4 != filled_ff_hash) and (hash4 == hash6) and (hash8 == filled_ff_hash) and (hashA == filled_ff_hash):
        print("\n=== 8KB Mirrored ROM Detected ===")
        rom_info.mapperType = MapperType.NO_MAPPER_16K
        rom_info.mapperName = "8KB ROM (Mirrored)"
        rom_info.romSize = 0x2000
        rom_info.validDataStart = 0x4000
        rom_info.validDataSize = 0x2000
        return True

    if (hash0 == filled_ff_hash) and (hash2 == filled_ff_hash) and (hash4 == filled_ff_hash) and (hash6 == filled_ff_hash) and (hash8 != filled_ff_hash) and (hash8 == hashA):
        print("\n=== 8KB Mirrored ROM Detected ===")
        rom_info.mapperType = MapperType.NO_MAPPER_16K
        rom_info.mapperName = "8KB ROM (Mirrored)"
        rom_info.romSize = 0x2000
        rom_info.validDataStart = 0x8000
        rom_info.validDataSize = 0x2000
        return True

    if (hash0 == filled_ff_hash) and (hash2 == filled_ff_hash) and (hash4 != filled_ff_hash) and (hash6 == filled_ff_hash) and (hash8 == filled_ff_hash) and (hashA == filled_ff_hash):
        print("\n=== 16KB Standard ROM Detected ===")
        rom_info.mapperType = MapperType.NO_MAPPER_16K
        rom_info.mapperName = "8KB ROM"
        rom_info.romSize = 0x2000
        rom_info.validDataStart = 0x4000
        rom_info.validDataSize = 0x2000
        return True

    if (hash0 == filled_ff_hash) and (hash2 == filled_ff_hash) and (hash4 != filled_ff_hash) and (hash6 != filled_ff_hash) and (hash8 == filled_ff_hash) and (hashA == filled_ff_hash):
        print("\n=== 16KB Standard ROM Detected ===")
        rom_info.mapperType = MapperType.NO_MAPPER_16K
        rom_info.mapperName = "16KB ROM"
        rom_info.romSize = 0x4000
        rom_info.validDataStart = 0x4000
        rom_info.validDataSize = 0x4000
        return True

    if (hash0 == filled_ff_hash) and (hash2 == filled_ff_hash) and (hash4 == filled_ff_hash) and (hash6 == filled_ff_hash) and (hash8 != filled_ff_hash) and (hashA != filled_ff_hash):
        print("\n=== 16KB Standard ROM Detected ===")
        rom_info.mapperType = MapperType.NO_MAPPER_16K
        rom_info.mapperName = "16KB ROM"
        rom_info.romSize = 0x4000
        rom_info.validDataStart = 0x8000
        rom_info.validDataSize = 0x4000
        return True

    if (hash0 == hash4) and (hash2 == hash6) and (hash4 == hash8) and (hash6 == hashA):
        print("\n=== 16KB Standard ROM Detected ===")
        rom_info.mapperType = MapperType.NO_MAPPER_16K
        rom_info.mapperName = "16KB ROM"
        rom_info.romSize = 0x4000
        rom_info.validDataStart = 0x4000
        rom_info.validDataSize = 0x4000
        return True

    if (hash0 == filled_ff_hash) and (hash2 == filled_ff_hash) and (hash4 == hash8) and (hash6 == hashA):
        print("\n=== 16KB Standard ROM Detected ===")
        rom_info.mapperType = MapperType.NO_MAPPER_16K
        rom_info.mapperName = "16KB ROM"
        rom_info.romSize = 0x4000
        rom_info.validDataStart = 0x4000
        rom_info.validDataSize = 0x4000
        return True

    if (hash0 == filled_ff_hash) and (hash2 == filled_ff_hash) and (hash4 != hash8) and (hash6 != hashA):
        print("\n=== 32KB Standard ROM Detected ===")
        rom_info.mapperType = MapperType.NO_MAPPER_16K
        rom_info.mapperName = "32KB ROM"
        rom_info.romSize = 0x8000
        rom_info.validDataStart = 0x4000
        rom_info.validDataSize = 0x8000
        return True

    if (hash0 == hash4) and (hash2 == hash6) and (hash4 != hash8) and (hash6 != hashA):
        print("\n=== 32KB Standard ROM Detected ===")
        rom_info.mapperType = MapperType.NO_MAPPER_16K
        rom_info.mapperName = "32KB ROM"
        rom_info.romSize = 0x8000
        rom_info.validDataStart = 0x4000
        rom_info.validDataSize = 0x8000
        return True

    if (hash0 == hash8) and (hash2 == hashA) and (hash4 != hash8) and (hash6 != hashA):
        print("\n=== 32KB Standard ROM Detected ===")
        rom_info.mapperType = MapperType.NO_MAPPER_16K
        rom_info.mapperName = "32KB ROM"
        rom_info.romSize = 0x8000
        rom_info.validDataStart = 0x4000
        rom_info.validDataSize = 0x8000
        return True

    print("\n=== 48KB Standard ROM Detected ===")
    rom_info.mapperType = MapperType.NO_MAPPER_48K
    rom_info.mapperName = "48KB ROM"
    rom_info.romSize = 0xC000
    rom_info.validDataStart = 0x0000
    rom_info.validDataSize = 0xC000
    return True

# ============================================================================
# ROM ACCESS - Read Subroutines
# ============================================================================

def read_ascii_16k(ser: Any, rom_info: ROM_INFO) -> Optional[bytes]:
    print("=== Reading ASCII 16K ROM ===\n")
    out_data = bytearray()
    
    for bank in range(rom_info.bankCount):
        if not slot_write(ser, 0x7000, bank):
            return None
        buffer = slot_dump(ser, rom_info.readAreaStart, rom_info.readAreaSize)
        if not buffer:
            print(f"Failed to read bank {bank}")
            return None
        out_data.extend(buffer[:rom_info.readBankSize])
        print(f"Saved bank {bank} (0x{len(out_data) - rom_info.readBankSize:04X} - 0x{len(out_data) - 1:04X})")
        
    return bytes(out_data)

def read_ascii_8k(ser: Any, rom_info: ROM_INFO) -> Optional[bytes]:
    print("=== Reading ASCII 8K ROM ===\n")
    out_data = bytearray()
    
    for bank in range(rom_info.bankCount):
        if not slot_write(ser, 0x7000, bank):
            return None
        buffer = slot_dump(ser, rom_info.readAreaStart, rom_info.readAreaSize)
        if not buffer:
            print(f"Failed to read bank {bank}")
            return None
        out_data.extend(buffer[:rom_info.readBankSize])
        print(f"Saved bank {bank} (0x{len(out_data) - rom_info.readBankSize:04X} - 0x{len(out_data) - 1:04X})")
        
    return bytes(out_data)

def read_konami_8k(ser: Any, rom_info: ROM_INFO) -> Optional[bytes]:
    print("=== Reading KONAMI 8K ROM ===\n")
    out_data = bytearray()
    
    for bank in range(rom_info.bankCount):
        if not slot_write(ser, 0x8000, bank):
            return None
        buffer = slot_dump(ser, rom_info.readAreaStart, rom_info.readAreaSize)
        if not buffer:
            print(f"Failed to read bank {bank}")
            return None
        out_data.extend(buffer[:rom_info.readBankSize])
        print(f"Saved bank {bank} (0x{len(out_data) - rom_info.readBankSize:04X} - 0x{len(out_data) - 1:04X})")
        
    return bytes(out_data)

def read_konami_scc(ser: Any, rom_info: ROM_INFO) -> Optional[bytes]:
    print("=== Reading KONAMI SCC ROM ===\n")
    out_data = bytearray()
    
    for bank in range(rom_info.bankCount):
        if not slot_write(ser, 0x9000, bank):
            return None
        buffer = slot_dump(ser, rom_info.readAreaStart, rom_info.readAreaSize)
        if not buffer:
            print(f"Failed to read bank {bank}")
            return None
        out_data.extend(buffer[:rom_info.readBankSize])
        print(f"Saved bank {bank} (0x{len(out_data) - rom_info.readBankSize:04X} - 0x{len(out_data) - 1:04X})")
        
    return bytes(out_data)

def read_generic_16k(ser: Any, rom_info: ROM_INFO) -> Optional[bytes]:
    print("=== Reading Generic 16K ROM ===\n")
    out_data = bytearray()
    
    for bank in range(rom_info.bankCount):
        if not slot_write(ser, 0x4000, bank): return None
        if not slot_write(ser, 0x8000, bank + 1): return None
        buffer = slot_dump(ser, rom_info.readAreaStart, rom_info.readAreaSize)
        if not buffer:
            print(f"Failed to read bank {bank}")
            return None
        out_data.extend(buffer[:rom_info.readBankSize])
        print(f"Saved bank {bank} (0x{len(out_data) - rom_info.readBankSize:04X} - 0x{len(out_data) - 1:04X})")
        
    return bytes(out_data)

def read_generic_8k(ser: Any, rom_info: ROM_INFO) -> Optional[bytes]:
    print("=== Reading Generic 8K ROM ===\n")
    out_data = bytearray()
    
    for bank in range(rom_info.bankCount):
        if not slot_write(ser, 0x4000, bank): return None
        if not slot_write(ser, 0x6000, bank + 1): return None
        if not slot_write(ser, 0x8000, bank + 2): return None
        if not slot_write(ser, 0xA000, bank + 3): return None
        buffer = slot_dump(ser, rom_info.readAreaStart, rom_info.readAreaSize)
        if not buffer:
            print(f"Failed to read bank {bank}")
            return None
        out_data.extend(buffer[:rom_info.readBankSize])
        print(f"Saved bank {bank} (0x{len(out_data) - rom_info.readBankSize:04X} - 0x{len(out_data) - 1:04X})")
        
    return bytes(out_data)

def read_rtype(ser: Any, rom_info: ROM_INFO) -> Optional[bytes]:
    print("=== Reading R-TYPE ROM ===\n")
    out_data = bytearray()
    
    for bank in range(rom_info.bankCount):
        if not slot_write(ser, 0x7000, bank):
            return None
        buffer = slot_dump(ser, rom_info.readAreaStart, rom_info.readAreaSize)
        if not buffer:
            print(f"Failed to read bank {bank}")
            return None
        out_data.extend(buffer[:rom_info.readBankSize])
        print(f"Saved bank {bank} (0x{len(out_data) - rom_info.readBankSize:04X} - 0x{len(out_data) - 1:04X})")
        
    return bytes(out_data)

def read_harry_fox(ser: Any, rom_info: ROM_INFO) -> Optional[bytes]:
    print("=== Reading Harry Fox -Yuki no Maou- ROM ===\n")
    out_data = bytearray()
    
    for bank in range(rom_info.bankCount):
        if not slot_write(ser, 0x6000, bank): return None
        if not slot_write(ser, 0x7000, bank): return None
        buffer = slot_dump(ser, rom_info.readAreaStart, rom_info.readAreaSize)
        if not buffer:
            print(f"Failed to read bank {bank}")
            return None
        out_data.extend(buffer[:rom_info.readBankSize])
        print(f"Saved bank {bank} (0x{len(out_data) - rom_info.readBankSize:04X} - 0x{len(out_data) - 1:04X})")
        
    return bytes(out_data)

def read_hal_note(ser: Any, rom_info: ROM_INFO) -> Optional[bytes]:
    print("=== Reading HALNOTE ROM ===\n")
    out_data = bytearray()
    
    if not slot_write(ser, 0xC000, 0x03):
        return None
        
    for bank in range(rom_info.bankCount):
        if not slot_write(ser, 0x6FFF, bank):
            return None
        buffer = slot_dump(ser, rom_info.readAreaStart, rom_info.readAreaSize)
        if not buffer:
            print(f"Failed to read bank {bank}")
            return None
        out_data.extend(buffer[:rom_info.readBankSize])
        print(f"Saved bank {bank} (0x{len(out_data) - rom_info.readBankSize:04X} - 0x{len(out_data) - 1:04X})")
        
    return bytes(out_data)

def read_standard_rom(ser: Any, rom_info: ROM_INFO) -> Optional[bytes]:
    print("=== Reading Standard ROM ===")
    print(f"Reading standard ROM: 0x{rom_info.validDataStart:04X} - 0x{rom_info.validDataStart + rom_info.validDataSize - 1:04X} ({rom_info.validDataSize} bytes)")
    
    data = slot_dump(ser, rom_info.validDataStart, rom_info.validDataSize)
    if not data:
        print("Failed to read ROM")
        return None
    return data

def read_complete_rom(ser: Any, rom_info: ROM_INFO) -> Optional[bytes]:
    print("\n========== READING ROM DATA ==========")
    mtype = rom_info.mapperType
    
    if mtype == MapperType.ASCII_16K:
        return read_ascii_16k(ser, rom_info)
    elif mtype == MapperType.ASCII_8K:
        return read_ascii_8k(ser, rom_info)
    elif mtype == MapperType.KONAMI_8K:
        return read_konami_8k(ser, rom_info)
    elif mtype == MapperType.KONAMI_SCC:
        return read_konami_scc(ser, rom_info)
    elif mtype == MapperType.GENERIC_16K:
        return read_generic_16k(ser, rom_info)
    elif mtype == MapperType.GENERIC_8K:
        return read_generic_8k(ser, rom_info)
    elif mtype == MapperType.RTYPE:
        return read_rtype(ser, rom_info)
    elif mtype == MapperType.HARRYFOX:
        return read_harry_fox(ser, rom_info)
    elif mtype == MapperType.HALNOTE:
        return read_hal_note(ser, rom_info)
    elif mtype in [MapperType.NO_MAPPER_16K, MapperType.NO_MAPPER_32K, MapperType.NO_MAPPER_48K]:
        return read_standard_rom(ser, rom_info)
    else:
        print("Unknown mapper type")
        return None

# ============================================================================
# Main Mapper Detection
# ============================================================================

def detect_mapper(ser: Any, rom_info: ROM_INFO) -> bool:
    print("\n========== ROM DETECTION START ==========")
    print("\n=== Testing MegaROM Mappers ===")
    
    detectors = [
        detect_ascii_16k, detect_ascii_8k, detect_konami_8k, detect_konami_scc,
        detect_generic_16k, detect_generic_8k, detect_rtype, detect_harry_fox,
        detect_halnote, detect_standard_rom
    ]
    
    for detector in detectors:
        if detector(ser, rom_info):
            return True
            
    print("\nROM detection failed")
    return False

# ============================================================================
# Main Processing
# ============================================================================

def process_rom_read(output_file_arg: Optional[str], auto_file_name_mode: bool) -> int:
    import serial
    
    port = find_com_port()
    if not port:
        print("No suitable device found")
        return 1
        
    print(f"Found USB COM port: {port}\n")
    
    # outputFileArg == NULL の場合は、自動ファイル名モードと同じ動作にする
    if output_file_arg is None:
        auto_file_name_mode = True

    output_dir = "."
    if auto_file_name_mode:
        # 自動ファイル名モード時は outputFileArg を出力先ディレクトリとして扱う
        if output_file_arg:
            output_dir = output_file_arg
        else:
            output_dir = "."
    else:
        # 通常モード時は outputFileArg を出力ファイル名として扱う
        if output_file_arg:
            output_dir = os.path.dirname(output_file_arg) or "."
        else:
            output_dir = "."

    try:
        ser = serial.Serial(
            port=port,
            baudrate=BAUDRATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=SERIAL_TIMEOUT,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False
        )
    except Exception as e:
        print(f"Failed to open COM port: {e}")
        return 1

    print(f"Connected to {port}\n")

    try:
        if not slot_check(ser):
            print("ERROR: Cartridge is not properly inserted\n")
            return 1

        if not slot_power_on(ser):
            print("ERROR: Failed to power on slot\n")
            return 1

        if not slot_reset(ser):
            print("ERROR: Failed to reset on slot\n")
            slot_power_off(ser)
            return 1

        if not check_hash_with_retry(ser):
            print("ERROR: Failed to ROM Read :-( on slot\n")
            slot_power_off(ser)
            return 1

        rom_info = ROM_INFO()
        if not detect_mapper(ser, rom_info):
            print("Mapper detection failed\n")
            slot_power_off(ser)
            return 1

        if not slot_reset(ser):
            print("ERROR: Failed to reset on slot\n")
            slot_power_off(ser)
            return 1

        print("\n========== DETECTION RESULT ==========")
        print(f"Detected: {rom_info.mapperName}")
        print(f"Bank Count: {rom_info.bankCount if rom_info.bankCount > 0 else 'N/A'}")
        print(f"ROM Size: {rom_info.romSize} bytes (0x{rom_info.romSize:X})")

        rom_data = read_complete_rom(ser, rom_info)
        if not rom_data:
            print("ROM reading failed")
            slot_power_off(ser)
            return 1

        sha1 = hashlib.sha1(rom_data).hexdigest()
        print("\n========== SHA1 ==========")
        print(sha1)

        save_name = ""
        db_info, used_xml = find_rom_info_with_priority(sha1)

        if used_xml:
            if db_info.get("found"):
                print("\n========== DB MATCH ==========")
                print(f"Title  : {db_info['title']}")
                print(f"Company: {db_info['company']}")
                print(f"Year   : {db_info['year']}")
                print(f"System : {db_info['system']}")
                if db_info.get('status'): print(f"Status : {db_info['status']}")
                if db_info.get('remark'): print(f"Remark : {db_info['remark']}")

                save_name = build_auto_file_name(db_info)
            else:
                print(f"\n========== DB MATCH ==========\nNo match found in {used_xml}")
                if not auto_file_name_mode and output_file_arg:
                    print("Saving with specified output file name.")
                    save_name = os.path.basename(output_file_arg)
                else:
                    print("Saving with auto-generated file name.")
                    mapper_w = sanitize_mapper_name_for_file_name(rom_info.mapperName)
                    save_name = f"Unknown_{sha1}[{mapper_w}].rom"
        else:
            print("\nXML database not found: softwaredb.xml / msxromdb.xml")
            if not auto_file_name_mode and output_file_arg:
                print("Saving with specified output file name.")
                save_name = os.path.basename(output_file_arg)
            else:
                print("Saving with auto-generated file name.")
                mapper_w = sanitize_mapper_name_for_file_name(rom_info.mapperName)
                save_name = f"Unknown_{sha1}[{mapper_w}].rom"

        if not is_successful_rom_image(rom_data):
            save_name = "[unsuccessful]" + save_name

        final_path = os.path.join(output_dir, save_name)

        if os.path.exists(final_path):
            try:
                with open(final_path, "rb") as f:
                    existing_data = f.read()
                existing_sha1 = hashlib.sha1(existing_data).hexdigest()
                print("\n========== EXISTING FILE SHA1 ==========")
                print(existing_sha1)
                
                if existing_sha1 == sha1:
                    save_name = "[same]" + save_name
                else:
                    save_name = f"[other_{sha1}]" + save_name
            except Exception:
                print("\n========== EXISTING FILE SHA1 ==========")
                print("Failed to calculate SHA1 of existing file")
                save_name = "[same]" + save_name
                
            final_path = os.path.join(output_dir, save_name)

        try:
            print("\n=== Saving ROM to File ===\n")
            with open(final_path, "wb") as f:
                f.write(rom_data)
            print(f"ROM saved successfully: {final_path} ({len(rom_data)} bytes)")
        except Exception as e:
            print(f"[ERROR] File save failed: {e}")
            slot_power_off(ser)
            return 1

        print(f"\nSaved output: {final_path}")
        print("\nROM read and save completed successfully!\n")

        slot_power_off(ser)
        ser.close()
        return 0

    except Exception as e:
        print(f"An unexpected error occurred during processing: {e}")
        try:
            slot_power_off(ser)
            ser.close()
        except Exception:
            pass
        return 1

# ============================================================================
# Entry Point
# ============================================================================

def main():
    print("MSX Game Adapter ROM Dumper")
    print("Original Copyright @v9938")
    print("Build:   Python Port\n")

    args = sys.argv[1:]
    auto_file_name_mode = False
    output_file_arg = None

    for arg in args:
        if arg.lower() == "/auto":
            auto_file_name_mode = True
        else:
            output_file_arg = arg

    # 通常モード時は出力ファイル名必須
    # /auto 時は引数省略ならカレントディレクトリを使う
    if not auto_file_name_mode and output_file_arg is None:
        print(f"Usage: {sys.argv[0]} <output_file_path> [/auto]\n")
        print("Normal mode:")
        print(f"  {sys.argv[0]} <output_file_path>")
        print("    Save ROM using the specified output file path.\n")
        print("Auto file name mode:")
        print(f"  {sys.argv[0]} /auto [output_directory]")
        print("    Save ROM using an automatically generated file name.")
        print("    If [output_directory] is omitted, the current directory is used.\n")
        print("Notes:")
        print("  softwaredb.xml is used if present.")
        print("  If softwaredb.xml is not present, msxromdb.xml is used.")
        
        # 定義された対応マッパー一覧の表示
        print("\nSupported Mappers List:")
        for m_name in get_supported_mappers():
            print(f"  - {m_name}")
            
        sys.exit(1)

    result = process_rom_read(output_file_arg, auto_file_name_mode)
    print("Done.")
    sys.exit(result)

if __name__ == "__main__":
    main()
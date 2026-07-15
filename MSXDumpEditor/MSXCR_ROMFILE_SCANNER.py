# -*- coding: utf-8 -*-
# MSX_ROM_Scanner.py - MSX ROM File Scanner & DB Matcher
# Purpose: Scan ROM files in a specified directory, calculate SHA-1,
#          match with XML DB, and output/append to dump_list_log.csv.

import os
import sys
import datetime
import hashlib
import csv
import html

# ============================================================================
# Utilities copied from MSXCR_ROMDUMPER.py (Unchanged for compatibility)
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


def CalcSHA1Hex(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


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

# ============================================================================
# Scanning Logic
# ============================================================================

def ScanDirectory(targetDir: str) -> int:
    if not os.path.isdir(targetDir):
        print(f"Error: Directory not found: {targetDir}")
        return 1

    # XML データベースファイルの存在チェック
    softwareDbExists = os.path.isfile("softwaredb.xml")
    msxRomDbExists = os.path.isfile("msxromdb.xml")
    
    if not softwareDbExists and not msxRomDbExists:
        print("Warning: Neither softwaredb.xml nor msxromdb.xml was found in the current directory.")

    print(f"Scanning directory: {targetDir}\n")

    # 指定フォルダ内のファイルを走査
    files = [f for f in os.listdir(targetDir) if os.path.isfile(os.path.join(targetDir, f))]
    rom_files = [f for f in files if f.lower().endswith('.rom')]

    if not rom_files:
        print("No .rom files found in the directory.")
        return 0

    processed_count = 0

    for filename in rom_files:
        filePath = os.path.join(targetDir, filename)
        print(f"Processing: {filename}")

        # SHA-1 計算
        success, sha1 = CalcFileSHA1Hex(filePath)
        if not success:
            print(f"  Failed to calculate SHA1 for {filename}")
            continue

        # ROMの内容確認 (AB / CD ヘッダの検出)
        try:
            with open(filePath, "rb") as f:
                romData = f.read()
            romSize = len(romData)
        except Exception as e:
            print(f"  Failed to read file: {e}")
            continue

        # ヘッダー検証
        if IsSuccessfulROMImage(romData):
            romFileStatus = "OK"
        else:
            romFileStatus = "Unsuccessful"

        # XMLデータベース照合
        dbInfo, usedXmlPath = FindROMInfoWithPriority(sha1)

        dbStatus = "Unknown"
        title = ""
        company = ""
        year = ""
        system = ""
        status = ""
        remark = ""
        romType = "Standard ROM" # ファイルからマッパー自動判別は困難なため、既定値として設定

        if dbInfo["found"]:
            dbStatus = "MATCH"
            title = dbInfo["title"]
            company = dbInfo["company"]
            year = dbInfo["year"]
            system = dbInfo["system"]
            status = dbInfo["status"]
            remark = dbInfo["remark"]
            print(f"  -> DB MATCH: {title} ({system})")
        else:
            print("  -> DB MATCH: No match found")

        # ファイル作成/更新日時（または現在日時）
        try:
            mtime = os.path.getmtime(filePath)
            dumpDateTime = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            dumpDateTime = GetCurrentDateTimeString()

        # CSVに追記 (CSVファイルは targetDir に出力)
        csv_success = AppendDumpListLogCsv(
            targetDir,
            dbStatus,
            romFileStatus,
            status,
            title,
            company,
            year,
            system,
            remark,
            romType,
            romSize,
            sha1,
            dumpDateTime
        )

        if csv_success:
            processed_count += 1
        else:
            print("  Failed to write to CSV")

    print(f"\nScan completed. {processed_count} files processed and recorded in CSV.")
    return 0


# ============================================================================
# Entry Point
# ============================================================================

def main():
    print("MSX ROM Folder Scanner & DB Matcher")
    print(f"Run Date: {datetime.datetime.now().strftime('%b %d %Y %H:%M:%S')}")
    print()

    args = sys.argv[1:]
    if not args:
        prog_name = os.path.basename(sys.argv[0])
        print(f"Usage: python {prog_name} <target_directory_path>")
        print()
        print("Description:")
        print("  Scans all '.rom' files in the specified directory, calculates SHA-1,")
        print("  queries softwaredb.xml / msxromdb.xml, and creates or appends results")
        print("  to 'dump_list_log.csv' inside the target directory.")
        sys.exit(1)

    targetDir = args[0]
    result = ScanDirectory(targetDir)
    sys.exit(result)


if __name__ == '__main__':
    main()

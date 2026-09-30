# -*- coding: utf-8 -*-
# MSXCR_ROM_Scanner.py - MSX ROM File Scanner & DB Matcher
# Purpose: Scan ROM files in a specified directory, calculate SHA-1,
#          match with XML DB, output/append to dump_list_log.csv, and rename/deduplicate files.
# Copyright @v9938 (Ported to Python by @uniskie with gemini3.5 flash pro)

import os
import sys
import datetime
import hashlib
import csv
import html
import uuid

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
# File & CSV Operations
# ============================================================================

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
    return s.replace('"', '""')


def GetCurrentDateTimeString() -> str:
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


def AppendDumpListLogCsvWithIgnore(outputDir: str, dbStatus: str, romFileStatus: str, status: str,
                                    title: str, company: str, year: str, system: str, remark: str,
                                    romType: str, romSize: int, sha1: str, dumpDateTime: str) -> bool:
    csvPath = JoinPath(outputDir if outputDir else ".", "dump_list_log.csv")
    
    header_fields = [
        "DBステータス", "ROMファイルの状態", "ステータス", "タイトル",
        "メーカ", "年", "システム", "備考", "ROMタイプ", "容量", "SHA1値", "ダンプ日時"
    ]

    existing_rows = []
    has_valid_header = False

    if os.path.exists(csvPath) and os.path.getsize(csvPath) > 0:
        try:
            with open(csvPath, "r", newline="", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                first_row = next(reader, None)
                if first_row and len(first_row) >= 12 and first_row[0] == "DBステータス":
                    has_valid_header = True
                    existing_rows.append(first_row)
                
                for row in reader:
                    if len(row) >= 12:
                        existing_rows.append(row)
        except Exception as e:
            print(f"CSV read warning: {e}")

    if has_valid_header and len(existing_rows) > 1:
        for row in existing_rows[1:]:
            existing_sha1 = row[10].strip().lower()
            existing_datetime = row[11].strip()

            if len(existing_sha1) == 40:
                if existing_sha1 == sha1.strip().lower() and existing_datetime == dumpDateTime.strip():
                    print("  Log entry already exists in dump_list_log.csv. Skipped.")
                    return True

    new_row = [
        dbStatus, romFileStatus, status, title, company, year,
        system, remark, romType, str(romSize), sha1, dumpDateTime
    ]

    if not has_valid_header:
        existing_rows = [header_fields]
    
    existing_rows.append(new_row)

    try:
        with open(csvPath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerows(existing_rows)
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

    if dbInfo.get("has_different_system_duplicate", False):
        renamedFile = f"{titleW}({systemW})-{companyW}({yearW})"
    else:
        renamedFile = f"{titleW}-{companyW}({yearW})"

    if not IsIgnorableTagValue(statusW):
        renamedFile += f"[{statusW}]"

    if not IsIgnorableTagValue(remarkW):
        renamedFile += f"[{remarkW}]"

    renamedFile += ".rom"
    return renamedFile


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


def SafeRename(src_path: str, dst_path: str) -> bool:
    """Windowsの大文字小文字のみの変更やリネームに対応する安全な関数"""
    try:
        # 大文字小文字のみの変更の場合、一度一時名を経由
        if os.path.normcase(os.path.abspath(src_path)) == os.path.normcase(os.path.abspath(dst_path)):
            temp_path = src_path + f".tmp_{uuid.uuid4().hex[:8]}"
            os.rename(src_path, temp_path)
            os.rename(temp_path, dst_path)
        else:
            os.rename(src_path, dst_path)
        return True
    except Exception as e:
        print(f"\n[ERROR] Rename failed ({src_path} -> {dst_path}): {e}")
        return False


# ============================================================================
# Core Directory Scanner & Renamer
# ============================================================================

def ScanDirectory(targetDir: str, renameMode: bool = False) -> int:
    if not os.path.isdir(targetDir):
        print(f"Error: Directory not found: {targetDir}")
        return 1

    softwareDbExists = os.path.isfile("softwaredb.xml")
    msxRomDbExists = os.path.isfile("msxromdb.xml")
    
    if not softwareDbExists and not msxRomDbExists:
        print("Warning: Neither softwaredb.xml nor msxromdb.xml was found in the current directory.")

    print(f"Scanning directory: {targetDir}")
    print(f"Mode: {'RENAME & DEDUPLICATE' if renameMode else 'LOG ONLY (Dry run)'}\n")

    files = [f for f in os.listdir(targetDir) if os.path.isfile(os.path.join(targetDir, f))]
    # 大文字・小文字を問わず .rom ファイルを抽出
    rom_files = [f for f in files if f.lower().endswith('.rom')]

    if not rom_files:
        print("No .rom files found in the directory.")
        return 0

    processed_count = 0
    renamed_count = 0
    deleted_count = 0
    unchanged_count = 0

    for filename in rom_files:
        filePath = os.path.join(targetDir, filename)
        
        # 既に他の重複処理等で削除されている場合はスキップ
        if not os.path.exists(filePath):
            continue

        print("========================================")
        print(f"File   : {filename}")

        # SHA-1 計算
        success, sha1 = CalcFileSHA1Hex(filePath)
        if not success:
            print(f"Failed to calculate SHA1 for {filename}\n")
            continue

        print("\n========== SHA1 ==========")
        print(sha1)

        # ROMデータ読み込み
        try:
            with open(filePath, "rb") as f:
                romData = f.read()
            romSize = len(romData)
        except Exception as e:
            print(f"Failed to read file: {e}\n")
            continue

        # DB照合
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

                baseFileName = BuildAutoFileName(dbInfo)
            else:
                print(f"\n========== DB MATCH ==========")
                print(f"No match found in {usedXmlPath}")
                mapperW = SanitizeMapperNameForFileName("UnknownMapper")
                baseFileName = f"Unknown_{sha1}[{mapperW}].rom"
        else:
            print("\nXML database not found: softwaredb.xml / msxromdb.xml")
            mapperW = SanitizeMapperNameForFileName("UnknownMapper")
            baseFileName = f"Unknown_{sha1}[{mapperW}].rom"

        # ヘッダー検証 (AB / CD)
        if not IsSuccessfulROMImage(bytes(romData)):
            baseFileName = "[unsuccessful]" + baseFileName
            romFileStatus = "Unsuccessful"

        # --------------------------------------------------------------------
        # 重複・衝突判定ロジック
        # --------------------------------------------------------------------
        candidateName = baseFileName
        candidatePath = JoinPath(targetDir, candidateName)
        action = "RENAME"
        other_index = 0

        abs_file = os.path.abspath(filePath)

        while True:
            abs_cand = os.path.abspath(candidatePath)

            # 1. パス・大文字小文字ともに完全一致している場合
            if abs_file == abs_cand:
                action = "KEEP"
                break

            # 2. Windowsで大文字・小文字のみが異なる場合（自分自身）
            if os.path.normcase(abs_file) == os.path.normcase(abs_cand):
                action = "RENAME"
                break

            # 3. 候補先が存在しない場合（新規リネーム可能）
            if not os.path.exists(candidatePath):
                action = "RENAME"
                break

            # 4. 別の同名ファイルが既に存在する場合：ハッシュを比較
            success_exist, existingSha1 = CalcFileSHA1Hex(candidatePath)
            if success_exist and existingSha1.lower() == sha1.lower():
                # 同一ハッシュのファイルが既にあるため、自分を重複削除
                action = "DELETE"
                romFileStatus = "Duplicate(Deleted)"
                break
            else:
                # ハッシュが異なる別ファイルが存在する ➔ [OTHER] / [OTHER(n)] を付与
                romFileStatus = "Other"
                if other_index == 0:
                    candidateName = f"[OTHER]{baseFileName}"
                else:
                    candidateName = f"[OTHER({other_index})]{baseFileName}"
                candidatePath = JoinPath(targetDir, candidateName)
                other_index += 1

        # --------------------------------------------------------------------
        # ファイル操作実行
        # --------------------------------------------------------------------
        if renameMode:
            if action == "DELETE":
                try:
                    os.remove(filePath)
                    print(f"\nIdentical file already exists: {candidateName}")
                    print(f"Removed duplicate: {filename}")
                    deleted_count += 1
                except Exception as e:
                    print(f"\n[ERROR] Failed to delete duplicate file: {e}")
            elif action == "RENAME":
                if SafeRename(filePath, candidatePath):
                    print(f"\nRenamed output: {candidatePath}")
                    renamed_count += 1
            else:
                print(f"\nFile name is already up to date: {candidateName}")
                unchanged_count += 1
        else:
            if action == "DELETE":
                print(f"\n[Plan] -> Duplicate of '{candidateName}' (Will be deleted if /rename is set)")
                deleted_count += 1
            elif action == "RENAME":
                print(f"\n[Plan to Rename] -> {candidateName}")
                renamed_count += 1
            else:
                print(f"\n[Plan to Rename] -> (No change needed: {candidateName})")
                unchanged_count += 1

        # --------------------------------------------------------------------
        # CSV追記用メタデータ
        # --------------------------------------------------------------------
        dbStatus = "MATCH" if dbInfo["found"] else "Unknown"
        title = dbInfo["title"]
        company = dbInfo["company"]
        year = dbInfo["year"]
        system = dbInfo["system"]
        status = dbInfo["status"]
        remark = dbInfo["remark"]
        romType = "Unknown"

        try:
            mtime = os.path.getmtime(candidatePath if (renameMode and action != "DELETE" and os.path.exists(candidatePath)) else filePath)
            dumpDateTime = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            dumpDateTime = GetCurrentDateTimeString()

        csv_success = AppendDumpListLogCsvWithIgnore(
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

        if not csv_success:
            print("WARNING: Failed to append dump_list_log.csv")

        print()
        processed_count += 1

    # ------------------------------------------------------------------------
    # 最終結果サマリー表示
    # ------------------------------------------------------------------------
    print("========================================")
    print("Scan completed.")
    print(f"  Total processed  : {processed_count}")
    if renameMode:
        print(f"  Renamed files    : {renamed_count}")
        print(f"  Deleted files    : {deleted_count} (Duplicates)")
        print(f"  Unchanged files  : {unchanged_count}")
    else:
        print(f"  Plan to Rename   : {renamed_count}")
        print(f"  Plan to Delete   : {deleted_count} (Duplicates)")
        print(f"  No change        : {unchanged_count}")
    print()
    return 0


# ============================================================================
# Entry Point
# ============================================================================

def main():
    print("MSX ROM Folder Scanner & DB Matcher")
    print("Copyright @v9938")
    print(f"Run Date: {datetime.datetime.now().strftime('%b %d %Y %H:%M:%S')}")
    print()

    args = sys.argv[1:]
    renameMode = False
    targetDir = None

    for arg in args:
        if arg.lower() in ("/rename", "-rename", "--rename"):
            renameMode = True
        else:
            targetDir = arg

    if not targetDir:
        prog_name = os.path.basename(sys.argv[0])
        print(f"Usage: python {prog_name} <target_directory_path> [/rename]")
        print()
        print("Options:")
        print("  <target_directory_path>  Directory containing .rom files.")
        print("  /rename                  Actually rename and deduplicate files.")
        print("                           - Identical files (same SHA-1) will be removed.")
        print("                           - Different files with same name will get [OTHER] / [OTHER(n)].")
        print("                           (If omitted, only CSV logging is performed without file modification).")
        print()
        print("Description:")
        print("  Scans all '.rom' files, calculates SHA-1, queries softwaredb.xml / msxromdb.xml,")
        print("  appends results to 'dump_list_log.csv', and cleans up/standardizes ROM names.")
        sys.exit(1)

    result = ScanDirectory(targetDir, renameMode)
    sys.exit(result)


if __name__ == '__main__':
    main()

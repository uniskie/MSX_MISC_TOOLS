import sys
import os
import re
import datetime
import xml.etree.ElementTree as ET

def extract_doctype_declarations(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            matches = re.findall(r"(<!DOCTYPE\s+[^>]+>)", content, re.DOTALL)
            return [match.strip() for match in matches if match.strip()]
    except Exception:
        return []

def extract_cdata_blocks(file_path):
    cdata_contents = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            matches = re.findall(r"<!\[CDATA\[(.*?)\]\]>", content, re.DOTALL)
            for match in matches:
                if match:
                    cdata_contents.append(match)
    except Exception:
        pass
    return cdata_contents

def merge_msx_xml_overwrite(input_files, output_file):
    if not input_files:
        print("エラー: 入力ファイルが指定されていません。")
        return

    merged_dict = {}
    seen_doctype = set()
    unique_doctypes = []
    seen_cdata = set()
    unique_cdatas = []

    for file in input_files:
        doctypes = extract_doctype_declarations(file)
        for doctype in doctypes:
            if doctype not in seen_doctype:
                seen_doctype.add(doctype)
                unique_doctypes.append(doctype)

        cdatas = extract_cdata_blocks(file)
        for cdata in cdatas:
            if cdata not in seen_cdata:
                seen_cdata.add(cdata)
                unique_cdatas.append(cdata)

    try:
        for file_idx, file in enumerate(input_files):
            is_base_file = (file_idx == 0)
            
            with open(file, "r", encoding="utf-8") as f:
                raw_content = f.read()
            escaped_content = raw_content.replace("&amp;", "___AMP_TOKEN___").replace("&apos;", "___APOS_TOKEN___")
            
            file_root = ET.fromstring(escaped_content)
            
            for software in file_root.findall("software"):
                attr_key = frozenset(software.attrib.items())
                
                if attr_key in merged_dict:
                    existing_software = merged_dict[attr_key]
                    
                    for new_rom in software.findall("rom"):
                        new_sha1 = new_rom.get("sha1")
                        
                        is_duplicated = False
                        for idx, existing_rom in enumerate(existing_software.findall("rom")):
                            if existing_rom.get("sha1") == new_sha1:
                                if not is_base_file:
                                    print(f"{software.attrib}\n -> 置換: {new_rom.attrib}")
                                existing_software[idx] = new_rom
                                is_duplicated = True
                                break
                        
                        if not is_duplicated:
                            if not is_base_file:
                                print(f"{software.attrib}\n -> 追加: {new_rom.attrib}")
                            existing_software.append(new_rom)
                else:
                    if not is_base_file:
                        print(f"{software.attrib}\n -> 新規追加 (ソフトウェア全体)")
                    merged_dict[attr_key] = software

        new_root = ET.Element("softwaredb")
        for software in merged_dict.values():
            new_root.append(software)

        ET.indent(new_root, space="  ")
        xml_bytes = ET.tostring(
            new_root, 
            encoding="utf-8", 
            method="xml", 
            short_empty_elements=True
        )
        xml_string = xml_bytes.decode("utf-8")

        xml_string = xml_string.replace("___AMP_TOKEN___", "&amp;").replace("___APOS_TOKEN___", "&apos;")

        cdata_strings = ""
        for cdata_body in unique_cdatas:
            cdata_strings += f"\n<![CDATA[{cdata_body}]]>\n"

        final_xml = xml_string.replace("<softwaredb>", f"<softwaredb>{cdata_strings}", 1)

        total_roms = 0
        system_stats = {}
        for software in merged_dict.values():
            system_name = software.get("system")
            if system_name:
                rom_count = len(software.findall("rom"))
                total_roms += rom_count
                system_stats[system_name] = system_stats.get(system_name, 0) + rom_count

        sorted_systems = sorted(system_stats.keys())
        stats_parts = [f"{sys_name}: {system_stats[sys_name]}" for sys_name in sorted_systems]
        stats_string = " | ".join(stats_parts)

        now = datetime.datetime.now()
        timestamp = now.strftime("%a %b %d %Y - %H:%M:%S")

        summary_comment = (
            f"<!-- Roms in this XML file: {total_roms} - Created on {timestamp}\n"
            f"      Per platform: {stats_string} -->\n"
        )

        final_xml = final_xml.replace("</softwaredb>", f"{summary_comment}</softwaredb>")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("<?xml version='1.0' encoding='utf-8'?>\n")
            for doctype_line in unique_doctypes:
                f.write(f"{doctype_line}\n")
            f.write(final_xml)

        print(f"成功: {output_file} にマージしました。")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    import os
    script_name = os.path.basename(__file__)
    if len(sys.argv) < 3:
        print( "使い方:\n"
              f" python {script_name} <出力ファイル名> <入力ファイル1> <入力ファイル2> ...\n"
               " # ROMバリエーションのsha1要素が重複した場合は後から入力したほうで上書き"
              )
    else:
        output = sys.argv[1]
        inputs = sys.argv[2:]
        merge_msx_xml_overwrite(inputs, output)

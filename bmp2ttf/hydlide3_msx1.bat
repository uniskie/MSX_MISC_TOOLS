@set rom=hyd3msx1.rom
@set bmp=hydlide3_msx1_font.bmp
@set cfg=hydlide3_msx1_font_extract.cfg
@set json_main=hydlide3_msx1_main.json
@set json_oped=hydlide3_msx1_oped.json
extract_font.exe %rom% %bmp% -c %cfg%
bmp2ttf2.exe -c %json_main%
bmp2ttf2.exe -c %json_oped%
timeout /t 5

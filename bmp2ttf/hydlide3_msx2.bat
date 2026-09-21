@set rom=hyd3m2v2.rom
@set bmp=hydlide3_msx2_font.bmp
@set cfg=hydlide3_msx2_font_extract.cfg
@set json=hydlide3_msx2.json
extract_font.exe %rom% %bmp% -c %cfg% --vscale 2
bmp2ttf2.exe -c %json%
timeout /t 5

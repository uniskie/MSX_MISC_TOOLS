namespace eval save_debuggable {

set_help_text save2bmp \
{Dump a selected region of the video memory into a bitmap file.

save2bmp filename <start address> <width> <length> [<convert_mode>] [<neg_height>]

convert_mode: (default 0)
    0 = RAW DUMP
        - (bpp2*512 as bpp4*256 at screen 6/9)
    1 = Auto Stretch (Keeping the look of BMP)
		**** Can't use as dump data ****
        - vertical strech: x2 at screen 6/7/9
        - convert pixel: bpp2*512 to bpp4*512 at screen 6/9

neg_height: (default 1)
    0 = BitmapInfoHeader's height is positive value.
        - (BITMAP appears upside down)
    1 = BitmapInfoHeader's height is negative value.
        - (BITMAP looks natural)
        - (Not supported by some incomplete BMP viewer)

usage example: save2bmp RawDataDump.bmp 0 256 1024
}

# save2bmp  by uniskie
proc save2bmp {filename start dx dy {convert_mode 0} {neg_height 1}} {

	set screen_mode [get_screen_mode];
	# screen width
	switch -- $screen_mode {
		6 - 7 - 9 { set scr_width 512 }
		default   { set scr_width 256 }
	}
	# color palette count
	switch -- $screen_mode {
		8 - 11 - 12 { set pal_num 256 }
		default     { set pal_num 16  }
	}
	# pixel by byte
	switch -- $screen_mode {
		6 - 9       { set ppb 4 }
		8 - 11 - 12 { set ppb 1 }
		default     { set ppb 2 }
	}

	#screen6/9 ... BMP convert to 4bpp
	set bpp [expr {($ppb <= 2) ? (8 / $ppb) : 4}]
	# covert_mode 0 : screen6/9 -> width 256 / dynamic cast to bpp4
	# covert_mode 1 : screen6/9 -> width 512 / stretch to bpp4
	#               : screen6/7/8 -> height x2
	set scalex [expr (($convert_mode == 0) && ($ppb == 4)) ? 0.5 : 1]
	set scaley [expr ($convert_mode && ($scr_width == 512)) ? 2 : 1]
	set dsx [expr {int($dx * $scalex)}]
	set dsy [expr {int($dy * $scaley)}]

	set line_size [expr {$scr_width / $ppb}]
	set clen [expr int(($dx + $ppb - 1) / $ppb)]
	set cl_size [expr {($line_size < $clen) ? $line_size : $clen}]

	set file [open $filename "WRONLY CREAT TRUNC"]
	set data_len [expr {$dx * $dy / 2}]
	set pal_len [expr {$pal_num * 4} ]
	set head_len [expr {0x0E + 0x28}]
	set off_bits [expr {$head_len + $pal_len}]
	set file_len [expr {$off_bits + $data_len}]

	# ********* DEBUG ********
	#puts "line_size: $line_size"
	#puts "clen: $clen"
	#puts "screen: $screen_mode / width: $scr_width / colors: $pal_num"
	#puts "pixel per byte: $ppb"
	#puts "scaley: $scaley"
	#puts "BMP bit per pixel: $bpp"
	#puts [format "head_len: %06X" $head_len]
	#puts [format "file_len: %06X" $file_len]
	#puts [format "off_bits: %06X" $off_bits]
	#puts "dsx: $dsx"
	#puts "dsy: $dsy"
	# ************************

	fconfigure $file -translation binary -buffersize $file_len

	# *** BITMAPFILEHEADER ***
	# char	bfType[2];	// BMP FILE identificator 'BM'
	# u32	bfSize;		// File size
	# u16	bfReserved[2];	// fill zero
	# u32	bfOffBits;	// offset to bitmap data : (sizeof(BITMAPFILEHEADER) + sizeof(BITMAPINFOHEADER))
	puts -nonewline $file "\x42\x4d"								;# bfType
	puts -nonewline $file [format %c [expr {$file_len & 0xff}]]		;# bfSize
	puts -nonewline $file [format %c [expr {($file_len / 0x100 ) & 0xff}]]
	puts -nonewline $file [format %c [expr {($file_len / 0x10000) & 0xff}]]
	puts -nonewline $file "\x00"
	puts -nonewline $file "\x00\x00\x00\x00"						;# bfReserved
	puts -nonewline $file [format %c [expr {$off_bits & 0xff}]]		;# bfOffBits
	puts -nonewline $file [format %c [expr {($off_bits / 0x100 ) & 0xff}]]
	puts -nonewline $file "\x00\x00"

	# *** BITMAPINFOHEADER ***
	# u32	biSize;		// size of BITMAPINFOHEADER
	# s32	biWidth;	// pixel width
	# s32	biHeight;	// pixel height
	# u16	biPlanes;	// pixel plane
	# u16	biBitCount;	// screen0-7: 4bpp / screen8-12: 8bpp
	# u32	biCompression;	// compression flag
	# u32	biSizeImage;	// raw image data length
	# s32	biXPelsPerMeter;// no use
	# s32	biYPelsPerMeter;// no use
	# u32	biClrUsed;	// how many color used
	# u32	biClrImportant;	// important colors
	puts -nonewline $file "\x28\x00\x00\x00"						;#biSize
	puts -nonewline $file [format %c [expr {$dsx & 0xff}]]			;#biWidth
	puts -nonewline $file [format %c [expr {($dsx / 0x100) & 0xff}]]
	puts -nonewline $file "\x00\x00"
	if {$neg_height} {
		puts -nonewline $file [format %c [expr {-$dsy & 0xff}]]			;#biHeight
		puts -nonewline $file [format %c [expr {(-$dsy / 0x100) & 0xff}]]
		puts -nonewline $file "\xff\xff"
	} else {
		puts -nonewline $file [format %c [expr {$dsy & 0xff}]]			;#biHeight
		puts -nonewline $file [format %c [expr {($dsy / 0x100) & 0xff}]]
		puts -nonewline $file "\x00\x00"
	}
	puts -nonewline $file "\x01\x00"								;# biPlanes      : 1 plane used
	puts -nonewline $file [format %c $bpp]							;# biBitCount    : 4 bits per pixel
	puts -nonewline $file "\x00"
	puts -nonewline $file "\x00\x00\x00\x00"						;#biCompression : no compression used
	puts -nonewline $file [format %c [expr {$data_len & 0xff}]]		;#biSizeImage
	puts -nonewline $file [format %c [expr {($data_len / 0x100) & 0xff}]]
	puts -nonewline $file [format %c [expr {($data_len / 0x10000) & 0xff}]]
	puts -nonewline $file "\x00" 
	puts -nonewline $file "\x00\x00\x00\x00"						;#biXPelsPerMeter
	puts -nonewline $file "\x00\x00\x00\x00"						;#biYPelsPerMeter
	puts -nonewline $file [format %c [$pal_num]]
	puts -nonewline $file "\x00\x00\x00"						;#biClrUsed
	puts -nonewline $file "\x00\x00\x00\x00"						;#biClrImportant

	#set color palette BGRA
	for {set col 0} {$col < $pal_num} {incr col} {
		if {$pal_num == 256} {
			# GGGRRRBB
			set g [expr ($col / 32) & 7]
			set r [expr ($col / 4 ) & 7]
			set b [expr ($col * 2 ) & 7]
			set color [format "%1d%1d%1d" $r $g $b]
		} else {
			if {$bpp == 2} {
				set color [getcolor [expr ($col & 3)]]
			} else {
				set color [getcolor $col]
			}
		}
		#puts "color $col : $color"
		puts -nonewline $file [format %c [expr {[string index $color 2] * 255 / 7}]]
		puts -nonewline $file [format %c [expr {[string index $color 1] * 255 / 7}]]
		puts -nonewline $file [format %c [expr {[string index $color 0] * 255 / 7}]]
		puts -nonewline $file "\x00"
	}

	set cur_addr $start
	if {($ppb == 4) && ($scalex == 1)} {
		# screen 6/9
		for {set i 0} {$i < $dy} {incr i} {
			for {set l 0} {$l < $scaley} {incr l} {
				for {set addr $cur_addr} {$addr < ($cur_addr + $cl_size)} {incr addr} {
					set p [vpeek $addr]
					puts -nonewline $file [format %c [expr {($p & 0x30)/16+($p & 0xc0)/4}]]
					puts -nonewline $file [format %c [expr {($p & 0x03)+($p & 0x0c)*4}]]
				}
			}
			set cur_addr [expr {$cur_addr + $line_size}]
		}
	} else {
		# screen 0/1/2/3/4/5/6/7/8/9/11/12
		for {set i 0} {$i < $dy} {incr i} {
			for {set l 0} {$l < $scaley} {incr l} {
				for {set addr $cur_addr} {$addr < ($cur_addr + $cl_size)} {incr addr} {
					puts -nonewline $file [format %c [vpeek $addr]]
				}
			}
			set cur_addr [expr {$cur_addr + $line_size}]
		}
	}
	close $file

}

namespace export save2bmp

} ;# namespace save_debuggable

namespace import save_debuggable::*

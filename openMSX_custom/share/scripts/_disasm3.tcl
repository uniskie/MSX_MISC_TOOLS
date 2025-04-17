# source $env(OPENMSX_USER_DATA)/scripts/_disasm3.tcl

namespace eval disasm3 {

#
# get_symbol
#
set_help_text get_symbol \
{get_symbol <value>
Returns the label that matches the value from the symbols registered in the Symbol Manager.
(Returns the first one found.)
}
proc get_symbol {value} {
	return [lindex [debug symbols lookup -value $value] 0 3]
}

set_help_text from_symbol \
{from_symbol <name>
Returns the value that matches label name from the symbols registered in the Symbol Manager.
(Returns the first one found.)
}
proc from_symbol {name} {
	set a [lindex [debug symbols lookup -name $name] 0 3]
	if {[llength $a]} {
		return [format "0x%04X" $a]
	}
}

#
# disasm3_l
#
set_help_text disasm3_l \
{disasm3_l <addr>
debug disasm variation (dis-assemble one line with label)
}
proc disasm3_l {addr} {
	set hex [lrange [debug disasm $addr] 1 end]
	set bin [binary format H* [join $hex {}]]
	set dsa [debug disasm_blob $bin $addr {get_symbol}]
	return [concat [list [lindex $dsa 0]] $hex]
}
#proc disasm3_l {addr} {
#	set bin [debug read_block memory $addr 4]
#	set dsa [debug disasm_blob $bin $addr {get_symbol}]
#	set cnt [lindex $dsa 1]
#	set hex {}
#	for {set i 0} {$i < $cnt} {incr i} {
#		binary scan $bin [join [list "x" $i "H2"] {}] h
#		lappend hex $h
#	}
#	return [concat [list [lindex $dsa 0]] $hex]
#}

#
# disasm3
#
set_help_text disasm3 \
{Disassemble z80 instructions

Usage:
  disasm3               Disassemble 8 instr starting at the currect PC
  disasm3 <start>       Disassemble 8 instr starting at address <adr>
  disasm3 <start> <end> Disassemble <num> instr starting at address <addr>

  start,end ... can use symbol name.  ** case sensitive **
  end ... can use relative size.
          e.g.) disasm3 0x4000 +0x1f
                same as `disasm3 0x4000 0x401f`

  based on disasm2: https://www.msx.org/forum/msx-talk/openmsx/openmsx-disasm
}
proc disasm3 {{address -1} {endadr -1} {useadr 0}} {
	set a [from_symbol $address]
	if {[string length $a]} {set address $a}
	if {$address == -1} {set address [reg PC]}

	set a [from_symbol $endadr]
	if {[string length $a]} {set endadr $a}
	if {[string index $endadr 0] == "+"} {set endadr [expr {$address + $endadr}]}
	if {$endadr == -1} {set endadr [expr {$address + 16}]}
	if {$endadr > 65535} {set endadr 0xffff}

	#puts [format "start:0x%04X, end:0x%04X" $address $endadr]

	# pick up address list
	set addr $address
	while {$addr<=$endadr} {
		set data [debug disasm $addr]
		set start [string first "#" $data]
		if {$start != -1} {
			scan [string range $data $start end] "#%x" curadr
			if {$curadr >= $address && $curadr <= $endadr} {
				lappend adrlist $curadr
			}
		}
		set b [llength $data]
		set addadr [expr {($b < 1 ? 1 : $b -1)}]
		#set addr [expr {($addr + [llength $data] - 1) & 0xFFFF}] ;NG : over flow -> 0000 -> inifinite loop
		set addr [expr {$addr + $addadr}]
	}
	# tail guardian (need Explicit integer specification)
	lappend adrlist  int(0x7FFFFF)

	# process list
	set addr $address
	set adrlist [lsort -dictionary -unique $adrlist]
	set ind 0
	set curadr [lindex $adrlist $ind]

	# list top
	if {$addr != $curadr} {
		set label [get_symbol $addr]
		set label_l [llength $label]
		if {$label_l == 0} {
			append result [format ".X%04X: \n" $addr]
		}
	}

	# list lines
	while {$addr<=$endadr} {
		#address label
		set label [get_symbol $addr]
		set label_l [llength $label]
		if {$label_l} {
			append result [format "%s: \n" $label]
		}
		if {$addr == $curadr} {
		#	if {$label_l == 0} {
				append result [format ".X%04X: \n" $curadr]
		#	}
			incr ind
			set curadr [lindex $adrlist $ind]
		}
		append result " "
		set data [debug disasm $addr]

		set dstr [string toupper [lindex $data 0]]
		set dump \t\;[format "%04X: %s" $addr [join [lrange $data 1 end]]]

		#nemonic get value string
		set start [string first "#" $dstr]
		set adr_l 0
		set pointr -1
		if {$start >= 0} {
			set e $start
			for {set i 1} {$i < 8} {incr i} {
				if {[string match -nocase {[0-9A-F]} [string index $dstr [expr $e+1]]]} {
					incr e
				} else {
					break
				}
			}
			set adr_l [expr $e - $start]
			set adr_s [string range $dstr [expr $start+1] $e]
			if {$adr_l == 4} {
				scan $adr_s "%x" pointr
			} else {
				set pointr -1
			}
		}
		#get label
		if {$pointr < 0}  {
			set label ""
		} else {
			set label [get_symbol $pointr]
		}

		#replace address
		if {[llength $label]} {
			set nemonic [string map [list #$adr_s $label] $dstr]
		} elseif {$pointr >= $address && $pointr <= $endadr} {
			set nemonic [string map {"#" .X} $dstr]
		} else {
			set nemonic $dstr
		}
		
		#tab reformat text
		set trimed [string trimright $nemonic]
		set spacing [string repeat " " [expr 22-[string length $trimed]]]
		append result $trimed$spacing$dump\n

		set b [llength $data]
		set addadr [expr {($b < 1 ? 1 : $b -1)}]
		#set addr [expr {($addr + [llength $data] - 1) & 0xFFFF}] ;NG : over flow -> 0000 -> inifinite loop
		set addr [expr {$addr + $addadr}]

		#intermediate completion label
		while {$addr > $curadr} {
			append result [format ".X%04X: EQU $[expr ($curadr-$addr)]\n" $curadr]
			incr ind
			set curadr [lindex $adrlist $ind]
		}
	}
	return $result
}

namespace export from_symbol
namespace export get_symbol
namespace export disasm3_l
namespace export disasm3


} ;# namespace disasm3

namespace import disasm3::*

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

#
# disasm3_sub
#
set_help_text disasm3_sub \
{disasm3_sub <addr>
}
proc disasm3_sub {addr} {
	set data [debug read_block memory $addr 4]
	return [debug disasm_blob $data $addr {get_symbol}]
}

#
# disasm3
#
set_help_text disasm3 \
{Disassemble z80 instructions

Usage:
  disasm3               Disassemble 8 instr starting at the currect PC
  disasm3 <start>       Disassemble 8 instr starting at address <adr>
  disasm3 <start> <end> Disassemble <num> instr starting at address <addr>
  disasm3 <start> <end> <useadr>  useadr==1 ... 
  https://www.msx.org/forum/msx-talk/openmsx/openmsx-disasm
}
proc disasm3 {{address -1} {endadr -1} {useadr 0}} {
	if {$address == -1} {set address [reg PC]}
	if {$endadr == -1} {set endadr [expr {$address + 16}]}
	set addr $address
	while {$addr<=$endadr} {
		set data [debug disasm $addr]

		set start [string first "#" $data]
		if {$start ne -1} {
			scan [string range $data $start end] "#%x" curadr
			if {$curadr >= $address && $curadr <= $endadr} {lappend adrlist $curadr}
		}
		set label [get_symbol $addr]
		if {[llength $label]} {lappend adrlist $addr}
		set addr [expr {($addr + [llength $data] - 1) & 0xFFFF}]
	}
	lappend adrlist 99999
	set pointr 99999
	set addr $address
	set ind 0
	set adrlist [lsort -dictionary -unique $adrlist]
	set curadr [lindex $adrlist $ind]

	# list top
	set label [get_symbol $addr]
	#if {[llength $label]} {
	#	append result $label ": \n"
	#} else {
		append result [format ".X%04X: \n" $addr]
	#}
	if {$addr == $curadr} {
		incr ind
		set curadr [lindex $adrlist $ind]
	}

	while {$addr<=$endadr} {
		if {$addr == $curadr} {
			set label [get_symbol $addr]
			if {[llength $label]} {
				append result $label ": \n"
			} else {
				append result [format ".X%04X: \n" $curadr]
			}
			incr ind
			set curadr [lindex $adrlist $ind]
		}
		append result " "
		set datar [debug disasm $addr]
		set data [disasm3_sub $addr]
		set start [string first "#" $data]
		scan [string range $data $start end] "#%x" pointr
		set dump \t\;[format "%04X: %s" $addr [join [lrange $datar 1 4]]]
		if {$pointr >= $address && $pointr <= $endadr} {
		#	append result [string map {# .X} [string toupper [lindex $data 0]\n]]
			append result [string map {# .X} [string toupper [lindex $data 0]$dump\n]]
		} else {
		#	append result [string toupper [lindex $data 0]\n]
			append result [string toupper [lindex $data 0]$dump\n]
		}
		set addr [expr {($addr + [llength $datar] - 1) & 0xFFFF}]
		while {$addr > $curadr} {
			append result [format ".X%04X: EQU $[expr ($curadr-$addr)]\n" $curadr]
			incr ind
			set curadr [lindex $adrlist $ind]
		}
	}
	return $result
}

namespace export get_symbol
namespace export disasm3_sub
namespace export disasm3


} ;# namespace disasm3

namespace import disasm3::*

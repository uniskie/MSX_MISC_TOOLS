# additional user_script lazy

# List of Tcl-scripts that can be loaded on-demand. For each script you also
# needs to provide a list of Tcl procs that it provides.
#  (preferably keep this list sorted on script name)

# > init.tcl: Skip scripts that start with a '_' character. (By convention) those
# >           are loaded on-demand (see 'lazy.tcl').

register_lazy "_bmp_util.tcl" {save2bmp}
register_lazy "_disasm3.tcl" {get_symbol}
register_lazy "_disasm3.tcl" {from_symbol}
register_lazy "_disasm3.tcl" {disasm3_sub}
register_lazy "_disasm3.tcl" {disasm3}

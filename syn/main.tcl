# Import Design


set source_path ./verilog/
set file BT_MULT
set syn_path ./syn/
set design DUT
set sv 1

if {$sv} {
read_file -format sverilog  ${source_path}${file}.sv
} else {
read_file -format verilog  ${source_path}${file}.v
}

current_design [get_designs $design]
link

source -echo -verbose _syn.sdc

# Compile Design
current_design [get_designs $design]

set high_fanout_net_threshold 0

uniquify
set_fix_multiple_port_nets -all -buffer_constants [get_designs *]

#compile 
compile_ultra
# Output Design
current_design [get_designs $design]

remove_unconnected_ports -blast_buses [get_cells -hierarchical *]

set bus_inference_style {%s[%d]}
set bus_naming_style {%s[%d]}
set hdlout_internal_busses true
change_names -hierarchy -rule verilog
define_name_rules name_rule -allowed {a-z A-Z 0-9 _} -max_length 255 -type cell
define_name_rules name_rule -allowed {a-z A-Z 0-9 _[]} -max_length 255 -type net
define_name_rules name_rule -map {{"\\*cell\\*" "cell"}}
define_name_rules name_rule -case_insensitive
change_names -hierarchy -rules name_rule

write -format ddc     -hierarchy -output  ${syn_path}/${design}/${design}_syn.ddc
#EX:"FAS_syn.ddc"
if {$sv} {
write -format sverilog -hierarchy -output  ${syn_path}/${design}/${design}_syn.sv
} else {
write -format verilog -hierarchy -output  ${syn_path}/${design}/${design}_syn.v
}
#EX:"FAS_syn.v"
write_sdf -version 2.1  ${syn_path}/${design}/${design}_syn.sdf
echo "usage: $ DESIGN=\[design\] TEST=\[test\] MODULE=\[module\] COND=\[condition\] pt_shell "
echo "       $ pt_shell> source primetime.tcl" 
echo "ex   : $  DESIGN=PE_3ns_cg_ultra_070322 TEST=PETEST COND=_5ns pt_shell MODULE=PE"
set company {NTUGIEE}                                                                                                            
set designer {EnHo}                                                                                                              
set memdb_path ~/research/lpAccel/src/MEM/memdb                                                                                  
set memdb_list [ glob  ${memdb_path}/*.db ]                                                                                      
#glob return each names of files that matches the pattern                                                                        
echo $memdb_list                                                                                                                 
set search_path [concat  [list . /opt/CAD/cell_lib/CBDK_TSMC90GUTM_Arm_f1.0/CIC/SynopsysDC/db .] $search_path $memdb_path]       
echo $search_path                                                                                                                
#set search_path [concat  [list . /opt/CAD/cell_lib/CBDK_IC_Contest_v2.1/SynopsysDC/db .] $search_path]                          
set link_library [list "dw_foundation.sldb" "typical.db" "slow.db" "fast.db" ]                                                   
set link_library [concat $link_library $memdb_list ]                                                                             
#set target_library [list "typical_hvt.db" "slow.db" "fast.db"]                                                                       
set target_library [list "typical.db" ]                                                                       
set target_library [concat $target_library $memdb_list]                                                                          
set link_path "* $target_library"
#============ parsed variables ================
proc my_get_unix { var , deflt } {
    return [ expr { [ catch {  get_unix_variable $var  } ] ? $deflt : [ get_unix_variable $var ] }] 
}
set design [ get_unix_variable DESIGN] 
set module [ my_get_unix MODULE , TOP] 
set test   [ my_get_unix TEST , Top_test]
set cond   [ my_get_unix COND , ""]
echo $design 
echo $module
echo $cond
read_verilog ./${design}.v
current_design $module 
link
set power_enable_analysis "true"
set power_analysis_mode "averaged"
set cond [expr {$cond=="" ? "": "_${cond}" }]
set saif_file ../sim/${design}_${test}${cond}.fsdb.saif
echo $saif_file
read_saif $saif_file -strip_path ${test}/dut
set write_file ./rpt/${design}_${test}${cond}_power.txt
report_switching_activity -list_not_annotated > $write_file 
report_power -verbose -hierarchy >> $write_file 
report_power >> $write_file 
exit

                                                                                                                                  
# set company {NTUGIEE}                                                                                                            
# set designer {EnHo}                                                                                                              
# set memdb_path ~/research/lpAccel/src/MEM/memdb                                                                                  
# set memdb_list [ glob  ${memdb_path}/*.db ]                                                                                      
# #glob return each names of files that matches the pattern                                                                        
# echo $memdb_list                                                                                                                 
# set search_path [concat  [list . /opt/CAD/cell_lib/CBDK_TSMC90GUTM_Arm_f1.0/CIC/SynopsysDC/db .] $search_path $memdb_path]       
# echo $search_path                                                                                                                
# #set search_path [concat  [list . /opt/CAD/cell_lib/CBDK_IC_Contest_v2.1/SynopsysDC/db .] $search_path]                          
# set link_library [list "dw_foundation.sldb" "typical.db" "slow.db" "fast.db" ]                                                   
# set link_library [concat $link_library $memdb_list ]                                                                             
# set target_library [list "typical.db" "slow.db" "fast.db"]                                                                       
# set target_library [concat $target_library $memdb_list]                                                                          
#                                                                                                                                  
#
#
#set search_path "tsmc28/sram/NLDM tsmc28/cell/db ../src"
#set target_library "ts1n28lpb128x16m4sr_180a_tt1p05v25c.db ts1n28lpb256x16m4sr_180a_tt1p05v25c.db ts1n28lpb32x128m4sr_180a_tt1p05v25c.db ts1n28lpb32x144m4sr_180a_tt1p05v25c.db ts1n28lpb32x144m4sr_180a_tt1p05v25c.db ts1n28lpb64x16m4sr_180a_tt1p05v25c.db ts1n28lpb32x16m4sr_180a_tt1p05v25c.db ts1n28lpb64x128m4sr_180a_tt1p05v25c.db ts1n28lpb64x144m4sr_180a_tt1p05v25c.db tcbn28lpbwp30p140tt1p05v25c_ccs.db"
#set link_library "* $target_library dw_foundation.sldb"
#set link_path "* $target_library"
#read_verilog ./Top_syn.v
#current_design Top
#link
#set power_enable_analysis "true"
#set power_analysis_mode "averaged"
#read_saif ../sim/Top_syn.fsdb.saif -strip_path "Top_test/u_top/u_top"
#report_switching_activity -list_not_annotated > ./rpt/30_power.txt
#report_power -verbose -hierarchy >> ./rpt/30_power.txt
#exit
#
#

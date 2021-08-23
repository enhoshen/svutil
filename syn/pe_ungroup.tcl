set ungroup_cells {}
foreach_in_collection d [get_designs { \
    RF_2P RF_2P_* \
    RF_2P_MSK RF_2P_MSK_* \
    DataPathController \
    FetchStage \
    MultStage \
    SumStage \
    PathStage  
}] {
	set dname [get_object_name $d]
	echo $dname
	foreach_in_collection c [get_cells -hier -filter ref_name==$dname] {
		lappend ungroup_cells [get_object_name $c]
	}
}
uniquify
ungroup -flatten $ungroup_cells

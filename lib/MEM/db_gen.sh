LC_PATH=/opt/CAD/synopsys/lc/cur/bin/lc_shell
echo "use read_lib [file].lib"
echo "then write_lib [instance] -output [instance].db"
conds=( ff_1.1_-40.0 ff_1.1_125.0 ss_0.9_125.0 tt_1.0_25.0 ) 
_conds=( ff40 ff125 ss125 tt25 )
for i in "${!_conds[@]}"
 do
    echo $i ${_conds[i]}
 done
echo "condition"
 read IN

COND=${conds[$IN]} MODULE=$1 LIB_PATH=memlib/ DB_PATH=memdb/ $LC_PATH -f lib2db.tcl 



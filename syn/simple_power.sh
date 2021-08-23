echo "usage define three env varaiables DESIGN, TEST, MODULE beforehand" 
[ -z $COND ] && cond="" || cond="_$COND"
echo $cond
fsdbfile="../sim/${DESIGN}_${TEST}${cond}.fsdb"
echo $fsdbfile
sh fsdb2saif.sh $fsdbfile 
pt_shell -f primetime.tcl

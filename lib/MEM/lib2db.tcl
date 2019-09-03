#set files [glob memv/*.v]
set cond [ get_unix_variable COND]
set mod [ get_unix_variable MODULE]
set lib [ get_unix_variable LIB_PATH]
set db [ get_unix_variable DB_PATH ]
echo $mod
#foreach f  [glob $lib$mod*] {
#set module [ file rootname [file tail $f]]
#echo "filename:" $f
#read_lib $f
#set instance [file tail [ file rootname $f]]
#echo instance: $instance
#write_lib $mod -output $db$instance.db
#}
read_lib $lib$mod\_$cond\_syn.lib
write_lib $mod -output $db$mod.db
exit

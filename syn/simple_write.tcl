write_sdf $write_name.sdf
write_sdc $write_name.sdc
write -format ddc -o ./$write_name.ddc -hier
write -format verilog -o ./$write_name.v -hier

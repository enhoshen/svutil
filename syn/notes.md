# Synthesis and tools notes
## design compiler
* use variables just like using shell
useful variable such as `$current_design`, so that your tcl files can be easily modular.
```shell
source $current_design\_syn.sdc
report_timing >> $current_design.txt
```
* Design compiler `DC` macro: when trying to synthesize my design, you'd try to define sythesis related macro like defining `SIM`,`GATE_LEVEL` 
Macros for simulations, and it's tricky to define macro inside dc_shell. Haven't try other workarounds, but using 
the design compiler built-in **`DC`** macro is enough for synthesis purpose so far.
```verilog
    //inside define.sv, GenCfg
    `ifdef SIM                                
         parameter GenMode GENMODE = SIM;      
    `elsif DC //DC macro is automatically defined as inside dc_shell         
         parameter GenMode GENMODE = SYN;      
    `elsif FPGA                               
         parameter GenMode GENMODE = FPGA;     
    `else
    `endif
```
* dc_shell user defined variable: following tcl rules, the method to initialize your own variable is
```shell
$dc_shell> set mymodule PE_2-5ns 
$dc_shell> echo $mymodule
$dc_shell> report_timing > $mymodule.txt
```
* The help "command" for these shells tool is the unix `man`, just type `man` followed by your questioned command.
```shell
$dc_shell> man get_unix_variable
$pt_shell> man read_saif
```
# Synthesis issues
## An unexpected critical path
* As prof suggested, some unexpected critical path may occured if logics are not properly blocked by registers,
this will directly impact the resulting **area** and timing. At first I couldn't figure out how synthesizing  
MATmux module resulting much smaller area than doing it inside the PE, by following prof's suggestion and found  
out that the output of MultStage is directly connected to MATmux sum and wasn't blocked behind the register,  
and the following synthesis results makes much more sense.
```verilog
//inside MultStage.sv
        MATmux MA (                                             
                .*,                                                     
                .i_ipix(i_data[pe_row].Input_FS),                               
                .i_wpix(i_data[pe_row].Weight_FS),                              
                .o_sum(o_data[pe_row].Sum_MS) // this line connect output directly to comb circuit                                   
                );             
//after modification in sequential part
        for ( int i=0 ; i<PEROW ; ++i)begin
            o_data[i].Psum_MS <= '0;
            o_data[i].Sum_MS <= '0;
        end
    `ff_cg( `rdyNack(FS) || `rdyNack(MS) )
        o_MSpipe_MS <= {i_pipe.ssctl,i_pipe.ssppctl};
        for ( int i=0 ; i<PEROW ; ++i)begin
            o_data[i].Psum_MS <= i_data[i].Psum_FS ;
            o_data[i].Sum_MS <= sum[i];
        end
    `ff_e
``` 
from this example, the moral is that when examine a unreasonable large synthesis result, you might  
need to check **critical path**, where it might be a cause of unblocked comb wires.
## Unexpected broken synthesis with rtl simulation intact
* This could be related to clock gate signal closely
```verilog
//inside DatapathController
    ce = s_main == MAIN || PE_inst.dval;
    // this is used as a clock gating signal
    // this seems to break the entire controller so the system breaks entirely
    ce = s_main == MAIN || s_main == IDLE;
```
it is very very hard to pinpoint the mistake of a failed synthesized code out of the blue especially for the simulation results working perfectly. So modify your clock-gating signal very carefully.


`define RF2PIf_logic(logname , WORDWD , DWD , AWD)\
    logic logname``_read;\
    logic logname``_write;\
    logic [AWD-1:0] logname``_raddr;\
    logic [AWD-1:0] logname``_waddr;\
    logic [DWD-1:0] logname``_rdata;\
    logic [DWD-1:0] logname``_wdata;\
    logic           logname``_rvalid;
`define RF2PIf_sharedCtl_logic( logname , WORDWD , DWD , AWD)\
    logic logname``_read;\
    logic logname``_write;\
    logic [AWD-1:0] logname``_raddr;\
    logic [AWD-1:0] logname``_waddr;\
    logic           logname``_rvalid;
`define RF2PIf_pc_rf(logname)\
    .i_read(logname``_read),\
    .i_write(logname``_write),\
    .i_raddr(logname``_raddr),\
    .i_waddr(logname``_waddr),\
    .o_rdata(logname``_rdata),\
    .i_wdata(logname``_wdata)
`define RF2PIf_sharedCtl_pc_rf(logname)\
    .i_read(logname``_read),\
    .i_write(logname``_write),\
    .i_raddr(logname``_raddr),\
    .i_waddr(logname``_waddr)
`define RF2Pinstance(  name )\
      name(\
    .QA  (o_rdata),\
    .CLKA(i_clk),\
    .CENA(re_n),\
    .AA  (raddr),\
    .CLKB(i_clk),\
    .CENB(we_n),\
    .AB  (waddr),\
    .DB  (i_wdata),\
    .EMAA(EMA),\
    .EMAB(EMA)\
    );
`define RF2Pinstance_arr(  name , idx)\
      name(\
    .QA  (o_rdata[idx]),\
    .CLKA(i_clk),\
    .CENA(re_n),\
    .AA  (raddr),\
    .CLKB(i_clk),\
    .CENB(we_n),\
    .AB  (waddr),\
    .DB  (i_wdata[idx]),\
    .EMAA(EMA),\
    .EMAB(EMA)\
    );
`define RF2Pinstance_msk_arr( name , idx)\
    name (\
    .QA(o_rdata[idx]),\
    .CLKA(i_clk),\
    .CENA(re_n),\
    .AA(raddr),\
    .CLKB(i_clk),\
    .CENB(we_n),\
    .WENB(wmsk_n),\
    .AB(waddr),\
    .DB(i_wdata[idx]),\
    .EMAA(EMA),\
    .EMAB(EMA)\
    );
`define SRAMSPinstance_arr( name , idx)\
    name (\
    .Q(o_rdata[idx]),\
    .CLK(i_clk),\
    .CEN(ce_n),\
    .WEN(we_n),\
    .A(addr),\
    .D(i_wdata[idx]),\
    .EMA(EMA)\
    ); 

package RFCfg;
    typedef enum logic [1:0] { D16 , D32 } DWD_mode;
    task automatic ErrorRF;
        begin
            $display("RF configuration wrong!");
            $finish();
        end
    endtask
endpackage 
package SRAMCfg;
    typedef enum logic [1:0] { D16 , D32 } DWD_mode;
    typedef enum logic {READ , WRITE} SP_rwmode;
    task automatic ErrorSRAM;
        begin
            $display("SRAM configuration wrong!");
            $finish();
        end
    endtask
endpackage 
/*
package SramCfg;                                    
    typedef enum {BEHAVIOUR} GenerateMode;          
    typedef enum {UNDEF, OLD, NEW} ConcurrentRW;    
    parameter GenerateMode GEN_MODE = BEHAVIOUR;    
    parameter ConcurrentRW CON_RW = UNDEF;          
endpackage                                          
*/

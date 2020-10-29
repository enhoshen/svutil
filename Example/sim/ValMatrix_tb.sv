
import "DPI-C" function string getenv(input string env_name);
`timescale 1ns/1ns
`include "testdefines.sv"
`include "common/Define.sv"
`include "ValMatrix_include.sv"
`define TIMEOUTCYCLE 100
`define HCYCLE 5
`define TEST_CFG //TODO
`define FSDBNAME(suffix) `"ValMatrix_tb``suffix``.fsdb`"
module ValMatrix_tb;
    logic clk;
    logic rst;
    int clk_cnt;
    `Pos(rst_out, rst)
    `PosIf(ck_ev , clk, rst)
    logic intr_any, init_cond, resp_cond, fin_cond, sim_stop, sim_pass, time_out; //TODO modify event condition
    `PosIf(intr_ev, intr_any,     rst)//TODO modify reset logic
    `PosIf(init_ev, init_cond,    rst)//TODO modify reset logic
    `PosIf(resp_ev, resp_cond,    rst)//TODO modify reset logic
    `PosIf(fin_ev, fin_cond,      rst)//TODO modify reset logic
    `PosIf(sim_stop_ev, sim_stop, rst)//TODO modify reset logic
    `PosIf(sim_pass_ev, sim_pass, rst)//TODO modify reset logic
    `PosIf(time_out_ev, time_out, rst)//TODO modify reset logic
    `WithFinish

    always #`HCYCLE clk= ~clk;
    //always #(2*`HCYCLE) clk_cnt = clk_cnt+1;
    string ansi_blue   = "\033[34m";
    string ansi_cyan   = "\033[36m";
    string ansi_green  = "\033[32m";
    string ansi_yellow = "\033[33m";
    string ansi_red    = "\033[31m";
    string ansi_reset  = "\033[0m";
    initial begin
        $fsdbDumpfile({"ValMatrix_tb_", getenv("TEST_CFG"), ".fsdb"});
        $fsdbDumpvars(0,ValMatrix_tb,"+all");
        sim_pass = 0;
        sim_stop = 0;
        time_out = 0;
        clk = 0;
        rst = 0;
        #1 `NicotbInit
        #10
        rst = 0;
        #10
        rst = 1;
        clk_cnt = 0;

        while (clk_cnt < `TIMEOUTCYCLE && sim_stop == 0 && time_out ==0) begin
            @ (posedge clk)
            clk_cnt <= clk_cnt + 1;
        end

        $display({ansi_blue,"==========================================", ansi_reset});
        $display({"[Info] Test case:", ansi_yellow, getenv("TEST_CFG"), ansi_reset});
        if (clk_cnt >= `TIMEOUTCYCLE|| time_out)
            $display({"[Error]", ansi_yellow, " Simulation Timeout.", ansi_reset});
        else if (sim_pass)
            $display({"[Info]", ansi_green, " Congrat! Simulation Passed.", ansi_reset});
        else
            $display({"[Error]", ansi_red, " Simulation Failed.", ansi_reset});
        $display({ansi_blue,"==========================================", ansi_reset});

        `NicotbFinal
        $finish;
    end


    //===================================
    //            Parameters             
    //===================================
    parameter DIM = 3;
    parameter DIM2 = (3+4)*(5+6);


    //===================================
    //              Logics               
    //===================================
    logic signed test_sig;
    logic  happy [3];
    logic [3:0] fuck [4];
    type1 shooshoo [DIM];
    logic  booboo [DIM][7];
    logic [`TM-1:0] papa;

    parameter DIM3 = `D3;

    logic onebit [DIM3][5];


    ValMatrix #(
         .DIM  (DIM)
        ,.DIM2 (DIM2)
        ,.DIM3 (DIM3)
    ) dut (
         .test_sig (test_sig)
        ,.happy    (happy)
        ,.fuck     (fuck)
        ,.shooshoo (shooshoo)
        ,.booboo   (booboo)
        ,.papa     (papa)
        ,.onebit   (onebit)
    );


endmodule

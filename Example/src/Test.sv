
`include "common/Defines.sv"
`include "common/TestRegbk.sv"
`define TM 8

typedef struct packed{
    logic e;
    logic f;
} type2;
typedef enum logic { BOO, PEE} poopee;
typedef struct packed{
    logic a;
    logic b;
    type2 c;
    poopee d;
} type1;
module TestModule 
    //import TestRegbk::*;
    import TestRegbk::REG_ADDR_BW
    ,TestRegbk::REG_BSIZE
    ,TestRegbk::SLV_PAIR;
    import Intr::*;
#(
     localparam ADDR_BW = REG_ADDR_BW
    ,localparam BSIZE = $clog2(REG_BSIZE)
    ,localparam DATA_BW = 2 ** (BSIZE+3)
    ,parameter DIM=3
    ,parameter DIM3 = 7
    ,parameter DIM2 = (3+4)*(5+6)
    ,parameter poopee SUCKY=PEE
)(
    input signed test_sig
    ,output happy [3]
    ,input [3:0] fuck [4]
    ,input type1 shooshoo [DIM] //reged
    ,output booboo [DIM][7]
    ,input [`TM-1:0] papa
    ,inout inout_test
    ,input poopee suck
    ,input logic onebit [DIM3][5]
);
    parameter SHIFT = 3 >>1 ;
    parameter WS = 32;     // size of a vector (similar to CUDA GPU warp)
	     `p_C(WS);
	    `p_C1(WS);
	   `p_C1C(WS);

    import TestRegbk::intr_ctrl; 
endmodule

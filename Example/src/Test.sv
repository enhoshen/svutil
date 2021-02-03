
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
module ValMatrix
    //import P2PRegbk::*;
    import P2PRegbk::REG_ADDR_BW
    ,P2PRegbk::REG_BSIZE
    ,P2PRegbk::SLV_PAIR;
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
    import P2PRegbk::intr_ctrl; 
endmodule

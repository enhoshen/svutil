typedef struct packed{
    logic dval;
    logic inc;
    logic reset;
} LpCtl;
module LoopCounter #(
parameter NDEPTH = 3,
parameter int IDXDW [NDEPTH]= '{3,5,3},
parameter IDXMAXDW = 11,
parameter STARTPOINT = 0
)(
`clk_input,
input  [IDXMAXDW-1:0] i_loopSize [NDEPTH],
output [IDXMAXDW-1:0] o_loopIdx [NDEPTH],
input  LpCtl i_ctl, 
output [NDEPTH-1:0] o_loopEnd
//TODO idx > 1 ? idx output ?
);
    //================
    //parameter
    //================
  
 


    //=================
    //logic
    //=================
    logic [NDEPTH-1:0] loopEnd ;
        assign o_loopEnd = loopEnd;
    logic [IDXMAXDW-1:0] loopIdx_r [NDEPTH], loopIdx_w [NDEPTH];


    `define MSKIDX [i][IDXDW[i]-1:0] 
    genvar i;
    generate
        for ( i=0 ; i<NDEPTH ; ++i)begin 
            assign loopEnd[i] =  loopIdx_r[i] == i_loopSize `MSKIDX || i_loopSize[i] == '0;
            assign o_loopIdx[i] = loopIdx_r[i];
            if ( i==0 ) begin
                always_comb begin
                    loopIdx_w[i]=loopIdx_r[i];
                    if(i_ctl.reset)
                        loopIdx_w `MSKIDX = STARTPOINT;
                    else if (i_ctl.inc)
                        loopIdx_w `MSKIDX = (loopEnd[0])? 1 : loopIdx_r `MSKIDX + 1'b1; 
                    else
                        loopIdx_w `MSKIDX = loopIdx_r `MSKIDX;
                end
            end     
            else begin
                always_comb begin
                    loopIdx_w[i] = loopIdx_r[i];
                    if(i_ctl.reset)
                        loopIdx_w `MSKIDX = 1 ;
                    else if (i_ctl.inc) 
                        loopIdx_w `MSKIDX = (&loopEnd[i:0])? 1 : (&loopEnd[i-1:0])? loopIdx_r `MSKIDX +1'b1 : loopIdx_r `MSKIDX ;  
                    else
                        loopIdx_w `MSKIDX = loopIdx_r `MSKIDX ;   
                end        
            end
        end
    endgenerate

    `ff_rstn
        for ( int j=1 ; j<NDEPTH ; ++j)
            loopIdx_r[j] <= 1;    
        loopIdx_r[0] <= STARTPOINT;
    `ff_cg(i_ctl.dval)
        for ( int j=0 ; j<NDEPTH ; ++j)
            loopIdx_r[j] <= loopIdx_w[j];
    `ff_end

endmodule
module LoopCounterD1 #(
parameter IDXDW = 3,
parameter STARTPOINT = 0
)(
`clk_input,
input  [IDXDW-1:0] i_loopSize, 
output [IDXDW-1:0] o_loopIdx,
input  LpCtl i_ctl, 
output o_loopEnd
//TODO idx > 1 ? idx output ?
);
    //=================
    //logic
    //=================
    logic loopEnd ;
        assign o_loopEnd = loopEnd;
    logic [IDXDW-1:0] loopIdx_r ,loopIdx_w; 


    assign loopEnd =  loopIdx_r == i_loopSize  || i_loopSize == '0;
    assign o_loopIdx = loopIdx_r;
    always_comb begin
        loopIdx_w=loopIdx_r;
        if(i_ctl.reset)
            loopIdx_w = STARTPOINT;
        else if (i_ctl.inc)
            loopIdx_w = (loopEnd)? 1 : loopIdx_r + 1'b1; 
        else
            loopIdx_w = loopIdx_r ;
    end
       
            

    `ff_rstn
        loopIdx_r <= STARTPOINT;
    `ff_cg(i_ctl.dval)
        loopIdx_r <= loopIdx_w;
    `ff_end

endmodule
typedef struct packed{
    logic dval;
    logic inc;
    logic strideCond;
    logic reset;
} LpSSCtl;
module LoopCounterStrideStart #(
parameter IDXDW = 3,
parameter STARTPOINT=0
)(
`clk_input,
input  [IDXDW-1:0] i_loopSize, 
input  [IDXDW-1:0] i_stride,
output [IDXDW-1:0] o_loopIdx,
output [IDXDW-1:0] o_loopStrideIdx,
input  LpSSCtl i_ctl, 
output o_loopEnd
);
    //=================
    //logic
    //=================
    logic loopEnd ;
        assign o_loopEnd = loopEnd;
    logic [IDXDW-1:0] loopIdx_r ,loopIdx_w; 
    logic [IDXDW-1:0] loopStrideIdx_r , loopStrideIdx_w;
    logic [IDXDW-1:0] loopStart_r , loopStart_w;
    logic [IDXDW-1:0] nxtLoopStart;
        assign nxtLoopStart = ( i_stride+loopStart_r > i_loopSize) ? i_stride+loopStart_r-i_loopSize : i_stride+loopStart_r;
        assign o_loopStrideIdx = loopStrideIdx_r; 
    assign loopEnd =  loopIdx_r == i_loopSize  || i_loopSize == '0;
    assign o_loopIdx = loopIdx_r;
    always_comb begin
        loopIdx_w=loopIdx_r;
        loopStart_w = loopStart_r;
        loopStrideIdx_w = loopStrideIdx_r;
        if(i_ctl.reset)
            loopIdx_w = STARTPOINT;
        else if (i_ctl.inc)
            loopIdx_w = (loopEnd)? 1 : loopIdx_r + 1'b1; 
        else
            loopIdx_w = loopIdx_r ;

        if(i_ctl.reset) 
            loopStart_w = STARTPOINT;
        else if(i_ctl.inc && i_ctl.strideCond && loopEnd ) 
            loopStart_w = nxtLoopStart;
        else 
            loopStart_w = loopStart_r;
        
        if(i_ctl.reset)
            loopStrideIdx_w = STARTPOINT;
        else if (i_ctl.strideCond && loopEnd && i_ctl.inc)
            loopStrideIdx_w = nxtLoopStart;
        else if (i_ctl.inc)
            loopStrideIdx_w = (loopStrideIdx_r==i_loopSize)? 1 : loopStrideIdx_r + 1'b1;
        else
            loopStrideIdx_w = loopStrideIdx_r;
    end
       
            

    `ff_rstn
        loopIdx_r <= STARTPOINT;
        loopStart_r <= STARTPOINT;
        loopStrideIdx_r <= STARTPOINT;
    `ff_cg(i_ctl.dval)
        loopIdx_r <= loopIdx_w;
        loopStart_r <= loopStart_w;
        loopStrideIdx_r <= loopStrideIdx_w;
    `ff_end

endmodule

`ifdef Loop
module Loop;
   
    parameter NDEPTH = 3;
    parameter IDXMAXDW = 11;
    //parameter int IDXDW [NDEPTH] = {3,5,3};
    LpCtl i_ctl;
    logic [NDEPTH-1:0] o_loopEnd;
    logic [IDXMAXDW-1:0] i_loopSize [NDEPTH]; 
        assign i_loopSize = {11'd5,11'd0,11'd7};
    `default_Nico_define
LoopCounter #(
.NDEPTH(NDEPTH), .IDXDW( {10'd3,10'd5,10'd3} ), .IDXMAXDW(IDXMAXDW)
) dut(
.*
//`clk_connect,
//.i_loopSize({11'd5,11'd30,11'd7}),
//.i_ctl(i_ctl)
//.o_loopEnd(loopend)
);
`default_Nico_init_block(Loop,10000)
endmodule
`endif

`timescale 1 ns/1 ps
// MEMdefin
import RFCfg::*;
import GenCfg::*;
module RF_2P #(
    parameter WORDWD = 12,
    parameter DWD    = 16,
    parameter AWD    = $clog2(WORDWD),
    parameter SIZE   = 1
)(
`clk_input,
input i_read,
input i_write,
input [AWD-1:0] i_raddr,
input [AWD-1:0] i_waddr,
output logic [DWD-1:0] o_rdata[SIZE], 
input        [DWD-1:0] i_wdata[SIZE]
);
    localparam EMA = 3'b000;

    wire we_n, re_n;
        assign we_n = !i_write;
        assign re_n = !i_read ; 
    logic [AWD-1:0] raddr , waddr;
        assign raddr = i_raddr;
        assign waddr = i_waddr;

    genvar arr;
    generate  
        if (GENMODE == SIM) begin: sim_mode
            logic [DWD-1:0] data_r[WORDWD][SIZE];
            always @(posedge i_clk) begin
                if (i_write) begin
                    if( i_write && i_read && i_waddr == i_raddr)
                        data_r [i_waddr] <= {SIZE{'x}};
                    else
                        data_r [i_waddr] <= i_wdata ;
                end

                if (i_read) begin
                    if (!i_write || i_waddr != i_raddr) 
                        o_rdata <= data_r[i_raddr];
                    else
                        o_rdata <= {SIZE{'x}};
                end
            end
        end 
        else if (GENMODE == SYN) begin: syn_mode
            for ( arr=0 ; arr<SIZE ; ++arr)begin: rf_instance 
                case ({WORDWD,DWD}) 
                    {32'd12,32'd16}: RF_2P_12x16 `RF2Pinstance_arr(RF12x16,arr)
                    {32'd48,32'd16}: RF_2P_48x16 `RF2Pinstance_arr(RF48x16,arr)
                    {32'd64,32'd16}: RF_2P_64x16 `RF2Pinstance_arr(RF64x16,arr)
                    default: initial ErrorRF;
                endcase
            end
        end
        else if (GENMODE == FPGA) begin:fpga_mode
            //TODO
            initial ErrorRF;
        end
        else begin: syn_fail
            initial ErrorRF;
        end
    endgenerate
endmodule
module RF_2P_MSK 
    import RFCfg::*;#(
    parameter WORDWD = 32,
    parameter DWD    = 32,
    parameter WENWD  = 2,
    parameter AWD    = $clog2(WENWD*WORDWD),
    parameter WPSIZE = DWD/WENWD,
    parameter SIZE   = 1
)(
`clk_input,
input DWD_mode i_dwd_mode, 
input i_read,
input i_write,
input [AWD-1:0] i_raddr,
input [AWD-1:0] i_waddr,
output logic [DWD-1:0] o_rdata[SIZE], 
input        [DWD-1:0] i_wdata[SIZE]
);
    localparam EMA = 3'b000;
    localparam RFAWD = $clog2(WORDWD);
    wire we_n, re_n;
        assign we_n = !i_write;
        assign re_n = !i_read ;
    logic [RFAWD-1:0] waddr , raddr;
    logic [WENWD-1:0] wmsk , wmsk_n; 
        assign raddr = (i_dwd_mode == D16)? i_raddr[1+:RFAWD] : i_raddr[0+:RFAWD];
        assign waddr = (i_dwd_mode == D16)? i_waddr[1+:RFAWD] : i_waddr[0+:RFAWD];
        assign wmsk  = (i_dwd_mode == D16)? ( (i_waddr[0])? 2'b01 : 2'b10 ): 2'b11; 
        assign wmsk_n = ~wmsk;
    genvar arr;
    generate  
        if (GENMODE == SIM) begin: sim_mode
            for ( arr=0 ; arr<SIZE ; ++arr)begin: rf_instance 
                case({WORDWD,DWD})
                    {32'd32,32'd32}: RF_2P_32x32 `RF2Pinstance_msk_arr(RF32x32,arr)
                    default: initial ErrorRF;
                endcase 
            end
            /*
            logic [WPSIZE-1:0] data_r [WORDWD][WENWD][SIZE];
            always @(posedge i_clk) begin
                for (int k=0 ; k < WENWD  ; ++k)begin
                    if (i_write && wmsk[k] ) begin
                        for (int j=0 ; j < SIZE   ; ++j)begin
                            if( i_write && i_read && i_waddr == i_raddr)
                                data_r [i_waddr][k][j] <= 'x;
                            else
                                data_r [i_waddr][k][j] <= i_wdata[j][(k*WPSIZE)+:WPSIZE] ;
                        end
                    end
                end

                if (i_read) begin
                    if (!i_write || i_waddr != i_raddr) 
                        `forstart( j , SIZE)
                            `forstart(k,WENWD)
                                o_rdata[j][(k*WPSIZE)+:WPSIZE] <= data_r[i_raddr][k][j];
                            `forend
                        `forend
                    else
                        o_rdata <= {SIZE{'x}};
                end
            end
            */
        end 
        else if (GENMODE == SYN) begin: syn_mode
            for ( arr=0 ; arr<SIZE ; ++arr)begin: rf_instance 
                case ({WORDWD,DWD}) 
                    {32'd32,32'd32}: RF_2P_32x32 `RF2Pinstance_msk_arr(RF32x32,arr)
                    default: initial ErrorRF;
                endcase
            end
            
        end
        else if (GENMODE == FPGA) begin:fpga_mode
            //TODO
            initial ErrorRF;
        end
        else begin: syn_fail
            initial ErrorRF;
        end
    endgenerate
endmodule


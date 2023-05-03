`timescale 1 ns/1 ps
// MEMdefin
import SRAMCfg::*;
import GenCfg::*;
module SRAM_SP#(
    parameter WORDWD = 256,
    parameter DWD    = 16,
    parameter AWD    = $clog2(WORDWD),
    parameter SIZE   = 16
)(
`clk_input,
input SP_rwmode i_rw,
input ce,
input [AWD-1:0] i_addr,
output logic [DWD-1:0] o_rdata[SIZE], 
input        [DWD-1:0] i_wdata[SIZE]
);
    localparam EMA = 3'b000;

    wire ce_n , we_n;
        assign we_n = !(i_rw==WRITE);
        assign ce_n = !ce; 
    logic [AWD-1:0] addr;
        assign addr = i_addr; 
    genvar arr;
    generate  
        if (GENMODE == SIM) begin: sim_mode
            /*
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
            */
            for ( arr=0 ; arr<SIZE ; ++arr)begin: rf_instance 
                case ({WORDWD,DWD}) 
                    {32'd256,32'd16}: SRAM_SP_256x16 `SRAMSPinstance_arr(SRAM256x16,arr)
                    {32'd512,32'd16}: SRAM_SP_512x16 `SRAMSPinstance_arr(SRAM512x16,arr)
                    {32'd1024,32'd32}: SRAM_SP_1024x32 `SRAMSPinstance_arr(SRAM1024x32,arr)
                    {32'd800,32'd32}: SRAM_SP_800x32 `SRAMSPinstance_arr(SRAM800x32,arr)
        
                    default: initial ErrorSRAM;
                endcase
            end 
        end 
        else if (GENMODE == SYN) begin: syn_mode
            for ( arr=0 ; arr<SIZE ; ++arr)begin: rf_instance 
                case ({WORDWD,DWD}) 
                    {32'd256,32'd16}: SRAM_SP_256x16 `SRAMSPinstance_arr(SRAM256x16,arr)
                    {32'd512,32'd16}: SRAM_SP_512x16 `SRAMSPinstance_arr(SRAM512x16,arr)
                    {32'd1024,32'd32}: SRAM_SP_1024x32 `SRAMSPinstance_arr(SRAM1024x32,arr)
                    {32'd800,32'd32}: SRAM_SP_800x32 `SRAMSPinstance_arr(SRAM800x32,arr)

                    default: initial ErrorSRAM;
                endcase
            end
        end
        else if (GENMODE == FPGA) begin:fpga_mode
            //TODO
            initial ErrorSRAM;
        end
        else begin: syn_fail
            initial ErrorSRAM;
        end
    endgenerate
endmodule


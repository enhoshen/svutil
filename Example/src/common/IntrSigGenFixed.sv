// Copyright (C) Ganzin Technology - All Rights Reserved
// ---------------------------
// Unauthorized copying of this file, via any medium is strictly prohibited
// Proprietary and confidential
//
// Contributors
// ---------------------------
// En-Ho Shen <enhoshen@ganzin.com.tw>, 2019

`ifndef __INTRSIGGENFIXED_SV__
`define __INTRSIGGENFIXED_SV__

//pacakges 
`include "Peripheral/common/IntrDefines.sv"

import Intr::*;
module IntrSigGenFixed #(
     parameter intr_trigger_type INTR_TRIG = INTR_PULSE_TRIG
    ,parameter INTR_PULSE_WIDTH = 10 
)(
     input i_clk
    ,input i_rst_n
    ,input i_intr_stat //reged
    ,output o_intr_sig
);
    localparam INTR_PULSE_WIDTH_BW = $clog2(INTR_PULSE_WIDTH);

    
    enum logic [1:0] {IDLE, HOLD, CLR} state_main_r, state_main_w;
    logic intr_clr;
    logic [INTR_PULSE_WIDTH_BW-1:0] cnt_r, cnt_w;

    assign o_intr_sig = state_main_r == HOLD;

    generate
        case (INTR_TRIG)
            INTR_EDGE_TRIG:  assign intr_clr = '1;
            INTR_PULSE_TRIG: assign intr_clr = cnt_r == INTR_PULSE_WIDTH - 1'd1;
            INTR_LEVEL_TRIG: assign intr_clr = !i_intr_stat; 
            default: initial ErrorIntr;
        endcase
    endgenerate

    always_comb begin
        case (state_main_r)
            IDLE: state_main_w = (i_intr_stat)? HOLD : IDLE;
            HOLD: state_main_w = (intr_clr)? ((INTR_TRIG==INTR_LEVEL_TRIG)? IDLE : CLR) : HOLD;
            CLR:  state_main_w = (!i_intr_stat)? IDLE : CLR;
            default: state_main_w = IDLE;
        endcase
    end
    
    always_comb begin
        cnt_w = (state_main_r == IDLE)? '0 : (state_main_w == HOLD)? cnt_r + 1'd1 : cnt_r;
    end
    
    always_ff @(posedge i_clk or negedge i_rst_n) begin
        if (!i_rst_n) state_main_r <= IDLE;
        else state_main_r <= state_main_w;
    end

    always_ff @(posedge i_clk or negedge i_rst_n) begin
        if (!i_rst_n) cnt_r <= '0;
        else if (cnt_r != cnt_w) cnt_r <= cnt_w;
    end
endmodule

`endif // __INTRSIGGENFIXED_SV__

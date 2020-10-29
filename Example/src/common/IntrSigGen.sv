// Copyright (C) Ganzin Technology - All Rights Reserved
// ---------------------------
// Unauthorized copying of this file, via any medium is strictly prohibited
// Proprietary and confidential
//
// Contributors
// ---------------------------
// En-Ho Shen <enhoshen@ganzin.com.tw>, 2019

`ifndef __INTRSIGGEN_SV__
`define __INTRSIGGEN_SV__

//pacakges 
`include "Peripheral/common/IntrDefines.sv"

import Intr::*;
module IntrSigGen #(
     parameter INTR_PULSE_WIDTH_BW = 8
    ,parameter INTR_PULSE_WIDTH_DEFAULT = 10
)(
     input i_clk
    ,input i_rst_n
    ,input intr_trigger_type i_trigger_type
    ,input [INTR_PULSE_WIDTH_BW-1:0] i_pulse_width
    ,input i_intr_stat //reged
    ,output o_intr_sig
);

    enum logic [1:0] {IDLE, HOLD, CLR} state_main_r, state_main_w;
    logic intr_clr;
    logic [INTR_PULSE_WIDTH_BW-1:0] cnt_r, cnt_w;
    logic [INTR_PULSE_WIDTH_BW-1:0] pulse_width;

    assign o_intr_sig = state_main_r == HOLD;
    assign pulse_width = (i_pulse_width=='0)? INTR_PULSE_WIDTH_DEFAULT: i_pulse_width - 1'd1;

    always_comb begin
        case (i_trigger_type)
            INTR_EDGE_TRIG:  assign intr_clr = '1;
            INTR_PULSE_TRIG: assign intr_clr = cnt_r == pulse_width;
            INTR_LEVEL_TRIG: assign intr_clr = !i_intr_stat; 
            default: assign intr_clr = !i_intr_stat;
        endcase
    end 

    always_comb begin
        case (state_main_r)
            IDLE: state_main_w = (i_intr_stat)? HOLD : IDLE;
            HOLD: state_main_w = (intr_clr)? ((i_trigger_type==INTR_LEVEL_TRIG)? IDLE : CLR) : HOLD;
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

`endif // __INTRSIGGEN_SV__

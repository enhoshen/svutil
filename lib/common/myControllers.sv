module RoundRobinForward #(
parameter N = 2
)(
    `clk_input,
    input logic [N-1:0] src_rdys,
    output logic [N-1:0] src_acks,
    `rdyack_output(dst)
);
    //============    
    //logic
    //============
    logic [N-1:0] last_src_r , last_src_w;
    logic dst_rdy_w;
    //============
    //comb
    //============
    always_comb begin
        src_acks[0] = last_src_r[N-1] && src_rdys[0] && ( !dst_rdy || dst_ack );
        last_src_w[N-2:0] = last_src_r[N-1:1] ;
        last_src_w[N-1] = last_src_r[0];
        for(int i = 1 ; i<N ; ++i ) begin
            src_acks[i] = last_src_r[i-1] && src_rdys[i] && ( !dst_rdy || dst_ack );
        end
        dst_rdy_w = |src_rdys || (dst_rdy && !dst_ack);
    end 
    //============
    //sequental
    //============
    `ff_rstn
        dst_rdy <= 1'b0;
        last_src_r <= 1;
    `ff_nocg
        dst_rdy <= dst_rdy_w;
        last_src_r <= last_src_w;
    `ff_end 
endmodule


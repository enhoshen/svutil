package Intr;
    task automatic ErrorIntr;
        begin
            $display("Intr related configuration went wrong" );
            $finish(); 
        end 
    endtask
    typedef enum logic [1:0] {INTR_EDGE_TRIG, INTR_PULSE_TRIG, INTR_LEVEL_TRIG} intr_trigger_type;

endpackage

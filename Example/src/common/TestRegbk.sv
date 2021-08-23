`include "common/IntrDefines.sv"
package TestRegbk;
    import Intr::*;
    parameter REG_ADDR_BW = 6;
    parameter REG_BSIZE = 4;
    parameter REG_BSIZE_BW = $clog2(REG_BSIZE);
    parameter REG_BW = 32;
    parameter INTR_PULSE_WIDTH_BW = 8;
    parameter INTR_PULSE_WIDTH_DEFAULT = 10;

    //====================
    //      regbank
    //====================

    parameter SLV_PAIR_NUM = 8;
    parameter ARR_TEST_NUM= 5;
    parameter ARR_SEL_MINUEND_BW = $clog2(SLV_PAIR_NUM);

    `define T 3
    parameter MACRO = `T;
    enum {   
             SLV_PAIR                         //R/W  //arr
            ,ARR_TEST = SLV_PAIR+SLV_PAIR_NUM //RO //ARR
            ,SLV_MSK = 32                     //R/W  
            ,SYNC_CTRL                        //R/W
            ,STATUS                           //RO
            ,INTR_STAT                        // 
            ,MODE_CTRL        //R/W 
            ,CMT_TEST                         
            ,CMT_TEST2                        //
            ,INTR_MSK                         //R/W
            ,RAW_INTR_STAT                    //WO //ARR
            ,INTR_CTRL                        //R/W
            ,PACKED_ARRAY                     //R/W
            ,CLR_DISABLED                     //RO //test 
            ,DISABLE                          //R/W
            ,WOTEST                           //WO
            // happy group
            ,TEST [5 : 10] =WOTEST+`T   //RW
            ,TESTARRMACRO [`T]                //RW //ARR
            ,TESTARRNUM [4] 
    } regaddr;
    enum {   SLV_PAIR_ARR = SLV_PAIR
            ,ARR_TEST_ARR = ARR_TEST
    } regaddr_arr;

    parameter SLV_PAIR_BW = 5;
    parameter SLV_PAIR_DEFAULT = 0;

    typedef struct packed {
        logic alarm_wakeup_en;
        logic alarm_en;
        logic [5:0] alarm_strobe;
        logic [5:0] sync_strobe;
        logic [2:0] unit_cycle; //W1C
    } mode_ctrl;
    parameter mode_ctrl MODE_CTRL_DEFAULT = {1'b0, 1'b0, 6'd3, 6'd2, 3'b1}; 



    //enum {BUSY, PAUSE, WRITE_DONE, STATUS_RESERVED} STATUS_regfield;
    typedef struct packed{
        logic write_done; //RW
        logic pause; //W1C 
        logic busy;
        // group2
    } status; 
    parameter status STATUS_DEFAULT = {1'b0, 1'b0, 1'b0};
    typedef enum logic [1:0] {
         DD
        // group3
        ,EE
    } gg;

    enum { 
         INTR_DISABLED //RO
        ,INTR_BITCH    //W1C //fuck
        ,INTR_RESERVED 
    } RAW_INTR_STAT_regfield;
    typedef struct packed{
        logic disabled;
        logic bitch;
    } raw_intr_stat;
    parameter raw_intr_stat RAW_INTR_STAT_DEFAULT  = {1'b0}; 
    parameter raw_intr_stat NON_MASKABLE_INTR = {1'b1};
    parameter raw_intr_stat INIT_CLR_INTR     = {1'b1}; 

    enum {  INTR_TYPE, INTR_PULSE_WIDTH=2, INTR_CTRL_RESERVED=2+INTR_PULSE_WIDTH_BW } INTR_CTRL_regfield;
    typedef struct packed{
        logic [INTR_PULSE_WIDTH_BW-1:0] intr_width;
        intr_trigger_type intr_type;
    } intr_ctrl;
    parameter intr_ctrl INTR_CTRL_DEFAULT = { '1, INTR_PULSE_TRIG};

    typedef logic [5:0] [3] packed_array;

    //parameter RAW_INTR_STAT_BW         = ; //TODO

    parameter DISABLE_BW = 1;
    parameter DISABLE_DEFAULT = '0;
    
    parameter FUCK = 8;
    //parameter TEST_DEFAULT [REG_BSIZE] = '{ REG_BSIZE,'{1,2, {FUCK, 2} },5,5,5,'{FUCK,3}};


    `define test(a,b) parameter a = b; 
    `test  (c,300)

endpackage


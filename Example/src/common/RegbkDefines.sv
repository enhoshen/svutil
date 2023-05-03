`include "Peripheral/common/IntrDefines.sv"


package BusAccessorRegbk;
    import Intr::*;
    
    parameter REG_ADDR_BW = 7;
    parameter REG_BSIZE = 1;
    parameter REG_BSIZE_BW = $clog2(REG_BSIZE);
    parameter REG_BW = 8;
    parameter INTR_PULSE_WIDTH_BW = 8;
    parameter INTR_PULSE_WIDTH_DEFAULT = 10;

    //====================
    //      regbank
    //====================

    typedef enum {   
             MODE_CTRL        //R/W 
            ,START_CTRL       //R/W
            ,PAUSE_CTRL       //R/W
            ,STATUS           //RO
            ,CLOCK_CNT        //R/W
            ,ALARM_CLOCK      //R/W
            ,SUBSEC_CNT       //R/W
            ,ALARM_SUBSEC     //R/W
            ,INTR_STAT        //RO 
            ,INTR_MSK         //R/W
            ,RAW_INTR_STAT    //R/W
            ,INTR_CTRL        //R/W
            ,PACKED_ARRAY     //R/W
            ,CLR_ALARM        //RO
            ,CLR_OOB          //RO
            ,CLR_ILL_TIME     //RO
            ,CLR_DISABLED     //RO
            ,DISABLE          //R/W
    } regaddr;

    
    parameter UNIT_CLK_CYCLE_BW = 10;
    typedef enum {UNIT_CYCLE, SYNC_STROBE=UNIT_CLK_CYCLE_BW, ALARM_STROBE=SYNC_STROBE+6,
          ALARM_EN=ALARM_STROBE+6, ALARM_WAKEUP_EN, MODE_CTRL_RESERVED} MODE_CTRL_regfield; //TODO
    typedef struct packed {
        logic alarm_wakeup_en;
        logic alarm_en;
        logic [5:0] alarm_strobe;
        logic [5:0] sync_strobe;
        logic [UNIT_CLK_CYCLE_BW-1:0] unit_cycle;
    } mode_ctrl;
    parameter mode_ctrl MODE_CTRL_DEFAULT = {1'b0, 1'b0, 6'b111111, 6'b0, 10'b0}; 
    // DEFAULT parameter order follows the regfield instead of the struct !!

    typedef enum {BUSY, PAUSE, WRITE_DONE, STATUS_RESERVED} STATUS_regfield;
    typedef struct packed {
        logic write_done;
        logic pause;
        logic busy;
    } status; 
    parameter status STATUS_DEFAULT = {1'b0, 1'b0, 1'b0};
    typedef enum {INTR_OOB, INTR_DISABLED, INTR_RESERVED
    } RAW_INTR_STAT_regfield;
    typedef struct packed {
        logic disabled;
        logic oob;
    } raw_intr_stat;
    parameter raw_intr_stat RAW_INTR_STAT_DEFAULT = { 1'b0, 1'b0, 1'b0}
    parameter raw_intr_stat NON_MASKABLE_INTR = { 1'b1, 1'b1, 1'b1}
    parameter raw_intr_stat INIT_CLR_INTR = { 1'b1, 1'b1, 1'b1}

    typedef enum {INTR_TYPE, INTR_PULSE_WIDTH=2, INTR_CTRL_RESERVED=2+INTR_PULSE_WIDTH_BW} INTR_CTRL_regfield;
    typedef struct packed {
        logic [INTR_PULSE_WIDTH_BW-1:0] intr_width;
        intr_trigger_type               intr_type;
    } intr_ctrl;
    parameter intr_ctrl INTR_CTRL_DEFAULT = {'0, INTR_LEVEL_TRIG};

    typedef logic [5:0][6] packed_array;

    parameter MODE_CTRL_BW            = UNIT_CLK_CYCLE_BW + 6 + 6 + 1 + 1; //TODO
    parameter RAW_INTR_STAT_BW        = 14;
    parameter INTR_STAT_BW            = RAW_INTR_STAT_BW;
    parameter INTR_MSK_BW             = RAW_INTR_STAT_BW;
    parameter INTR_CTRL_BW            = INTR_PULSE_WIDTH_BW+2;
    parameter CLR_OOB_BW              = 1;
    parameter CLR_DISABLED_BW         = 1;
    parameter DISABLE_BW              = 1;
    
    //parameter MODE_CTRL_DEFAULT     = ;
    parameter INTR_STAT_DEFAULT       = '0;
    parameter INTR_MSK_DEFAULT        = '0;
    //parameter RAW_INTR_STAT_DEFAULT = ;
    //parameter INTR_CTRL_DEFAULT     = ;
    parameter CLR_ALARM_DEFAULT       = 1'b0;
    parameter CLR_OOB_DEFAULT         = 1'b0;
    parameter CLR_DISABLED_DEFAULT    = 1'b0;
    parameter DISABLE_DEFAULT         = 1'b0;

endpackage

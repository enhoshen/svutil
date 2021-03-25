import os
import sys
from SVutil.SVparse import *
from SVutil.SVgen import *
from SVutil.SVclass import *
import itertools
import numpy as np


class PRESET:
    """"""

    REQACK_INSTANT = 0
    REQACK_RD_AFTER_ACK = 1
    REQACK_WR_AFTER_ACK = 2
    VALID = 3
    AHB = 4
    APB3 = 5


class PRCL_PRESET:
    REQACK = 0
    VALID = 1
    AHB = 2
    APB3 = 3


class WRDATA_PRESET:
    """
    INSTANT: when transaction occurs (valid,  req && ack etc..), the read/write data is valid
    RD NEXT cycle: write data valid when transaction occurs, and read data valid on the next cycle
                   for reqack protocol, this is the generally the case
    NEXT_CYCLE: write data and read data are valid the next cycle after a transaction occurs
    """

    INSTANT = 0
    RD_NEXT_CYCLE = 1
    NEXT_CYCLE = 2


class DISABLE_PRESET:
    DISABLE_REG = 0
    DISABLE_STATE = 1
    EN_WIRE = 2


class SrcGen(SVgen):
    def __init__(self, session=None):
        super().__init__(session=session)
        self.V_(GBV.VERBOSE)
        self.customlst += ["clk_name", "rst_name"]
        self.userfunclst += []
        self.clk_name = "i_clk"
        self.rst_name = "i_rst_n"

    @SVgen.str
    def port_logic(self, w, reg, bw, tp, dim, io):
        bwstr = "" if bw == 1 else f"[{bw}-1:0] "
        inout = {'i':'input', 'o':'output', 'ro':'input', 'ro':'output'}.get(io)
        return f',{inout} {tp+" "+bwstr:<{w[0]}}{io[0]}_{reg+dim}\n'

    @SVgen.str
    def RegLogicStr(self, w, reg, bw, tp, dim):
        bwstr = "" if bw == 1 else f"[{bw}-1:0] "
        return f'{tp+" "+bwstr:<{w[0]}}{reg+"_r"+dim:<{w[1]}} ,{reg}_w{dim};\n'

    @SVgen.str
    def CombLogicStr(self, w, reg, bw, tp, dim):
        bwstr = "" if bw == 1 else f"[{bw}-1:0] "
        return f'{tp+" "+bwstr:<{w[0]}}{reg+dim:<{w[1]}};\n'

    @SVgen.str
    def SeqCeStr(self, s1, s2, ce=None, ind=None):
        ff_str = (
            f"always_ff @(posedge {self.clk_name} or negedge {self.rst_name}) begin"
        )
        s = f"{ind.b}{ff_str}\n"
        rst_sign = "!" if self.rst_name[-1] == "n" else ""
        s += f"{ind[1]}if ({rst_sign}{self.rst_name}) begin\n"
        for _s in s1:
            s += f"{ind[2]}" + _s + "\n"
        s += f"{ind[1]}end\n"
        if ce is None:
            s += f"{ind[1]}else begin\n"
        else:
            s += f"{ind[1]}else if ({ce}) begin //TODO\n"
        for _s in s2:
            s += f"{ind[2]}" + _s + "\n"
        s += f"{ind[1]}end\n"
        s += f"{ind.b}end\n"
        return s

    # port list
    @SVgen.str
    def ProtocolImportStr(self):
        s = ""
        if self.protocol == PRCL_PRESET.AHB:
            s  = f"import Ahb::*;\n"
            s += f"import AhbWrap::*;\n"
            s += f"import Amba::amba_rwmode;\n"
        if self.protocol == PRCL_PRESET.APB3:
            s  = f"import Apb::*;\n"
            s += f"import ApbWrap::*;\n"
            s += f"import Amba::amba_rwmode;\n"
        return s

    @SVgen.str
    def ProtocolParameterPortStr(self):
        s = ""
        if self.protocol == PRCL_PRESET.AHB:
            s += f" parameter ahb_endian SLVEND = LITTLE_END\n"
            s += f",parameter ahb_wrap_mastend MASTEND = DYNAMIC_END\n"
            s += f",parameter ADDR_BASE = 32'h8000_000\n"
            s += f",parameter ADDR_SIZE = 32'h0800_000\n"
        return s

    @SVgen.str
    def ProtocolDataPortStr(self, addrbw, bw):
        """ addrbw, bw are name to the parameters """
        s = f"// data and address\n"
        if (
            self.protocol is None
            or self.protocol == PRCL_PRESET.REQACK
            or self.protocol == PRCL_PRESET.VALID
        ):
            w = len(bw) + 5 + 7 + 8
            s += f'{",input":<{w}} {self.write_name}\n'
            s += f'{",input ["+addrbw+"-1:0]":<{w}} {self.addr_port_name}\n'
            s += f'{",input ["+bw+"-1:0]":<{w}} {self.wdata_name}\n'
            s += f'{",output logic ["+bw+"-1:0]":<{w}} o_{self.rdata_name}\n'
        if self.protocol == PRCL_PRESET.AHB or self.protocol == PRCL_PRESET.APB3:
            w = len(bw) + 5 + 8
            p = "h" if self.protocol == PRCL_PRESET.AHB else "p"
            s  = f',input  logic {"["+addrbw+"-1:0]":<{w}} i_{p}addr\n'
            s += f',input  logic {"["+bw+"-1:0]":<{w}} i_{p}wdata\n'
            s += f',output logic {"["+bw+"-1:0]":<{w}} o_{p}rdata\n'
        return s

    @SVgen.str
    def ProtocolPortStr(self, bw):
        """ bw are name to the parameters """
        # disable
        s = ""
        if self.disable_style == DISABLE_PRESET.EN_WIRE:
            w = len(bw) + 5 + 7 + 8
            s += f"// enable\n"
            s += f'{",input":<{w}} i_en\n'
        # protocol
        w = len(bw) + 5 + 8
        if self.protocol is None:
            s += f"//TODO protocol\n"
        elif self.protocol == PRCL_PRESET.REQACK:
            w = len(bw) + 5 + 7 + 8
            s += f'{",input":<{w}} i_req\n'
            s += f'{",output logic":<{w}} o_ack\n'
        elif self.protocol == PRCL_PRESET.VALID:
            w = len(bw) + 5 + 7 + 8
            s += f",input  i_val\n"
        elif self.protocol == PRCL_PRESET.AHB:
            s += f',input  {"ahb_wrap_ctrl":<{w+6}} i_hctl\n'
            s += f',output {"ahb_resp":<{w+6}} o_resp\n'
        elif self.protocol == PRCL_PRESET.APB3:
            s += f',input  {"apb3_wrap_ctrl":<{w+6}} i_pctl\n'
            s += f',input  {"apb3_resp":<{w+6}} o_resp\n'
        return s

    # Logic list
    @SVgen.str
    def ProtocolLogicStr(self, w=20):
        # state
        s = ""
        if self.disable_style == DISABLE_PRESET.DISABLE_REG:
            s = f"// state\n"
            s += f"enum logic [1:0] {{MAIN_IDLE, WORK, DISABLED}} state_main_r, state_main_w;\n"
        s += "\n"
        # protocol
        s += "" if self.protocol is None else f"// protocol\n"
        if self.protocol is None:
            s += f"// protocol\n"
        elif self.protocol == PRCL_PRESET.REQACK:
            s += f'{"logic":<{w}} ack_w;\n'
        elif self.protocol == PRCL_PRESET.AHB:
            s += f'{"ahb_hresp":<{w}} resp_r, resp_w;\n'
        elif self.protocol == PRCL_PRESET.APB3:
            s += f'{"apb3_resp":<{w}} resp_r, resp_w;\n'
        return s + "\n"

    @SVgen.str
    def DataAddrLogicStr(self, addrbw, bw):
        s = f"// Data and address\n"
        if self.protocol == PRCL_PRESET.AHB:
            pass
        elif self.protocol == PRCL_PRESET.APB3:
            pass
        ##
        if self.wrdata_style == WRDATA_PRESET.INSTANT:
            if self.protocol == PRCL_PRESET.REQACK:
                s += f"logic [{bw}-1:0] {self.rdata_name}_w;\n"
            pass
        elif self.wrdata_style == WRDATA_PRESET.RD_NEXT_CYCLE:
            s += f"logic [{bw}-1:0] {self.rdata_name}_w;\n"
        elif self.wrdata_style == WRDATA_PRESET.NEXT_CYCLE:
            s += f"logic [{addrbw}-1:0] {self.addr_name}_r;\n"
            s += f"logic [{bw}-1:0] {self.rdata_name}_w;\n"
        return s + "\n"

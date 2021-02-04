import os
import sys
import itertools

import numpy as np
from dataclasses import dataclass, field
from typing import *


from SVutil.SVparse import *
from SVutil.gen.SrcGen import *
from SVutil.SVclass import *

@dataclass
class Customlst:
    protocol: PRCL_PRESET= None
    wrdata_style: WRDATA_PRESET = None
    disable_style: DISABLE_PRESET= None
    omitlogiclst: List[str]= field(default_factory=["VERSION"])

    addr_name: str= "addr"
    addr_port_name: str= f"i_{addr_name}"
    write_name: str= "i_write"
    wdata_name: str= "i_wdata"
    rdata_name: str= "rdata"
    ointr_name: str= "o_intr"
    addr_slice: str= "REG_ADDR_BW-1:REG_BSIZE_BW"
    #"[{self.regbk.regaddrbw_name}-1:{(self.regbk.regbsizebw_name)}]"
    
    write_cond: str = "write_valid"
    read_cond: str = "read_valid"
    cg_cond: str = "ce"
    wo_cg_cond: str = "wo_ce"
    ro_cg_cond: str = "ro_ce"

    arr_sel_subtrahend: str= "arr_sel_subtrahend"
    arr_sel_suf: str= "_sel"
    arr_sel: str= "arr_sel"
    arr_idx_suf: str= "arr_idx"

    output_all: bool= True
    

@SVgen.UserClass
class RegbkGen(SrcGen):
    r"""
    This class saves you effort on reptitive but non-trivial part of your source system verilog code,
    like register bank related logics.
    Common function arguments:
        pkg: the name of the register bank package used to create a SVRegbk object from
            corresponding SVhier object. Default: self.regbk
        ind: the base indentation using Ind(n) object. Default: self.cur_ind
    Function naming suffix conventions:
        Str(self, *arg, ind): return a str of a code block. ind is the text base indentation of type Ind.
        ToClip(self, *arg, ind): try copying text result to xclip and return the text as string.
    """

    def Clip(orig):
        """
        clip decorator, the function must be a member function
        the argument list must ends with ... pkg=None, toclip=True, ind=None
        """

        def new_func(*arg, **kwargs):
            pkg = arg[0].Swap(kwargs.get("pkg"))
            kwargs["pkg"] = pkg
            x = SVgen.Clip(orig)(*arg, **kwargs)
            arg[0].regbk = pkg
            return x

        return new_func

    def __init__(self, ind=Ind(0), session=None):
        super().__init__(session=session)
        self.regbkhier = self.regbk
        self.regbk = SVRegbk(self.regbkhier) if self.regbkhier else None
        self.customlst += [
            "protocol",
            "wrdata_style",
            "addr_port_name",
            "addr_name",
            "write_name",
            "wdata_name",
            "rdata_name",
            "ointr_name",
            "addr_slice",
            "write_cond",
            "read_cond",
            "cg_cond",
            "wo_cg_cond",
            "ro_cg_cond",
            "arr_sel_subtrahend",
            "arr_sel",
            "arr_sel_suf",
            "arr_idx_suf",
            "output_all",
            "omitlogiclst",
        ]
        self.protocol = None
        self.wrdata_style = None
        self.disable_style = None
        self.omitlogiclst = ["VERSION"]

        self.addr_name = "addr"
        self.addr_port_name = f"i_{self.addr_name}"
        self.write_name = "i_write"
        self.wdata_name = "i_wdata"
        self.rdata_name = "rdata"
        self.ointr_name = "o_intr"
        self.addr_slice = (
            f"[{self.regbk.regaddrbw_name}-1:{(self.regbk.regbsizebw_name)}]"
        )
        self.write_cond = "write_valid"
        self.read_cond = "read_valid"
        self.cg_cond = "ce"
        self.wo_cg_cond = "wo_ce"
        self.ro_cg_cond = "ro_ce"

        self.arr_sel_subtrahend = "arr_sel_subtrahend"
        self.arr_sel_suf = "_sel"
        self.arr_sel = "arr_sel"
        self.arr_idx_suf = "arr_idx"

        self.output_all = True


        self.flag_logic_lst = [
            self.write_cond,
            self.read_cond,
            self.cg_cond,
            self.ro_cg_cond,
            self.wo_cg_cond,
        ]
        self.clr_affix = "clr_"

    @SVgen.UserMethod
    def LoadPreset(self, p):
        if p == PRESET.AHB:
            self.protocol = PRCL_PRESET.AHB
            self.wrdata_style = WRDATA_PRESET.NEXT_CYCLE
            self.addr_name = "haddr"
            self.clk_name = "i_ahb_clk"
            self.rst_name = "i_ahb_rst_n"
            self.write_name = "i_hctl.hwrite"
            self.wdata_name = "i_hwdata"
            self.rdata_name = "hrdata"
        if p == PRESET.APB3:
            self.protocol = PRCL_PRESET.APB3
            self.wrdata_style = WRDATA_PRESET.NEXT_CYCLE
            self.addr_name = "paddr"
            self.clk_name = "i_apb_clk"
            self.rst_name = "i_apb_rst_n"
            self.write_name = "i_pctl.pwrite"
            self.wdata_name = "i_pwdata"
            self.rdata_name = "prdata"
        if p == PRESET.REQACK_INSTANT:
            self.protocol = PRCL_PRESET.REQACK
            self.wrdata_style = WRDATA_PRESET.INSTANT
            self.disable_style = DISABLE_PRESET.DISABLE_REG
        if p == PRESET.REQACK_RD_AFTER_ACK:
            self.protocol = PRCL_PRESET.REQACK
            self.wrdata_style = WRDATA_PRESET.RD_NEXT_CYCLE
            self.disable_style = DISABLE_PRESET.DISABLE_REG
        if p == PRESET.REQACK_WR_AFTER_ACK:
            self.protocol = PRCL_PRESET.REQACK
            self.wrdata_style = WRDATA_PRESET.NEXT_CYCLE
            self.disable_style = DISABLE_PRESET.DISABLE_REG
        if p == PRESET.VALID:
            self.protocol = PRCL_PRESET.VALID
            self.wrdata_style = WRDATA_PRESET.INSTANT
            self.disable_style = DISABLE_PRESET.EN_WIRE

    def Reload(self):
        self.session.Reload()
        self.regbkhier = self.session.hiers.get(self.regbkstr)
        self.regbk = SVRegbk(self.regbkhier) if self.regbkhier else None

    def ModBlk(self):
        ind = self.cur_ind.Copy()
        yield ""
        s = "\n"
        s += (
            f"{ind.b}`include "
            + f'"{self.regbkstr}Defines.sv" // Please manually modify the path\n\n'
        )
        if self.regbk.raw_intr_stat:
            s += f"{ind.b}// submodules\n"
            s += f'{ind.b}`include "Peripheral/common/IntrSigGen.sv"\n\n'
        s += f"{ind.b}module {self.regbkstr}\n"
        s += f"{ind[1]}import {self.regbkstr}::*;\n"
        s += self.ProtocolImportStr(ind=ind + 1)
        s += f"{ind.b}#(\n"
        s += self.ProtocolParameterPortStr(ind=ind + 1)
        s += f"{ind.b})(\n"
        s += f"{ind[1]} input  {self.clk_name}\n"
        s += f"{ind[1]},input  {self.rst_name}\n"
        s += self.ProtocolPortStr(self.regbk.regbw_name, ind=ind + 1)
        s += self.ProtocolDataPortStr(
            self.regbk.regaddrbw_name, self.regbk.regbw_name, ind=ind + 1
        )
        w = len(self.regbk.regbw_name) + 5 + 8
        if self.regbk.raw_intr_stat:
            s += f"{ind[1]}// interrupt\n"
            s += (
                f'{ind[1]}{",output "+self.regbk.regintr_name:<{w}} {self.ointr_name}\n'
            )
        if self.output_all:
            s += self.output_all_register_block(ind=ind+1)
        s += f"{ind.b});\n"
        yield s
        yield ""
        s = "\n" + ind.b + "endmodule"
        yield s

    @SVgen.Str
    def LogicStr(self, w, reg, bw, tp, arr=None, dim=None, comb=None, ind=None):
        if arr and arr != "":
            dim = f" [{reg.upper()}{self.regbk.arr_num_suf}]"
        else:
            dim = "" if dim is None else dim
        if comb:
            return self.CombLogicStr(w, reg, bw, tp, dim, ind=ind)
        else:
            return self.RegLogicStr(w, reg, bw, tp, dim, ind=ind)

    def rdata_basic_string(self, reg, comb, const):
        pad = f"{self.regbk.regbw_name}-{reg}{self.regbk.bw_suf}"
        pad = "{{" + f"{pad}" + "{1'b0}}"
        logic = f"{reg.lower()}" if comb else f"{reg.lower()}_r"
        logic = "" if const else logic
        sel = f"[{self.arr_sel}[{reg.upper()}_NUM_BW-1:0]]"
        const_cmt = f'{"//TODO" if const else ""}'
        return pad, logic, sel, const_cmt

    @SVgen.Str
    def rdata_vector_comb(self, reg, _slice, w, rw=None, comb=False, const=False, ind=None):
        # TODO slice dependent, now it only pad the MSB and it's usually the case
        if rw and rw == "WO":
            return ""
        if (
            self.wrdata_style == WRDATA_PRESET.INSTANT
            and self.protocol == PRCL_PRESET.VALID
        ):
            s = f"{ind.b}{reg:<{w[0]}}: o_{self.rdata_name} = "
        else:
            s = f"{ind.b}{reg:<{w[0]}}: {self.rdata_name}_w = "
        pad, logic, sel, const_cmt = self.rdata_basic_string(reg, comb, const)
        # concatenate style
        #s += f'{pad:<{w[1]}} ,{logic}}};{const_cmt}\n'
        s += f"{self.regbk.regbw_name}'({logic});{const_cmt}\n"
        # casting style
        return s


    @SVgen.Str
    def rdata_arr_comb(self, reg, ifelse, w, rw=None, comb=False, const=False, ind=None):
        if rw and rw == "WO":
            return ""
        addr_r = ""
        s = f'{ind.b}{ifelse}({reg.lower()}{self.arr_sel_suf}) begin\n'
        if (
            self.wrdata_style == WRDATA_PRESET.INSTANT
            and self.protocol == PRCL_PRESET.VALID
        ):
            s += f"{ind[1]}o_{self.rdata_name} = "
        else:
            s += f"{ind[1]}{self.rdata_name}_w = "
        pad, logic, sel, const_cmt = self.rdata_basic_string(reg, comb, const)
        # concatenate style
        #s += f'{pad:<{w[1]}} ,{logic}{sel}}};{const_cmt}\n'
        # casting style 
        s += f"{self.regbk.regbw_name}'({logic}{sel});{const_cmt}\n"
        s += f"{ind.b}end\n"
        return s
    @SVgen.Str
    def rdata_arr_slice_bw (self, reg, ind=None):
        """
        """
        s = f"{ind.b}localparam {reg.upper()}_NUM_BW = $clog2({reg.upper()}_NUM);\n"
        return s
    
    @SVgen.Str
    def rdata_arr_slice_param_block (self, arr_reg, ind=None):
        s = f"{ind.b}// rdata array selection slice bw\n"
        for v in arr_reg:
            s += self.rdata_arr_slice_bw (v[0].name, ind=ind)
        return s+'\n'


    @SVgen.Str
    def RdataArrIdxLogic(self, reg, ind=None):
        """deprecated"""
        s = f"{ind.b}logic [$clog2({reg.upper()}_NUM)-1:0] {reg.lower()}_{self.arr_idx_suf};\n"
        return s

    @SVgen.Str
    def RdataArrIdxComb(self, reg, ind=None):
        """deprecated"""
        s = f"{ind.b}assign {reg.lower()}_{self.arr_idx_suf} = {self.addr_port_name}{self.addr_slice}-{reg};\n"
        return s

    @SVgen.Str
    def rdata_sel_subtrahend_comb(self, reg, ifelse, ind=None):
        s = f"{ind.b}{ifelse}({reg.lower()}{self.arr_sel_suf}) begin\n"
        s += f"{ind[1]}{self.arr_sel_subtrahend} = {reg};\n" 
        s += f"{ind.b}end\n"
        return s

    @SVgen.Str
    def rdata_sel_subtrahend_comb_block(self, arr_reg, ind=None):
        s = f"{ind.b}assign {self.arr_sel} = {self.addr_port_name}{self.addr_slice}-{self.arr_sel_subtrahend};\n"
        s += f"{ind.b}always_comb begin\n"
        ifelse_dic = {0:'unique if', len(arr_reg)-1:'else'}
        for i,v in enumerate(arr_reg):
            ifelse = ifelse_dic.get(i, 'else if')
            s += self.rdata_sel_subtrahend_comb(v[0].name, ifelse, ind=ind+1)
        s += f"{ind.b}end\n"
        return s

    @SVgen.Str
    def rdata_address_condition_comb(self, reg, ind=None):
        s = f'{ind.b}assign {reg.lower()}{self.arr_sel_suf} = '
        s += f'{self.addr_port_name}{self.addr_slice} >= {reg}\n'
        s += f'{ind[1]}&& {self.addr_port_name}{self.addr_slice} < {reg}+{reg}{self.regbk.arr_num_suf};\n'
        return s

    @SVgen.Str
    def WdataSeqStr(self, reg, _slice, rw=None, dim=None, ind=None):
        # TODO slice dependent, now it only pad the MSB and it's usually the case
        disable_reg = False
        if self.disable_style == DISABLE_PRESET.DISABLE_REG and reg == "DISABLE":
            disable_reg = True

        dim = "" if not dim else f"[{dim}]"
        rstedge = "negedge" if self.rst_name[-2:] == "_n" else "posedge"
        s = f"{ind.b}always_ff @(posedge {self.clk_name} or {rstedge} {self.rst_name}) begin\n"
        s += f'{ind[1]}if ({"!" if self.rst_name[-2:] == "_n" else ""}{self.rst_name}) '
        s += f"{reg.lower()}_r{dim} <= {reg}{self.regbk.default_suf};"
        s += (
            "\n"
            if dim == ""
            else "//TODO do indexing if the default parameter is an array\n"
        )
        # s += f'{ind[1]}end\n'
        addr = (
            self.addr_port_name
            if self.wrdata_style != WRDATA_PRESET.NEXT_CYCLE
            else self.addr_name + "_r"
        )

        cg_cond = f"{self.cg_cond} && " if not disable_reg else ""
        if rw and rw == "RO":
            s += f"{ind[1]}else if ({self.ro_cg_cond} && ({reg.lower()}_r{dim} != {reg.lower()}_w{dim})) "
        elif rw and rw == "WO":
            s += f"{ind[1]}else if ({self.wo_cg_cond} && ({reg.lower()}_r{dim} != {reg.lower()}_w{dim})) "
        else:
            s += f"{ind[1]}//else if ({cg_cond}{addr}{self.addr_slice} == {reg}) \n"
            s += f"{ind[1]}else if ({cg_cond}({reg.lower()}_r{dim} != {reg.lower()}_w{dim})) "
        s += f"{reg.lower()}_r{dim} <= {reg.lower()}_w{dim};\n"
        s += f"{ind.b}end\n"
        return s

    @SVgen.Str
    def WdataCombStr(self, reg, _slice, rw=None, dim=None, comb=None, ind=None):
        # TODO slice dependent, now it only pad the MSB and it's usually the case
        disable_reg = False
        if self.disable_style == DISABLE_PRESET.DISABLE_REG and reg == "DISABLE":
            disable_reg = True

        dim = "" if not dim else dim
        s = f"{ind.b}always_comb begin\n"
        addr = (
            self.addr_port_name
            if self.wrdata_style != WRDATA_PRESET.NEXT_CYCLE
            else self.addr_name + "_r"
        )
        if rw and rw == "RO":
            if self.clr_affix.upper() in reg:
                s += f"{ind[1]}if ({self.read_cond} && {addr}{self.addr_slice} == {reg}) "
                s += f"{reg.lower()}_w = 1;\n"
                s += f"{ind[1]}else {reg.lower()}_w = '0;//TODO\n"
                s += f"{ind[1]}//TODO\n{ind.b}end\n"
            else:
                if comb:
                    s += f"{ind[1]}{reg.lower()} = ;//TODO\n"
                    s += f"{ind.b}end\n"
                else:
                    s += f"{ind[1]}{reg.lower()}_w = {reg.lower()}_r;\n"
                    s += f"{ind[1]}//TODO\n{ind.b}end\n"
        else:
            s += f"{ind[1]}if ({self.write_cond} && {addr}{self.addr_slice} == {reg}) begin\n"
            if comb:
                s += f"{ind[2]}{reg.lower()} = {self.wdata_name}[{reg}{self.regbk.bw_suf}-1:0];\n"
            else:
                s += f"{ind[2]}{reg.lower()}_w = {self.wdata_name}[{reg}{self.regbk.bw_suf}-1:0];\n"
            s += f"{ind[1]}end \n"
            s += f"{ind[1]}else begin\n"
            if self.regbk.regintr_name.upper() in reg.upper():
                s += f"{ind[2]}\n"
                s += self.IntrCombToClip(reg, pkg=self.regbk, toclip=False, ind=ind + 2)
            else:
                if comb:
                    s += f"{ind[2]}{reg.lower()} = ;//TODO\n"
                else:
                    if disable_reg:
                        s += f"{ind[2]}if (clr_disable_r && state_main_r == DISABLED) disable_w = '0;\n"
                        s += f"{ind[2]}else disable_w = disable_r;\n"
                    else:
                        s += f"{ind[2]}{reg.lower()}_w = {reg.lower()}_r;\n"
                        s += f"{ind[2]}//TODO\n"
            s += f"{ind[1]}end\n{ind.b}end\n"
        return s

    @SVgen.Str
    def WdataCombArrStr(self, reg, rw=None, dim=None, comb=None, ind=None):
        # TODO slice dependent, now it only pad the MSB and it's usually the case
        dim = "" if not dim else dim
        s = f"{ind.b}always_comb begin\n"
        addr = (
            self.addr_port_name
            if self.wrdata_style != WRDATA_PRESET.NEXT_CYCLE
            else self.addr_name + "_r"
        )
        if rw and rw == "RO":
            if self.clr_affix.upper() in reg:
                s += f"{ind[1]}if ({self.read_cond} && (({addr}{self.addr_slice} - {reg}) == {dim})) "
                s += f"{reg.lower()}_w[{dim}] = 1;\n"
                s += f"{ind[1]}else {reg.lower()}_w[{dim}] = '0;//TODO\n"
                s += f"{ind[1]}//TODO\n{ind.b}end\n"
            else:
                if comb:
                    s += f"{ind[1]}{reg.lower()}[{dim}] = ;//TODO\n"
                    s += f"{ind.b}end\n"
                else:
                    s += f"{ind[1]}{reg.lower()}_w[{dim}] = {reg.lower()}_r[{dim}];\n"
                    s += f"{ind[1]}//TODO\n{ind.b}end\n"
        else:
            s += f"{ind[1]}if ({self.write_cond} && ({addr}{self.addr_slice} - {reg} == {dim})) begin\n"
            if comb:
                s += f"{ind[2]}{reg.lower()}[{dim}] = {self.wdata_name}[{reg}{self.regbk.bw_suf}-1:0];\n"  # TODO
            else:
                s += f"{ind[2]}{reg.lower()}_w[{dim}] = {self.wdata_name}[{reg}{self.regbk.bw_suf}-1:0];\n"  # TODO
            s += f"{ind[1]}end \n"
            s += f"{ind[1]}else begin\n"
            if self.regbk.regintr_name.upper() in reg.upper():
                s += f"{ind[2]}\n"
                s += self.IntrCombToClip(
                    reg, pkg=self.regbk, dim=dim, toclip=False, ind=ind + 2
                )
            else:
                if comb:
                    s += f"{ind[2]}{reg.lower()}[{dim}] = ;//TODO\n"
                else:
                    s += f"{ind[2]}{reg.lower()}_w[{dim}] = {reg.lower()}_r[{dim}];\n"
                    s += f"{ind[2]}//TODO\n"
            s += f"{ind[1]}end\n{ind.b}end\n"
        return s
    def reg_format_width(self):
        """String format width tuple
        """
        w = [0,0]
        for reg in self.regbk.addrs.enumls:
            bw, tp = self.get_tpbw(reg)
            width, rw, arr, *_ = self.regbk.GetAddrCmt(reg.name)
            bwstr = "" if bw == 1 else f"[{bw}-1:0] "
            w[0] = max(w[0], len(f'{tp+" "+bwstr}'))
            dim = "" if arr == "" else " [" + reg.name + self.regbk.arr_num_suf + "]"
            w[1] = max(w[1], len(reg.name + dim) + 2)
        return w
    @SVgen.Str
    def assign_output_all_block (self, ind=None):
        s = f"{ind.b}// direct control register to output\n"
        for reg in self.regbk.addrs.enumls:
            s += f"{ind.b} assign r_{reg.name.lower()} = {reg.name.lower()}_r;\n"
        return s+'\n'

    @SVgen.Str
    def output_all_register_block (self, ind=None):
        """
        """
        w = self.reg_format_width()
        s = f'{ind.b}// control register output\n'
        for reg in self.regbk.addrs.enumls:
            bw, tp = self.get_tpbw(reg)
            width, rw, arr, omit, comb, *_ = self.regbk.GetAddrCmt(reg.name)
            if reg.name in self.omitlogiclst or omit:
                pass
            else:
                dim = ""
                if arr and arr != "":
                    dim = f" [{reg.name.upper()}{self.regbk.arr_num_suf}]"
                s += self.port_logic(w, reg.name.lower(), bw, tp, dim, 'ro',ind=ind)
        return s

    @SVgen.Str
    def control_reg_logic_block(self, ind=None):
        """Control register logic
        Parameters
            w: width tuple
            ind: current indent object
        """
        s = f"{ind.b}// control register\n"
        w = self.reg_format_width()
        for reg in self.regbk.addrs.enumls:
            bw, tp = self.get_tpbw(reg)
            width, rw, arr, omit, comb, *_ = self.regbk.GetAddrCmt(reg.name)
            if reg.name in self.omitlogiclst or omit:
                pass
            else:
                s += self.LogicStr( w, reg.name.lower(), bw, tp, arr=arr, comb=comb, ind=ind)
        s += "\n"
        return s
    @SVgen.Str
    def rdata_address_condition_logic_block(self, ind=None):
        """deprecated"""
        s = f"{ind.b}// read data address selection condtion\n"
        for reg in self.regbk.addrs.enumls:
            bw, tp = self.get_tpbw(reg)
            width, rw, arr, omit, comb, *_ = self.regbk.GetAddrCmt(reg.name)
            if reg.name in self.omitlogiclst or omit:
                pass
            else:
                if arr:
                    s += self.LogicStr(
                        (0,0), reg.name.lower()+self.arr_sel_suf, 1, 'logic', arr=None, comb=True, ind=ind
                    )
        s += "\n"
        return s

    @SVgen.Str
    def rdata_arr_sel_logic_block(self, ind=None):
        """
        """
        s = f"{ind.b}// read data address selection\n"
        s += self.LogicStr(
            (0,0), self.arr_sel,
            bw = self.regbk.regaddrbw_name,
            tp = 'logic',
            arr=None,
            comb=True,
            ind=ind
        )
        s += self.LogicStr(
            (0,0), self.arr_sel_subtrahend,
            bw = self.arr_sel_subtrahend.upper()+'_BW',
            tp = 'logic',
            arr=None,
            comb=True,
            ind=ind
        )
        s += "\n"
        return s

    @SVgen.Str
    def IntrCombStr(self, intr_logic, intr_field, dim=None, ind=None):
        dim = "" if dim is None else f"[{dim}]"
        s = f"{ind.b}if ({self.clr_affix}{intr_logic}_r{dim}) {self.regbk.regintr_name}_w{dim}.{intr_logic} = '0;\n"
        s += f"{ind.b}else begin\n"
        s += f"{ind[1]}{self.regbk.regintr_name}_w{dim}.{intr_logic} = {self.regbk.regintr_name}_r{dim}.{intr_logic};//TODO\n"
        s += f"{ind.b}end\n"
        return s

    @SVgen.Str
    def IntrSigGenStr(self, ind=None):
        s = "\n"
        s += f"{ind.b}// interrupt\n"
        s += f"{ind.b}genvar gen;\n"
        s += f"{ind.b}generate \n"
        s += f"{ind[1]}for (gen = 0 ; gen < RAW_INTR_STAT_BW ; ++gen) begin: intr_sig\n"
        s += f"{ind[2]}IntrSigGen #(\n"
        s += f"{ind[3]}.INTR_PULSE_WIDTH_BW (8) \n"
        s += f"{ind[2]}) u_intr (\n"
        s += f"{ind[3]} .i_clk          (i_clk)\n"
        s += f"{ind[3]},.i_rst_n        (i_rst_n)\n"
        s += f"{ind[3]},.i_trigger_type (intr_ctrl_r.intr_type)\n"
        s += f"{ind[3]},.i_pulse_width  (intr_ctrl_r.intr_width)\n"
        s += f"{ind[3]},.i_intr_stat    (intr_stat_r[gen])\n"
        s += f"{ind[3]},.o_intr_sig     (o_intr[gen])\n"
        s += f"{ind[2]});\n"
        s += f"{ind[1]}end\n"
        s += f"{ind.b}endgenerate\n"
        return s + "\n"

    @SVgen.Str
    def WRCondLogicStr(self, ind=None):
        s = ""
        if self.protocol is None:
            s = f"{ind.b}//TODO\n"
        if self.protocol == PRCL_PRESET.REQACK:
            if self.wrdata_style == WRDATA_PRESET.NEXT_CYCLE:
                s += f"{ind.b}logic reqNack_r;\n"
                s += f"{ind.b}logic write_r;\n"
            ##
        if self.protocol == PRCL_PRESET.VALID:
            s += f"{ind.b}//TODO\n"
        if self.protocol == PRCL_PRESET.AHB:
            s += f"{ind.b}//TODO\n"
        if self.protocol == PRCL_PRESET.APB3:
            s += f"{ind.b}//TODO\n"
        return s

    def get_tpbw(self, reg):
        tp = self.regbk.GetType(reg.name.lower())
        bw = self.regbk.GetBWStr(reg.name)
        try:
            bw = int(bw)
        except:
            pass
        bw = reg.name + self.regbk.bw_suf if not bw == 1 else 1
        bw = 1 if tp else bw
        tp = reg.name.lower() if tp else "logic"
        return bw, tp

    @SVgen.UserMethod
    @Clip
    def LogicToClip(self, pkg=None, toclip=True, ind=None):
        w = [0, 0]
        s = ""

        s += self.ProtocolLogicStr(ind=ind)
        s += self.DataAddrLogicStr(
            self.regbk.regaddrbw_name, self.regbk.regbw_name, ind=ind
        )

        s += self.control_reg_logic_block(ind=ind)

        s += self.rdata_address_condition_logic_block(ind=ind)

        s += self.rdata_arr_sel_logic_block(ind=ind)

        s += f"{ind.b}// interrupt clear\n"
        intr = self.regbk.raw_intr_stat
        if not self.regbk.raw_intr_stat:
            self.print("interrupt struct not specified")
        else:
            width, rw, arr, omit, comb, *_ = self.regbk.GetAddrCmt(
                self.regbk.regintr_name.upper()
            )
            w[0] = 0
            for intr in self.regbk.raw_intr_stat:
                w[1] = max(w[1], len(self.clr_affix + intr.name) + 2)
            for intr in self.regbk.raw_intr_stat:
                if (
                    not self.clr_affix.upper() + intr.name.upper()
                    in self.regbk.regaddrsdict
                ):
                    if arr:
                        dim = f" [{self.regbk.regintr_name.upper()}{self.regbk.arr_num_suf}]"
                    else:
                        dim = ""
                    s += self.LogicStr(
                        w,
                        self.clr_affix + intr.name.lower(),
                        1,
                        "logic",
                        dim=dim,
                        ind=ind,
                    )
            s += "\n"

        s += f"{ind.b}// flags\n"
        for l in self.flag_logic_lst:
            s += f"{ind.b}logic {l};\n"

        s += f"{ind.b}//\n"
        s += self.WRCondLogicStr(ind=ind)

        return s

    @SVgen.UserMethod
    @Clip
    def RdataToClip(self, pkg=None, toclip=True, ind=None):
        r"""
        Help building register bank read data part of combinational logics.
        Follow specific coding style in your register bank description package, the function generate
        logics based on the regaddr enum list.
        """
        w = [0, 0]
        s = ""
        arr_reg = []
        nonarr_reg = []
        for i in self.regbk.addrs.enumls:
            w[0] = max(w[0], len(i.name))
            w[1] = max(
                w[1], len(self.regbk.regbw_name + i.name + self.regbk.bw_suf) + 10
            )
            width, rw, arr, omit, comb, *_ = self.regbk.GetAddrCmt(i.name)
            if arr != "":
                arr_reg.append((i, width, rw, arr, omit, comb))
            else:
                nonarr_reg.append((i, width, rw, arr, omit, comb))

        if self.output_all:
            s += self.assign_output_all_block(ind=ind)

        if arr_reg != []:
            s += f"{ind.b}// array register read data index\n"
            #for i in arr_reg:
            #    s += self.RdataArrIdxLogic(i[0].name, ind=ind)
            #for i in arr_reg:
            #    s += self.RdataArrIdxComb(i[0].name, ind=ind)
            for i in arr_reg:
                s += self.rdata_address_condition_comb(i[0].name, ind=ind)
            s += f"\n"
            s += self.rdata_arr_slice_param_block(arr_reg, ind=ind)
            s += self.rdata_sel_subtrahend_comb_block(arr_reg, ind=ind)

            s += f"\n"


        s += f"\n"
        s += f"{ind.b}always_comb begin\n"
        rdata_dst = (
            f"o_{self.rdata_name}"
            if self.wrdata_style == WRDATA_PRESET.INSTANT
            and self.protocol != PRCL_PRESET.REQACK
            else f"{self.rdata_name}_w"
        )
        if self.disable_style == DISABLE_PRESET.DISABLE_REG:
            s += f"{ind[1]}if (state_main_r == DISABLED) begin\n"
            s += f"{ind[2]}{rdata_dst} = ({self.read_cond} && {self.addr_port_name}{self.addr_slice} == CLR_DISABLED)? 1 : '0;\n"
        elif self.disable_style == DISABLE_PRESET.EN_WIRE:
            s += f"{ind[1]}if (!i_en) begin\n"
            s += f"{ind[2]}{rdata_dst} = '0;\n"
        else:
            s += f"{ind[1]}if () begin //TODO Disabled default read value\n"
            s += f"{ind[2]}{rdata_dst} = '0;\n"

        s += f"{ind[1]}end\n"
        s += f"{ind[1]}else if ({self.read_cond}) begin\n"
        # array registers
        for i, (reg, width, rw, arr, omit, comb) in enumerate(arr_reg):
            reg = reg.name
            const = True if reg in self.omitlogiclst or omit else False
            if i == 0:
                s += self.rdata_arr_comb(
                    reg, "unique if", w, rw, comb=comb, const=const, ind=ind + 2
                )
            else:
                s += self.rdata_arr_comb(
                    reg, "else if", w, rw, comb=comb, const=const, ind=ind + 2
                )

        # non-array registers
        case_ind = 2 if len(arr_reg) == 0 else 3
        s += f"{ind[2]}else begin\n" if len(arr_reg) != 0 else ""
        s += f"{ind[case_ind]}case ({self.addr_port_name}{self.addr_slice})\n"
        for reg, width, rw, arr, omit, comb in nonarr_reg:
            _slice = self.regbk.regslices.get(reg.name)
            reg = reg.name
            const = True if reg in self.omitlogiclst or omit else False
            s += self.rdata_vector_comb(
                reg, _slice, w, rw, comb=comb, const=const, ind=ind + case_ind + 1
            )
        s += f"{ind[case_ind+1]}default: {self.rdata_name}_w = '0;\n"
        s += f"{ind[case_ind]}endcase\n"
        s += f"{ind[2]}end\n" if len(arr_reg) != 0 else ""

        # default
        if (
            self.wrdata_style == WRDATA_PRESET.INSTANT
            and self.protocol == PRCL_PRESET.VALID
        ):
            s += f"{ind[1]}end\n"
            s += f"{ind[1]}else o_{self.rdata_name} = '0;\n"
            s += f"{ind.b}end\n\n"
        else:
            s += f"{ind[1]}end\n"
            s += f"{ind[1]}else {self.rdata_name}_w = o_{self.rdata_name};\n"
            s += f"{ind.b}end\n\n"
            s1 = [f"o_{self.rdata_name} <= '0;"]
            s2 = [f"o_{self.rdata_name} <= {self.rdata_name}_w;"]
            s += self.SeqCeStr(s1, s2, ce=self.read_cond, ind=ind)
        return s

    @SVgen.UserMethod
    @Clip
    def WdataToClip(self, pkg=None, toclip=True, ind=None):
        r"""
        Help building register bank write data part of both combinational and sequential part logics.
        Follow specific coding style in your register bank description package, the function generate
        logics based on the regaddr enum list.
        """
        s = ""
        w = 30
        gen = "arrgen"
        s += f'{ind.b}//{"Array GenVar":=^{w}}\n'
        s += f"{ind.b}genvar {gen};\n\n"
        for reg in self.regbk.addrs.enumls:
            width, rw, arr, omit, comb, *_ = self.regbk.GetAddrCmt(reg.name)
            if reg.name in self.omitlogiclst or omit:
                continue
            _slice = self.regbk.regslices.get(reg.name)
            _s = "reg " if not arr else "reg array "
            s += f"{ind.b}//{_s+reg.name:=^{w}}\n"
            if reg.name == "DISABLE":
                s += f"{ind.b}//TODO Be careful of DISABLE clock enable condition\n"
            if arr != "":
                dim = f"{gen}"
                s += f"{ind.b}generate\n"
                s += f"{ind[1]}for ({gen} = 0; {gen} < {reg.name}{self.regbk.arr_num_suf}; ++{gen}) begin: arr_{reg.name.lower()}\n"
                s += self.WdataCombArrStr(reg.name, rw, dim=dim, comb=comb, ind=ind + 2)
                if not comb:
                    s += self.WdataSeqStr(reg.name, _slice, rw, dim, ind=ind + 2)
                s += f"{ind[1]}end\n"
                s += f"{ind.b}endgenerate\n\n"
            else:
                s += self.WdataCombStr(reg.name, _slice, rw, comb=comb, ind=ind)
                if not comb:
                    s += self.WdataSeqStr(reg.name, _slice, rw, ind=ind) + "\n"
        return s

    @SVgen.UserMethod
    @Clip
    def IntrCombToClip(self, reg, dim=None, pkg=None, toclip=True, ind=None):
        r"""
        Help build clear register read part of interrupts combinational logics.
        """
        s = ""
        w = 30
        for intr, field in zip(
            self.regbk.GetType(reg.lower()),
            self.regbk.regfields[self.regbk.regintr_name.upper()].enumls,
        ):
            s += self.IntrCombStr(intr.name, field.name, dim=dim, ind=ind) + "\n"
        return s

    @SVgen.UserMethod
    @SVgen.Clip
    def CombToClip(self, pkg=None, toclip=True, ind=None):
        """ Build basic combinational part including flags, states ... etc."""
        s = ""
        #
        if self.protocol is None:
            s = f"\n"
        if self.protocol == PRCL_PRESET.REQACK:
            s += self.ReqAckCombStr(ind=ind)
        if self.protocol == PRCL_PRESET.VALID:
            if self.wrdata_style == WRDATA_PRESET.INSTANT:
                pass
        if self.protocol == PRCL_PRESET.AHB:
            s = f"{ind.b}assign {self.write_cond} = ;\n"  # TODO
            s += f"{ind.b}assign {self.read_cond} = i_req && !{self.write_name} && !o_ack;\n"  # TODO
        if self.protocol == PRCL_PRESET.APB3:
            s = f"{ind.b}assign {self.write_cond} = i_pctl.psel && i_pctl.penable && i_pctl.pwrite == WRITE && !o_resp.o_pslverr && o_resp.o_pready;\n"
            s += f"{ind.b}assign {self.read_cond} = i_pctl.psel && !i_pctl.penable && !o_resp.o_pslverr;\n"
        #
        if self.regbk.raw_intr_stat:
            s += self.IntrSigGenStr(ind=ind)
        return s

    @SVgen.Str
    def ReqAckCombStr(self, ind=None):
        s = ""
        if self.wrdata_style == WRDATA_PRESET.INSTANT:
            s += f"{ind.b}assign {self.write_cond} = i_req && o_ack && {self.write_name};\n"
            s += f"{ind.b}assign {self.read_cond} = i_req && !{self.write_name} && !o_ack;\n"
            s += f"{ind.b}assign ack_w = (!o_ack)? i_req : '0; // delayed for reged read data\n"
        elif self.wrdata_style == WRDATA_PRESET.RD_NEXT_CYCLE:
            s += f"{ind.b}assign {self.write_cond} = i_req && o_ack && {self.write_name};\n"
            s += f"{ind.b}assign {self.read_cond} = i_req && o_ack && !{self.write_name};\n"
            s += f"{ind.b}assign o_ack = i_req; //TODO handle stall condition\n"
        elif self.wrdata_style == WRDATA_PRESET.NEXT_CYCLE:
            s += f"{ind.b}assign {self.write_cond} = reqNack_r && write_r;\n"
            s += f"{ind.b}assign {self.read_cond} = i_req && o_ack && !{self.write_name};\n"
            s += f"{ind.b}assign o_ack = i_req; //TODO handle stall condition\n"
        s += f"{ind.b}\n"
        ##
        s += f"{ind.b}assign {self.ro_cg_cond} = 1'b1;\n"
        if self.disable_style is None:
            s += f"{ind.b}assign {self.cg_cond} = 1'b1;\n"
        elif self.disable_style == DISABLE_PRESET.DISABLE_REG:
            s += f"{ind.b}assign {self.cg_cond} = (state_main_r != DISABLED);\n"
            s += f"{ind.b}\n"
            s += f"{ind.b}always_comb begin\n"
            s += f"{ind[1]}case (state_main_r)\n"
            s += f"{ind[2]}MAIN_IDLE: state_main_w = (disable_r)? DISABLED : ()? WORK: MAIN_IDLE;//TODO\n"
            s += f"{ind[2]}WORK:      state_main_w = (disable_r)? DISABLED : ()? MAIN_IDLE : WORK;//TODO\n"
            s += f"{ind[2]}DISABLED:  state_main_w = (clr_disable_r)? MAIN_IDLE : DISABLED;//TODO\n"
            s += f"{ind[2]}default    state_main_w = MAIN_IDLE;\n"
            s += f"{ind[1]}endcase\n"
            s += f"{ind.b}end\n"
        elif self.disable_style == DISABLE_PRESET.EN_WIRE:
            s += f"{ind.b}assign {self.cg_cond} = i_en;\n"
        return s

    @SVgen.UserMethod
    @Clip
    def SeqToClip(self, pkg=None, toclip=True, ind=None):
        """
        Build basic sequential part including state_main, clr_interrupts not in the control reg list...etc.
        """
        s = ""
        s1 = []
        s2 = []
        w = 0
        clr = self.clr_affix
        if self.protocol is None:
            s += f"\n"
        if self.protocol == PRCL_PRESET.REQACK:
            s += self.ReqAckSeqStr(ind=ind)

        s += f"{ind.b}\n"
        # TODO array clear interrupt
        if not self.regbk.raw_intr_stat:
            self.print("interrupt struct not specified")
        else:
            for intr in self.regbk.raw_intr_stat:
                w = max(w, len(clr + intr.name) + 2)
            for intr in self.regbk.raw_intr_stat:
                if not clr.upper() + intr.name.upper() in self.regbk.regaddrsdict:
                    s1 += [f'{clr+intr.name+"_r":<{w}} <= \'0;']
                    s2 += [f'{clr+intr.name+"_r":<{w}} <= {clr+intr.name}_w;']
            s += self.SeqCeStr(s1, s2, ce="", ind=ind)
        return s

    @SVgen.Str
    def ReqAckSeqStr(self, ind=None):
        s = ""
        if self.wrdata_style == WRDATA_PRESET.INSTANT:
            s += self.SeqCeStr([f"o_ack <= '0;"], [f"o_ack <= ack_w;"], ind=ind)
        elif self.wrdata_style == WRDATA_PRESET.RD_NEXT_CYCLE:
            pass
        elif self.wrdata_style == WRDATA_PRESET.NEXT_CYCLE:
            s += self.SeqCeStr(
                [f"reqNack_r <= '0;"], [f"reqNack_r <= i_req && o_ack;"], ind=ind
            )
            s += self.SeqCeStr(
                [f"write_r <= '0;", f"{self.addr_name}_r <= '0;"],
                [
                    f"write_r <= {self.write_name};",
                    f"{self.addr_name}_r <= i_{self.addr_name};",
                ],
                ce="i_req && o_ack",
                ind=ind,
            )
        s += f"{ind.b}\n"
        ##
        if self.disable_style is None:
            pass
        elif self.disable_style == DISABLE_PRESET.DISABLE_REG:
            s += self.SeqCeStr(
                [f"state_main_r <= MAIN_IDLE;"],
                [f"state_main_r <= state_main_w;"],
                ce="state_main_r != state_main_w",
                ind=ind,
            )
        elif self.disable_style == DISABLE_PRESET.EN_WIRE:
            pass
        return s

    @SVgen.UserMethod
    def ToFile(self, pkg=None, ind=None, toclip=False, overwrite=False):
        self.Custom()
        regbktemp = self.Swap(pkg)
        ind = self.cur_ind if not ind else ind
        Ind = self.IndBlk()
        mod = self.ModBlk()
        banw = 25
        logicban = self.Line3BannerBlk(banw, "//", "Logic")
        logic = self.Str2Blk(self.LogicToClip, pkg=pkg, toclip=False)
        combban = self.Line3BannerBlk(banw, "//", "Combinational")
        comb = self.Str2Blk(self.CombToClip, pkg=pkg, toclip=False)
        seqban = self.Line3BannerBlk(banw, "//", "Sequential")
        seq = self.Str2Blk(self.SeqToClip, pkg=pkg, toclip=False)
        regbkban = self.Line3BannerBlk(banw, "//", "Reg bank")
        rdata = self.Str2Blk(self.RdataToClip, pkg=pkg, toclip=False)
        wdata = self.Str2Blk(self.WdataToClip, pkg=pkg, toclip=False)
        s = self.Genlist(
            [
                (mod,),
                mod,
                (1, logicban, logic, combban, comb, seqban, seq, regbkban),
                [Ind, rdata],
                [Ind, wdata],
                mod,
            ]
        )
        if toclip:
            ToClip(s)
        p = self.FileWrite(self.regbkstr, s, "sv", overwrite=overwrite)
        self.print("Regbk file write to", p)
        self.regbk = regbktemp

    def Swap(self, pkg=None):
        regbktemp = self.regbk
        regbk = SVRegbk(pkg) if pkg and type(pkg) == str else self.regbk
        self.regbk = regbk
        return regbktemp


if __name__ == "__main__":
    g = RegbkGen()

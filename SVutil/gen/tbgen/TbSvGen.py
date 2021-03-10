import os
import sys
import itertools
from functools import reduce

import numpy as np

from SVutil.SVparse import *
from SVutil.SVgen import *
from SVutil.SVclass import *
from SVutil.gen.TestGen import TestGen

@SVgen.UserClass
class TbSvGen(TestGen):

    def DefineBlk(self):
        ind = self.cur_ind.Copy()
        yield ""
        s = "\n"
        s += 'import "DPI-C" function string getenv(input string env_name);\n'
        s += "`timescale 1ns/1ns\n"
        s += "`include " + f'"{self.incfile}.sv"\n'
        s += f"`define {self.endcyclemacro} 100\n"
        s += f"`define {self.hclkmacro} 5\n"

        s += f"`define TEST_CFG //TODO\n"

        s += f'`define FSDBNAME(suffix) `"{self.fsdbname}``suffix``.fsdb`"\n'
        s = s.replace("\n", f"\n{ind.b}")
        yield s

    def ModBlk(self):
        ind = self.cur_ind.Copy()
        yield ""
        s = f"{ind.b}module " + GBV.TOPMODULE + ";\n"
        yield s + self.InitialStr(ind=ind + 1)
        s = "\n" + ind.b + "endmodule"
        yield s

    @SVgen.Str
    def InitialStr(self, ind=None):
        s = self.clocking_str(ind=ind)
        s += self.event_macro_str(ind=ind)
        # dummy
        s += f'{ind.b}logic dummy; // general purpose dummy logic\n'
        s += self.initial_block_str(ind=ind)
        return s

    @SVgen.Str
    def clocking_str(self, ind=None):
        # clock, reset and clock count
        ck_lst = reduce(
            (lambda x, y: x + ", " + f'{y[0]+"_" if y[0] != "" else ""}clk'),
            self.clk_domain_lst,
            "",
        )[2:]
        rst_lst = reduce(
            (lambda x, y: x + ", " + f'{y[0]+"_" if y[0] != "" else ""}rst{y[1]}'),
            self.clk_domain_lst,
            "",
        )[2:]
        ccnt_lst = reduce(
            (lambda x, y: x + ", " + f'{y[0]+"_" if y[0] != "" else ""}clk_cnt'),
            self.clk_domain_lst,
            "",
        )[2:]
        s = f"{ind.b}logic {ck_lst};\n"
        s += f"{ind.b}logic {rst_lst};\n"
        s += f"{ind.b}int {ccnt_lst};\n"
        for ck in self.clk_domain_lst:
            _aff = ck[0] + "_" if ck[0] != "" else ""
            s += f"{ind.b}`Pos({_aff}rst_out, {_aff}rst{ck[1]})\n"
            s += f"{ind.b}`PosIf({_aff}ck_ev , {_aff}clk, {_aff}rst{ck[1]})\n"
        return s

    @SVgen.Str
    def event_macro_str(self, ind=None):
        # events
        ev_lst = reduce(
            (lambda x, y: x + ", " + str(y[1])), self.eventlst + [("", "")], ""
        )[2:-2]
        s = f"{ind.b}logic {ev_lst}; //TODO modify event condition\n"

        w = self.FindFormatWidth([i[0] + ", " + i[1] + "," for i in self.eventlst])
        for ev in self.eventlst:
            s += f'{ind.b}`PosIf({ev[0]+", "+ev[1]+",":<{w}} {self.rststr}_n)//TODO modify reset logic\n'
        return s

    @SVgen.Str
    def initial_block_str(self, ind=None):
        s = f"{ind.b}`WithFinish\n\n"
        for i, ck in enumerate(self.clk_domain_lst):
            _aff = ck[0] + "_" if ck[0] != "" else ""
            s += f"{ind.b}always #`{self.hclkmacro} {_aff}clk= ~{_aff}clk;\n"
            _cmt = "//" if i == 0 else ""
            s += f"{ind.b}{_cmt}always #(2*`{self.hclkmacro}) {_aff}clk_cnt = {_aff}clk_cnt+1;\n"
        s += self.AnsiColorVarStr(ind=ind)
        s += f"{ind.b}initial begin\n"
        _s = f'{ind[1]}$fsdbDumpfile({{"{self.fsdbname}_", getenv("TEST_CFG"), ".fsdb"}});\n'
        _s += f'{ind[1]}$fsdbDumpvars(0,{GBV.TEST},"+all");\n'

        for pyev in self.pyeventlgclst:
            _s += f"{ind[1]}{pyev} = 0;\n"
        for ck in self.clk_domain_lst:
            _aff = ck[0] + "_" if ck[0] != "" else ""
            _s += f"{ind[1]}{_aff}clk = 0;\n"
            _s += f'{ind[1]}{_aff}rst{ck[1]} = {1 if ck[1] =="_n" else 0};\n'
        _s += f"{ind[1]}#1 `NicotbInit\n"
        _s += f"{ind[1]}#10\n"
        for ck in self.clk_domain_lst:
            _aff = ck[0] + "_" if ck[0] != "" else ""
            rst = _aff + "rst" + ck[1]
            _s += f'{ind[1]}{rst} = {0 if ck[1] == "_n" else 1};\n'
        _s += f"{ind[1]}#10\n"
        for ck in self.clk_domain_lst:
            _aff = ck[0] + "_" if ck[0] != "" else ""
            rst = _aff + "rst" + ck[1]
            _s += f'{ind[1]}{rst} = {1 if ck[1] == "_n" else 0};\n'
            _s += f"{ind[1]}{_aff}clk_cnt = 0;\n"
        _s += "\n"
        _ck = self.clk_domain_lst[0][0]
        _aff = _ck + "_" if _ck != "" else ""
        _s += f"{ind[1]}while ({_aff}clk_cnt < `{self.endcyclemacro} && sim_stop == 0 && time_out ==0) begin\n"
        _s += f"{ind[2]}@ (posedge {_aff}clk)\n"
        _s += f"{ind[2]}{_aff}clk_cnt <= {_aff}clk_cnt + 1;\n"
        _s += f"{ind[1]}end\n"
        # _s += f'#(2*`{self.hclkmacro+"*`"+self.endcyclemacro}) $display("timeout");\n' #TODO
        _s += "\n"
        _s += self.SimFinStr(ind=ind + 1)
        _s += f"{ind[1]}`NicotbFinal\n"
        _s += f"{ind[1]}$finish;\n"
        _s += f"{ind.b}end\n\n"
        return s + _s

    @SVgen.Str
    def AnsiColorVarStr(self, ind=None):
        s = f'\n{ind.b}string ansi_blue   = "\\033[34m";\n'
        s += f'{ind.b}string ansi_cyan   = "\\033[36m";\n'
        s += f'{ind.b}string ansi_green  = "\\033[32m";\n'
        s += f'{ind.b}string ansi_yellow = "\\033[33m";\n'
        s += f'{ind.b}string ansi_red    = "\\033[31m";\n'
        s += f'{ind.b}string ansi_reset  = "\\033[0m";\n'
        return s

    @SVgen.Str
    def SimFinStr(self, ind=None):
        _ck = self.clk_domain_lst[0][0]
        _aff = _ck + "_" if _ck != "" else ""
        s = f'{ind.b}$display({{ansi_blue,"{"":=<42}", ansi_reset}});\n'
        s += f'{ind.b}$display({{"[Info] Test case:", ansi_yellow, getenv("TEST_CFG"), ansi_reset}});\n'
        s += f"{ind.b}if ({_aff}clk_cnt >= `{self.endcyclemacro}|| time_out)\n"
        s += f'{ind[1]}$display({{"[Error]", ansi_yellow, " Simulation Timeout.", ansi_reset}});\n'
        s += f"{ind.b}else if (sim_pass)\n"
        s += f'{ind[1]}$display({{"[Info]", ansi_green, " Congrat! Simulation Passed.", ansi_reset}});\n'
        s += f"{ind.b}else\n"
        s += f'{ind[1]}$display({{"[Error]", ansi_red, " Simulation Failed.", ansi_reset}});\n'
        s += f'{ind.b}$display({{ansi_blue,"{"":=<42}", ansi_reset}});\n\n'
        return s

    def DeclareBlkBlk(self):
        pass

    def TopBlkBlk(self, tpname):
        ind = self.cur_ind.Copy()
        yield ""
        yield

    def LogicBlk(self, module, **conf):
        ind = self.cur_ind.Copy()
        yield ""
        s = self.comment_banner_str("Logics", ind=ind)
        pfield = SVhier.portfield
        for p in module.ports:
            p = SVPort(p)
            if p.tp == "logic" or p.tp == "signed logic":
                s += f"{ind.b}{p.tp} {p.bwstr} {p.name}"
            else:
                s += f"{ind.b}{p.tp} {p.name}"
            if not p.dimstr == "":
                s += f" {p.dimstr};\n"
            else:
                s += ";\n"

        yield s

    @SVgen.Blk
    def ParamBlk(self, module, ind=None, **conf):
        s = self.comment_banner_str("Parameters", ind=ind)
        for pkg, param in module.scope.imported.items():
            for _p in param:
                s += f"{ind.b}import {pkg}::{_p};\n"
        for pkg, param in module.imported.items():
            for _p in param:
                s += f"{ind.b}import {pkg}::{_p};\n"
        pmfield = SVhier.paramfield
        for param, v in module.paramports.items():
            detail = module.paramsdetail[param]
            tpstr = detail[pmfield.tp] + " " if detail[pmfield.tp] != "" else ""
            bwstr = detail[pmfield.bwstr] + " " if detail[pmfield.bwstr] != "" else ""
            pmtp = detail[pmfield.paramtype]
            s += f"{ind.b}{pmtp} {tpstr}{bwstr}{param} = {detail[pmfield.numstr]};\n"
        yield s

    @SVgen.Blk
    def CommentBlkBlk(self, s, width=35):
        yield f'{ind.b}//{"":=<{width}}\n{ind.b}//{s:^{width}}\n{ind.b}//{"":=<{width}}\n'

    @SVgen.Str
    def comment_banner_str(self, s, width=35, ind=None):
        return (
            f'{ind.b}//{"":=<{width}}\n{ind.b}//{s:^{width}}\n{ind.b}//{"":=<{width}}\n'
        )

    @SVgen.Blk
    def InsBlk(self, module, name="dut", ind=None, **conf):
        s = "\n"
        s += ind.base + module.hier + " #(\n"
        s_param = ""
        w = self.FindFormatWidth(
            [(param + " ",) for param, v in module.paramports.items()]
        )
        for param, v in module.paramports.items():
            if module.paramsdetail[param][SVhier.paramfield.paramtype] == "parameter":
                s_param += f"{ind[1]},.{param:<{w[0]}}({param})\n"
        s_param = s_param.replace(f"{ind[1]},", ind[1] + " ", 1)
        sb = f"{ind.b}) {name} (\n"
        s_port = ""
        w = self.FindFormatWidth([(n + " ",) for io, n, *_ in module.ports])
        for io, n, dim, *_ in module.ports:
            if "clk" in n:
                s_port += ind[1] + ",." + f"{n:<{w[0]}}" + f"({self.clkstr})\n"
            elif "rst" in n:
                s_port += ind[1] + ",." + f"{n:<{w[0]}}" + f"({self.rststr})\n"
            else:
                s_port += (
                    ind[1]
                    + ",."
                    + f"{n:<{w[0]}}"
                    + f"({n})\n" 
                )

        s_port = s_port.replace(f"{ind[1]},", ind[1] + " ", 1)
        s += s_param + sb + s_port + ind.base + ");\n"
        yield s

    def module_test(self, module=None, **conf):
        module = self.dut if not module else module
        ins = self.InsBlk(module)
        mod = self.ModBlk()
        pm = self.ParamBlk(module)
        lg = self.LogicBlk(module)

        defb = self.DefineBlk()
        ind = self.IndBlk()

        s = self.Genlist([(defb,), (mod,),  (1, pm, lg, ins), mod])
        if conf.get("copy") == True:
            ToClip(s)
        return s

    def write(self, text, **conf):
        p = self.TbWrite(text, "sv", **conf)
        self.print("SV testbench written to ", p)

    @SVgen.UserMethod
    def ShowIns(self, module=None):
        module = self.dut if not module else module
        ins = self.InsBlk(module)
        s = self.Genlist([(ins,)])
        ToClip(s)
        self.print(s)


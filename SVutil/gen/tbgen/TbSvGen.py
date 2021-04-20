import os
import sys
import itertools
from functools import reduce

import numpy as np

from SVutil.SVparse import *
from SVutil.SVgen import *
from SVutil.SVclass import *
from SVutil.gen.TestGen import TestGen
from SVutil.gen.SrcGen import SrcGen
# TODO instance block can be from ConnectGen

def initial_block(orig):
    @wraps(orig)
    def new_func(*arg, **kwargs):
        ind = kwargs.get("ind")
        ind = (
            arg[0].cur_ind.Copy() if ind is None else ind
        )  # orig must be a member function
        kwargs["ind"] = ind
        s = f"{ind.b}initial begin\n"
        s += SVgen.str(orig)(*arg, **kwargs)
        s += f"{ind.b}end\n\n"
        return s
    return new_func

@SVgen.UserClass
class TbSvGen(TestGen, SrcGen):
    def __init__(self, ind=Ind(0), session=None):
        super().__init__(ind=ind, session=session)
        self.customlst += [
            "hclkmacro",
            "endcyclemacro",
            "clkstr",
            "rststr",
            "endcycle",
            "clk_domain_lst"
            "nicoinit_delay"
            "pre_reset_delay"
            "mid_reset_delay"
        ]
        self.hclkmacro = "HCYCLE"
        self.endcyclemacro = "TIMEOUTCYCLE"
        self.clkstr = "clk"
        self.rststr = "rst"
        self.endcycle = 10000

        self.clk_domain_lst = [('tb', '_n')]

        self.nicoinit_delay = 1
        self.pre_reset_delay = 10
        self.mid_reset_delay = 10

    @SVgen.str
    def include_str(self, paths=[], ind=None):
        s  = f'{ind.b}import "DPI-C" function string getenv(input string env_name);\n'
        s += f"{ind.b}`include " + f'"{self.incfile}.sv"\n'
        for p in paths:
            s += f"{ind.b}`include \"p\"\n"
        return s

    @SVgen.str
    def define_str(self, ind=None):
        s  = f"{ind.b}`timescale 1ns/1ns\n"
        s += f"{ind.b}`define {self.endcyclemacro} 100\n"
        s += f"{ind.b}`define {self.hclkmacro} 5\n"

        s += f"{ind.b}`define TEST_CFG //TODO\n"

        s += f'{ind.b}`define FSDBNAME(suffix) `"{self.fsdbname}``suffix``.fsdb`"\n'
        return s

    def ModBlk(self):
        ind = self.cur_ind.Copy()
        yield ""
        s = f"{ind.b}module " + GBV.TOPMODULE + ";\n"
        yield s + self.declare_logic(ind=ind + 1)
        s = "\n" + ind.b + "endmodule"
        yield s

    @SVgen.str
    def declare_logic(self, ind=None):
        s  = self.comment_banner_str("Signal Declaration", ind=ind)
        s += self.clocking_logic(ind=ind)
        s += self.event_macro_logic(ind=ind)
        s += self.misc_logic(ind=ind)
        s += self.initial_block_str(ind=ind)
        return s

    @SVgen.str
    def clocking_logic(self, ind=None):
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
        s  = f"{ind.b}logic {ck_lst};\n"
        s += f"{ind.b}logic {rst_lst};\n"
        s += f"{ind.b}int {ccnt_lst};\n"
        for ck in self.clk_domain_lst:
            _aff = ck[0] + "_" if ck[0] != "" else ""
            s += f"{ind.b}`Pos({_aff}rst_out, {_aff}rst{ck[1]})\n"
            s += f"{ind.b}`PosIf({_aff}ck_ev , {_aff}clk, {_aff}rst{ck[1]})\n"
        return s

    @SVgen.str
    def event_macro_logic(self, ind=None):
        # events
        #ev_lst = reduce(
        #    (lambda x, y: x + ", " + str(y[1])), self.nico_eventlst + [("", "")], ""
        #)[2:-2]
        s = ""
        for ev in self.nico_eventlst:
            s += f"{ind.b}logic {ev[1]}; //TODO modify event condition\n"

        w = self.FindFormatWidth([i[0] + ", " + i[1] + "," for i in self.nico_eventlst])
        for ev in self.nico_eventlst:
            s += f'{ind.b}`PosIf({ev[0]+", "+ev[1]+",":<{w}} {self.rststr}_n)//TODO modify reset logic\n'
        s += '\n'
        for ev in self.sv_eventlst:
            s += f'{ind.b}event event_{ev};\n'
        s += '\n'
        s += f"{ind.b}`WithFinish\n"
        return s

    @SVgen.str
    def misc_logic(self, ind=None):
        s  = f'{ind.b}logic dummy; // general purpose dummy logic\n'
        s += f'{ind.b}logic [31:0] seed; // random seed\n'
        s += f'{ind.b}logic [3:0] sim_stat; // can be used for programmable event trigger\n'
        return s

    @SVgen.str
    def initial_block_str(self, ind=None):
        s = self.clocking_block(ind=ind)
        s += self.AnsiColorVarStr(ind=ind)
        s += self.timeformat_initial_block(ind=ind)
        s += self.seed_initial_block(ind=ind)
        s += self.clocking_initial_block(ind=ind)
        s += self.event_initial_block(ind=ind)
        s += self.sim_exit_initial_block(ind=ind)
        s += self.fsdb_initial_block(ind=ind)
        return s

    @SVgen.str
    def clocking_block(self, ind=None):
        s = ''
        for i, ck in enumerate(self.clk_domain_lst):
            _aff = ck[0] + "_" if ck[0] != "" else ""
            s += f"{ind.b}always #`{self.hclkmacro} {_aff}clk= ~{_aff}clk;\n"
            _cmt = "//" if i == 0 else ""
            s += f"{ind.b}{_cmt}always #(2*`{self.hclkmacro}) {_aff}clk_cnt = {_aff}clk_cnt+1;\n"
        return s

    @initial_block
    def clocking_initial_block(self, ind=None):
        s = ''
        for ck in self.clk_domain_lst:
            _aff = ck[0] + "_" if ck[0] != "" else ""
            s += f"{ind[1]}{_aff}clk = 0;\n"
            s += f'{ind[1]}{_aff}rst{ck[1]} = {1 if ck[1] =="_n" else 0};\n'
        s += f"{ind[1]}#{self.nicoinit_delay} `NicotbInit\n"
        s += f"{ind[1]}#{self.pre_reset_delay}\n"
        for ck in self.clk_domain_lst:
            _aff = ck[0] + "_" if ck[0] != "" else ""
            rst = _aff + "rst" + ck[1]
            s += f'{ind[1]}{rst} = {0 if ck[1] == "_n" else 1};\n'
        s += f"{ind[1]}#{self.mid_reset_delay}\n"
        for ck in self.clk_domain_lst:
            _aff = ck[0] + "_" if ck[0] != "" else ""
            rst = _aff + "rst" + ck[1]
            s += f"{ind[1]}{rst} = {1 if ck[1] == '_n' else 0};\n"
            s += f"{ind[1]}{_aff}clk_cnt = 0;"
        return s

    @initial_block
    def event_initial_block(self, ind=None):
        s = ''
        for pyev in self.py_logic_eventlst:
            s += f"{ind[1]}{pyev} = 0;\n"
        s += "\n"
        s += f"{ind[1]}@ (event_exit)\n"
        s += f"{ind[1]}`NicotbFinal\n"
        s += f"{ind[1]}$finish;"
        return s

    @initial_block
    def timeformat_initial_block(self, unit=-9, precision=3, suffix='" ns"', width=12, ind=None):
        """
        parameters:
        unit: in {-3,-6,-9,-12,-15}, corresponds to ms, us, ns, ps, fs
        precision: the number of fraction digits
        suffix: display the scale alongside the time values
        width: minimum display text field width
        """
        s = f"{ind[1]}$timeformat({unit}, {precision}, {suffix}, {width});"
        return s 

    
    @initial_block
    def seed_initial_block(self, salt="32'h44495936", ind=None):
        s = f"{ind[1]}if ($value$plusargs(\"seed=%d\", seed)) seed = seed ^ {salt};\n"
        s += f"{ind[1]}else seed = {salt};"
        return s


    @initial_block
    def fsdb_initial_block(self, ind=None):
        s = f'{ind[1]}$fsdbDumpfile({{"{self.fsdbname}_", getenv("TEST_CFG"), ".fsdb"}});\n'
        s += f'{ind[1]}$fsdbDumpvars(0,{GBV.TEST},"+all");'
        return s

    @initial_block
    def sim_exit_initial_block(self, ind=None):
        s = f"{ind[1]}#{self.nicoinit_delay} `NicotbInit\n"
        s += f"{ind[1]}#{self.pre_reset_delay}\n"
        s += f"{ind[1]}#{self.mid_reset_delay}\n"
        _ck = self.clk_domain_lst[0][0]
        _aff = _ck + "_" if _ck != "" else ""
        s += f"{ind[1]}while ({_aff}clk_cnt < `{self.endcyclemacro} && sim_stop == 0 && time_out ==0) begin\n"
        s += f"{ind[2]}@ (posedge {_aff}clk)\n"
        s += f"{ind[2]}{_aff}clk_cnt <= {_aff}clk_cnt + 1;\n"
        s += f"{ind[1]}end\n"
        # _s += f'#(2*`{self.hclkmacro+"*`"+self.endcyclemacro}) $display("timeout");\n' #TODO
        s += "\n"
        s += self.SimFinStr(ind=ind + 1)
        s += f"{ind[1]}-> event_exit;"
        return s

    @SVgen.str
    def AnsiColorVarStr(self):
        s  = f'string ansi_blue   = "\\033[34m";\n'
        s += f'string ansi_cyan   = "\\033[36m";\n'
        s += f'string ansi_green  = "\\033[32m";\n'
        s += f'string ansi_yellow = "\\033[33m";\n'
        s += f'string ansi_red    = "\\033[31m";\n'
        s += f'string ansi_reset  = "\\033[0m";\n'
        return s

    @SVgen.str
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
        s += f'{ind.b}$display({{ansi_blue,"{"":=<42}", ansi_reset}});'
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
        cur_group = SVPort(module.ports[0]).group
        for p in module.ports:
            p = SVPort(p)
            if cur_group != p.group:
                s += '\n'
                cur_group = p.group
            if p.tp == "logic" or p.tp == "signed logic":
                s += f"{ind.b}{p.tp} {p.bwstr} {p.name}"
            else:
                s += f"{ind.b}{p.tp} {p.name}"
            if not p.dimstr == "":
                s += f" {p.dimstr};\n"
            else:
                s += ";\n"

        yield s+'\n'

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
        yield s+'\n'

    @SVgen.Blk
    def CommentBlkBlk(self, s, width=35):
        yield f'{ind.b}//{"":=<{width}}\n{ind.b}//{s:^{width}}\n{ind.b}//{"":=<{width}}\n'

    @SVgen.str
    def comment_banner_str(self, s, width=30, ind=None, spacing=False):
        return f'{ind.b}//{"":=<{width}}\n' \
            + f'{ind.b}//{s:^{width}}\n' \
            + f'{ind.b}//{"":=<{width}}\n'

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
        cur_group = SVPort(module.ports[0]).group
        for p in module.ports:
            p = SVPort(p)
            if cur_group != p.group:
                s_port += '\n'
                cur_group = p.group
            if "clk" in p.name:
                s_port += f"{ind[1]},.{p.name:<{w[0]}}({self.clkstr})\n"
            elif "rst" in p.name:
                s_port += f"{ind[1]},.{p.name:<{w[0]}}({self.rststr})\n"
            else:
                s_port += f"{ind[1]},.{p.name:<{w[0]}}({p.name})\n"

        s_port = s_port.replace(f"{ind[1]},", ind[1] + " ", 1)
        s += s_param + sb + s_port + ind.base + ");\n"
        yield s

    def module_test(self, module=None, **conf):
        module = self.dut if not module else module

        inc = self.include_str()
        defb = self.define_str()
        mod = self.ModBlk()
        pm = self.ParamBlk(module)
        lg = self.LogicBlk(module)
        ins = self.InsBlk(module)

        s = self.Genlist([inc, defb, (mod,),  (1, pm, lg, ins), mod])
        if conf.get("copy") == True:
            ToClip(s)
        return s

    def write(self, text, **conf):
        p = self.TbWrite(text, "sv", **conf)
        self.print("SV testbench written to ", p)

    # decorator
    def initial_block(orig):
        return initial_block(orig)

    @SVgen.UserMethod
    def ShowIns(self, module=None):
        module = self.dut if not module else module
        ins = self.InsBlk(module)
        s = self.Genlist([(ins,)])
        ToClip(s)
        self.print(s)


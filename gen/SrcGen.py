import os
import sys
sys.path.append(os.environ.get('SVutil'))
from SVparse import *
from SVgen import * 
from SVclass import *
import itertools
import numpy as np
class SrcGen(SVgen):
    def __init__(self, ind=Ind(0)):
        super().__init__()
        self.regbk= SVRegbk(self.regbkstr)
        self.clk_name = 'i_clk'
        self.rst_name = 'i_rst_n'
        self.regbk_addr_name = 'i_addr'
        self.regbk_wdata_name = 'i_wdata'
        self.regbk_addr_slice = f'[{self.regbk.regaddrbw_name}:{(self.regbk.regbsizebw_name)}]'
        self.regbk_write_cond = 'write_valid'
        self.regbk_cg_cond = 'regbk_cg'
        self.regbk_ro_cg_cond = 'regbk_ro_cg'
    def RegbkRdataStr(self, reg, _slice, w, ind):
        #TODO slice dependent, now it only pad the MSB and it's usually the case
        pad = f'{SVRegbk.regbw_name}-{reg}{SVRegbk.bw_suf}'
        return f'{ind.b}{reg:<{w}}: rdata_w = {{{{({pad}){{1\'b0}}}}, {reg.lower()}_r}};\n'
    def RegbkWdataSeqStr(self, reg, _slice, rw=None, ind=None):
        #TODO slice dependent, now it only pad the MSB and it's usually the case
        ind = self.cur_ind.Copy() if not ind else ind
        rstedge = 'negedge' if self.rst_name[-2:] == '_n' else 'posedge'
        s = f'{ind.b}always_ff @(posedge {self.clk_name} or {rstedge} {self.rst_name}) begin\n'
        s += f'{ind[1]}if({"!" if self.rst_name[-2:] == "_n" else ""}{self.rst_name}) '
        s += f'{reg.lower()}_r <= {reg}{SVRegbk.default_suf};\n'
        #s += f'{ind[1]}end\n'
        if rw and rw == 'RO':
            s += f'{ind[1]}else if({self.regbk_ro_cg_cond} && ({reg.lower()}_r != {reg.lower()}_w)) '
        else:
            s += f'{ind[1]}//else if ({self.regbk_cg_cond} && {self.regbk_addr_name}{self.regbk_addr_slice} == {reg}) \n'
            s += f'{ind[1]}else if ({self.regbk_cg_cond} && ({reg.lower()}_r != {reg.lower()}_w)) '
        s += f'{reg.lower()}_r <= {reg.lower()}_w;\n'
        s += f'{ind.b}end\n'
        return s
    def RegbkWdataCombStr(self, reg, _slice, rw=None, ind=None):
        #TODO slice dependent, now it only pad the MSB and it's usually the case
        ind = self.cur_ind.Copy() if not ind else ind
        s = f'{ind.b}always_comb begin\n'
        s += f'{ind[1]}{reg.lower()}_w = {reg.lower()}_r;\n'
        if rw and rw == 'RO':
            s += f'{ind[1]}//TODO\n{ind.b}end\n'
        else:
            s += f'{ind[1]}if ({self.regbk_write_cond} && {self.regbk_addr_name}{self.regbk_addr_slice} == {reg}) begin\n'
            s += f'{ind[2]}{reg.lower()}_w = {self.regbk_wdata_name}[{reg}{SVRegbk.bw_suf}-1:0];\n' #TODO
            s += f'{ind[1]}end \n'
            s += f'{ind[1]}else begin\n'
            s += f'{ind[2]}//TODO\n'
            s += f'{ind[1]}end\n{ind.b}end\n'
        return s
    def RegbkRdataToClip(self, pkg=None, ind=None):
        regbk = SVRegbk(pkg) if pkg and type(pkg)==str else self.regbk
        ind = self.cur_ind.Copy() if not ind else ind
        s = ''
        w = 0
        for i in regbk.addrs.enumls:
            w = max(w, len(i.name))
        for reg in regbk.addrs.enumls:
            _slice = regbk.regslices.get(reg.name)
            s += self.RegbkRdataStr( reg.name, _slice, w, ind)
        ToClip(s)
        return s
    def RegbkWdataToClip(self, pkg=None, ind=None):
        regbk = SVRegbk(pkg) if pkg and type(pkg)==str else self.regbk
        ind = self.cur_ind.Copy() if not ind else ind
        s = ''
        w = 30
        print ( f'write condition: {self.regbk_write_cond}')
        print ( f'clock gating condition: {self.regbk_cg_cond}')
        for reg in regbk.addrs.enumls:
            _slice = regbk.regslices.get(reg.name)
            s += f'{ind.b}//{"reg "+reg.name:=^{w}}\n'
            rw = None
            if len(reg.cmt) >= 2 and 'RO' in reg.cmt[1] :
                rw = 'RO'
            s += self.RegbkWdataCombStr( reg.name, _slice, rw, ind)
            s += self.RegbkWdataSeqStr( reg.name, _slice, rw, ind) + '\n'
        ToClip(s)
        return s
if __name__ == '__main__':
    g = SrcGen()

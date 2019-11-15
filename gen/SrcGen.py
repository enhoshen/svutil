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
        self.regbk_addr_slice = f'[{int(np.log2(self.regbk.regbsize)-1)}:0]'
        self.regbk_write_cond = 'i_req && o_ack'
    def RegbkRdataStr(self, reg, _slice, w, ind):
        #TODO slice dependent, now it only pad the MSB and it's usually the case
        pad = f'{SVRegbk.regbw_name}-{reg}{SVRegbk.bw_suf}'
        return f'{ind.b}{reg:<{w}}: rdata_w = {{{{({pad}){{1\'b0}}}}, {reg.lower()}_r}};\n'
    def RegbkWdataStr(self, reg, _slice, ind=None):
        #TODO slice dependent, now it only pad the MSB and it's usually the case
        ind = self.cur_ind.Copy() if not ind else ind
        rstedge = 'negedge' if self.rst_name[-2:] == '_n' else 'posedge'
        s = f'{ind.b}always_ff @(posedge {self.clk_name} or {rstedge} {self.rst_name}) begin\n'
        s += f'{ind[1]}if({"!" if self.rst_name[-2:] == "_n" else ""}{self.rst_name})\n'
        s += f'{ind[2]}{reg.lower()}_r <= {reg}{SVRegbk.default_suf};\n'
        s += f'{ind[1]}else if ({self.regbk_write_cond} && {self.regbk_addr_name}{self.regbk_addr_slice} == {reg})\n'
        s += f'{ind[2]}{reg.lower()}_r <= {reg.lower()}_w;\n' #TODO
        s += f'{ind.b}end\n'
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
        for reg in regbk.addrs.enumls:
            _slice = regbk.regslices.get(reg.name)
            s += f'{ind.b}//{"reg "+reg.name:=^{w}}\n'
            s += self.RegbkWdataStr( reg.name, _slice, ind)
        ToClip(s)
        return s
if __name__ == '__main__':
    g = SrcGen()

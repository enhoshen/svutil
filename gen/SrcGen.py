import os
import sys
sys.path.append(os.environ.get('SVutil'))
from SVparse import *
from SVgen import * 
from SVclass import *
import itertools
import numpy as np

class SrcGen(SVgen):
    def __init__(self):
        super().__init__()
        self.customlst += [ 'clk_name',
                            'rst_name']
        self.clk_name = 'i_clk'
        self.rst_name = 'i_rst_n'
    def RegLogicStr(self, w, reg, bw, tp, ind):
        bwstr = '' if bw ==1 else f'[{bw}-1:0] ' 
        return  f'{ind.b}{tp+" "+bwstr:<{w[0]}}{reg+"_r":<{w[1]}} ,{reg}_w;\n'
    def RegLogicArrStr(self, w, reg, bw, tp, dim, ind):
        bwstr = '' if bw ==1 else f'[{bw}-1:0] ' 
        return  f'{ind.b}{tp+" "+bwstr:<{w[0]}}{reg+"_r "+dim:<{w[1]}} ,{reg}_w {dim};\n'
    def SeqCeStr(self, s1, s2, ce='', ind=None):
        ff_str = f'always_ff @(posedge {self.clk_name} or negedge {self.rst_name}) begin' 
        s = f'{ind.b}{ff_str}\n'
        rst_sign = '!' if self.rst_name[-1]=='n' else ''
        s += f'{ind[1]}if ({rst_sign}{self.rst_name}) begin\n'
        s += s1
        s += f'{ind[1]}end\n'
        s += f'{ind[1]}else if ({ce}) begin //TODO\n'
        s += s2
        s += f'{ind[1]}end\n'
        s += f'{ind.b}end\n'
        return s

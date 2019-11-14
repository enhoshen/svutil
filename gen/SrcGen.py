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
    def RegbkRdataStr(self, reg, _slice, w, ind):
        #TODO slice dependent, now it only pad the MSB and it's usually the case
        pad = f'{SVRegbk.regbw_name}-{reg}{SVRegbk.bw_suf}'
        return f'{ind.b}{reg:<{w}}: rdata_w = {{{{({pad}){{1\'b0}}}}, {reg.lower()}_r}};\n'
    def RegbkRdataToClip(self, pkg=None):
        regbk = SVRegbk(pkg) if pkg and type(pkg)==str else self.regbk
        ind = self.cur_ind.Copy() 
        s = ''
        w = 0
        for i in regbk.addrs.enumls:
            w = max(w, len(i.name))
        for reg in regbk.addrs.enumls:
            _slice = regbk.regslices.get(reg.name)
            s += self.RegbkRdataStr( reg.name, _slice, w, ind)
        ToClip(s)
        print(s)
if __name__ == '__main__':
    g = SrcGen()

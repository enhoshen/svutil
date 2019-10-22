from SVparse import EAdict
from NicoUtil import Busdict
from nicotb import *
from nicotb.utils import RandProb
import numpy as np

class Master(Receiver):
    __slots__ = ['psel', 'penable', 'pwrite', 'pstrb', 'pready',
                 'paddr', 'prdata', 'pwdata', 'clk', 'buses', 'A', 'B']
    psize_tp =  EAdict(["BYTE", "HALFWORD", "WORD"])
    def __init__(self,clk):
        self.clk = GetEvent(clk)
        super(Master, self).__init__(list())
    def __getattr__(self, s):
        return self.buses.dic[s]
    def StructConnect( self, pctl,  pready, paddr, pwdata, prdata, A=1, B=5 ) :
        dic = {}
        dic['psel']    = pctl.psel
        dic['penable'] = pctl.penable
        dic['pwrite'] = pctl.pwrite
        dic['pstrb']  = pctl.pstrb
        dic['paddr']  = paddr
        dic['pready'] = pready
        dic['prdata'] = prdata
        dic['pwdata'] = pwdata
        self.buses = Busdict(dic) 
        self.buses.SetTo(0)
        self.buses.Write()
        self.A=A
        self.B=B
    def SendIter(self, cmds):
        # cmd : [address, data, rw]
        rdata = []
        for a,d,rw in cmds:
            self.psel.value = 1
            self.penable.value = 0
            self.paddr.value = a
            if rw :
                self.pwdata.value = d
                self.pwrite.value = 1
            else:
                self.pwdata.value = 0
                self.pwrite.value = 0
            self.buses.Write()
            yield self.clk
            self.penable.value = 1
            self.buses.Write()
            while True:
                self.pready.Read()
                if self.pready.value[0] == 1 :
                    if not rw:
                        rdata.append(self.prdata.value)
                    break
                yield self.clk
            self.psel.value = 0
            self.penable.value = 0
            self.buses.Write()
            if not RandProb(self.A, self.B):
                yield self.clk
                while not RandProb(self.A, self.B):
                    yield self.clk
        self.buses.SetTo(0)
        self.buses.Write()
        yield self.clk
   

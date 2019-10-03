from SVparse import EAdict
from NicoUtil import Busdict
from nicotb import *
from nicotb.protocol import TwoWire
from nicotb.primitives import Semaphore
import numpy as np

class Master():
    __slots__ = ['psel', 'penable', 'pwrite', 'pstrb', 'pready', 'paddr', 'prdata', 'pwdata']
    psize_tp =  EAdict(["BYTE", "HALFWORD", "WORD"])
    def __init__(self,clk=None):
        if clk == None:
            return
        clk = GetEvent(clk)
        self.clk=clk
    def __getattr__(self, s):
        return self.buses.dic[s]
    def StructConnect( self, pctl,  pready, paddr, pwdata, prdata ) :
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
    def SendIter(self, a , d, l):
        pass
    #def Write(self, a, d, l):
    #    yield from self.Issue(True, a, d, l)
   

from SVparse import EAdict
from NicoUtil import Busdict
from nicotb import *
from nicotb.protocol import TwoWire
from nicotb.primitives import Semaphore
import numpy as np

# Only 32b mode
# Do not support error and burst
class Master():
    __slots__ = [
        "hsel", "haddr", "hwrite", "htrans", "hsize", "hburst",
        "hready", "hresp", "hrdata", "hwdata", "clk", "buses"
    ]
    htrans_tp = EAdict([ "IDLE", "BUSY", "NONSEQ", "SEQ" ])
    hburst_tp = EAdict(["SINGLE", "INCR", "WRAP4", "INCR4" 
                            ,"WRAP8", "INCR8", "WRAP16", "INCR16"])
    hend_tp =   EAdict(["LITTLE_END", "BIG_END", "WORD_INV_BIG" ])
    hsize_tp =  EAdict(["BYTE", "HALFWORD", "WORD", "WORD_2"
                            ,"WORD_4", "WORD_8", "WORD16", "WORD32"])
    hresp_tp =  EAdict (["OKAY" , "ERROR" , "RETRY" , "SPLIT" ]) 
    def __init__(self,clk=None):
        if clk == None:
            return
        clk = GetEvent(clk)
        self.clk=clk
    def __getattr__(self, s):
        return self.buses.dic[s]
    def StructConnect( self, hctl, hresp, hready, haddr, hwdata, hrdata ) :
        dic = {}
        dic['hsel'] =   hctl.hsel
        dic['haddr'] =  haddr
        dic['hwrite'] = hctl.hwrite
        dic['htrans'] = hctl.htrans
        dic['hsize'] =  hctl.hsize
        dic['hburst'] = hctl.hburst
        dic['hready'] = hready
        dic['hresp'] =  hresp
        dic['hrdata'] = hrdata
        dic['hwdata'] = hwdata
        self.buses = Busdict(dic) 
        self.hsel.value[0] = 0
        self.hwrite.value[0] = 0
        self.haddr.value[0] = 0 
        self.htrans.value[0] = self.htrans_tp.IDLE
        self.hsize.value[0] = self.hsize_tp.WORD 
        self.hburst.value[0] = self.hburst_tp.SINGLE
        self.buses.Write()
    def DirectConnect(
        self,
        hsel, haddr, hwrite, htrans, hsize, hburst, hready, hresp,
        hrdata, hwdata, clk
    ):
                
        clk = GetEvent(clk)
        self.clk = clk
        dic = {}
        dic['hsel'] = hsel
        dic['haddr'] = haddr
        dic['hwrite'] = hwrite
        dic['htrans'] = htrans
        dic['hsize'] = hsize
        dic['hburst'] = hburst
        dic['hready'] = hready
        dic['hresp'] = hresp
        dic['hrdata'] = hrdata
        dic['hwdata'] = hwdata
        self.buses = Busdict(dic)
        self.hsel.value[0] = 0
        self.hwrite.value[0] = 0
        self.haddr.value[0] = 0
        self.htrans.value[0] = self.htrans_tp.IDLE
        self.hsize.value[0] = self.hsize_tp.WORD 
        self.hburst.value[0] = self.hburst_tp.SINGLE
        self.buses.Write()
    def SendIter(self, a , d, l):
        pass
    #def Write(self, a, d, l):
    #    yield from self.Issue(True, a, d, l)
    def Read(self, a, l):
        ret = yield from self.Issue(False, a, 0, l)
        return ret[0]
             
    def Write(self, a ,d ):
        yield from self.IssueCommands([(True,a,d)])
    def IssueCommands(self, it):
        # format: iterable tuples (True, write_a, write_d, len) or (False, read_a, len)
        # return a list of read_d
        ret = list()
        prev = None
        retry = None
        self.hsel.value[0] = 1
        # TODO Burst size and HTRANS
        # TODO RETRY response
        self.htrans.value[0] = self.htrans_tp.NONSEQ
        print( " issue commands ") 
        self.hsel.Write()
        self.htrans.Write()
        for cmd in it:
            retry_state = False
            error_state = False
            while True:
                if retry_state: 
                    self._HandleCommand(prev)
                    self._HandleWdata(None)
                if self.hresp.value[0] == self.hresp_tp.OKAY : 
                    self._HandleCommand(cmd)
                    self._HandleWdata(prev)
                if prev is None:
                    # Fisrt cycle should be responsed immediately
                    yield self.clk 
                    break
                else:
                    yield from self._WaitReady(prev[0], ret)
                    if self.hresp.value[0] == self.hresp_tp.OKAY :
                        if retry_state :
                            retry_state = False
                        else:
                            break
                    if self.hresp.value[0] == self.hresp_tp.RETRY: 
                        retry_state = True
                    if self.hresp.value[0] == self.hresp_tp.ERROR:
                        print ( f"master error on command {prev}" )
                        error_state = True
            prev = cmd
        # prev is None when iter is empty
        if not prev is None:
            self._HandleWdata(prev)
            self.htrans.value[0] = 0
            self.htrans.Write()
            yield from self._WaitReady(prev[0], ret)
            self.hsel.value[0] = 0
            self.hsel.Write()
        return ret
    def WaitReady(self):
        while True:
            yield self.clk
            self.hready.Read()
            if self.hready.value[0]:
                break
    def _HandleCommand(self, cmd):
        self.haddr.value[0] = cmd[1]
        self.hwrite.value[0] = int(cmd[0])
        self.haddr.Write()
        self.hwrite.Write()

    def _HandleWdata(self, cmd_prev):
        if (not cmd_prev is None) and cmd_prev[0]:
            self.hwdata.value[0] = cmd_prev[2]
            self.hwdata.Write()

    def _WaitReady(self, is_write, ret):
        while True:
            self.hready.Read()
            yield self.clk
            self.hresp.Read()
            #if self.hresp.value[0] == self.hresp_tp.RETRY or self.hresp.value[0] == self.hresp_tp.ERROR:
            #    break
            self.hready.Read()
            if self.hready.value[0]:
                if not is_write:
                    self.hrdata.Read()
                    ret.append(int(self.hrdata.value[0]))
                break


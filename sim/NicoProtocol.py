from nicotb import *
from SVparse import *
import os
import itertools
import numpy as np
from NicoUtil import *
import EnhoAhb 
from nicotb.protocol import Ahb
from nicotb.protocol import TwoWire
from nicotb.protocol import OneWire 
from nicotb.utils import RandProb


class ReqAckBus ( ProtoCreateBus):
    def __init__( self , *args ,clk , side='master' , **kwargs ):
        protoCallback = TwoWire.Master if side == 'master' else MySlaveTwoWire
        self.ArgParse(protoCallback, self.PortParse, *args, clk=clk, **kwargs)
        self.SideChoose(side)
    def PortParse(self, name , hier=''):
        self.req , self.ack = CreateBuses( [((hier,name+'_req',),) , ((hier,name+'_ack',),) ])
        return [self.req , self.ack]
    def Connect(self, ports):
        pass
class ValBus ( ProtoCreateBus): 
    def __init__(self, *args, clk , side = 'master' , **kwargs):
        protoCallback = OneWire.Master if side == 'master' else OneWire.Slave
        self.ArgParse(protoCallback, self.PortParse, *args , clk=clk , **kwargs)
        self.SideChoose(side)
    def PortParse(self,name,hier=''):
        self.val = CreateBus( (hier,name+'_val',))
        return [self.val]
class TwoWireBus ( ProtoCreateBus):
    #EX: inbus = TwoWireBus( data[0],clk=ck_ev ,A=5,name='Input' )
    def __init__( self , *args ,clk , side='master' , **kwargs ):
        protoCallback = TwoWire.Master if side == 'master' else MySlaveTwoWire
        self.ArgParse(protoCallback, self.PortParse, *args, clk=clk, **kwargs)
        self.SideChoose(side)
    def PortParse(self, name , hier=''):
        self.rdy , self.ack = CreateBuses( [((hier,name+'_rdy',),) , ((hier,name+'_ack',),) ])
        return [self.rdy , self.ack]
class OneWireBus ( ProtoCreateBus): 
    def __init__(self, *args, clk , side = 'master' , **kwargs):
        protoCallback = OneWire.Master if side == 'master' else OneWire.Slave
        self.ArgParse(protoCallback, self.PortParse, *args , clk=clk , **kwargs)
        self.SideChoose(side)
    def PortParse(self,name,hier=''):
        self.dval = CreateBus( (hier,name+'_dval',))
        return [self.dval]
class NicoAhbBus( ProtoCreateBus):
    def __init__(self, *args, clk , side = 'master' , **kwargs):
        protoCallback = Ahb.Master  
        self.ArgParse(protoCallback, self.PortParse, *args , clk=clk , **kwargs)
        #self.SideChoose(side)
    def PortParse(self,name,hier=''):
        self.hsel = CreateBus( (hier,name+'_hsel',))
        self.haddr = CreateBus( (hier,name+'_haddr',))
        self.hwrite = CreateBus( (hier,name+'_hwrite',))
        self.htrans = CreateBus( (hier,name+'_htrans',))
        self.hsize = CreateBus( (hier,name+'_hsize',))
        self.hburst = CreateBus( (hier,name+'_hburst',))
        self.hready = CreateBus( (hier,name+'_hready',))
        self.hresp = CreateBus( (hier,name+'_hresp',))
        self.hrdata = CreateBus( (hier,name+'_hrdata',))
        self.hwdata = CreateBus( (hier,name+'_hwdata',))
        return [self.hsel, self.haddr, self,hwrite, self.htrans, self.hsize,\
                self.hburst, self.hready, self.hresp, self.hready ]
class MySlaveTwoWire(TwoWire.Slave):
    def __init__(
            self, rdy: Bus, ack: Bus, data: Bus,
            clk: int, A=1, B=5, callbacks=list()
    ):
        super(TwoWire.Slave, self).__init__(callbacks)
        self.rdy = GetBus(rdy)
        self.ack = GetBus(ack)
        self.data = GetBus(data)
        self.clk = GetEvent(clk)
        self.A = A
        self.B = B
        self.ack.value[0] = RandProb(self.A, self.B)
        self.ack.Write()
    def MyMonitor(self,n):
        for i in range(n):
            while True:
                self.ack.value[0] = RandProb(self.A, self.B) and self.rdy.value[0]
                self.ack.Write()            
                yield self.clk
                self.rdy.Read()
                if self.rdy.x[0] != 0 or self.rdy.value[0] == 0:
                    continue
                if self.ack.value[0] != 0:
                    self.data.Read()
                    super(TwoWire.Slave, self).Get(self.data)
                    break
        print( "monitor done")
        self.ack.value[0]=0
        self.ack.Write()
        yield self.clk

import site, sys
sys.path.insert(0,'/home/enhoshen/.local/lib/python3.7/site-packages')
print(sys.path)
# sys.path.append(site.USER_SITE)
import numpy as np
from Datagen import *
from SVparse import SVparse
from itertools import repeat
from nicotb import *
from nicotb.primitives import JoinableFork
from NicoUtil import *
import os
def RdyAckInit(bus,name):
    return TwoWireBus( bus, clk=ck_ev , A=2, name=name)
def DataBusInit(name,dim):
    return CreateBus( (('',name,dim,),) )
def test():
     
    inrbus = RdyAckInit(DataBusInit('i_Input',(1,)) , 'r_Input') 
    wrbus = RdyAckInit(DataBusInit('i_Weight',(1,)) , 'r_Weight') 
    grbus = RdyAckInit(DataBusInit('i_GB',(2,)) , 'r_GB') 
    iwbus = RdyAckInit(DataBusInit('o_Input',(1,)) , 'w_Input') 
    wwbus = RdyAckInit(DataBusInit('o_Weight',(1,)) , 'w_Weight') 
    gwbus = RdyAckInit(DataBusInit('o_GB',(2,)) , 'w_GB') 
    conf = AlexBest[4]
    c=conf
    process_cycle = c.B * c.Tm * c.Th * c.Tw * c.S * c.S * c.Pch * c.Xb * c.Wb//256  
    ir  ,  iw ,  wr ,  ww ,  gr ,  gw = BufData(c,1)
    j=[]
    for it,bus in zip( *[[ir , iw , wr, ww, gr, gw],[inrbus,iwbus,wrbus,wwbus,grbus,gwbus]]):
        j.append(JoinableFork (bus.SendIter(it(bus.data)) )  ) 
    for jj in j:
        yield from jj.Join() 
    for i in range(c.Pch*c.Pm*c.R*c.Tw*c.Xb):
        yield ck_ev
    [jj.Destroy() for jj in j]
    FinishSim()
    
rst_out , ck_ev = CreateEvents(["rst_out","ck_ev"])
RegisterCoroutines(
    [test()]

)
 

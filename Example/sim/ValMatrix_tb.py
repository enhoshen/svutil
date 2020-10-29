
from nicotb import *
import numpy as np 

import sys
import os
sys.path.append(os.environ.get('SVutil'))
sys.path.append(os.environ.get('PROJECT_PATH')+'/sim')
from itertools import repeat
from nicotb.primitives import JoinableFork
from SVutil.SVparse import SVparse,EAdict
from SVutil.sim.NicoUtil import *

TEST_CFG= os.environ.get('TEST_CFG',None)
Nico = NicoUtil() 

def BusInit():
    #Nico.SBC.TopTypes()
    #Nico.SBC.AllTypes()
    dic = {}
    dic['test_sig'] = Nico.SBC.Get('signed logic', 'test_sig', dim=Nico.DutPortDim('test_sig'))
    dic['happy']    = CreateBus(( ('', 'happy'    , Nico.DutPortDim('happy'   ),),  ))
    dic['fuck']     = CreateBus(( ('', 'fuck'     , Nico.DutPortDim('fuck'    ),),  ))
    dic['shooshoo'] = Nico.SBC.Get('type1'       , 'shooshoo', dim=Nico.DutPortDim('shooshoo'))
    dic['booboo']   = CreateBus(( ('', 'booboo'   , Nico.DutPortDim('booboo'  ),),  ))
    dic['papa']     = CreateBus(( ('', 'papa'     , Nico.DutPortDim('papa'    ),),  ))
    Nico.print(Nico.DutPortDim('onebit'))
    dic['onebit'] = Nico.SBC.Get('logic'       , 'onebit', dim=Nico.DutPortDim('onebit'))
    return Busdict(dic) # access by name without quotes

def main():
    buses = BusInit()
    buses.SetToN()
    buses.Write() #don't use this afterward if you're not sure what you're doing
    yield rst_out
    #j = []
    #for jj in j:
    #    yield from jj.Join()
    #[jj.Destroy() for jj in j]
    FinishSim()
rst_out, ck_ev = CreateEvents(["rst_out", "ck_ev"])
intr_ev, init_ev, resp_ev, fin_ev, sim_stop_ev, sim_pass_ev, time_out_ev = CreateEvents(["intr_ev", "init_ev", "resp_ev", "fin_ev", "sim_stop_ev", "sim_pass_ev", "time_out_ev"])

RegisterCoroutines([
    main()
])

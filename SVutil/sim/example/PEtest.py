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
def BusInit():
    SBC = StructBusCreator
    SBC.TopTypes()
    confbus = SBC.Get('Conf','i_PEconf')
    instbus = SBC.Get('Inst','i_PEinst')
    status = SBC.Get('DPstatus','o_status' )
    dummy = CreateBus( ('dummy',) )
    return confbus , instbus , status,dummy
def PErdyack(data):
    inbus = TwoWireBus( data[0],clk=ck_ev ,A=5,name='Input' )
    wbus = TwoWireBus ( data[1],clk=ck_ev ,A=5,name='Weight') 
    obus = TwoWireBus ( data[2],clk=ck_ev ,side='slave',A=5,name='POUT')
    lpebus = TwoWireBus ( data[3],clk=ck_ev ,A=5,name='LPE')
    return inbus , wbus , obus , lpebus
    #TODO LPE data and bus
def DataBusInit():
    Input , Weight , Psum , Psum_lpe= CreateBuses([
        (('','i_Input',(1,)) ,),
        ((None,'i_Weight',(16,)) ,),
        ((None,'o_Psum', (16,))  ,),
        ((None,'i_Psum_LPE', (16,)),)
    ])
    return Input , Weight , Psum , Psum_lpe
    #TODO LPE data and bus
def test():
    yield rst_out
    conf ,inst ,status,dummy = BusInit()
    data = DataBusInit()
    
    inbus , wbus ,obus ,lpebus= PErdyack(data)
    print(inbus.data.values)
    SVparse.hiers['PE'].ShowPorts
    conf.SetTo(0)
    inst.SetTo(0)
    layer=AlexBest[4]
    peconf=layer.ToPEconf() 
    print(peconf)
    config = [ (  4,4,4,1,1,3,3, 48,12,13*4,4,1,2,1   ,0,0,1,0,13),\
                (  4,2,3,1,1,3,3, 24,12,13*2,4,1,3,2,0,0,2,1,13),\
                 (  1,2,3,1,3,3,3, 6,3,13*2,3,0,3,2,0,0,2,1,13)  ]
    def it(i):
        for _ in range(i):
            yield dummy.value
    def lpedata(i,bus):
        print(type(bus))
        for _ in range(i):
            for j in range(16):
                arr = np.random.randint(np.iinfo(np.int32).max,size=(16),dtype=np.int32 )
                bus.value[j] = arr[j] 
            yield bus.values
    inst.reset.value =1
    inst.Write()
    yield ck_ev
    yield ck_ev
    inst.reset.value =0
    inst.start.value =1
    inst.dval.value =1
    inst.Write()
    yield ck_ev
    inst.reset.value =0
    inst.start.value =0
    inst.Write()
    conf.values =peconf
    conf.Au.value=4
    conf.Write()
    print(layer)
    print (conf)
    for iteration  in range ( layer.PEpass): 
        print ('iteration:',iteration)
        s = conf.S.value[0]
        r = conf.R.value[0]
        pm = conf.Pm.value[0]
        pch = conf.Pch.value[0]
        tw = conf.Tw.value[0]
        tw_padded = tw+r-1
        xb=conf.Xb.value[0]
        wb=conf.Wb.value[0]
        upix = conf.Upix.value[0]
        j = []
        ab = 1 if conf.Au.value[0] == 0 else 2**(conf.Au.value[0]-1)
        Input = InputData(layer.Pch,(layer.Tw*layer.U)-layer.U+layer.R,layer.S  , layer.Xb , layer.Ab ,1.3)
        Weight = WeightData(layer.Pch,layer.R ,layer.Pm ,layer.S ,layer.Wb ,layer.Ab , 1.3)
        if conf.PixReuse.value[0] == 1:
            j.append( JoinableFork( inbus.SendIter( Input[3](inbus.data) ) ) )
            #j.append( JoinableFork(inbus.SendIter(it(pch*tw*xb*s)))   )
            j.append( JoinableFork( wbus.SendIter(Weight[3](wbus.data)) ) )
            j.append( JoinableFork( lpebus.SendIter(lpedata(layer.Tw*layer.Pm,lpebus.data))) )
            #j.append( JoinableFork( wbus.SendIter(it(pm*pch*r*s)) ) )
            #j.append( JoinableFork( obus.MyMonitor(tw*xb*s*pm*pch*r) ) )
        else:
            j.append( JoinableFork( inbus.SendIter(it(xb*tw*upix*s)) ) )
            j.append( JoinableFork( wbus.SendIter(it(pm*pch*r*s)) ) )
            j.append( JoinableFork( obus.MyMonitor(tw*xb*s*pm*pch*r) ) )
        
        for jj in j:
            yield from jj.Join() 
        [jj.Destroy() for jj in j]
        while True:
            yield ck_ev
            status.Read()
            if status.confEnd.value[0]:
                print ( "confEnd")
                inst.next.value=1
                inst.Write()
                yield ck_ev
                inst.next.value=0
                inst.Write()
                break         
    #yield from repeat(ck_ev,100)
    FinishSim()

rst_out , ck_ev = CreateEvents(["rst_out","ck_ev"])
RegisterCoroutines(
    [test()]

)
 

from nicotb import *
from SVparse import *
from SVclass import *
from SVsim   import *
import os
import itertools
import numpy as np
from nicotb.utils import RandProb
 
class StructBus():
    "name , bw , dim , type , enum literals"
    def __init__ (self, structName,signalName,attrs, buses):
        self.structName= structName
        self.signalName= signalName
        self.attrs = attrs
        self.namelist = {v[0]:i for i,v in enumerate(self.attrs)}
        self.buses = buses
    def __getitem__(self,i):
        return self.buses[i]
    @property
    def values(self):
        return [ x.values if isinstance(x,StructBus) else x.values[0] for x in self.buses]
    @values.setter
    def values(self, v):
        for bb,vv in zip(self.buses,v):
            try:
                bb.values = vv
            except:
                bb.value = vv
    @property
    def value(self):
        return self.buses[0]._vs[0]
    @value.setter
    def value(self,v):
        self.buses[0].signals[0].value = v
    def SetToZ(self):
        [ x.SetToZ() for x in self.buses ]
    def SetToX(self):
        [ x.SetToX() for x in self.buses ]
    def SetToN(self):
        [ x.SetToN() if isinstance(x,StructBus) else [s._x.fill(0) for s in x.signals]  for x in self.buses]
    def SetTo(self,n):
        self.SetToN()
        [ x.SetTo(n) if isinstance(x,StructBus) else [s._value.fill(n) for s in x.signals] for x in self.buses ]
    #def Write(self, imm=False):
    #    [ x.Write(imm) for x in self.buses ]
    def Write(self, *lst, imm=False ):
        if not lst:
            [ x.Write(imm=imm) for x in self.buses ]
        else:
            if len(lst)==1 and type(lst[0])==list:
                [ self.buses[self.namelist[x]].Write(imm=imm) for x in lst[0] ]
            else:
                [ self.buses[self.namelist[x]].Write(imm=imm) for x in lst ]
    def Read(self):
        [ x.Read() for x in self.buses ]
    #TODO *arg setter
    def __setitem__(self, k , v):
        i = self.namelist[k]
        for x in v:
            self.buses[i].value = x
    def __getattr__(self,k):
        return self.buses[self.namelist[k]]
    def __repr__(self,indent=13,top=True):
        w=13
        s=''
        if top:
            s=f'{self.signalName:=^{3*w}}\n'
        for a,v,b in zip(self.attrs,self.values,self.buses):
            if isinstance(b,StructBus):
                s+=f'{a[0]:<{w}}\n'
                s+=b.__repr__(indent+13,False)
            else:
                s+=f'{"":<{indent-13}}'f'{a[0]:<{w}}'f'{list(v) if len(a)!=5 else [a[4][i] for i in v] !r:<{w}}\n'
        return s 
class StructBusCreator():
    structlist = {}
    def __init__ ( self, structName , attrs):
        if attrs:
            for memb in attrs:
                assert self.structlist.get(memb[3] ) != None , f"can't find type {memb[3]}; \
                                                            \n  (1)change the declartion of the type/import\
                                                            \n  (2)probably use StructBusCreator.AllTypes()?"
        if self.structlist.get(structName) == None:
            self.structlist[structName] = self
        self.structName = structName
        self.attrs = attrs
    @classmethod
    def FileParse(cls,paths=None):
        ''' deprecated '''
        S = SVparseSession()
        S.FileParse(paths)
        return S
    @classmethod
    def BasicTypes(cls):
        StructBusCreator('logic',None)
        StructBusCreator('enum',None)
    @classmethod
    def AllTypes(cls):
        cls.Reset()
        cls.BasicTypes()
        S = cls.FileParse()
        for h in SVparse.hiers.values():
            for k,v in h.types.items():
                StructBusCreator(k,v)
        return S
    @classmethod
    def TopTypes(cls):
        cls.Reset()
        cls.BasicTypes()
        S = cls.FileParse( (False,TOPSV) )
        for T in SVparse.hiers[TOPMODULE].Types: # TOPMODULE defined in SVparse
            for k,v in T.items():
                StructBusCreator(k,v)
        return S
    @classmethod
    def Get(cls,t,name,hier='',dim=()):
        if dim == ():
            return cls.structlist[t].CreateStructBus(name,hier,dim)
        else:
            return cls.structlist[t].MDACreateStructBus(name,hier,dim)
    @classmethod
    def Reset(cls):
        cls.structlist = {}
    def CreateStructBus (self, signalName , hier='',DIM=() ):
        #buses = {'logic' :  CreateBus( self.createTuple(signalName) )}
        buses = []
        attrs = self.structlist[self.structName].attrs
        if not attrs:
            return  CreateBus( ((hier, signalName, DIM),) ) 
        else:
            for  n , bw, dim ,t ,*_ in attrs :
                if t=='logic':
                    buses.append ( CreateBus( ((hier, signalName+'.'+n ,DIM+dim),) ) )
                elif t == 'enum':
                    buses.append ( CreateBus( ((hier, signalName , DIM+dim ),) ) )
                else:
                    buses.append ( self.structlist[t].CreateStructBus( signalName+'.'+n , hier, DIM+dim ) )
        return StructBus(self.structName,signalName,attrs,buses)
    def MDACreateStructBus ( self, signalName, hier='', DIM=()):
        buses = []
        if DIM == ():
            return self.CreateStructBus(signalName,hier,DIM)
        else:
            for d in range(DIM[0]):
                buses.append( self.MDACreateStructBus(signalName+f'[{d}]', hier, DIM[1:])  )
            return buses
class Busdict (EAdict):
    def Flatten(self, lst):
        return self.Flatten(lst[0]) + (self.Flatten(lst[1:]) if len(lst) > 1 else []) if type(lst) == list else [lst]
    def Read(self):
        [ [i.Read() for i in self.Flatten(x)] if type(x) == list\
         else x.Read() for x in self.dic.values() ]
    def Write(self, *lst, imm=False, ):
        if not lst:
            [ [i.Write(imm=imm) for i in self.Flatten(x)] if type(x) == list\
                else x.Write(imm=imm) for x in self.dic.values() ]
        else:
            if len(lst)==1 and type(lst[0])==list:
                [ [i.Write(imm=imm) for i in self.Flatten(self.dic[x])] if type(self.dic[x]) == list\
                    else  self.dic[x].Write(imm=imm) for x in lst[0] ]
            else:
                [ [i.Write(imm=imm) for i in self.Flatten(self.dic[x])] if type(self.dic[x]) == list\
                    else  self.dic[x].Write(imm=imm) for x in lst ]
    def IsSB(self,x):
        return isinstance(x,StructBus)
    def SetToN(self):
        bussettoN = lambda x: [s._x.fill(0) for s in x.signals]
        [ [i.SetToN() if self.IsSB(i) else bussettoN(i) for i in self.Flatten(x)] if type(x) == list\
            else  x.SetToN() if self.IsSB(x) else bussettoN(x)  for x in self.dic.values()]
    def SetTo(self,n):
        busfill = lambda x: [s._value.fill(n) for s in x.signals]
        self.SetToN()
        [ [i.SetTo(n) if self.IsSB(i) else busfill(i) for i in self.Flatten(x)] if type(x) == list\
            else  x.SetTo(n) if self.IsSB(x) else busfill(x) for x in self.dic.values() ]
class RegbkMaster(SVutil):
    ''' Wrapper for register bank controller '''
    def __init__ (self, regbk:SVRegbk, addr:Bus, write:Bus, wdata:Bus, rdata:Bus, master=None):
        self.verbose = 1
        self.master = master 
        self.regbk = regbk
        self.addr = addr
        self.write= write 
        self.wdata= wdata
        self.rdata= rdata
        from nicotb.protocol import TwoWire
        from nicotb.protocol import OneWire 
        from protocol import Apb
        self.proto_it_dict = { 
                TwoWire.Master: self.RegWriteAddrIt,\
                OneWire.Master: self.RegWriteAddrIt,\
                Apb.Master: self.RegWriteIt
            }
    def Write(self):
        self.addr.Write()
        self.rw.Write()
        self.wdata.Write()        
    def Read(self):
        self.rdata.Read()
    def SendIter(self, regseq, rwseq, dataseq):
        assert self.master, "Specify the protocol master"
        it = self.proto_it_dict[type(self.master)]
        yield from self.master.SendIter(it(regseq, rwseq, dataseq))
    def RegWriteIt (self, regseq, rwseq, dataseq):
        '''
            Generate an iterable to loop through a sequence of register bank's
            address, read/write, and data.
            Args:
                regseq: list of register name string
                rwseq : list of read/write, 1 for write, 0 for read.
                dataseq: list of data. Data can be either integer or list 
                    of integer if the register has underlying register fields.
                    SVRegbk.regwrite will handle the data compaction for you.
                #TODO: string data of parsed parameters that can be converted
                    SVRegbk
        '''
        w = 15 
        for reg, rw, data in zip (regseq, rwseq, dataseq):
            addr, wdata, regfields = self.regbk.RegWrite(reg, data)
            w = max(w, len(reg))
            self.print('register bank access:', f'{reg:<{w}} {addr:<5}', hex(self.wdata.value[0]), regfields, data, verbose=1)
            yield (addr, wdata, rw)
    def RegWriteAddrIt (self, regseq, rwseq, dataseq):
        '''
            Used by nico protocol SendIter() thread with single data. This thread is 
            a workaround by yield the address and manually Write() data and write buses.
            That is, the corresponding protocol bus' data is the address bus.
            Ex: regbus = TwoWire.Master(buses.i_req, buses.o_ack, buses.i_addr, ck_ev)
                ...
                regbus.SendIter(RegbkMasterObjec.RegwriteAddrIt(regseq, rwseq, dataseq))
        '''
        for addr, wdata, rw in self.RegWriteIt(regseq, rwseq, dataseq):
            self.write.value = rw 
            self.addr.value = addr 
            self.write.Write()
            self.addr.Write()
            yield addr.value
            if not rw:
                self.Read()
                self.print('register bank read: ', hex(addr), ':', hex(self.rdata.value[0]), verbose=1, trace=None)
class ThreadCreator(SVutil):
    ''' Helper class for creating simulation threads. '''
    def __init__(self, ck_ev):
        self.ck_ev = ck_ev 
        #self.init_ev  = init_ev  
        #self.resp_ev  = resp_ev  
        #self.fin_ev   = fin_ev   
        #self.intr_ev  = intr_ev  
    def Phse3Send(self, cfg):
        yield from INITS[cfg]()
        yield from RESPS[cfg]()
        yield from FINS [cfg]()
        self.print('Sim done')
    
class NicoUtil(PYUtil):
    def __init__(self):
        self.SBC = StructBusCreator
        s = self.SBC.TopTypes()
        self.session = s
        super().__init__()
        self.test = TEST
        self.testname = TEST.rsplit('_tb')[0]
        self.fsdbname = self.testname + '_tb' #TODO
        self.topfile  = SV.rstrip('.sv')
        self.incfile  = INC
        self.dutname = TESTMODULE 
        self.dut = self.session.hiers.get(self.dutname)
        self.top = self.session.hiers.get(TOPMODULE)
        self.dutfile = self.session.hiers.get(self.dutname+'_sv')
    def TopTypes(self):
        self.session = self.SBC.TopTypes()
    def AllTypes(self):
        self.session = self.SBC.AllTypes()
    def Macro2num (self, s):
        _s = s 
        _s = SVstr(_s).MultiMacroExpand(self.top.AllMacro)
        _s = SVstr(_s).S2num(self.top.Params) 
        reobj = True
        while reobj:
            if type(_s) == int:
                break
            reobj = re.search(r'`(\w+)\b', _s)
            if reobj:    
                _s = SVstr(_s).MultiMacroExpand(self.top.AllMacro)
                _s = SVstr(_s).S2num(self.top.Params) 
        return _s 
    @property
    def DutPorts(self):
        return {  i:SVPort(v)for i,v in self.dut.Portsdic.items()}
    def DutPortDim(self, p):
        ''' Find the port dimension based on the port name from dut module specified by TESTMODULE '''
        d = self.DutPorts[p].dimstrtuple
        return self.Tuple2num(d)
    def Tuple2num(self, t):
        return tuple(map(lambda x : self.Macro2num(x),t))
global ck_ev
def clk_cnt():

    global n_clk
    while(1):
        yield ck_ev
        n_clk+=1    
if __name__=='__main__':
    n = NicoUtil()

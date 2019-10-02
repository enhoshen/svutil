from nicotb import *
from SVparse import *
import os
import itertools
import numpy as np
from nicotb.protocol import TwoWire
from nicotb.protocol import OneWire 
from nicotb.utils import RandProb
class StructBus:
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
    def Write(self):
        [ x.Write() for x in self.buses ]
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
    structlist = {'logic':[],'enum':[]}
    def __init__ ( self, structName , attrs):
        for memb in attrs:
            assert self.structlist.get(memb[3] ) != None , "change the declaration order"
        if self.structlist.get(structName) == None:
            self.structlist[structName] = self
        self.structName = structName
        self.attrs = attrs
    @classmethod
    def Alltypes(cls):
        FileParse()
        for h in SVparse.hiers.values():
            for k,v in h.types.items():
                StructBusCreator(k,v)
    @classmethod
    def TopTypes(cls):
        FileParse( (False,TOPSV) )
        for T in SVparse.hiers[TOPMODULE].Types: # TOPMODULE defined in SVparse
            for k,v in T.items():
                StructBusCreator(k,v)
    @classmethod
    def Get(cls,i,name,hier=''):
        return cls.structlist[i].CreateStructBus(name,hier)
    def CreateStructBus (self, signalName , hier='',DIM=() ):
        #buses = {'logic' :  CreateBus( self.createTuple(signalName) )}
        buses = []
        attrs = self.structlist[self.structName].attrs
        for  n , bw, dim ,t ,*_ in attrs :
            
            if t=='logic':
                buses.append ( CreateBus( ((hier, signalName+'.'+n ,DIM+dim),) ) )
            elif t == 'enum':
                buses.append ( CreateBus( ((hier, signalName , DIM+dim ),) ) )
            else:
                buses.append ( self.structlist[t].CreateStructBus( signalName+'.'+n , hier, DIM+dim ) )
        return StructBus(self.structName,signalName,attrs,buses)
global ck_ev
class ProtoCreateBus ():
    # this class member functions help createbuses, if you've already connected buses, 
    # ArgParse is not needed
    def __init__(self):
        pass
    def ArgParse(self, protoCallback, portCallback,*args , clk  , **kwargs):
        # args[0] is the data bus, it could be a list, ex: [hrdata,hwdata] in AHB
        # portCallback should return list of buses for protocl buses
        # protoCallback should create the protocal object, ex: TwoWire.Master
        # see NicoProtocol inherited protobus classes
        kw = dict(kwargs)
        if len(args) == 0:
            self.data = kw['data'] 
        else:
            self.data = args[0]

        if len(args)==1:
            protolist =  portCallback( kw['name'] , hier=kw['hier']) if kw.get('hier') else portCallback(kw['name'])  
            kw.pop('name')
            if kw.get('hier'):
                kw.pop('hier')
            datalist = self.data if type(self.data) == list else [self.data] 
            self.proto = protoCallback( *(protolist),*datalist ,clk=clk ,**kw)
        else:
            self.proto = protoCallback( *args , clk=clk ,**kw)
    def SideChoose (self, side='master'):
        if side == 'master':
            self.master = self.proto
            return
        if side == 'slave':
            self.slave = self.proto
            return
    def SendIter(self,it):
        yield from self.master.SendIter(it)
    def Monitor(self):
        yield from self.slave.Monitor()
    def MyMonitor(self,n):
        yield from self.slave.MyMonitor(n)
    @property
    def Data(self):
        return self.data
    @Data.setter
    def Data(self,data):
        self.proto.data = GetBus(data)
    @property
    def values(self):
        return [ x.values for x in self.data]
class Busdict (EAdict):
    def Read(self):
        [ i.Read() for i in self.dic.values() ]
    def Write(self):
        [ i.Write() for i in self.dic.values() ]
    def SetTo(self,n):
        [ i.SetToN() for i in self.dic.values() ]
        [ i.SetTo(n) for i in self.dic.values() ]
def clk_cnt():

    global n_clk
    while(1):
        yield ck_ev
        n_clk+=1    
if __name__=='__main__':
    ParseFirstArgument()

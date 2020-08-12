from nicotb import *
from SVparse import *
from SVclass import *
from SVsim   import *
import colorama
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
        '''
            Apply Write() on the elements
            if lst is not provided, write every elements
            lst could be a list of bus names,
            or it could be seperated arguments of bus names.
            Ex: Write('a','b') equals Write(['a','b'])
        '''
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
        n = self.namelist.get(k)
        return self.buses[n] if n is not None else None
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
    def FileParse(cls,paths=None, inc=True, inclvl=-1):
        S = SVparseSession()
        S.FileParse(paths=paths, inc=inc, inclvl=inclvl)
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
    def TopTypes(cls, inclvl=-1):
        cls.Reset()
        cls.BasicTypes()
        S = cls.FileParse(paths=[GBV.TOPSV], inc=False, inclvl=inclvl)
        for T in SVparse.hiers[GBV.TOPMODULE].Types: # TOPMODULE defined in SVparse
            for k,v in T.items():
                StructBusCreator(k,v)
        return S
    @classmethod
    def Get(cls,t,name,hier='',dim=(),dtype=np.int32):
        if '::' in t:
            _pkg , _type= t.split('::')
            tp = SVparse.package[_pkg].types[_type] 
            StructBusCreator(t,tp)
        if dim == ():
            return cls.structlist[t].CreateStructBus(name,hier,dim, dtype=dtype)
        else:
            return cls.structlist[t].MDACreateStructBus(name,hier,dim, dtype=dtype)
    @classmethod
    def Reset(cls):
        cls.structlist = {}
    def CreateStructBus (self, signalName , hier='',DIM=(), dtype=None ):
        #buses = {'logic' :  CreateBus( self.createTuple(signalName) )}
        buses = []
        attrs = self.structlist[self.structName].attrs
        if not attrs:
            return  CreateBus( ((hier, signalName, DIM, dtype),) ) 
        else:
            for  n , bw, dim ,t ,*_ in attrs :
                if t=='logic':
                    buses.append ( CreateBus( ((hier, signalName+'.'+n ,DIM+dim, dtype),) ) )
                elif t == 'enum':
                    buses.append ( CreateBus( ((hier, signalName , DIM+dim, dtype),) ) )
                else:
                    buses.append ( self.structlist[t].CreateStructBus( signalName+'.'+n , hier, DIM+dim, dtype) )
        return StructBus(self.structName,signalName,attrs,buses)
    def MDACreateStructBus ( self, signalName, hier='', DIM=(), dtype=None):
        buses = []
        if DIM == ():
            return self.CreateStructBus(signalName,hier,DIM, dtype=dtype)
        else:
            for d in range(DIM[0]):
                buses.append( self.MDACreateStructBus(signalName+f'[{d}]', hier, DIM[1:], dtype=dtype)  )
            return buses
class Busdict (EAdict):
    def Flatten(self, lst):
        return self.Flatten(lst[0]) + (self.Flatten(lst[1:]) if len(lst) > 1 else []) if type(lst) == list else [lst]
    def Read(self, *lst):
        if not lst:
            [ [i.Read() for i in self.Flatten(x)] if type(x) == list\
             else x.Read() for x in self.dic.values() ]
        else:
            if len(lst)==1 and type(lst[0])==list:
                [ [i.Read() for i in self.Flatten(x)] if type(x) == list\
                 else self.dic[x].Read() for x in lst[0]]
            else:
                [ [i.Read() for i in self.Flatten(x)] if type(x) == list\
                 else self.dic[x].Read() for x in lst ]
    def Write(self, *lst, imm=False ):
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
    def __init__ (self, regbk:SVRegbk, addr:Bus = None, write:Bus = None, wdata:Bus = None, rdata:Bus = None, master=None):
        self.verbose = V_(VERBOSE) 
        self.master = master 
        self.regbk = regbk
        self.addr = addr
        self.write= write 
        self.wdata= wdata
        self.rdata= rdata
        from nicotb.protocol import TwoWire
        from nicotb.protocol import OneWire 
        from protocol import Apb
        from protocol import Ahb
        self.proto_it_dict = { 
             TwoWire.Master: self.RegWriteAddrIt
            ,OneWire.Master: self.RegWriteAddrIt
            ,Apb.Master: self.RegWriteIt
            ,Ahb.Master: self.AhbRegWriteIt}
        self.ac= f'{colorama.Fore.YELLOW}' # attribute color
        self.cr= f'{colorama.Style.RESET_ALL}' # color reset
        self.regfieldfmt = lambda f, endl=f'\n{"":>8}': f'{endl}{self.ac}Reg fields: {self.cr}{f.__str__()}{endl}' if f else '' 
        self.addrfmt = lambda addr: f'{self.ac}Address:{self.cr} {addr.__str__():<5}'
        self.regfmt  = lambda reg, offset, rw, w: f'{self.ac}Register bank {"write" if rw else "read":>5}:{self.cr}{reg.__str__()+offset.__str__():<{w}}'
        self.rdfmt  = f'{self.ac}Read data: {self.cr}'
        self.rdatafmt = lambda rdata : rdata.__str__()
        self.readfmt = lambda reg, offset, addr, dlst, regfields, w:\
                            f'{self.regfmt(reg, offset, False, w)} {self.addrfmt(addr)}{self.rdfmt+self.rdatafmt(dlst):<5} {self.regfieldfmt(regfields)}'
        self.wrfmt = f'{self.ac}Written: {self.cr}'
        self.wdatafmt = lambda wdata: hex(wdata)
        self.wrorigfmt = f'{self.ac}Original: {self.cr}'
        self.wdataorigfmt = lambda data: data.__str__()
        self.writefmt = lambda reg, rw,  offset, addr, wdata, regfields, data, w:\
                            f'{self.regfmt(reg, offset, rw, w)} {self.addrfmt(addr)}{self.wrfmt}{self.wdatafmt(wdata):>10} '\
                            + f'{self.regfieldfmt(regfields)}{self.wrorigfmt}{self.wdataorigfmt(data)}' 
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
    def IssueCommands(self, regseq, rwseq, dataseq):
        it = self.proto_it_dict[type(self.master)]
        yield from self.master.IssueCommands(it(regseq, rwseq, dataseq))
    def RegWriteIt (self, regseq, rwseq, dataseq):
        '''
            Generate an iterable to loop through a sequence of register bank's
            address, read/write, and data.
            Args:
                regseq: list of 
                        (1)register name string, or 
                        (2)the integer address offset, or
                        (3)even a tuple of (register name, offset) representing an
                        offset starting from the register 
                rwseq : list of read/write, 1 for write, 0 for read.
                dataseq: list of data. Data can be either integer or list 
                    of integer if the register has underlying register fields.
                    SVRegbk.regwrite will handle the data compaction for you. If 
                    the reg is a integer address offset, the regfield can't be
                    retrieved, so the data must a compacted integer generated by
                    yourself.
                #TODO: string data of parsed parameters that can be converted
                    SVRegbk
        '''
        w = 15 
        orig_cb = self.master.callbacks
        for reg, rw, data in itertools.zip_longest (regseq, rwseq, dataseq, fillvalue=0):
            offset = ''
            if type(reg) == int:
                assert type(data)==int, "raw register address offset only takes integer data"
                addr, wdata, regfields = reg, data, 'undefined regfields' 
            elif type(reg) == tuple:
                addr, wdata, regfields = self.regbk.RegWrite(reg[0], data)
                offset =reg[1] * self.regbk.regbsize
                addr += offset 
                offset = f'+{offset}'
                reg = reg[0]
                w = max(w, len(reg+offset))
            elif type(reg) == str:
                addr, wdata, regfields = self.regbk.RegWrite(reg, data)
                w = max(w, len(reg))
            else:
                raise TypeError('un-recognized register sequence type')
            def MsgCb(_):
                if not rw:
                    self.Read()
                    dlst, rf= self.regbk.RegRead(reg, self.rdata.value[0])
                    self.print( self.readfmt(reg, offset, addr,  dlst, rf, w)
                        ,verbose=1
                        ,trace=2
                        ,level=True)
                else:
                    self.print(self.writefmt(reg, rw,  offset, addr, wdata, regfields, data, w)
                        ,verbose=1
                        ,trace=2
                        ,level=True)
            try:
                if self.verbose >= 1:
                    self.msgcb = MsgCb
                else:
                    self.msgcb = lambda _:None 
            except:
                self.msgcb = lambda _:None 
            self.master.callbacks = [MsgCb] + orig_cb
            yield (addr, wdata, rw)
            self.master.callbacks = orig_cb
    def RegWriteAddrIt (self, regseq, rwseq, dataseq):
        '''
            Used by nico protocol SendIter() thread without addr bus. This thread is 
            a workaround by yielding the address and manually Write() data and write buses.
            That is, the corresponding protocol bus' data is the address bus.
            Ex: regbus = TwoWire.Master(buses.i_req, buses.o_ack, buses.i_addr, ck_ev)
                ...
                regbus.SendIter(RegbkMasterObjec.RegwriteAddrIt(regseq, rwseq, dataseq))
        '''
        for addr, wdata, rw in self.RegWriteIt(regseq, rwseq, dataseq):
            self.write.value = rw 
            self.addr.value = addr 
            self.wdata.value = wdata
            self.write.Write()
            self.wdata.Write()
            yield self.addr.value
    def AhbRegWriteIt ( self, regseq, rwseq, dataseq):
        for addr, wdata, rw in self.RegWriteIt(regseq, rwseq, dataseq):
            yield (rw, addr, wdata)
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
        self.print('Sim done', trace=3)
class EventTrigger(SVutil):
    ''' Helper class for triggering a python event at the same time write to a nicotb bus '''
    # TODO
    def __init__(self, ck_ev=None, clk_cnt=None, pulse_width=None):
        self.V_(VERBOSE)
        self.clk = ck_ev
        self.clk_cnt = clk_cnt
        self.pulse_width = pulse_width
        self.sim_pass_ev = None
        self.sim_stop_ev = None
        self.time_out_ev = None
        self.sig_trig_type = {'LEVEL':self.SVSigTriggerLevel, 'Edge': self.SVSigTriggerEdge, 'Pulse': self.SVSigTriggerPulse}
        pass
    def RegEvents(self, sim_pass_ev, sim_stop_ev, time_out_ev):
        self.sim_pass_ev = sim_pass_ev
        self.sim_stop_ev = sim_stop_ev
        self.time_out_ev = time_out_ev
    def Trigger(self, ev_name, sig_name=None, trig_type='LEVEL', high=True):
        ''' 
            Trigger ev_name in python and sig_name(optional) in verilog 
                ev_name: an integer event created by CreateEvent/CreateEvents or event name's string
                sig_name: signal string name
        '''
        self.PYEVTrigger(ev_name)
        if sig_name:
            Fork(self.sig_trig_type[trig_type](sig_name, high))
    def Triggers(self, ev_tuples, trig_type='LEVEL', high=True):
        ''' Trigger each of the event pairs in ev_tuples '''
        for ev, sig in ev_tuples:
            self.Trigger(ev, sig, trig_type, high)
    def PYEVTrigger(self, name):
        ev = GetEvent(name)
        SignalEvent(ev)
    def SVSigTriggerLevel(self, name, high=True):
        ev_bus = CreateBus((name,))
        ev_bus.value[0] = 1 if high else 0
        ev_bus.Write()
        yield self.clk
        self.print( f'Event bus {name} level triggered', trace=3)
    def SVSigTriggerEdge(self, name, high=True):
        ev_bus = CreateBus((name,))
        ev_bus.value[0] = 1 if high else 0
        ev_bus.Write()
        yield self.clk
        self.print( f'Event bus {name} edge triggered', trace=3)
        ev_bus.value[0] = 0
        ev_bus.Write()
    def SVSigTriggerPulse(self, name, high=True): 
        ev_bus = CreateBus((name,))
        ev_bus.value[0] = 1 if high else 0
        ev_bus.Write()
        yield self.clk
        self.print( f'Event bus {name} pulse triggered', trace=3)
        yield from itertools.repeat(self.clk, self.width-1)
        ev_bus.value[0] = 0 if high else 1
    @property
    def SimPass(self):
        if not self.sim_pass_ev:
            sim_pass_ev = CreateEvent('sim_pass_ev')
            self.Trigger(sim_pass_ev, 'sim_pass')
            return sim_pass_ev
        else:
            self.Trigger(self.sim_pass_ev, 'sim_pass')
            return self.sim_pass_ev 
    @property
    def SimStop(self):
        if not self.sim_stop_ev:
            sim_stop_ev = CreateEvent('sim_stop_ev')
            self.Trigger(sim_stop_ev, 'sim_stop')
            return sim_stop_ev 
        else:
            self.Trigger(self.sim_stop_ev, 'sim_stop')
            return self.sim_stop_ev 
    @property
    def TimeOut(self):
        if not self.time_out_ev:
            time_out_ev = CreateEvent('time_out_ev')
            self.Trigger(time_out_ev, 'time_out')
            return time_out_ev 
        else:
            self.Trigger(self.time_out_ev , 'time_out')
            return self.time_out_ev 
    
class NicoUtil(PYUtil):
    def __init__(self, noparse=False):
        self.SBC = StructBusCreator
        self.V_(GBV.VERBOSE)
        self.endcycle = 10000
        self.test = GBV.TEST
        self.testname = GBV.TEST.rsplit('_tb')[0]
        self.fsdbname = self.testname + '_tb' #TODO
        self.topfile  = GBV.SV.rstrip('.sv')
        self.incfile  = GBV.INC
        self.dutname  = GBV.TESTMODULE 
        if not noparse:
            self.session = self.SBC.TopTypes()
            self.SessionInit()
            super().__init__()
        self.ev = EventTrigger()
    def TopTypes(self, inclvl=-1):
        self.session = self.SBC.TopTypes(inclvl=inclvl)
        self.SessionInit()
    def AllTypes(self):
        self.session = self.SBC.AllTypes()
        self.SessionInit()
    def SessionInit(self):
        self.dut = self.session.hiers.get(self.dutname)
        self.top = self.session.hiers.get(GBV.TOPMODULE)
        self.dutfile = self.session.hiers.get(self.dutname+'_sv')
        self.hiers = EAdict(self.session.hiers)
        self.regbkstr= self.session.hiers.get(GBV.REGBK)
        self.regbk= SVRegbk(self.regbkstr) if self.regbkstr else None
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
    def ne(self, head,x):
        if head == [[None]]:
            return False
        else:
            return not all ([np.array_equal(a,b) for a,b in zip(head,x)])
    

if __name__=='__main__':
    n = NicoUtil()

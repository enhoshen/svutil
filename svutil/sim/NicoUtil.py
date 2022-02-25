from nicotb import *
from svutil.SVparse import *
from svutil.SVclass import *
from svutil.SVsim import *
from svutil.SVutil import colorama
from svutil.SVclass import SVType 
import os
import itertools
import numpy as np
from nicotb.utils import RandProb


class StructBus:
    "name , bw , dim , type , enum literals"

    def __init__(self, structName, signalName, attrs, buses):
        self.structName = structName
        self.signalName = signalName
        self.attrs = attrs
        self.namelist = {v[0]: i for i, v in enumerate(self.attrs)}
        self.buses = buses

    def __getitem__(self, i):
        return self.buses[i]

    @property
    def values(self):
        return [
            x.values if isinstance(x, StructBus) else x.values[0] for x in self.buses
        ]

    @values.setter
    def values(self, v):
        for bb, vv in zip(self.buses, v):
            try:
                bb.values = vv
            except:
                bb.value = vv

    @property
    def value(self):
        return self.buses[0]._vs[0]

    @value.setter
    def value(self, v):
        self.buses[0].signals[0].value = v

    def SetToZ(self):
        [x.SetToZ() for x in self.buses]

    def SetToX(self):
        [x.SetToX() for x in self.buses]

    def SetToN(self):
        [
            x.SetToN()
            if isinstance(x, StructBus)
            else [s._x.fill(0) for s in x.signals]
            for x in self.buses
        ]

    def SetTo(self, n):
        self.SetToN()
        [
            x.SetTo(n)
            if isinstance(x, StructBus)
            else [s._value.fill(n) for s in x.signals]
            for x in self.buses
        ]

    # def Write(self, imm=False):
    #    [ x.Write(imm) for x in self.buses ]
    def Write(self, *lst, imm=False):
        """
        Apply Write() on the elements
        if lst is not provided, Write every elements
        lst could be a list of bus names,
        or it could be seperated arguments of bus names.
        Ex: Write('a','b') equals Write(['a','b'])
        """
        if not lst:
            [x.Write(imm=imm) for x in self.buses]
        else:
            if len(lst) == 1 and type(lst[0]) == list:
                [self.buses[self.namelist[x]].Write(imm=imm) for x in lst[0]]
            else:
                [self.buses[self.namelist[x]].Write(imm=imm) for x in lst]

    def Read(self):
        [x.Read() for x in self.buses]

    # TODO *arg setter
    def __setitem__(self, k, v):
        i = self.namelist[k]
        for x in v:
            self.buses[i].value = x

    def __getattr__(self, k):
        n = self.namelist.get(k)
        return self.buses[n] if n is not None else None

    def __repr__(self, indent=13, top=True):
        w = 13
        s = ""
        if top:
            s = f"{self.signalName:=^{3*w}}\n"
        for a, v, b in zip(self.attrs, self.values, self.buses):
            if isinstance(b, StructBus):
                s += f"{a[0]:<{w}}\n"
                s += b.__repr__(indent + 13, False)
            else:
                s += (
                    f'{"":<{indent-13}}'
                    f"{a[0]:<{w}}"
                    f"{list(v) if len(a)!=5 else [a[4][i] for i in v] !r:<{w}}\n"
                )
        return s


class StructBusCreator:
    structlist = {}
    basic_sv_type = {"logic": np.uint32, "unsigned logic": np.uint32, "signed logic": np.int32, "bit": np.bool}

    def __init__(self, structName, attrs):
        if attrs:
            for memb in attrs:
                assert (
                    self.structlist.get(memb[3]) != None
                ), f"can't find type {memb[3]}; \
                                                            \n  (1)change the declartion of the type/import\
                                                            \n  (2)probably use StructBusCreator.all_types()?"
        if self.structlist.get(structName) == None:
            self.structlist[structName] = self
        self.structName = structName
        self.attrs = attrs

    @classmethod
    def file_parse(cls, paths=None, inc=True, inclvl=-1):
        S = SVparseSession()
        S.file_parse(paths=paths, inc=inc, inclvl=inclvl)
        return S

    @classmethod
    def basic_types(cls):
        StructBusCreator("logic", None)
        StructBusCreator("signed logic", None)
        StructBusCreator("enum", None)

    @classmethod
    def all_types(cls):
        cls.reset()
        cls.basic_types()
        S = cls.file_parse()
        for h in SVparse.session.hiers.values():
            for k, v in h.types.items():
                StructBusCreator(k, v)
        return S

    @classmethod
    def top_types(cls, inclvl=-1):
        cls.reset()
        cls.basic_types()
        S = cls.file_parse(paths=[GBV.TOPSV], inc=False, inclvl=inclvl)
        for T in SVparse.session.hiers[
            GBV.TOPMODULE
        ].Types:  # TOPMODULE defined in SVparse
            for k, v in T.items():
                StructBusCreator(k, v)
        return S

    @classmethod
    def get(cls, t, name, hier="", dim=(), dtype=np.int32):
        if "::" in t:
            _pkg, _type = t.split("::")
            tp = SVparse.session.package[_pkg].types[_type]
            StructBusCreator(t, tp)
        if dim == ():
            return cls.structlist[t].create_struct_bus(name, hier, dim, dtype=dtype)
        else:
            return cls.structlist[t].mda_create_struct_bus(name, hier, dim, dtype=dtype)

    @classmethod
    def reset(cls):
        cls.structlist = {}

    def create_struct_bus(self, signalName, hier="", DIM=(), dtype=None):
        """
        Return StructBus or nicotb Bus based on the type name
        * If the type is a struct, return StructBus
        * If the type is built-in types (EX:logic), return nicotb Bus
        """
        # buses = {'logic' :  CreateBus( self.createTuple(signalName) )}
        buses = []
        attrs = self.structlist[self.structName].attrs
        if attrs is None:
            return CreateBus(((hier, signalName, DIM, dtype),))
        else:
            tps = [SVType(i) for i in attrs]
            if len(tps)==1 and tps[0].name == self.structName:
                # type aliasing (EX: typedef Type1 TypeAlias;)
                dim = tps[0].dim
                tp = tps[0].tp
                return self.structlist[tp].create_struct_bus(signalName, hier, DIM+dim, dtype)
            else:
                for n, bw, dim, t, *_ in attrs:
                    if t in self.basic_sv_type:
                        if dtype is None:
                            _dtype = self.basic_sv_type[t]
                        else:
                            _dtype = dtype
                        buses.append(
                            CreateBus(((hier, f"{signalName}.{n}", DIM + dim, _dtype),))
                        )
                    elif t == "enum":
                        buses.append(CreateBus(((hier, signalName, DIM + dim, dtype),)))
                    else:
                        buses.append(
                            self.structlist[t].create_struct_bus(
                                signalName + "." + n, hier, DIM + dim, dtype
                            )
                        )
        return StructBus(self.structName, signalName, attrs, buses)

    def mda_create_struct_bus(self, signalName, hier="", DIM=(), dtype=None):
        buses = []
        if DIM == ():
            return self.create_struct_bus(signalName, hier, DIM, dtype=dtype)
        else:
            for d in range(DIM[0]):
                buses.append(
                    self.mda_create_struct_bus(
                        signalName + f"[{d}]", hier, DIM[1:], dtype=dtype
                    )
                )
            return buses


class Busdict(EAdict):
    def Flatten(self, lst):
        return (
            self.Flatten(lst[0]) + (self.Flatten(lst[1:]) if len(lst) > 1 else [])
            if type(lst) == list
            else [lst]
        )

    def Read(self, *lst):
        if not lst:
            [
                [i.Read() for i in self.Flatten(x)] if type(x) == list else x.Read()
                for x in self.dic.values()
            ]
        else:
            if len(lst) == 1 and type(lst[0]) == list:
                [
                    [i.Read() for i in self.Flatten(x)]
                    if type(x) == list
                    else self.dic[x].Read()
                    for x in lst[0]
                ]
            else:
                [
                    [i.Read() for i in self.Flatten(x)]
                    if type(x) == list
                    else self.dic[x].Read()
                    for x in lst
                ]

    def Write(self, *lst, imm=False):
        if not lst:
            [
                [i.Write(imm=imm) for i in self.Flatten(x)]
                if type(x) == list
                else x.Write(imm=imm)
                for x in self.dic.values()
            ]
        else:
            if len(lst) == 1 and type(lst[0]) == list:
                [
                    [i.Write(imm=imm) for i in self.Flatten(self.dic[x])]
                    if type(self.dic[x]) == list
                    else self.dic[x].Write(imm=imm)
                    for x in lst[0]
                ]
            else:
                [
                    [i.Write(imm=imm) for i in self.Flatten(self.dic[x])]
                    if type(self.dic[x]) == list
                    else self.dic[x].Write(imm=imm)
                    for x in lst
                ]

    def is_sb(self, x):
        return isinstance(x, StructBus)

    def SetToN(self):
        bussettoN = lambda x: [s._x.fill(0) for s in x.signals]
        [
            [i.SetToN() if self.is_sb(i) else bussettoN(i) for i in self.Flatten(x)]
            if type(x) == list
            else x.SetToN()
            if self.is_sb(x)
            else bussettoN(x)
            for x in self.dic.values()
        ]

    def SetTo(self, n):
        busfill = lambda x: [s._value.fill(n) for s in x.signals]
        self.SetToN()
        [
            [i.SetTo(n) if self.is_sb(i) else busfill(i) for i in self.Flatten(x)]
            if type(x) == list
            else x.SetTo(n)
            if self.is_sb(x)
            else busfill(x)
            for x in self.dic.values()
        ]


class RegbkMaster(SVutil):
    """Wrapper for register bank controller
    The class convert more readible register sequence format to all number sequence.
        regbk: SVRegbk object providing control register information
        addr: bus of the control register address port
        wdata: bus of the control register write data port
        rdata: bus of the control register read data port
        master: a nicotb protocol module that drive register sequence to the register bank dut
        proto_it: a RegbkMaster method to convert register sequence to corresponding data
            Iterable sender (i.e nicotb.protocol.TwoWire.Master.send_iter).
            Here is a table of protocol module' corresponding iterable function
            nicotb.protocol.TwoWire: RegbkMaster.reg_read_write_addr_it
            nicotb.protocol.OneWire: RegbkMaster.reg_read_write_addr_it
            gzsim.protocol.Apb: RegbkMaster.reg_read_write_it
            gzsim.protocol.Ahb: RegbkMaster.ahb_reg_read_write_it
    """

    def __init__(
        self,
        regbk: SVRegbk,
        addr: Bus = None,
        write: Bus = None,
        wdata: Bus = None,
        rdata: Bus = None,
        master=None,
        proto_it=None,
    ):

        self.verbose = v_(VERBOSE)
        self.master = master
        self.regbk = regbk
        self.addr = addr
        self.write = write
        self.wdata = wdata
        self.rdata = rdata
        self.proto_it = RegbkMaster.reg_read_write_it if proto_it is None else proto_it
        self.ac = f"{colorama.Fore.YELLOW}"  # attribute color
        self.cr = f"{colorama.Style.RESET_ALL}"  # color reset
        self.regfieldfmt = (
            lambda f, endl=f'\n{"":>8}': f"{endl}{self.ac}Reg fields: {self.cr}{f.__str__()}{endl}"
            if f
            else ""
        )
        self.addrfmt = lambda addr: f"{self.ac}Address:{self.cr} {addr.__str__():<5}"
        self.regfmt = (
            lambda reg, offset, rw, w: f'{self.ac}Register bank {"write" if rw else "read":>5}:{self.cr}{reg.__str__()+offset.__str__():<{w}}'
        )
        self.rdfmt = f"{self.ac}read data: {self.cr}"
        self.rdatafmt = lambda rdata: rdata.__str__()
        self.readfmt = (
            lambda reg, offset, addr, dlst, regfields, w: f"{self.regfmt(reg, offset, False, w)} {self.addrfmt(addr)}{self.rdfmt+self.rdatafmt(dlst):<5} {self.regfieldfmt(regfields)}"
        )
        self.wrfmt = f"{self.ac}Written: {self.cr}"
        self.wdatafmt = lambda wdata: hex(wdata)
        self.wrorigfmt = f"{self.ac}Original: {self.cr}"
        self.wdataorigfmt = lambda data: data.__str__()
        self.writefmt = (
            lambda reg, rw, offset, addr, wdata, regfields, data, w: f"{self.regfmt(reg, offset, rw, w)} {self.addrfmt(addr)}{self.wrfmt}{self.wdatafmt(wdata):>10} "
            + f"{self.regfieldfmt(regfields)}{self.wrorigfmt}{self.wdataorigfmt(data)}"
        )

    def write(self):
        self.addr.Write() # nicotb.bus
        self.rw.Write()
        self.wdata.Write()

    def read(self):
        self.rdata.Read() # nicotb.bus

    def SendIter(self, regseq, rwseq, dataseq):
        assert self.master, "Specify the protocol master"
        it = self.proto_it
        yield from self.master.SendIter(it(self, regseq, rwseq, dataseq))

    def send_iter(self, regseq, rwseq, dataseq):
        assert self.master, "Specify the protocol master"
        it = self.proto_it
        yield from self.master.send_iter(it(self, regseq, rwseq, dataseq))

    def issue_commands(self, regseq, rwseq, dataseq):
        it = self.proto_it
        yield from self.master.issue_commands(it(self, regseq, rwseq, dataseq))

    def reg_read_write_it(self, regseq, rwseq, dataseq):
        """
        Generate an iterable to loop through a sequence of register bank's
        address, read/write, and data.
        Args:
            regseq: list of
                    (1)register name string, or
                    (2)the integer address offset, or
                    (3)even a tuple of (register name, offset) representing an
                    offset starting from the register
            rwseq : list of read/write, 1 for write, 0 for read.
            dataseq: list of data. data can be either integer or list
                of integer if the register has underlying register fields.
                SVRegbk.regwrite will handle the data compaction for you. If
                the reg is a integer address offset, the regfield can't be
                retrieved, so the data must a compacted integer generated by
                yourself.
            #TODO: string data of parsed parameters that can be converted
                SVRegbk
        """
        w = 15
        orig_cb = self.master.callbacks
        leng = list(map(len, [regseq, rwseq, dataseq]))
        if (
            len([len(i) for i in [regseq, rwseq, dataseq] if len(i) != len(regseq)])
            != 0
        ):
            self.print(f"[Warning] {leng} register sequence length mismatch", trace=0)
        for reg, rw, data in itertools.zip_longest(regseq, rwseq, dataseq, fillvalue=0):
            offset = ""
            if type(reg) == int:
                assert (
                    type(data) == int
                ), "raw register address offset only takes integer data"
                addr, wdata, regfields = reg, data, "undefined regfields"
            elif type(reg) == tuple:
                addr, wdata, regfields = self.regbk.reg_write(reg[0], data)
                offset = reg[1] * self.regbk.regbsize
                addr += offset
                offset = f"+{offset}"
                reg = reg[0]
                w = max(w, len(reg + offset))
            elif type(reg) == str:
                addr, wdata, regfields = self.regbk.reg_write(reg, data)
                w = max(w, len(reg))
            else:
                raise TypeError("un-recognized register sequence type")

            def msg_cb(_):
                if not rw:
                    self.read()
                    dlst, rf = self.regbk.reg_read(reg, self.rdata.value[0])
                    self.print(
                        self.readfmt(reg, offset, addr, dlst, rf, w),
                        verbose=1,
                        trace=2,
                        level=True,
                    )
                else:
                    self.print(
                        self.writefmt(reg, rw, offset, addr, wdata, regfields, data, w),
                        verbose=1,
                        trace=2,
                        level=True,
                    )

            try:
                if self.verbose >= 1:
                    self.msgcb = msg_cb
                else:
                    self.msgcb = lambda _: None
            except:
                self.msgcb = lambda _: None
            self.master.callbacks = [msg_cb] + orig_cb
            yield (addr, wdata, rw)
            self.master.callbacks = orig_cb

    def reg_read_write_addr_it(self, regseq, rwseq, dataseq):
        """
        Used by nico protocol send_iter() thread without addr bus. This thread is
        a workaround by yielding the address and manually write() data and write buses.
        That is, the corresponding protocol bus' data is the address bus.
        Ex: regbus = TwoWire.Master(buses.i_req, buses.o_ack, buses.i_addr, ck_ev)
            ...
            regbus.send_iter(RegbkMasterObjec.RegwriteAddrIt(regseq, rwseq, dataseq))
        """
        for addr, wdata, rw in self.reg_read_write_it(regseq, rwseq, dataseq):
            self.write.value = rw
            self.addr.value = addr
            self.wdata.value = wdata
            self.write.Write() # nicobus
            self.wdata.Write() # nicobus
            yield self.addr.value

    def ahb_reg_read_write_it(self, regseq, rwseq, dataseq):
        for addr, wdata, rw in self.reg_read_write_it(regseq, rwseq, dataseq):
            yield (rw, addr, wdata)


class ThreadCreator(SVutil):
    """ Helper class for creating simulation threads. """

    def __init__(self, ck_ev):
        self.ck_ev = ck_ev
        # self.init_ev  = init_ev
        # self.resp_ev  = resp_ev
        # self.fin_ev   = fin_ev
        # self.intr_ev  = intr_ev

    def phse3_send(self, cfg):
        yield from INITS[cfg]()
        yield from RESPS[cfg]()
        yield from FINS[cfg]()
        self.print("Sim done", trace=3)


class EventTrigger(SVutil):
    """ Helper class for triggering a python event at the same time write to a nicotb bus """

    # TODO
    def __init__(self, ck_ev=None, clk_cnt=None, pulse_width=None):
        self.v_(VERBOSE)
        self.clk = ck_ev
        self.clk_cnt = clk_cnt
        self.pulse_width = pulse_width
        self.sim_pass_ev = None
        self.sim_stop_ev = None
        self.time_out_ev = None
        self.sig_trig_type = {
            "LEVEL": self.sv_sig_trigger_level,
            "Edge": self.sv_sig_trigger_edge,
            "Pulse": self.sv_sig_trigger_pulse,
        }
        pass

    def reg_events(self, sim_pass_ev, sim_stop_ev, time_out_ev):
        self.sim_pass_ev = sim_pass_ev
        self.sim_stop_ev = sim_stop_ev
        self.time_out_ev = time_out_ev

    def trigger(self, ev_name, sig_name=None, trig_type="LEVEL", high=True):
        """
        trigger ev_name in python and sig_name(optional) in verilog
            ev_name: an integer event created by CreateEvent/CreateEvents or event name's string
            sig_name: signal string name
        """
        self.py_ev_trigger(ev_name)
        if sig_name:
            Fork(self.sig_trig_type[trig_type](sig_name, high))

    def triggers(self, ev_tuples, trig_type="LEVEL", high=True):
        """ trigger each of the event pairs in ev_tuples """
        for ev, sig in ev_tuples:
            self.trigger(ev, sig, trig_type, high)

    def py_ev_trigger(self, name):
        ev = GetEvent(name)
        SignalEvent(ev)

    def sv_sig_trigger_level(self, name, high=True):
        ev_bus = CreateBus((name,))
        ev_bus.value[0] = 1 if high else 0
        ev_bus.write()
        yield self.clk
        self.print(f"Event bus {name} level triggered", trace=3)

    def sv_sig_trigger_edge(self, name, high=True):
        ev_bus = CreateBus((name,))
        ev_bus.value[0] = 1 if high else 0
        ev_bus.write()
        yield self.clk
        self.print(f"Event bus {name} edge triggered", trace=3)
        ev_bus.value[0] = 0
        ev_bus.write()

    def sv_sig_trigger_pulse(self, name, high=True):
        ev_bus = CreateBus((name,))
        ev_bus.value[0] = 1 if high else 0
        ev_bus.write()
        yield self.clk
        self.print(f"Event bus {name} pulse triggered", trace=3)
        yield from itertools.repeat(self.clk, self.width - 1)
        ev_bus.value[0] = 0 if high else 1

    @property
    def sim_pass(self):
        if not self.sim_pass_ev:
            sim_pass_ev = CreateEvent("sim_pass_ev")
            self.trigger(sim_pass_ev, "sim_pass")
            return sim_pass_ev
        else:
            self.trigger(self.sim_pass_ev, "sim_pass")
            return self.sim_pass_ev

    @property
    def sim_stop(self):
        if not self.sim_stop_ev:
            sim_stop_ev = CreateEvent("sim_stop_ev")
            self.trigger(sim_stop_ev, "sim_stop")
            return sim_stop_ev
        else:
            self.trigger(self.sim_stop_ev, "sim_stop")
            return self.sim_stop_ev

    @property
    def time_out(self):
        if not self.time_out_ev:
            time_out_ev = CreateEvent("time_out_ev")
            self.trigger(time_out_ev, "time_out")
            return time_out_ev
        else:
            self.trigger(self.time_out_ev, "time_out")
            return self.time_out_ev


class NicoUtil(PYUtil):
    def __init__(self, noparse=False):
        self.SBC = StructBusCreator
        self.v_(GBV.VERBOSE)
        self.endcycle = 10000
        self.test = GBV.TEST
        self.testname = GBV.TEST.rsplit("_tb")[0]
        self.fsdbname = self.testname + "_tb"  # TODO
        self.topfile = GBV.SV.rstrip(".sv")
        self.incfile = GBV.INC
        self.dutname = GBV.TESTMODULE
        if not noparse:
            self.session = self.SBC.top_types()
            self.session_init()
            super().__init__()
        self.ev = EventTrigger()

    def top_types(self, inclvl=-1):
        self.session = self.SBC.top_types(inclvl=inclvl)
        self.session_init()

    def all_types(self):
        self.session = self.SBC.all_types()
        self.session_init()

    def session_init(self):
        self.dut = self.session.hiers.get(self.dutname)
        self.top = self.session.hiers.get(GBV.TOPMODULE)
        self.dutfile = self.session.hiers.get(self.dutname + "_sv")
        self.hiers = EAdict(self.session.hiers)
        self.regbkstr = self.session.hiers.get(GBV.REGBK)
        self.regbk = SVRegbk(self.regbkstr) if self.regbkstr else None

    def macro_to_num(self, s):
        _s = s
        _s = SVstr(_s).multi_macro_expand(self.top.AllMacro)
        _s = SVstr(_s).to_num(self.top)
        reobj = True
        while reobj:
            if type(_s) == int:
                break
            reobj = re.search(r"`(\w+)\b", _s)
            if reobj:
                _s = SVstr(_s).multi_macro_expand(self.top.AllMacro)
                _s = SVstr(_s).to_num(self.top)
        return _s

    @property
    def dut_ports(self):
        return {i: SVPort(v) for i, v in self.dut.Portsdic.items()}

    def dut_port_dim(self, p):
        """
            Find the port dimension based on the port name
            from dut module specified by TESTMODULE
        """
        d = self.dut_ports[p].dimstrtuple
        return self.tuple_to_num(d)

    def tuple_to_num(self, t):
        return tuple(map(lambda x: self.macro_to_num(x), t))

    def ne(self, head, x):
        if head == [[None]]:
            return False
        else:
            return not all([np.array_equal(a, b) for a, b in zip(head, x)])


if __name__ == "__main__":
    n = NicoUtil()

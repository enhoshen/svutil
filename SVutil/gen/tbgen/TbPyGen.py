import os
import sys
import itertools
from functools import reduce

import numpy as np

from SVutil.SVparse import *
from SVutil.SVgen import *
from SVutil.SVclass import *
from SVutil.gen.TestGen import TestGen

@SVgen.UserClass
class TbPyGen(TestGen):
    def TbBlk(self):
        ind = self.cur_ind.Copy()
        yield ""
        s = "\n"
        yield s
        s = ""
        for ck in self.clk_domain_lst:
            _aff = ck[0] + "_" if ck[0] != "" else ""
            s += f'{ind.b}{_aff}rst_out, {_aff}ck_ev = CreateEvents(["{_aff}rst_out", "{_aff}ck_ev"])\n'
        self.print(self.nico_eventlst, verbose=3)
        ev_lst = reduce(lambda x, y: x + ", " + y[0], self.nico_eventlst + [("", "")], "")[
            2:-2
        ]
        self.print(ev_lst, verbose=3)
        ev_lst_str = (
            f'{ind[1]} "{self.nico_eventlst[0][0]}"\n'
            + reduce(
                (lambda x, y: x + f'{ind[1]},"{str(y[0])}"\n'), self.nico_eventlst[1:], ""
            )[:-1]
        )
        self.print(ev_lst_str, verbose=3)
        s += f"{ind.b}{ev_lst} = CreateEvents([\n{ev_lst_str}])\n\n"
        s += f"{ind.b}RegisterCoroutines([\n"
        s += f"{ind[1]}main()\n"
        s += f"{ind.b}])"
        yield s

    @SVgen.Blk
    def NicoutilImportBlk(self, ind=None):
        s  = f"{ind.b}from nicotb import *\n"
        s += f"{ind.b}import numpy as np \n\n"
        yield s

        s = f"{ind.b}Nico = NicoUtil.NicoUtil()\n"
        yield s
    @SVgen.str
    def builtin_import(self):
        s  = f"import sys\n"
        s += f"import os\n"
        s += f"from itertools import repeat\n"
        return s

    @SVgen.str
    def svutil_import(self):
        s  = f"from SVutil.SVparse import GBV, EAdict\n"
        s += f"from SVutil.sim import NicoUtil\n"
        return s

    @SVgen.str
    def gzsim_import(self):
        s  = f"from gzsim.nicobus.bus import *\n"
        s += f"from gzsim.utils import *\n"
        s += f"from gzsim.tester import *\n"
        s += f"from gzsim.sequencer import *\n"
        s += f"from gzsim.scoreboard import *\n"
        s += f"from gzsim.protocol import OneWire\n"
        return s

    def NicoutilImportBlkNonPackage(self):
        """ deprecated """
        ind = self.cur_ind.Copy()
        yield ""
        s = "\n"
        s += "import sys\n"
        s += "import os\n"
        s += "sys.path.append(os.environ.get('SVutil'))\n"
        s += "sys.path.append(os.environ.get('PROJECT_PATH')+'/sim')\n"
        s += "from itertools import repeat\n"
        s += "from nicotb.primitives import JoinableFork\n"
        s += "from SVparse import SVparse,EAdict\n"
        s += "from sim.NicoUtil import *\n\n"
        s += "TEST_CFG= os.environ.get('TEST_CFG',None)\n"
        s += "Nico = NicoUtil() \n"
        s = s.replace("\n", f"\n{ind.b}")
        yield s

    def businitBlk(self, module):
        ind = self.cur_ind.Copy()
        yield ""
        s = "\n"

        s += f"{ind.b}def businit():\n"
        # s += f'{ind[1]}SBC = StructBusCreator\n'
        s += f"{ind[1]}#Nico.SBC.TopTypes()\n"
        s += f"{ind[1]}#Nico.SBC.AllTypes()\n"
        s += f"{ind[1]}dic = {{}}\n"
        w = [0, 0]
        for p in module.ports:
            p = SVPort(p)
            w[0] = max(w[0], len(p.name))
            w[1] = max(w[1], len(p.tp))
        last_gp = None
        for p in module.ports:
            p = SVPort(p)
            if p.group != [] and p.group[0] != last_gp:
                last_gp = p.group[0]
                s += f'{ind[1]}#{" "+last_gp+" ":=^{20}}#\n'
            tp = p.tp
            _q = "'"
            dimf = f"Nico.DutPortDim('{p.name+_q:<{w[0]+1}})"
            dim = f"Nico.DutPortDim('{p.name+_q})"
            if tp == "logic" or tp == "signed logic":
                s += f"{ind[1]}dic['"
                s += f'{p.name + _q+"] ":<{w[0]+3}}'
                s += f"= CreateBus(( ('', '{p.name+_q:<{w[0]+2}}, {dimf},),  ))\n"
            else:
                s += f"{ind[1]}dic['"
                s += f'{p.name + _q+"] ":<{w[0]+3}}'
                s += f"= Nico.SBC.Get('{p.tp+_q:<{w[1]+1}}, '{p.name+_q}, dim={dim})\n"

                # TODO macro....
        s += f"{ind[1]}return NicoUtil.Busdict(dic) # access by name without quotes\n"
        yield s

    def mainBlk(self):
        ind = self.cur_ind.Copy()
        yield ""
        s = "\n"

        s += f"{ind.b}def main():\n"
        s += f"{ind[1]}buses = businit()\n"
        s += f"{ind[1]}buses.SetToN()\n"
        s += f"{ind[1]}buses.Write() #don't use this afterward if you're not sure what you're doing\n"
        s += f"{ind[1]}yield rst_out\n"
        s += f"{ind[1]}#j = []\n"
        s += f"{ind[1]}#for jj in j:\n"
        s += f"{ind[1]}#    yield from jj.Join()\n"
        s += f"{ind[1]}#[jj.Destroy() for jj in j]\n"
        s += f"{ind[1]}#FinishSim()\n"
        yield s

    def module_test(self, module=None, **conf):
        module = self.dut if not module else module
        tb = self.TbBlk()
        builtin = self.builtin_import(spacing=True)
        nicoutil = self.NicoutilImportBlk()
        gzsim = self.gzsim_import(spacing=True)
        svutil = self.svutil_import(spacing=True)
        businit = self.businitBlk(module)
        main = self.mainBlk()
        s = self.Genlist([(tb,), builtin, (nicoutil,), gzsim, svutil, nicoutil, (businit, main), tb])
        if conf.get("copy") == True:
            ToClip(s)
        return s

    def write(self, text, **conf):
        p = self.TbWrite(text, "py", **conf)
        self.print("PY testbench written to ", p)


import os
import sys
import itertools
from functools import reduce

import numpy as np

from svutil.SVparse import *
from svutil.SVgen import *
from svutil.SVclass import *

@SVgen.user_class
class TestGen(SVgen):
    def __init__(self, ind=Ind(0), session=None):
        super().__init__(session=session)
        self.customlst += [
            "eventlst", 
            "py_logic_eventlst",
            "genpath",
            "clk_domain_lst"]
        self.nico_eventlst = [
            ("intr_ev", "intr_any"),
            ("init_ev", "init_cond"),
            ("resp_ev", "resp_cond"),
            ("fin_ev", "fin_cond"),
            ("sim_stop_ev", "sim_stop"),
            ("sim_pass_ev", "sim_pass"),
            ("sim_fail_ev", "sim_fail"),
            ("sim_abort_ev", "sim_abort"),
            ("time_out_ev", "time_out"),
        ]
        self.sv_eventlst = ["exit"]
        self.py_logic_eventlst = ["fin_cond", "sim_pass", "sim_fail", "sim_stop", "time_out"]
        self.clk_domain_lst = [("", "_n")]
        self.userfunclst = []


    def refresh(self):
        super().refresh()
        self.test = GBV.TEST
        self.testname = GBV.TEST.rsplit("_tb")[0]
        self.fsdbname = self.testname + "_tb"  # TODO
        self.topfile = GBV.SV.rstrip(".sv")

        self.genpath = "./"

    def module_test(self):
        """ pure virtual """
        raise NotImplementedError("Overide module_test in subclass")


    @SVgen.user_method
    def write_module_test(self, module=None, **conf):
        module = self.dut if not module else module
        conf["copy"] = False
        overwrite = conf.get("overwrite")
        self.write(self.module_test(module, **conf), overwrite=overwrite)

    @SVgen.user_method
    def show_module_test(self, module=None, copy=True, **conf):
        module = self.dut if not module else module
        conf["copy"] = copy
        self.print(self.module_test(module, **conf))


    @SVgen.user_method
    def show_mod_port_logic(self, module=None):
        module = self.dut if not module else module
        ins = self.logic_blk(module)
        s = self.genlist([(ins,)])
        to_clip(s)
        self.print(s)

    def tb_write(self, text, suf, **conf):
        overwrite = conf.get("overwrite")
        self.print("overwriting:", overwrite)
        fpath = self.test
        return self.file_write(fpath, text, suf, overwrite)


if __name__ == "__main__":
    g = TestGen()

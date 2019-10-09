import os
import sys
sys.path.append(os.environ.get('SVutil'))
from SVparse import *
from SVgen import * 
import itertools
import numpy as np
class LatexGen(SVgen):
    def __init__(self):
        super().__init__()
    def L_(self, s):
        return s.replace('_','\_')
    def ParameterStr(self , param):
        ind = Ind(1)
        pfield = SVhier.paramfield
        tpfield = SVhier.typefield
        param_tp = param[pfield.tp]
        s = ''
        desp='\n'
        memblist = []
        tp = self.cur_module.AllType.get(param_tp)  
        if tp: 
            for enuml in tp[0][tpfield.enumliteral]:
                _s = enuml.replace('_','\_')
                desp += f'{ind[2]}{_s}:\\\\\n'
        name = self.L_(param[pfield.name])
        num = self.L_(param[pfield.numstr])
        s = f'{ind.b}\\parameter{{ {name} }} {{ \n'
        s += f'{ind[1]}\\parameterDES{{  }} {{ {num} }} {{ }} {{ {desp}{ind[1]} }} }}\n'
        return s
    def SignalStr(self , sig, clk=None):
        ind=Ind(1)
        pfield = SVhier.portfield
        tpfield = SVhier.typefield
        sig_tp = sig[pfield.tp]
        s = ''
        memblist = []
        tp = self.cur_module.AllType.get(sig_tp)  
        if sig_tp != 'logic' and sig_tp != 'logic signed' and len(tp) != 1: 
            for memb in self.cur_module.AllType[sig_tp]:
                name = sig[pfield.name].replace('_','\_') +'.'+ memb[tpfield.name].replace('_','\_')
                width = str(memb[tpfield.bw])
                active = 'LOW' if name[-2:] == '_n' else  ( 'HIGH' if width =='1' else 'N/A' )
                if '-1:0' in width:
                    width = width.split('-')[0][1:]
                io = sig[pfield.direction]
                memb_tp = self.cur_module.AllType.get(memb[tpfield.tp])
                desp='\n'
                if memb_tp :
                    if memb_tp[0][tpfield.tp] =='enum':
                        for enuml in memb_tp[0][tpfield.enumliteral]:
                            _s = enuml.replace('_','\_')
                            desp += f'{ind[2]}{_s}:\\\\\n'
                memblist.append( (name, io, desp, width, active, clk)  )
        else:
            desp='\n'
            if sig_tp =='enum':
                for enuml in sig[tpfield.enumliteral]:
                    _s = enuml.replace('_','\_')
                    desp += f'{ind[2]}{_s}:\\\\\n'
            name = sig[pfield.name].replace('_','\_')
            width = '1' if sig[pfield.bwstr] == '' else sig[pfield.bwstr].replace('_','\_')
            active = 'LOW' if name[-2:] == '_n' else  ( 'HIGH' if width =='1' else 'N/A' )
            if '-1:0' in width:
                width = width.split('-')[0][1:]
            io = sig[pfield.direction]
            memblist.append( ( name, io, desp, width, active, clk) )
            
        for name,io,desp,width,active,clk in memblist:
            s += f'{ind.b}\\signal{{ {name} }} {{ {io} }} {{ \n'
            s += f'{ind[1]}\\signalDES{{ {desp} {ind[1]}}} {{ {width} }} {{ {active} }} {{ {clk} }} {{ }} {{ \\%}}  }}\n'
        return s
    def SignalDescription( self, module=None):
        module = self.dut if not module else module
        self.cur_module = module
        pfield = SVhier.portfield
        s = ''
        clk = None
        for p in module.ports:
            name = p[pfield.name]
            if not 'rst' in name:
                s += self.SignalStr(p, clk)
            else:
                s += self.SignalStr(p, None)
            if 'clk' in name:
                clk = name.replace('_','\_')
        ToClip(s)
        return s
    def ParameterDescription(self, module=None, local=True):
        module = self.dut if not module else module
        self.cur_module = module
        param = module.AllParamsDetail if not local else module.paramsdetail
        s = ''
        for p in param.values():
            s += self.ParameterStr(p)
        ToClip(s)
        return s
if __name__ == '__main__':
    g = LatexGen()

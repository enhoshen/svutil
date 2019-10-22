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
        self.default_input_delay = 30
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
            desp += self.DespStr(tp[0][tpfield.enumliteral], ind)
        name = self.L_(param[pfield.name])
        num = self.L_(param[pfield.numstr])
        s = f'{ind.b}\\parameter{{ {name} }} {{ \n'
        s += f'{ind[1]}\\parameterDES{{  }} {{ {num} }} {{ None }} {{ {desp}{ind[1]} }} }}\n'
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
                io = 'Input' if io =='input' else 'Output'
                memb_tp = self.cur_module.AllType.get(memb[tpfield.tp])
                desp='\n'
                if memb_tp :
                    if memb_tp[0][tpfield.tp] =='enum':
                        desp += self.DespStr(memb_tp[0][tpfield.enumliteral], ind )
                memblist.append( (name, io, desp, width, active, clk)  )
        else:
            desp='\n'
            if sig_tp =='enum' :
                desp += self.DespStr(sig[tpfield.enumliteral], ind)
            if (sig_tp!='logic' and sig_tp!='logic signed' and len(tp)==1 ):
                desp += self.DespStr(tp[0][tpfield.enumliteral], ind)
            name = sig[pfield.name].replace('_','\_')
            width = '1' if sig[pfield.bwstr] == '' else sig[pfield.bwstr].replace('_','\_')
            active = 'LOW' if name[-2:] == '_n' else  ( 'HIGH' if width =='1' and not 'clk' in sig[pfield.name] else 'N/A' )
            if '-1:0' in width:
                width = width.split('-')[0][1:]
            io = sig[pfield.direction]
            io = 'Input' if io =='input' else 'Output'
            memblist.append( ( name, io, desp, width, active, clk) )
            
        for name,io,desp,width,active,clk in memblist:
            delay = self.default_input_delay if not 'clk' in sig[pfield.name] else 'N/A'
            s += f'{ind.b}\\signal{{ {name} }} {{{io}}} {{ \n'
            s += f'{ind[1]}\\signalDES{{ {desp} {ind[1]}}} {{ {width} }} {{ {active} }} {{ {clk} }} {{ No }} {{ {delay}\\%}}  }}\n'
        return s
    def DespStr ( self, enuml, ind ):
        desp = f'{ind[2]}\\\\\n'
        for e in enuml:
            _s = e.replace('_','\_')
            desp += f'{ind[2]}{_s}:\\\\\n'
        desp = desp[:-3]+'\n'
        return desp
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

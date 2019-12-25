import os
import sys
sys.path.append(os.environ.get('SVutil'))
from SVparse import *
from SVgen import * 
from SVclass import *
import itertools
import numpy as np
class LatexGen(SVgen):
    # TODO $clog2 in latex
    def __init__(self):
        super().__init__()
        self.default_input_delay = 30
        self.regbk= SVRegbk(self.regbk) if self.regbk else None
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
    def RegMemMapStr(self, reg, reg_bsize=4, reg_slices=None, reg_defaults=None, reg_bw=None, reg_bw_str=None, rw=None): #reg is a SVEnuml object
        ind = Ind(1)
        name = reg.name.replace('_','\_')
        ofs  = reg.num*reg_bsize
        s = f'{ind.b}\\memmap{{\\hyperref[subsubsec:{reg.name.lower()}]{{{name}}}}}'
        s += f'{{{hex(ofs).upper().replace("X","x")}}}{{{reg_bw}}}{{{rw}}}{{\n'
        s += f'{ind[1]}\\memDES{{\n'
        s += f'{ind[1]}}}{{\n'
        reg_slices = self.RegSliceList(reg_slices) if reg_slices else None
        if reg_slices and reg_slices[0][0] == SVRegbk.reserved_name:
            reg_slices.pop(0)
        if reg_defaults:
            if reg_slices :
                for _slice, _default in zip ( reg_slices, reg_defaults):
                    s += f'{ind[2]}{{[{_slice[1]}]}}: {_default}\\\\\n'
                s = s[:-2]+'\n'
            else:
                try:
                    reg_bw_str = int(reg_bw_str)-1
                    reg_bw_str = '0' if reg_bw_str == 0 else f'{reg_bw_str}:0' 
                except: 
                    reg_bw_str = f'{reg_bw_str}-1:0'
                s += f'{ind[2]}{{[{reg_bw_str}]}}: {reg_defaults[0]}\\\\\n'
        else:
            reset = '\\TODO' if len(cmt) < 3 else cmt[2] 
            reset = self.L_(self.Lbrac(reset))
            s += f'{ind[2]}{reset}\n'
        s += f'{ind[1]}}}\n'
        s += f'{ind.b}}}\n'
        return s
    def RegFieldStr(self, reg_name, reg_slices, reg_types, reg_membtypes, reg_defaults, rw): # str, SVRegbk.regslices, SVRegbk.regtypes; align slices to types!
        ind = Ind(0)
        _name = reg_name.replace('_', '\_')
        s = f'{ind.b}\\begin{{regfieldtable}}{{{reg_name.lower()}}}{{{_name} register field}}\n'
        reg_slices = self.RegSliceList(reg_slices)
        if reg_slices[0][0] == SVRegbk.reserved_name:
            s += f'{ind[1]}\\regfield{{{reg_slices[0][1]}}}{{RESERVED}}{{N/A}}{{reserved}}\n'
            reg_slices.pop(0)
        for _slice, _type, _membtype, _default in zip(reg_slices, reg_types, reg_membtypes, reg_defaults):
            _slice_name = _slice[0].replace('_', '\_')
            s += f'{ind[1]}\\regfield{{{_slice[1]}}}{{{_slice_name}}}{{{rw}}}{{\n'
            s += f'{ind[2]}\\regDES{{\\TODO\\\\\n'
            if _membtype and _membtype[0].tp == 'enum':
                s += f'{ind[3]}{self.DespStr(_membtype[0].enumliteral, ind[3])}'
            s += f'{ind[3]}}}{{{_default}}}{{N/A}}\n'
            s += f'{ind[2]}}}\n'
        s += f'{ind.b}\\end{{regfieldtable}}\n'
        return s
    def RegFieldSubSec(self, reg, ofs, size, rw):
        ind = Ind(0)
        _name = self.L_(reg) 
        s = f'{ind.b}\\subsubsection{{{_name}}} \\label{{subsubsec:{reg.lower()}}}\n'
        s += f'{ind[1]}\\begin{{paragitemize}}\n'
        s += f'{ind[2]}\\item \\textbf{{Address Offset:}} {ofs}\n'
        s += f'{ind[2]}\\item \\textbf{{Size:}} {size}\n'
        s += f'{ind[2]}\\item \\textbf{{Read/Write Access:}} {rw}\n'
        s += f'{ind[1]}\\end{{paragitemize}}\n'
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
    def RegMemMapDescription(self, pkg=None):
        s = ''
        regbk = SVRegbk(pkg) if pkg and type(pkg)==str else self.regbk
        for reg in regbk.addrs.enumls:
            reg_slices = regbk.regslices.get(reg.name)
            defaults = self.Str2Lst(regbk.GetDefaultsStr(reg.name))
            reg_bw = regbk.params.get(f'{reg.name}_BW')
            reg_bw = reg_bw.num if reg_bw else None
            reg_bw_str = self.L_(regbk.GetBWStr(reg.name))
            width, rw = regbk.GetAddrCmt(reg.name) 
            reg_bw = width if not reg_bw else reg_bw
            reg_bw_str = width if not reg_bw_str else reg_bw_str
            s += self.RegMemMapStr(reg, regbk.regbsize, reg_slices, defaults, reg_bw, reg_bw_str, rw ) 
        ToClip(s)
        return s
    def RegFieldDescription(self, pkg=None):
        s = ''
        regbk = SVRegbk(pkg) if pkg and type(pkg)==str else self.regbk
        for reg in regbk.regfields:
            ofs = regbk.addrsdict[reg].num*regbk.regbsize
            ofs = hex(ofs).upper().replace('X', 'x')
            reg_bw = self.L_(regbk.GetBWStr(reg))
            width, rw = regbk.GetAddrCmt(reg) 
            reg_bw = width if not reg_bw else reg_bw
            s += self.RegFieldSubSec( reg, ofs, reg_bw+'b', rw) 
            s += self.RegFieldStr ( reg, regbk.regslices[reg], regbk.regtypes[reg], regbk.regmembtypes[reg], \
                                    self.Str2Lst(regbk.GetDefaultsStr(reg)), rw)
            s += '\n'
        ToClip(s)
        return s
    def RegSliceStr(self, _slice):
        _slice_str = ''
        for _ss in _slice[1]:
            if _ss[0] == _ss[1]:
                _slice_str += f'{_ss[0]}, '
            else:
                _slice_str += f'{_ss[0]}:{_ss[1]}, ' 
        _slice_str = _slice_str[:-2]
        return _slice_str 
    def RegSliceList(self, slices):
        return [ (_slice[0], self.RegSliceStr(_slice)) for _slice in slices]
    def Lbrac(self, s):
        return s.replace('[','{[').replace(']', ']}')
    def L_ (self, s):
        return s.replace('_', '\_') if s else None
    def Str2Lst(self,s):
        if not s:
            return s
        s = self.L_(s)
        s = SVstr(s).ReplaceSplit([',', '\'{', '{', '}'])
        return s
if __name__ == '__main__':
    g = LatexGen()

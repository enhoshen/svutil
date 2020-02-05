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
    def Reload(self):
        self.session.Reload()
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
        tpfield = SVhier.typefield
        sig = SVPort(sig)
        sig_tp = sig.tp
        s = ''
        memblist = []
        if self.cur_module.AllType.get(sig_tp):
            tp = [SVType(i) for i in self.cur_module.AllType.get(sig_tp)]
        else:
            tp = None
        if sig_tp != 'logic' and sig_tp != 'logic signed' and len(tp) != 1: 
            for memb in self.cur_module.AllType[sig_tp]:
                memb = SVType(memb)
                name = self.L_(sig.name+memb.name +' '+sig.dimstr)
                width = str(memb.bw)
                active = 'LOW' if name[-2:] == '_n' else  ( 'HIGH' if width =='1' else 'N/A' )
                if '-1:0' in width:
                    width = width.split('-')[0][1:]
                io = sig.direction
                io = 'Input' if io =='input' else 'Output'
                memb_tp = self.cur_module.AllType.get(memb.tp)
                desp='\\TODO\n'
                if memb_tp :
                    memb_tp = [SVType(i) for i in memb_tp]
                    if memb_tp[0].tp =='enum':
                        desp += self.DespStr(memb_tp[0].enumliteral, ind )
                memblist.append( (name, io, desp, width, active, clk)  )
        else:
            desp='\\TODO\n'
            if sig_tp =='enum' :
                desp += self.DespStr(sig.enumliteral, ind)
            if (sig_tp!='logic' and sig_tp!='logic signed' and len(tp)==1 ):
                desp += self.DespStr(tp[0].enumliteral, ind)
            name = self.L_(sig.name+' '+sig.dimstr)
            width = '1' if sig.bwstr == '' else sig.bwstr.replace('_','\_')
            active = 'LOW' if name[-2:] == '_n' else  ( 'HIGH' if width =='1' and not 'clk' in sig.name else 'N/A' )
            if '-1:0' in width:
                width = width.split('-')[0][1:]
            io = sig.direction
            io = 'Input' if io =='input' else 'Output'
            memblist.append( ( name, io, desp, width, active, clk) )
            
        for name,io,desp,width,active,clk in memblist:
            delay = self.default_input_delay if not 'clk' in sig.name else 'N/A'
            s += f'{ind.b}\\signal{{ {name} }} {{{io}}} {{\n'
            s += f'{ind[1]}\\signalDES{{ {desp} {ind[1]}}} {{ {width} }} {{ {active} }} {{ {clk} }} {{ No }} {{ {delay}\\%}}  }}\n'
        return s
    def RegMemMapStr(self, reg, reg_bsize=4, reg_slices=None, reg_defaults=None, reg_bw=None, reg_bw_str=None, rw=None, arr=None): #reg is a SVEnuml object
        ind = Ind(1)
        name = self.L_(reg.name)
        arr_suf = self.L_(SVRegbk.arr_num_suf)
        ofs  = reg.num*reg_bsize
        arr = '' if arr=='' else f' [{name}{arr_suf}]' 
        s = f'{ind.b}\\memmap{{\\hyperref[subsubsec:{reg.name.lower()}]{{{name}}}{arr}}}'
        s += f'{{{hex(ofs).upper().replace("X","x")}}}{{{reg_bw}}}{{{rw}}}{{\n'
        s += f'{ind[1]}\\memDES{{\n'
        s += f'{ind[2]}\\TODO\n' if arr == '' else f'{ind[2]}Array register of size {name}{arr_suf}\n'
        s += f'{ind[1]}}}{{\n'
        reg_slices = self.RegSliceList(reg_slices) if reg_slices else None
        if reg_slices and reg_slices[0][0] == SVRegbk.reserved_name:
            reg_slices.pop(0)
        if reg_defaults:
            if reg_slices :
                for _slice, _default in zip ( reg_slices, reg_defaults):
                    s += f'{ind[2]}{{[{_slice[1]}]}}: {_default.__str__()}\\\\\n'
                s = s[:-2]+'\n'
            else:
                try:
                    reg_bw_str = int(reg_bw_str)-1
                    reg_bw_str = '0' if reg_bw_str == 0 else f'{reg_bw_str}:0' 
                except: 
                    reg_bw_str = f'{reg_bw_str}-1:0'
                s += f'{ind[2]}{{[{reg_bw_str}]}}: {reg_defaults[0].__str__()}\\\\\n'
        else:
            reset = '\\TODO' if len(reg.cmt) < 3 else reg.cmt[2] 
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
        self.print( reg_types)
        for _slice, _type, _membtype, _default in zip(reg_slices, reg_types, reg_membtypes, reg_defaults):
            _slice_name = _slice[0].replace('_', '\_')
            s += f'{ind[1]}\\regfield{{{_slice[1]}}}{{{_slice_name}}}{{{rw}}}{{\n'
            s += f'{ind[2]}\\regDES{{\\TODO\\\\\n'
            if _membtype and _membtype[0].tp == 'enum':
                s += f'{ind[3]}{self.DespStr(_membtype[0].enumliteral, ind[3])}'
            s += f'{ind[3]}}}{{{_default.__str__()}}}{{N/A}}\n'
            s += f'{ind[2]}}}\n'
        s += f'{ind.b}\\end{{regfieldtable}}\n'
        return s
    def RegFieldSubSec(self, reg, ofs, size, rw, arr=None, reg_bsize=4):
        ind = Ind(0)
        _name = self.L_(reg) 
        arr_suf = self.L_(SVRegbk.arr_num_suf)
        arr_ofs = '' if not arr else f'+:{reg_bsize}{_name}{arr_suf}'
        s = f'{ind.b}\\subsubsection{{{_name}}} \\label{{subsubsec:{reg.lower()}}}\n'
        s += f'{ind[1]}\\begin{{paragitemize}}\n'
        s += f'{ind[2]}\\item \\textbf{{Address Offset:}} {ofs}{arr_ofs}\n'
        s += '' if arr=='' else f'{ind[2]}\\item \\textbf{{Register array size:}} {_name}{arr_ofs}\n'
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
    def SignalDesp( self, module=None):
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
    def ParameterDesp(self, module=None, local=True):
        module = self.dut if not module else module
        self.cur_module = module
        param = module.AllParamsDetail if not local else module.paramsdetail
        s = ''
        for p in param.values():
            s += self.ParameterStr(p)
        ToClip(s)
        return s
    def RegMemMapDesp(self, pkg=None):
        s = ''
        regbk = SVRegbk(pkg) if pkg and type(pkg)==str else self.regbk
        for reg in regbk.addrs.enumls:
            reg_slices = regbk.regslices.get(reg.name)
            defaults = self.L_(regbk.GetDefaultsStr(reg.name, lst=True))
            self.print(defaults, verbose='RegMemMap')
            if defaults:
                defaults.reverse()
            reg_bw = regbk.params.get(f'{reg.name}_BW')
            reg_bw = reg_bw.num if reg_bw else None
            reg_bw_str = self.L_(regbk.GetBWStr(reg.name))
            width, rw, arr= regbk.GetAddrCmt(reg.name) 
            reg_bw = width if not reg_bw else reg_bw
            reg_bw_str = width if not reg_bw_str else reg_bw_str
            s += self.RegMemMapStr(reg, regbk.regbsize, reg_slices, defaults, reg_bw, reg_bw_str, rw, arr ) 
        ToClip(s)
        return s
    def RegFieldDesp(self, pkg=None):
        s = ''
        regbk = SVRegbk(pkg) if pkg and type(pkg)==str else self.regbk
        for reg in regbk.regfields:
            ofs = regbk.addrsdict[reg].num*regbk.regbsize
            ofs = hex(ofs).upper().replace('X', 'x')
            reg_bw = self.L_(regbk.GetBWStr(reg))
            width, rw, arr= regbk.GetAddrCmt(reg) 
            reg_bw = width if not reg_bw else reg_bw
            s += self.RegFieldSubSec( reg, ofs, reg_bw+'b', rw, arr, regbk.regbsize) 
            defaults = self.L_(regbk.GetDefaultsStr(reg, lst=True))
            if defaults:
                defaults.reverse()
            tps =[i for i in regbk.regtypes[reg]]
            tps.reverse()
            membtypes = [i for i in regbk.regmembtypes[reg]]
            membtypes.reverse()
            s += self.RegFieldStr ( reg, regbk.regslices[reg], tps, membtypes, \
                                    defaults, rw)
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
        if type(s) == str:
            return s.replace('_', '\_') if s else None
        if type(s) == list:
            return [ self.L_(i) for i in s]
        return None
    def Str2Lst(self,s):
        if not s:
            return s
        s = self.L_(s)
        s = SVstr(s).ReplaceSplit([',', '\'{', '{', '}'])
        return s
if __name__ == '__main__':
    g = LatexGen()

import os
import sys
sys.path.append(os.environ.get('SVutil'))
from SVparse import *
from SVgen import * 
from SVclass import *
import itertools
import numpy as np
import re
class LatexGen(SVgen):
    # TODO $clog2 in latex
    def __init__(self, session=None, regbk=None, dut=None):
        super().__init__(session=session)
        self.customlst = [   'default_input_delay'
                            ,'struct_lvl']
        self.userfunclst = [
            'SignalDesp',
            'ParameterDesp',
            'RegMemMapDesp',
            'RegFieldDesp'
        ]
        self.default_input_delay = 30
        self.struct_lvl = 2
        if regbk and type(regbk)==str:
            self.regbk= SVRegbk(self.session.hiers.get(regbk))
        else:
            self.regbk= SVRegbk(self.regbk) if self.regbk else None
        self.dut = dut if dut else self.dut
    def Reload(self):
        self.session.Reload()
        self.Refresh()
        self.regbk= SVRegbk(self.regbk) if self.regbk else None
    def L_(self, s):
        return s.replace('_','\_')
    def ParameterStr(self , param):
        ind = Ind(1)
        param = SVParam(param)
        param_tp = param.tp
        s = ''
        desp='\n'
        memblist = []
        tp = self.cur_module.AllType.get(param_tp)
        if tp: 
            memb_tp = [SVType(i) for i in tp]
            if memb_tp[0].tp =='enum':
                desp += self.EnumlDespStr(memb_tp[0].enumliteral, ind )
        name = self.L_(param.name)
        num = self.L_(param.numstr)
        s = f'{ind.b}\\parameter{{ {name} }} {{ \n'
        s += f'{ind[1]}\\parameterDES{{  }} {{ {num} }} {{ None }} {{ {desp}{ind[1]}}}\n'
        s += f'{ind.b}}}\n'
        s = s.replace('$', '\\$')
        return s
    def SignalStr(self , sig, clk=None, ind=None):
        ind=Ind(1) if ind is None else ind
        tpfield = SVhier.typefield
        sig = SVPort(sig)
        sig_tp = sig.tp
        s = ''
        memblist = []
        if self.cur_module.AllType.get(sig_tp):
            tp = [SVType(i) for i in self.cur_module.AllType.get(sig_tp)]
        else:
            tp = [None]
        if sig_tp != 'logic' and sig_tp != 'logic signed' and len(tp) != 1: 
            #for memb in self.cur_module.AllType.get(sig_tp):
            #    memb = SVType(memb)
            #    name = self.L_(sig.name+'.'+memb.name +' '+sig.dimstr)
            #    width = str(memb.bw)
            #    active = 'LOW' if name[-2:] == '_n' else  ( 'HIGH' if width =='1' else 'N/A' )
            #    if '-1:0' in width:
            #        width = width.split('-')[0][1:]
            #    io = sig.direction
            #    io = 'Input' if io =='input' else 'Output'
            #    memb_tp = self.cur_module.AllType.get(memb.tp)
            #    desp='\\TODO\n'
            #    if memb_tp :
            #        memb_tp = [SVType(i) for i in memb_tp]
            #        if memb_tp[0].tp =='enum':
            #            desp += self.EnumlDespStr(memb_tp[0].enumliteral, ind )
            #    memblist.append( (name, io, desp, width, active, clk)  )
            sig_struct = self.cur_module.AllType.get(sig_tp)
            memblist = self.MemlistAppend(self.cur_module, sig, sig_struct,  ind, clk, self.struct_lvl)
            memblist = [ (self.L_(sig.name+'.')+name, *_) for name, *_ in memblist]
        else:
            desp= f'\n{ind[2]}\\TODO\\\\\n'
            if sig_tp =='enum' :
                desp += self.EnumlDespStr(sig.enumliteral, ind)
            if (sig_tp!='logic' and sig_tp!='logic signed' and len(tp)==1 ):
                try:
                    desp += self.EnumlDespStr(tp[0].enumliteral, ind)
                except:
                    self.print(tp, sig_tp)
            name = self.L_(sig.name+' '+sig.dimstr)
            width = '1' if sig.bwstr == '' else sig.bwstr.replace('_','\_')
            active = 'LOW' if name[-2:] == '_n' else  ( 'HIGH' if width =='1' and not 'clk' in sig.name else 'N/A' )
            if '-1:0' in width:
                width = width.split('-')[0][1:]
            io = sig.direction
            io = 'Input' if io =='input' else 'Output'
            memblist.append( ( name, io, desp, width, active, clk) )
            
        reged = 'Yes' if sig.name in self.cur_module.regs else 'No' 
        for name,io,desp,width,active,clk in memblist:
            delay = self.default_input_delay if not 'clk' in sig.name else 'N/A'
            s += f'{ind.b}\\signal{{ {name} }} {{{io}}} {{\n'
            s += f'{ind[1]}\\signalDES{{ {desp} {ind[1]}}} {{ {width} }} {{ {active} }} {{ {clk} }} {{{reged}}} {{ {delay}\\%}}  }}\n'
        return s
    def MemlistAppend(self, module, sig, struct, ind, clk, lvl=1):
        memlist = []
        for memb in struct:
            memb = SVType(memb)
            sub_tp = module.AllType.get(memb.tp)
            if memb.tp != 'logic' and memb.tp != 'logic signed' and len(sub_tp) != 1 : 
                sub_memlist = [(  self.L_(memb.name+'.')+name, *_ ) 
                    for  name, *_ in self.MemlistAppend(module, sig, sub_tp, ind, clk, lvl-1)] 
                self.print(sub_memlist, verbose=2)
            else:
                name = self.L_(memb.name +' '+sig.dimstr)
                width = str(memb.bw)
                active = 'LOW' if name[-2:] == '_n' else  ( 'HIGH' if width =='1' else 'N/A' )
                if '-1:0' in width:
                    width = width.split('-')[0][1:]
                io = sig.direction
                io = 'Input' if io =='input' else 'Output'
                memb_tp = self.cur_module.AllType.get(memb.tp)
                desp= f'\n{ind[2]}\\TODO\\\\\n'
                if memb_tp :
                    memb_tp = [SVType(i) for i in memb_tp]
                    if memb_tp[0].tp =='enum':
                        desp += self.EnumlDespStr(memb_tp[0].enumliteral, ind )
                sub_memlist = [(name, io, desp, width, active, clk)] 
            memlist += sub_memlist
        return memlist
    def RegMemMapStr(self, reg, regdesp): #reg is a SVEnuml object
        reg_bsize=regdesp.reg_bsize
        reg_slices=regdesp.reg_slices
        reg_defaults=regdesp.reg_defaults
        reg_bw=regdesp.reg_bw
        reg_bw_str=regdesp.reg_bw_str
        rw=regdesp.rw
        arr=regdesp.arr
        desp = regdesp.desp

        ind = Ind(1)
        name = self.L_(reg.name)
        arr_suf = self.L_(self.cur_regbk.arr_num_suf)
        ofs  = reg.num*reg_bsize
        arr = '' if arr=='' else f' [{name}{arr_suf}]' 
        s = f'{ind.b}\\memmap{{\\hyperref[subsubsec:{reg.name.lower()}]{{{name}}}{arr}}}'
        s += f'{{{hex(ofs).upper().replace("X","x")}}}{{{reg_bw}}}{{{rw}}}{{\n'
        s += f'{ind[1]}\\memDES{{\n'
        if desp is None:
            s += f'{ind[2]}\\TODO\n' if arr == '' else f'{ind[2]}Array register of size {name}{arr_suf}.\n'
        else:
            s += desp + '\n'
        s += f'{ind[1]}}}{{\n'
        reg_slices = self.RegSliceList(reg_slices) if reg_slices else None
        if reg_slices and reg_slices[0][0] == self.cur_regbk.reserved_name:
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
    def RegFieldStr(self, reg_name, regdesp): # str, self.cur_regbk.regslices, self.cur_regbk.regtypes; align slices to types!
        reg_slices = regdesp.reg_slices
        reg_types = regdesp.reg_types
        reg_membtypes = regdesp.reg_membtypes
        reg_defaults = regdesp.reg_defaults
        rw = regdesp.rw
        desp = regdesp.desp

        ind = Ind(0)
        _name = reg_name.replace('_', '\_')
        s = f'{ind.b}\\begin{{regfieldtable}}{{{reg_name.lower()}}}{{{_name} register field}}\n'
        reg_slices = self.RegSliceList(reg_slices)
        if reg_slices[0][0] == self.cur_regbk.reserved_name:
            s += f'{ind[1]}\\regfield{{{reg_slices[0][1]}}}{{RESERVED}}{{N/A}}{{reserved}}\n'
            reg_slices.pop(0)
        self.print( reg_types, verbose='RegFieldStr')
        for _slice, _type, _membtype, _default, _desp in zip(reg_slices, reg_types, reg_membtypes, reg_defaults, desp):
            _slice_name = _slice[0].replace('_', '\_')
            s += f'{ind[1]}\\regfield{{{_slice[1]}}}{{{_slice_name}}}{{{rw}}}{{\n'
            s += f'{ind[2]}\\regDES{{\n'
            s += f'{ind[3]}{_desp}\n'
            if (_membtype and _membtype[0].tp == 'enum'):
                s += self.EnumlDespStr(_membtype[0].enumliteral, ind=ind+1)
            s += f'{ind[3]}}}{{{_default.__str__()}}}{{N/A}}\n'
            s += f'{ind[2]}}}\n'
        s += f'{ind.b}\\end{{regfieldtable}}\n'
        return s
    def RegFieldSubSec(self, reg, regdesp):
        ofs = regdesp.ofs
        size = regdesp.size
        rw = regdesp.rw
        arr = regdesp.arr
        reg_bsize = regdesp.reg_bsize

        ind = Ind(0)
        _name = self.L_(reg) 
        arr_suf = self.L_(self.cur_regbk.arr_num_suf)
        arr_ofs = '' if not arr else f'+:{reg_bsize}{_name}{arr_suf}'
        s = f'{ind.b}\\subsubsection{{{_name}}} \\label{{subsubsec:{reg.lower()}}}\n'
        s += f'{ind[1]}\\begin{{paragitemize}}\n'
        s += f'{ind[2]}\\item \\textbf{{Address Offset:}} {ofs}{arr_ofs}\n'
        s += '' if arr=='' else f'{ind[2]}\\item \\textbf{{Register array size:}} {_name}{arr_ofs}\n'
        s += f'{ind[2]}\\item \\textbf{{Size:}} {size}\n'
        s += f'{ind[2]}\\item \\textbf{{Read/Write Access:}} {rw}\n'
        s += f'{ind[1]}\\end{{paragitemize}}\n'
        return s
    def EnumlDespStr ( self, enuml, ind ):
        desp = f'{ind[2]}\\\\\n'
        for e in enuml:
            _s = e.replace('_','\_')
            desp += f'{ind[2]}{_s}:\\\\\n'
        desp = desp[:-3]+'\n'
        return desp
    def SignalDesp( self, module=None, sel=None):
        module = self.dut if not module else module
        self.cur_module = module
        pfield = SVhier.portfield
        s = ''
        clk = None
        last_gp = None 
        for p in module.ports:
            _p = SVPort(p)
            if sel and _p.name not in sel:
                continue
            name = _p.name
            if _p.group != [] and  _p.group[0] != last_gp:
                last_gp = _p.group[0]
                s += f'\n\\emptyrowbold{{3}}\n'
                s += f'\\ganzinmergerowbold{{1.2}}{{3}}{{\\centering \\textbf{{{last_gp}}}}}\n' 
            if 'rst' in name or 'clk' in name:
                s += self.SignalStr(p, '\\TODO')
            else:
                s += self.SignalStr(p, clk)
            if 'clk' in name:
                clk = name.replace('_','\_')
        ToClip(s)
        return s
    def ParameterDesp(self, module=None, local=True):
        module = self.dut if not module else module
        self.cur_module = module
        param = module.paramsdetail if not local else module.paramports
        s = ''
        for p in param.keys():
            p = module.paramsdetail[p]
            if SVParam(p).paramtype != 'localparam':
                s += self.ParameterStr(p)
        ToClip(s)
        return s
    def RegMemMapDesp(self, pkg=None):
        s = ''
        regbk = SVRegbk(pkg) if pkg and type(pkg)==str else self.regbk
        self.cur_regbk = regbk
        for reg in regbk.addrs.enumls:
            reg_slices = regbk.regslices.get(reg.name)
            defaults = self.L_(regbk.GetDefaultsStr(reg.name, lst=True))
            self.print(defaults, verbose='RegMemMap')
            if defaults:
                defaults.reverse()
            reg_bw = regbk.params.get(f'{reg.name}_BW')
            reg_bw = reg_bw.num if reg_bw else None
            reg_bw_str = self.L_(regbk.GetBWStr(reg.name))
            width, rw, arr, *_= regbk.GetAddrCmt(reg.name) 
            reg_bw = width if not reg_bw else reg_bw
            reg_bw_str = width if not reg_bw_str else reg_bw_str
            tps =[i for i in regbk.regtypes.get(reg.name,[None])]
            tps.reverse()
            if len(tps) == 1 and tps[0] is not None and tps[0].tp == 'enum':
                desp = f'{Ind(3).b}\\TODO\\\\\n'
                desp += self.EnumlDespStr(tps[0].enumliteral, Ind(1) )
            else:
                desp = None 
            regdesp = RegDesp( regbk.regbsize, reg_slices, defaults, reg_bw, reg_bw_str, rw, arr, desp,
                                memblst=[   'reg_bsize', 
                                            'reg_slices',
                                            'reg_defaults',
                                            'reg_bw',
                                            'reg_bw_str',
                                            'rw',
                                            'arr',
                                            'desp'])
            s += self.RegMemMapStr(reg, regdesp) 
        ToClip(s)
        return s
    def RegFieldDesp(self, pkg=None):
        s = ''
        regbk = SVRegbk(pkg) if pkg and type(pkg)==str else self.regbk
        self.cur_regbk = regbk
        for reg in regbk.regfields:
            ofs = regbk.addrsdict[reg].num*regbk.regbsize
            ofs = hex(ofs).upper().replace('X', 'x')
            reg_bw = self.L_(regbk.GetBWStr(reg))
            width, rw, arr, *_= regbk.GetAddrCmt(reg) 
            reg_bw = width if not reg_bw else reg_bw
            regdesp = RegDesp(  ofs, reg_bw+'b', rw, arr, regbk.regbsize,
                                memblst =  ['ofs', 
                                            'size', 
                                            'rw', 
                                            'arr', 
                                            'reg_bsize'])
            s += self.RegFieldSubSec( reg, regdesp) 
            defaults = self.L_(regbk.GetDefaultsStr(reg, lst=True))
            if defaults:
                defaults.reverse()
            tps =[i for i in regbk.regtypes[reg]]
            tps.reverse()
            membtypes = [i for i in regbk.regmembtypes[reg]]
            membtypes.reverse()
            desp = [f'\\TODO\\\\' for i in membtypes]  
            regdesp = RegDesp(regbk.regslices[reg], tps, membtypes, defaults, rw, desp,
                                memblst=['reg_slices',
                                         'reg_types',
                                         'reg_membtypes',
                                         'reg_defaults',
                                         'rw',
                                         'desp']) 
            s += self.RegFieldStr (reg, regdesp)
            s += '\n'
        ToClip(s)
        return s
    def ExtractDesp(self, s):
        regfpat = r'(\regDES{)([^}]*)(})'
        pass
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
class RegDesp():
    def __init__(self, *arg, memblst=[], **kwargs):
        for i,v in enumerate(arg):
            self.__dict__[memblst[i]] = v
        for k,v in kwargs.items():
            self.__dict__[k]=v
if __name__ == '__main__':
    g = LatexGen()

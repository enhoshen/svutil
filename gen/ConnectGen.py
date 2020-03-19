import os
import sys
sys.path.append(os.environ.get('SVutil'))
from SVparse import *
from gen.SrcGen import * 
from SVclass import *
from itertools import zip_longest
import numpy as np
import re
class ConnectGen(SrcGen):
    r""" 
    This class saves you effor writing a top module connecting numbers of 
    sub-modules. With manual tweaks, user-comments, the module tries to declare logic,
    connect ports.
    """
    def __init__(self, ind=Ind(0), session=None):
        super().__init__(session=session)
        self.customlst += []
    # TODO
    @SVgen.Blk
    def LogicBlk(self, module, short=None, ind=None):
        s = f'{ind.b}// {module.name}\n' 
        pfield = SVhier.portfield 
        for p in module.ports:
            p = SVPort(p)
            name = [ x for x in re.split(rf'^i_|^o_', p.name) if x != ''][0] 
            short = '' if short is None else short
            if p.tp == 'logic' or p.tp == 'signed logic':
                s += f'{ind.b}{p.tp} {p.bwstr} {short}_{name}'
            else:
                s += f'{ind.b}{p.tp} {short}_{name}'
            if  not p.dimstr == '':
                s += f' {p.dimstr};\n'
            else:
                s += ';\n'
            
        yield s
    @SVgen.Blk
    def InsBlk(self, module, short=None, ind=None):
        s = '\n'
        s += ind.base + module.name+ ' #(\n'
        s_param = ''
        w = self.FindFormatWidth( [ (param+' ',) for param,v in module.paramports.items()])
        for param,v in module.paramports.items():
            if module.paramsdetail[param][SVhier.paramfield.paramtype] == 'parameter':
                s_param += f'{ind[1]},.{param:<{w[0]}}({param})\n'
        s_param = s_param.replace(f'{ind[1]},' , ind[1]+' ', 1)
             
        ins_name = self.InstanceName(module.name) if short is None else short
        sb = f'{ind.b}) u_{ins_name} (\n'
        s_port =''
        w = self.FindFormatWidth( [ (n+' ',) for io, n , *_ in module.ports])
        for io , n , dim , *_ in module.ports:
            if 'clk' in n:
                s_port += ind[1] + ',.' + f'{n:<{w[0]}}' + f'({self.clkstr})\n'
            elif 'rst' in n:
                s_port += ind[1] + ',.' + f'{n:<{w[0]}}' + f'({self.rststr})\n'
            else:
                s_port += ind[1] + ',.' + f'{n:<{w[0]}}' + (  (f'({n})\n') if dim ==() else (f'({{ >>{{{n}}} }})\n'))
                
        s_port = s_port.replace(f'{ind[1]},' , ind[1]+' ' , 1)
        s += s_param + sb + s_port + ind.base + ');\n' 
        yield s
    def InstanceName(self, s):
        name_split = re.split(rf'([A-Z][^A-Z]+)', s)
        return '_'.join([ x.lower() for x in name_split if x!=''])
    @SVgen.Clip
    def ShowIns(self, module=[], short=[], toclip=True, ind=None):
        banw = 25
        module = [self.dut] if not module else module
        logicban = (1,) + (self.Line3BannerBlk( banw, '//', 'Logic'),)
        logic = tuple( self.LogicBlk(m, short=s) for m,s in zip_longest(module, short) )
        logic = (1,) + logic 
        combban = (1,) + (self.Line3BannerBlk( banw, '//', 'Combinational'),)
        ins = tuple( self.InsBlk(m, short=s) for m,s in zip_longest(module, short) )
        ins = (1,) + ins
        s =  self.Genlist( [logicban, logic, '\n', combban, ins]) 
        self.print('\n',s, verbose=1)
        return s

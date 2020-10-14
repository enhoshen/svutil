import os
import sys
from SVutil.SVparse import *
from SVutil.gen.SrcGen import * 
from SVutil.SVclass import *
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
        self.customlst += [  'group_dft'
                            ,'logic_group_dft']
        self.userfunclst += ['ShowIns']
        self.group_dft = 'short'
        self.logic_group_dft = 'short'
    # TODO
    @SVgen.Blk
    def LogicBlk(self, module, short=None, group=None, ind=None):
        s = f'{ind.b}// {module.name}\n' 
        pfield = SVhier.portfield 

        cur_group = SVPort(module.ports[0]).group
        group = group.__iter__() if group is not None else None
        cur_group_name = next(group, self.logic_group_dft) if group is not None else self.logic_group_dft 
        w = 0
        for p in module.ports:
            p = SVPort(p)
            w = max(w, len(p.tp+p.bwstr))
        w += 1
        for p in module.ports:
            p = SVPort(p)
            if cur_group != p.group and group is not None:
                cur_group_name = next(group, self.logic_group_dft)
                cur_group = p.group
            _c = '' if short is None and cur_group_name == 'short' else cur_group_name
            connect = self.ConnectName(_c, short, p)
            if p.tp == 'logic' or p.tp == 'signed logic':
                s += f'{ind.b}{p.tp+" "+p.bwstr:<{w}} {connect}'
            else:
                s += f'{ind.b}{p.tp:<{w}} {connect}'
            if  not p.dimstr == '':
                s += f' {p.dimstr};\n'
            else:
                s += ';\n'
            
        yield s
    @SVgen.Blk
    def InsBlk(self, module, short=None, group=None, ind=None):
        '''
            Generates sub modules connection codes.
            Arguments:
                module: a list of SVhier to be connected as sub modules
                short : the shorthand for each sub modules
                group : each name for the group. group name for ports are 
                        comments seperating a number of ports.
        '''
        s = '\n'
        s += ind.base + module.name+ ' #(\n'
        s_param = ''
        w = self.FindFormatWidth( [ (param+' ',) for param,v in module.paramports.items()])
        for param,v in module.paramports.items():
            if module.paramsdetail[param][SVhier.paramfield.paramtype] == 'parameter':
                s_param += f'{ind[1]},.{param:<{w[0]}}({param})\n'
        s_param = s_param.replace(f'{ind[1]},' , ind[1]+' ', 1)
             
        ins_name = self.InstanceName(module.name) if short is None else short
        short = '' if short is None else short
        sb = f'{ind.b}) u_{ins_name} (\n'
        s_port =''
        w = self.FindFormatWidth( [ (n+' ',) for io, n , *_ in module.ports])
        cur_group = SVPort(module.ports[0]).group
        group = group.__iter__() if group is not None else None
        cur_group_name = next(group,self.group_dft) if group is not None else self.group_dft 
        for p in module.ports:
            p = SVPort(p)
            if cur_group != p.group and group is not None:
                cur_group_name = next(group,self.group_dft)
                cur_group = p.group
            connect = self.ConnectName(cur_group_name, short, p)
            #if 'clk' in n:
            #    s_port += ind[1] + ',.' + f'{p.name:<{w[0]}}' + f'({self.clk_name})\n'
            #elif 'rst' in n:
            #    s_port += ind[1] + ',.' + f'{p.name:<{w[0]}}' + f'({self.rst_name})\n'
            #else:
            s_port += f'{ind[1]},.{p.name:<{w[0]}}' + (f'({connect})\n' if p.dim ==() else f'({{ >>{{{connect}}} }})\n')
                
        s_port = s_port.replace(f'{ind[1]},' , ind[1]+' ' , 1)
        s += s_param + sb + s_port + ind.base + ');\n' 
        yield s
    def ConnectName(self, group, short, port):
        name = [ x for x in re.split(rf'^i_|^o_', port.name) if x != ''][0] 
        gname = group + '_' if group is not '' else ''
        if group == 'io':
            connect = port.name
        elif group == 'short':
            connect = f'{short}_{name}' if short is not '' else port.name
        else:
            connect = f'{gname}{name}'
        return connect
    def InstanceName(self, s):
        name_split = re.split(rf'([A-Z][^A-Z]+)|([A-Z]*(?=[A-Z][^A-Z]*))', s)
        return '_'.join([ x.lower() for x in name_split if x != '' and x is not None])
    @SVgen.Clip
    def ShowIns(self, module=[], short=[], group=[], toclip=True, ind=None):
        '''
            A SVgen Clip function to generates sub modules connection codes.
            Arguments:
                module: a list of SVhier to be connected as sub modules
                short : the shorthand for each sub modules
                group : each name for the group. group name for ports are 
                        the comments seperating ports.
                        There are two special group that makes connection
                        easier:
                        'short': the logics are prefixed with the shorthand
                        of the submodule.
                        'io': the logics are prefixed with 'i_'/'o_' depending
                        on its port direction.
        '''
        banw = 20
        module = [self.dut] if not module else module
        logicban = (1,) + (self.Line3BannerBlk( banw, '//', 'Logic'),)
        logic = tuple( self.LogicBlk(m, short=s, group=g) for m,s,g in zip_longest(module, short, group) )
        logic = (1,) + logic 
        combban = (1,) + (self.Line3BannerBlk( banw, '//', 'Combinational'),)
        ins = tuple( self.InsBlk(m, short=s, group=g) for m,s,g in zip_longest(module, short, group) )
        ins = (1,) + ins
        s =  self.Genlist( [logicban, logic, '\n', combban, ins]) 
        self.print('\n',s, verbose=1, level=True)
        return s

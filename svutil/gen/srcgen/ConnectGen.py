import os
import sys
from svutil.SVparse import *
from svutil.gen.SrcGen import *
from svutil.SVclass import *
from itertools import zip_longest
import numpy as np
import re


@SVgen.user_class
class ConnectGen(SrcGen):
    r"""
    This class saves you effor writing a top module connecting numbers of
    sub-modules. With manual tweaks, user-comments, the module tries to declare logic,
    connect ports.
    """

    def __init__(self, ind=Ind(0), session=None):
        super().__init__(session=session)
        self.customlst += ["group_dft", "logic_group_dft"]
        self.group_dft = "short"
        self.logic_group_dft = "short"

    # TODO
    @SVgen.blk
    def logic_block(self, module, short=None, group=None, ind=None):
        s = f"{ind.b}// {module.name}\n"
        pfield = SVhier.portfield

        cur_group = SVPort(module.ports[0]).group
        group = group.__iter__() if group is not None else None
        cur_group_name = (
            next(group, self.logic_group_dft)
            if group is not None
            else self.logic_group_dft
        )
        w = 0
        for p in module.ports:
            p = SVPort(p)
            w = max(w, len(p.tp + p.bwstr))
        w += 1
        for p in module.ports:
            p = SVPort(p)
            if cur_group != p.group and group is not None:
                cur_group_name = next(group, self.logic_group_dft)
                cur_group = p.group
            _c = "" if short is None and cur_group_name == "short" else cur_group_name
            connect = self.connect_name(_c, short, p)
            if p.tp == "logic" or p.tp == "signed logic":
                s += f'{ind.b}{p.tp+" "+p.bwstr:<{w}} {connect}'
            else:
                s += f"{ind.b}{p.tp:<{w}} {connect}"
            if not p.dimstr == "":
                s += f" {p.dimstr};\n"
            else:
                s += ";\n"

        yield s

    @SVgen.blk
    def instance_block(self, module, short=None, group=None, ind=None):
        """
        Generates sub modules connection codes.
        Arguments:
            module: a list of SVhier to be connected as sub modules
            short : the shorthand for each sub modules
            group : each name for the group. group name for ports are
                    comments seperating a number of ports.
        """
        s = "\n"
        s += ind.base + module.name + " #(\n"
        s_param = ""
        w = self.find_format_width(
            [(param + " ",) for param, v in module.paramports.items()]
        )
        for param, v in module.paramports.items():
            if module.paramsdetail[param][SVhier.paramfield.paramtype] == "parameter":
                s_param += f"{ind[1]},.{param:<{w[0]}}({param})\n"
        s_param = s_param.replace(f"{ind[1]},", ind[1] + " ", 1)

        ins_name = self.instance_name(module.name) if short is None else short
        short = "" if short is None else short
        sb = f"{ind.b}) u_{ins_name} (\n"
        s_port = ""
        w = self.find_format_width([(n + " ",) for io, n, *_ in module.ports])
        cur_group = SVPort(module.ports[0]).group
        group = group.__iter__() if group is not None else None
        cur_group_name = (
            next(group, self.group_dft) if group is not None else self.group_dft
        )
        for p in module.ports:
            p = SVPort(p)
            self.print(cur_group, p.group)
            if cur_group != p.group:
                s_port += '\n'
                cur_group = p.group
                if group is not None:
                    cur_group_name = next(group, self.group_dft)
            connect = self.connect_name(cur_group_name, short, p)
            # if 'clk' in n:
            #    s_port += ind[1] + ',.' + f'{p.name:<{w[0]}}' + f'({self.clk_name})\n'
            # elif 'rst' in n:
            #    s_port += ind[1] + ',.' + f'{p.name:<{w[0]}}' + f'({self.rst_name})\n'
            # else:
            s_port += f"{ind[1]},.{p.name:<{w[0]}}" + f"({connect})\n"

        s_port = s_port.replace(f"{ind[1]},", ind[1] + " ", 1)
        s += s_param + sb + s_port + ind.base + ");\n"
        yield s

    def connect_name(self, group, short, port):
        name = [x for x in re.split(rf"^i_|^o_", port.name) if x != ""][0]
        gname = group + "_" if group is not "" else ""
        if group == "io":
            connect = port.name
        elif group == "short":
            connect = f"{short}_{name}" if short is not "" else port.name
        else:
            connect = f"{gname}{name}"
        return connect

    def instance_name(self, s):
        name_split = re.split(rf"([A-Z][^A-Z]+)|([A-Z]*(?=[A-Z][^A-Z]*))", s)
        return "_".join([x.lower() for x in name_split if x != "" and x is not None])

    @SVgen.user_method
    @SVgen.clip
    def show_ins(self, module=[], short=[], group=[], toclip=True, ind=None):
        """
        A SVgen clip function to generates sub modules connection codes.
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
        """
        banw = 20
        module = [module] if isinstance(module, SVhier) else module 

        logicban = (1,) + (self.one_line_banner_blk(cmtc="//", text="Logic"),)
        logic = tuple(
            self.logic_block(m, short=s, group=g)
            for m, s, g in zip_longest(module, short, group)
        )
        logic = (1,) + logic
        combban = (1,) + (self.one_line_banner_blk(cmtc="//", text="Combinational"),)
        ins = tuple(
            self.instance_block(m, short=s, group=g)
            for m, s, g in zip_longest(module, short, group)
        )
        ins = (1,) + ins
        s = self.genlist([logicban, logic, "\n", combban, ins])
        self.print("\n", s, verbose=1, level=True)
        return s

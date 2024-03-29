import numpy as np
import parser as ps
import re
import os
from collections import namedtuple
from collections import deque
from subprocess import Popen, PIPE
from functools import reduce
from dataclasses import dataclass

from svutil.SVutil import SVutil, v_
from svutil.SVclass import *
from svutil.SVstr import *

@dataclass
class GBV(SVutil):
    """
    Just wrapper for environment variables
    The variables can be easily inspected via dataclass
    generated __repr__(): print(GBV())
    """
    # Nico makefile specified
    ARGS :str= os.environ.get("ARGS", "")
    TOPMODULE :str= os.environ.get("TOPMODULE", "")
    TEST :str= os.environ.get("TEST", "")
    TEST_CFG :str= os.environ.get("TEST_CFG", "")
    TEST_ID :str= os.environ.get("TEST_ID", "")
    # SVutil optional specified
    SVutilenv :str= os.environ.get("SVutil", "")
    TESTMODULE :str= os.environ.get("TESTMODULE", "")
    SV :str= os.environ.get("SV", "")
    TOPSV :str= os.environ.get("TOPSV", "")
    INC :str= os.environ.get("INC", "")
    HIER :str= os.environ.get("HIER", "")
    REGBK :str= os.environ.get("REGBK", "")
    PROJECT_PATH :str= os.environ.get("PROJECT_PATH", "")
    VERBOSE :str= os.environ.get("VERBOSE", 0)

    def show():
        print(GBV().__str__().replace(',','\n'))


def to_clip(s):
    clip = os.environ.get("XCLIP")
    clip = "xclip" if not clip else clip
    try:
        p = Popen([clip, "-selection", "clipboard"], stdin=PIPE)
        p.communicate(input=s.encode())
    except:
        print("xclip not found or whatever, copy it yourself")
        print("try install xclip and export XCLIP variable for the executable path")


class SVTypeDic(dict):
    def __init__(self, arg):
        super().__init__(arg)

    def get(self, k, d=None):
        if "::" in k:
            _pkg, _type = k.split("::")
            return SVparse.session.package[_pkg].types[_type]
        else:
            return super().get(k, d)


class SVParamDic(dict):
    def __init__(self, arg):
        super().__init__(arg)

    def get(self, k, d=None):
        if "::" in k:
            _pkg, _param = k.split("::")
            return SVparse.session.package[_pkg].params[_param]
        else:
            return super().get(k, d)


class SVEnumDic(dict):
    def __init__(self, arg):
        super().__init__(arg)

    def get(self, k, d=None):
        if "::" in k:
            _pkg, _enum = k.split("::")
            return SVparse.session.package[_pkg].enums[_enum]
        else:
            return super().get(k, d)


class SVParamDetailDic(dict):
    def __init__(self, arg):
        super().__init__(arg)

    def get(self, k, d=None):
        if "::" in k:
            _pkg, _param = k.split("::")
            return SVparse.session.package[_pkg].paramsdetail[_param]
        else:
            return super().get(k, d)


class HIERTP:
    FILE = 0
    MODULE = 1
    PACKAGE = 2


class SVhier:
    paramfield = paramfield
    typefield = typefield
    portfield = portfield
    enumfield = enumfield
    enumsfield = enumsfield
    enumlfield = enumlfield
    macrofield = macrofield

    def __init__(self, name=None, scope=None, tp: HIERTP=None):
        self.hier = (
            name  # this is fucking ambiguous, but str method use it so it remains
        )
        self.name = name
        self.params = {}
        self.paramsdetail = {}
        self.types = {}
        self.macros = {}
        self.child = {}
        self.paramports = {}
        self.ports = []
        self.protoports = []
        self.enums = {}
        self.imported = {}
        self.regs = {}
        self.sub_modules = []

        self.identifiers = {}
        self.hiertype = tp
        self._scope = scope
        self.valuecb = int
        if scope != None:
            scope.child[name] = self

    @property
    def scope(self):
        return self._scope

    @scope.setter
    def scope(self, scope):
        self._scope = scope

    @property
    def Params(self):
        if self._scope == None:
            return deque([h.params for _, h in self.child.items()])
        else:
            _l = self._scope.Params
            _l.appendleft(self.params)
            return _l

    @property
    def Enums(self):
        if self._scope == None:
            return deque([h.enums for _, h in self.child.items()])
        else:
            _l = self._scope.Enums
            _l.appendleft(self.enums)
            return _l

    @property
    def ParamsDetail(self):
        if self._scope == None:
            return deque([h.paramsdetail for _, h in self.child.items()])
        else:
            _l = self._scope.ParamsDetail
            _l.appendleft(self.paramsdetail)
            return _l

    @property
    def Types(self):
        if self._scope == None:
            _l = deque([h.types for _, h in self.child.items()])
            return _l
        else:
            _l = self._scope.Types
            _l.appendleft(self.types)
            return _l

    @property
    def Macros(self):
        if self._scope == None:
            _l = deque([self.macros]) + deque([h.macros for _, h in self.child.items()])
            return _l
        else:
            _l = self._scope.Macros
            _l.appendleft(self.macros)
            return _l

    @property
    def Portsdic(self):
        idx = self.portfield.name
        return {x[idx]: x for x in self.ports}

    ## types ##
    @property
    def SelfTypeKeys(self):
        return {x for x in self.types.keys()}

    @property
    def AllTypeKeys(self):
        return {x for i in self.Types for x in i.keys()}

    @property
    def AllType(self):
        return SVTypeDic({k: v for i in self.Types for k, v in i.items()})

    @property
    def ShowTypes(self):
        s = ""
        for k, v in self.types.items():
            s += self.type_str(k, v)
        return s

    @property
    def ShowAllTypes(self):
        s = ""
        for k, v in self.AllType.items():
            s += self.type_str(k, v)
        return s

    ## parameters ##
    @property
    def AllParamKeys(self):
        return {x for i in self.Params for x in i.keys()}

    @property
    def AllParams(self):
        return SVParamDic({k: v for i in self.Params for k, v in i.items()})

    @property
    def AllParamDetails(self):
        return SVParamDetailDic({k: v for i in self.ParamsDetail for k, v in i.items()})

    @property
    def ShowParams(self):
        w = 30
        s = f'{self.hier+" Parameters":-^{2*w}}'
        s += self.param_str(self.params, w)
        return s

    @property
    def ShowAllParams(self):
        w = 30
        s = f'{self.hier+" All Parameters":-^{2*w}}\n'
        s += self.param_str(self.AllParams, w)
        return s

    @property
    def ShowParamsDetail(self):
        w = 20
        s = f'{self.hier+" All Parameters detail":-^{2*w}}\n'
        s += self.field_str(self.paramfield, w)
        s += self.dict_str(self.paramsdetail, w)
        return s

    @property
    def ShowAllParamDetails(self):
        w = 20
        s = f'{self.hier+" All Parameters detail":-^{2*w}}\n'
        s += self.field_str(self.paramfield, w)
        s += self.dict_str(self.AllParamDetails, w)
        return s

    ## enums ##
    @property
    def AllEnums(self):
        return SVEnumDic({k: v for i in self.Enums for k, v in i.items()})

    ## macros ##
    @property
    def AllMacro(self):
        return {k: v for i in self.Macros for k, v in i.items()}

    ##
    @property
    def ShowPorts(self):
        w = 15
        s = ""
        for i in ["io", "name", "dim", "type"]:
            s += f"{i:{w}} "
        s += f'\n{"":=<{4*w}}\n'
        for io, n in self.protoports:
            s += f'{io:<{w}}{n:<{w}}{"()":<{w}}\n'
        for io, n, dim, tp, *_ in self.ports:
            s += f"{io:<{w}}{n:<{w}}{dim.__str__():<{w}}{tp:<{w}}\n"
        return s

    @property
    def ShowConnect(self, **conf):
        """ deprecated """
        s = ".*\n" if conf.get("explicit") == True else ""
        for t, n in self.protoports:
            if t == "rdyack":
                s += ",`rdyack_connect(" + n + ",)\n"
            if t == "dval":
                s += ",`dval_connect(" + n + ",)\n"
        for io, n, *_ in self.ports:
            s += ",." + n + "()\n"
        s = s[:-1].replace(",", " ", 1)
        return s

    def type_str(self, n, l, w=13):
        s = ""
        s += f'{self.hier+"."+n:-^{4*w}}\n'
        for i in ["name", "BW", "dimension", "type"]:
            s += f"{i:^{w}} "
        s += f' \n{"":=<{4*w}}\n'
        for i in l:
            for idx, x in enumerate(i):
                if idx < 4:
                    s += f"{x.__str__():^{w}} "
                else:
                    s += f"\n{x.__str__():^{4*w}} "
            s += "\n"
        return s

    def param_str(self, dic, w=13):
        s = ""
        for i in ["name", "value"]:
            s += f"{i:^{w}} "
        s += f'\n{"":=<{2*w}}\n'
        # l = self.params
        for k, v in dic.items():
            s += f"{k:^{w}}{self.valuecb(v).__str__() if type(v)==int else v.__str__():^{w}}\n"
        return s

    def field_str(self, field, w=13):
        s = ""
        for i in field.dic:
            s += f"{i:^{w}} "
        s += f'\n{"":=<{len(field.dic)*w}}\n'
        return s

    def dict_str(self, dic, w=13):
        s = ""
        for t in dic.values():
            for v in t:
                s += f"{self.valuecb(v).__repr__() if type(v)==int else v.__repr__():^{w}}"
            s += "\n"
        return s

    def __str__(self):
        sc = self._scope.hier if self._scope != None else None
        return (
            f"\n{self.hier:-^52}\n"
            + f'{"params":^15}:{[x for x in self.params] !r:^}\n'
            + f'{"scope":^15}:{sc !r:^}\n'
            + f'{"types":^15}:{[x for x in self.types] !r:^}\n'
            + f'{"child":^15}:{[x for x in self.child] !r:^}\n'
            + f'{"ports":^15}:{[io[0]+" "+n for io,n,*_ in self.ports] !r:^}\n'
        )

    def __svcompleterfmt__(self, attr, match):
        if "show" in attr:
            return f"{SVutil.cgreen}{match}{SVutil.creset}"
        else:
            return f"{match}"


class SVparse(SVutil):
    # One SVparse object one file, and it's also SVhier
    session = None
    session_var_lst = [
        "verbose",
        "parsed",
        "package",
        "module",
        "hiers",
        "paths",
        "gb_hier",
        "top",
        "base_path",
        "include_path",
        "sim_path",
        "src_path",
        "cur_scope",
        "cur_path",
        "flags",
        "path_level",
    ]

    @classmethod
    def __cls_getattr__(cls, n):
        if n in cls.session_var_lst:
            return getattr(cls.session, n)

    def __getattr__(self, n):
        if n in SVparse.session_var_lst:
            return getattr(SVparse.session, n)
        else:
            return SVparse.session.hiers[n]

    def __init__(self, name=None, scope=None, parse=None):
        self.parse = parse
        if name:
            if scope != None:
                self.cur_hier = SVhier(name, scope, HIERTP.FILE)
                SVsysfunc.cur_hier = self.cur_hier
                self.gb_hier.child[name] = self.cur_hier
            else:
                self.cur_hier = SVhier(name, self.gb_hier, HIERTP.FILE)
            SVparse.session.hiers[name] = self.cur_hier
        self.cur_key = ""
        self.keyword = {
            "logic": self.logic_parse,
            "parameter": self.param_parse,
            "localparam": self.param_parse,
            "typedef": self.typedef_parse,
            "struct": self.struct_parse,
            "package": self.hier_parse,
            "enum": self.enum_parse,
            "module": self.hier_parse,
            "import": self.import_parse,
            "input": self.port_parse,
            "inout": self.port_parse,
            "output": self.port_parse,
            "`include": self.include_read,
            "`rdyack_input": self.rdyack_parse,
            "`rdyack_output": self.rdyack_parse,
            "always_ff@": self.register_parse,
            "always_ff": self.register_parse,
            "`define": self.define_parse,
            "`ifndef": self.ifndef_parse,
            "`ifdef": self.if_def_parse,
            "`endif": self.endif_parse,
            "`elsif": self.elsif_parse,
            "`else": self.else_parse,
        }
        self.parselist = {
            "typedef",
            "package",
            "import",
            "module",
            "`include",
            "`define",
            "`ifdef",
            "`ifndef",
            "`endif",
            "`elsif",
            "`else",
        }
        self.alwaysparselist = {"`endif", "`elsif", "`else"}
        for k in self.cur_hier.AllMacro.keys():
            self.keyword["`" + k] = self.macro_parse
        self.cnt_ifdef = -1
        self.cnt_ifndef = -1
        self.cur_macrodef = None

        # flags
        # the subsequent code is preceded by `elsif macro
        self.flag_elsif_parsed = False
        # flag to parse subsequent code when some macro is set
        self.flag_parse = True
        # current parse is preceded by typedef
        self.flag_typedef = False

        self.cur_cmt = ""
        self.cur_s = SVstr("")
        self.last_pure_cmt = ""
        self.last_end = False
        self.inclvl = -1

    @classmethod
    def args_parse(cls):
        s = SVARGstr(GBV.ARGS)
        l = s.plus_split()
        for _l in l:
            func = _l[0]
            args = _l[1:]
            SVutil(cls.session.verbose).print(func, args, verbose="args_parse")
            if func == "define":
                m = s.define(args)
                for k, v in m.items():
                    cls.session.gb_hier.macros[k] = v
                    SVutil(cls.session.verbose).print(k, v[2](), verbose="args_parse")
        pass

    @classmethod
    def parse_files(cls, paths=[GBV.INC], inc=True, inclvl=-1):
        SVutil().print(
            "project path:", GBV.PROJECT_PATH, ", include path:", GBV.INC, trace=0
        )
        SVutil().print(
            "assumed base path of the project:", cls.session.base_path, trace=0
        )
        cls.args_parse()
        cls.session.paths = paths
        SVutil().print("parsing list:", cls.session.paths, trace=0)
        for p in cls.session.paths:
            if not cls.session.visited.get(os.path.normpath(p)):
                n = (p.rsplit("/", maxsplit=1)[1] if "/" in p else p).replace(".", "_")
                if inc:
                    n += "_sv"
                cls.session.cur_parse = SVparse(n, cls.session.gb_hier)
                cls.session.cur_parse.inclvl = inclvl
                cls.session.cur_parse.readfile(p if "/" in p else f"./{p}", inc=inc)
                cls.session.visited[os.path.normpath(p)] = True
            else:
                SVutil().print(
                    f'{"":>{SVparse.session.path_level*4}}{os.path.normpath(p)} visited!',
                    trace=2,
                    level=True,
                    color="YELLOW",
                    verbose=2,
                )
        cls.session.parsed = True

    # TODO Testbench sv file parse
    def readfile(self, path, inc=False):
        if inc:
            path = f"{SVparse.session.include_path}{path}.sv"
        path = os.path.normpath(path)
        self.print(
            f'{"":>{SVparse.session.path_level*4}}{path}',
            trace=2,
            level=True,
            verbose=2,
        )
        with open(path, "r", encoding="utf-8") as f:
            self.f = f
            self.cur_path = path
            self.lines = iter(self.f.readlines())
            self.cur_s, self.cur_cmt = self.rdline(self.lines)
            while 1:
                self.print(self.cur_s, verbose=5)
                _w = ""
                if self.cur_s == None:
                    return
                if self.cur_s.end():
                    _cmt = self.cur_cmt
                    self.cur_s, self.cur_cmt = self.rdline(self.lines)
                    self.cur_cmt = _cmt + self.cur_cmt if self.cur_s == "" else self.cur_cmt
                    continue

                _w = self.cur_s.lsplit()
                _catch = None
                if _w in self.parselist:
                    self.cur_key = _w
                    if (
                        SVparse.session.path_level == self.inclvl
                        and self.cur_key == "`include"
                    ):
                        continue
                    if self.flag_parse or _w in self.alwaysparselist:
                        _catch = self.keyword[_w](self.cur_s, self.lines)
                        
            self.f = None

    def include_read(self, s, lines):
        SVparse.session.path_level += 1
        parent_path = self.cur_path
        _s = s.s.replace('"', "")
        p = [_s, self.include_path + _s, self.src_path + _s, self.sim_path + _s]
        last_parse = SVparse.session.cur_parse
        visited = None
        for pp in p:
            pp = os.path.normpath(pp)
            if os.path.isfile(pp):
                if visited:
                    self.print(
                        "Warning, duplicated file:",
                        os.path.normpath(visited),
                        os.path.normpath(pp),
                    )
                visited = pp
                n = pp.rsplit("/", maxsplit=1)[1] if "/" in pp else pp
                n = n.replace(".", "_")
                if not SVparse.session.visited.get(pp):
                    # path = self.cur_path.rsplit('/',maxsplit=1)[0] + '/' + _s
                    SVparse.session.cur_parse = SVparse(n, self.cur_hier)
                    SVparse.session.cur_parse.inclvl = last_parse.inclvl
                    SVparse.session.cur_parse.readfile(pp)
                    SVparse.session.visited[pp] = True
                    last_parse.cur_hier.child[n] = SVparse.session.cur_parse.cur_hier
                    last_parse.cur_hier.sub_modules += [ 
                        m.name for m in SVparse.session.hiers[n].child.values()
                            if m.hiertype == HIERTP.MODULE
                    ] 
                else:
                    self.print(
                        f'{"":>{SVparse.session.path_level*4}}{os.path.normpath(pp)} visited!',
                        trace=2,
                        level=True,
                        color="YELLOW",
                        verbose=2,
                    )
        SVparse.session.path_level -= 1
        for k in SVparse.session.cur_parse.cur_hier.macros:
            last_parse.keyword['`' + k] = self.macro_parse
        SVparse.session.cur_parse = last_parse
        return

    def logic_parse(self, s, lines):
        """
        When the keyword logic is encountered:
        return information of the following identifier
        commas (multiple identifiers) is not supported...
        """
        # TODO signed keyword
        s.lstrip()
        sign = s.sign_parse()
        packed_dim = s.bracket_parse()
        bwstr = SVstr("" if packed_dim == () else packed_dim[-1])
        n, d = s.id_dim_arr_parse()
        if self.cur_key == 'logic':
            tp = ("signed " if sign == True else "") + "logic"
        else:
            tp = self.cur_key
        cmts = [""] if not self.cur_cmt else self.cur_cmt
        lst = []
        for _n, _d in zip(n, d):
            bw = bwstr.slice_to_num(self.cur_hier)
            dim = self.tuple_to_num(_d)+self.tuple_to_num(packed_dim[:-1])
            lst.append(
                ( _n,
                bw,
                dim,
                tp,
                [],  # enumliteral, not used , this fucking needs refactor
                cmts,)
            )
            if not self.flag_typedef:
                self.cur_hier.identifiers[_n] = Identifier(
                    name = _n,
                    tp = tp, #TODO
                    bwstr = bwstr,
                    bw = bw,
                    dim = dim,
                    dimstr = self.tuple_to_str(_d),
                )

        return lst

    def vector_parse(self, s, lines):
        """ parse an identifier with packed dimension specified"""
        dim = s.bracket_parse()
        name = s.id_parse()
        return (name, "", self.tuple_to_num(dim), "")

    def param_parse(self, s, lines):
        # TODO type parse (in SVstr) , array parameter
        # TODO multi-line statement, it has to know if it's parameter port... where
        # the end of the statement is not indicated by ;
        sign = s.sign_parse()
        tp = s.type_parse(self.cur_hier.AllTypeKeys.union(self.gb_hier.SelfTypeKeys))
        bw = s.bracket_parse()
        bwstr = self.tuple_to_str(bw)
        bw = 32 if tp == "int" and bw == () else self.bw2num(bw)
        name = s.id_parse()
        dim = s.bracket_parse()
        dimstr = self.tuple_to_str(dim)
        if "{" in s:
            while "}" not in s:
                _s, cmt = self.rdline(lines)
                s += _s
        if self.flag_port != 'pport':
            while ";" not in s:
                _s, cmt = self.rdline(lines)
                s += _s
        numstr = s.rstrip().rstrip(";").rstrip(",").s.lstrip("=").lstrip()
        numstrlst = SVstr(numstr).to_lst()
        # num =self.cur_hier.params[name]=s.lstrip('=').to_num(self.cur_hier.Params)
        num = self.cur_hier.params[name] = s.num_parse(self.cur_hier, self.package)
        self.cur_hier.paramsdetail[name] = (
            name,
            self.tuple_to_num(dim),
            tp,
            bw,
            num,
            bwstr,
            dimstr,
            numstr,
            self.cur_key,
            numstrlst,
        )
        if self.flag_port == "pport":
            self.cur_hier.paramports[name] = num
        return name, num

    def port_parse(self, s, lines):
        # bw = s.bracket_parse()
        if self.flag_port is not 'port':
            return None
        tp = s.type_parse(self.cur_hier.AllTypeKeys.union(self.gb_hier.SelfTypeKeys))
        tp = "logic" if tp == "" else tp
        sign = s.sign_parse()
        if sign and tp == "logic":
            tp = "logic signed"
        bw = s.bracket_parse()
        name = s.id_parse()
        self.print(name, verbose=4)
        if self.cur_cmt != "":
            for i in self.cur_cmt:
                if "reged" in i:
                    self.cur_hier.regs[name] = "N/A"
        bwstr = self.tuple_to_str(bw)
        bw = SVstr("" if bw == () else bw[0]).slice_to_num(self.cur_hier)
        dim = s.bracket_parse()
        dimstrtuple = dim
        dimstr = self.tuple_to_str(dim)
        # dim = self.tuple_to_num(s.bracket_parse())
        dim = self.tuple_to_num(dim)
        group = [s.lstrip() for s in self.last_pure_cmt]
        self.cur_hier.ports.append(
            (
                self.cur_key,
                name,
                dim,
                tp,
                bw,
                bwstr,
                dimstr,
                dimstrtuple,
                self.cur_cmt,
                group,
            )
        )

    def rdyack_parse(self, s, lines):
        _, args = s.function_parse()
        self.cur_hier.protoports.append(("rdyack", args[0]))

    def enum_parse(self, s, lines):

        if "logic" in s:
            s.lsplit()
        bw = s.bracket_parse()
        bw = SVstr("" if bw == () else bw[0])
        cmt = self.cur_cmt
        cmts = []
        _s = SVstr(s.s).lsplit("}") if "}" in s else s.s
        enums = [i for i in re.split(r"{ *| *, *", _s) if i is not ""]
        groups = [
            list([""]) if self.last_pure_cmt == "" else [list(self.last_pure_cmt)]
            for i in range(len(enums))
        ]
        cmt = [""] if cmt == "" else cmt
        cmts = [[""] for i in range(len(enums) - 1)]
        cmts += [cmt for i in enums]
        while "}" not in s:
            # TODO ifdef ifndef blabla
            _s, cmt = self.rdline(lines)
            cmt = [""] if cmt == "" else cmt
            group = [""] if self.last_pure_cmt == "" else self.last_pure_cmt
            s += _s
            _s = _s.lsplit("}") if "}" in _s else _s.s
            _enum = [i for i in re.split(r"{ *| *, *", _s) if i is not ""]
            if _enum == []:
                continue
            enums += _enum
            cmts += [[""] for i in range(len(_enum) - 1)] + [cmt]
            groups += [list(group) for i in range(len(_enum))]
        _pair = [(e, c) for e, c in zip(enums, cmts) if e != ""]
        enums = [p[0] for p in _pair]
        cmts = [p[1] for p in _pair]
        self.print(enums, cmts, verbose="enum_parse")
        # _s = s.lsplit('}')
        # enums = SVstr(_s).replace_split(['{',','] )
        enum_name, enum_num, cmts, idxs, sizes, name_bases, groups = self.enum2_num(
            enums, cmts, groups
        )
        for _name, _num in zip(enum_name, enum_num):
            self.cur_hier.params[_name] = _num
            self.cur_hier.paramsdetail[_name] = (
                _name,
                (),
                "",
                1,
                _num,
                "",
                "",
                "",
                "enum literal",
            )
        s.lsplit("}")
        n = s.id_arr_parse()
        self.cur_s = s
        for _n in n:
            self.cur_hier.enums[_n] = (
                enum_name,
                enum_num,
                cmts,
                idxs,
                sizes,
                name_bases,
                groups,
            )
        return [
            (_n, bw.slice_to_num(self.cur_hier), (), "enum", enum_name, cmts, groups)
            for _n in n
        ]

    def import_parse(self, s, lines):
        while ";" not in s:
            _s, cmt = self.rdline(lines)
            s += _s
        s = s.split(";")[0]
        for _s in s.split(","):
            search = re.search(rf"\s*::\s*", _s)
            if search:
                _pkg, _param = _s.lstrip().rstrip().split(search.group())
            else:
                self.print(f"only support importing packages: \"{_s}\"")
                return

            if _pkg in self.cur_hier.imported:
                self.cur_hier.imported[_pkg] += [_param]
            else:
                self.cur_hier.imported[_pkg] = [_param]

            if _pkg not in SVparse.session.package:
                self.print(f"Package {_pkg} not yet parsed", verbose=2)
                return

            if _param == "*":
                for k, v in SVparse.session.package[_pkg].params.items():
                    self.cur_hier.params[k] = v
                for k, v in SVparse.session.package[_pkg].paramsdetail.items():
                    self.cur_hier.paramsdetail[k] = v
                for k, v in SVparse.session.package[_pkg].types.items():
                    self.cur_hier.types[k] = v
                for k, v in SVparse.session.package[_pkg].enums.items():
                    self.cur_hier.enums[k] = v
            else:
                if _param in SVparse.session.package[_pkg].params:
                    self.cur_hier.params[_param] = SVparse.session.package[_pkg].params[
                        _param
                    ]
                if _param in SVparse.session.package[_pkg].paramsdetail:
                    self.cur_hier.paramsdetail[_param] = SVparse.session.package[
                        _pkg
                    ].paramsdetail[_param]
                if _param in SVparse.session.package[_pkg].types:
                    tp = SVparse.session.package[_pkg].types[_param]
                    self.keyword[_param] = self.logic_parse
                    for t in tp:
                        # register each imported type to types
                        t = SVType(t)
                        _tp = SVparse.session.package[_pkg].types.get(t.tp)
                        if _tp:
                            self.cur_hier.types[t.tp] = _tp
                            self.keyword[t.tp] = self.logic_parse
                    self.cur_hier.types[_param] = tp
                if _param in SVparse.session.package[_pkg].enums:
                    self.cur_hier.enums[_param] = SVparse.session.package[_pkg].enums[
                        _param
                    ]

    def struct_parse(self, s, lines):
        _step = 0
        rule = ["{", "}"]
        attrlist = []
        _s = s
        while 1:
            _w = ""
            if _step == 2:
                name = _s.id_arr_parse()
                return (name, attrlist)
            if _s.end():
                _s, self.cur_cmt = self.rdline(lines)
                continue
            _w = _s.lsplit()
            if _w == rule[_step]:
                _step = _step + 1
                continue
            if _w in self.keyword:
                _k = self.cur_key
                self.cur_key = _w
                _catch = self.keyword[_w](_s, lines)
                self.cur_key = _k
                if type(_catch) == list:
                    attrlist += _catch
                else:
                    attrlist.append(_catch)
                continue
            types = self.cur_hier.AllTypeKeys
            tp = SVstr(_w).type_parse(types)
            if not tp == "":
                if "::" in tp:
                    _pkg, _param = tp.split("::")
                    self.cur_hier.types[tp] = SVparse.session.package[_pkg].types[
                        _param
                    ]
                    bw = np.sum(
                        [x[1] for x in SVparse.session.package[_pkg].types[_param]]
                    )
                else:
                    bw = np.sum([x[1] for x in self.cur_hier.AllType[tp]])
                n, d = _s.id_dim_arr_parse()
                # _n = _s.id_parse()
                # dim = _s.bracket_parse()
                # dimstr = self.tuple_to_str(dim)
                # dim = self.tuple_to_num(dim)
                attrlist += [
                    (_n, bw, self.tuple_to_num(_d), tp, [], self.cur_cmt)
                    for _n, _d in zip(n, d)
                ]

    def typedef_parse(self, s, lines):
        """ when keyword typedef is met """
        self.flag_typedef = True
        _w = s.lsplit()
        types = self.cur_hier.AllTypeKeys
        tp = SVstr(_w).type_parse(types)
        if not tp == "":
            try:
                _pkg, _param = tp.split("::")
                self.cur_hier.types[tp] = SVparse.session.package[_pkg].types[_param]
            except:
                pass
        _k = self.cur_key
        self.cur_key = _w
        _m = self.keyword.get(_w)
        _catch = ()

        # if typedef is followed by types (EX: logic, struct or user defined types)
        # use the keyword parsing function, otherwise treats the remaining string like 
        # regular logic identifier using vector_parse; regular logic identifier takes 
        # the format of [type][packed array dimension] {identifier}
       
        if _m != None:
            _catch = _m(s, lines)
        else:
            _catch = self.vector_parse(s, lines)
            # (identifier, bandwidth ,packed dimension, type) 
            _catch = (
                _catch[0],
                int(np.multiply.reduce(_catch[2]) * self.cur_hier.types[_w][0][1]),
                _catch[2],
                _w,
            )
        self.cur_key = _k
        # struct type 
        if _w == "struct":
            for n in _catch[0]:
                self.cur_hier.types[n] = _catch[1]
                self.keyword[n] = self.logic_parse
        else:
            # enum type 
            if type(_catch) == list:
                for n in _catch:
                    self.cur_hier.types[n[0]] = [n]
                    self.keyword[n[0]] = self.logic_parse
            # alias type 
            else:
                self.cur_hier.types[_catch[0]] = [_catch]
                self.keyword[_catch[0]] = self.logic_parse
        self.flag_typedef = False

    def register_parse(self, s, lines):
        endflag = 0
        _w = ""
        while True:
            if endflag == 0 and s.end():
                break
            if s.end():
                s, self.cur_cmt = self.rdline(lines)
                continue
            pre_w = _w
            _w = s.lsplit()
            if re.match(r"\bbegin\b", _w):
                endflag += 1
            if re.match(r"\bend\b", _w):
                endflag -= 1
            if s.s[0:2] == "<=":
                pre_w = _w
                _w = s.lsplit("<=")
                _w = s.lsplit()
                self.cur_hier.regs[pre_w] = _w

    def hier_parse(self, s, lines):
        self.cur_s = s
        self.flag_port = ""
        self.port_flag(self.cur_key, self.cur_s.s)
        name = self.cur_s.id_parse()
        new_hier = SVhier(name, self.cur_hier)
        SVparse.session.hiers[name] = new_hier
        if self.cur_key == "module":
            SVparse.session.module[name] = new_hier
            self.cur_hier.scope.identifiers[name] = new_hier
            new_hier.hiertype = HIERTP.MODULE
        if self.cur_key == "package":
            SVparse.session.package[name] = new_hier
            new_hier.hiertype = HIERTP.PACKAGE
        self.cur_hier = new_hier
        _end = {"package": "endpackage", "module": "endmodule"}[self.cur_key]
        self.last_pure_cmt = ""
        while 1:
            _w = ""
            if self.cur_s == None:
                break
            if self.cur_s.end():
                self.cur_s, self.cur_cmt = self.rdline(lines)
                continue
            _w = self.cur_s.lsplit()
            self.port_flag(_w, self.cur_s.s)
            if _w == _end:
                break
            if _w in self.keyword:
                _k = self.cur_key
                self.cur_key = _w
                _catch = self.keyword[_w](self.cur_s, lines)
                self.cur_key = _k
        self.cur_hier = self.cur_hier.scope

    def define_parse(self, s, lines):
        name, args = s.function_parse()
        _s = s.s
        while True:
            if s == None or s.end():
                break
            else:
                if s.s[-1] == "\\":
                    s, self.cur_cmt = self.rdline(lines)
                    _s += s.s
                    continue
                else:
                    break
        self.print(_s, verbose=56)
        _s = _s.replace("\\", "")
        func = lambda *_args: reduce(
            lambda x, y: re.sub(rf"(\b|(``)){y[1]}(\b(``)|\b)", str(y[0]), x),
            [i for i in zip(_args, args)],
            _s,
        )
        if self.gb_hier.macros.get(name):
            pass
        else:
            self.cur_hier.macros[name] = (args, _s, func)
        self.keyword["`" + name] = self.macro_parse
        self.parselist.add("`" + name)
        self.cur_s.s = ""
        self.print(
            re.sub(
                rf"(\b|(``))b(\b(``)|\b)",
                "2",
                re.sub(rf"(\b|(``))a(\b(``)|\b)", "4", _s),
            ),
            verbose=4,
        )

    def macro_parse(self, s, lines):
        # TODO not gonna work properly
        k = self.cur_key
        s.lstrip()
        _s = s.s
        reobj = re.search(r"^[(]", _s)
        if reobj:
            span = SVstr(_s).first_bracket_span()
            try:
                s.s = (
                    SVstr(k + _s[: span[1] + 1]).macro_func_expand(self.cur_hier.AllMacro)
                    + s.s[span[1] + 1 :]
                )
            except:
                self.print("Macro expansion failed", k, _s, verbose=2)
            self.print(k + _s[: span[1] + 1], verbose="macro_parse")
            self.print(s.s, verbose="macro_parse")
        else:
            s.s = SVstr(k).simple_macro_expand(self.cur_hier.AllMacro) + s.s
        self.print(k, verbose=3)

    def if_def_parse(self, s, lines):
        self.cnt_ifdef += 1
        self.cur_macrodef = "ifdef"
        n = s.id_parse()
        if self.cur_hier.AllMacro.get(n):
            self.flag_parse = True
        else:
            self.flag_parse = False
        pass

    def ifndef_parse(self, s, lines):
        self.cnt_ifndef += 1
        self.cur_macrodef = "ifndef"
        n = s.id_parse()
        if not self.cur_hier.AllMacro.get(n):
            self.flag_parse = True
        else:
            self.flag_parse = False
        pass

    def elsif_parse(self, s, lines):
        self.cur_macrodef = "elsif"
        n = s.id_parse()
        if self.flag_elsif_parsed:
            self.flag_parse = False
        else:
            if self.cur_hier.AllMacro.get(n):
                self.flag_parse = True
                self.flag_elsif_parsed = True
            else:
                self.flag_parse = False

    def else_parse(self, s, lines):
        self.cur_macrodef = "else"
        if self.flag_elsif_parsed:
            self.flag_parse = False
        else:
            self.flag_parse = True

    def endif_parse(self, s, lines):
        if self.cur_macrodef == "ifdef":
            self.cnt_ifdef -= 1
        elif self.cur_macrodef == "ifndef":
            self.cnt_ifndef -= 1
        self.cur_macrodef = None
        self.flag_parse = True
        self.flag_elsif_parsed = False

    def port_flag(self, w, s=None):
        """
        flag indicating in what stage the processing is
        pport: parameter port
        port: port
        end: inside module

        """
        # w+' '+s is the whole string being processed
        _s = w + " " + s
        if re.match(r"module[\w\W]*;", _s) and self.flag_port == "":
            self.flag_port = "end"
        if "#" in w and self.flag_port == "":
            self.flag_port = "pport"
        #if self.flag_port == "pport":
        if "input" in w or "output" in w or re.match(r"^ *[)] *[(]", _s):
            self.flag_port = "port"
        if re.match(r"^ *[)]\s*;", _s) and self.flag_port == "port":
            self.flag_port = "end"

    def rdline(self, lines):
        s = next(lines, None)
        # line number TODO
        # return SVstr(s.lstrip().split('//')[0].rstrip().strip(';')) if s != None else None
        # return SVstr(s.lstrip().split('//')[0].rstrip()) if s != None else None
        if s == None:
            return (None, None)
        _s = SVstr(s.lstrip())
        cmt = _s.comment_parse()
        self.cur_s = _s
        self.cur_cmt = cmt
        if _s.end():
            self.print(self.last_end, self.last_pure_cmt, verbose="rdline")
            if not self.last_end or self.last_pure_cmt == "":
                if self.cur_cmt != "":
                    self.last_pure_cmt = self.cur_cmt
                    self.last_end = _s.end()
            else:
                self.last_pure_cmt += self.cur_cmt
                self.last_end = _s.end()
        else:
            self.last_end = _s.end()
        return (_s.rstrip(), cmt)

    def tuple_to_num(self, t):
        _t = []
        for i in t:
            if ':' in i:
                _t.append(SVstr(i).slice_to_num(self.cur_hier, self.package))
            else:
                _t.append(SVstr(i).num_parse(self.cur_hier, self.package))
        return tuple(_t)
        #return tuple(map(lambda x: SVstr(x).num_parse(self.cur_hier, self.package), t))
        # num_parse(params=self.cur_hier.Params, macros=self.cur_hier.AllMacro, package=self.package)

    def tuple_to_str(self, t):
        return reduce(lambda x, y: x + f"[{y}]", t, "")

    def bw2num(self, bw):
        return SVstr("" if bw == () else bw[0]).slice_to_num(self.cur_hier)

    def enum2_num(self, enum, cmt, group):
        ofs = 0
        cmts = []
        groups = []
        name = []
        name_base = []
        idx = []
        size = []
        num = []
        import copy

        for e, c, g in zip(enum, cmt, group):
            _s = SVstr(e)
            _name = _s.id_parse()
            bw = _s.bracket_parse()
            bw = (
                SVstr(bw[0]).slice_to_two_num(self.cur_hier)
                if bw
                else SVstr("").slice_to_two_num(self.cur_hier)
            )
            _num = _s.num_parse(self.cur_hier, SVparse.session.package)
            if type(bw) == tuple:
                bw = (0, bw[1] - 1) if bw[0] == "" else bw
                for i in range(bw[1] - bw[0] + 1):
                    idx.append(bw[0] + i)
                    size.append(bw[1] - bw[0] + 1)
                    name.append(_name + str(bw[0] + i))
                    name_base.append(_name)
                    num.append(ofs + i if _num == "" else _num + i)
                    cmts.append(c)
                    groups.append(g)
                ofs = (
                    ofs + bw[1] - bw[0] + 1 if _num == "" else _num + bw[1] - bw[0] + 1
                )
            else:
                idx.append(0)
                size.append(0)
                cmts.append(c)
                groups.append(g)
                name_base.append(_name)
                name.append(_name)  # TODO
                num.append(ofs if _num == "" else _num)
                try:
                    ofs = ofs + 1 if _num == "" else _num + 1
                except:
                    self.print(f"enum number intepretation failed", verbose=2)
                    ofs = _num + "+1"
            self.cur_hier.params[name[-1]] = num[-1]
        return name, num, cmts, idx, size, name_base, groups


class SVparseSession(SVutil):
    def __init__(self, name=None, scope=None, verbose=None):
        """
        this part must be synced with SVparse class initialization.
        Might as well do an overhaul of refactor.
        """
        self.verbose = v_(VERBOSE)
        self.parsed = False
        self.package = {}
        self.module = {}
        self.hiers = {}
        self.paths = []
        self.visited = {}
        self.gb_hier = SVhier("files", None)
        self.gb_hier.types = {"integer": None, "int": None, "logic": None}
        _top = GBV.TOPMODULE
        self.top = _top if _top != None else ""
        if GBV.PROJECT_PATH:
            self.base_path = os.path.join(os.environ.get("PWD"), GBV.PROJECT_PATH, "")
        else:
            match = re.search(r"/sim\b|/include\b|/src\b", os.environ.get("PWD"))
            if match:
                self.base_path = os.path.join(
                    os.environ.get("PWD")[0 : match.span()[0]], ""
                )
            else:
                self.base_path = os.environ.get("PWD")
        self.include_path = self.base_path + "include/"
        self.sim_path = self.base_path + "sim/"
        self.src_path = self.base_path + "src/"
        self.cur_scope = ""
        self.cur_path = ""
        self.flags = {"pport": False, "module": False}  # TODO
        self.path_level = 0

    def swap_to(self):
        SVparse.session = self

    def hiers_update(self):
        global hiers
        hiers = EAdict(self.hiers)  # TODO

    def parse_first_argument(self):
        import sys

        self.file_parse(paths=[sys.argv[1]])

    def reset(self):
        self.parsed = False
        self.package = {}
        self.hiers = {}
        self.paths = []
        self.visited = {}
        self.gb_hier = SVhier("files", None, HIERTP.FILE)
        self.gb_hier.types = {"integer": None, "int": None, "logic": None}

    def show_file(n, start=0, end=None):
        with open(self.paths[n], "r") as f:
            l = f.readlines()
            end = start + 40 if end == None else end
            for i, v in enumerate([x + start for x in range(end - start)]):
                print(f"{i+start:<4}|", l[v], end="")

    def show_paths(self):
        for i, v in enumerate(self.paths):
            print(i, ":  ", v)

    def file_parse(self, paths=None, inc=True, inclvl=-1):
        """
        Arguments:
            inc: the paths are the include file name (without .sv suffix)
            inclvl: the depth at which the included files to be parsed
        """
        if not paths:
            paths = [(GBV.INC)]
        self.swap_to()
        if self.parsed == True:
            self.print("Incremental parse")
        paths = [paths] if type(paths) == tuple else paths
        SVparse.parse_files(paths, inc=inc, inclvl=inclvl)
        self.parsed = True
        self.hiers_update()

    def reload(self, paths=None, inc=True, inclvl=-1):
        self.reset()
        self.file_parse(paths=paths, inc=inc, inclvl=inclvl)

    def top_all_param_e_adict(self):
        return EAdict(self.gb_hier[TOPMODULE].AllParams)

    def param_get(self, s, svhier):
        """ deprecated """
        if "::" in s:
            _pkg, _param = s.split("::")
            return self.package[_pkg].params[_param]
        else:
            return svhier.AllParams.get(s)

    def type_get(self, s, svhier):
        """ deprecated """
        if "::" in s:
            _pkg, _type = s.split("::")
            return self.package[_pkg].types[_type]
        else:
            return svhier.AllType.get(s)


if __name__ == "__main__":

    # sv = SVparse('SVparse',None)
    # print (sv.gb_hier.child)
    # ss = SVstr
    # print(ss('[3]').bracket_parse() )
    # print(sv.param_parse(ss('DW  =4;'))  )
    # print(ss(' happy=4;').id_parse())
    # print(sv.parameter)
    # print(ss('waddr;\n').id_parse() )
    # print(sv.logic_parse(ss(' [ $clog2(DW):0]waddr[3] [2][1];')) )
    # print(sv.slice_to_num(' 13:0 '))
    # print(sv.struct_parse(iter([' {logic a [2];','parameter sex =5;',' logic b [3];', '} mytype;',' logic x;'])))
    # import sys
    # SVparse.session.parse_files(sys.argv[1])
    #
    # print('typedef \'Conf\' under PECfg:')
    #    #SVparse.session.IncludeFileParse('PE_compile.sv')
    # for i in SVparse.session.gb_hier.child['DatapathControl.sv'].Types:
    #    print(i)
    # for i in SVparse.session.hiers.keys():
    #    print (i)
    # print(SVparse.session.hiers['PECtlCfg'])
    SVstr.verbose = VERBOSE
    SVparse.session.verbose = VERBOSE
    S = SVparseSession()
    S.parse_first_argument()

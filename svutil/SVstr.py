import numpy as np
import parser as ps
import re
import os
from subprocess import Popen, PIPE
from svutil.SVutil import SVutil, v_
from svutil.SVclass import *

VERBOSE = os.environ.get("VERBOSE", 0)
# verilog system function implementation
# to_num can evaulate the functions directly
class SVsysfunc (SVutil):
    # current SVhier
    def __init__(self, cur_hier, package):
        super().__init__()
        self.package = package
        self.cur_hier = cur_hier

    def clog2(self, s):
        if isinstance(s, str):
            try:
                num = int(s)
            except:
                num = self.cur_hier.params[s] 
        else:
            num = s
        return int(np.ceil((np.log2(num))))

    def bits(self, s):
        if self.cur_hier.types.get(s):
            bits = 0
            for i in self.cur_hier.types.get(s):
                i = SVType(i)
                bits += i.bits()
            return bits


class SVstr(SVutil):
    """ String wrapper for parsing systemverilog code
    Note that *_parse methods will parse and change the string in-place
    """
    sp_chars = ['=', '{', '}', '[', ']', '::', ';', ',', '(', ')', '#']
    op_chars = ['+', '-', '*', '/', '(', ')', '<<', '>>']
    verbose = v_(VERBOSE)

    def __init__(self, s):
        self.s = s

    def __repr__(self):
        return self.s

    def __add__(self, foo):
        return SVstr(self.s + foo.s)

    def __iadd__(self, foo):
        self.s += foo.s
        return self

    def split(self, sep=None, maxsplit=-1):
        return self.s.split(sep=sep, maxsplit=maxsplit)

    def lstrip(self, chars=None):
        self.s = self.s.lstrip(chars)
        return self

    def rstrip(self, chars=None):
        self.s = self.s.rstrip(chars)
        return self

    def lsplit(self, sep=None):
        # split sep or any special chars from the start
        self.lstrip()
        if self.end():
            return ""
        _s = self.s
        if sep == None:
            _idx = SVstr(_s).first_s_pchar()
            _spidx = _s.find(" ")
            if _idx != -1 and (_idx < _spidx or _spidx == -1):
                if _idx == 0:
                    _s, self.s = _s[0], _s[1:]
                else:
                    _s, self.s = _s[0:_idx], _s[_idx:]
            else:
                _s = _s.split(maxsplit=1)
                self.s = _s[1] if len(_s) > 1 else ""
                _s = _s[0]
            return _s
        _s = _s.split(sep, maxsplit=1)
        if len(_s) != 0:
            self.s = _s[1]
            _s = _s[0]
        else:
            _s = ""
            self.s = ""
        return _s

    def span_replace(self, span, s):
        self.s = self.s[0 : span[0]] + s + self.s[span[1] + 1 :]
        return self

    def first_s_pchar(self):
        # FUCKING cool&concise implementation:
        return next((i for i, x in enumerate(self.s) if x in self.sp_chars), -1)
        # _specC = [ x for x in (map(self.s.find,self.sp_chars)) if x > -1]
        # _idx = -1 if len(_specC) == 0 else min(_specC)
        # return _idx

    def comment_parse(self):
        _s = self.s.rstrip()
        if "//" in _s:
            self.s = _s.split("//")[0]
            return _s.split("//")[1:]
        else:
            return ""

    def id_parse(self):
        """
        find one identifier at the start of the string
        TODO multiple ID ( often sperated by , )
        """
        if self.end():
            return ""
        self.s = self.s.lstrip()
        _idx = self.first_s_pchar()
        if _idx != -1:
            _s = self.s[0:_idx]
            self.s = self.s[_idx:]
            return _s.rstrip()
        _s = self.s.rstrip("\n").rstrip().split(maxsplit=1)
        self.s = _s[1] if len(_s) > 1 else ""
        return _s[0].rstrip(";")

    def id_arr_parse(self):
        n = []
        name = self.id_parse()
        n.append(name)
        while self.s != "" and self.s[0] == ",":
            self.s = self.s[1:]
            name = self.id_parse()
            n.append(name)
        return n

    def id_dim_arr_parse(self):
        n = []
        d = []
        name = self.id_parse()
        n.append(name)
        dim = self.bracket_parse()
        d.append(dim)
        while not self.end() and self.s[0] == ",":
            self.s = self.s[1:]
            name = self.id_parse()
            n.append(name)
            dim = self.bracket_parse()
            d.append(dim)
        return n, d

    def sign_parse(self):
        self.lstrip()
        if "unsigned" in self.s:
            self.s = self.s.replace("unsigned", "")
        else:
            if "signed" in self.s:
                self.s = self.s.replace("signed", "")
                return True
        return False

    def bracket_parse(self, bracket="[]"):
        """find and convert every brackets at the start of the string
        Parameters
            bracket: a string containing square bracket pairs and starting with [ 
        Returns
            tuple(num): a tuple of string in each of the bracket pairs
        """
        self.s = self.s.lstrip()
        num = []
        while 1:
            self.print(self.s, verbose="bracket_parse")
            if self.end() or self.s[0] != bracket[0]:
                break
            rbrack = self.s.find(bracket[1])
            num.append(self.s[1:rbrack])
            self.s = self.s[rbrack + 1 :].lstrip()
        return tuple(num)

    def type_parse(self, typekeylist):
        tp = ""
        temp = SVstr(self.s).lsplit()
        if temp in typekeylist or "::" in temp:
            tp = temp
            self.lsplit()
        return tp

    def keyword_parse(self, key, rules):
        _step = 0
        self.s = self.s.lsplit()
        if self.s == None:
            raise StopIteration
        if _step == len(rules):
            return

    def function_parse(self):
        self.print(self.end(), verbose=3)
        func = self.lsplit()
        if self.end():
            return func, []
        if self.s[0] == "(":
            _s, self.s = self.split(")", maxsplit=1)
            args = SVstr(_s).replace_split(["(", ","])
            return func, args
        else:
            return func, []

    def num_parse(self, cur_hier, package=None):
        """
        split the equal sign at the start of the string
        return left string as num, meaning that it converts
        the remain string no matter what ( determine if
        a string is an equation is hard), leaving the object
        empty. Try to expand text macro if macros is provided.
        """
        _s = self.lstrip("=")
        # if cur_hier.AllMacro:
        _s = SVstr(_s.multi_macro_expand(cur_hier.AllMacro))

        num = _s.to_num(cur_hier, package)
        self.s = ""
        return num

    def arit_to_num(self, s):
        pass

    def to_num(self, cur_hier, package=None):
        params = cur_hier.Params
        _s = self.s.lstrip()
        # if '$clog2' in _s:
        #    _temp = self.s.split('(')[1].split(')')[0]
        #    _s = _s.replace( _s[_s.find('$'):_s.find(')')+1] , 'int(np.log2('+ _temp + '))')
        sysfunc = SVsysfunc(cur_hier, package)
        _s_no_op = SVstr(_s).replace_split(self.op_chars + [",", "'", "{", "}"])
        for w in _s_no_op:
            if "::" in w:
                _pkg, _param = w.split("::")
                if _pkg in package:
                    _s = _s.replace(
                        _pkg + "::" + _param, str(package[_pkg].params[_param])
                    )
            for p in params:
                # substitute numbers found in cur_hier.params for identifiers in the string
                if w in p:
                    _s = re.sub(rf"\b{w}\b", str(p[w]), _s)
                    # _s = _s.replace( w , str(p[w]) )
                    break
        _s = _s.replace("$", "sysfunc.")
        _s = re.sub(rf"(sysfunc.\w*\s*)\((\w*)\)", r'\1("\2")', _s)
        _s = (
            _s.replace("'{", " [ ")
            .replace("{", " [ ")
            .replace("}", " ] ")
            .replace("(", " ( ")
            .replace(")", " ) ")
            .replace(",", " , ")
        )
        _s = re.sub(rf"/([^/])", rf"//\1", _s)
        slist = _s.split()
        for i, v in enumerate(slist):
            _n, _ = SVstr(v).base_convert()
            slist[i] = _n if _n else slist[i]
        _s = " ".join(slist)
        try:
            return eval(ps.expr(_s).compile("file.py"))
        except Exception as e:
            if _s != "":
                self.print(
                    f"to_num {_s} failed with {e},"
                    "return original string: {self.s}"
                    , verbose=3
                )
            return _s

    def base_convert(self):
        mapping = {"'b": "0b", "'h": "0x", "'o": "0o", "'d": "", "'": ""}
        rule = rf"(\'[bB]|\'[hH]|\'[oO]|\'[dD]|\')"
        if re.search(rule, self.s):
            lst = re.split(rule, self.s)
            _base = mapping[lst[1].lower()]
            _size = lst[0]
            _n = f"{_base}{lst[2]}"
            if lst[1] == "'":
                _n = f'0b{"":{lst[2]}<{32}}'
                self.print(_n, lst[2], verbose="base_convert")
            return _n, _size
        else:
            return None, None

    def to_lst(self):
        # TODO
        if not "{" in self.s:
            return [self.s]
        _s = SVstr(self.s.replace("'{", "{"))
        while True:
            span = _s.deepest_bracket_span()
            if not span:
                break
            spans = _s.s[span[0] : span[1] + 1]
            self.print(spans, verbose=46)
            spans = re.sub(r"{ *(?=\w|[\'])", '["', spans)
            spans = re.sub(r"(?<=\w) *,", '",', spans)
            spans = re.sub(r", *(?=\w)", ',"', spans)
            self.print(spans, verbose=46)
            spans = re.sub(r"(?<=\w) *}", '"]', spans)
            spans = re.sub(r"}", "]", spans)
            spans = re.sub(r"{", "[", spans)
            _s = _s.span_replace(span, spans)
        self.print(_s, verbose=46)
        try:
            return eval(ps.expr(_s.s).compile("file.py"))
        except:
            self.print(
                f"to_lst {_s.s} failed, return original string: {self.s}", verbose=3
            )
            return [self.s]

    def slice_to_num(self, cur_hier, package=None):
        if self.s == "":
            return 1
        _temp = self.s.replace("::", "  ")
        _idx = _temp.find(":")
        _s, _e = self.s[0:_idx], self.s[_idx + 1 :]
        try:
            return SVstr(_s).num_parse(cur_hier, package) - SVstr(_e).num_parse(cur_hier, package) + 1
        except (TypeError):
            self.print("slice_to_num fail, TypeError", verbose=3)
            self.print(self.s, verbose="Slice2Num")

    def slice_to_two_num(self, cur_hier, package=None):
        if self.s == "":
            return 1
        _temp = self.s.replace("::", "  ")
        _idx = _temp.find(":")
        self.print(_idx, verbose="slice_to_two_num")
        _s, _e = self.s[0:_idx] if _idx != -1 else "", self.s[_idx + 1 :]
        self.print(_s, _e, verbose="slice_to_two_num")
        return (SVstr(_s).num_parse(cur_hier, package), SVstr(_e).num_parse(cur_hier, package))

    def simple_macro_expand(self, macros):
        """
        Expand a simple substituion macro
        the string must start with ` and end with a word character
        """
        _s = self.s.rstrip().lstrip()
        exp = _s
        reobj = True
        while reobj:
            reobj = re.search(r"`(\w+)\b", exp)
            if reobj:
                m0 = reobj.group(0)
                m = reobj.group(1)
                exp = re.sub(rf"{m0}\b", f"macros['{m}'][2]()", exp)
        try:
            return eval(ps.expr(exp).compile("file.py"))
        except:
            self.print("macro expansion error", verbose=2)

    def macro_func_expand(self, macros):
        """
        Expand a potentially nested macro to a string.
        Limitation: the string start with ` and end with )
        Arguments:
            macros: the dictionary to find required macro definitions
        """
        _s = self.s.rstrip().lstrip()
        exp = _s
        self.print(exp, verbose="MacroFunc")
        reobj = True
        exp = re.sub(rf"[\']", "\\'", exp)
        exp = re.sub(rf'["]', '\\"', exp)
        exp = re.sub(rf"[(]", '("', exp)
        exp = re.sub(rf"[,]", '","', exp)
        exp = re.sub(rf"(?!^[`])[`]", '"+`', exp)
        exp = re.sub(rf"(?![)]$)[)]", '")+"', exp)
        exp = re.sub(rf"[)]$", '")', exp)
        while reobj:
            self.print(exp, verbose="MacroFunc")
            reobj = re.search(r"`(\w+)\b", exp)
            if reobj:
                m0 = reobj.group(0)
                m = reobj.group(1)
                if macros[m][0] == []:
                    exp = re.sub(rf"{m0}\b", f"macros['{m}'][2]()+\"", exp)
                else:
                    exp = re.sub(rf"{m0}\b", f"macros['{m}'][2]", exp)
            self.print(exp, verbose=3)
        try:
            return eval(ps.expr(exp).compile("file.py"))
        except:
            self.print("macro function expansion error", verbose=2)

    def multi_macro_expand(self, macros):
        _s = self.s
        self.print(_s, verbose="MacroFunc")
        nested = -1
        rbkt = 0
        exp = _s
        reobj = True
        while reobj:
            reobj = re.search(r"`(\w+)\b", exp)
            if reobj:
                span = reobj.span()
                self.print(exp[span[0] :], verbose="MacroFunc")
                funccheck = re.search(r"\s+[(]", exp[span[1] :])
                if funccheck and funccheck.span[0] != 0:
                    for i, c in enumerate(exp[span[0] :]):
                        if c == "(":
                            nested += 1
                        if c == ")":
                            nested -= 1
                            if nested == -1:
                                rbkt = i
                if rbkt == 0:
                    rbkt = span[1]
                    try:
                        exp = (
                            exp[0 : span[0]]
                            + SVstr(exp[span[0] : rbkt]).simple_macro_expand(macros)
                            + exp[rbkt:]
                        )
                    except:
                        self.print(exp, verbose="SimpleMacro")
                        break
                else:
                    exp = (
                        exp[0 : span[0]]
                        + SVstr(exp[span[0] : rbkt + 1]).macro_func_expand(macros)
                        + exp[rbkt + 1 :]
                    )
                nested = -1
                rbkt = 0
        return exp

    def first_bracket_span(self, bracket=["(", ")"]):
        """
        Find the first enclosed bracket span if the
        string start with bracket[0]
        """
        rbkt = 0
        lbkt = 0
        nested = 0
        for i, c in enumerate(self.s):
            self.print(i, c, verbose=5)
            if c == bracket[0]:
                if nested == 0:
                    lbkt = i
                nested += 1
            if c == bracket[1]:
                nested -= 1
                if nested == 0:
                    rbkt = i
        return (lbkt, rbkt)

    def deepest_bracket_span(self, bracket=["{", "}"]):
        """
        Find the deepest nested bracket span of a
        string
        """
        lbkt, rbkt = 0, -1
        for i, c in enumerate(self.s):
            rbkt += 1
            if c == bracket[0]:
                lbkt = i
            if c == bracket[1]:
                return (lbkt, rbkt)
        return None

    def delete_list(self, clist):
        _s = self.s
        for c in clist:
            _s = _s.replace(c, "")
        return _s

    def replace_split(self, clist):
        _s = self.s
        for c in clist:
            _s = _s.replace(c, " ")
        return _s.split()

    def __len__(self):
        return len(self.s)

    def __contains__(self, st):
        return st in self.s

    def end(self):
        return self.s == ""


class SVARGstr(SVstr):
    def pluslsplit(self):
        bcnt = False
        prvc = ""
        if self.end():
            return None
        for i, c in enumerate(self.s):
            if c == '"':
                if prvc == "\\":
                    pass
                else:
                    bcnt = False if bcnt else True
            if bcnt == False:
                if c == "+" or c == " ":
                    _s = self.s[0:i]
                    self.s = self.s[i + 1 :].lstrip()
                    return _s, c
            prvc = c
        _s = self.s
        self.s = ""
        return _s, ""

    def plus_split(self):
        l = []
        parse = self.pluslsplit()
        while parse:
            if parse == ("", "+"):
                l.append([])
            if parse[0] != "":
                l[-1].append(parse[0])
            parse = self.pluslsplit()
        return l

    def define(self, args):
        l = {}
        for a in args:
            _a = a.split("=")
            name = _a[0]
            text = _a[1] if len(_a) > 1 else ""
            func = lambda *, text=text: text
            l[name] = ([], text, func)
            self.print(func(), func, verbose="args_parse")
        for k, v in l.items():
            self.print(v[2](), verbose="args_parse")
        return l

    def incdir(self, args):
        # TODO
        return []

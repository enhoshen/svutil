import os
import inspect
import logging
from functools import wraps

import colorama

class SVutil:
    trace_format_width = 0
    creset = f"{colorama.Style.RESET_ALL}"
    ccyan = f"{colorama.Fore.CYAN}"
    cred = f"{colorama.Fore.RED}"
    cgreen = f"{colorama.Fore.GREEN}"
    cblue = f"{colorama.Fore.BLUE}"
    cyellow = f"{colorama.Fore.YELLOW}"

    def __init__(self, verbose=None):
        self.verbose = verbose
        pass

    def v_(self, verbose):
        try:
            self.verbose = int(verbose)
        except:
            self.verbose = verbose

    def print(self, *arg, verbose=None, trace=1, level=False, color=None, **kwarg):
        """
        Customized message print controlled with verbose level for each messages seperately
        and trace setting for code tracing configuration
            Args:
                verbose: determine the verbose level of the message, if not given, messages
                    is printed nonetheless
                trace: see self.trace
                level: print messages with lower verbose level than self.verbose if True
                    or else only the specific verbose level messages are printed
        """
        level = level if level else 0
        ins = inspect.getframeinfo(inspect.currentframe().f_back)
        if color is None:
            color = ""
        else:
            if color[0] == "\033":
                pass
            else:
                color = colorama.Fore.__dict__.get(color)
                color = "" if not color else color
        ins = (
            f"{colorama.Fore.CYAN}"
            + self.trace(ins, trace)
            + f"{colorama.Style.RESET_ALL}"
            + color
        )
        try:
            if level:
                if self.verbose >= verbose:
                    print(ins, *arg, f"{colorama.Style.RESET_ALL}", **kwarg)
            else:
                if self.verbose == verbose or verbose is None:
                    print(ins, *arg, f"{colorama.Style.RESET_ALL}", **kwarg)
        except:
            if verbose == self.verbose or verbose is None:
                print(ins, *arg, f"{colorama.Style.RESET_ALL}", **kwarg)

    def trace(self, ins, sel):
        """ code tracing using inspect module """
        home = os.environ.get("HOME", "")
        fn = ins.filename.replace(home, "")
        self.trace_format_width = max(self.trace_format_width, len(fn))
        w = self.trace_format_width
        trace = {
            None: "",
            0: f"[SVutil]",
            1: f"[{fn:<{w}},line:{ins.lineno}, in {ins.function}]",
            2: f"[{fn:<{w}}, in {ins.function}]",
            3: f"[{fn:<{w}},line:{ins.lineno}]",
            4: f"[{os.path.basename(fn)}, in {ins.function}]",
        }
        return trace[sel]

    def custom(self):
        self.print(f"{self.cyellow}Customizable variable: {self.creset}", trace=2)
        w = len(max(self.customlst, key=len))
        for i in self.customlst:
            v = self.__dict__[i]
            v = f'"{v}"' if type(v) == str else v.__str__()
            self.print(f"    {self.cgreen}{i:>{w}}:{self.creset} {v}", trace=2)

    # completer
    def __svcompleterattr__(self):
        return set()

    def __svcompleterfmt__(self, attr, match):
        if hasattr(self, "customlst") and attr in self.customlst:
            return f"{SVutil.cyellow}{match}{SVutil.creset}"
        if hasattr(super(), "customlst") and attr in super().customlst:
            return f"{SVutil.cyellow}{match}{SVutil.creset}"
        if (
            hasattr(self.__class__, "userfunclst")
            and attr in self.__class__.userfunclst
        ):
            return f"{SVutil.cgreen}{match}{SVutil.creset}"

        if hasattr(self, "userfunclst") and attr in self.userfunclst:
            return f"{SVutil.cgreen}{match}{SVutil.creset}"

        return f"{match}"

    # decorator class
    def user_class(cls):
        if not cls.__dict__.get("customlst"):
            cls.customlst = []

        if not cls.__dict__.get("userfunclst"):
            cls.userfunclst = []

        for name, method in cls.__dict__.items():
            if hasattr(method, "__svutil_custom__"):
                cls.customlst += [name]
            if hasattr(method, "__svutil_userfunc__"):
                cls.userfunclst += [name]

        for c in cls.__mro__:
            if hasattr(c, "customlst"):
                cls.customlst += c.customlst
            if hasattr(c, "userfunclst"):
                cls.userfunclst += c.userfunclst

        return cls

    def user_custom(orig):
        orig.__svutil_custom__ = True
        return orig

    def user_method(orig):
        orig.__svutil_userfunc__ = True
        return orig 


class SVcvar:
    """
    SVcvar marks customizable variables;
    as there could be considerable amount of such variable
    the class is named with a short but ambigous name
    """

    pass


def v_(verbose):
    try:
        verbose = int(verbose)
    except:
        pass
    return verbose

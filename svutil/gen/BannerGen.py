import os
import sys

sys.path.append(os.environ.get("SVutil"))
from svutil.SVparse import *
from svutil.SVgen import *
from svutil.SVclass import *
import itertools
import numpy as np
import time


@SVgen.user_class
class BannerGen(SVgen):
    def __init__(self, ind=Ind(0)):
        self.v_(VERBOSE)
        self.cur_ind = ind
        self.genpath = "./"
        self.customlst = ["name", "email", "genpath", "yyyy", "mm", "dd", "time"]
        self.name = []
        self.email = []
        _time = time.localtime()
        self.yyyy, self.mm, self.dd = _time.tm_year, _time.tm_mon, _time.tm_mday
        self.time = lambda: f"{self.yyyy}"

    @SVgen.user_method
    def user_reg(self, nmtuplelst):
        """
        customzie your name and email
        with a list of (name, email) pairs
        """
        if type(nmtuplelst) == tuple:
            nmtuplelst = [nmtuplelst]
        for (n, e) in nmtuplelst:
            print(n, e)
            self.name += [n]
            self.email += [f"<{e}>"]

    @SVgen.user_method
    def user_empty(self):
        self.name, self.email = [], []

    @SVgen.user_method
    def file_reg(self, f):
        self.filepath = f
        _f = f.split("/")[-1].rsplit(".", 1)
        self.filename = _f[0]
        _f = _f[-1] if len(_f) != 1 else ""
        self.filesuf = _f

    @SVgen.user_method
    def time_reg(self, yyyy, mm, dd):
        self.yyyy, self.mm, self.dd = yyyy, mm, dd


@SVgen.user_class
class GanzinBanner(BannerGen):
    def __init__(self, ind=Ind(0)):
        super().__init__()
        self.customlst += ["svcopyrightstr", "svstatementstr"]
        self.svcopyrightstr = (
            f"// Copyright (C) Ganzin Technology - All Rights Reserved\n"
        )
        self.svstatementstr = (
            f"// ---------------------------\n"
            + f"// Unauthorized copying of this file, via any medium is strictly prohibited\n"
            + f"// Proprietary and confidential\n"
            + f"//\n"
            + f"// Contributors\n"
            + f"// ---------------------------\n"
        )
        self.pycopyrightstr = self.svcopyrightstr.replace("//", "#")
        self.pystatementstr = self.svstatementstr.replace("//", "#")

    def inc_guard_str(self):
        return f"__{self.filename.upper()}_{self.filesuf.upper()}__"

    def banner_blk(self, suf="sv"):
        ind = self.cur_ind.copy()
        yield ""
        s = ""
        if suf == "sv":
            s = f"{ind.b}" + self.svcopyrightstr
            s += f"{ind.b}" + self.svstatementstr
            s.replace("\n", f"{ind.b}")
            for n, e in itertools.zip_longest(self.name, self.email):
                s += f"{ind.b}//"
                s += f" {n} {e}, {self.time()}\n"
            s += "\n"
        elif suf == "py" or suf == "Makefile":
            s = f"{ind.b}" + self.pycopyrightstr
            s += f"{ind.b}" + self.pystatementstr
            s.replace("\n", f"{ind.b}")
            for n, e in itertools.zip_longest(self.name, self.email):
                s += f"{ind.b}#"
                s += f" {n} {e}, {self.time()}\n"
            s += "\n"
        yield s

    def inc_guard_blk(self):
        ind = self.cur_ind.copy()
        yield ""
        s = f"{ind.b}`ifndef {self.inc_guard_str()}\n"
        s += f"{ind.b}`define {self.inc_guard_str()}\n\n"
        yield s
        yield f"\n{ind.b}`endif // {self.inc_guard_str()}"

    def banner_str(self, fr, suf="sv"):
        with open(fr, "r") as fr:
            ban = self.banner_blk(suf)
            try:
                fstr = fr.read()
            except:
                self.print("file read not supported")
                return None
            s = self.genlist([(ban,), fstr])
        return s

    def banner_incguard_str(self, fr, suf="sv"):
        with open(fr, "r") as fr:
            ban = self.banner_blk(suf)
            incg = self.inc_guard_blk()
            try:
                fstr = fr.read()
            except:
                self.print("file read not supported")
                return None
            s = self.genlist([(ban,), (incg,), fstr, incg])
        return s

    @SVgen.user_method
    def ban_write(self, fr=None, overwrite=False):
        """
        write Banner at the start of the file
        Arguments:
            fr = file name
            overwrite = True to write to the file, False to generate a new one
        """
        fpath = self.write(self.banner_str, fr, overwrite)
        if os.path.isfile(fpath) or not os.path.exists(fpath):
            self.print("Banner attached to ", fpath)

    @SVgen.user_method
    def ban_inc_write(self, fr=None, overwrite=False):
        fpath = self.write(self.banner_incguard_str, fr, overwrite)
        if os.path.isfile(fpath) or not os.path.exists(fpath):
            self.print("Banner, include guard attached to ", fpath)

    def write(self, strcallback=None, fr=None, overwrite=False):
        """
        Utility to write strings to files
        """
        if not strcallback:
            strcallback = self.banner_str
        if not fr:
            self.print("specify a file")
            return
        else:
            self.file_reg(fr)
        if not overwrite and os.path.isfile(self.filepath):
            self.print("file exists, make a copy, rename the file right away")
            fpath = self.genpath + self.filename + "_" + time.strftime("%m%d%H")
            if self.filesuf:
                fpath += "." + self.filesuf
        else:
            fpath = self.filepath
        _suf = "Makefile" if self.filename == "Makefile" else self.filesuf
        if os.path.isfile(fpath) or not os.path.exists(fpath):
            t = self.type_check(fr)
            s = strcallback(fr, _suf)
            if s is None or t is None:
                self.print("un-supported files or something went wrong")
                return ""
            with open(fpath, "w") as f:
                f.write(s)
        return fpath

    @SVgen.user_method
    def folder_ban_write(self, _dir=".", overwrite=False):
        """
        write Banner to every files of provided folder _dir
            Arguments:
                _dir = folder path
                overwrite = True to write to the file, False to generate a new one
        """
        assert self.name != [] and self.email != [], "specify name and email"
        for f in os.listdir(_dir):
            self.ban_write(_dir + "/" + f, overwrite)

    @SVgen.user_method
    def folder_ban_inc_write(self, _dir=".", overwrite=False):
        """
        write Banner and include guard to every files of the provided folder _dir
        This is meant for .sv files.
            Arguments:
                _dir = folder path
                overwrite = True to write to the file, False to generate a new one
        """
        for f in os.listdir(_dir):
            if f.endswith(".sv"):
                self.ban_inc_write(_dir + "/" + f, overwrite)
            else:
                self.ban_write(_dir + "/" + f, overwrite)

    def type_check(self, fr):
        return fr.endswith((".sv", ".py", "Makefile"))


if __name__ == "__main__":
    g = GanzinBanner()
    g.user_reg([("En-Ho Shen", "enhoshen@ganzin.com.tw")])
    pass

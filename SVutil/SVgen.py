import os
import inspect
from functools import wraps

from SVutil.SVparse import *
from SVutil.SVutil import SVutil

class Ind:
    def __init__(self, n):
        self.n = n
        self.base = "" if n == 0 else f'{" ":{4*n}}'
        self.b = self.base

    def __getitem__(self, n):
        return self.base if n == 0 else f'{" ":{4*(int(n)+self.n)}}'

    def __iadd__(self, n):
        self.n += n
        self.base = f'{" ":{4*self.n}}'
        return self

    def __isub__(self, n):
        self.n -= n
        self.base = "" if self.n == 0 else f'{" ":{4*self.n}}'
        return self

    def __add__(self, n):
        return Ind(self.n + n)

    def Copy(self):
        return Ind(self.n)


class SVgen(SVutil):
    def __init__(self, paths=None, session=None, verbose=None):
        self.V_(GBV.VERBOSE)
        if session is None:
            self.session = SVparseSession(verbose=self.verbose)
            self.session.FileParse(paths)
        else:
            self.session = session
        self.genlist = {}
        self.customlst = []
        self.userfunclst = []

        self.Refresh()

    def Refresh(self):
        self.hier = self.session.hiers.get(GBV.HIER)
        self.regbkstr = GBV.REGBK
        self.regbk = self.session.hiers.get(GBV.REGBK)
        self.cond = {}  # syn 2ns test name etc.
        self.cur_ind = Ind(0)

    def IndBlk(self):
        ind = self.cur_ind.Copy()
        yield ""
        while 1:
            yield ind.b + "\n"

    def Genlist(self, structure):
        """
        Generate texts based on a simple structure description list.
        
        SVgen building blocks are **generators** generating strings accessed by
        next() built-in function. Users can choose desirable block and
        combine them into a file description list:  
        `EX`: genlist([ (A,B) , A , (C,) , [1, D , E], (2, F, G), A])
        generates a file structure of such

        ```
        A
        B
        A'
        C
          D
            E
            E'
          D'
            F
            G
        A''
        ```

        * naked block structure generates a string once
        * tuple initializes and generates once of its contents
        * nested list will initialize, generates strings and expands its
        content in a hierarchical structure
        * integer will add up to the current indent level

        """

        o = ""
        _ind = self.cur_ind.Copy()
        for strt in structure:
            if isinstance(strt, int):
                self.cur_ind += strt
            elif type(strt) == list:
                for v in strt:
                    next(v)  # initialize
                    o += self.Nextblk(v)
                    self.cur_ind += 1
                strt.reverse()
                for v in strt:
                    o += self.Nextblk(v)
                    self.cur_ind -= 1
            elif type(strt) == tuple:
                prev_ind = self.cur_ind.Copy()
                for i in strt:
                    if isinstance(i, int):
                        self.cur_ind += i 
                        continue
                    self.Nextblk(i)
                    o += self.Nextblk(i)
                self.cur_ind = prev_ind
            elif type(strt) == str:
                o += strt
            else:
                o += self.Nextblk(strt)

        self.cur_ind = _ind.Copy()
        return o

    def Str2Blk(self, strcallback, *arg, **kwargs):
        ind = self.cur_ind.Copy()
        yield ""
        yield strcallback(*arg, **kwargs, ind=ind)

    def BlkGroup(self, *arg):
        ind = self.cur_ind.Copy()
        yield ""
        s = self.Genlist([tuple(arg)])
        yield s

    def GenStr(self, gen):
        s = ""
        for _s in gen:
            s += _s
        return s

    def Blkprint(self, gen):
        s = ""
        print(self.GenStr(gen))

    def Nextblk(self, blk):
        s = next(blk, None)
        return s if s != None else ""

    def FileWrite(self, fpath, text, suf, overwrite=False):
        if os.path.isfile(self.genpath + fpath + "." + suf) and not overwrite:
            self.print("file exists, make a copy, rename the file right away")
            import time

            fpath = self.genpath + fpath + "_" + time.strftime("%m%d%H") + "." + suf
        else:
            fpath = self.genpath + fpath + "." + suf
        with open(fpath, "w") as f:
            f.write(text)
        return fpath



    def FindFormatWidth(self, lst):
        """
        Find from a list of strings the largest width,
        used in format string formatting the seperation width.
        lst is a list of tuple or string, return a tuple of
        integer or a single integer of the width.
        """
        if len(lst) == 0:
            return 0
        if type(lst[0]) == str:
            w = 0
            for i in lst:
                w = max(w, len(i))
            return w
        if type(lst[0]) == tuple:
            w = [0 for i in lst[0]]
            for i in lst:
                for idx, j in enumerate(i):
                    w[idx] = max(w[idx], len(j))
            return w

    # decorators
    def str(orig):
        sig = inspect.signature(orig)

        @wraps(orig)
        def new_func(*arg, **kwargs):
            # for each kwargs, check if it's existing argument, if so, don't do post
            # processing
            post = {}

            ind = arg[0].cur_ind.Copy() if not kwargs.get('ind') else kwargs.get('ind')
            if sig.parameters.get('ind'):
                kwargs['ind'] = ind
            else:
                kwargs.pop('ind',None)
                post['ind'] = True

            if sig.parameters.get('spacing') is None:
                spacing = kwargs.pop('spacing', None)
                post['spacing'] = True

            x = orig(*arg, **kwargs)

            # post processing
            if post.get('ind'):
                x = f'{ind.b}' + x.replace('\n', f'\n{ind.b}')
            if post.get('spacing'):
                x = x+'\n'

            return x

        return new_func

    def Clip(orig):
        @wraps(orig)
        def new_func(*arg, **kwargs):
            ind = kwargs.get("ind")
            ind = (
                arg[0].cur_ind.Copy() if ind is None else ind
            )  # orig must be a member function
            toclip = kwargs.get("toclip")
            toclip = True if toclip is None else toclip
            kwargs["ind"] = ind
            x = orig(*arg, **kwargs)
            if toclip:
                ToClip(x)
            return x

        return new_func

    def Blk(orig):
        @wraps(orig)
        def new_func(*arg, **kwargs):
            ind = kwargs.get("ind")
            ind = (
                arg[0].cur_ind.Copy() if ind is None else ind
            )  # orig must be a member function
            kwargs["ind"] = ind
            yield ''
            x = orig(*arg, **kwargs)
            yield from x

        return new_func

    @Blk
    def Line3BannerBlk(self, w, cmtc, text, ind=None):
        """
        w: banner width; 
        cmtc: language specified comment character
        text: banner text
        EX:
        //============
        //   logic
        //============
        """
        s = f'{ind.b}{cmtc}{"":=^{w}}\n'
        s += f"{ind.b}{cmtc}{text:^{w}}\n"
        s += f'{ind.b}{cmtc}{"":=^{w}}\n'
        yield s

    @Blk
    def one_line_banner_blk(self, w=None, cmtc='//', text='', ind=None):
        """
        w: banner width; 
        cmtc: language specified comment character
        text: banner text
        EX: //-- logic --//
        """
        if isinstance(w, int):
            text = f' {text} '
            s = f"{ind.b}{cmtc}{text:-^{w}}{cmtc}\n"
        else:
            s = f"{ind.b}{cmtc}-- {text} --{cmtc}\n"
        yield s

def GenSession():
    pass
    # dut = hiers.Ahb2ToReqAckWrap
    # ins = g.InsGen(dut, 'u1' )
    # lg = g.LogicGen(dut)
    # tb = g.TbSVGen()
    # ind = g.IndBlk()
    # g.Genlist( [ (tb,), tb , (lg,) , [ins] , tb , tb])
    # print(o)

if __name__ == "__main__":
    pass

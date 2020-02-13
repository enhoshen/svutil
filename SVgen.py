from SVparse import * 
import os
class Ind():
    def __init__(self , n):
        self.n = n
        self.base = '' if n==0 else f'{" ":{4*n}}'
        self.b = self.base
    def __getitem__(self, n):
        return  self.base if n==0 else f'{" ":{4*(int(n)+self.n)}}' 
    def __iadd__ (self, n):
        self.n += n
        self.base = f'{" ":{4*self.n}}'
        return self
    def __isub__ (self,n):
        self.n -= n
        self.base = '' if self.n==0 else f'{" ":{4*self.n}}'
        return self 
    def __add__ (self, n):
        return Ind(self.n+n)
    def Copy(self):
        return Ind(self.n)
class SVgen(SVutil):
    def __init__(self , paths=None, session=None, verbose=None ):
        self.V_(VERBOSE)
        if session is None:
            self.session = SVparseSession(verbose=self.verbose)
            self.session.FileParse(paths)
        else:
            self.session = session
        self.genlist = {}    
        self.customlst = [  'hclkmacro',
                            'endcyclemacro',
                            'clkstr',
                            'rststr',
                            'genpath',
                            'endcycle']

        self.hclkmacro = 'HCYCLE'
        self.endcyclemacro = 'TIMEOUTCYCLE'
        self.clkstr = 'clk'
        self.rststr = 'rst'
        self.genpath = './'
        self.endcycle = 10000

        self.test = TEST
        self.testname = TEST.rsplit('_tb')[0]
        self.fsdbname = self.testname + '_tb' #TODO
        self.topfile  = SV.rstrip('.sv')
        self.incfile  = INC
        self.dutname = TESTMODULE 
        self.dut = self.session.hiers.get(self.dutname)
        self.dutfile = self.session.hiers.get(self.dutname+'_sv')
        self.hier = self.session.hiers.get(HIER) 
        self.regbkstr= REGBK 
        self.regbk = self.session.hiers.get(REGBK)
        self.cond = {} # syn 2ns test name etc.
        self.cur_ind = Ind(0)
    def IndBlk(self):
        ind = self.cur_ind.Copy() 
        yield ''
        while 1:
            yield ind.b + '\n' 
    def Genlist(self , structure):
        o = ''
        for strt in structure:
            if type(strt) == list:
                for v in strt:
                    next(v) # initialize
                    o += self.Nextblk(v)
                    self.cur_ind+=1
                strt.reverse()
                for v in strt:
                    o += self.Nextblk(v)
                    self.cur_ind-=1
            elif type(strt) == tuple:
                for i in strt:
                    self.Nextblk(i)
                    o += self.Nextblk(i)
            elif type(strt) == str:
                o += strt
            else :
                o += self.Nextblk(strt)
        return o
    def Str2Blk(self, strcallback, *arg):
        ind = self.cur_ind.Copy()
        yield ''
        yield strcallback( *arg , ind=ind)
    def BlkGroup (self, *arg):
        ind = self.cur_ind.Copy()
        yield ''
        s = self.Genlist( [ tuple(arg) ])
        yield s 
    def GenStr( self , gen):
        s = ''
        for _s in gen:
            s += _s
        return s
    def Blkprint( self , gen):
        s = ''
        print ( self.GenStr(gen) )
    def Nextblk(self, blk):
        s = next(blk,None)
        return s if s != None else ''
    def FileWrite(self , fpath, text, suf, overwrite=False): 
        if os.path.isfile(self.genpath+fpath+'.'+suf) and not overwrite:
            print( "file exists, make a copy, rename the file right away")
            import time
            fpath = self.genpath + fpath +'_'+ time.strftime('%m%d%H') +'.'+ suf 
        else:
            fpath = self.genpath + fpath + '.' + suf 
        f = open( fpath,'w')
        f.write(text)
        return fpath
    def Line3BannerBlk(self, w, cmtc, text):
        '''
            w: banner width; cmtc: language specified comment character
            text: banner text
        '''
        ind = self.cur_ind.Copy()
        yield ''
        s =f'{ind.b}{cmtc}{"":=^{w}}\n'
        s += f'{ind.b}{cmtc}{text:^{w}}\n'
        s += f'{ind.b}{cmtc}{"":=^{w}}\n'
        yield s
    def FindFormatWidth(self, lst):
        '''
            Find from a list of strings the largest width,
            used in format string formatting the seperation width.
            lst is a list of tuple or string, return a tuple of
            integer or a single integer of the width. 
        '''
        if len(lst) == 0:
            return 0
        if type(lst[0]) == str:
            w = 0
            for i in lst:
                w = max(w, len(i))
            return w
        if type(lst[0]) == tuple:
            w = [ 0 for i in lst[0] ]
            for i in lst:
                for idx, j in enumerate(i):
                    w[idx] = max(w[idx], len(j))
            return w
if __name__ == "__main__":
    pass
    #dut = hiers.Ahb2ToReqAckWrap
    #ins = g.InsGen(dut, 'u1' )  
    #lg = g.LogicGen(dut)
    #tb = g.TbSVGen()                                    
    #ind = g.IndBlk()                                     
    #g.Genlist( [ (tb,), tb , (lg,) , [ins] , tb , tb])
    #print(o)
    from SVparse import *
    import sys
    sys.path.append('./gen')
    from gen.TestGen import TestGen
    from gen.RegbkGen import RegbkGen
    from gen.DrawioGen import DrawioGen
    from gen.LatexGen import LatexGen
    from gen.BannerGen import BannerGen
    session = SVparseSession(V_(VERBOSE))
    session.FileParse(None)
    gTest = TestGen(session=session)
    gRegbk = RegbkGen(session=session)
    gDrawio = DrawioGen(session=session)
    gLatex = LatexGen(session=session)
    gBanner = BannerGen()

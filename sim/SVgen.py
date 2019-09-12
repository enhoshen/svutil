from SVparse import * 
from itertools import zip_longest
import os
TOPMODULE = os.environ.get("TOPMODULE")
TESTMODULE = os.environ.get("TESTMODULE")
TEST = os.environ.get("TEST")
SV = os.environ.get("SV")
hiers = EAdict(SVparse.hiers)
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
    def Copy(self):
        return Ind(self.n)
class SVgen():
    def __init__(self ):
        FileParse()
        self.genlist = {}    
        self.hclkmacro = 'HCYCLE'
        self.endcyclemacro = 'ENDCYCLE'
        self.test = TEST
        self.testname = TEST.rsplit('_tb')[0]
        self.fsdbname = self.testname + '_tb' #TODO
        self.topfile  = SV.rstrip('.sv')
        self.dutname = TESTMODULE 
        self.dut = hiers.dic[self.dutname]
        self.dutfile = hiers.dic[self.dutname+'_sv']
        self.genpath = './'
        self.endcycle = 10000
        self.cond = {} # syn 2ns test name etc.
        self.cur_ind = Ind(0)
    def IndBlk(self):
        ind = self.cur_ind.Copy() 
        yield ''
        while 1:
            yield ind.b + '\n' 
    def TbSVGen(self): 
        ind = self.cur_ind.Copy() 
        yield ''
        s = '\n'
        s += '`timescale 1ns/1ns\n'
        s += '`include ' + f'"../include/{SV}"\n' #TODO
        s += 'module ' + TOPMODULE + ';\n'
        s = s.replace('\n',f'\n{ind.b}')
        yield s
        s = '\n`Pos(rst_out, rst)\n' +'`PosIf(ck_ev , clk, rst)\n' + '`WithFinish\n\n' 
        s += f'always #`{self.hclkmacro} clk= ~clk;\n\n'
        s += f'initial begin'
        s = s.replace('\n',f'\n{ind[1]}')
        _s =  f'\n$fsdbDumpfile({self.fsdbname}.fsdb);\n' 
        _s +=  f'$fsdbDumpvars(0,{TEST},"+all");\n'
        _s +=  'clk = 0;\n' + 'rst = 1;\n'
        _s +=  '#1 `NicotbInit\n' 
        _s +=  '#10 rst = 0;\n' +  '#10 rst = 1;\n'
        _s +=  f'#(2*{self.hclkmacro+"*"+self.endcyclemacro}) $display("timeout");\n'
        _s +=  '`NicotbFinal();\n' +  '$finish;'
        _s = _s.replace('\n',f'\n{ind[2]}')
        _s += f'\n{ind[1]}end\n\n'
        yield s+_s
        s = '\n' + ind.b +'endmodule'
        yield s
    def DeclareBlkGen(self ):
        pass
    def TopBlkGen(self , tpname ):
        ind = self.cur_ind.Copy()
        yield ''
        yield 
    def ModBlkGen(self):
        pass
    def LogicGen(self , module , **conf):
        ind = self.cur_ind.Copy()
        yield ''
        s = ''
        for p in module.ports:
            if p[3] == 'logic':
                s += f'{ind.b}{p[3]} {p[5]} {p[1]} {p[6]};\n'
            else:
                s += f'{ind.b}{p[3]} {p[1]} {p[6]};\n' 
        yield s
    def InsGen(self , module , name='dut' ,  **conf):
        ind = self.cur_ind.Copy() 
        yield ''
        s = '\n'
        s += ind.base + module.hier + ' #(\n'
        #TODO parameter ports
        s += ind.base + '.*\n'
        s += ind.base + ') ' + name + ' (\n' 
        s += ind[1] + '.*\n'
        for io , n , *_ in module.ports:
            s += ind[1] + ',.' + n + '()\n'
        s += ind.base + ');\n' 
        yield s

    def TbPYGen(self):
        ind = self.cur_ind.Copy()
        yield ''
        s = '\n'
        s += f'{ind.b}from nicotb import *\n'
        s += f'{ind.b}import numpy as np \n'
        yield s
        s =  f'{ind.b}rst_out, clk = CreateEvents(["rst_out" , "ck_ev"])\n\n'
        s += f'{ind.b}RegisterCoroutines([\n'
        s += f'{ind[1]}main(),\n'
        s += f'{ind.b}])'
        yield s
    def NicoutilImportGen(self):
        ind = self.cur_ind.Copy()
        yield ''
        s = '\n'
        s +='from SVparse import SVparse\n'
        s +='from itertools import repeat\n'
        s +='from nicotb.primitives import JoinableFor\n'
        s +='from NicoUtil import *\n'
        s +='import os'
        s = s.replace('\n',f'\n{ind.b}') 
        yield s
    def PYbusinitGen(self,module):
        ind = self.cur_ind.Copy()
        yield ''
        s = '\n'
        s += f'{ind.b}def BusInit():\n'
        s += f'{ind[1]}SBC = StructBusCreator\n'
        s += f'{ind[1]}SBC.TopTypes()\n'
        for p in module.ports:
            tp = p[3]
            if tp == 'logic':
                s += f'{ind[1]}{p[1]} = CreateBus((\'\', \'{p[1]}\', {p[2] if p[2]!=() else "(1,)"},)\n'
            else:
                s += f'{ind[1]}{p[1]} = SBC.Get(\'{p[3]}\' , \'{p[1]}\')\n'     
        yield s
            
    def PYmainGen(self):
        ind = self.cur_ind.Copy()
        yield '' 
        s = '\n'
        s += f'{ind.b}def main():\n'
        s += f'{ind[1]}yield rst_out\n'
        s += f'{ind[1]}FinishSim()\n' 
        yield s
        


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
            elif  type(strt) == tuple:
                for i in strt:
                    next(i)
                    o += self.Nextblk(i)
            else :
                o += self.Nextblk(strt)
        return o
    def Nextblk(self, blk):
        s = next(blk,None)
        return s if s != None else ''
    def ModuleTestSV(self , module , **conf):
        ins = g.InsGen(module)
        lg = g.LogicGen(module)
        tb = g.TbSVGen()
        ind = g.IndBlk()
        return g.Genlist( [ (tb,) , tb , [ind,lg] , [ind,ins] , tb , tb]) 
    def SVWrite(self): 
        fpath = self.genpath + self.test + '.sv'
        if os.path.isfile(fpath):
            print( "file exists, make a copy")
            f = open( self.genpath + self.test + '_new.sv','w')
            f.write(self.ModuleTest(self.dut))
            return
        else:
            f = open( fpath, 'w')
            f.write(self.ModuleTest(self.dut))
            print( f"Module test .sv written to {fpath}")
        return
    def ModuleTestPY(self , module , **conf):
        tb = g.TbPYGen()
        nicoutil = g.NicoutilImportGen() 
        businit = g.PYbusinitGen(module)
        main = g.PYmainGen()
        return g.Genlist( [(tb,nicoutil,businit,main), tb ] )

def FileParse(inc=True):
    if SVparse.parsed == True:
        return
    p = SV if inc == True else [SV]
    SVparse.ParseFiles(p,inc)
def Reset():
    FileParse()
if __name__ == "__main__":
    g=SVgen()
    #dut = hiers.Ahb2ToReqAckWrap
    #ins = g.InsGen(dut, 'u1' )  
    #lg = g.LogicGen(dut)
    #tb = g.TbSVGen()                                    
    #ind = g.IndBlk()                                     
    #g.Genlist( [ (tb,), tb , (lg,) , [ins] , tb , tb])
    #print(o)

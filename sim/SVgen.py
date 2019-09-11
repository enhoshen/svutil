from SVparse import * 
from itertools import zip_longest
import os
TOPMODULE = os.environ.get("TOPMODULE")
TEST = os.environ.get("TEST")
SV = os.environ.get("SV")
DUT = SV.rstrip('.sv')
TESTNAME = TEST.rsplit('_tb')[0]
hiers = EAdict(SVparse.hiers)
class SVgen():
    genlist = {}    
    hclkmacro = 'HCYCLE'
    endcyclemacro = 'ENDCYCLE'
    endcycle = 10000
    cond = {} # syn 2ns test name etc.
    def __init__(self ):
        pass
    def TbBlkGen(self ): 
        s = '\n'
        s += '`timescale 1ns/1ns\n'
        s += '`include ' + f'"{SV}"\n' #TODO
        s += 'module ' + TOPMODULE + '\n\n'
        
        yield s
        s = '`Pos(rst_out, rst)\n' +'`PosIf(ck_ev , clk, rst)\n' + '`WithFinish\n\n' 
        s += f'always #`{self.hclkmacro} clk= ~clk;\n'
        s += f'initial begin\n'
        ind = Ind(1)
        s += ind.b + f'$fsdbDumpfile({TESTNAME}.fsdb);\n' 
        s += ind.b + f'$fsdbDumpvars(0,{TEST},"+all");\n'
        s += ind.b + 'clk = 0;\n' + ind.b + 'rst = 1;\n'
        s += ind.b + '#1 `NicotbInit\n' 
        s += ind.b + '#10 rst = 0;\n' + ind.b + '#10 rst = 1;\n'
        s += ind.b + f'#(2*{self.hclkmacro+"*"+self.endcyclemacro}) $display("timeout");\n'
        s += ind.b + '`NicotbFinal();\n' + ind.b + '$finish;\n'
        s += 'end\n'
        yield s
        s = 'endmodule'
        yield s
    def DeclareBlkGen(self):
        pass
    def TopBlkGen(self , tpname ):
        yield 
        yield 
    def ModBlkGen(self):
        pass
    def InstanceGen(self , module , name , indent , **conf):
        ind = Ind(indent)
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
            
    def Output(self , genlist):
        o = ''
        for i in zip_longest(*genlist):
            for s in i:
                o += s
        print(o)
                    
    @classmethod
    def TopModule(cls,inc=True):
        FileParse(inc)

        
class Ind():
    def __init__(self , n):
        self.n = n
        self.base = f'{" ":{4*n}}'
        self.b = self.base
    def __getitem__(self, n):
        return  f'{" ":{4*(int(n)+self.n)}}'

def FileParse(inc=True):
    if SVparse.parsed == True:
        return
    p = SV if inc == True else [SV]
    SVparse.ParseFiles(p,inc)
def Reset():
    FileParse()

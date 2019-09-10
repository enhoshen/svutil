from SVparse import * 
import os
TOPMODULE = os.environ.get("TOPMODULE")
TOP = os.environ.get("TOP")
TEST = os.environ.get("TEST")
SV = os.environ.get("SV")
hiers = EAdict(SVparse.hiers)
class SVgen():
    genlist = {}    
    def __init__(self ):
        FileParse()
    def TbGen(self , mod , path): 
        pass
    def TopGen(self):
        pass
    def ModGen(self):
        pass
    def InstanceGen(self , module , name , indent):
        ind = Ind(indent)
        s = ''
        s += ind.base + module.hier + ' #(\n'
        #TODO parameter ports
        s += ind.base + '.*\n'
        s += ind.base + ') ' + name + ' (\n' 
        s += ind[1] + '.*\n'
        for io , n , *_ in module.ports:
            s += ind[1] + ',.' + n + '()\n'
        s += ind.base + ');\n' 
        return s
            

    @classmethod
    def TopModule(cls,inc=True):
        FileParse(inc)

        
class Ind():
    def __init__(self , n):
        self.n = n
        self.base = f'{" ":{4*n}}'
    def __getitem__(self, n):
        return  f'{" ":{4*(int(n)+self.n)}}'

def FileParse(inc=True):
    if SVparse.parsed == True:
        return
    p = SV if inc == True else [SV]
    SVparse.ParseFiles(p,inc)

from SVparse import * 
class SVclass():
    def __init__(self):
        self.w = 20
        pass
    def __getattr__(self, n):
        return self.data[self.field.dic[n]]
    @property
    def ShowData(self):
        for f in self.field.dic:
            print(f'{self.data[self.field.dic[f]].__repr__():<{self.w}}', end='')
        print()
    @property
    def ShowLine(self, char='='):
        print(f'{"":{char}<{len(self.field.dic)*self.w}}')
    @property
    def ShowField(self):
        for f in self.field.dic: 
            print(f'{f:<{self.w}}', end='')
        print() 
class SVParam(SVclass):
    field = SVhier.paramfield
    def __init__(self, param=None):
        self.w = 20
        self.data = param
class SVPort(SVclass):
    field = SVhier.portfield
    def __init__(self, port=None):
        self.w = 20
        self.data = port
class SVEnums(SVclass):
    field = SVhier.enumsfield
    def __init__(self, enums=None):
        self.w = 30
        self.data = enums
        self.enumls = [ SVEnuml((name, num, cmt)) for name, num, cmt in zip( self.names, self.nums, self.cmts) ]
class SVEnuml(SVclass):
    field = SVhier.enumlfield
    def __init__(self, enuml=None):
        self.w = 20
        self.data = enuml
class SVRegbk(): 
    def __init__(self, pkg):
        self.w = 20
        self.pkg = pkg
        self.addrs = SVEnums ( pkg.enums['regaddr'] )
        #self.regfields = pkg. TODO reg fields, defaults etc...
    def ShowAddr(self):
        print ( f'{self.pkg.name:-^{3*self.w}}') #TODO name banner width
        SVEnuml().ShowField
        SVEnuml().ShowLine
        for i in self.addrs.enumls:
            i.ShowData

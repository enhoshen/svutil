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
    def ShowDataCb(self, cblst):
        for f, cb in zip(self.field.dic, cblst):
            s = cb(self.data[self.field.dic[f]]) if cb else self.data[self.field.dic[f]]
            s = s.__repr__() if type(s) != str else s
            print(f'{s:<{self.w}}', end='')
        print()
class SVParam(SVclass):
    field = SVhier.paramfield
    def __init__(self, param=None):
        self.w = 20
        self.data = param
class SVType(SVclass):
    field = SVhier.typefield
    def __init__(self, tp = None):
        self.w = 15
        self.data = tp
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
    regfield_suf = '_regfield'
    default_suf  = '_DEFAULT'
    bw_suf  = '_BW'
    reserved_name = 'RESERVED'
    regaddr_name = 'regaddr'
    regbw_name = 'REG_BW'
    regaddrbw_name = 'REG_ADDR_BW'
    regbsize_name = 'REG_BSIZE'
    regbsizebw_name = 'REG_BSIZE_BW'
    def __init__(self, pkg):
        self.w = 20
        self.pkg = pkg
        self.addrs = SVEnums ( pkg.enums[self.regaddr_name] )
        self.addrsdict = { x.name: x for x in self.addrs.enumls }
        self.regbw = pkg.params[self.regbw_name]
        self.regaddrbw = pkg.params[self.regaddrbw_name]
        self.regbsize = pkg.params[self.regbsize_name]
        self.regbsizebw = pkg.params[self.regbsizebw_name]
        self.regtypes = {}
        self.regmembtypes = {}
        self.regfields = {} 
        self.regslices = {}
        self.defaultstr = {} 
        self.bwstr = {}
        self.params = {} 
        for i,v in pkg.paramsdetail.items():
            _v = SVParam(v)
            self.params[i]=(_v)
            _s = i.split(self.default_suf)
            if len(_s) == 2:
                self.defaultstr[_s[0]] = _v.numstr
            _s = i.split(self.bw_suf)
            if len(_s) == 2:
                self.bwstr[_s[0]] = _v.numstr
        for i,v in pkg.enums.items():
            _v = SVEnums(v)
            _s = i.split(self.regfield_suf)
            if len(_s) == 2:
                self.regfields[_s[0]] = _v
                pre_slice = 0
                self.regslices[_s[0]] = []
                _regslices =[ (name, [(start, end-1)] ) for name, start, end in zip(_v.names, _v.nums, _v.nums[1:]+[self.regbw])] 
                reserved = []
                for ii in _regslices:
                    if self.reserved_name in ii[0]:
                        reserved.append( ii[1][0] ) 
                    else:
                        self.regslices[_s[0]].append(ii)
                if len(reserved)!=0:
                    self.regslices[_s[0]].insert(0, (self.reserved_name , reserved))
        for i,v in pkg.types.items():
            _v = [ SVType(vv) for vv in v]
            tt = [ self.GetType(vv.tp) for vv in _v ]
            self.regtypes[i.upper()] = _v
            self.regmembtypes[i.upper()] = tt
        #self.regfields = pkg. TODO reg fields, defaults etc...
    def GetDefaultsStr(self, name):
        _s = self.defaultstr.get(name)
        if not _s:
            return None
        _s = _s.replace('_', '\_')
        lst = SVstr(_s).ReplaceSplit([',','{','}'])
        return lst
    def GetType(self, tp):
        tp = self.pkg.AllType.get(tp)
        return [ SVType(t) for t in tp] if tp else None
    def GetAddrCmt(self, reg):
        cmt = self.addrsdict[reg].cmt 
        width = ''
        rw = ''
        if len(cmt) == 2:
            width= cmt[0].lstrip().rstrip()
            rw = cmt[1].lstrip().rstrip()
        return width, rw
            
    def ShowAddr(self, valuecb=hex):
        print ( f'{self.pkg.name:-^{3*self.w}}') #TODO name banner width
        SVEnuml().ShowField
        SVEnuml().ShowLine
        for i in self.addrs.enumls:
            i.ShowDataCb([None, hex, None])
    def ShowRegfield(self, name):
        pass

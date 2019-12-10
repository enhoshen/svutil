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
            try:
                print(f'{self.data[self.field.dic[f]].__repr__():<{self.w}}', end='')
            except:
                print(f'{"":<{self.w}}', end='')
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
    '''
    Register bank information parsed from a *Regbk package
        regfields: SVEnums
    '''
    regfield_suf = '_regfield'
    default_suf  = '_DEFAULT'
    bw_suf  = '_BW'
    reserved_name = 'RESERVED'
    regaddr_name = 'regaddr'
    regbw_name = 'REG_BW'
    regaddrbw_name = 'REG_ADDR_BW'
    regbsize_name = 'REG_BSIZE'
    regbsizebw_name = 'REG_BSIZE_BW'
    regintr_name = 'raw_intr_stat'
    def __init__(self, pkg):
        self.w = 20
        self.pkg = pkg
        self.addrs = SVEnums ( pkg.enums[self.regaddr_name] )
        self.addrsdict = { x.name: x for x in self.addrs.enumls }
        self.regaddrs = self.addrs
        self.regaddrsdict = self.addrsdict
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
        self.raw_intr_stat = self.GetType('raw_intr_stat')
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
            
    def GetAddrNField(self, reg):
        '''
            Return the address and regfield given the register name
            the address is multiplied by regaddrbw
        '''
        addr = self.regaddrsdict[reg].num * self.regbsize
        regfield = self.regfields.get(reg)
        nums = regfield.nums if regfield else [0]
        names = regfield.names if regfield else None
        return addr, nums, names 
    def RegWrite(self, reg, datalst):
        '''
            Return the address ,packed data and register fields names given register name
            and list of data of each register fields.
        '''
        addr, regnums, regnames = self.GetAddrNField(reg)
        data = self.RegfieldPack(regnums, datalst)
        return addr, data, regnames
    def RegRead(self, reg, data):
        '''
            Return the address ,extracted data fields and register fields names given register name
            and read data.
        '''
        addr, regnums, regnames = self.GetAddrNField(reg)
        datalst = self.RegfieldPack(regnums, data)
        return datalst, regnames 
    def ShowAddr(self, valuecb=hex):
        print ( f'{self.pkg.name:-^{3*self.w}}') #TODO name banner width
        SVEnuml().ShowField
        SVEnuml().ShowLine
        for i in self.addrs.enumls:
            i.ShowDataCb([None, hex, None])
    def ShowRegfield(self, name):
        pass
    def RegfieldPack (self, regfieldlst, datalst):
        '''
            The function packs the provided data list
            based on each fields to a data of bandwidth self.regbw.
            regfieldlst consists of a list
            Ex: [0,6,31]; the first data will be packed to data[5:0], then data[30:6] and data[31]
            this list corresponds to self.regfield['reg name'].nums
        '''
        print(regfieldlst)
        data = 0
        try:
            iterator = iter(datalst)
        except TypeError:
            datalst = [datalst]
        else:
            pass
        for f, d in zip( regfieldlst, datalst):
            msk = (1 << f) -1
            data = (data & msk) + (d << f )
        msk = ( 1 << self.regbw) -1 
        data = data & msk
        return data
    def RegfieldExtract(self, regfieldlst, data):
        '''
            Given the regfield list and a data, extract each fields' bit slice
            Co-test with RegfieldPack by:
                datalst == g.regbk.RegfieldExtract( regfieldlst, g.regbk.RegfieldPack( regfieldlst, datalst))
                Ex:g.regbk.RegfieldExtract( [0,5,17,30,31], g.regbk.RegfieldPack( [0, 5, 17, 30, 31], [31, 1033, 2033, 0, 1]))
        '''
        datalst = []
        for s, e in zip(regfieldlst, regfieldlst[1:]+[self.regbw]):
            print( s, e, e-s)
            msk = ((1 << s) -1) ^ ((1 << e) -1) if s!=e else (1 << s)
            print ( bin(msk))
            datalst.append((data & msk) >> s)
        return datalst[0] if len(datalst)==1 else datalst

from SVparse import * 
from SVutil import *
class SVclass(SVutil):
    def __init__(self):
        self.w = 20
        self.V_(VERBOSE) 
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
    def ShowLine(self):
        print(f'{"":{self.linechar}<{len(self.field.dic)*self.w}}')
    @property
    def ShowField(self):
        for f in self.field.dic: 
            print(f'{f:<{self.w}}', end='')
        print() 
    @property
    def Show(self):
        self.ShowField
        self.ShowLine
        self.ShowData 
    def ShowDataCb(self, cblst):
        ''' 
            cblst:callback list; applied to each field
            Ex: ShowDataCb([hex,bin]) would print hex(field0), bin(field1)
        '''
        for f, cb in zip(self.field.dic, cblst):
            s = cb(self.data[self.field.dic[f]]) if cb else self.data[self.field.dic[f]]
            s = s.__repr__() if type(s) != str else s
            print(f'{s:<{self.w}}', end='')
        print()
class SVParam(SVclass):
    field = SVhier.paramfield
    def __init__(self, param=None):
        self.w = 20
        self.linechar = '='
        self.data = param
class SVStruct(SVclass):
    field = SVhier.typefield
    def __init__(self, tp = None):
        self.w = 15
        self.linechar = '='
        self.datas = [ SVType(t) for t in tp] 
    @property
    def ShowData(self):
        for d in self.datas:
            d.ShowData
        
class SVType(SVclass):
    field = SVhier.typefield
    def __init__(self, tp = None):
        self.w = 15
        self.linechar = '='
        self.data = tp
    def __repr__(self):
        type_ = type(self)
        module = type_.__module__
        qualname = type_.__qualname__
        return f"<{module}.{qualname} {self.name} at {hex(id(self))}>"
        
class SVPort(SVclass):
    field = SVhier.portfield
    def __init__(self, port=None):
        self.w = 20
        self.linechar = '='
        self.data = port
class SVEnums(SVclass):
    field = SVhier.enumsfield
    def __init__(self, enums=None):
        self.w = 30
        self.linechar = '='
        self.data = enums
        #self.enumls = [ SVEnuml((name, num, cmt, idx, size, name_base)) \
        #                for name, num, cmt, idx, size, name_base in \
        #                zip( self.names, self.nums, self.cmts, self.idxs, self.sizes, self.name_bases) ]
        self.enumls = [ SVEnuml(d) for d in zip(*self.data)]
    def __str__(self):
        slst = [ str(i)+':'+x.__str__() for i,x in enumerate(self.enumls)]
        return '[ '+' , '.join(slst)+' ]'
class SVEnuml(SVclass):
    ''' enum literal '''
    field = SVhier.enumlfield
    def __init__(self, enuml=None):
        self.w = 20
        self.linechar = '='
        self.data = enuml
    def __repr__(self):
        type_ = type(self)
        module = type_.__module__
        qualname = type_.__qualname__
        return f"<{module}.{qualname} {self.name} at {hex(id(self))}>"
    def __str__(self):
        return f"<SVEnuml: {self.name}>"
class SVRegbk(SVutil): 
    '''
    Register bank information parsed from a *Regbk package
        regfields: SVEnums
    '''
    regfield_suf = '_regfield'
    default_suf  = '_DEFAULT'
    bw_suf  = '_BW'
    arr_num_suf = '_NUM'
    reserved_name = 'RESERVED'
    regaddr_name = 'regaddr'
    regaddr_arr_name = 'regaddr_arr'
    regbw_name = 'REG_BW'
    regaddrbw_name = 'REG_ADDR_BW'
    regbsize_name = 'REG_BSIZE'
    regbsizebw_name = 'REG_BSIZE_BW'
    regintr_name = 'raw_intr_stat'
    def __init__(self, pkg):
        self.verbose = V_(VERBOSE) 
        self.w = 20
        self.pkg = pkg
        self.addrs = pkg.enums.get(self.regaddr_name) 
        self.addrs = SVEnums(self.addrs) if self.addrs else None
        self.addrsdict = { x.name: x for x in self.addrs.enumls }
        self.regaddrs = self.addrs
        self.regaddrsdict = self.addrsdict
        self.regaddrsreversedict = {v:k for k,v in self.addrsdict.items()}
        self.regaddrs_arr = pkg.enums.get(self.regaddr_arr_name)
        self.regaddrs_arr = SVEnums(self.regaddrs_arr) if self.regaddrs_arr else None
        self.regaddrs_arrdict = { x.name: x for x in self.regaddrs_arr.enumls } if self.regaddrs_arr else None
        self.regbw =      pkg.params.get(self.regbw_name)
        self.regaddrbw =  pkg.params.get(self.regaddrbw_name)
        self.regbsize =   pkg.params.get(self.regbsize_name)
        self.regbsizebw = pkg.params.get(self.regbsizebw_name)
        self.regtypes = {}
        self.regmembtypes = {}
        self.regfields = {} 
        self.regslices = {}
        self.regdefaults = {}
        self.regbws = {}
        self.params = {} 
        self.raw_intr_stat = self.GetType('raw_intr_stat')
        for i,v in pkg.paramsdetail.items():
            _v = SVParam(v)
            self.params[i]=(_v)
            _s = i.split(self.default_suf)
            if len(_s) == 2:
                self.regdefaults[_s[0]] = _v
            _s = i.split(self.bw_suf)
            if len(_s) == 2:
                self.regbws[_s[0]] = _v
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
            while True:
                _v = v[0]
                if len(v)==1 and pkg.types.get(SVType(_v).tp):
                    v = pkg.types.get(SVType(_v).tp)
                else:
                    break
            _v = [ SVType(vv) for vv in v]
            tt = [ self.GetType(vv.tp) for vv in _v ]
            self.regtypes[i.upper()] = _v
            self.regmembtypes[i.upper()] = tt
        #self.regfields = pkg. TODO reg fields, defaults etc...
    def GetDefaultsStr(self, name, lst=False):
        reg = self.regaddrsdict.get(name)
        d  = self.regdefaults.get(name)
        if not d:
            d = self.regdefaults.get(reg.name_base)
        if not d:
            return None
        if lst:
            _s = d.numstrlst
        else:
            _s = d.numstr
        return _s 
    def GetBWStr(self, name, lst=False):
        reg = self.regaddrsdict.get(name)
        bw = self.regbws.get(name)
        if not bw:
            bw = self.regbws.get(reg.name_base) 
        if not bw:
            return None 
        if lst:
            _s = bw.numstrlst
        else:
            _s = bw.numstr
        return _s 
    def GetType(self, tp):
        tp = self.pkg.AllType.get(tp)
        return [ SVType(t) for t in tp] if tp else None
    def GetAddrCmt(self, reg):
        cmt = self.addrsdict[reg].cmt 
        width = ''
        rw = ''
        arr= ''
        for c in cmt:
            if re.search(r'RW|R/W|RO|WO',c):
                rw= c.lstrip().rstrip()
                continue
            if re.search(r"\d",c):
                width = c.lstrip().rstrip()
                continue
            if re.search(r"arr|ARR", c):
                arr = c.lstrip().rstrip()
                continue
        return width, rw, arr
            
    def GetAddrNField(self, reg):
        '''
            Return the address and regfield given the register name
            the address is multiplied by regaddrbw
        '''
        #TODO  multi-dimensional register
        if type(reg)=int:
            addr = reg
        else:
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
        datalst = self.RegfieldExtract(regnums, data)
        return datalst, regnames 
    def ShowAddr(self, valuecb=hex):
        print ( f'{self.pkg.name:-^{3*self.w}}')
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
            self.print( s, e, e-s, verbose=3)
            msk = ((1 << s) -1) ^ ((1 << e) -1) if s!=e else (1 << s)
            self.print ( bin(msk), verbose=3)
            datalst.append((data & msk) >> s)
        return datalst[0] if len(datalst)==1 else datalst

import numpy as np
import parser as ps
import re
import os
from collections import namedtuple
from collections import deque
from subprocess import Popen, PIPE
from functools import reduce
from SVutil import SVutil, V_
from SVstr import *
class GBV(SVutil):
    #Nico makefile specified
    ARGS = os.environ.get('ARGS','')
    TOPMODULE = os.environ.get('TOPMODULE','')
    TEST = os.environ.get('TEST','')
    #SVutil optional specified
    SVutilenv = os.environ.get('SVutil','')
    TESTMODULE = os.environ.get('TESTMODULE','')
    SV = os.environ.get('SV','')
    TOPSV = os.environ.get('TOPSV','')
    INC = os.environ.get('INC','')
    HIER= os.environ.get('HIER','')
    REGBK= os.environ.get('REGBK','')
    PROJECT_PATH = os.environ.get('PROJECT_PATH','')
    VERBOSE = os.environ.get('VERBOSE',0)
def ToClip(s):
    clip = os.environ.get('XCLIP')
    clip = 'xclip' if not clip else clip 
    try:
        p = Popen([clip ,'-selection' , 'clipboard'], stdin=PIPE)
        p.communicate(input=s.encode())
    except:
        print( "xclip not found or whatever, copy it yourself")
        print( "try install xclip and export XCLIP variable for the executable path")
class EAdict():  #easy access
    def __init__(self, items ):
        if type(items) == dict:
            self.dic = items 
        elif type(items) == list:
            self.dic = { v:i for i,v in enumerate(items) }
        else:
            print("un-supported type for EAdict")
            raise TypeError
    def __getattr__(self, n):
        return self.dic[n]
class SVhier ():
    paramfield = EAdict([ 'name' , 'dim' , 'tp', 'bw' , 'num' , 'bwstr' , 'dimstr', 'numstr' , 'paramtype', 'numstrlst'] )
    typefield  = EAdict([ 'name' , 'bw' , 'dim' , 'tp' , 'enumliteral', 'cmts' ] )
    portfield =  EAdict( [ 'direction' , 'name' , 'dim' , 'tp' , 'bw' , 'bwstr', 'dimstr', 'dimstrtuple', 'cmts', 'group' ] )
    enumfield  = EAdict( [ 'name', 'bw', 'dim', 'tp', 'enumliterals', 'cmts'] )
    enumsfield = EAdict( [ 'names' , 'nums' , 'cmts', 'idxs', 'sizes', 'name_bases', 'groups'] )
    enumlfield = EAdict( [ 'name' , 'num' , 'cmt', 'idx', 'size', 'name_base', 'group'  ] )
    macrofield = EAdict( [ 'args', 'macrostr', 'lambda'] )
    def __init__(self,name,scope):
        self.hier= name # this is fucking ambiguous, but str method use it so it remains 
        self.name = name
        self.params = {}
        self.paramsdetail = {}
        self.types = {}
        self.macros = {}
        self.child = {}
        self.paramports = {} 
        self.ports = []
        self.protoPorts = []
        self.enums = {}
        self.imported = {} 
        self.regs = {}
        self._scope = scope
        self.valuecb = int
        if scope != None:
            scope.child[name] = self
    @property
    def scope(self):
        return self._scope
    @scope.setter
    def scope(self,scope):
        self._scope=scope
    @property
    def Params(self):
        if self._scope == None:
            return deque([h.params for _ , h in self.child.items()]) 
        else:
            _l = self._scope.Params
            _l.appendleft(self.params)
            return _l
    @property
    def ParamsDetail(self):
        if self._scope == None:
            return deque([h.paramsdetail for _ , h in self.child.items()]) 
        else:
            _l = self._scope.ParamsDetail
            _l.appendleft(self.paramsdetail)
            return _l
    @property
    def Types(self):
        if self._scope == None:
            _l = deque([h.types for _ , h in self.child.items()] )
            return _l 
        else:
            _l = self._scope.Types
            _l.appendleft(self.types)
            return _l
    @property
    def Macros(self):
        if self._scope == None:
            _l = deque([self.macros])+deque([h.macros for _ , h in self.child.items()] )
            return _l 
        else:
            _l = self._scope.Macros
            _l.appendleft(self.macros)
            return _l
    @property
    def Portsdic(self):
        idx = self.portfield.name
        return { x[idx]:x for x in self.ports }
    ########################
    # types
    ########################
    @property
    def SelfTypeKeys(self):
        return { x for x in self.types.keys()} 
    @property
    def AllTypeKeys(self):
        return { x for i in self.Types for x in i.keys() }  
    @property
    def AllType(self):
        return { k:v for i in self.Types for k,v in i.items() }
    @property
    def ShowTypes(self):
        for k,v in self.types.items():
            self.TypeStr(k,v)
    @property
    def ShowAllTypes(self):
        for k,v in self.AllType.items():
            self.TypeStr(k,v)
    #########################
    # parameters
    #########################
    @property
    def AllParamKeys(self):
        return { x for i in self.Params for x in i.keys() }  
    @property
    def AllParams(self):
        return { k:v for i in self.Params for k,v in i.items() }
    @property
    def AllParamDetails(self):
        return { k:v for i in self.ParamsDetail for k,v in i.items() }
    @property
    def ShowParams(self):
        w= 30
        print(f'{self.hier+" Parameters":-^{2*w}}' )
        self.ParamStr(self.params, w)
        return
    @property
    def ShowAllParams(self):
        w =30 
        print(f'{self.hier+" All Parameters":-^{2*w}}')
        self.ParamStr(self.AllParams, w)
        return None
    @property
    def ShowParamsDetail(self):
        w = 20 
        print(f'{self.hier+" All Parameters detail":-^{2*w}}')
        self.FieldStr(self.paramfield,w)
        self.DictStr(self.paramsdetail,w)
        return None
    @property
    def ShowAllParamDetails(self):
        w = 20 
        print(f'{self.hier+" All Parameters detail":-^{2*w}}')
        self.FieldStr(self.paramfield,w)
        self.DictStr(self.AllParamDetails,w)
        return None
    #########################
    # macros 
    #########################
    @property
    def AllMacro(self):
        return { k:v for i in self.Macros for k,v in i.items() }
    ##########################
    @property
    def ShowPorts(self):
        w=15
        for i in ['io' , 'name' , 'dim' , 'type']:
            print(f'{i:{w}}' , end=' ')
        print(f'\n{"":=<{4*w}}')
        for io , n in self.protoPorts:
            print(f'{io:<{w}}'f'{n:<{w}}'f'{"()":<{w}}')
        for io , n ,dim,tp , *_ in self.ports:
            print(f'{io:<{w}}'f'{n:<{w}}'f'{dim.__str__():<{w}}'f'{tp:<{w}}')
        return
    @property
    def ShowConnect(self,**conf):
        s = '.*\n' if conf.get('explicit')==True else ''
        for t , n in self.protoPorts:
            if t == 'rdyack':
                s += ',`rdyack_connect('+n+',)\n'
            if t == 'dval':
                s += ',`dval_connect('+n+',)\n'
        for io , n , *_ in self.ports:
            s += ',.'+n+'()\n'
        s = s[:-1].replace(',',' ',1)
        ToClip(s)
        print(s)
        return
    
    def TypeStr(self,n,l,w=13):
        print(f'{self.hier+"."+n:-^{4*w}}' )
        for i in ['name','BW','dimension' , 'type']:
            print(f'{i:^{w}}', end=' ')
        print( f' \n{"":=<{4*w}}')
        for i in l:
            for idx,x in enumerate(i):
                if idx < 4:
                    print (f'{x.__str__():^{w}}' , end=' ')
                else:
                    print(f'\n{x.__str__():^{4*w}}',end=' ')
            print()
    def ParamStr(self,dic,w=13):
        for i in ['name','value']:
            print(f'{i:^{w}}' , end=' ')
        print(f'\n{"":=<{2*w}}')
        #l = self.params
        for k,v in dic.items():
            print (f'{k:^{w}}'f'{self.valuecb(v).__str__() if type(v)==int else v.__str__():^{w}}', end=' ')
            print()
    def FieldStr(self,field,w=13):
        for i in field.dic:
            print ( f'{i:^{w}}', end=' ')
        print(f'\n{"":=<{len(field.dic)*w}}')
    def DictStr(self, dic, w=13):
        for t in dic.values():
            for v in t:
                print (f'{self.valuecb(v).__repr__() if type(v)==int else v.__repr__():^{w}}', end=' ')
            print()
    def __str__(self):
        sc = self._scope.hier if self._scope!=None else None
        return f'\n{self.hier:-^52}\n'+\
                f'{"params":^15}:{[x for x in self.params] !r:^}\n'+\
                f'{"scope":^15}:{sc !r:^}\n'+\
                f'{"types":^15}:{[x for x in self.types] !r:^}\n'+\
                f'{"child":^15}:{[x for x in self.child] !r:^}\n'+\
                f'{"ports":^15}:{[io[0]+" "+n for io,n,*_ in self.ports] !r:^}\n'
        
class SVparse(SVutil):
    # One SVparse object one file, and it's also SVhier
    verbose = V_(VERBOSE) 
    parsed = False
    package = {}
    hiers = {}
    paths = []
    gb_hier = SVhier('files',None)
    gb_hier.types =  {'integer':None,'int':None,'logic':None}
    _top =  GBV.TOPMODULE
    top = _top if _top != None else ''
    if GBV.PROJECT_PATH:
        base_path = os.environ.get("PWD")+'/'+GBV.PROJECT_PATH
    else:
        match = re.search( r'/sim\b|/include\b|/src\b', os.environ.get("PWD"))
        if match:
            base_path = os.environ.get("PWD")[0:match.span()[0]] + '/'
        else:
            base_path = os.environ.get("PWD")
    include_path = base_path + 'include/'
    sim_path = base_path+'sim/'
    src_path = base_path+'src/'
    cur_scope = '' 
    cur_path= ''
    flags = { 'pport': False , 'module' : False } #TODO
    path_level = 0
    def __getattr__(self , n ):
        return hiers[n]
    def __init__(self,name=None,scope=None,parse=None):
        self.parse = parse
        if name:
            if scope != None: 
                self.cur_hier = SVhier(name,scope) 
                self.gb_hier.child[name] = self.cur_hier
            else: 
                SVhier(name,self.gb_hier) 
            SVparse.hiers[name]= self.cur_hier
        self.cur_key = ''
        self.keyword = { 'logic':self.LogicParse , 'parameter':self.ParamParse, 'localparam':self.ParamParse,\
                        'typedef':self.TypedefParse , 'struct':self.StructParse  , 'package':self.HierParse , 'enum': self.EnumParse,\
                        'module':self.HierParse , 'import':self.ImportParse, 'input':self.PortParse , 'output':self.PortParse,\
                        '`include':self.IncludeRead ,'`rdyack_input':self.RdyackParse, '`rdyack_output':self.RdyackParse,\
                        'always_ff@': self.RegisterParse, 'always_ff': self.RegisterParse, '`define':self.DefineParse,\
                        '`ifndef':self.IfNDefParse, '`ifdef':self.IfDefParse, '`endif':self.EndifParse,\
                        '`elsif':self.ElsifParse, '`else':self.ElseParse}
        self.parselist = {'typedef','package','import','module','`include', '`define',\
                        '`ifdef', '`ifndef', '`endif', '`elsif', '`else'}
        self.alwaysparselist = {'`endif', '`elsif', '`else'}
        for k in self.cur_hier.AllMacro.keys():
            self.keyword['`'+k] = self.MacroParse
        self.cnt_ifdef = -1
        self.cnt_ifndef = -1
        self.cur_macrodef = None
        self.flag_elsif_parsed = False
        self.flag_parse = True
        self.cur_cmt = ''
        self.cur_s = SVstr('')
        self.last_pure_cmt = ''
        self.last_end = False 
    @classmethod
    def ARGSParse(cls):
        s = SVARGstr(GBV.ARGS)
        l = s.PlusSplit()
        for _l in l:
            func = _l[0]
            args = _l[1:]
            SVutil(cls.verbose).print(func, args, verbose='ARGSParse')
            if func == 'define':
                m = s.define(args) 
                for k,v in m.items():
                    cls.gb_hier.macros[k]=v
                    SVutil(cls.verbose).print(k,v[2](), verbose='ARGSParse')
        pass
    @classmethod
    def ParseFiles(cls , paths=[(True,GBV.INC)] ):
        SVutil().print ('project path:', GBV.PROJECT_PATH,', include path:', GBV.INC, trace=0)
        SVutil().print("assumed base path of the project:", cls.base_path, trace=0)
        cls.ARGSParse()
        for p in paths:
            if not p[1] == '':
                cls.paths.append(f'{cls.include_path}{p[1]}.sv' if p[0] else p[1] )
        SVutil().print('parsing list:',cls.paths, trace=0)
        for p in cls.paths:
            n = (p.rsplit('/',maxsplit=1)[1] if '/' in p else p ).replace('.','_')
            cur_parse = SVparse( n , cls.gb_hier)
            cur_parse.Readfile(p if '/' in p else f'./{p}')
        cls.parsed = True
    @classmethod 
    def IncludeFileParse(cls , path):
        f = open(cls.include_path+path ,'r')
        paths = []
        for line in f.readlines():
            line = line.split('//')[0]
            if '`include' in line:
                line = line.split('`include')[1].split()[0].replace('"','')
                paths.append( cls.include_path+line)
        return paths
    #TODO Testbench sv file parse
    def Readfile(self , path):
        path = os.path.normpath(path)
        self.print(f'{"":>{SVparse.path_level*4}}{path}', trace=2, verbose=1)
        self.f = open(path , 'r')
        self.cur_path = path
        self.lines = iter(self.f.readlines())
        self.cur_s , self.cur_cmt = self.Rdline(self.lines)
        while(1):
            self.print(self.cur_s,verbose=5)
            _w = ''
            if self.cur_s == None:
                return
            if self.cur_s.End():
                _cmt = self.cur_cmt
                self.cur_s, self.cur_cmt=self.Rdline(self.lines)
                self.cur_cmt = _cmt + self.cur_cmt if self.cur_s == '' else self.cur_cmt
                continue 
            _w = self.cur_s.lsplit()
            _catch = None
            if _w in self.parselist:
                self.cur_key = _w
                if self.flag_parse or _w in self.alwaysparselist:
                    _catch = self.keyword[_w](self.cur_s,self.lines) 
    def IncludeRead( self, s , lines):
        SVparse.path_level += 1
        parent_path = self.cur_path
        _s = s.s.replace('"','')
        p = [ self.include_path+_s , self.src_path+_s , self.sim_path+_s ]
        for pp in p:
            if ( os.path.isfile(pp) ):
                #path = self.cur_path.rsplit('/',maxsplit=1)[0] + '/' + _s
                path = pp
                n = path.rsplit('/',maxsplit=1)[1].replace('.','_')
                cur_parse = SVparse( n , self.cur_hier )
                cur_parse.Readfile(path)
                
        SVparse.path_level -= 1
        return
    def LogicParse(self, s ,lines):
        '''
            When the keyword logic is encountered:
            return information of the following identifier
            commas (multiple identifiers) is not supported...
        '''
        #TODO signed keyword
        self.print(s,verbose=3)
        s.lstrip()
        sign = s.SignParse() 
        bw = s.BracketParse()
        bw = SVstr(''if bw == () else bw[0])
        n, d = s.IDDIMarrParse()
        tp = ('signed ' if sign==True else '') + 'logic'
        lst = [(_n,bw.Slice2num(self.cur_hier.Params, self.cur_hier.AllMacro),self.Tuple2num(_d),tp) for _n,_d in zip(n,d)]
        self.print(lst,verbose=3)
        return lst 
    def ArrayParse(self, s , lines):
        dim = s.BracketParse()
        name = s.IDParse()
        return (name, '', self.Tuple2num(dim), '')
    def ParamParse(self, s ,lines):
        #TODO type parse (in SVstr) , array parameter 
        tp = s.TypeParse(self.cur_hier.AllTypeKeys.union(self.gb_hier.SelfTypeKeys) )
        bw = s.BracketParse()
        bwstr = self.Tuple2str(bw)
        bw = 32 if tp == 'int' and bw== () else self.Bw2num(bw) 
        name = s.IDParse()
        dim = s.BracketParse()
        dimstr = self.Tuple2str(dim)
        if '{' in s:
            while '}' not in s:
                _s, cmt = self.Rdline(lines)
                s += _s
        numstr = s.rstrip().rstrip(';').rstrip(',').s.lstrip('=').lstrip()
        numstrlst = SVstr(numstr).S2lst()
        #num =self.cur_hier.params[name]=s.lstrip('=').S2num(self.cur_hier.Params)
        num = self.cur_hier.params[name] = s.NumParse(self.cur_hier.Params, self.cur_hier.AllMacro, self.package)
        self.cur_hier.paramsdetail[name] = ( name ,\
                                             self.Tuple2num(dim) ,\
                                             tp,\
                                             bw ,\
                                             num ,\
                                             bwstr,\
                                             dimstr,\
                                             numstr ,\
                                             self.cur_key,\
                                             numstrlst)
        if self.flag_port == 'pport' :
            self.cur_hier.paramports[name] = num 
        return name , num
    def PortParse(self, s , lines):
        #bw = s.BracketParse()
        tp = s.TypeParse(self.cur_hier.AllTypeKeys.union(self.gb_hier.SelfTypeKeys) ) 
        tp = 'logic' if tp == '' else tp
        sign = s.SignParse()
        if sign and tp =='logic':
            tp = 'logic signed'
        bw = s.BracketParse()
        name = s.IDParse()
        self.print(name, verbose=4)
        if self.cur_cmt != '':
            for i in self.cur_cmt:
                if 'reged' in i:
                    self.cur_hier.regs[name] = 'N/A'
        bwstr = self.Tuple2str(bw)
        bw = SVstr('' if bw==() else bw[0]).Slice2num(self.cur_hier.Params, self.cur_hier.AllMacro)
        dim = s.BracketParse()
        dimstrtuple = dim
        dimstr = self.Tuple2str(dim)
        #dim = self.Tuple2num(s.BracketParse())
        dim = self.Tuple2num(dim)
        group = [ s.lstrip() for s in self.last_pure_cmt ] 
        self.cur_hier.ports.append((self.cur_key
                                        ,name
                                        ,dim
                                        ,tp
                                        ,bw,bwstr
                                        ,dimstr
                                        ,dimstrtuple
                                        ,self.cur_cmt
                                        ,group) )
    def RdyackParse(self, s , lines):
        _ , args = s.FunctionParse()
        self.cur_hier.protoPorts.append(('rdyack',args[0]))
    def EnumParse(self, s , lines):
        
        if 'logic' in s:
            s.lsplit()
        bw = s.BracketParse()
        bw = SVstr('' if bw==() else bw[0] )
        cmt = self.cur_cmt
        cmts = []
        groups = [] if self.last_pure_cmt == '' else [list(self.last_pure_cmt)]
        _s = SVstr(s.s).lsplit('}') if '}' in s else s.s
        enums = [ i for i in re.split( r'{ *| *, *', _s) ]
        cmt = [''] if cmt =='' else cmt
        cmts = [ [''] for i in range(len(enums)-1) ] + [cmt]
        while '}' not in s:
            #TODO ifdef ifndef blabla
            _s, cmt = self.Rdline(lines)
            cmt = [''] if cmt =='' else cmt
            group = [''] if self.last_pure_cmt == '' else self.last_pure_cmt 
            s += _s
            _s = _s.lsplit('}') if '}' in _s else _s.s
            _enum = [ i for i in re.split( r'{ *| *, *', _s) ]
            enums += _enum
            cmts += [ [''] for i in range(len(_enum)-1) ] + [cmt]
            groups += [ list(group) for i in range(len(_enum)) ]  
        _pair = [ (e,c)  for e,c in zip(enums, cmts) if e !='']
        enums = [ p[0] for p in _pair ]
        cmts  = [ p[1] for p in _pair ]
        self.print(enums,cmts, verbose='EnumParse')
        #_s = s.lsplit('}')
        #enums = SVstr(_s).ReplaceSplit(['{',','] )
        enum_name, enum_num, cmts, idxs, sizes, name_bases= self.Enum2Num( enums, cmts, params=self.cur_hier.Params, macros=self.cur_hier.AllMacro)
        for _name, _num in zip( enum_name, enum_num):
            self.cur_hier.params[_name] = _num
            self.cur_hier.paramsdetail[_name] = ( _name , () , '', 1 , _num , '', '', '','enum literal')
        s.lsplit('}')
        n = s.IDarrParse()
        for _n in n:
            self.cur_hier.enums[_n] = ( enum_name, enum_num , cmts, idxs, sizes, name_bases, groups)
        return [(    _n
                    ,bw.Slice2num(self.cur_hier.Params
                    , self.cur_hier.AllMacro)
                    ,() 
                    , 'enum' 
                    , enum_name
                    , cmts
                    , groups  ) for _n in n]
        
    def ImportParse(self, s , lines):
        s = s.split(';')[0]
        if '::' in s:
            _pkg , _param = s.rstrip().split('::')
        else:
            self.print('only support importing packages')
            return 
        self.cur_hier.imported[_pkg] = _param
        if _param == '*':
            for k,v in self.package[_pkg].params.items():
                self.cur_hier.params[k] = v
            for k,v in self.package[_pkg].paramsdetail.items():
                self.cur_hier.paramsdetail[k]=v
            for k,v in self.package[_pkg].types.items():
                self.cur_hier.types[k] = v
        else:
            if _param in self.package[_pkg].params:
                self.cur_hier.params[_param] = self.package[_pkg].params[_param]  
            if _param in self.package[_pkg].paramsdetail:
                self.cur_hier.paramsdetail[_param] = self.package[_pkg].paramsdetail[_param]  
            if _param in self.package[_pkg].types:
                tp = self.package[_pkg].types[_param] 
                f = SVhier.typefield
                if len(tp)==1:
                    _tp = self.package[_pkg].types.get(tp[0][f.tp])
                    if _tp:
                        self.cur_hier.types[tp[0][f.tp]] = _tp 
                else:
                    for t in tp:
                        _tp = self.package[_pkg].types.get(t[f.tp])
                        if _tp:
                            self.print(t[f.tp],verbose='ImportParse')
                            self.cur_hier.types[t[f.tp]] = _tp 
                self.cur_hier.types[_param] = tp 
            if _param in self.package[_pkg].enums:
                self.cur_hier.enums[_param] = self.package[_pkg].enums[_param]
    def StructParse(self ,s ,lines ):
        _step = 0      
        rule = [ '{' , '}' ]
        attrlist = []
        _s = s
        while(1):
            _w = ''
            if _step == 2:
                name = _s.IDarrParse()
                return (name,attrlist)
            if _s.End():
                _s, self.cur_cmt=self.Rdline(lines)
                continue
            _w = _s.lsplit()
            if _w == rule[_step]:     
                _step = _step+1
                continue
            if _w in self.keyword:
                _catch = self.keyword[_w](_s,lines)
                if type(_catch) == list:
                    attrlist += _catch
                else:
                    attrlist.append(_catch)
                continue
            types = self.cur_hier.AllTypeKeys
            tp = SVstr(_w).TypeParse(types)
            if not tp == '':
                if '::' in tp:
                    _pkg , _param = tp.split('::')
                    self.cur_hier.types[tp] = SVparse.package[_pkg].types[_param]
                    bw = np.sum([x[1] for x in SVparse.package[_pkg].types[_param] ] )
                else:
                    bw = np.sum([x[1] for x in self.cur_hier.AllType[tp] ]) 
                n, d = _s.IDDIMarrParse()
                #_n = _s.IDParse()
                #dim = _s.BracketParse()
                #dimstr = self.Tuple2str(dim)
                #dim = self.Tuple2num(dim) 
                attrlist += [( _n , bw, self.Tuple2num(_d) , tp) for _n, _d in zip(n, d)]
    def TypedefParse(self, s , lines):
        _w = s.lsplit()
        types = self.cur_hier.AllTypeKeys
        tp = SVstr(_w).TypeParse(types)
        if not tp == '':
            try:
                _pkg , _param = tp.split('::')
                self.cur_hier.types[tp] = SVparse.package[_pkg].types[_param]
            except:
                pass
        _m = self.keyword.get(_w)
        _catch = () 
        if _m != None:
            _catch = _m(s , lines)
        else :
            _catch = self.ArrayParse(s,lines)
            _catch = ( _catch[0], int(np.multiply.reduce(_catch[2])*self.cur_hier.types[_w][0][1]) \
                        ,_catch[2], _w)
        if _w == 'struct':
            for n in _catch[0]:
                self.cur_hier.types[n] = _catch[1]
        else :
            if type(_catch)==list:
                for n in _catch:
                    self.cur_hier.types[n[0]] = [n] 
            else:
                self.cur_hier.types[_catch[0]] = [_catch] 
    def RegisterParse(self, s, lines):
        endflag = 0 
        _w = ''
        while True:
            if endflag==0 and s.End():
                break
            if s.End():
                s, self.cur_cmt = self.Rdline(lines)
                continue
            pre_w = _w
            _w = s.lsplit()
            if 'begin' in _w:
                endflag += 1
            if 'end' in _w:
                endflag -= 1
            if s.s[0:2] == '<=':
                pre_w = _w
                _w = s.lsplit('<=')
                _w = s.lsplit()
                self.cur_hier.regs[pre_w] = _w
    def HierParse(self,  s , lines):
        self.cur_s = s
        name = self.cur_s.IDParse()
        new_hier = SVhier(name, self.cur_hier)
        SVparse.hiers[name] = new_hier        
        self.cur_hier = new_hier
        _end = {'package':'endpackage' , 'module':'endmodule'}[self.cur_key]
        if self.cur_key == 'package':
            self.package[name] = new_hier
        self.flag_port = ''
        while(1):
            _w=''
            if self.cur_s == None:
                break        
            if self.cur_s.End():
                self.cur_s, self.cur_cmt = self.Rdline(lines)
                continue
            _w = self.cur_s.lsplit()
            self.PortFlag(_w)
            if _w == _end:
                break 
            if _w in self.keyword:
                _k = self.cur_key
                self.cur_key = _w
                _catch = self.keyword[_w](self.cur_s,lines)
                self.print(self.cur_key,':', self.cur_s,verbose=56)
                self.cur_key = _k
        self.cur_hier = self.cur_hier.scope   
    def DefineParse ( self, s, lines):
        name, args = s.FunctionParse() 
        _s = s.s
        while True:
            if s == None or s.End():
                break        
            else:
                if s.s[-1] == '\\':
                    s, self.cur_cmt = self.Rdline(lines)
                    _s += s.s
                    continue
                else:
                    break
        self.print(_s,verbose=56)
        _s = _s.replace('\\','')
        func = lambda *_args: reduce( lambda x,y: \
                                re.sub( rf'(\b|(``)){y[1]}(\b(``)|\b)', str(y[0]),x )\
                                , [i for i in zip(_args,args)], _s )
        if self.gb_hier.macros.get(name):
            pass
        else:
            self.cur_hier.macros[name] = (args, _s, func)
        self.keyword['`'+name] = self.MacroParse
        self.parselist.add('`'+name)
        self.cur_s.s = ''
        self.print (re.sub( rf'(\b|(``))b(\b(``)|\b)','2',re.sub(rf'(\b|(``))a(\b(``)|\b)', '4', _s) ), verbose=4)
    def MacroParse(self, s, lines):
        #TODO not gonna work properly
        k = self.cur_key
        s.lstrip()
        _s = s.s
        reobj = re.search( r'^[(]', _s)
        if reobj:
            span = SVstr(_s).FirstBracketSpan()
            s.s = SVstr(k+_s[:span[1]+1]).MacroFuncExpand(self.cur_hier.AllMacro) + s.s[span[1]+1:]
            self.print(k+_s[:span[1]+1], verbose='MacroParse')
            self.print(s.s, verbose='MacroParse')
        else:
            s.s = SVstr(k).SimpleMacroExpand(self.cur_hier.AllMacro) + s.s
        self.print(k,verbose=3)
    def IfDefParse( self, s, lines):
        self.cnt_ifdef += 1 
        self.cur_macrodef = 'ifdef'
        n = s.IDParse()
        if self.cur_hier.AllMacro.get(n):
            self.flag_parse = True
        else:
            self.flag_parse = False
        pass
    def IfNDefParse( self, s, lines):
        self.cnt_ifndef += 1
        self.cur_macrodef = 'ifndef'
        n = s.IDParse()
        if not self.cur_hier.AllMacro.get(n):
            self.flag_parse = True
        else:
            self.flag_parse = False 
        pass
    def ElsifParse( self, s, lines):
        self.cur_macrodef = 'elsif'
        n = s.IDParse()
        if self.flag_elsif_parsed:
            self.flag_parse = False
        else:
            if self.cur_hier.AllMacro.get(n):
                self.flag_parse = True
                self.flag_elsif_parsed = True
            else:
                self.flag_parse = False
    def ElseParse( self, s, lines):
        self.cur_macrodef = 'else'
        if self.flag_elsif_parsed:
            self.flag_parse = False
        else:
            self.flag_parse = True
    def EndifParse( self, s, lines):
        if self.cur_macrodef == 'ifdef':
            self.cnt_ifdef -= 1
        elif self.cur_macrodef == 'ifndef':
            self.cnt_ifndef -= 1
        self.cur_macrodef = None 
        self.flag_parse = True
        self.flag_elsif_parsed = False
    def PortFlag(self , w ):
        if ';' in w and self.flag_port =='':
            self.flag_port = 'end' 
        if '#' in w and self.flag_port == '':
            self.flag_port = 'pport' 
        if ('input' in w or 'output' in w) and self.flag_port =='pport':
            self.flag_port = 'port' 
        if ')' in w and self.flag_port == 'port':
            self.flag_port = 'end'
    def Rdline(self, lines):
        s = next(lines,None) 
        # line number TODO
        #return SVstr(s.lstrip().split('//')[0].rstrip().strip(';')) if s != None else None
        #return SVstr(s.lstrip().split('//')[0].rstrip()) if s != None else None
        if s == None:
            return ( None, None)
        _s = SVstr(s.lstrip())
        cmt = _s.CommentParse()  
        self.cur_s = _s
        self.cur_cmt = cmt
        if _s.End():
            if not self.last_end or self.last_pure_cmt == '': 
                if self.cur_cmt != '':
                    self.last_pure_cmt = self.cur_cmt 
            else: 
                self.last_pure_cmt += self.cur_cmt
        self.last_end = _s.End()
        return ( _s.rstrip() , cmt ) 
    def Tuple2num(self, t ):
        return tuple(map(lambda x : SVstr(x).NumParse(params=self.cur_hier.Params, macros=self.cur_hier.AllMacro, package=self.package) ,t))
    def Tuple2str(self, t):
        return reduce(lambda x,y : x+f'[{y}]' , t , '')
    def Bw2num(self, bw):
        return SVstr('' if bw==() else bw[0]).Slice2num(self.cur_hier.Params, self.cur_hier.AllMacro)
    def Enum2Num(self, enum, cmt, params={}, macros=None):
        ofs =0
        cmts = []
        name = []
        name_base = []
        idx = []
        size = []
        num = []
        import copy
        _params = copy.deepcopy(params)
        _params.appendleft({})
        for e,c in zip(enum, cmt):
            _s = SVstr(e)
            _name = _s.IDParse()
            bw = _s.BracketParse()
            bw = SVstr(bw[0]).Slice2TwoNum(_params, macros) if bw else SVstr('').Slice2TwoNum(_params, macros)
            _num = _s.NumParse(_params,self.cur_hier.AllMacro, self.package) 
            if type(bw)==tuple:
                bw = (0,bw[1]-1) if bw[0]=='' else bw
                for i in range (bw[1]-bw[0]+1):
                    idx.append (bw[0]+i)
                    size.append(bw[1]-bw[0]+1)
                    name.append(_name+str(bw[0]+i))
                    name_base.append(_name)
                    num.append( ofs+i if _num=='' else _num + i)
                    cmts.append(c)
                ofs = ofs + bw[1] - bw[0] + 1 if _num=='' else _num + bw[1] - bw[0] + 1
            else:
                idx.append(0)
                size.append(0)
                cmts.append(c)
                name_base.append(_name)
                name.append(_name) #TODO
                num.append ( ofs if _num == '' else _num)
                ofs = ofs+1 if _num == '' else _num+1
            _params[0][name[-1]] = num[-1]
        return name, num, cmts, idx, size, name_base
 
    
def ParseFirstArgument():
    import sys
    SVparse.ParseFiles([(True,sys.argv[1])])
hiers = EAdict(SVparse.hiers)
class SVparseSession(SVutil):
    def __getattr__(self , n ):
        return self.hiers[n]
    def __init__(self,name=None,scope=None, verbose=None):
        self.verbose = V_(VERBOSE) 
        self.parsed = False
        self.package = {}
        self.hiers = {}
        self.paths = []
        self.gb_hier = SVhier('files',None)
        self.gb_hier.types =  {'integer':None,'int':None,'logic':None}
        _top =  GBV.TOPMODULE
        self.top = _top if _top != None else ''
        if GBV.PROJECT_PATH:
            self.base_path = os.environ.get("PWD")+'/'+GBV.PROJECT_PATH
        else:
            match = re.search( r'/sim\b|/include\b|/src\b', os.environ.get("PWD"))
            if match:
                self.base_path = os.environ.get("PWD")[0:match.span()[0]] + '/'
            else:
                self.base_path = os.environ.get("PWD")
        self.include_path = self.base_path + 'include/'
        self.sim_path = self.base_path+'sim/'
        self.src_path = self.base_path+'src/'
        self.cur_scope = '' 
        self.cur_path= ''
        self.flags = { 'pport': False , 'module' : False } #TODO
    def SwapTo (self):
        SVparse.verbose =self.verbose
        SVparse.parsed =self.parsed
        SVparse.package =self.package
        SVparse.hiers =self.hiers
        SVparse.paths =self.paths
        SVparse.gb_hier =self.gb_hier
        SVparse.top =self.top
        SVparse.base_path =self.base_path
        SVparse.include_path =self.include_path
        SVparse.sim_path =self.sim_path
        SVparse.src_path =self.src_path
        SVparse.cur_scope =self.cur_scope
        SVparse.cur_path =self.cur_path
        SVparse.flags =self.flags
    def HiersUpdate(self):
        global hiers
        hiers = EAdict(self.hiers) #TODO
    def ParseFiles(self , paths=[(True,GBV.INC)] ):
        ''' Deprecated '''
        for p in paths:
            self.paths.append(f'{cls.include_path}{p[1]}.sv' if p[0] else p[1] )
        print(self.paths)
        for p in cls.paths:
            n = (p.rsplit('/',maxsplit=1)[1] if '/' in p else p ).replace('.','_')
            cur_parse = SVparseFile( n , self.gb_hier)
            cur_parse.Readfile(p if '/' in p else f'./{p}')
        self.parsed = True
    def IncludeFileParse(self, path):
        f = open(self.include_path+path ,'r')
        paths = []
        '''
        while 1:
            line = f.readline()
            if '`else' in line:
                break
            #TODO this part is very unpolished
        '''
        for line in f.readlines():
            line = line.split('//')[0]
            if '`include' in line:
                line = line.split('`include')[1].split()[0].replace('"','')
                paths.append( self.include_path+line)
        return paths
    def ParseFirstArgument(self):
        import sys
        self.FileParse([(True,sys.argv[1])])
    def Reset(self):
        self.parsed = False
        self.package = {}
        self.hiers = {}
        self.paths = []
        self.gb_hier = SVhier('files',None)
        self.gb_hier.types =  {'integer':None,'int':None,'logic':None}
    def ShowFile(n,start=0,end=None):
        f=open(self.paths[n],'r')
        l=f.readlines()
        end = start+40 if end==None else end
        for i,v in enumerate([ x+start for x in range(end-start)]):
            print(f'{i+start:<4}|',l[v],end='')
    def ShowPaths(self):
        for i,v in enumerate(self.paths):
            print (i ,':  ',v)
    def FileParse(self, paths = None):
        if not paths:
            paths = [(True,GBV.INC)]
        self.SwapTo()
        if SVparse.parsed == True:
            return
        paths = [paths] if type(paths) == tuple else paths
        SVparse.ParseFiles( paths)
        self.parsed = True
        self.HiersUpdate()
    def Reload(self, paths=None):
        self.Reset()
        self.FileParse(paths)
    def TopAllParamEAdict(self):
        return EAdict(self.gb_hier[TOPMODULE].AllParams)
    def ParamGet(self, s, svhier):
        if '::' in s:
            _pkg , _param = s.split('::')
            return self.package[_pkg].params[_param] 
        else:
            return svhier.AllParams.get(s) 
    def TypeGet(self, s, svhier):
        if '::' in s:
            _pkg , _type= s.split('::')
            return self.package[_pkg].types[_type] 
        else:
            return svhier.AllType.get(s) 

if __name__ == '__main__':

    #sv = SVparse('SVparse',None)
    #print (sv.gb_hier.child)
    #ss = SVstr
    #print(ss('[3]').BracketParse() )
    #print(sv.ParamParse(ss('DW  =4;'))  )
    #print(ss(' happy=4;').IDParse())
    #print(sv.parameter)
    #print(ss('waddr;\n').IDParse() )
    #print(sv.LogicParse(ss(' [ $clog2(DW):0]waddr[3] [2][1];')) )
    #print(sv.Slice2num(' 13:0 '))
    #print(sv.StructParse(iter([' {logic a [2];','parameter sex =5;',' logic b [3];', '} mytype;',' logic x;'])))
    #import sys
    #SVparse.ParseFiles(sys.argv[1])
    #
    #print('typedef \'Conf\' under PECfg:')
    #    #SVparse.IncludeFileParse('PE_compile.sv')
    #for i in SVparse.gb_hier.child['DatapathControl.sv'].Types:
    #    print(i)
    #for i in SVparse.hiers.keys():
    #    print (i)
    #print(SVparse.hiers['PECtlCfg'])
    SVstr.verbose = VERBOSE 
    SVparse.verbose = VERBOSE 
    S = SVparseSession()
    S.ParseFirstArgument()

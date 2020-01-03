import numpy as np
import parser as ps
import re
import os
from collections import namedtuple
from collections import deque
from subprocess import Popen, PIPE
from functools import reduce
from SVutil import SVutil 
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
            raise TypeError
    def __getattr__(self, n):
        return self.dic[n]
class SVhier ():
    paramfield = EAdict([ 'name' , 'dim' , 'tp', 'bw' , 'num' , 'bwstr' , 'dimstr', 'numstr' , 'paramtype'] )
    typefield  = EAdict([ 'name' , 'bw' , 'dim' , 'tp' , 'enumliteral', 'cmts' ] )
    portfield =  EAdict( [ 'direction' , 'name' , 'dim' , 'tp' , 'bw' , 'bwstr', 'dimstr', 'dimstrtuple' ] )
    enumfield  = EAdict( [ 'name', 'bw', 'dim', 'tp', 'enumliterals', 'cmts' ] )
    enumsfield = EAdict( [ 'names' , 'nums' , 'cmts' ] )
    enumlfield = EAdict( [ 'name' , 'num' , 'cmt' ] )
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
    def AllParam(self):
        return { k:v for i in self.Params for k,v in i.items() }
    @property
    def AllParamsDetail(self):
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
        self.ParamStr(self.AllParam, w)
        return None
    @property
    def ShowParamsDetail(self):
        w = 20 
        print(f'{self.hier+" All Parameters detail":-^{2*w}}')
        self.FieldStr(self.paramfield,w)
        self.DictStr(self.paramsdetail,w)
        return None
    @property
    def ShowAllParamsDetail(self):
        w = 20 
        print(f'{self.hier+" All Parameters detail":-^{2*w}}')
        self.FieldStr(self.paramfield,w)
        self.DictStr(self.AllParamsDetail,w)
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
            print(f'{io:<{w}}'f'{n:<{w}}'f'{dim.__repr__():<{w}}'f'{tp:<{w}}')
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
                    print (f'{x.__repr__():^{w}}' , end=' ')
                else:
                    print(f'\n{x.__repr__():^{4*w}}',end=' ')
            print()
    def ParamStr(self,dic,w=13):
        for i in ['name','value']:
            print(f'{i:^{w}}' , end=' ')
        print(f'\n{"":=<{2*w}}')
        #l = self.params
        for k,v in dic.items():
            print (f'{k:^{w}}'f'{self.valuecb(v).__repr__() if type(v)==int else v.__repr__():^{w}}', end=' ')
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
    def __repr__(self):
        sc = self._scope.hier if self._scope!=None else None
        return f'\n{self.hier:-^52}\n'+\
                f'{"params":^15}:{[x for x in self.params] !r:^}\n'+\
                f'{"scope":^15}:{sc !r:^}\n'+\
                f'{"types":^15}:{[x for x in self.types] !r:^}\n'+\
                f'{"child":^15}:{[x for x in self.child] !r:^}\n'+\
                f'{"ports":^15}:{[io[0]+" "+n for io,n,*_ in self.ports] !r:^}\n'
        
class SVparse(SVutil):
    # One SVparse object one file, and it's also SVhier
    verbose = 0
    parsed = False
    package = {}
    hiers = {}
    paths = []
    gb_hier = SVhier('files',None)
    gb_hier.types =  {'integer':None,'int':None,'logic':None}
    _top =  TOPMODULE
    top = _top if _top != None else ''
    if PROJECT_PATH:
        base_path = os.environ.get("PWD")+'/'+PROJECT_PATH
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
    @classmethod
    def ARGSParse(cls):
        s = SVARGstr(ARGS)
        l = s.PlusSplit()
        for _l in l:
            func = _l[0]
            args = _l[1:]
            if func == 'define':
                m = s.define(args) 
                for k,v in m.items():
                    cls.gb_hier.macros[k]=v
        pass
    @classmethod
    def ParseFiles(cls , paths=[(True,INC)] ):
        print ( PROJECT_PATH, INC)
        print("supposed base path of the project:", cls.base_path)
        cls.ARGSParse()
        for p in paths:
            if not p[1] == '':
                cls.paths.append(f'{cls.include_path}{p[1]}.sv' if p[0] else p[1] )
        print(cls.paths)
        for p in cls.paths:
            n = (p.rsplit('/',maxsplit=1)[1] if '/' in p else p ).replace('.','_')
            cur_parse = SVparse( n , cls.gb_hier)
            cur_parse.Readfile(p if '/' in p else f'./{p}')
        cls.parsed = True
    @classmethod 
    def IncludeFileParse(cls , path):
        f = open(cls.include_path+path ,'r')
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
                paths.append( cls.include_path+line)
        return paths
    #TODO Testbench sv file parse
    def Readfile(self , path):
        self.print(path)
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
        lst = [(_n,bw.Slice2num(self.cur_hier.Params),self.Tuple2num(_d),tp) for _n,_d in zip(n,d)]
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
        num =self.cur_hier.params[name]=s.lstrip('=').S2num(self.cur_hier.Params)
        self.cur_hier.paramsdetail[name] = ( name , self.Tuple2num(dim) , tp, bw , num , bwstr, dimstr, numstr ,self.cur_key )
        if self.flag_port == 'pport' :
            self.cur_hier.paramports[name] = num 
        return name , num
    def PortParse(self, s , lines):
        cmt = self.cur_cmt
        #bw = s.BracketParse()
        tp = s.TypeParse(self.cur_hier.AllTypeKeys.union(self.gb_hier.SelfTypeKeys) ) 
        tp = 'logic' if tp == '' else tp
        bw = s.BracketParse()
        name = s.IDParse()
        if cmt != '':
            for i in cmt:
                if 'reged' in i:
                    self.cur_hier.regs[name] = 'N/A'
        bwstr = self.Tuple2str(bw)
        bw = SVstr('' if bw==() else bw[0]).Slice2num(self.cur_hier.Params)
        dim = s.BracketParse()
        dimstrtuple = dim
        dimstr = self.Tuple2str(dim)
        #dim = self.Tuple2num(s.BracketParse())
        dim = self.Tuple2num(dim)
        self.cur_hier.ports.append( (self.cur_key,name,dim,tp,bw,bwstr,dimstr, dimstrtuple) )
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
        _s = SVstr(s.s).lsplit('}') if '}' in s else s.s
        enums = SVstr(_s).ReplaceSplit(['{',','] )
        cmts = [ '' for i in range(len(enums)-1) ] + [cmt]
        while '}' not in s:
            _s, cmt = self.Rdline(lines)
            s += _s
            _s = _s.lsplit('}') if '}' in _s else _s.s
            _enum = SVstr(_s).ReplaceSplit(['{',','] )
            enums += _enum
            cmts += [ '' for i in range(len(_enum)-1) ] + [cmt]
        #_s = s.lsplit('}')
        #enums = SVstr(_s).ReplaceSplit(['{',','] )
        enum_name, enum_num = self.Enum2Num( enums, params=self.cur_hier.Params )
        for _name, _num in zip( enum_name, enum_num):
            self.cur_hier.params[_name] = _num
            self.cur_hier.paramsdetail[_name] = ( _name , () , '', 1 , _num , '', '', '','enum literal')
        s.lsplit('}')
        n = s.IDarrParse()
        for _n in n:
            self.cur_hier.enums[_n] = ( enum_name, enum_num , cmts )
        return [( _n,bw.Slice2num(self.cur_hier.Params),() , 'enum' , enums, cmts ) for _n in n]
        
    def ImportParse(self, s , lines):
        s = s.split(';')[0]
        _pkg , _param = s.rstrip().split('::')
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
                self.cur_hier.types[_param] = self.package[_pkg].types[_param] 
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
        name = s.IDParse()
        new_hier = SVhier(name, self.cur_hier)
        SVparse.hiers[name] = new_hier        
        self.cur_hier = new_hier
        _end = {'package':'endpackage' , 'module':'endmodule'}[self.cur_key]
        if self.cur_key == 'package':
            self.package[name] = new_hier
        self.flag_port = ''
        while(1):
            _w=''
            if s == None:
                break        
            if s.End():
                s, self.cur_cmt = self.Rdline(lines)
                continue
            _w = s.lsplit()
            self.PortFlag(_w)
            if _w == _end:
                break 
            if _w in self.keyword:
                _k = self.cur_key
                self.cur_key = _w
                _catch = self.keyword[_w](s,lines)
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
        self.print(_s,verbose=4)
        _s = _s.replace('\\','')
        func = lambda *_args: reduce( lambda x,y: \
                                re.sub( rf'(\b|(``)){y[1]}(\b(``)|\b)', str(y[0]),x )\
                                , [i for i in zip(_args,args)], _s )
        self.cur_hier.macros[name] = (args, _s, func)
        self.keyword['`'+name] = self.MacroParse
        self.parselist.add('`'+name)
        self.print (re.sub( rf'(\b|(``))b(\b(``)|\b)','2',re.sub(rf'(\b|(``))a(\b(``)|\b)', '4', _s) ), verbose=4)
    def MacroParse(self, s, lines):
        k = self.cur_key
        s.lstrip() 
        _s = s.s
        reobj = re.search( r'`^[(]', _s)
        if reobj:
            span = SVstr(_s).FirstBracketSpan()
            s.s = SVstr(k).MacroFuncExpand(self.cur_hier.AllMacro) + s.s[span[1]:]
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
        return ( _s.rstrip() , cmt ) 
    def Tuple2num(self, t ):
        return tuple(map(lambda x : SVstr(x).S2num(params=self.cur_hier.Params) ,t))
    def Tuple2str(self, t):
        return reduce(lambda x,y : x+f'[{y}]' , t , '')
    def Bw2num(self, bw):
        return SVstr('' if bw==() else bw[0]).Slice2num(self.cur_hier.Params)
    def Enum2Num(self, enum, params={}):
        ofs =0
        name = []
        num = []
        import copy
        _params = copy.deepcopy(params)
        _params.appendleft({})
        for e in enum:
            _s = SVstr(e)
            _name = _s.IDParse()
            bw = _s.BracketParse()
            bw = SVstr(bw[0]).Slice2TwoNum(_params) if bw else SVstr('').Slice2TwoNum(_params)
            _num = _s.NumParse(_params) 
            if type(bw)==tuple:
                bw = (0,bw[1]-1) if bw[0]=='' else bw
                for i in range (bw[1]-bw[0]+1):
                    name.append(_name+str(bw[0]+i))
                    num.append( ofs+i if _num=='' else _num + i)
                ofs = ofs + bw[1] - bw[0] + 1 if _num=='' else _num + bw[1] - bw[0] + 1
            else:
                name.append(_name) #TODO
                num.append ( ofs if _num == '' else _num)
                ofs = ofs+1 if _num == '' else _num+1
            _params[0][name[-1]] = num[-1]
        return name, num 
class SVstr(SVutil):
    sp_chars = ['=','{','}','[',']','::',';',',','(',')','#']
    op_chars = ['+','-','*','/','(',')']
    verbose = 0
    def __init__(self,s):
        self.s = s
    def __repr__(self):
        return self.s
    def __add__(self, foo ):
        return SVstr( self.s+ foo.s )
    def __iadd__(self,foo ):
        self.s += foo.s
        return self
    def split( self, sep=None, maxsplit=-1):
        return self.s.split(sep=sep,maxsplit=maxsplit)
    def lstrip(self,chars=None):
        self.s = self.s.lstrip(chars)
        return self
    def rstrip(self,chars=None):
        self.s = self.s.rstrip(chars)
        return self
    def lsplit(self,sep=None):    
        #split sep or any special chars from the start
        self.lstrip()
        if self.End():
            return ''
        _s = self.s
        if sep == None:    
            _idx = SVstr(_s).FirstSPchar()
            _spidx = _s.find(' ')
            if _idx != -1 and (_idx < _spidx or _spidx == -1):
                if _idx == 0:
                    _s , self.s = _s[0] , _s[1:]
                else:
                    _s , self.s = _s[0:_idx] , _s[_idx:]
            else:
                _s  = _s.split(maxsplit=1)
                self.s = _s[1] if len(_s)>1 else ''
                _s = _s[0]
            return _s
        _s = _s.split(sep,maxsplit=1)
        if len(_s)!=0:
            self.s=_s[1]
            _s = _s[0]
        else:
            _s = ''
            self.s=''
        return _s
    def FirstSPchar(self):
        # FUCKING cool&concise implementation:
        return next( (i for i,x in enumerate(self.s) if x in self.sp_chars) , -1)
        #_specC = [ x for x in (map(self.s.find,self.sp_chars)) if x > -1]
        #_idx = -1 if len(_specC) == 0 else min(_specC)
        #return _idx
    def CommentParse(self):
        _s = self.s.rstrip()
        if '//' in _s:
            self.s = _s.split('//')[0] 
            return _s.split('//')[1:]
        else:
            return ''
    def IDParse (self):
        '''
            find one identifier at the start of the string
            TODO multiple ID ( often sperated by , ) 
        '''
        if self.End():
            return ''
        self.s = self.s.lstrip()
        _idx = self.FirstSPchar()
        if _idx != -1:
            _s = self.s[0:_idx]
            self.s = self.s[_idx:]
            return _s.rstrip()
        _s = self.s.rstrip('\n').rstrip().split(maxsplit=1)
        self.s =  _s[1] if len(_s)>1 else ''
        return _s[0].rstrip(';')
    def IDarrParse(self):
        n= []
        name = self.IDParse()
        n.append(name)
        while self.s[0] == ',': 
            self.s = self.s[1:]
            name = self.IDParse()
            n.append(name)
        return n
    def IDDIMarrParse(self):
        n = []
        d = []
        name = self.IDParse()
        n.append(name)
        dim = self.BracketParse()  
        d.append(dim) 
        while self.s[0] == ',': 
            self.s = self.s[1:]
            name = self.IDParse()
            n.append(name)
            dim = self.BracketParse()  
            d.append(dim) 
        return n, d
    def SignParse (self):
        self.lstrip()
        if 'signed' in self.s:
            self.s = self.s.replace('signed','')
            return True
        else:
            return False
    def BracketParse(self,  bracket = '[]' ):
        # find and convert every brackets at the start of the string
        self.s = self.s.lstrip()
        num = []
        while(1):
            if self.End() or self.s[0] != bracket[0]:
                break
            rbrack = self.s.find(bracket[1])
            num.append(self.s[1:rbrack] )
            self.s=self.s[rbrack+1:].lstrip()
        return tuple(num)
    def TypeParse(self , typekeylist ):
        tp = ''
        temp = SVstr(self.s).lsplit()
        if temp in typekeylist or '::' in temp:
            tp = temp
            self.lsplit()
        return tp
    def KeywordParse(self, key , rules ):
        _step = 0
        self.s = self.s.lsplit()
        if self.s == None:
            raise StopIteration
        if _step == len(rules) :
            return
    def FunctionParse(self):
        self.print(self.End(),verbose=3)
        func = self.lsplit()
        if self.End():
            return func , []
        if self.s[0] == '(':
            _s , self.s = self.split(')',maxsplit=1)
            args = SVstr(_s).ReplaceSplit(['(',','])
            return func,args
        else:
            return func, []
    def NumParse(self,params):
        # split the equal sign at the start of the string
        # return left string as num, meaning that it converts
        # the remain string no matter what ( determine if 
        # a string is an equation is hard), leaving the object
        # empty
        num = self.lstrip('=').S2num(params)
        self.s = ''
        return num 
    def Arit2num(self, s):
        pass
    def S2num(self,params):
        _s = self.s.lstrip()
        if '$clog2' in _s:
            _temp = self.s.split('(')[1].split(')')[0] 
            _s = _s.replace( _s[_s.find('$'):_s.find(')')+1] , 'int(np.log2('+ _temp + '))')
        _s_no_op = SVstr(_s).ReplaceSplit(self.op_chars+[',', "'", '{', '}'])
        #TODO package import :: symbol  , white spaces around '::' not handled
        for w in _s_no_op:
            if '::' in w:
                _pkg , _param = w.split('::')
                _s = _s.replace(_pkg+'::'+_param,str(SVparse.package[_pkg].params[_param]) )
            for p in params:    
                if w in p:
                    _s = re.sub(rf'\b{w}\b', str(p[w]), _s)
                    #_s = _s.replace( w , str(p[w]) )
                    break
        _s = _s.replace("\'{", ' [ ').replace('{',' [ ').replace('}',' ] ').replace(',',' , ')
        slist = _s.split()
        for i,v in enumerate(slist):
            if '\'b' in v:
                _n = v.split('\'b')[1]
                slist[i] = f'int( "{_n}", 2)'
            if '\'h' in v:
                _n = v.split('\'h')[1]
                slist[i] = f'int( "{_n}", 16)'
            if '\'o' in v:
                _n = v.split('\'o')[1]
                slist[i] = f'int( "{_n}", 8)'
            if '\'d' in v:
                _n = v.split('\'d')[1]
                slist[i] = f'int("{_n}")'
        _s = ' '.join(slist)
        #_s = _s.replace('\'','')
        try:
            return eval(ps.expr(_s).compile('file.py'))
        except:
            if _s !='':
                self.print(f"S2num failed, return original string: {_s}",verbose=1)
            return _s
    def Slice2num(self,params):
        if self.s == '':
            return 1
        _temp = self.s.replace('::','  ')
        _idx = _temp.find(':')
        _s,_e = self.s[0:_idx] , self.s[_idx+1:]
        try:
            return SVstr(_s).S2num(params)-SVstr(_e).S2num(params)+1
        except(TypeError):
            print('Slice2num fail, TypeError')
            print (self.s)
    def Slice2TwoNum(self,params):
        if self.s == '':
            return 1
        _temp = self.s.replace('::','  ')
        _idx = _temp.find(':')
        _s,_e = self.s[0:_idx] , self.s[_idx+1:]
        try:
            return (SVstr(_s).S2num(params),SVstr(_e).S2num(params))
        except(TypeError):
            print('Slice2num fail, TypeError')
            print (self.s)
    def SimpleMacroExpand(self, macros):
        '''
            Expand a simple substituion macro
            the string must start with ` and end with a word character
        '''
        _s = self.s.rstrip().lstrip()
        exp = _s
        reobj = True
        while reobj:
            reobj = re.search(r'`(\w+)\b', exp)
            if reobj:
                m0 = reobj.group(0)
                m = reobj.group(1)
                exp = re.sub(rf'{m0}\b', f'macros[\'{m}\'][2]()', exp)
        try:
            return eval(ps.expr(exp).compile('file.py'))
        except:
            print('macro expansion error')
    def MacroFuncExpand(self, macros):
        '''
            Expand a potentially nested macro to a string.
            Limitation: the string start with ` and end with )
            Arguments:
                macros: the dictionary to find required macro definitions
        '''
        _s = self.s.rstrip().lstrip()
        exp = _s
        reobj = True
        exp = re.sub(rf'[\']', '\\\'', exp)
        exp = re.sub(rf'["]', '\\\"', exp)
        exp = re.sub(rf'[(]', '("', exp)
        exp = re.sub(rf'[,]', '","' , exp)  
        exp = re.sub(rf'(?!^[`])[`]', '"+`', exp)      
        exp = re.sub(rf'(?![)]$)[)]',  '")+"', exp)
        exp = re.sub(rf'[)]$', '")', exp) 
        while reobj:
            self.print(exp,verbose=1)
            reobj = re.search( r'`(\w+)\b', exp )
            if reobj:
                m0 = reobj.group(0)
                m = reobj.group(1)
                if macros[m][0] == []:
                    exp = re.sub(rf'{m0}\b', f'macros[\'{m}\'][2]()+"', exp) 
                else:
                    exp = re.sub(rf'{m0}\b', f'macros[\'{m}\'][2]', exp) 
            self.print(exp,verbose=1)
        try:
            return eval(ps.expr(exp).compile('file.py'))
        except:
            print('macro expansion error')
    def MultiMacroExpand(self, macros):
        _s = self.s
        nested = -1 
        rbkt= 0
        exp = _s
        reobj = True
        while reobj:
            reobj = re.search ( r'`(\w+)\b', exp)
            if reobj:
                span = reobj.span()
                for i,c in enumerate(exp[span[0]:]):
                    if c == '(':
                        nested += 1
                    if c == ')':
                        nested -= 1
                        if nested == -1:
                            rbkt = i
                if rbkt == 0:
                    rbkt = span[1]
                    exp = exp[0:span[0]] + SVstr(exp[span[0]:rbkt]).SimpleMacroExpand(macros) + exp[rbkt:]
                else:
                    exp = exp[0:span[0]] + SVstr(exp[span[0]:rbkt+1]).MacroFuncExpand(macros) + exp[rbkt+1:]
                nested = -1 
                rbkt = 0
        return exp
    def FirstBracketSpan(self):
        '''
            Find the first enclosed round bracket span if the 
            string start with (
        '''
        if self.s[0] != '(':
            return (0,0)
        rbkt = 0
        nested = 0 
        reobj = re.search ( r'`(\w+)\b', exp)
        for i,c in enumerate():
            if c == '(':
                nested += 1
            if c == ')':
                nested -= 1
                if nested == -1:
                    rbkt = i
        return (0,rbkt)
    def DeleteList(self,clist):
        _s = self.s
        for c in clist:
            _s = _s.replace(c,'')
        return _s
    def ReplaceSplit(self, clist):
        _s = self.s
        for c in clist:
            _s = _s.replace(c, ' ')
        return _s.split()
    def __len__(self):
        return len(self.s)
    def __contains__(self,st):
        return st in self.s
    def End(self):
        return self.s==''
class SVARGstr(SVstr):
    def Pluslsplit(self):
        bcnt = False 
        prvc = ''
        if self.End():
            return None
        for i,c in enumerate(self.s):
            if c == '"':
                if prvc == '\\':
                    pass 
                else:
                    bcnt = False if bcnt else True 
            if bcnt == False:
                if c == '+' or c ==' ':
                    _s = self.s[0:i]
                    self.s = self.s[i+1:].lstrip()
                    return _s, c
            prvc = c
        _s = self.s
        self.s = ''
        return _s, '' 
    def PlusSplit(self):
        l = []
        parse = self.Pluslsplit()
        while parse:
            if parse == ('','+'):
                l.append([])
            if parse[0] != '':
                l[-1].append(parse[0])
            parse = self.Pluslsplit()
        return l
    def define(self, args):
        l = {} 
        for a in args:
            _a = a.split('=')
            name = _a[0]
            text = _a[1] if len(_a) > 1 else ''
            func = lambda : text;
            l[name]=([],text,func)
        return l 
    def incdir(self, args):
        #TODO
        return [] 
    
def ParseFirstArgument():
    import sys
    SVparse.ParseFiles([(True,sys.argv[1])])
hiers = EAdict(SVparse.hiers)
class SVparseSession(SVutil):
    def __getattr__(self , n ):
        return self.hiers[n]
    def __init__(self,name=None,scope=None):
        self.verbose = 0
        self.parsed = False
        self.package = {}
        self.hiers = {}
        self.paths = []
        self.gb_hier = SVhier('files',None)
        self.gb_hier.types =  {'integer':None,'int':None,'logic':None}
        _top =  TOPMODULE
        self.top = _top if _top != None else ''
        if PROJECT_PATH:
            self.base_path = os.environ.get("PWD")+'/'+PROJECT_PATH
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
    def ParseFiles(self , paths=[(True,INC)] ):
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
            paths = [(True,INC)]
        self.SwapTo()
        if SVparse.parsed == True:
            return
        paths = [paths] if type(paths) == tuple else paths
        SVparse.ParseFiles( paths)
        self.parsed = True
        self.HiersUpdate()
    def TopAllParamEAdict():
        return EAdict(self.gb_hier[TOPMODULE].AllParam)

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
    SVstr.verbose = 1
    SVparse.verbose = 1
    S = SVparseSession()
    S.ParseFirstArgument()

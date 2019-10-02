import numpy as np
import parser as ps
import re
import os
from collections import namedtuple
from collections import deque
from subprocess import Popen, PIPE
from functools import reduce
from enum import Enum
#Nico makefile specified
TOPMODULE = os.environ.get('TOPMODULE','')
TEST = os.environ.get('TEST','')
#SVutil optional specified
SVutil = os.environ.get('SVutil','')
TESTMODULE = os.environ.get('TESTMODULE','')
SV = os.environ.get('SV','')
TOPSV = os.environ.get('TOPSV','')
INC = os.environ.get('INC','')
def ToClip(s):
    try:
        p = Popen(['xclip' ,'-selection' , 'clipboard'], stdin=PIPE)
        p.communicate(input=s.encode())
    except:
        print( "xclip not found or whatever, copy it yourself")
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
    typefield  = EAdict([ 'name' , 'bw' , 'dim' , 'tp' , 'enumliteral' ] )
    portfield =  EAdict( [ 'direction' , 'name' , 'dim' , 'tp' , 'bw' , 'bwstr', 'dimstr' ] )
    def __init__(self,name,scope):
        self.hier= name # this is fucking ambiguous, but str method use it so it stays put
        self.name = name
        self.params = {}
        self.paramsdetail = {}
        self.types = {}
        self.child = {}
        self.paramports = {} 
        self.ports = []
        self.protoPorts = []
        self.imported = {} 
        self._scope = scope
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
    def Types(self):
        if self._scope == None:
            _l = deque([h.types for _ , h in self.child.items()] )
            return _l 
        else:
            _l = self._scope.Types
            _l.appendleft(self.types)
            return _l
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
    def ShowParams(self):
        w=17
        print(f'{self.hier+" Parameters":-^{2*w}}' )
        self.ParamStr(w)
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
    def ParamStr(self,w=13):
        for i in ['name','value']:
            print(f'{i:^{w}}' , end=' ')
        print(f'\n{"":=<{2*w}}')
        l = self.params
        for k,v in l.items():
            print (f'{k:^{w}}'f'{v.__repr__():^{w}}', end=' ')
            print()
       
    def __repr__(self):
        sc = self._scope.hier if self._scope!=None else None
        return f'\n{self.hier:-^52}\n'+\
                f'{"params":^15}:{[x for x in self.params] !r:^}\n'+\
                f'{"scope":^15}:{sc !r:^}\n'+\
                f'{"types":^15}:{[x for x in self.types] !r:^}\n'+\
                f'{"child":^15}:{[x for x in self.child] !r:^}\n'+\
                f'{"ports":^15}:{[io[0]+" "+n for io,n,*_ in self.ports] !r:^}\n'
        
class SVparse():
    # One SVparse object one file, and it's also SVhier
    parsed = False
    package = {}
    hiers = {}
    paths = []
    gb_hier = SVhier('files',None)
    gb_hier.types =  {'integer':None,'int':None,'logic':None}
    _top =  TOPMODULE
    top = _top if _top != None else ''
    base_path = os.environ.get("PWD").replace('/vcs','').replace('/verilator','').replace('/sim','')+'/'
    print(base_path)
    include_path = base_path + 'include/'
    sim_path = base_path+'sim/'
    src_path = base_path+'src/'
    cur_scope = '' 
    cur_path= ''
    flags = { 'pport': False , 'module' : False } #TODO
    def __getattr__(self , n ):
        return hiers[n]
    def __init__(self,name,scope):
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
                        '`include':self.IncludeRead ,'`rdyack_input':self.RdyackParse, '`rdyack_output':self.RdyackParse}
    @classmethod
    def ParseFiles(cls , paths=[(True,INC)] ):
        for p in paths:
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
        print(path)
        self.f = open(path , 'r')
        self.cur_path = path
        self.lines = iter(self.f.readlines())
        _s = self.Rdline(self.lines)
        while(1):
            _w = ''
            if _s == None:
                return
            if _s.End():
                _s=self.Rdline(self.lines)
                continue 
            _w = _s.lsplit()
            _catch = None
            if _w in {'typedef','package','import','module','`include'}:
                self.cur_key = _w
                _catch = self.keyword[_w](_s,self.lines) 
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
        #TODO signed keyword
        s.lstrip()
        sign = s.SignParse() 
        bw = s.BracketParse()
        bw = SVstr(''if bw == () else bw[0])
        name = s.IDParse()
        dim = s.BracketParse()  
        tp = ('signed ' if sign==True else '') + 'logic'
        return (name,bw.Slice2num(self.cur_hier.Params),self.Tuple2num(dim),tp)
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
        numstr = s.rstrip().rstrip(';').rstrip(',').s.lstrip('=').lstrip()
        num =self.cur_hier.params[name]=s.lstrip('=').S2num(self.cur_hier.Params)
        self.cur_hier.paramsdetail[name] = ( name , self.Tuple2num(dim) , tp, bw , num , bwstr, dimstr, numstr ,self.cur_key )
        if self.flag_port == 'pport' :
            self.cur_hier.paramports[name] = num 
        return name , num
    def PortParse(self, s , lines):
        bw = s.BracketParse()
        tp = 'logic'
        temp = s.lsplit()
        types = self.cur_hier.AllTypeKeys.union(self.gb_hier.SelfTypeKeys)
        #TODO clean this up, why not IDparse for name?
        if temp in types or '::' in temp :
            tp = temp
            bw = s.BracketParse()
            name = s.IDParse()
        else:
            name = temp
        bwstr = self.Tuple2str(bw)
        bw = SVstr('' if bw==() else bw[0]).Slice2num(self.cur_hier.Params)
        dim = s.BracketParse()
        dimstr = self.Tuple2str(dim)
        #dim = self.Tuple2num(s.BracketParse())
        dim = self.Tuple2num(dim)
        self.cur_hier.ports.append( (self.cur_key,name,dim,tp,bw,bwstr,dimstr) )
    def RdyackParse(self, s , lines):
        _ , args = s.FunctionParse()
        self.cur_hier.protoPorts.append(('rdyack',args[0]))
    def EnumParse(self, s , lines):
        
        if 'logic' in s:
            s.lsplit()
        bw = s.BracketParse()
        bw = SVstr('' if bw==() else bw[0] )
        while '}' not in s:
            s += self.Rdline(lines)
        _s = s.lsplit('}')
        _enum = SVstr(_s).ReplaceSplit(['{',','] )
        for i,p in enumerate(_enum):
            self.cur_hier.params[p]= i
        name = s.IDParse()
        return ( name ,bw.Slice2num(self.cur_hier.Params),() , 'enum' , _enum  )
    def ImportParse(self, s , lines):
        s = s.split(';')[0]
        _pkg , _param = s.rstrip().split('::')
        self.cur_hier.imported[_pkg] = _param
        if _param == '*':
            for k,v in self.package[_pkg].params.items():
                self.cur_hier.params[k] = v
            for k,v in self.package[_pkg].types.items():
                self.cur_hier.types[k] = v
        else:
            if _param in self.package[_pkg].params:
                self.cur_hier.params[_param] = self.package[_pkg].params[_param]  
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
                name = _s.IDParse()
                return (name,attrlist)
            if _s.End():
                _s=self.Rdline(lines)
                continue
            _w = _s.lsplit()
            if _w == rule[_step]:     
                _step = _step+1
                continue
            if _w in self.keyword:
                _catch = self.keyword[_w](_s,lines)
                attrlist.append(_catch)
                continue
            for t in self.cur_hier.Types:
                if _w in t :
                    _n = _s.IDParse()
                    dim = _s.BracketParse()
                    attrlist.append( ( _n , np.sum([x[1] for x in t[_w] ]) ,self.Tuple2num(dim) , _w) )
                    break
    def TypedefParse(self, s , lines):
        _w = s.lsplit()
        _m = self.keyword.get(_w)
        _catch = () 
        if _m != None:
            _catch = _m(s , lines)
        else :
            _catch = self.ArrayParse(s,lines)
            _catch = ( _catch[0],np.multiply.reduce(_catch[2])*self.cur_hier.types[_w][0][1]\
                        ,_catch[2], _w)
        if _w == 'struct':
            self.cur_hier.types[_catch[0]] = _catch[1]
        else :
            self.cur_hier.types[_catch[0]] = [_catch] 
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
            if s.End():
                s = self.Rdline(lines)
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
        return SVstr(s.lstrip().split('//')[0].rstrip()) if s != None else None
    def Tuple2num(self, t ):
        return tuple(map(lambda x : SVstr(x).S2num(params=self.cur_hier.Params) ,t))
    def Tuple2str(self, t):
        return reduce(lambda x,y : x+f'[{y}]' , t , '')
    def Bw2num(self, bw):
        return SVstr('' if bw==() else bw[0]).Slice2num(self.cur_hier.Params)
class SVstr():
    sp_chars = ['=','{','}','[',']','::',';',',','(',')','#']
    op_chars = ['+','-','*','/','(',')']
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
    def IDParse (self):
        # find one identifier at the start of the string
        self.s = self.s.lstrip()
        _idx = self.FirstSPchar()
        if _idx != -1:
            _s = self.s[0:_idx]
            self.s = self.s[_idx:]
            return _s.rstrip()
        _s = self.s.rstrip('\n').rstrip().split(maxsplit=1)
        self.s =  _s[1] if len(_s)>1 else ''
        return _s[0].rstrip(';')
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
        func = self.lsplit()
        _s , self.s = self.split(')',maxsplit=1)
        args = SVstr(_s).ReplaceSplit(['(',','])
        return func,args
    def Arit2num(self, s):
        pass
    def S2num(self,params):
        _s = self.s.lstrip()
        if '$clog2' in _s:
            _temp = self.s.split('(')[1].split(')')[0] 
            _s = _s.replace( _s[_s.find('$'):_s.find(')')+1] , 'int(np.log2('+ _temp + '))')
        _s_no_op = SVstr(_s).ReplaceSplit(self.op_chars)
        #TODO package import :: symbol  , white spaces around '::' not handled
        for w in _s_no_op:
            if '::' in w:
                _pkg , _param = w.split('::')
                _s = _s.replace(_pkg+'::'+_param,str(SVparse.package[_pkg].params[_param]) )
            for p in params:    
                if w in p:
                    _s = _s.replace( w , str(p[w]) )
                    break
        _s = _s.replace('{','[').replace('}',']').replace('\'','')
        try:
            return eval(ps.expr(_s).compile('file.py'))
        except:
            print("S2num failed, return original string")
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
def ParseFirstArgument():
    import sys
    SVparse.ParseFiles([(True,sys.argv[1])])
def Reset():
    SVparse.parsed = False
def ShowFile(n,start=0,end=None):
    f=open(SVparse.paths[n],'r')
    l=f.readlines()
    end = start+40 if end==None else end
    for i,v in enumerate([ x+start for x in range(end-start)]):
        print(f'{i+start:<4}|',l[v],end='')
def ShowPaths():
    for i,v in enumerate(SVparse.paths):
        print (i ,':  ',v)
def FileParse( paths = [(True,INC)]):
    if SVparse.parsed == True:
        return
    paths = [paths] if type(paths) == tuple else paths
    SVparse.ParseFiles( paths)
    SVparse.parsed = True

hiers = EAdict(SVparse.hiers)

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
    ParseFirstArgument()

import numpy as np
import parser as ps
import re
from os import environ
from collections import namedtuple
from collections import deque
from subprocess import Popen, PIPE
def ToClip(s):
    try:
        p = Popen(['xclip' ,'-selection' , 'clipboard'], stdin=PIPE)
        p.communicate(input=s.encode())
    except:
        print( "xclip not found or whatever, copy it yourself")
class SVhier ():
    def __init__(self,name,scope):
        self.hier= name
        self.params = {}
        self.types = {}
        self.child = {}
        self.ports = []
        self.protoPorts = []
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
        for io , n ,dim,tp in self.ports:
            print(f'{io:<{w}}'f'{n:<{w}}'f'{dim.__repr__():<{w}}'f'{tp:<{w}}')
    @property
    def ShowConnect(self,*conf):
        s = '.*,\n'
        for t , n in self.protoPorts:
            if t == 'rdyack':
                s += '`rdyack_connect('+n+',),\n'
            if t == 'dval':
                s += '`dval_connect('+n+',),\n'
        for io , n , *_ in self.ports:
            s += '.'+n+'(),\n'
        s = s[:-2]
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
    package = {}
    hiers = {}
    paths = []
    gb_hier = SVhier('files',None)
    gb_hier.types =  {'integer':None,'int':None,'logic':None}
    cur_scope = ''
    base_path = '/home/enhoshen/research/lpAccel/'
    include_path = '/home/enhoshen/research/lpAccel/include/'
    def __getattr__(self , n ):
        return hiers[n]
    def __init__(self,name,scope):
        self.cur_hier = SVhier(name,scope) if scope != None else SVhier(name,self.gb_hier) 
        SVparse.hiers[name]= self.cur_hier
        self.cur_key = ''
        self.keyword = { 'logic':self.LogicParse , 'parameter':self.ParamParse, 'localparam':self.ParamParse,\
                        'typedef':self.TypeParse , 'struct':self.StructParse  , 'package':self.HierParse , 'enum': self.EnumParse,\
                        'module':self.HierParse , 'import':self.ImportParse, 'input':self.PortParse , 'output':self.PortParse,\
                        '`rdyack_input':self.RdyackParse, '`rdyack_output':self.RdyackParse}
    @classmethod
    def ParseFiles(cls , path , inc=True ):
        _top =  environ.get("TOPMODULE") 
        _top = _top if _top != None else ''
        paths = cls.IncludeFileParse(path) if inc == True else path
        cls.paths += paths
        for p in paths:
            print(p)
            n = p.rsplit('/',maxsplit=1)[1]
            cur_parse = SVparse( n , cls.gb_hier)
            cur_parse.Readfile(p)
    @classmethod 
    def IncludeFileParse(cls , path):
        f = open(cls.include_path+path)
        paths = []
        while 1:
            line = f.readline()
            if '`else' in line:
                break
            #TODO this part is very unpolished
        for line in f.readlines():
            line = line.split('//')[0]
            if '`include' in line:
                line = line.split('`include')[1].split()[0].replace('"','')
                paths.append( cls.include_path+line)
        return paths
    def Readfile(self , path):
        try:
            self.f = open(path)
        except:
            return
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
            if _w in {'typedef','package','import','module'}:
                self.cur_key = _w
                _catch = self.keyword[_w](_s,self.lines) 
    def LogicParse(self, s ,lines):
        bw = s.BracketParse()
        bw = SVstr(''if bw == () else bw[0])
        name = s.IDParse()
        dim = s.BracketParse()  
        return (name,bw.Slice2num(self.cur_hier.Params),self.Tuple2num(dim),'logic')
    def ParamParse(self, s ,lines):
        #TODO type parse (in SVstr) , array parameter 
        name = s.IDParse()
        dim = s.BracketParse()
        s.rstrip().rstrip(';').rstrip(',')
        _n=self.cur_hier.params[name]=s.lstrip('=').S2num(self.cur_hier.Params)
        return name,_n
    def PortParse(self, s , lines):
        bw = s.BracketParse()
        tp = 'logic'
        temp = s.lsplit()
        types = [ x for i in self.cur_hier.Types for x in i.keys() ]
        types += [ x for x in self.gb_hier.types.keys()]
        if temp in types or '::' in temp :
            tp = temp
            bw = s.BracketParse()
            name = s.lsplit()
        else:
            name = temp
        dim = self.Tuple2num(s.BracketParse())
        self.cur_hier.ports.append( (self.cur_key,name,dim,tp) )
    def RdyackParse(self, s , lines):
        _ , args = s.FunctionParse()
        self.cur_hier.protoPorts.append(('rdyack',args[0]))
    def EnumParse(self, s , lines):
        
        if 'logic' in s:
            s.lsplit()
        bw = s.BracketParse()
        bw = SVstr('' if bw==() else bw[0])    
        _s = s.lsplit('}')
        _enum = SVstr(_s).ReplaceSplit(['{',','] )
        for i,p in enumerate(_enum):
            self.cur_hier.params[p]= i
        name = s.IDParse()
        return ( name ,bw.Slice2num(self.cur_hier.Params),() , 'enum' , _enum  )
    def ImportParse(self, s , lines):
        s = s.split(';')[0]
        _pkg , _param = s.rstrip().split('::')
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
    def TypeParse(self, s , lines):
        _w = s.lsplit()
        _catch = self.keyword[_w](s , lines)
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
        while(1):
            _w=''
            if s.End():
                s = self.Rdline(lines)
                continue
            _w = s.lsplit()
            if _w == _end:
                break 
            if _w in self.keyword:
                _k = self.cur_key
                self.cur_key = _w
                _catch = self.keyword[_w](s,lines)
                self.cur_key = _k
        self.cur_hier = self.cur_hier.scope   
    def Rdline(self, lines):
        s = next(lines,None) 
        return SVstr(s.lstrip().split('//')[0].rstrip().strip(';')) if s != None else None
    def Tuple2num(self, t ):
        return tuple(map(lambda x : SVstr(x).S2num(params=self.cur_hier.Params) ,t))
class SVstr():
    sp_chars = ['=','{','}','[',']','::',';',',','(',')','#']
    op_chars = ['+','-','*','/','(',')']
    def __init__(self,s):
        self.s = s
    def __repr__(self):
        return self.s
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
    def TypeParse(self , params):
        pass
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
            print('TypeError')
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
class EAdict():
    def __init__(self,dic):
        self.dic = dic
    def __getattr__(self, n):
        return self.dic[n]
def ParseFirstArgument():
    import sys
    SVparse.ParseFiles(sys.argv[1])
def Reset():
    ParseFirstArgument()
def ShowFile(n,start=0,end=None):
    f=open(SVparse.paths[n])
    l=f.readlines()
    end = start+40 if end==None else end
    for i,v in enumerate([ x+start for x in range(end-start)]):
        print(f'{i+start:<4}|',l[v],end='')
def ShowPaths():
    for i,v in enumerate(SVparse.paths):
        print (i ,':  ',v)
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
    hiers = EAdict(SVparse.hiers)

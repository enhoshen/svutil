import os
import sys
from SVutil.SVparse import *
from SVutil.SVgen import * 
from SVutil.SVclass import *
import itertools
import numpy as np
from functools import reduce
@SVgen.UserClass
class TestGen(SVgen):
    def __init__(self, ind=Ind(0), session=None):
        super().__init__(session=session)
        self.customlst += ['eventlst', 'pyeventlgclst', 'clk_domain_lst']
        self.eventlst = [   ( 'intr_ev', 'intr_any'),
                            ( 'init_ev', 'init_cond'),                         
                            ( 'resp_ev', 'resp_cond'), 
                            ( 'fin_ev' , 'fin_cond'),
                            ( 'sim_stop_ev' , 'sim_stop'),
                            ( 'sim_pass_ev' , 'sim_pass'),
                            ( 'time_out_ev' , 'time_out')]
        self.pyeventlgclst = ['sim_pass', 'sim_stop', 'time_out']
        self.clk_domain_lst = [('','_n')]
    def SVDefineBlk(self): 
        ind = self.cur_ind.Copy() 
        yield ''
        s = '\n'
        s += 'import "DPI-C" function string getenv(input string env_name);\n'
        s += '`timescale 1ns/1ns\n'
        s += '`include ' + f'"{self.incfile}.sv"\n' 
        s += f'`define {self.endcyclemacro} 100\n'  
        s += f'`define {self.hclkmacro} 5\n'  

        s += f'`define TEST_CFG //TODO\n'

        s += f'`define FSDBNAME(suffix) `"{self.fsdbname}``suffix``.fsdb`"\n'
        s = s.replace('\n',f'\n{ind.b}')
        yield s

    def ModBlk(self):
        ind = self.cur_ind.Copy() 
        yield ''
        s = f'{ind.b}module ' + GBV.TOPMODULE + ';\n'
        yield s+self.InitialStr(ind=ind+1)
        s = '\n' + ind.b +'endmodule'
        yield s
        
    @SVgen.Str
    def InitialStr(self, ind=None):
        ck_lst   = reduce( (lambda x,y: x+', '+f'{y[0]+"_" if y[0] != "" else ""}clk'),       self.clk_domain_lst , '')[2:]
        rst_lst  = reduce( (lambda x,y: x+', '+f'{y[0]+"_" if y[0] != "" else ""}rst{y[1]}'), self.clk_domain_lst , '')[2:]
        ccnt_lst = reduce( (lambda x,y: x+', '+f'{y[0]+"_" if y[0] != "" else ""}clk_cnt'),   self.clk_domain_lst, '') [2:]
        s = f'{ind.b}logic {ck_lst};\n'
        s += f'{ind.b}logic {rst_lst};\n'
        s += f'{ind.b}int {ccnt_lst};\n'
        for ck in self.clk_domain_lst:
            _aff = ck[0]+"_" if ck[0] != "" else ""
            s += f'{ind.b}`Pos({_aff}rst_out, {_aff}rst{ck[1]})\n' 
            s += f'{ind.b}`PosIf({_aff}ck_ev , {_aff}clk, {_aff}rst{ck[1]})\n' 
        ev_lst = reduce( (lambda x,y: x+', '+str(y[1])), self.eventlst + [("","")], '')[2:-2]
        s += f'{ind.b}logic {ev_lst}; //TODO modify event condition\n'
            
        w = self.FindFormatWidth([ i[0]+', '+i[1]+',' for i in self.eventlst])
        for ev in self.eventlst:
            s += f'{ind.b}`PosIf({ev[0]+", "+ev[1]+",":<{w}} {self.rststr}_n)//TODO modify reset logic\n' 

        s += f'{ind.b}`WithFinish\n\n' 
        for i,ck in enumerate(self.clk_domain_lst):
            _aff = ck[0]+"_" if ck[0] != "" else ""
            s += f'{ind.b}always #`{self.hclkmacro} {_aff}clk= ~{_aff}clk;\n'
            _cmt = '//' if i==0 else ''
            s += f'{ind.b}{_cmt}always #(2*`{self.hclkmacro}) {_aff}clk_cnt = {_aff}clk_cnt+1;\n'
        s += self.AnsiColorVarStr(ind=ind)
        s += f'{ind.b}initial begin\n'
        _s =  f'{ind[1]}$fsdbDumpfile({{"{self.fsdbname}_", getenv("TEST_CFG"), ".fsdb"}});\n' 
        _s +=  f'{ind[1]}$fsdbDumpvars(0,{GBV.TEST},"+all");\n'

        for pyev in self.pyeventlgclst:
            _s += f'{ind[1]}{pyev} = 0;\n'
        for ck in self.clk_domain_lst:
            _aff = ck[0]+"_" if ck[0] != "" else ""
            _s +=  f'{ind[1]}{_aff}clk = 0;\n' 
            _s +=  f'{ind[1]}{_aff}rst{ck[1]} = {1 if ck[1] =="_n" else 0};\n'
        _s += f'{ind[1]}#1 `NicotbInit\n' 
        _s += f'{ind[1]}#10\n'
        for ck in self.clk_domain_lst:
            _aff = ck[0]+"_" if ck[0] != "" else ""
            rst = _aff+'rst'+ck[1]
            _s += f'{ind[1]}{rst} = {0 if ck[1] == "_n" else 1};\n' 
        _s += f'{ind[1]}#10\n'
        for ck in self.clk_domain_lst:
            _aff = ck[0]+"_" if ck[0] != "" else ""
            rst = _aff+'rst'+ck[1]
            _s += f'{ind[1]}{rst} = {1 if ck[1] == "_n" else 0};\n'
            _s += f'{ind[1]}{_aff}clk_cnt = 0;\n'
        _s += '\n'
        _ck = self.clk_domain_lst[0][0]
        _aff = _ck+"_" if _ck != "" else ""
        _s += f'{ind[1]}while ({_aff}clk_cnt < `{self.endcyclemacro} && sim_stop == 0 && time_out ==0) begin\n'
        _s += f'{ind[2]}@ (posedge {_aff}clk)\n'
        _s += f'{ind[2]}{_aff}clk_cnt <= {_aff}clk_cnt + 1;\n'
        _s += f'{ind[1]}end\n'
        #_s += f'#(2*`{self.hclkmacro+"*`"+self.endcyclemacro}) $display("timeout");\n' #TODO
        _s += '\n'
        _s += self.SimFinStr(ind=ind+1)
        _s += f'{ind[1]}`NicotbFinal\n'
        _s += f'{ind[1]}$finish;\n'
        _s += f'{ind.b}end\n\n'
        return s+_s

    @SVgen.Str
    def AnsiColorVarStr(self, ind=None):
        s  = f'\n{ind.b}string ansi_blue   = "\\033[34m";\n'
        s += f'{ind.b}string ansi_cyan   = "\\033[36m";\n'
        s += f'{ind.b}string ansi_green  = "\\033[32m";\n'
        s += f'{ind.b}string ansi_yellow = "\\033[33m";\n'
        s += f'{ind.b}string ansi_red    = "\\033[31m";\n'
        s += f'{ind.b}string ansi_reset  = "\\033[0m";\n'
        return s

    @SVgen.Str
    def SimFinStr (self, ind=None):
        _ck = self.clk_domain_lst[0][0]
        _aff = _ck+"_" if _ck != "" else ""
        s =  f'{ind.b}$display({{ansi_blue,"{"":=<42}", ansi_reset}});\n'
        s += f'{ind.b}$display({{"[Info] Test case:", ansi_yellow, getenv("TEST_CFG"), ansi_reset}});\n'
        s += f'{ind.b}if ({_aff}clk_cnt >= `{self.endcyclemacro}|| time_out)\n'
        s += f'{ind[1]}$display({{"[Error]", ansi_yellow, " Simulation Timeout.", ansi_reset}});\n'
        s += f'{ind.b}else if (sim_pass)\n'
        s += f'{ind[1]}$display({{"[Info]", ansi_green, " Congrat! Simulation Passed.", ansi_reset}});\n'
        s += f'{ind.b}else\n'
        s += f'{ind[1]}$display({{"[Error]", ansi_red, " Simulation Failed.", ansi_reset}});\n'
        s +=  f'{ind.b}$display({{ansi_blue,"{"":=<42}", ansi_reset}});\n\n'
        return s

    def DeclareBlkBlk(self ):
        pass

    def TopBlkBlk(self , tpname ):
        ind = self.cur_ind.Copy()
        yield ''
        yield 

    def LogicBlk(self , module , **conf):
        ind = self.cur_ind.Copy()
        yield ''
        s = self.CommentBlkStr ( 'Logics' , ind)
        pfield = SVhier.portfield 
        for p in module.ports:
            p = SVPort(p)
            if p.tp == 'logic' or p.tp == 'signed logic':
                s += f'{ind.b}{p.tp} {p.bwstr} {p.name}'
            else:
                s += f'{ind.b}{p.tp} {p.name}'
            if  not p.dimstr == '':
                s += f' {p.dimstr};\n'
            else:
                s += ';\n'
            
        yield s

    def ParamBlk(self , module , **conf):
        ind = self.cur_ind.Copy()
        yield ''
        s = self.CommentBlkStr(  'Parameters' , ind )
        for pkg,param  in module.scope.imported.items():
            for _p in param:
                s += f'{ind.b}import {pkg}::{_p};\n'
        for pkg,param  in module.imported.items():
            for _p in param:
                s += f'{ind.b}import {pkg}::{_p};\n'
        pmfield = SVhier.paramfield
        for param,v in module.paramports.items():
            detail = module.paramsdetail[param]
            tpstr = detail[pmfield.tp] + ' ' if detail[pmfield.tp] != '' else ''
            bwstr = detail[pmfield.bwstr] + ' ' if detail[pmfield.bwstr] != '' else ''
            pmtp  = detail[pmfield.paramtype]
            s += f'{ind.b}{pmtp} {tpstr}{bwstr}{param} = {detail[pmfield.numstr]};\n'
        yield s

    def CommentBlkBlk(self , s  ,width=35):
        ind = self.cur_ind.Copy()
        yield ''
        yield f'{ind.b}//{"":=<{width}}\n{ind.b}//{s:^{width}}\n{ind.b}//{"":=<{width}}\n'

    def CommentBlkStr(self, s , ind , width=35):
        return f'{ind.b}//{"":=<{width}}\n{ind.b}//{s:^{width}}\n{ind.b}//{"":=<{width}}\n'

    def InsBlk(self , module , name='dut' ,  **conf):
        ind = self.cur_ind.Copy() 
        yield ''
        s = '\n'
        s += ind.base + module.hier + ' #(\n'
        s_param = ''
        w = self.FindFormatWidth( [ (param+' ',) for param,v in module.paramports.items()])
        for param,v in module.paramports.items():
            if module.paramsdetail[param][SVhier.paramfield.paramtype] == 'parameter':
                s_param += f'{ind[1]},.{param:<{w[0]}}({param})\n'
        s_param = s_param.replace(f'{ind[1]},' , ind[1]+' ', 1)
        sb = f'{ind.b}) {name} (\n'
        s_port =''
        w = self.FindFormatWidth( [ (n+' ',) for io, n , *_ in module.ports])
        for io , n , dim , *_ in module.ports:
            if 'clk' in n:
                s_port += ind[1] + ',.' + f'{n:<{w[0]}}' + f'({self.clkstr})\n'
            elif 'rst' in n:
                s_port += ind[1] + ',.' + f'{n:<{w[0]}}' + f'({self.rststr})\n'
            else:
                s_port += ind[1] + ',.' + f'{n:<{w[0]}}' + (  (f'({n})\n') if dim ==() else (f'({{ >>{{{n}}} }})\n'))
                
        s_port = s_port.replace(f'{ind[1]},' , ind[1]+' ' , 1)
        s += s_param + sb + s_port + ind.base + ');\n' 
        yield s

    def TbPYBlk(self):
        ind = self.cur_ind.Copy()
        yield ''
        s = '\n'
        s += f'{ind.b}from nicotb import *\n'
        s += f'{ind.b}import numpy as np \n'
        yield s
        s = ''
        for ck in self.clk_domain_lst:
            _aff = ck[0]+"_" if ck[0] != "" else ""
            s +=  f'{ind.b}{_aff}rst_out, {_aff}ck_ev = CreateEvents(["{_aff}rst_out", "{_aff}ck_ev"])\n'
        self.print(self.eventlst, verbose=3)
        ev_lst = reduce( lambda x,y: x+', '+y[0], self.eventlst + [("","")], '')[2:-2]
        self.print(ev_lst, verbose=3)
        ev_lst_str = reduce( (lambda x,y: x + f'{ind[1]},"{str(y[0])}"\n')
            ,self.eventlst
            ,'')[:-1]
        self.print(ev_lst_str, verbose=3)
        s += f'{ind.b}{ev_lst} = CreateEvents([\n{ev_lst_str}])\n\n'
        s += f'{ind.b}RegisterCoroutines([\n'
        s += f'{ind[1]}main()\n'
        s += f'{ind.b}])'
        yield s

    def NicoutilImportBlk(self):
        ind = self.cur_ind.Copy()
        yield ''
        s = '\n'
        s +='import sys\n'
        s +='import os\n'
        s +='from itertools import repeat\n'
        s +='from nicotb.primitives import JoinableFork\n'
        s +='from SVutil.SVparse import SVparse,EAdict\n'
        s +='from SVutil.sim.NicoUtil import *\n\n'
        s +='TEST_CFG= os.environ.get(\'TEST_CFG\',None)\n'
        s +='Nico = NicoUtil() \n'
        s = s.replace('\n',f'\n{ind.b}') 
        yield s

    def NicoutilImportBlkNonPackage(self):
        ''' deprecated '''
        ind = self.cur_ind.Copy()
        yield ''
        s = '\n'
        s +='import sys\n'
        s +='import os\n'
        s +='sys.path.append(os.environ.get(\'SVutil\'))\n'
        s +='sys.path.append(os.environ.get(\'PROJECT_PATH\')+\'/sim\')\n'
        s +='from itertools import repeat\n'
        s +='from nicotb.primitives import JoinableFork\n'
        s +='from SVparse import SVparse,EAdict\n'
        s +='from sim.NicoUtil import *\n\n'
        s +='TEST_CFG= os.environ.get(\'TEST_CFG\',None)\n'
        s +='Nico = NicoUtil() \n'
        s = s.replace('\n',f'\n{ind.b}') 
        yield s

    def PYbusinitBlk(self,module):
        ind = self.cur_ind.Copy()
        yield ''
        s = '\n'

        s += f'{ind.b}def BusInit():\n'
        #s += f'{ind[1]}SBC = StructBusCreator\n'
        s += f'{ind[1]}#Nico.SBC.TopTypes()\n'
        s += f'{ind[1]}#Nico.SBC.AllTypes()\n'
        s += f'{ind[1]}dic = {{}}\n'
        w = [0, 0]
        for p in module.ports:
            p = SVPort(p)
            w[0] = max(w[0], len(p.name))
            w[1] = max(w[1], len(p.tp))
        last_gp = None 
        for p in module.ports:
            p = SVPort(p)
            if p.group != [] and  p.group[0] != last_gp:
                last_gp = p.group[0]
                s += f'{ind[1]}#{" "+last_gp+" ":=^{20}}#\n'
            tp = p.tp
            _q = '\''
            dimf = f'Nico.DutPortDim(\'{p.name+_q:<{w[0]+1}})'
            dim = f'Nico.DutPortDim(\'{p.name+_q})'
            if tp == 'logic' or tp == 'signed logic':
                s += f'{ind[1]}dic[\''
                s += f'{p.name + _q+"] ":<{w[0]+3}}'
                s += f'= CreateBus(( (\'\', \'{p.name+_q:<{w[0]+2}}, {dimf},),  ))\n'
            else:
                s += f'{ind[1]}dic[\''
                s += f'{p.name + _q+"] ":<{w[0]+3}}'
                s +=  f'= Nico.SBC.Get(\'{p.tp+_q:<{w[1]+1}}, \'{p.name+_q}, dim={dim})\n'     

                #TODO macro....
        s += f'{ind[1]}return Busdict(dic) # access by name without quotes\n'
        yield s

    def PYmainBlk(self):
        ind = self.cur_ind.Copy()
        yield '' 
        s = '\n'

        s += f'{ind.b}def main():\n'
        s += f'{ind[1]}buses = BusInit()\n'
        s += f'{ind[1]}buses.SetToN()\n'
        s += f'{ind[1]}buses.Write() #don\'t use this afterward if you\'re not sure what you\'re doing\n'
        s += f'{ind[1]}yield rst_out\n'
        s += f'{ind[1]}#j = []\n' 
        s += f'{ind[1]}#for jj in j:\n'
        s += f'{ind[1]}#    yield from jj.Join()\n'
        s += f'{ind[1]}#[jj.Destroy() for jj in j]\n'
        s += f'{ind[1]}#FinishSim()\n' 
        yield s
 
    def ModuleTestSV(self , module=None , **conf):
        module = self.dut if not module else module
        ins = self.InsBlk(module)
        mod = self.ModBlk()
        pm = self.ParamBlk(module)
        lg = self.LogicBlk(module)

        defb = self.SVDefineBlk()
        ind = self.IndBlk()

        s = self.Genlist( [ (defb,) , (mod,) , [ind,pm] , [ind,lg] , [ind,ins] , mod]) 
        if (conf.get('copy')==True):
            ToClip(s)
        return s

    def ModuleTestPY(self , module=None , **conf):
        module = self.dut if not module else module
        tb = self.TbPYBlk()
        nicoutil = self.NicoutilImportBlk() 
        businit = self.PYbusinitBlk(module)
        main = self.PYmainBlk()
        s = self.Genlist( [(tb,nicoutil,businit,main), tb ] )
        if (conf.get('copy')==True):
            ToClip(s)
        return s

    @SVgen.UserMethod
    def ShowModuleTestPY(self, module=None , copy=True, **conf):
        module = self.dut if not module else module
        conf['copy'] = copy
        self.print(self.ModuleTestPY(module, **conf))

    @SVgen.UserMethod
    def WriteModuleTestALL(self, module=None , **conf):
        module = self.dut if not module else module
        conf['copy']=False
        overwrite = conf.get('overwrite')
        self.SVWrite(self.ModuleTestSV(module,**conf),overwrite=overwrite)
        self.PYWrite(self.ModuleTestPY(module,**conf),overwrite=overwrite) 

    @SVgen.UserMethod
    def ShowIns(self, module=None):
        module = self.dut if not module else module
        ins = self.InsBlk(module)
        s =  self.Genlist( [(ins,)]) 
        ToClip(s)
        self.print(s)

    @SVgen.UserMethod
    def ShowModPortLogic(self, module=None):
        module = self.dut if not module else module
        ins = self.LogicBlk(module)
        s =  self.Genlist( [(ins,)]) 
        ToClip(s)
        self.print(s)

    def SVWrite(self , text, **conf ):
        p = self.TbWrite(text,'sv', **conf) 
        self.print ( "SV testbench written to " , p )

    def PYWrite(self , text, **conf ):
        p = self.TbWrite(text,'py', **conf)
        self.print ( "PY testbench written to " , p )

    def TbWrite(self , text , suf, **conf): 
        overwrite = conf.get('overwrite')
        self.print('overwriting:',overwrite)
        fpath =  self.test
        return self.FileWrite(fpath,text,suf, overwrite)
if __name__ == '__main__':
    g = TestGen()



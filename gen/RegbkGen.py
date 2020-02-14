import os
import sys
sys.path.append(os.environ.get('SVutil'))
from SVparse import *
from gen.SrcGen import * 
from SVclass import *
import itertools
import numpy as np
class RegbkGen(SrcGen):
    r"""
    This class saves you effort on reptitive but non-trivial part of your source system verilog code,
    like register bank related logics.
    Common function arguments:
        pkg: the name of the register bank package used to create a SVRegbk object from
            corresponding SVhier object. Default: self.regbk
        ind: the base indentation using Ind(n) object. Default: self.cur_ind
    Function naming suffix conventions:
        Str(self, *arg, ind): return a str of a code block. ind is the text base indentation of type Ind.
        ToClip(self, *arg, ind): try copying text result to xclip and return the text as string.
    """
    def __init__(self, ind=Ind(0), session=None):
        super().__init__(session=session)
        self.V_(VERBOSE) 
        self.regbkhier = self.regbk
        self.regbk= SVRegbk(self.regbkhier) if self.regbkhier else None
        self.customlst += [ 'addr_name',
                            'write_name',
                            'wdata_name',
                            'rdata_name',
                            'ointr_name',
                            'addr_slice',
                            'write_cond',
                            'read_cond',
                            'cg_cond',
                            'wo_cg_cond',
                            'ro_cg_cond',
                            'omitlogiclst']
        self.addr_name = 'i_addr'
        self.write_name = 'i_write'
        self.wdata_name = 'i_wdata'
        self.rdata_name = 'rdata'
        self.ointr_name = 'o_intr'
        self.addr_slice = f'[{self.regbk.regaddrbw_name}-1:{(self.regbk.regbsizebw_name)}]'
        self.write_cond = 'write_valid'
        self.read_cond = 'read_valid'
        self.cg_cond = 'ce'
        self.wo_cg_cond = 'wo_ce'
        self.ro_cg_cond = 'ro_ce'
        self.omitlogiclst = ['VERSION']
        self.flag_logic_lst = [   self.write_cond,\
                                        self.read_cond,\
                                        self.cg_cond,\
                                        self.ro_cg_cond,\
                                        self.wo_cg_cond ]
        self.clr_affix = 'clr_'
    def Reload(self):
        self.session.Reload()
        self.regbkhier = self.session.hiers.get(self.regbkstr)
        self.regbk= SVRegbk(self.regbkhier) if self.regbkhier else None
    def ModBlk(self): 
        ind = self.cur_ind.Copy() 
        yield ''
        s = '\n'
        s += f'{ind.b}`include ' + f'"{self.regbkstr}Defines.sv" // Please manually modify the path\n\n' 
        s += f'{ind.b}import {self.regbkstr}::*;\n'
        s += f'{ind.b}module ' + self.regbkstr+ ' #(\n'
        s += f'{ind.b})(\n'
        s += f'{ind[1]} input {self.clk_name}\n'
        s += f'{ind[1]},input {self.rst_name}\n'
        s += f'{ind[1]}//TODO protocol\n'
        yield s
        w = len(self.regbk.regbw_name)+5+7+8
        s = f'{ind[1]}{",input":<{w}} {self.write_name}\n'
        s += f'{ind[1]}{",input ["+self.regbk.regaddrbw_name+"-1:0]":<{w}} {self.addr_name}\n'
        s += f'{ind[1]}{",input ["+self.regbk.regbw_name+"-1:0]":<{w}} {self.wdata_name}\n'
        s += f'{ind[1]}{",output logic ["+self.regbk.regbw_name+"-1:0]":<{w}} o_{self.rdata_name}\n'
        if self.regbk.raw_intr_stat:
            s += f'{ind[1]}{",output "+self.regbk.regintr_name:<{w}} {self.ointr_name}\n'
        s += f'{ind.b});\n'
        yield s
        s = '\n' + ind.b +'endmodule'
        yield s
    def LogicStr(self, w, reg, bw, tp, arr=None, comb=None, ind=None):
        ind = self.cur_ind.Copy() if not ind else ind
        dim = ''
        if arr and arr != '':
            dim = f' [{reg.upper()}{self.regbk.arr_num_suf}]'
        if comb:
            return self.CombLogicStr(w, reg, bw, tp, dim, ind=ind)
        else:
            return self.RegLogicStr(w, reg, bw, tp, dim, ind=ind)
    def RdataStr(self, reg, _slice, w, rw=None, comb=False, const=False, ind=None):
        #TODO slice dependent, now it only pad the MSB and it's usually the case
        ind = self.cur_ind.Copy() if not ind else ind
        if rw and rw=='WO':
            return ''
        pad = f'{self.regbk.regbw_name}-{reg}{self.regbk.bw_suf}'
        s =f'{ind.b}{reg:<{w[0]}}: {self.rdata_name}_w = '
        pad = '{{'+f'{pad}'+'{1\'b0}}'
        logic = f'{reg.lower()}' if comb else f'{reg.lower()}_r'
        logic = "" if const else logic
        s += f'{pad:<{w[1]}} ,{logic}}};{"//TODO" if const else ""}\n'
        return s 
    def RdataArrStr(self, reg, ifelse, w, rw=None, comb=False, const=False, ind=None):
        if rw and rw=='WO':
            return ''
        pad = f'{self.regbk.regbw_name}-{reg}{self.regbk.bw_suf}'
        s = f'{ind.b}{ifelse+" (":<9}{self.addr_name}{self.addr_slice} >= {reg} &&\n'
        s +=      f'{ind.b}{"":<9}{self.addr_name}{self.addr_slice} < {reg}+{reg}{self.regbk.arr_num_suf}) begin\n'
        s +=f'{ind[1]}{self.rdata_name}_w = '
        pad = '{{'+f'{pad}'+'{1\'b0}}'
        logic = f'{reg.lower()}' if comb else f'{reg.lower()}_r'
        logic = "" if const else logic
        s += f'{pad:<{w[1]}} ,{logic}[{self.addr_name}{self.addr_slice}-{reg}]}};{"//TODO" if const else ""}\n'
        s += f'{ind.b}end\n'
        return s 
    def WdataSeqStr(self, reg, _slice, rw=None, dim=None, ind=None):
        #TODO slice dependent, now it only pad the MSB and it's usually the case
        ind = self.cur_ind.Copy() if not ind else ind
        dim = '' if not dim else f'[{dim}]'
        rstedge = 'negedge' if self.rst_name[-2:] == '_n' else 'posedge'
        s = f'{ind.b}always_ff @(posedge {self.clk_name} or {rstedge} {self.rst_name}) begin\n'
        s += f'{ind[1]}if ({"!" if self.rst_name[-2:] == "_n" else ""}{self.rst_name}) '
        s += f'{reg.lower()}_r{dim} <= {reg}{self.regbk.default_suf};'
        s += '\n' if dim =='' else '//TODO do indexing if the default parameter is an array\n'
        #s += f'{ind[1]}end\n'
        if rw and rw == 'RO':
            s += f'{ind[1]}else if ({self.ro_cg_cond} && ({reg.lower()}_r{dim} != {reg.lower()}_w{dim})) '
        elif rw and rw == 'WO':
            s += f'{ind[1]}else if ({self.wo_cg_cond} && ({reg.lower()}_r{dim} != {reg.lower()}_w{dim})) '
        else:
            s += f'{ind[1]}//else if ({self.cg_cond} && {self.addr_name}{self.addr_slice} == {reg}) \n'
            s += f'{ind[1]}else if ({self.cg_cond} && ({reg.lower()}_r{dim} != {reg.lower()}_w{dim})) '
        s += f'{reg.lower()}_r{dim} <= {reg.lower()}_w{dim};\n'
        s += f'{ind.b}end\n'
        return s
    def WdataCombStr(self, reg, _slice, rw=None, dim=None, comb=None, ind=None):
        #TODO slice dependent, now it only pad the MSB and it's usually the case
        ind = self.cur_ind.Copy() if not ind else ind
        dim = '' if not dim else dim
        s = f'{ind.b}always_comb begin\n'
        if rw and rw == 'RO':
            if self.clr_affix.upper() in reg:
                s += f'{ind[1]}if ({self.read_cond} && {self.addr_name}{self.addr_slice} == {reg}) '
                s += f'{reg.lower()}_w = \'1;\n'
                s += f'{ind[1]}else {reg.lower()}_w = \'0;//TODO\n'
                s += f'{ind[1]}//TODO\n{ind.b}end\n'
            else:
                if comb:
                    s += f'{ind[1]}{reg.lower()} = ;//TODO\n'
                    s += f'{ind.b}end\n'
                else:
                    s += f'{ind[1]}{reg.lower()}_w = {reg.lower()}_r ;\n'
                    s += f'{ind[1]}//TODO\n{ind.b}end\n'
        else:
            s += f'{ind[1]}if ({self.write_cond} && {self.addr_name}{self.addr_slice} == {reg}) begin\n'
            if comb:
                s += f'{ind[2]}{reg.lower()} = {self.wdata_name}[{reg}{self.regbk.bw_suf}-1:0];\n'
            else:
                s += f'{ind[2]}{reg.lower()}_w = {self.wdata_name}[{reg}{self.regbk.bw_suf}-1:0];\n'
            s += f'{ind[1]}end \n'
            s += f'{ind[1]}else begin\n'
            if reg.upper() == self.regbk.regintr_name.upper():
                s += f'{ind[2]}\n'
                s += self.IntrCombToClip(self.regbk, toclip=False, ind=ind+2)
            else:
                if comb:
                    s += f'{ind[2]}{reg.lower()} = ;//TODO\n'
                else:
                    s += f'{ind[2]}{reg.lower()}_w = {reg.lower()}_r ;\n'
                    s += f'{ind[2]}//TODO\n'
            s += f'{ind[1]}end\n{ind.b}end\n'
        return s
    def WdataCombArrStr(self, reg, rw=None, dim=None, comb=None, ind=None):
        #TODO slice dependent, now it only pad the MSB and it's usually the case
        ind = self.cur_ind.Copy() if not ind else ind
        dim = '' if not dim else dim
        s = f'{ind.b}always_comb begin\n'
        if rw and rw == 'RO':
            if self.clr_affix.upper() in reg:
                s += f'{ind[1]}if ({self.read_cond} && (({self.addr_name}{self.addr_slice} - {reg}) == {dim})) '
                s += f'{reg.lower()}_w[{dim}] = \'1;\n'
                s += f'{ind[1]}else {reg.lower()}_w[{dim}] = \'0;//TODO\n'
                s += f'{ind[1]}//TODO\n{ind.b}end\n'
            else:
                if comb:
                    s += f'{ind[1]}{reg.lower()}[{dim}] = ;//TODO\n'
                    s += f'{ind.b}end\n'
                else:
                    s += f'{ind[1]}{reg.lower()}_w[{dim}] = {reg.lower()}_r[{dim}] ;\n'
                    s += f'{ind[1]}//TODO\n{ind.b}end\n'
        else:
            s += f'{ind[1]}if ({self.write_cond} && ({self.addr_name}{self.addr_slice} - {reg} == {dim})) begin\n'
            if comb:
                s += f'{ind[2]}{reg.lower()}[{dim}] = {self.wdata_name}[{reg}{self.regbk.bw_suf}-1:0];\n' #TODO
            else:
                s += f'{ind[2]}{reg.lower()}_w[{dim}] = {self.wdata_name}[{reg}{self.regbk.bw_suf}-1:0];\n' #TODO
            s += f'{ind[1]}end \n'
            s += f'{ind[1]}else begin\n'
            if reg.upper() == self.regbk.regintr_name.upper():
                s += f'{ind[2]}\n'
                s += self.IntrCombToClip(self.regbk, toclip=False, ind=ind+2)
            else:
                if comb:
                    s += f'{ind[2]}{reg.lower()}[{dim}] = ;//TODO\n'
                else:
                    s += f'{ind[2]}{reg.lower()}_w[{dim}] = {reg.lower()}_r[{dim}] ;\n'
                    s += f'{ind[2]}//TODO\n'
            s += f'{ind[1]}end\n{ind.b}end\n'
        return s
    def IntrCombStr(self, intr_logic, intr_field, ind=None):
        ind = self.cur_ind.Copy() if not ind else ind
        s = f'{ind.b}if ({self.clr_affix}{intr_logic}_r) {self.regbk.regintr_name}_w.{intr_logic} = \'0;\n'
        s += f'{ind.b}else begin\n'
        s += f'{ind[1]}{self.regbk.regintr_name}_w.{intr_logic} = {self.regbk.regintr_name}_r.{intr_logic};//TODO\n'
        s += f'{ind.b}end\n'
        return s
    def LogicToClip(self, pkg=None, toclip=True, ind=None):
        regbktemp = self.Swap(pkg)
        ind = self.cur_ind.Copy() if not ind else ind
        w = [0,0] 
        s = ''
        def gettpbw(reg):
            tp = self.regbk.GetType(reg.name.lower())
            bw = self.regbk.GetBWStr(reg.name)
            try:
                bw = int(bw)
            except:
                pass
            bw = reg.name + self.regbk.bw_suf if not bw == 1 else 1
            bw = 1 if tp else bw
            tp = reg.name.lower() if tp else 'logic'
            return bw,tp 
        s += f'{ind.b}// control register\n'
        for reg in self.regbk.addrs.enumls:
            bw,tp = gettpbw(reg)
            width, rw, arr, *_= self.regbk.GetAddrCmt(reg.name)
            bwstr = '' if bw ==1 else f'[{bw}-1:0] ' 
            w[0] = max(w[0], len(f'{tp+" "+bwstr}'))
            dim = '' if arr=='' else ' ['+reg.name+self.regbk.arr_num_suf+']'
            w[1] = max(w[1], len(reg.name+dim)+2)
        for reg in self.regbk.addrs.enumls:
            bw,tp = gettpbw(reg)
            width, rw, arr, omit, comb, *_= self.regbk.GetAddrCmt(reg.name)
            if reg.name in self.omitlogiclst or omit:
                pass
            else:
                s += self.LogicStr( w, reg.name.lower(), bw, tp, arr=arr, comb=comb, ind=ind)
        s += f'{ind.b}logic [{self.regbk.regbw_name}-1:0] {self.rdata_name}_w;\n'
        s += '\n'

        s += f'{ind.b}// interrupt clear\n'
        intr = self.regbk.raw_intr_stat
        if not self.regbk.raw_intr_stat:
            self.print("interrupt struct not specified")
        else:
            w[0] = 0
            for intr in self.regbk.raw_intr_stat:
                w[1] = max(w[1], len(self.clr_affix+intr.name)+2)
            for intr in self.regbk.raw_intr_stat:
                if not self.clr_affix.upper()+intr.name.upper() in self.regbk.regaddrsdict:
                    s += self.LogicStr( w, self.clr_affix+intr.name.lower(), 1, 'logic', ind=ind)
            s += '\n'

        s += f'{ind.b}// flags\n'
        for l in self.flag_logic_lst:
            s += f'{ind.b}logic {l};\n' 
        
        if toclip:
            ToClip(s)
        self.regbk = regbktemp
        return s
    def RdataToClip(self, pkg=None, toclip=True, ind=None):
        r"""
        Help building register bank read data part of combinational logics.
        Follow specific coding style in your register bank description package, the function generate
        logics based on the regaddr enum list.
        """
        regbktemp = self.Swap(pkg)
        ind = self.cur_ind.Copy() if not ind else ind
        w = [0,0]
        self.print ( f'read condition: {self.read_cond}')
        s = f'{ind.b}always_comb begin\n'
        s += f'{ind[1]}if () begin //TODO Disabled default read value\n'
        s += f'{ind[2]}{self.rdata_name}_w = ({self.read_cond} && {self.addr_name}{self.addr_slice} == CLR_DISABLED)? 1 : \'0;\n'
        s += f'{ind[1]}end\n'
        s += f'{ind[1]}else if ({self.read_cond}) begin\n'
        arr_reg = []
        nonarr_reg = []
        for i in self.regbk.addrs.enumls:
            w[0] = max(w[0], len(i.name))
            w[1] = max(w[1], len(self.regbk.regbw_name+i.name+self.regbk.bw_suf)+10)
            width, rw, arr, omit, comb, *_= self.regbk.GetAddrCmt(i.name)
            if arr != '':
                arr_reg.append((i, width, rw, arr, omit, comb))
            else:
                nonarr_reg.append((i, width, rw, arr, omit, comb))
        # array registers
        for i, (reg, width, rw, arr, omit, comb) in enumerate(arr_reg):
            reg = reg.name
            const = True if reg in self.omitlogiclst or omit else False 
            if i == 0:
                s += self.RdataArrStr( reg, 'unique if', w, rw, comb=comb, const=const, ind=ind+2)
            else:
                s += self.RdataArrStr( reg, 'else if', w, rw, comb=comb, const=const, ind=ind+2)

        # non-array registers
        case_ind = 2 if len(arr_reg)==0 else 3
        s += f'{ind[2]}else begin\n' if len(arr_reg)!= 0 else ''
        s += f'{ind[case_ind]}case ({self.addr_name}{self.addr_slice})\n'
        for reg, width, rw, arr, omit, comb in nonarr_reg:
            _slice = self.regbk.regslices.get(reg.name)
            reg = reg.name
            const = True if reg in self.omitlogiclst or omit else False 
            s += self.RdataStr( reg, _slice, w, rw, comb=comb, const=const, ind=ind+case_ind+1)
        s += f'{ind[case_ind+1]}default: {self.rdata_name}_w = \'0;\n'
        s += f'{ind[case_ind]}endcase\n'
        s += f'{ind[2]}end\n' if len(arr_reg)!= 0 else ''

        # default
        s += f'{ind[1]}end\n'
        s += f'{ind[1]}else {self.rdata_name}_w = o_{self.rdata_name};\n'
        s += f'{ind.b}end\n\n'
        s1 = f'{ind[2]}o_{self.rdata_name} <= \'0;\n' #TODO 
        s2 = f'{ind[2]}o_{self.rdata_name} <= {self.rdata_name}_w;\n' #TODO 
        s += self.SeqCeStr(s1, s2, ce=self.read_cond, ind=ind)
        if toclip:
            ToClip(s)
        self.regbk = regbktemp
        return s
    def WdataToClip(self, pkg=None, toclip=True, ind=None):
        r"""
        Help building register bank write data part of both combinational and sequential part logics.
        Follow specific coding style in your register bank description package, the function generate
        logics based on the regaddr enum list.
        """
        regbktemp = self.Swap(pkg)
        ind = self.cur_ind.Copy() if not ind else ind
        s = ''
        w = 30
        self.print ( f'write condition: {self.write_cond}')
        self.print ( f'clock gating condition: {self.cg_cond}')
        gen = 'arrgen'
        s += f'{ind.b}//{"Array GenVar":=^{w}}\n'
        s += f'{ind.b}genvar {gen};\n\n'
        for reg in self.regbk.addrs.enumls:
            width, rw, arr, omit, comb, *_= self.regbk.GetAddrCmt(reg.name)
            if reg.name in self.omitlogiclst or omit:
                continue
            _slice = self.regbk.regslices.get(reg.name)
            _s = "reg " if not arr else "reg array "
            s += f'{ind.b}//{_s+reg.name:=^{w}}\n'
            if reg.name == 'DISABLE':
                s += f'{ind.b}//TODO Be careful of DISABLE clock enable condition\n'
            if arr != '':
                dim = f'{gen}'
                s += f'{ind.b}generate\n'
                s += f'{ind[1]}for ({gen} = 0; {gen} < {reg.name}{self.regbk.arr_num_suf}; ++{gen}) begin: arr_{reg.name.lower()}\n'
                s += self.WdataCombArrStr( reg.name, rw, dim=dim, comb=comb, ind=ind+2)
                if not comb:
                    s += self.WdataSeqStr( reg.name, _slice, rw, dim, ind=ind+2)
                s += f'{ind[1]}end\n'
                s += f'{ind.b}endgenerate\n\n'
            else:
                s += self.WdataCombStr( reg.name, _slice, rw, comb=comb, ind=ind)
                if not comb:
                    s += self.WdataSeqStr( reg.name, _slice, rw, ind=ind) + '\n'
        if toclip:
            ToClip(s)
        self.regbk = regbktemp
        return s
    def IntrCombToClip(self, pkg=None, toclip=True, ind=None):
        r"""
        Help build clear register read part of interrupts combinational logics.
        """
        regbktemp = self.Swap(pkg)
        ind = self.cur_ind.Copy() if not ind else ind
        s = ''
        w = 30
        if not self.regbk.raw_intr_stat:
            self.print("interrupt struct not specified")
            return ""
        for intr, field in zip ( self.regbk.raw_intr_stat, self.regbk.regfields[self.regbk.regintr_name.upper()].enumls):
            s += self.IntrCombStr( intr.name, field.name, ind) + '\n'
        if toclip:
            ToClip(s)
        self.regbk = regbktemp
        return s 
    def SeqToClip(self, pkg=None, toclip=True, ind=None):
        r"""
        Build basic sequential part including state_main, clr_interrupts not in the control reg list...etc.
        """
        regbktemp = self.Swap(pkg)
        ind = self.cur_ind.Copy() if not ind else ind
        s = ''
        s1 = ''
        s2 = ''
        w = 0
        clr = self.clr_affix
        if not self.regbk.raw_intr_stat:
            self.print("interrupt struct not specified")
        else:
            for intr in self.regbk.raw_intr_stat:
                w = max(w, len(clr+intr.name)+2)
            for intr in self.regbk.raw_intr_stat:
                if not clr.upper()+intr.name.upper() in self.regbk.regaddrsdict:
                    s1 += f'{ind[2]}{clr+intr.name+"_r":<{w}} <= \'0;\n' #TODO 
                    s2 += f'{ind[2]}{clr+intr.name+"_r":<{w}} <= {clr+intr.name}_w;\n' #TODO 
            s += self.SeqCeStr(s1,s2,ind=ind)
        if toclip:
            ToClip(s)
        self.regbk = regbktemp
        return s 

    def ToFile(self, pkg=None, ind=None, overwrite=False):
        regbktemp = self.Swap(pkg)
        ind = self.cur_ind if not ind else ind
        Ind   = self.IndBlk()
        mod   = self.ModBlk()
        banw = 25
        logicban = self.Line3BannerBlk( banw, '//', 'Logic') 
        logic = self.Str2Blk(self.LogicToClip, pkg, False)
        seqban = self.Line3BannerBlk( banw, '//', 'Sequential') 
        seq = self.Str2Blk(self.SeqToClip, pkg, False)
        regbkban = self.Line3BannerBlk( banw, '//', 'Reg bank') 
        rdata = self.Str2Blk(self.RdataToClip, pkg, False)
        wdata = self.Str2Blk(self.WdataToClip, pkg, False)
        s = self.Genlist ( [(mod,), mod, [Ind,logicban], [Ind,logic], [Ind,seqban], [Ind,seq], [Ind,regbkban], [Ind,rdata], [Ind,wdata],  mod] )
        ToClip(s)
        p = self.FileWrite( self.regbkstr, s, 'sv', overwrite=overwrite)
        self.print ('Regbk file write to', p) 
        self.regbk = regbktemp
    def Swap(self, pkg=None):
        regbktemp = self.regbk
        regbk = SVRegbk(pkg) if pkg and type(pkg)==str else self.regbk
        self.regbk = regbk
        return regbktemp
if __name__ == '__main__':
    g = RegbkGen()

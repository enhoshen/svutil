
import os
import sys
sys.path.append(os.environ.get('SVutil'))
from gen.XLGen import *
import xlsxwriter as xl

class MemmapGen(XLGen):
    def __init__(self, session=None):
        super().__init__(session=session)
        self.customlst += [
             'filepath'
            ,'regfieldfmt'
            ,'titlefmt'
            ,'fieldfmt'
            ,'regdespfmt'
            ]
        self.userfunclst += []
        self.filepath = './memmap.xlsx'
        self.CreateWorkbook(self.filepath)
        self.cols = [
             'Reg Offset'
            ,'Register Name'
            ,'Accessibility'
            ,'Default'
            ,'Description'
            ]
        self.title_row = 1
        self.field_row = 2
        self.reg_row = 3
        self.col_start = 1
        self.regfield_lvl = 2
        self.DftFmt()
        self.DftColWid()
    def DftFmt(self):
        self.regfieldfmt = self.wb.add_format({
             'font_name': 'Arial'
            ,'bg_color': '#E7E6E6'
            ,'text_wrap': True
            })
        self.regfieldfmt_c = self.wb.add_format({
             'font_name': 'Arial'
            ,'bg_color': '#E7E6E6'
            ,'text_wrap': True
            ,'align': 'center'
            })
        self.regfmt = self.wb.add_format({
             'font_name': 'Arial'
            ,'text_wrap': True
            })
        self.regfmt_c = self.wb.add_format({
             'font_name': 'Arial'
            ,'text_wrap': True
            ,'align': 'center'
            })
        self.titlefmt = self.wb.add_format({
             'font_name': 'Arial'
            ,'bold': True
            ,'bg_color': '#000000'
            ,'font_color': '#FFFFFF'
            ,'align': 'center'
            })
        self.fieldfmt = self.wb.add_format({
             'font_name': 'Arial'
            ,'bold': True
            ,'bg_color': '#27708B'
            ,'font_color': '#FFFFFF'
            ,'text_wrap': True
            ,'align': 'center'
            })
        self.regdespfmt = self.wb.add_format({
             'font_name': 'Arial'
            ,'bold': True
            ,'text_wrap': True
            })
        self.regfielddespfmt_it = self.wb.add_format({
             'font_name': 'Arial'
            ,'italic': True
            ,'bg_color': '#E7E6E6'
            ,'text_wrap': True
            })
        self.regfielddespfmt = self.wb.add_format({
             'font_name': 'Arial'
            ,'bg_color': '#E7E6E6'
            ,'text_wrap': True
            })
        self.regfmt_lst = [
             self.regfmt_c
            ,self.regfmt
            ,self.regfmt_c
            ,self.regfmt_c
            ,self.regdespfmt ]
        self.regfieldfmt_lst = [
             self.regfieldfmt_c
            ,self.regfieldfmt
            ,self.regfieldfmt_c
            ,self.regfieldfmt_c
            ,self.regfielddespfmt ]
    def DftColWid(self):
        self.regofs_w = 12
        self.regname_w = 32
        self.access_w = 13
        self.default_w = 16
        self.desp_w = 72
        self.colwid_lst = [
             self.regofs_w
            ,self.regname_w
            ,self.access_w
            ,self.default_w
            ,self.desp_w]
        self.title_w = sum(self.colwid_lst)
    def SetCol(self):
        for i,v in enumerate(self.colwid_lst):
            col = self.col_start+i
            self.cur_sh.set_column(col, col, v)
    def AllRegbk(self):
        for i,v in self.session.package.items():
            if re.match(rf'\w*(?i)Regbk', i):
                regbk = SVRegbk(v)
                if regbk.addrs:
                    self.AddRegbk(regbk)
        self.wb.close()
    def AddRegbk(self, regbk):
        self.print(regbk.name)
        self.cur_sh = self.wb.add_worksheet(re.sub(rf'(?i)Regbk|(?i)Regbank', '', regbk.name))
        self.SetCol()
        self.AddTitle(regbk)
        self.AddField()
        self.cur_row = self.reg_row
        for v in regbk.regaddrs.enumls:
            self.AddReg(regbk, v, self.cur_row)
    def AddTitle(self, regbk):
        self.cur_sh.merge_range(
             self.title_row
            ,self.col_start
            ,self.title_row
            ,self.col_start+len(self.cols)-1
            ,regbk.name+'(Address Base:0x TODO)'
            ,self.titlefmt)
    def AddField(self):
        self.cur_sh.write_row(self.field_row, self.col_start, self.cols, self.fieldfmt)
    def AddReg(self, regbk, regenum, rowidx):
        _, rw, *_= regbk.GetCmt(regenum.cmt)
        dft = regbk.regdefaults.get(regenum.name.upper())
        dft = dft.num if dft else 'TODO'
        if type(dft) == list:
            dft = self.DftConvert(regbk, regenum.name, dft)
        data = [
             hex(regenum.num * regbk.regbsize)
            ,regenum.name
            ,rw
            ,dft
            ,'TODO']
        for i,d,f in zip(range(len(data)), data, self.regfmt_lst):
            self.cur_sh.write(rowidx, self.col_start+i, d, f)
        #self.SetGroup(self.cur_row, self.regfield_lvl) 
        self.cur_row += 1
        self.AddRegField(regbk, regenum.name)
    def AddRegField(self, regbk, name): #TODO set level, collapsed
        _, regrw, *_= regbk.GetCmt(regbk.regaddrsdict[name].cmt)
        slices = regbk.regslices.get(name.upper())
        field = regbk.regfields.get(name.upper())
        dft = regbk.regdefaults.get(name.upper())
        dft = dft.num if dft else 'TODO'
        # if dft is a list, it is in reverse or, where the last element
        # is the default value of the first field value
        if field:
            acc_dic = {}
            if type(dft) == int:
                dft = self.DftConvert(regbk, name, dft)
            for n,c in zip(field.names, field.cmts):
                _, rw, *_= regbk.GetCmt(c)
                acc_dic[n] = rw if rw != '' else regrw
                acc_dic[re.sub(rf'{name.upper()}_', '', n)] = rw if rw != '' else regrw
                acc_dic['RESERVED'] = 'RO'
            for i,s in enumerate(slices):
                if type(dft)==list and len(dft) > i:
                    fdft = dft[i] 
                else:
                    fdft = '0' if s[0] == 'RESERVED' else 'TODO'
                data = [
                     self.SliceToString(s[1])
                    ,s[0]
                    ,acc_dic[s[0]]
                    ,fdft
                    ,'Reserved' if s[0] == 'RESERVED' else 'TODO']
                self.RegfieldRow(data)
            return True
        else:
            if type(dft) == list:
                dft = self.DftConvert(regbk, name, dft)
            bw = regbk.regbws.get(name)
            try: 
                bw = bw.num
            except:
                bw = bw
            if bw is None:
                bw = regbk.regbw
            slce = f'[{bw-1}:0]'
            data = [slce ,name ,regrw , dft,'TODO']
            for ii,d,f in zip(range(len(data)), data, self.regfieldfmt_lst):
                self.cur_sh.write(self.cur_row, self.col_start+ii, d, f)
                self.SetGroup(self.cur_row, self.regfield_lvl) 
            self.cur_row += 1
            if bw != regbk.regbw:
                slce = f'[{regbk.regbw-1}:{bw}]'
                data = [slce ,name ,regrw , '0', 'Reserved']
                self.RegfieldRow(data)
            return True
    def RegfieldRow(self, data):
            for ii,d,f in zip(range(len(data)), data, self.regfieldfmt_lst):
                if d == 'Reserved':
                    f = self.regfielddespfmt_it
                self.cur_sh.write(self.cur_row, self.col_start+ii, d, f)
                self.SetGroup(self.cur_row, self.regfield_lvl) 
            self.cur_row += 1
             
    def DftConvert(self, regbk, regname, dft):
        if type(dft) == str:
            return dft
        if type(dft)==list:
            _, dft, _ = regbk.RegWrite(regname, dft)
            return dft
        if type(dft)==int:
            dft, _ = regbk.RegRead(regname, dft)
            return dft 
        return dft
    def SliceToString(self, slice_lst):
        s = ''
        for i in slice_lst:
            if i[0] != i[1]:
                s += f'[{i[1]}:{i[0]}]'
            else:
                s += f'[{i[0]}]'
        return s
    def SetGroup(self, row_idx, lvl):
        self.cur_sh.set_row(
             row_idx 
            ,None
            ,None
            ,{'level': lvl, 'hidden':True})


        
        


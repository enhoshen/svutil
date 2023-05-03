import os
import sys
import logging
import xlsxwriter as xl

from svutil.gen.XLGen import *


@SVgen.user_class
class MemmapGen(XLGen):
    def __init__(self, session=None):
        super().__init__(session=session)
        self.customlst += [
            "filepath",
            "regfieldfmt",
            "titlefmt",
            "fieldfmt",
            "regdespfmt",
        ]
        self.userfunclst += []
        self.filepath = "./memmap.xlsx"
        self.create_workbook(self.filepath)
        self.cols = [
            "Reg Offset",
            "Register Name",
            "Accessibility",
            "Default",
            "Description",
        ]
        self.title_row = 1
        self.field_row = 2
        self.reg_row = 3
        self.col_start = 1
        self.regfield_lvl = 2
        self.dft_fmt()
        self.dft_col_wid()
        self.logger = logging.getLogger(f'{__name__}.MemmapGen')

    def dft_fmt(self):
        self.regfieldfmt = self.wb.add_format(
            {"font_name": "Arial", "bg_color": "#E7E6E6", "text_wrap": True}
        )
        self.regfieldfmt_c = self.wb.add_format(
            {
                "font_name": "Arial",
                "bg_color": "#E7E6E6",
                "text_wrap": True,
                "align": "center",
            }
        )
        self.regfmt = self.wb.add_format({"font_name": "Arial", "text_wrap": True})
        self.regfmt_c = self.wb.add_format(
            {"font_name": "Arial", "text_wrap": True, "align": "center"}
        )
        self.titlefmt = self.wb.add_format(
            {
                "font_name": "Arial",
                "bold": True,
                "bg_color": "#000000",
                "font_color": "#FFFFFF",
                "align": "center",
            }
        )
        self.fieldfmt = self.wb.add_format(
            {
                "font_name": "Arial",
                "bold": True,
                "bg_color": "#27708B",
                "font_color": "#FFFFFF",
                "text_wrap": True,
                "align": "center",
            }
        )
        self.regdespfmt = self.wb.add_format(
            {"font_name": "Arial", "bold": True, "text_wrap": True}
        )
        self.regfielddespfmt_it = self.wb.add_format(
            {
                "font_name": "Arial",
                "italic": True,
                "bg_color": "#E7E6E6",
                "text_wrap": True,
            }
        )
        self.regfielddespfmt = self.wb.add_format(
            {"font_name": "Arial", "bg_color": "#E7E6E6", "text_wrap": True}
        )
        self.regfmt_lst = [
            self.regfmt_c,
            self.regfmt,
            self.regfmt_c,
            self.regfmt_c,
            self.regdespfmt,
        ]
        self.regfieldfmt_lst = [
            self.regfieldfmt_c,
            self.regfieldfmt,
            self.regfieldfmt_c,
            self.regfieldfmt_c,
            self.regfielddespfmt,
        ]

    def dft_col_wid(self):
        self.regofs_w = 12
        self.regname_w = 32
        self.access_w = 13
        self.default_w = 16
        self.desp_w = 72
        self.colwid_lst = [
            self.regofs_w,
            self.regname_w,
            self.access_w,
            self.default_w,
            self.desp_w,
        ]
        self.title_w = sum(self.colwid_lst)

    def set_col(self):
        for i, v in enumerate(self.colwid_lst):
            col = self.col_start + i
            self.cur_sh.set_column(col, col, v)

    def add_regbk(self, regbk):
        self.print(regbk.name)
        self.cur_sh = self.wb.add_worksheet(
            re.sub(rf"(?i)Regbk|(?i)Regbank", "", regbk.name)
        )
        self.set_col()
        self.add_title(regbk)
        self.add_field()
        self.cur_row = self.reg_row
        for v in regbk.regaddrs.enumls:
            self.add_reg(regbk, v, self.cur_row)

    def add_title(self, regbk):
        self.cur_sh.merge_range(
            self.title_row,
            self.col_start,
            self.title_row,
            self.col_start + len(self.cols) - 1,
            regbk.name + "(Address Base:0x TODO)",
            self.titlefmt,
        )

    def add_field(self):
        self.cur_sh.write_row(self.field_row, self.col_start, self.cols, self.fieldfmt)

    def add_reg(self, regbk, regenum, rowidx):
        _, rw, arr, *_ = regbk.get_cmt(regenum.cmt)
        dft = regbk.regdefaults.get(regenum.name.upper())
        dft = dft.num if dft else "TODO"
        if type(dft) == list:
            dft = self.dft_convert(regbk, regenum.name, dft)
        # array regsiter

        if arr: 
            dim_name = f"{regenum.name.upper()}{regbk.arr_num_suf}"
            dim = regbk.params.get(dim_name)
            dim = dim.num - 1 if dim else dim_name
            reg_name = f"{regenum.name}_{0}\n- {regenum.name}_{dim}" 
            self.logger.debug(f"Array register: {dim_name}, {dim}, {reg_name}")
        else:
            reg_name = regenum.name
        data = [hex(regenum.num * regbk.regbsize), reg_name, rw, dft, "TODO"]
        for i, d, f in zip(range(len(data)), data, self.regfmt_lst):
            self.cur_sh.write(rowidx, self.col_start + i, d, f)
        # self.set_group(self.cur_row, self.regfield_lvl)
        self.cur_row += 1
        self.add_reg_field(regbk, regenum.name)

    def add_reg_field(self, regbk, name):  # TODO set level, collapsed
        _, regrw, *_ = regbk.get_cmt(regbk.regaddrsdict[name].cmt)
        slices = regbk.regslices.get(name.upper())
        field = regbk.regfields.get(name.upper())
        dft = regbk.regdefaults.get(name.upper())
        dft = dft.num if dft else "TODO"
        # if dft is a list, it is in reverse or, where the last element
        # is the default value of the first field value
        if field:
            acc_dic = {}
            if type(dft) == int:
                dft = self.dft_convert(regbk, name, dft)
            for n, c in zip(field.names, field.cmts):
                _, rw, *_ = regbk.get_cmt(c)
                acc_dic[n] = rw if rw != "" else regrw
                acc_dic[re.sub(rf"{name.upper()}_", "", n)] = rw if rw != "" else regrw
                acc_dic["RESERVED"] = "RO"
            for i, s in enumerate(slices):
                if type(dft) == list and len(dft) > i:
                    fdft = dft[i]
                else:
                    fdft = "0" if s[0] == "RESERVED" else "TODO"
                data = [
                    self.slice_to_string(s[1]),
                    s[0],
                    acc_dic[s[0]],
                    fdft,
                    "Reserved" if s[0] == "RESERVED" else "TODO",
                ]
                self.regfield_row(data)
            return True
        else:
            if type(dft) == list:
                dft = self.dft_convert(regbk, name, dft)
            bw = regbk.regbws.get(name)
            try:
                bw = bw.num
            except:
                bw = bw
            if bw is None:
                bw = regbk.regbw
            slce = f"[{bw-1}:0]"
            data = [slce, name, regrw, dft, "TODO"]
            for ii, d, f in zip(range(len(data)), data, self.regfieldfmt_lst):
                self.cur_sh.write(self.cur_row, self.col_start + ii, d, f)
                self.set_group(self.cur_row, self.regfield_lvl)
            self.cur_row += 1
            if bw != regbk.regbw:
                slce = f"[{regbk.regbw-1}:{bw}]"
                data = [slce, "RESERVED", regrw, "0", "Reserved"]
                self.regfield_row(data)
            return True

    def regfield_row(self, data):
        for ii, d, f in zip(range(len(data)), data, self.regfieldfmt_lst):
            if d == "Reserved":
                f = self.regfielddespfmt_it
            self.cur_sh.write(self.cur_row, self.col_start + ii, d, f)
            self.set_group(self.cur_row, self.regfield_lvl)
        self.cur_row += 1

    def dft_convert(self, regbk, regname, dft):
        if type(dft) == str:
            return dft
        if type(dft) == list:
            _, dft, _ = regbk.reg_write(regname, dft)
            return dft
        if type(dft) == int:
            dft, _ = regbk.reg_read(regname, dft)
            return dft
        return dft

    def slice_to_string(self, slice_lst):
        s = ""
        for i in slice_lst:
            if i[0] != i[1]:
                s += f"[{i[1]}:{i[0]}]"
            else:
                s += f"[{i[0]}]"
        return s

    def set_group(self, row_idx, lvl):
        self.cur_sh.set_row(row_idx, None, None, {"level": lvl, "hidden": True})

    @SVgen.user_method
    def all_regbk(self):
        for i, v in self.session.package.items():
            if re.match(rf"\w*(?i)Regbk", i):
                regbk = SVRegbk(v)
                if regbk.addrs:
                    self.add_regbk(regbk)
        self.wb.close()

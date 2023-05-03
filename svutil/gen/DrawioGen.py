import os
import sys
from svutil.SVparse import *
from svutil.SVgen import *
from svutil.SVclass import *
import itertools
import numpy as np

# TODO use ElementTree to work with XML files
class Shape:
    def __init__(self, x=None, y=None, w=None, h=None):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def pos(self):
        return self.x, self.y

    def dim(self):
        return self.w, self.h

    def copy(self):
        return Shape(self.x, self.y, self.w, self.h)


class Style(SVutil):
    def __init__(self, s=None, **kwargs):
        self.__dict__["verbose"] = None
        self.__dict__["attr"] = {}
        self.str_to_style(s)
        for k, v in kwargs.items():
            self.attr[k] = v
        pass

    def str_to_style(self, s):
        if not s:
            return None
        split = s.split(";")
        for s in split:
            if s is not "":
                s = s.rstrip().lstrip().split("=")
                if len(s) == 1:
                    self.attr[s[0]] = ""
                else:
                    self.attr[s[0]] = s[1]
        return s

    def style_str(self, deft=None, tp=None, **kwargs):
        s = ""
        if deft is not None:
            s += deft
            self.str_to_style(deft)
        s += f"{tp}; " if tp else ""
        for k, v in kwargs.items():
            self.attr[k] = v
        return self.str

    @property
    def str(self):
        s = ""
        for k, v in self.attr.items():
            s += f"{k}={v};" if v is not "" else f"{k};"
        return s

    def __getattr__(self, n):
        return self.attr[n]

    def __setattr__(self, a, v):
        if v is None and a in self.attr:
            self.attr.pop(a)
        else:
            self.attr[a] = v

    def __add__(self, y):
        pass


class DrawioGen(SVgen):
    unique_id = 300
    IDlist = []

    def __init__(self, ind=Ind(0), session=None):
        super().__init__(session=session)
        self.customlst += [
            "textstyle1",
            "textstyle2",
            "textstyle2left",
            "textstyle_rec1",
            "textstyle_rec1left",
            "textstyle_red",
            "textstyle_redleft",
            "arrowstyle1",
            "arrowboldstyle1",
            "struct_lvl",
        ]
        self.userfunclst += []
        self.textstyle1 = "text; align=center; rounded=0; verticalAlign=middle; labelPosition=center; verticalLabelPosition=middle; ;verticalAlign=middle; align=right;"
        self.textstyle2 = "text;html=1;strokeColor=none;fillColor=none;align=right;verticalAlign=middle;whiteSpace=wrap;rounded=0;"
        self.textstyle2left = "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;"
        self.textstyle_rec1 = "text;html=1;strokeColor=none;fillColor=none;align=right;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontStyle=1;fontSize=15;"
        self.textstyle_rec1left = "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontStyle=1;fontSize=15;"
        self.textstyle_red = "text;html=1;strokeColor=none;fillColor=none;align=right;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontColor=#FF0505;"
        self.textstyle_redleft = "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontColor=#FF0505;"
        self.arrowstyle1 = "endArrow=block; html=1; endFill=1;fontSize=8;"
        self.arrowboldstyle1 = "endArrow=classic;html=1;shape=flexArrow;fillColor=#000000;endWidth=4.93;endSize=2.54;width=1.20;"
        self.arrow_width = 50
        self.arrow_height = 50
        self.text_width = 100
        self.text_height = 10
        self.curly_width = 30
        self.arr_text_dist = 10
        self.arrow_ofs = 20
        self.center_ofs = 300
        self.center_x = 300
        self.center_y = 50
        self.prev_y_ofs = 0
        self.rec_txt_width = 145
        self.rec_txt_ofs = Shape(25, 20, 145, 20)
        self.cur_ind = ind
        self.struct_lvl = 2

        self.gray = ["#F5F5F5", "#CCCCCC", "#808080"]
        self.lightblue = ["#DDF0F1", "#A9D6E7", "#89CCD3"]
        self.heavyblue = ["#3081B0", "#27708B", "#1A4A5E"]

    def config(self, *arg, **kwargs):
        pass

    def mx_geometry(self, shape, ind):
        return f'{ind.b}<mxGeometry x="{shape.x}" y="{shape.y}" width="{shape.w}" height="{shape.h}" as="geometry"/>\n'

    def mx_point(self, shape, to, ind):
        return f'{ind.b}<mxPoint x="{shape.x}" y="{shape.y}" as="{to}"/>\n'

    def mx_point_blk(self, shape, to="sourcePoint"):
        ind = self.cur_ind.copy()
        yield ""
        yield self.mx_point(shape, to, ind)

    def mx_page_blk(self):
        ind = self.cur_ind.copy()
        yield ""
        s = f'{ind.b}<mxGraphModel dx="794" dy="1636" grid="1" gridSize="10" guides="1" tooltips="1" connect="1"'
        s += ' arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="1" shadow="0">\n'
        yield s
        yield f"{ind.b}</mxGraphModel>\n"

    def root_blk(self):
        ind = self.cur_ind.copy()
        yield ""
        yield f'{ind.b}<root>\n{ind.b}<mxCell id="0"/>\n{ind.b}<mxCell id="1" parent="0"/>\n'
        yield f"{ind.b}</root>\n"

    def mx_geometry_blk(self, shape):
        ind = self.cur_ind.copy()
        yield ""
        s = f'{ind.b}<mxGeometry width="{shape.w}" height="{shape.h}" relative="1" as="geometry">\n'
        yield s
        yield f"{ind.b}</mxGeometry>\n"

    def mx_cell_blk(self, value, style, parent, edge=None):
        ind = self.cur_ind.copy()
        ID = f"SVgen-mxCell-{value}-{DrawioGen.unique_id}"
        DrawioGen.unique_id += 1
        yield ""
        s = f'{ind.b}<mxCell id="{ID}" value="{value}" style="{style}"'
        if edge:
            s += f' edge="{edge}"'
        s += f' parent="{parent}" vertex="1">\n'
        yield s
        yield f"{ind.b}</mxCell>\n"

    def classic_arrow_str(self, value, style, shape, face, parent, ind):
        _d = DrawioGen(ind, self.session)
        mcblk = _d.mx_cell_blk(value, style, parent, edge="1")
        mxGeoBlk = _d.mx_geometry_blk(shape)
        _x = (
            [shape.x, shape.x + shape.w]
            if face == "right"
            else [shape.x + shape.w, shape.x]
        )
        src = _d.mx_point_blk(Shape(_x[0], shape.y), "sourcePoint")
        trg = _d.mx_point_blk(Shape(_x[1], shape.y), "targetPoint")
        srctrg = _d.blk_group(src, trg)
        s = _d.genlist([[mcblk, mxGeoBlk, srctrg]])
        return s

    def cell_geo_str(self, value, shape, style, parent, ind):
        _d = DrawioGen(ind, self.session)
        mcblk = _d.mx_cell_blk(value, style, parent)
        mxGeo = _d.str_to_blk(_d.mx_geometry, shape)
        s = _d.genlist([[mcblk, mxGeo]])
        return s

    def text_str(self, value, shape, style=None, parent="1", ind=Ind(0)):
        style = self.textstyle2 if not style else style
        return self.cell_geo_str(value, shape, style, parent, ind)

    def group_str(self, shape, parent, ind):
        return self.cell_geo_str("", shape, "group;", parent, ind)

    def curly_str(self, shape, parent, flip, ind):
        flipstr = "flipH=0" if not flip else "flipH=1"
        return self.cell_geo_str(
            "",
            shape,
            f"shape=curlyBracket;whiteSpace=wrap;html=1;rounded=1;{flipstr};",
            parent,
            ind,
        )

    def rectangle_str(self, value, shape, parent, flip, ind):
        _p = f"SVgen-mxCell--{DrawioGen.unique_id}"
        s = self.group_str(shape, parent, ind)
        txt_sh = self.rec_txt_ofs.copy()
        txt_sh.x = (shape.w - self.rec_txt_width) / 2
        textstyle = self.textstyle_rec1left if not flip else self.textstyle_rec1
        _d = DrawioGen(ind + 1, self.session)
        mcblk = _d.mx_cell_blk("", "fillColor=none;rounded=0;", _p)
        mxGeo = _d.str_to_blk(_d.mx_geometry, Shape(0, 0, shape.w, shape.h))
        s += _d.genlist([[mcblk, mxGeo]])
        s += self.text_str(value, txt_sh, textstyle, _p, ind + 1)
        return s


if __name__ == "__main__":
    g = DrawioGen()

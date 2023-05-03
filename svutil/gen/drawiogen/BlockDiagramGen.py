import os
import sys
from svutil.SVparse import *
from svutil.gen.DrawioGen import *
from svutil.SVclass import *
import itertools
import numpy as np


@SVgen.user_class
class BlockDiagramGen(DrawioGen):
    def __init__(self, ind=Ind(0), session=None):
        super().__init__(ind=ind, session=session)
        self.customlst += [
            "hier_lvl",
            "block_width",
            "block_min_width",
            "block_ratio",
            "block_ygap",
        ]
        self.hier_lvl = 3
        self.top = self.incfile.split("/")[-1]
        self.top = self.session.hiers[self.top + "_sv"]
        self.block_width = 700
        self.block_min_width = 100
        self.block_ratio = 0.3
        self.block_ygap = 50

    def config(self, *arg, **kwargs):
        pass

    @SVgen.str
    def rectangle_str(self, value, shape, parent, color, ind=None):
        """
        Draw a rectangle with a text box
            value: text value
            shape: rectangle posistion and dimension
            parent: mkcell parent
            color: hex RGB string representation of color, prefix with #
                Ex: "#FFFFFF"
        """
        _p = f"SVgen-mxCell--{DrawioGen.unique_id}"
        s = self.group_str(shape, parent, ind)
        txt_sh = self.rec_txt_ofs.copy()
        txt_sh.x = (shape.w - self.rec_txt_width) / 2
        textstyle = Style(s=self.textstyle_rec1, fontSize=10)
        self.print(textstyle.attr)
        textstyle.fontStyle = None

        if color != self.gray[0]:
            textstyle.fontColor = "#FFFFFF"
        _d = DrawioGen(ind + 1, self.session)
        if "Regbk" in value or "Regbank" in value:
            color = self.heavyblue[0]
            textstyle.fontColor = "#FFFFFF"
        mcblk = _d.mx_cell_blk(
            "", f"html=1;fillColor={color};strokeColor=None;rounded=0;", _p
        )
        mxGeo = _d.str_to_blk(_d.mx_geometry, Shape(0, 0, shape.w, shape.h))
        s += _d.genlist([[mcblk, mxGeo]])
        s += self.text_str(value, txt_sh, textstyle.Str, _p, ind + 1)
        return s

    @SVgen.str
    def module_blocklist_str(self, module, shape, parent, lvl=1, ind=None):
        """
        Append sub-module strings until lvl reduces to 1.
        Modules of same hierarchical level are drawn in the same column.
        This function is called recursively.
            module: SVhier object that must be of FILE hier_type
            shape: position and dimension for the top module
            parent: parent mkcell for the module, must be string, the parent must exist.
            lvl: current hierarchical level
        """
        s = ""
        width = shape.w * self.block_ratio
        width = self.block_min_width if width <= self.block_min_width else width
        shape = Shape(shape.x + (shape.w * self.block_ratio), shape.y, width, width)
        for i, v in module.identifiers.items():
            s += self.rectangle_str(
                v.name, shape, parent, color=self.gray[3 - lvl], ind=ind
            )
            if lvl != 1:
                _shape = shape.copy()
                _shape.x += shape.w + shape.w * self.block_ratio
                self.print(lvl, i)
                _parent = f"SVgen-mxCell--{self.unique_id+1}"
                s += self.module_blocklist_str(
                    self.session.hiers[i + "_sv"], _shape, parent, lvl - 1, ind=ind + 1
                )
            shape.y += shape.h + self.block_ygap
        self.print(s)
        return s

    @SVgen.user_method
    @SVgen.clip
    def block_diagram_to_clip(self, module=None, toclip=True, ind=None):
        """
        Block diagram generation.
            module: FILE type SVhier, which are those end with _sv
        """
        module = self.top if module is None else module
        indblk = self.ind_blk()
        mxg = self.mx_page_blk()
        rt = self.root_blk()
        shape = Shape(self.center_x, self.center_y, self.block_width, self.block_width)
        mod = self.str_to_blk(
            self.module_blocklist_str, module, shape, "1", lvl=self.hier_lvl
        )
        return self.genlist([(mxg, rt), (1, mod), rt, mxg])

    # def to_clip ( self, module=None, flip=False):
    #    m = self.dut if not module else module
    #    to_clip(self.interface_diagram_gen(m,flip))
    # def to_clip_two_side ( self, module =None ):
    #    m = self.dut if not module else module
    #    indblk = self.ind_blk()
    #    mxg = self.mx_page_blk()
    #    rt  = self.root_blk()
    #    port = self.str_to_blk ( self.module_port_arrow_str, m, '1', False)
    #    modblk = self.str_to_blk( self.module_block_str , m, '1', False)
    #    s = self.genlist( [ (mxg,rt) , [indblk,port] , [indblk,modblk] ])
    #    self.center_y = self.prev_y_ofs + 10
    #    portflip = self.str_to_blk ( self.module_port_arrow_str, m, '1', True)
    #    modblkflip = self.str_to_blk( self.module_block_str , m, '1', True)
    #    s += self.genlist( [  [indblk,portflip], [indblk,modblkflip], rt, mxg] )
    #    to_clip(s)
    #    return s
    # def to_file_two_side(self, path, module=None):
    #    f = open( path, 'w')
    #    s = self.to_clip_two_side(module)
    #    f.write(s)
    # def to_file (self, path, module=None, flip=False):
    #    f = open( path, 'w')
    #    s = self.interface_diagram_gen(module,flip)
    #    to_clip(s)
    #    f.write(s)


if __name__ == "__main__":
    g = BlockDiagramGen()

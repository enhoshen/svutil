import os
import sys
sys.path.append(os.environ.get('SVutil'))
from SVparse import *
from gen.DrawioGen import * 
from SVclass import *
import itertools
import numpy as np

class BlockDiagramGen(DrawioGen):
    def __init__(self, ind= Ind(0), session =None):
        super().__init__(ind=ind, session = session)
        self.customlst += [ 
             'hier_lvl']
        self.hier_lvl = 3
        self.block_width = 700
        self.block_min_width = 100 
        self.block_ratio = 0.3
        self.block_ygap = 50
    def Config(self, *arg, **kwargs):
        pass
    @SVgen.Str
    def RectangleStr(self, value, shape, parent, color, ind=None):
        _p = f'SVgen-mxCell--{DrawioGen.unique_id}'
        s = self.GroupStr(shape, parent, ind)
        txt_sh = self.rec_txt_ofs.Copy() 
        txt_sh.x = (shape.w-self.rec_txt_width)/2 
        textstyle = self.textstyle_rec1 + 'fontsize=10;' 
        textstyle +=  'fontColor=#FFFFFF;' if color != self.gray[0] else textstyle
        _d = DrawioGen(ind+1,self.session)
        if 'Regbk' in value or 'Regbank' in value:
            color = self.heavyblue[0]
            textstyle += 'fontColor=#FFFFFF;'
        mcblk = _d.mxCellBlk( "", f'html=1;fillColor={color};strokeColor=None;rounded=0;', _p)
        mxGeo = _d.Str2Blk( _d.mxGeometry, Shape( 0, 0, shape.w, shape.h) )
        s += _d.Genlist( [ [mcblk, mxGeo ] ] )
        s += self.TextStr( value, txt_sh, textstyle, _p, ind+1) 
        return s
    @SVgen.Str
    def ModuleBlocklistStr(self, module, shape, parent, lvl=1, ind=None):
        s = ''
        width = shape.w * self.block_ratio
        width = self.block_min_width if width <= self.block_min_width else width
        shape = Shape(
             shape.x + (shape.w * self.block_ratio)
            ,shape.y
            ,width
            ,width)
        for i, v in module.identifiers.items():
            if lvl != 1:
                _shape = shape.Copy()
                _shape.x += shape.w + shape.w * self.block_ratio
                self.print(lvl,i)
                _parent =  f'SVgen-mxCell--{self.unique_id+1}'
                s += self.ModuleBlocklistStr(SVparse.hiers[i+'_sv'], _shape, parent, lvl-1, ind=ind+1)
            s += self.RectangleStr(v.name, shape, parent, color=self.gray[3-lvl],ind=ind)
            shape.y += shape.h + self.block_ygap
        self.print(s)
        return s
            
    @SVgen.Clip 
    def BlockDiagramToClip(self, module, toclip=True, ind=None):
        indblk = self.IndBlk()
        mxg = self.mxPageBlk()
        rt  = self.RootBlk()
        shape = Shape(self.center_x, self.center_y, self.block_width, self.block_width)
        mod = self.Str2Blk(self.ModuleBlocklistStr, module, shape, '1', lvl=self.hier_lvl)
        return self.Genlist( [ (mxg,rt) , (1, mod), rt, mxg] )
    #def ToClip ( self, module=None, flip=False):
    #    m = self.dut if not module else module
    #    ToClip(self.InterfaceDiagramGen(m,flip))
    #def ToClipTwoSide ( self, module =None ):
    #    m = self.dut if not module else module
    #    indblk = self.IndBlk()
    #    mxg = self.mxPageBlk()
    #    rt  = self.RootBlk()
    #    port = self.Str2Blk ( self.ModulePortArrowStr, m, '1', False)
    #    modblk = self.Str2Blk( self.ModuleBlockStr , m, '1', False)
    #    s = self.Genlist( [ (mxg,rt) , [indblk,port] , [indblk,modblk] ])
    #    self.center_y = self.prev_y_ofs + 10 
    #    portflip = self.Str2Blk ( self.ModulePortArrowStr, m, '1', True)
    #    modblkflip = self.Str2Blk( self.ModuleBlockStr , m, '1', True)
    #    s += self.Genlist( [  [indblk,portflip], [indblk,modblkflip], rt, mxg] )
    #    ToClip(s)
    #    return s
    #def ToFileTwoSide(self, path, module=None):
    #    f = open( path, 'w')
    #    s = self.ToClipTwoSide(module) 
    #    f.write(s)
    #def ToFile (self, path, module=None, flip=False):
    #    f = open( path, 'w')
    #    s = self.InterfaceDiagramGen(module,flip) 
    #    ToClip(s)
    #    f.write(s)
if __name__ == '__main__':
    g = DrawioGen()
            
            
        

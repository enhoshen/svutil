import os
import sys
from SVutil.SVparse import *
from SVutil.gen.DrawioGen import * 
from SVutil.SVclass import *
import itertools
import numpy as np

@SVgen.UserClass
class InterfaceDiagramGen(DrawioGen):
    def __init__(self, ind= Ind(0), session =None):
        super().__init__(ind=ind, session = session)
    def Config(self, *arg, **kwargs):
        pass
    def ModuleBlockStr(self, module, parent, flip, ind):
        # use after port arrow making use of self.port_ofs
        x = self.center_x if not flip else self.center_x-self.port_ofs/1.625
        shape = Shape( x , self.center_y, self.port_ofs/1.625, self.port_ofs)
        return self.RectangleStr( module.name, shape, parent, flip, ind)
    def PortArrowStr(self, module, port, parent, reged , flip, ind=None):
        ind = self.cur_ind if ind is None else ind 
        pfield = SVhier.portfield
        tpfield = SVhier.typefield
        s = ''
        x_ofs = None
        y_ofs = None
        portsparent = parent #TODO
        total_w = self.text_width + self.arr_text_dist + self.arrow_width
        total_h = self.text_height
        port = SVPort(port)
        tp = module.AllType.get(port.tp)  
        struct_flag = False
        if port.tp != 'logic' and port.tp!= 'logic signed' and len(tp) != 1: 
            memlist = self.MemlistAppend(module, tp, self.struct_lvl)
            struct_flag = True
            top_grp_id = DrawioGen.unique_id
            portsparent =  f'SVgen-mxCell--{top_grp_id}'
            curly_height = len(memlist)*self.arrow_ofs-self.arrow_ofs+self.text_height
            if flip == False:
                curly_sh   = Shape(self.text_width, 0, self.curly_width, curly_height) 
                curly_txt_sh = Shape(0, (curly_height-self.text_height)/2, self.text_width, self.text_height)
                x_ofs = self.text_width + self.curly_width 
                y_ofs = 0 
                top_grp_x = self.center_x-2*self.text_width-self.curly_width-self.arr_text_dist-self.arrow_width
                top_grp_y = self.port_ofs+self.center_y
                curly_txt_style = self.textstyle_red if reged else self.textstyle2
            else:
                curly_ofs  = self.text_width + self.arrow_width + self.arr_text_dist
                curly_sh   = Shape(curly_ofs, 0, self.curly_width, curly_height) 
                curly_txt_sh = Shape(curly_ofs+self.curly_width, (curly_height-self.text_height)/2, self.text_width, self.text_height)
                x_ofs = 0 
                y_ofs = 0 
                top_grp_x = self.center_x 
                top_grp_y = self.port_ofs+self.center_y
                curly_txt_style = self.textstyle_redleft if reged else self.textstyle2left 
            top_grp_sh = Shape(top_grp_x, top_grp_y, total_w+self.text_width+self.curly_width, len(tp)*self.arrow_ofs)
            s += self.GroupStr( top_grp_sh, parent, ind)
            s += self.CurlyStr( curly_sh, portsparent, flip, ind+1) 
            s += self.TextStr( port.name, curly_txt_sh, curly_txt_style, portsparent, ind+1)
        else:
            if flip == False:
                x_ofs = self.center_x-self.text_width-self.arr_text_dist-self.arrow_width
                y_ofs = self.port_ofs+self.center_y
            else:
                x_ofs = self.center_x
                y_ofs = self.port_ofs+self.center_y
            boldarrow = port.dim != () or port.bw != 1
            memlist = [ (port.name+port.dimstr, boldarrow) ] 
            top_grp_y = 0
            #memlist = [ port[pfield.name]+port[pfield.bwstr]+port[pfield.dimstr] ]
        for txt,boldarrow in memlist:
            grp_sh = Shape(x_ofs , y_ofs, total_w, total_h)
            if flip == False:
                txt_sh = Shape(0, 0, self.text_width, self.text_height) 
                arr_sh = Shape(self.text_width + self.arr_text_dist, self.text_height/2, self.arrow_width, self.arrow_height)
                face = 'right' if port.direction=='input' else 'left'
            else:
                arr_sh = Shape(0, self.text_height/2 , self.arrow_width, self.arrow_height) 
                txt_sh = Shape(self.arrow_width + self.arr_text_dist, 0, self.text_width, self.text_height)
                face = 'right' if port.direction=='output' else 'left'
            grp_id = DrawioGen.unique_id
            s += self.GroupStr( grp_sh, portsparent, ind+1) 
            _p = f'SVgen-mxCell--{grp_id}'
            
            txt_style = self.textstyle2
            if flip:
                txt_style += "align=left;"
            if reged:
                txt_style += "fontColor=#FF0505;"
            if '[' in txt:
                txt_style += "fontStyle=1;"
            s += self.TextStr(txt, txt_sh, txt_style, _p, ind+2)
            
            arrow_style = self.arrowboldstyle1 if boldarrow else self.arrowstyle1 
            s += self.ClassicArrowStr( "", arrow_style, arr_sh, face , _p, ind+3) 
            self.port_ofs += self.arrow_ofs
            y_ofs += self.arrow_ofs 
        self.prev_y_ofs = y_ofs + top_grp_y
        return s
    def MemlistAppend(self, module, struct, lvl=1):
        memlist = []
        for mem in struct:
            tp = SVType(mem) 
            sub_tp = module.AllType.get(tp.tp)
            if tp.tp != 'logic' and tp.tp!= 'logic signed' and len(sub_tp) != 1 and lvl != 1: 
                sub_memlist = [(tp.name+'.'+n,bold) for n,bold in self.MemlistAppend(module, sub_tp, lvl-1)]
            else:
                sub_memlist = [(tp.name, tp.dim != () or tp.bw !=1)]
            memlist += sub_memlist
        return memlist
    
    def ModulePortArrowStr ( self, module, parent, flip, ind=None):
        ind = self.cur_ind if ind is None else ind
        self.port_ofs = 0
        s = ''
        for p in module.ports:
            reged = True if SVPort(p).name in module.regs else False
            s += self.PortArrowStr(module, p, parent, reged, flip, ind=ind) 
        return s
    def InterfaceDiagramGen (self, module, flip):
        indblk = self.IndBlk()
        mxg = self.mxPageBlk()
        rt  = self.RootBlk()
        port = self.Str2Blk ( self.ModulePortArrowStr, module, '1', flip)
        modblk = self.Str2Blk( self.ModuleBlockStr , module, '1', flip)
        return self.Genlist( [ (mxg,rt) , [indblk,port] , [indblk,modblk], rt, mxg] )
        
    @SVgen.Str
    def ToClip ( self, module=None, flip=False):
        m = self.dut if not module else module
        ToClip(self.InterfaceDiagramGen(m,flip))
        
    @SVgen.Str
    def ToClipTwoSide ( self, module =None ):
        m = self.dut if not module else module
        indblk = self.IndBlk()
        mxg = self.mxPageBlk()
        rt  = self.RootBlk()
        port = self.Str2Blk ( self.ModulePortArrowStr, m, '1', False)
        modblk = self.Str2Blk( self.ModuleBlockStr , m, '1', False)
        s = self.Genlist( [ (mxg,rt) , [indblk,port] , [indblk,modblk] ])
        self.center_y = self.prev_y_ofs + 10 
        portflip = self.Str2Blk ( self.ModulePortArrowStr, m, '1', True)
        modblkflip = self.Str2Blk( self.ModuleBlockStr , m, '1', True)
        s += self.Genlist( [  [indblk,portflip], [indblk,modblkflip], rt, mxg] )
        ToClip(s)
        return s
        
    @SVgen.Str
    def ToFileTwoSide(self, path, module=None):
        f = open( path, 'w')
        s = self.ToClipTwoSide(module) 
        f.write(s)
        
    @SVgen.Str
    def ToFile (self, path, module=None, flip=False):
        f = open( path, 'w')
        s = self.InterfaceDiagramGen(module,flip) 
        ToClip(s)
        f.write(s)
if __name__ == '__main__':
    g = InterfaceDiagramGen()
            
            
        

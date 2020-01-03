import os
import sys
sys.path.append(os.environ.get('SVutil'))
from SVparse import *
from SVgen import * 
from SVclass import *
import itertools
import numpy as np
class Shape():
    def __init__(self, x=None, y=None, w=None, h=None):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
    def Pos(self):
        return self.x, self.y
    def Dim(self):
        return self.w, self.h
    def Copy(self):
        return Shape( self.x, self.y, self.w, self.h)
class DrawioGen(SVgen):
    unique_id = 300 
    IDlist = []
    textstyle1 = "text; align=center; rounded=0; verticalAlign=middle; labelPosition=center; verticalLabelPosition=middle; ;verticalAlign=middle; align=right"
    textstyle2 = "text;html=1;strokeColor=none;fillColor=none;align=right;verticalAlign=middle;whiteSpace=wrap;rounded=0;"
    textstyle2left = "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;"
    textstyle_rec1 = "text;html=1;strokeColor=none;fillColor=none;align=right;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontStyle=1;fontSize=15"
    textstyle_rec1left = "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontStyle=1;fontSize=15"
    textstyle_red = "text;html=1;strokeColor=none;fillColor=none;align=right;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontColor=#FF0505;" 
    textstyle_redleft = "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontColor=#FF0505;" 
    arrowstyle1 = "endArrow=block; endFill=1;fontSize=8; html=1;"
    arrowboldstyle1 = "endArrow=classic;shape=flexArrow;fillColor=#000000;endWidth=4.938516283050313;endSize=2.5476510067114093;width=1.2080536912751678; html=1;"
    def __init__(self, ind= Ind(0), session =None):
        super().__init__(session = session)
        self.arrow_width = 50 
        self.arrow_height = 50 
        self.text_width = 100 
        self.text_height= 10
        self.curly_width = 30 
        self.arr_text_dist = 10
        self.arrow_ofs = 20
        self.center_ofs = 300
        self.center_x = 300
        self.center_y = 50
        self.prev_y_ofs = 0
        self.rec_txt_width = 145
        self.rec_txt_ofs = Shape( 25, 20, 145, 20)
        self.cur_ind = ind
     
    def Config(self, *arg, **kwargs):
        pass
    def mxGeometry(self, shape, ind):
        return f'{ind.b}<mxGeometry x="{shape.x}" y="{shape.y}" width="{shape.w}" height="{shape.h}" as="geometry"/>\n'
    def mxPoint(self, shape, to, ind):
        return f'{ind.b}<mxPoint x="{shape.x}" y="{shape.y}" as="{to}"/>\n'
    def mxPointBlk(self, shape, to="sourcePoint" ):
        ind = self.cur_ind.Copy()
        yield ''
        yield self.mxPoint(shape, to, ind)
    def mxPageBlk(self):
        ind = self.cur_ind.Copy()
        yield ''
        s = f'{ind.b}<mxGraphModel dx="794" dy="1636" grid="1" gridSize="10" guides="1" tooltips="1" connect="1"'
        s += ' arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="1" shadow="0">\n'
        yield s
        yield f'{ind.b}</mxGraphModel>\n'
    def RootBlk(self):
        ind = self.cur_ind.Copy()
        yield '' 
        yield f'{ind.b}<root>\n{ind.b}<mxCell id="0"/>\n{ind.b}<mxCell id="1" parent="0"/>\n'
        yield f'{ind.b}</root>\n'
    def mxGeometryBlk(self , shape):
        ind = self.cur_ind.Copy()
        yield ''
        s = f'{ind.b}<mxGeometry width="{shape.w}" height="{shape.h}" relative="1" as="geometry">\n'
        yield s
        yield f'{ind.b}</mxGeometry>\n'
    def mxCellBlk(self , value, style, parent, edge=None):
        ind = self.cur_ind.Copy()
        ID = f'SVgen-mxCell-{value}-{DrawioGen.unique_id}'
        DrawioGen.unique_id += 1
        yield ''
        s = f'{ind.b}<mxCell id="{ID}" value="{value}" style="{style}"'
        if edge:
            s += f' edge="{edge}"'
        s += f' parent="{parent}" vertex="1">\n'
        yield s
        yield f'{ind.b}</mxCell>\n'  
    def Stylestr( self, tp=None, **kwargs):
        s = f'{tp}; ' if tp else ''
        for k,v in kwargs.items(): 
            s += f'{k}={v}; ' 
        return s
    def ClassicArrowStr(self, value, style, shape, face , parent, ind):
        _d = DrawioGen(ind,self.session)
        mcblk = _d.mxCellBlk( value, style, parent, edge='1')
        mxGeoBlk = _d.mxGeometryBlk( shape )
        _x = [ shape.x, shape.x+shape.w ] if face == 'right' else [ shape.x+shape.w, shape.x] 
        src = _d.mxPointBlk( Shape(_x[0], shape.y), "sourcePoint")
        trg = _d.mxPointBlk( Shape(_x[1], shape.y), "targetPoint")
        srctrg = _d.BlkGroup(src,trg)
        s = _d.Genlist( [ [mcblk, mxGeoBlk, srctrg] ] )
        return s 
    def CellGeoStr(self, value, shape, style, parent, ind):
        _d = DrawioGen(ind,self.session)
        mcblk = _d.mxCellBlk( value, style, parent)
        mxGeo = _d.Str2Blk( _d.mxGeometry, shape)
        s = _d.Genlist( [ [mcblk, mxGeo ] ] )
        return s
    def TextStr(self, value, shape, style=None, parent='1', ind=Ind(0) ):
        style = self.textstyle2 if not style else style
        return self.CellGeoStr( value, shape, style, parent, ind)
    def GroupStr(self, shape, parent, ind):
        return self.CellGeoStr( "", shape, "group;", parent, ind)
    def CurlyStr(self, shape, parent, flip, ind):
        flipstr= "flipH=0" if not flip else "flipH=1"
        return  self.CellGeoStr( "", shape, f"shape=curlyBracket;whiteSpace=wrap;html=1;rounded=1;{flipstr};", parent, ind)
    def RectangleStr(self, value, shape, parent, flip, ind):
        _p = f'SVgen-mxCell--{DrawioGen.unique_id}'
        s = self.GroupStr(shape, parent, ind)
        txt_sh = self.rec_txt_ofs.Copy() 
        txt_sh.x = (shape.w-self.rec_txt_width)/2 
        textstyle = self.textstyle_rec1left if not flip else self.textstyle_rec1
        s += self.TextStr( value, txt_sh, textstyle, _p, ind+1) 
        _d = DrawioGen(ind+1,self.session)
        mcblk = _d.mxCellBlk( "", "rounded=0;", _p)
        mxGeo = _d.Str2Blk( _d.mxGeometry, Shape( 0, 0, shape.w, shape.h) )
        s += _d.Genlist( [ [mcblk, mxGeo ] ] )
        return s
    def ModuleBlockStr(self, module, parent, flip, ind):
        # use after port arrow making use of self.port_ofs
        x = self.center_x if not flip else self.center_x-self.port_ofs/1.625
        shape = Shape( x , self.center_y, self.port_ofs/1.625, self.port_ofs)
        return self.RectangleStr( module.name, shape, parent, flip, ind)
    def PortArrowStr(self, module, port, parent, reged , flip, ind):
        pfield = SVhier.portfield
        tpfield = SVhier.typefield
        s = ''
        x_ofs = None
        y_ofs = None
        portsparent = parent #TODO
        total_w = self.text_width + self.arr_text_dist + self.arrow_width
        total_h = self.text_height
        tp = module.AllType.get(port[pfield.tp])  
        struct_flag = False
        if port[pfield.tp] != 'logic' and port[pfield.tp]!= 'logic signed' and len(tp) != 1: 
            struct_flag = True
            top_grp_id = DrawioGen.unique_id
            portsparent =  f'SVgen-mxCell--{top_grp_id}'
            curly_height = len(tp)*self.arrow_ofs-self.arrow_ofs+self.text_height
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
            s += self.TextStr( port[pfield.name], curly_txt_sh, curly_txt_style, portsparent, ind+1)
            memlist = [ (mem[tpfield.name],mem[tpfield.dim] != () or mem[tpfield.bw]!=1 ) for mem in tp ]
        else:
            if flip == False:
                x_ofs = self.center_x-self.text_width-self.arr_text_dist-self.arrow_width
                y_ofs = self.port_ofs+self.center_y
            else:
                x_ofs = self.center_x
                y_ofs = self.port_ofs+self.center_y
            boldarrow = port[pfield.dim] != () or port[pfield.bw] != 1
            memlist = [ (port[pfield.name]+port[pfield.dimstr], boldarrow) ] 
            top_grp_y = 0
            #memlist = [ port[pfield.name]+port[pfield.bwstr]+port[pfield.dimstr] ]
        for txt,boldarrow in memlist:
            grp_sh = Shape(x_ofs , y_ofs, total_w, total_h)
            if flip == False:
                txt_sh = Shape(0, 0, self.text_width, self.text_height) 
                arr_sh = Shape(self.text_width + self.arr_text_dist, self.text_height/2, self.arrow_width, self.arrow_height)
                face = 'right' if port[pfield.direction]=='input' else 'left'
            else:
                arr_sh = Shape(0, self.text_height/2 , self.arrow_width, self.arrow_height) 
                txt_sh = Shape(self.arrow_width + self.arr_text_dist, 0, self.text_width, self.text_height)
                face = 'right' if port[pfield.direction]=='output' else 'left'
            grp_id = DrawioGen.unique_id
            s += self.GroupStr( grp_sh, portsparent, ind+1) 
            _p = f'SVgen-mxCell--{grp_id}'
            if reged:
                txt_style = self.textstyle_red if not flip else self.textstyle_redleft
            else:
                txt_style = self.textstyle2 if not flip else self.textstyle2left
            s += self.TextStr(txt, txt_sh, txt_style, _p, ind+2)
            
            arrow_style = self.arrowboldstyle1 if boldarrow else self.arrowstyle1 
            s += self.ClassicArrowStr( "", arrow_style, arr_sh, face , _p, ind+3) 
            self.port_ofs += self.arrow_ofs
            y_ofs += self.arrow_ofs 
        self.prev_y_ofs = y_ofs + top_grp_y
        return s
    
    def ModulePortArrowStr ( self, module, parent, flip, ind):
        self.port_ofs = 0
        s = ''
        for p in module.ports:
            reged = True if SVPort(p).name in module.regs else False
            s += self.PortArrowStr(module, p, parent, reged, flip, ind) 
        return s
    def InterfaceDiagramGen (self, module, flip):
        indblk = self.IndBlk()
        mxg = self.mxPageBlk()
        rt  = self.RootBlk()
        port = self.Str2Blk ( self.ModulePortArrowStr, module, '1', flip)
        modblk = self.Str2Blk( self.ModuleBlockStr , module, '1', flip)
        return self.Genlist( [ (mxg,rt) , [indblk,port] , [indblk,modblk], rt, mxg] )
    def DutPortToClip ( self, module=None, flip=False):
        m = self.dut if not module else module
        ToClip(self.InterfaceDiagramGen(m,flip))
    def DutPortToClipTwoSide ( self, module =None ):
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
    def DutPortToFileTwoSide( path):
        f = open( path, 'w')
        s = self.DutPortToClipTwoSide() 
        f.write(s)
    def DutPortToFile ( self, path, flip=False):
        f = open( path, 'w')
        s = self.InterfaceDiagramGen(g.dut,flip) 
        ToClip(s)
        f.write(s)
if __name__ == '__main__':
    g = DrawioGen()
            
            
        

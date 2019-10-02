import os
import sys
sys.path.append(os.environ.get('SVutil')+'/sim')
from SVparse import *
from SVgen import * 
import itertools
import numpy as np
class Layout():
    def __init__(self, x=None, y=None, w=None, h=None):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
    def Pos():
        return self.x, self.y
    def Dim():
        return self.w, self.h
class DrawioGen(SVgen):
    unique_id = 300 
    IDlist = []
    textstyle1 = "text; align=center; rounded=0; verticalAlign=middle; labelPosition=center; verticalLabelPosition=middle; ;verticalAlign=middle; align=right"
    textstyle2 = "text;html=1;strokeColor=none;fillColor=none;align=right;verticalAlign=middle;whiteSpace=wrap;rounded=0;"
    arrowstyle1 = "endArrow=classic; ;fontSize=8;"
    arrowboldstyle1 = "endArrow=classic;;fontSize=8;strokeWidth=2;perimeterSpacing=0;"
    def __init__(self, ind= Ind(0)):
        super().__init__()
        self.arrow_width = 50 
        self.arrow_height = 50 
        self.text_width = 100 
        self.text_height= 10
        self.curly_width = 30 
        self.arr_text_dist = 10
        self.arrow_ofs = 20
        self.center_ofs = 300
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
        _d = DrawioGen(ind)
        mcblk = _d.mxCellBlk( value, style, parent, edge='1')
        mxGeoBlk = _d.mxGeometryBlk( shape )
        _x = [ shape.x, shape.x+shape.w ] if face == 'right' else [ shape.x+shape.w, shape.x] 
        src = _d.mxPointBlk( Layout(_x[0], shape.y), "sourcePoint")
        trg = _d.mxPointBlk( Layout(_x[1], shape.y), "targetPoint")
        srctrg = _d.BlkGroup(src,trg)
        s = _d.Genlist( [ [mcblk, mxGeoBlk, srctrg] ] )
        return s 
    def TextStr(self, value, shape, parent, ind):
        _d = DrawioGen(ind)
        style = self.textstyle2
        mcblk = _d.mxCellBlk( value, style, parent)
        mxGeo = _d.Str2Blk( _d.mxGeometry, shape)
        s = _d.Genlist( [ [mcblk, mxGeo ] ] )
        return s
    def GroupStr(self, shape, parent, ind):
        _d = DrawioGen(ind)
        mcblk = _d.mxCellBlk( "", "group", parent)
        mxGeo = _d.Str2Blk( _d.mxGeometry, shape)
        s = _d.Genlist( [ [mcblk, mxGeo ] ] )
        return s
    def CurlyStr(self, shape, parent, ind):
        _d = DrawioGen(ind)
        mcblk = _d.mxCellBlk( "", "shape=curlyBracket;whiteSpace=wrap;html=1;rounded=1;", parent)
        mxGeo = _d.Str2Blk( _d.mxGeometry, shape)
        s = _d.Genlist( [ [mcblk, mxGeo ] ] )
        return s
    def PortArrowStr(self, module, port, parent, ind):
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
            x_ofs = self.text_width + self.curly_width 
            y_ofs = 0 
            top_grp_id = DrawioGen.unique_id
            portsparent =  f'SVgen-mxCell--{top_grp_id}'
            top_grp_x = self.center_ofs-2*self.text_width-self.curly_width-self.arr_text_dist-self.arrow_width
            top_grp_y = self.port_ofs+self.center_ofs
            top_grp_sh = Layout(top_grp_x, top_grp_y, total_w+self.text_width+self.curly_width, len(tp)*self.arrow_ofs)
            curly_height = len(tp)*self.arrow_ofs-self.arrow_ofs+self.text_height
            curly_sh   = Layout(self.text_width, 0, self.curly_width, curly_height) 
            curly_txt_sh = Layout(0, (curly_height-self.text_height)/2, self.text_width, self.text_height)
            s += self.GroupStr( top_grp_sh, parent, ind)
            s += self.CurlyStr( curly_sh, portsparent, ind+1) 
            s += self.TextStr( port[pfield.name], curly_txt_sh, portsparent, ind+1)
            memlist = [ mem[tpfield.name] for mem in tp ]
        else:
            x_ofs = self.center_ofs-self.text_width-self.arr_text_dist-self.arrow_width
            y_ofs = self.port_ofs+self.center_ofs
            memlist = [ port[pfield.name]+port[pfield.dimstr] ] 
            #memlist = [ port[pfield.name]+port[pfield.bwstr]+port[pfield.dimstr] ]
        for txt in memlist:
            grp_sh = Layout(x_ofs , y_ofs, total_w, total_h)
            txt_sh = Layout(0, 0, self.text_width, self.text_height)
            arr_sh = Layout(self.text_width + self.arr_text_dist, self.text_height/2, self.arrow_width, self.arrow_height)
            grp_id = DrawioGen.unique_id
            s += self.GroupStr( grp_sh, portsparent, ind+1) 
            _p = f'SVgen-mxCell--{grp_id}'
            s += self.TextStr(txt, txt_sh, _p, ind+2)
            face = 'right' if port[pfield.direction]=='input' else 'left'
            arrow_style = self.arrowstyle1 if port[pfield.dim]==() and port[pfield.bw]==1 else self.arrowboldstyle1
            s += self.ClassicArrowStr( "", arrow_style, arr_sh, face , _p, ind+3) 
            self.port_ofs += self.arrow_ofs
            y_ofs += self.arrow_ofs
        return s
    
    def ModulePortArrow ( self, module, parent, ind):
        ofs = 0
        self.port_ofs = 0
        s = ''
        for p in module.ports:
            s += self.PortArrowStr(module, p, parent, ind) 
        return s
    def PortGen (self, module ):
        mxg = self.mxPageBlk()
        rt  = self.RootBlk()
        port = self.Str2Blk ( self.ModulePortArrow, module, '1')
        return self.Genlist( [ [mxg,rt,port] ] )
    def DutPortToFile ( self, path):
        f = open( path, 'w')
        f.write(self.PortGen(g.dut))
 
            
            
        

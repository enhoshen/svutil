import numpy as np
from math import ceil
class LayerConf():
    def __init__(self,*arg,**kwarg):
        # avoid invoking setattr at initialization, use self.__dict__['attr']
        self.__dict__['dic']={}
        self.__dict__['arglist']= [ 'H','W','R','S','E','F','U','C','M','B','Xb','Wb','Ab','Ob','Tm','Tw','Th','Tb','Pch','Pm','Au','ibuf_row']
        for i,v in enumerate(arg):
            self.dic[ self.arglist[i] ] = v 
        for i , v in kwarg.items(): 
            self.dic[i]=v
        self.Cnew=ceil(self.C*self.Ab/16)
        self.Ctile=ceil(self.Cnew/self.Pch)
        self.Spattile=ceil(self.E/self.Tw)*ceil(self.F/self.Th)
        self.Btile=ceil(self.B/self.Tb)
        self.Mtile=ceil(self.M/self.Tm)
        self.Thtile=ceil(self.Th/16)
        self.Tmtile=ceil(self.Tm/self.Pm/16)
        self.PEpass=self.Wb*self.Tb*self.Thtile*self.Tmtile
    def __getattr__(self,n):
        return self.dic[n] 
    def __setattr__(self,n,v):
        self.dic[n]=v
    def __repr__(self):
        s=""
        w=5
        for i in self.arglist:
            s+=f"{i:<{w}}"
        s+='\n'
        for i in self.arglist:
            v=self.dic.get(i)
            s+=f"{ '' if v==None else v:<{w}}" 
        return s
    def ToPEconf(self):
        upix = 12 if self.Pch*self.U >= 12 else self.Pch*self.U
        peconf=[self.Pch , self.Pm ,self.Au , self.Tb , self.U , self.R , self.S , self.Pch*self.R*self.Pm , self.Pch*self.R , self.Pm*self.Tw , upix , upix!=12 , self.Xb , self.Wb, 1,1,1 ,0, self.Tw]
        return peconf
class ModelConf():
    def __init__(self , layers=[]):
        self.layers=layers
        pass 
    def AddLayer(self, conf):
        self.layers.append(conf)
    def __getitem__(self,i):
        return self.layers[i]
    def __iadd__(self, conf):
        self.layers.append(conf)
    def __iter__(self):
        yield from self.layers 
AlexBest = ModelConf( [ LayerConf(227,227,11,11,55,55,4,3,64,4,2,1,4,4,64,14,14,4,1,2,3,4),
                        LayerConf(31,31,5,5,27,27,1,64,256,4,1,1,4,4,64,27,27,4,4,4,2,2),
                        LayerConf(15,15,3,3,13,13,1,256,256,4,1,1,4,4,64,13,13,4,4,4,3,1),
                        LayerConf(15,15,3,3,13,13,1,256,256,4,1,1,4,4,64,13,13,4,4,4,3,1),
                        LayerConf(15,15,3,3,13,13,1,256,256,4,1,1,4,4,64,13,13,4,4,4,3,1)] )
Vgg16 = ModelConf ( [   LayerConf(227,227,3,3,224,224,1,3,64,3,1,1,4,4,64,224,224,4,4,4,3,1) ]) 
                    
for i in AlexBest:
    print( i ) 
def Pack(repack,x,bit_ch,pch,ab):
    ch_pack = int(16/ab)
    for i in range(bit_ch):
        for j in range(pch):
            for k in range(ch_pack):
                temp = (x[...,j*ch_pack+k]/(2**(ab*i))).astype(np.uint16)
                temp = (temp % (2**ab)).astype(np.uint16)
                temp = (temp * (2**(ab*k))).astype(np.uint16)
                repack [i,...,j]+= temp
    #pack function repack the array with additional dimension bit_ch , spliting the rightmost diemension
    #which is the channel dimension
def Quantize(x,bw,th):
    bound = 2**(bw-1)
    Quant = np.rint(np.clip(x*bound/th,-bound,bound-1 )).astype(np.int16)
    uQuant = Quant.astype(np.uint16)
    return Quant , uQuant
def InputData(pch,tw,s,   xb,ab,th):
    data = np.random.randn(s,tw,int(pch*16/ab))
    Quant , uQuant = Quantize(data,ab*xb,th)
    np.set_printoptions(formatter={'int':hex})
    Repack= np.zeros( shape=(xb,s,tw,pch ),dtype=np.uint16 )
    Pack( Repack , uQuant , xb , pch ,ab)
    Repack= np.swapaxes(Repack,0,1)
    def it(bus):
        size =(s*xb*tw*pch)
        for i in range(size):
            bus.value = Repack.flat[i]
            yield bus.value
        print("input done")
    return data , Quant , Repack , it
def WeightData(pch,r,m,s,    wb,ab,th):
    def onefilter( pch,r,m,s,  wb,ab,th):
        data = np.random.randn(s,m,r,int(pch*16/ab) )
        Quant , uQuant = Quantize(data,ab*wb,th)
        np.set_printoptions(formatter={'int':hex})
        Repack= np.zeros( shape=(wb,s,m,r,pch ),dtype=np.uint16 )
        Pack( Repack , uQuant , wb , pch ,ab)
        Repack= np.swapaxes(Repack,0,1)
        return data , Quant , uQuant , Repack, Pack
    datas , Quants, uQuants, Repacks, Packs = zip ( * [onefilter(pch,r,m,s, wb,ab,th) for i in range(16)])
    def it(bus):
        size = (s*wb*m*r*pch)
        for i in range(size):
            for f in range(16):
                bus.value[f] = Repacks[f].flat[i]
            yield bus.values
        print("weight done")
    return datas , Quants , Repacks , it
def Conv1d( r , indata, wtdata):
    pad = indata
def PsumData(m,tw,ab,th,inputdata,weightdata):
    pass
def BufData(conf,allgb=0):
    Tw=conf.Tw
    Pch=conf.Pch
    Pm =conf.Pm
    Xb=conf.Xb
    R=conf.R
    S=conf.S
    U=conf.U 
    TW=(Tw*U)-U+R
    input_size = TW*Pch*Xb*S
    weight_size = R*S*Pch*Pm
    ibuf_write = Pch*TW*Xb 
    wbuf_write = R*Pch*Pm 
    ibuf_read = input_size 
    wbuf_read = weight_size 
    psum_write = Tw*Pm
    gb_write = input_size + weight_size + psum_write 
    gb_read = ibuf_write + wbuf_write + psum_write
    gb_all_read= ibuf_read + wbuf_read + psum_write 
    def ibuf_r(bus):
        for i in range (ibuf_read if allgb==0 else 1):
            bus.values = np.random.randint( np.iinfo(np.uint16).max ,size=1,dtype=np.uint16) 
            yield bus.values
    def ibuf_w(bus):
        for i in range (ibuf_write if allgb==0 else 1):
            bus.values = np.random.randint( np.iinfo(np.uint16).max ,size=1,dtype=np.uint16) 
            yield bus.values
    def wbuf_r(bus):
        for i in range (wbuf_read if allgb==0 else 1):
            bus.values = np.random.randint( np.iinfo(np.uint16).max ,size=1,dtype=np.uint16) 
            yield bus.values
    def wbuf_w(bus):
        for i in range (wbuf_write if allgb==0 else 1):
            bus.values = np.random.randint( np.iinfo(np.uint16).max ,size=1,dtype=np.uint16) 
            yield bus.values
    def gbuf_r(bus):
        for i in range (gb_read//4 if allgb==0 else gb_all_read//4):
            bus.values = np.random.randint( np.iinfo(np.uint32).max ,size=2,dtype=np.uint32) 
            yield bus.values
    def gbuf_w(bus):
        for i in range (gb_write//4):
            bus.values = np.random.randint( np.iinfo(np.uint32).max ,size=2,dtype=np.uint32) 
            yield bus.values
    return ibuf_r ,ibuf_w , wbuf_r , wbuf_w , gbuf_r ,gbuf_w
if __name__ == "__main__":
    pass
    #d,q,r,i=InputData(4,3,1,8,1.3)
    #print( d , q ,r ) 

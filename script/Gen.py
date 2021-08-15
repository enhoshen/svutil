#!/usr/bin/env python3 -i
if __name__ == "__main__":
    from svutil.SVparse import *
    import sys
    import svutil.SVutilCompleter
    session = SVparseSession(V_(VERBOSE))
    session.FileParse(paths=None)
    hiers = EAdict(session.hiers)

    from svutil.gen.tbgen import *
    try:
        gTestSv = TbSvGen(session=session)
        gTestPy = TbPyGen(session=session)
    except:
        SVutil().print('TestGen initialization failed') 

    from svutil.gen.SrcGen import *
    from svutil.gen.srcgen import *
    try:
        gRegbk = RegbkGen(session=session)
    except:
        SVutil().print('RegbkGen initialization failed') 
    try:
        gConnect= ConnectGen(session=session)
    except:
        SVutil().print('ConnectGen initialization failed') 

    from svutil.gen.drawiogen import * 
    try:
        gIFgen = InterfaceDiagramGen(session=session)
    except:
        SVutil().print('InterfaceGen initialization failed') 
    try:
        gBLgen = BlockDiagramGen(session=session)
    except:
        SVutil().print('BlockGen initialization failed') 

    from svutil.gen.LatexGen import LatexGen
    try:
        gLatex = LatexGen(session=session)
    except:
        SVutil().print('LatexGen initialization failed') 

    from svutil.gen.BannerGen import GanzinBanner
    gBanner = GanzinBanner()


    from svutil.gen.xlgen import * 
    try:
        gmemmapxl = MemmapGen(session=session)
    except:
        SVutil().print('MemmapGen initialization failed') 

#!/usr/bin/env python3 -i
if __name__ == "__main__":
    from SVutil.SVparse import *
    import sys
    import SVutil.SVutilCompleter
    session = SVparseSession(V_(VERBOSE))
    session.FileParse(paths=None)
    hiers = EAdict(session.hiers)

    from SVutil.gen.tbgen import *
    try:
        gTestSv = TbSvGen(session=session)
        gTestPy = TbPyGen(session=session)
    except:
        SVutil().print('TestGen initialization failed') 

    from SVutil.gen.SrcGen import *
    from SVutil.gen.srcgen import *
    try:
        gRegbk = RegbkGen(session=session)
    except:
        SVutil().print('RegbkGen initialization failed') 
    try:
        gConnect= ConnectGen(session=session)
    except:
        SVutil().print('ConnectGen initialization failed') 

    from SVutil.gen.drawiogen import * 
    try:
        gIFgen = InterfaceDiagramGen(session=session)
    except:
        SVutil().print('InterfaceGen initialization failed') 
    try:
        gBLgen = BlockDiagramGen(session=session)
    except:
        SVutil().print('BlockGen initialization failed') 

    from SVutil.gen.LatexGen import LatexGen
    try:
        gLatex = LatexGen(session=session)
    except:
        SVutil().print('LatexGen initialization failed') 

    from SVutil.gen.BannerGen import GanzinBanner
    gBanner = GanzinBanner()


    from SVutil.gen.xlgen import * 
    try:
        gmemmapxl = MemmapGen(session=session)
    except:
        SVutil().print('MemmapGen initialization failed') 

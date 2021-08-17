from svutil.SVparse import *
import sys
import SVutil.SVutilCompleter
from svutil.gen.SrcGen import *
from svutil.gen.TestGen import TestGen
from svutil.gen.srcgen.RegbkGen import RegbkGen
from svutil.gen.srcgen.ConnectGen import ConnectGen
from svutil.gen.drawiogen.InterfaceDiagramGen import InterfaceDiagramGen
from svutil.gen.drawiogen.BlockDiagramGen import BlockDiagramGen
from svutil.gen.LatexGen import LatexGen
from svutil.gen.BannerGen import GanzinBanner
from svutil.gen.xlgen.MemmapGen import MemmapGen

if __name__ == "__main__":
    session = SVparseSession(V_(VERBOSE))
    session.FileParse(paths=None)
    hiers = EAdict(session.hiers)
    try:
        gTest = TestGen(session=session)
    except:
        SVutil().print("TestGen initialization failed")
    try:
        gRegbk = RegbkGen(session=session)
    except:
        SVutil().print("RegbkGen initialization failed")
    try:
        gConnect = ConnectGen(session=session)
    except:
        SVutil().print("ConnectGen initialization failed")
    try:
        gIFgen = InterfaceDiagramGen(session=session)
    except:
        SVutil().print("InterfaceGen initialization failed")
    try:
        gBLgen = BlockDiagramGen(session=session)
    except:
        SVutil().print("BlockGen initialization failed")
    try:
        gLatex = LatexGen(session=session)
    except:
        SVutil().print("LatexGen initialization failed")
    gBanner = GanzinBanner()
    try:
        gmemmapxl = MemmapGen(session=session)
    except:
        SVutil().print("MemmapGen initialization failed")

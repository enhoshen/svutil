from SVparse import *
from SVclass import *
import os
import itertools
import numpy as np

class PYUtil(SVutil):
    def __init__(self):
        self.hier = hiers.dic.get(HIER)
        self.regbkstr= hiers.dic.get(REGBK)
        self.regbk= SVRegbk(self.regbkstr) if self.regbkstr else None
        self.endcycle = 10000

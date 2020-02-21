from SVparse import *
from SVclass import *
import os
import itertools
import numpy as np

class PYUtil(SVutil):
    def __init__(self):
        self.V_(VERBOSE)
        self.hier = self.session.hiers.get(HIER)
        self.regbkstr= self.session.hiers.get(REGBK)
        self.regbk= SVRegbk(self.regbkstr) if self.regbkstr else None
        self.endcycle = 10000

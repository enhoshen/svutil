
import os
import sys
import xlsxwriter as xl
from SVutil.SVgen import * 

class XLGen(SVgen):
    def __init__(self, session=None):
        super().__init__(session=session)
        self.V_(GBV.VERBOSE) 
        self.customlst += []
        self.userfunclst += []
    def CreateWorkbook(self, path):
        self.wb = xl.Workbook(path)
    def CreateSheet(self):
        pass

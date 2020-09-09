
import os
import sys
sys.path.append(os.environ.get('SVutil'))
import xlsxwriter as xl
from SVgen import * 

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

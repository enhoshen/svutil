import os
import sys
import xlsxwriter as xl
from svutil.SVgen import *


class XLGen(SVgen):
    def __init__(self, session=None):
        super().__init__(session=session)
        self.v_(GBV.VERBOSE)
        self.customlst += []
        self.userfunclst += []

    def create_workbook(self, path):
        self.wb = xl.Workbook(path)

    def create_sheet(self):
        pass

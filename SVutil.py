import os
import inspect
class SVutil():
    trace_format_width = 0
    def __init__(self, verbose=None):
        self.verbose = verbose
        pass
    def V_(self, verbose):
        try:
            self.verbose = int(verbose)
        except:
            self.verbose = verbose
    def Verbose(self, v):
        ''' set verbose level '''
        self.verbose = v if v else 0
    def print(self,*arg,verbose=None, trace=1, level=False,**kwarg):
        '''
            Customized message print controlled with verbose level for each messages seperately. 
                Args:
                    verbose: determine the verbose level of the message, if not given, messages
                        is printed nonetheless
                    level: print messages with lower verbose level than self.verbose if True
                        or else only the specific verbose level messages are printed
        '''
        ins = inspect.getframeinfo(inspect.currentframe().f_back)
        ins = self.Trace(ins, trace)
        if not verbose:
            print(ins,*arg,**kwarg)
        if level:
            if self.verbose >= verbose: 
                print(ins, *arg,**kwarg)
        else:
            if self.verbose == verbose:
                print(ins, *arg,**kwarg)
    def Trace(self, ins, trace):
        home = os.environ.get('HOME','')
        fn = ins.filename.replace(home,"")
        self.trace_format_width = max(self.trace_format_width, len(fn))
        w = self.trace_format_width
        if not trace:
            return '' 
        if trace == 1:
            return f'[{fn:<{w}},line:{ins.lineno}, in {ins.function}]'
        if trace == 2:
            return f'[{fn:<{w}}, in {ins.function}]'

def V_ (verbose):
    try:
        verbose = int(verbose)
    except:
        pass
    return verbose

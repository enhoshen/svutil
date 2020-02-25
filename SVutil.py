import os
import inspect
import logging
import colorama
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
    def print(self,*arg,verbose=None, trace=1, level=None, color=None,**kwarg):
        '''
            Customized message print controlled with verbose level for each messages seperately
            and trace setting for code tracing configuration 
                Args:
                    verbose: determine the verbose level of the message, if not given, messages
                        is printed nonetheless
                    trace: see self.Trace
                    level: print messages with lower verbose level than self.verbose if True
                        or else only the specific verbose level messages are printed
        '''
        level = level if level else 0
        ins = inspect.getframeinfo(inspect.currentframe().f_back)
        if color is None:
            color = ''
        else: 
            if color[0] == '\033':
                pass
            else:
                color = colorama.Fore.__dict__.get(color); color = '' if not color else color
        ins = f'{colorama.Fore.CYAN}'+ self.Trace(ins, trace) + f'{colorama.Style.RESET_ALL}' + color
        try:
            if self.level >= level and verbose == self.verbose:
                print(ins, *arg, f'{colorama.Style.RESET_ALL}', **kwarg)
        except:
            if verbose == self.verbose or verbose is None:
                print(ins, *arg, f'{colorama.Style.RESET_ALL}', **kwarg)
    def Trace(self, ins, trace):
        ''' code tracing using inspect module '''
        home = os.environ.get('HOME','')
        fn = ins.filename.replace(home,"")
        self.trace_format_width = max(self.trace_format_width, len(fn))
        w = self.trace_format_width
        Trace = { None:''
                    ,0:f'[SVutil]'
                    ,1:f'[{fn:<{w}},line:{ins.lineno}, in {ins.function}]'
                    ,2:f'[{fn:<{w}}, in {ins.function}]'
                    ,3:f'[{os.path.basename(fn)}, in {ins.function}]'}
        return Trace[trace]
    def Custom(self):
        self.print('Customizable variable: ', trace=2)
        w = len(max(self.customlst, key=len))
        for i in self.customlst:
            v = self.__dict__[i]
            v = f'"{v}"' if type(v) == str else v.__str__()
            self.print(f'    {i:>{w}}: {v}', trace=2)
class SVcvar():
    ''' 
        SVcvar marks customizable variables;
        as there could be considerable amount of such variable
        the class is named with a short but ambigous name
    '''
    pass

def V_ (verbose):
    try:
        verbose = int(verbose)
    except:
        pass
    return verbose


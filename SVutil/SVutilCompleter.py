import atexit
import builtins
import __main__
import rlcompleter

from SVutil.SVutil import SVutil, colorama
from SVutil.SVparse import EAdict, SVhier
import subprocess 
import sys
import shutil
import inspect

__all__ = ["SVutilCompleter"]

CYAN = colorama.Fore.CYAN
CRESET = colorama.Style.RESET_ALL
class SVutilCompleter(rlcompleter.Completer):
    def __init__(self):
        super().__init__()
        self.cur_sv_words = None
        self.cur_object = None
        self.max_match_cols = 5
        self.prompt = '>>>'
    def complete(self, text, state):
        """Return the next possible completion for 'text'.
        This is called successively with state == 0, 1, 2, ... until it
        returns None.  The completion should begin with 'text'.
        """
        if self.use_main_ns:
            self.namespace = __main__.__dict__

        if not text.strip():
            if state == 0:
                if _readline_available:
                    readline.insert_text('\t')
                    readline.redisplay()
                    return ''
                else:
                    return '\t'
            else:
                return None

        if state == 0:
            if "." in text:
                self.matches = self.attr_matches(text)
            else:
                self.matches = self.global_matches(text)
        try:
            return self.matches[state]
        except IndexError:
            return None

    def global_matches(self, text):
        """Compute matches when text is a simple name.
        Return a list of all keywords, built-in functions and names currently
        defined in self.namespace that match.
        """
        import keyword
        matches = []
        seen = {"__builtins__"}
        n = len(text)
        for word in keyword.kwlist:
            if word[:n] == text:
                seen.add(word)
                if word in {'finally', 'try'}:
                    word = word + ':'
                elif word not in {'False', 'None', 'True',
                                  'break', 'continue', 'pass',
                                  'else'}:
                    word = word + ' '
                matches.append(word)
        for nspace in [self.namespace, builtins.__dict__]:
            for word, val in nspace.items():
                if word[:n] == text and word not in seen:
                    seen.add(word)
                    matches.append(self._callable_postfix(val, word))
        return matches

    def attr_matches(self, text):
        """Compute matches when text contains a dot.
        Assuming the text is of the form NAME.NAME....[NAME], and is
        evaluable in self.namespace, it will be evaluated and its attributes
        (as revealed by dir()) are used as possible completions.  (For class
        instances, class members are also considered.)
        WARNING: this can still invoke arbitrary C code, if an object
        with a __getattr__ hook is evaluated.
        """
        import re
        m = re.match(r"(\w+(\.\w+)*)\.(\w*)", text)
        if not m:
            return []
        expr, attr = m.group(1, 3)
        try:
            thisobject = eval(expr, self.namespace)
        except Exception:
            return []

        # get the content of the object, except __builtins__
        words = set(dir(thisobject))
        words.discard("__builtins__")

        if hasattr(thisobject, '__class__'):
            words.add('__class__')
            words.update(get_class_members(thisobject.__class__))

        if not inspect.isclass(thisobject):
            self.cur_sv_words = self.SVtypeAttr(thisobject)
            self.cur_object = thisobject
            words.update(self.cur_sv_words)

        matches = []
        n = len(attr)
        if attr == '':
            noprefix = '_'
        elif attr == '_':
            noprefix = '__'
        else:
            noprefix = None
        while True:
            for word in words:
                if (word[:n] == attr and
                    not (noprefix and word[:n+1] == noprefix)):
                    match = "%s.%s" % (expr, word)
                    try:
                        val = self.SVGetAttr(thisobject, word)
                    except Exception:
                        pass  # Include even if attribute not set
                    else:
                        match = self._callable_postfix(val, match)
                    matches.append(match)
            if matches or not noprefix:
                break
            if noprefix == '_':
                noprefix = '__'
            else:
                noprefix = None
        matches.sort()
        return matches
    def SVGetAttr(self, obj, word):
        #omit = {SVhier}
        #if hasattr(obj, '__class__'):
        #    tp = obj.__class__
        #    if tp in omit:
        #        return None
        return getattr(obj, word) 

    def SVtypeAttr(self, obj):
        if not hasattr(obj, '__class__'):
            return set()
        if hasattr(obj, '__svcompleterattr__'):
            return obj.__svcompleterattr__() 
        else:
            return set()
    def SVtypeFmt(self, obj):
        return hasattr(obj, '__svcompleterfmt__')
    def SV_display_hook(self, substitution, matches, longest_match_length):
        #rows, columns = subprocess.check_output(['stty', 'size']).split()
        #columns = subprocess.check_output(['tput', 'cols']).split()
        columns, row = shutil.get_terminal_size((80, 20)) 
        x = self.cur_sv_words 
        w = longest_match_length+1
        cols = int(int(columns)/w)
        if not matches:
            sys.stdout.flush()
        else:
            print()
        cur_col = 0
        for i, match in enumerate(matches):
            _match = match.split('.')[-1]
            if self.SVtypeFmt(self.cur_object):
                attr = _match[:-1] if _match[-1] == '(' else _match
                print(self.cur_object.__svcompleterfmt__(attr, f'{match:<{w}}'), end='')
            else:
                print(f'{match:<{w}}', end='')
            if cur_col%cols == cols-1 \
                or cur_col%self.max_match_cols == self.max_match_cols-1:
                cur_col = 0 
                print()
            else:
                cur_col += 1
        if cur_col != 0:
            print()
        print(f'{self.prompt} ',readline.get_line_buffer(), sep='', end='')
        sys.stdout.flush()
        return 


def get_class_members(klass):
    if klass in {EAdict}:
        return {'dic'}
    ret = dir(klass)
    if hasattr(klass,'__bases__'):
        for base in klass.__bases__:
            ret = ret + get_class_members(base)
    return ret

try:
    import readline
except ImportError:
    _readline_available = False
else:
    sc = SVutilCompleter()
    readline.set_completer(sc.complete)
    # Release references early at shutdown (the readline module's
    # contents are quasi-immortal, and the completer function holds a
    # reference to globals).
    atexit.register(lambda: readline.set_completer(None))
    _readline_available = True
    readline.set_completion_display_matches_hook(sc.SV_display_hook)
    #sc.SV_display_hook(None, ['123','456','789'], 5)
    #print(EAdict([1,2,3]).__svcompleterfmt__(1,'1'))

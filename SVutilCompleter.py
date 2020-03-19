"""Word completion for GNU readline.
The completer completes keywords, built-ins and globals in a selectable
namespace (which defaults to __main__); when completing NAME.NAME..., it
evaluates (!) the expression up to the last dot and completes its attributes.
It's very cool to do "import sys" type "sys.", hit the completion key (twice),
and see the list of names defined by the sys module!
Tip: to use the tab key as the completion key, call
    readline.parse_and_bind("tab: complete")
Notes:
- Exceptions raised by the completer function are *ignored* (and generally cause
  the completion to fail).  This is a feature -- since readline sets the tty
  device in raw (or cbreak) mode, printing a traceback wouldn't work well
  without some complicated hoopla to save, reset and restore the tty state.
- The evaluation of the NAME.NAME... form may cause arbitrary application
  defined code to be executed if an object with a __getattr__ hook is found.
  Since it is the responsibility of the application (or the user) to enable this
  feature, I consider this an acceptable risk.  More complicated expressions
  (e.g. function calls or indexing operations) are *not* evaluated.
- When the original stdin is not a tty device, GNU readline is never
  used, and this module (and the readline module) are silently inactive.
"""
import atexit
import builtins
import __main__
import rlcompleter

import SVutil
from SVparse import EAdict, SVhier

__all__ = ["SVutilCompleter"]

CYAN = SVutil.colorama.Fore.CYAN
CRESET = SVutil.colorama.Style.RESET_ALL
class SVutilCompleter(rlcompleter.Completer):
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

        self.cur_sv_words = self.SVtypeAttr(thisobject)
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
        tp = obj.__class__
        CB = {EAdict: self.EAdictAttr}
        x = CB.get(tp)
        return set() if x is None else x(obj)
    
    def EAdictAttr(self, obj):
        x = set(obj.dic.keys())
        return x
    def SV_display_hook(self, substitution, matches, longest_match_length):
        ''' broken '''
        x = self.cur_sv_words 
        w = max(map(len,matches))
        for match in matches:
            if match.split('.')[-1] in x:
                _s = f'{CYAN}{match}{CRESET}'
            else:
                _s = match
            print(f'{_s:<{w}}', end='')
        print(self.prompt.rstrip(), readline.get_line_buffer(), sep='', end='')
        sys.stdout.flush()


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
    #readline.set_completion_display_matches_hook(sc.SV_display_hook)

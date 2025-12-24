from typing import Iterator

def agda2_quote_char(c):
    '''Convert a character to its Haskell escaped representation.'''
    ord_c = ord(c)
    if ord_c < 128:
        return c
    return "\\x%x\&" % ord_c

def agda2_quote_list(ss: Iterator[str]) -> str:
    '''Convert a list of strings to its Haskell string list representation.'''
    return '[' + ', '.join(escape(s) for s in ss) + ']'

# This technically needs to turn a string into a Haskell escaped string, buuuut just gonna cheat.
def escape(s):
    estr = s.replace('\\', '\\\\').replace('"', '\\"').replace('\n','\\n')
    return '"' + ''.join(agda2_quote_char(c) for c in estr) + '"'

# This technically needs to turn a Haskell escaped string into a string, buuuut just gonna cheat.
def unescape(s):
    return s.replace('\\\\','\x00').replace('\\"', '"').replace('\\n','\n').replace('\x00', '\\') # hacktastic


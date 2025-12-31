from __future__ import annotations
from typing import Iterator, List, Union
import logging
from dataclasses import dataclass

from .token import Token, TokenString, TokenAtom, TokenKind, tokenize

logger = logging.getLogger(__name__)

@dataclass(order=True, frozen=True, slots=True)
class Nil:
    """
    Represents the nil atom in S-expressions
    """

    def __str__(self):
        return "nil"
    

@dataclass(order=True, frozen=True, slots=True)
class Symbol:
    name: str

    def __str__(self):
        return self.name

@dataclass(order=True, frozen=True, slots=True)
class Pair:
    car: SExpr
    cdr: SExpr
    
    def __str__(self):
        return format([self.car, Symbol('.'), self.cdr])

SAtom = Union[Symbol, str, int, float, bool, Nil]
SExpr = Union[SAtom, List["SExpr"], Pair]

NIL = Nil()
DOT = Symbol('.')
QUOTE = Symbol('quote')

def qq(expr: SExpr) -> SExpr:
    return [QUOTE, expr]

def isqq(sexpr: SExpr) -> bool:
    return (isinstance(sexpr, list)
            and len(sexpr) == 2
            and sexpr[0] == QUOTE)

def _parse_list(tokens: Iterator[Token]) -> Iterator[SExpr]:
    for tok in tokens:
        if tok.kind == TokenKind.RPAREN:
            return
        elif tok.kind == TokenKind.LPAREN:
            lst = list(_parse_list(tokens))
            if not DOT in lst:
                yield lst
            elif len(lst) == 3 and lst[0] != DOT and lst[1] == DOT and lst[2] != DOT:
                yield Pair(lst[0], lst[2])
            else:
                raise ValueError("Invalid dotted pair syntax: %s" % lst)
        elif isinstance(tok, TokenString):
            yield tok.value
        elif isinstance(tok, TokenAtom):
            yield _convert_atom(tok.value)
        elif tok.kind == TokenKind.DOT:
            yield DOT
        elif tok.kind == TokenKind.QUOTE:
            next_tok = next(tokens)
            if next_tok.kind == TokenKind.LPAREN:
                qexpr = list(_parse_list(tokens))
                if not DOT in qexpr:
                    yield qq(qexpr)
                elif len(qexpr) == 3 and qexpr[0] != DOT and qexpr[1] == DOT and qexpr[2] != DOT:
                    yield qq(Pair(qexpr[0], qexpr[2]))
                else:
                    raise ValueError("Invalid dotted pair syntax: %s" % qexpr)
            elif isinstance(next_tok, TokenString):
                yield qq(next_tok.value)
            elif isinstance(next_tok, TokenAtom):
                yield qq(_convert_atom(next_tok.value))
            else:
                raise ValueError("Unexpected token after quote: %s" % next_tok)
        else:
            raise ValueError("Unexpected token inside list: %s" % tok)
    raise ValueError("Unterminated list: missing ')'")


def _convert_atom(atom: str) -> SAtom:
    # Booleans and nil
    if atom == 't' or atom.lower() == '#t':
        return True
    if atom == 'nil' or atom.lower() == '#f':
        return NIL
    # Integers
    try:
        return int(atom)
    except ValueError:
        pass
    # Floats
    try:
        return float(atom)
    except ValueError:
        pass
    # Symbols as strings
    return Symbol(atom)


def parse(s: str) -> SExpr:
    """
    Parse an S-expressions from a string.
    """
    it = tokenize(s)
    tok = next(it)
    if tok.kind == TokenKind.LPAREN:
        res = list(_parse_list(it))
        try:
            extra = next(it)
        except StopIteration:
            if not DOT in res:
                return res
            elif len(res) == 3 and res[0] != DOT and res[1] == DOT and res[2] != DOT:
                return Pair(res[0], res[2])
            else:
                raise ValueError("Invalid dotted pair syntax: %s" % res)
        else:
            raise ValueError("Extra token after top-level list: %s..." % extra)
    elif tok.kind == TokenKind.STRING:
        raise ValueError("Unexpected '%s' at top level" % tok)
    elif tok.kind == TokenKind.ATOM:
        raise ValueError("Unexpected '%s' at top level" % tok)
    elif tok.kind == TokenKind.RPAREN:
        raise ValueError("Unexpected '%s' at top level" % tok)
    else:
        raise ValueError("Unexpected token: %s" % tok)

def format(sexpr: SExpr) -> str:
    """
    Convert an S-expression back to its string representation.
    """
    if isinstance(sexpr, list):
        if len(sexpr) >= 1 and sexpr[0] == QUOTE:
            return '\'' + ' '.join(format(s) for s in sexpr[1:])
        return '(' + ' '.join(format(s) for s in sexpr) + ')'
    if isinstance(sexpr, str):
        # Escape special characters in strings
        return '"' + sexpr.replace('"', '\\"') + '"'
    if isinstance(sexpr, Symbol):
        return str(sexpr)
    if isinstance(sexpr, bool):
        return 't' if sexpr else 'nil'
    return str(sexpr)

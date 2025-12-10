from __future__ import annotations
from enum import IntEnum, unique
from typing import Any, Iterator, List, Union, Optional, Type
import logging
from dataclasses import dataclass

from .token import Token, TokenKind, tokenize

class Nil:
    """
    Represents the nil atom in S-expressions
    """
    __slots__ = ()

    def __repr__(self):
        return "nil"
    
    def __str__(self):
        return "nil"
    
    def __eq__(self, other: 'Nil'):
        return isinstance(other, Nil)

@dataclass(frozen=True, slots=True)
class Symbol:
    name: str
    def __str__(self):
        return self.name

@dataclass(frozen=True)
class Pair:
    car: "SExpr"
    cdr: "SExpr"
    
    def __str__(self):
        return format([self.car, Symbol('.'), self.cdr])

SAtom: Type = Union[Symbol, str, int, float, bool, Nil]
SExpr: Type = Union[SAtom, List["SExpr"], Pair]

logger = logging.getLogger(__name__)

NIL = Nil()
DOT = Symbol('.')

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
        elif tok.kind == TokenKind.STRING:
            yield tok.value
        elif tok.kind == TokenKind.ATOM:
            yield _convert_atom(tok.value)
        elif tok.kind == TokenKind.DOT:
            yield DOT
        elif tok.kind == TokenKind.QUOTE:
            next_tok = next(tokens)
            if next_tok.kind == TokenKind.LPAREN:
                quoted_expr = list(_parse_list(tokens))
                if not DOT in quoted_expr:
                    yield ['quote', quoted_expr]
                elif len(quoted_expr) == 3 and quoted_expr[0] != DOT and quoted_expr[1] == DOT and quoted_expr[2] != DOT:
                    yield ['quote', Pair(quoted_expr[0], quoted_expr[2])]
                else:
                    raise ValueError("Invalid dotted pair syntax: %s" % quoted_expr)
            elif next_tok.kind == TokenKind.STRING:
                yield ['quote', next_tok.value]
            elif next_tok.kind == TokenKind.ATOM:
                yield ['quote', _convert_atom(next_tok.value)]
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
        logger.debug("parse string, token: %s" % tok)
        res = list(_parse_list(it))
        try:
            extra = next(it)
        except StopIteration:
            dot = Symbol('.')
            if not dot in res:
                return res
            elif len(res) == 3 and res[0] != dot and res[1] == dot and res[2] != dot:
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
        if len(sexpr) >= 1 and sexpr[0] == 'quote':
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

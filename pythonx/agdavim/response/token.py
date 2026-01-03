from enum import IntEnum, unique
from typing import Iterator, Union, Literal, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@unique
class TokenKind(IntEnum):
    LPAREN = 0
    RPAREN = 1
    ATOM = 2
    STRING = 3
    QUOTE = 4
    DOT = 5


@dataclass(eq=True, order=True, frozen=True)
class TokenSymbol:
    _kind: Literal[TokenKind.LPAREN, TokenKind.RPAREN, TokenKind.QUOTE, TokenKind.DOT]
    _value: None

    @property
    def kind(self) -> TokenKind:
        return self._kind

    @property
    def value(self) -> None:
        return self._value

    def __repr__(self):
        return f"Token(%r, %r)" % (self._kind, self._value)

    def __str__(self):
        return f"'%s'" % self._kind.name


@dataclass(eq=True, order=True, frozen=True)
class TokenString:
    _kind: Literal[TokenKind.STRING]
    _value: str

    @property
    def kind(self) -> TokenKind:
        return self._kind

    @property
    def value(self) -> str:
        return self._value

    def __repr__(self):
        return f"Token(%r, %r)" % (self._kind, self._value)

    def __str__(self):
        return f"Token(%s, %s)" % (self._kind.name, self._value)


@dataclass(eq=True, order=True, frozen=True)
class TokenAtom:
    _kind: Literal[TokenKind.ATOM]
    _value: str

    @property
    def kind(self) -> TokenKind:
        return self._kind

    @property
    def value(self) -> str:
        return self._value

    def __repr__(self):
        return f"Token(%r, %r)" % (self._kind, self._value)

    def __str__(self):
        return f"Token(%s, %s)" % (self._kind.name, self._value)


Token = Union[TokenSymbol, TokenString, TokenAtom]


def tokenize(s: str) -> Iterator[Token]:
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c.isspace():
            i += 1
            continue
        if c == ';':
            # Lisp-style line comment: skip until newline
            while i < n and s[i] != '\n':
                i += 1
            continue
        if c == '(':
            yield TokenSymbol(TokenKind.LPAREN, None)
            i += 1
            continue
        if c == ')':
            yield TokenSymbol(TokenKind.RPAREN, None)
            i += 1
            continue
        if c == '\'':
            yield TokenSymbol(TokenKind.QUOTE, None)
            i += 1
            continue
        if c == '.':
            yield TokenSymbol(TokenKind.DOT, None)
            i += 1
            continue
        if c == '"':
            # Parse string literal with escapes
            i += 1
            buf: List[str] = []
            while i < n:
                ch = s[i]
                if ch == '\\':
                    i += 1
                    if i >= n:
                        raise ValueError("Unterminated escape in string")
                    esc = s[i]
                    if esc == 'n':
                        buf.append('\n')
                    elif esc == 'r':
                        buf.append('\r')
                    elif esc == 't':
                        buf.append('\t')
                    elif esc == '"':
                        buf.append('"')
                    elif esc == '\\':
                        buf.append('\\')
                    else:
                        # Unknown escapes pass through
                        buf.append(ch + esc)
                    i += 1
                elif ch == '"':
                    i += 1
                    break
                else:
                    buf.append(ch)
                    i += 1
            else:
                logger.debug("break while: s[%d]:%s" % (i, ''.join(buf)))
                raise ValueError("Unterminated string literal")

            yield TokenString(TokenKind.STRING, ''.join(buf))
        else:
            # Parse atom: until whitespace or paren
            start = i
            while i < n and (not s[i].isspace()) and s[i] not in ')':
                i += 1
            atom = s[start:i]
            yield TokenAtom(TokenKind.ATOM, atom)


from enum import IntEnum, unique
from typing import Iterator, Optional
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


class Token:
    _kind: TokenKind
    _value: Optional[str]
    def __init__(self, kind: TokenKind, value: Optional[str] = None):
        self._kind = kind
        self._value = value

    @property
    def kind(self) -> TokenKind:
        return self._kind
    
    @property
    def value(self) -> Optional[str]:
        return self._value

    def __repr__(self):
        return f"Token(%r, %r)" % (self._kind, self._value)

    def __str__(self):
        if self._value is None:
            return f"Token(%s)" % self._kind.name
        else:
            return f"Token(%s, %s)" % (self._kind.name, self._value)


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
            yield Token(TokenKind.LPAREN)
            i += 1
            continue
        if c == ')':
            yield Token(TokenKind.RPAREN)
            i += 1
            continue
        if c == '\'':
            yield Token(TokenKind.QUOTE)
            i += 1
            continue
        if c == '.':
            yield Token(TokenKind.DOT)
            i += 1
            continue
        if c == '"':
            # Parse string literal with escapes
            i += 1
            buf = []
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
                    logger.debug("terminated string: %s" % ''.join(buf))
                    i += 1
                    break
                else:
                    buf.append(ch)
                    i += 1
            else:
                logger.debug("break while: s[%d]:%s" % (i, ''.join(buf)))
                raise ValueError("Unterminated string literal")

            yield Token(TokenKind.STRING, ''.join(buf))
        else:
            # Parse atom: until whitespace or paren
            start = i
            while i < n and (not s[i].isspace()) and s[i] not in ')':
                i += 1
            atom = s[start:i]
            logger.debug("atom: s[%d:%d]:%s" % (start, i, atom))
            yield Token(TokenKind.ATOM, atom)


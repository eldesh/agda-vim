from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import vim

from .agda_path import agda2_quote_string
from .response import sexpr
from .response.sexpr import Symbol
from .response.filepos import OBRange, OBPoint
from . import vimapi

@dataclass(order=True, frozen=True, slots=True)
class Position:
    """ Represents a position in a buffer.

    _point: int 1-based absolute position (in characters)
    _row: int 1-based line number
    _col: int 1-based column number (in characters)
    """

    _point: int
    _row: int
    _col: int

    @property
    def point(self) -> int:
        return self._point

    @property
    def row(self) -> int:
        return self._row

    @property
    def col(self) -> int:
        return self._col

    def __str__(self) -> str:
        return sexpr.format(self.to_sexpr())

    def to_sexpr(self) -> sexpr.SExpr:
        return [Symbol("Pn"), [], self.point, self.row, self.col]

    @classmethod
    def from_point(cls, pos: OBPoint, buffer: vim.Buffer) -> Position:
        """Convert from OBPoint (1-origin, byte unit) to Position (1-origin, char unit) in current buffer."""
        prev_nl = pos.row - 1 # Number of line breaks '\n'
        # Number of characters up to the previous line
        chars = sum(len(s) for s in buffer[:prev_nl])
        # In the line: byte column -> character column (1-based)
        line = buffer[prev_nl]
        colc = int(vimapi.charidx(line, pos.col)) + 1
        return cls(chars + prev_nl + colc, pos.row, pos.col)

    @classmethod
    def current(cls, buffer: vim.Buffer) -> Position:
        pos = vimapi.current_position()
        return cls.from_point(pos, buffer)


@dataclass(order=True, frozen=True, slots=True)
class BufferRange:
    _buffer: vim.Buffer
    _start: Position
    _end: Position

    @property
    def filename(self) -> str:
        return self._buffer.name

    @property
    def start(self) -> Position:
        return self._start

    @property
    def end(self) -> Position:
        return self._end

    def __str__(self) -> str:
        return sexpr.format(self.to_sexpr())

    def to_sexpr(self) -> sexpr.SExpr:
        S = Symbol
        interval = [S("Interval"), self.start.to_sexpr(), self.end.to_sexpr()]
        return [S("intervalsToRange"), [S("Just"), [S("mkAbsolute"), agda2_quote_string(self.filename)]], interval]


def mk_range(rng: Optional[OBRange]) -> Optional[BufferRange]:
    if rng:
        return BufferRange(
                vim.current.buffer,
                Position.from_point(rng.start, vim.current.buffer),
                Position.from_point(rng.end  , vim.current.buffer))
    else:
        return None


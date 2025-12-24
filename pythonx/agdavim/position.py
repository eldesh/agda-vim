from dataclasses import dataclass

from . import response
from .response import sexpr
from .response.sexpr import Symbol
from .agda_path import escape

@dataclass(eq=True, order=True, frozen=True, slots=True)
class Position:
    """ Represents a position in a buffer. """
    _point: int
    _line: int
    _col: int
    
    def __init__(self, point: int, line: int, col: int):
        self._point = point
        self._line = line
        self._col = col

    @property
    def point(self) -> int:
        return self._point

    @property
    def line(self) -> int:
        return self._line

    @property
    def col(self) -> int:
        return self._col

    def __str__(self) -> str:
        return sexpr.format(self.to_expr())

    def to_sexpr(self) -> sexpr.SExpr:
        return ["Pn", [], self.point, self.line, self.col]


class BufferRange:
    _file: str
    _start: Position
    _end: Position

    def __init__(self, file: str, start: Position, end: Position):
        self._file = file
        self._start = start
        self._end = end

    @property
    def file(self) -> str:
        return self._file

    @property
    def start(self) -> Position:
        return self._start

    @property
    def end(self) -> Position:
        return self._end

    def __str__(self) -> str:
        return sexpr.format(self.to_expr())

    def to_expr(self) -> sexpr.SExpr:
        interval = "[Interval %s %s]" % (self.start.to_sexpr(), self.end.to_sexpr())
        return ["intervalsToRange", ["Just", ["mkAbsolute", escape(self.file)]], Symbol(interval)]


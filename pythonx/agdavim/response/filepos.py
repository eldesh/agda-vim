from __future__ import annotations
from dataclasses import dataclass
from typing import Generic, TypeVar, ClassVar, Any

from .sexpr import Pair
from . import sexpr

class Origin0:
    """0-origin marker (phantom type)."""
    __slots__ = ()

class Origin1:
    """1-origin marker (phantom type)."""
    __slots__ = ()

class UnitByte:
    """Phantom type marker representing byte units"""
    __slots__ = ()

class UnitChar:
    """Phantom type marker representing char units"""
    __slots__ = ()

O = TypeVar('O', Origin0, Origin1)
U = TypeVar('U', UnitByte, UnitChar)


@dataclass(order=True, frozen=True, slots=True)
class Point(Generic[O, U]):
    """Represents a point in a buffer with row and column."""

    ORIGIN: ClassVar[int]
    _row: int
    _col: int

    @property
    def row(self) -> int:
        return self._row

    @property
    def col(self) -> int:
        return self._col

    def __str__(self) -> str:
        if self.ORIGIN == 0:
            return "(%d, %d)\u2080" % (self.row, self.col)
        if self.ORIGIN == 1:
            return "(%d, %d)\u2081" % (self.row, self.col)
        assert False, "unreachable"

    def to_zero_origin(self) -> Point[Origin0, U]:
        if self.ORIGIN == 0:
            return self  # type: ignore[return-value]
        else:
            return Point[Origin0, U](self.row - 1, self.col - 1)

    def to_one_origin(self) -> Point[Origin1, U]:
        if self.ORIGIN == 1:
            return self  # type: ignore[return-value]
        else:
            return Point[Origin1, U](self.row + 1, self.col + 1)


P_co = TypeVar("P_co", bound=Point[Any, Any], covariant=True)

@dataclass(order=True, frozen=True, slots=True)
class Range(Generic[P_co]):
    ORIGIN: ClassVar[int]
    _start: P_co
    _end: P_co

    @property
    def start(self) -> P_co:
        return self._start

    @property
    def end(self) -> P_co:
        return self._end

    def __str__(self) -> str:
        return "[%s,%s]" % (self.start, self.end)


@dataclass(order=True, frozen=True, slots=True)
class FilePosition(Generic[O, U]):
    """Represents the offset within a file.

    Type parameters:
    - O indicates the origin of the offset (e.g., Origin0 or Origin1).
    - U indicates the unit of the offset (e.g., UnitByte or UnitChar).
    """

    ORIGIN: ClassVar[int]
    _file: str
    _pos: int

    @property
    def file(self) -> str:
        return self._file

    @property
    def pos(self) -> int:
        return self._pos

    def to_sexpr(self) -> Pair:
        return Pair(self._file, self._pos)

    def __str__(self):
        return sexpr.format(self.to_sexpr())


@dataclass(order=True, frozen=True, slots=True)
class FilePoint(Generic[O, U]):
    """Represents the point within a file.

    Type parameters:
    - O indicates the origin of the offset (e.g., Origin0 or Origin1).
    - U indicates the unit of the offset (e.g., UnitByte or UnitChar).
    """

    ORIGIN: ClassVar[int]
    _file: str
    _point: Point[O, U]

    @property
    def file(self) -> str:
        return self._file

    @property
    def point(self) -> Point[O, U]:
        return self._point

    @property
    def row(self) -> int:
        return self._point.row

    @property
    def col(self) -> int:
        return self._point.col

    def __str__(self):
        return '%s:%s' % (self._file, self._point)


class ZCPoint(Point[Origin0, UnitChar]):
    ORIGIN = 0
    def to_one_origin(self) -> OCPoint:
        return OCPoint(self.row + 1, self.col + 1)

class OCPoint(Point[Origin1, UnitChar]):
    ORIGIN = 1
    def to_zero_origin(self) -> ZCPoint:
        return ZCPoint(self.row - 1, self.col - 1)

class ZBPoint(Point[Origin0, UnitByte]):
    ORIGIN = 0
    def to_one_origin(self) -> OBPoint:
        return OBPoint(self.row + 1, self.col + 1)

class OBPoint(Point[Origin1, UnitByte]):
    ORIGIN = 1
    def to_zero_origin(self) -> ZBPoint:
        return ZBPoint(self.row - 1, self.col - 1)


class ZCRange(Range[ZCPoint]):
    ORIGIN = ZCPoint.ORIGIN
    def to_one_origin(self) -> OCRange:
        return OCRange(self.start.to_one_origin(), self.end.to_one_origin())

class OCRange(Range[OCPoint]):
    ORIGIN = OCPoint.ORIGIN
    def to_zero_origin(self) -> ZCRange:
        return ZCRange(self.start.to_zero_origin(), self.end.to_zero_origin())

class ZBRange(Range[ZBPoint]):
    ORIGIN = ZBPoint.ORIGIN
    def to_one_origin(self) -> OBRange:
        return OBRange(self.start.to_one_origin(), self.end.to_one_origin())

class OBRange(Range[OBPoint]):
    ORIGIN = OBPoint.ORIGIN
    def to_zero_origin(self) -> ZBRange:
        return ZBRange(self.start.to_zero_origin(), self.end.to_zero_origin())


class ZCFilePosition(FilePosition[Origin0, UnitChar]):
    ORIGIN = 0

class OCFilePosition(FilePosition[Origin1, UnitChar]):
    ORIGIN = 1

class ZBFilePosition(FilePosition[Origin0, UnitByte]):
    ORIGIN = 0

class OBFilePosition(FilePosition[Origin1, UnitByte]):
    ORIGIN = 1


class ZCFilePoint(FilePoint[Origin0, UnitChar]):
    ORIGIN = 0

class OCFilePoint(FilePoint[Origin1, UnitChar]):
    ORIGIN = 1

class ZBFilePoint(FilePoint[Origin0, UnitByte]):
    ORIGIN = 0

class OBFilePoint(FilePoint[Origin1, UnitByte]):
    ORIGIN = 1


from __future__ import annotations
from dataclasses import dataclass
from typing import Generic, TypeVar, Tuple, ClassVar

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


@dataclass(eq=True, order=True, frozen=True, slots=True)
class FilePosition(Generic[O, U]):
    ORIGIN: ClassVar[int]
    _file: str
    _pos: int

    @property
    def as_tuple(self) -> Tuple[str, int]:
        return (self._file, self._pos)

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


@dataclass(eq=True, order=True, frozen=True, slots=True)
class LineCol(Generic[O, U]):
    ORIGIN: ClassVar[int]
    _file: str
    _line: int
    _col: int
    
    @property
    def file(self) -> str:
        return self._file

    @property
    def line(self) -> int:
        return self._line

    @property
    def col(self) -> int:
        return self._col


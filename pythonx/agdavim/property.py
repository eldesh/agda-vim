from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping
from enum import Enum, auto, unique

from .vimapi import GroundType


@dataclass(order=True, frozen=True, slots=True)
class PropertyId:
    """ Unique identifier for highlight properties. """
    _val: int

    def get(self) -> int:
        return self._val

    def __str__(self) -> str:
        return '%s' % self._val

    def __repr__(self) -> str:
        return 'PropertyId(%s)' % self._val

    def __add__(self, other: int) -> PropertyId:
        return PropertyId(self._val + other)


@unique
class PropertyKey(Enum):
    GOAL_NUMBER = auto()
    VIRTUAL_TXT = auto()


PropertyValue = GroundType


@dataclass(order=True, frozen=True, slots=True)
class AgdaProperty:
    _id: PropertyId
    _prop: Mapping[PropertyKey, PropertyValue]
    
    @property
    def id(self) -> PropertyId:
        return self._id

    def __getitem__(self, key: PropertyKey) -> PropertyValue:
        return self._prop[key]

    def __contains__(self, key: PropertyKey) -> bool:
        return key in self._prop

    def __items__(self):
        return self._prop.items()

    def __str__(self) -> str:
        return str(self._prop)


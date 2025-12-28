from dataclasses import dataclass
from typing import Mapping, Union
from enum import Enum, auto, unique


@dataclass(eq=True, order=True, frozen=True, slots=True)
class PropertyId:
    """ Unique identifier for highlight properties. """
    _val: int

    def __str__(self) -> str:
        return '%s' % self._val

    def __repr__(self) -> str:
        return 'PropertyId(%s)' % self._val

    def __add__(self, other: int) -> 'PropertyId':
        return PropertyId(self._val + other)


@unique
class PropertyKey(Enum):
    GOAL_NUMBER = auto()
    VIRTUAL_TXT = auto()


PropertyValue = Union[str, int]


@dataclass(eq=True, order=True, slots=True)
class AgdaProperty:
    _prop: Mapping[PropertyKey, PropertyValue]
    
    def __init__(self, prop: Mapping[PropertyKey, PropertyValue]) -> None:
        self._prop = prop

    def __getitem__(self, key: PropertyKey) -> PropertyValue:
        return self._prop[key]

    def __contains__(self, key: PropertyKey) -> bool:
        return key in self._prop

    def __items__(self):
        return self._prop.items()


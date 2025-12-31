from __future__ import annotations
from enum import IntEnum, unique

@unique
class ComputeMode(IntEnum):
    DefaultCompute = 0
    IgnoreAbstract = 1
    UseShowInstance = 2
    HeadCompute = 3

    @classmethod
    def from_int(cls, value: int) -> ComputeMode:
        return cls(value)

    @classmethod
    def parse(cls, text: str) -> ComputeMode:
        if text == "DefaultCompute":
            return cls.DefaultCompute
        if text == "IgnoreAbstract":
            return cls.IgnoreAbstract
        if text == "UseShowInstance":
            return cls.UseShowInstance
        if text == "HeadCompute":
            return cls.HeadCompute
        raise ValueError("%s is not a valid ComputeMode" % text)


@unique
class NormaliseType(IntEnum):
    Simplified = 0
    Instantiated = 1
    Normalised = 2
    HeadNormal = 3

    @classmethod
    def from_int(cls, value: int) -> NormaliseType:
        return cls(value)

    @classmethod
    def parse(cls, text: str) -> NormaliseType:
        if text == "Simplified":
            return cls.Simplified
        if text == "Instantiated":
            return cls.Instantiated
        if text == "Normalised":
            return cls.Normalised
        if text == "HeadNormal":
            return cls.HeadNormal
        raise ValueError("%s is not a valid NormaliseType" % text)


@unique
class NormaliseAsIsType(IntEnum):
    AsIs = 0
    Simplified = 1
    Normalised = 2
    HeadNormal = 3

    @classmethod
    def from_int(cls, value: int) -> NormaliseAsIsType:
        return cls(value)

    @classmethod
    def parse(cls, text: str) -> NormaliseAsIsType:
        if text == "AsIs":
            return cls.AsIs
        if text == "Simplified":
            return cls.Simplified
        if text == "Normalised":
            return cls.Normalised
        if text == "HeadNormal":
            return cls.HeadNormal
        raise ValueError("%s is not a valid NormaliseAsIsType" % text)


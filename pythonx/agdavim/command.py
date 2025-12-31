from __future__ import annotations
from enum import Enum, auto, unique
from typing import List, Optional
from dataclasses import dataclass
import logging

from .response.filepos import OCFilePosition

logger = logging.getLogger(__name__)


@unique
class UsePrefixArgs(Enum):
    WITH_FORCE = auto()
    WITHOUT_FORCE = auto()

    def __str__(self) -> str:
        if self == UsePrefixArgs.WITH_FORCE:
            return "WithForce"
        else:
            return "WithoutForce"


@dataclass
class HighlightCommand:
    """
    Represents a highlight annotation of the form:
    (FROM TO ASPECTS [TOKEN-BASED] [INFO] [FILEPOS])

    Notes:
    - FROM and TO are 1-origin positions within the buffer.
    - Positions are counted by bytes (not characters).

    Args:
        from_ (int): 1-origin start position in the buffer (byte-based).
        to (int): 1-origin end position in the buffer (byte-based).
        aspects (List[str]): List of aspect names associated with the annotation.
        token_based (Optional[Union[bool, Nil]]): Optional token-based flag (True or nil).
        info (Optional[Union[str, Nil]]): Optional information string or nil.
        filepos (Optional[OCFilePosition]): Optional file position (1-origin, character-based).
    """
    _from: int
    _to: int
    _aspects: List[str]
    _token_based: bool
    _info: Optional[str]
    _filepos: Optional[OCFilePosition]

    def __str__(self):
        aspects = '(' + ' '.join(self._aspects) + ')'
        token_based = 't' if self._token_based else 'f'
        if self.filepos is None and self.info is None:
            return "(%d %d %s %s)" % (
                self._from, self._to, aspects, token_based)
        if self.filepos is None:
            return "(%d %d %s %s %s)" % (
                self._from, self._to, aspects, token_based, self._info)
        else:
            return "(%d %d %s %s %s %s)" % (
                self._from, self._to, aspects, token_based, self._info, self._filepos)

    @property
    def from_(self) -> int:
        return self._from

    @property
    def to(self) -> int:
        return self._to

    @property
    def aspects(self) -> List[str]:
        return self._aspects

    @property
    def token_based(self) -> bool:
        return self._token_based

    @property
    def info(self) -> Optional[str]:
        return self._info

    @property
    def filepos(self) -> Optional[OCFilePosition]:
        return self._filepos


@unique
class Remove(Enum):
    REMOVE = auto()
    KEEP = auto()

    def __str__(self):
        if self == Remove.REMOVE:
            return "Remove"
        if self == Remove.KEEP:
            return "Keep"
        raise ValueError("Unknown Remove: %s" % self)

    @staticmethod
    def parse(s: str) -> Remove:
        if s == "Remove":
            return Remove.REMOVE
        if s == "Keep":
            return Remove.KEEP
        raise ValueError("Unknown Remove string: %s" % s)


@unique
class HighlightLevel(Enum):
    NONE = auto()
    NON_INTERACTIVE = auto()
    INTERACTIVE = auto()

    def __str__(self):
        if self == HighlightLevel.NONE:
            return "None"
        if self == HighlightLevel.NON_INTERACTIVE:
            return "NonInteractive"
        if self == HighlightLevel.INTERACTIVE:
            return "Interactive"
        raise ValueError("Unknown HighlightLevel: %s" % self)

    @staticmethod
    def parse(s: str) -> HighlightLevel:
        if s == "None":
            return HighlightLevel.NONE
        if s == "NonInteractive":
            return HighlightLevel.NON_INTERACTIVE
        if s == "Interactive":
            return HighlightLevel.INTERACTIVE
        raise ValueError("Unknown HighlightLevel string: %s" % s)


import logging
from enum import Enum, auto, unique

logger = logging.getLogger(__name__)

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

    def parse(s: str) -> 'Remove':
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

    def parse(s: str) -> 'HighlightLevel':
        if s == "None":
            return HighlightLevel.NONE
        if s == "NonInteractive":
            return HighlightLevel.NON_INTERACTIVE
        if s == "Interactive":
            return HighlightLevel.INTERACTIVE
        raise ValueError("Unknown HighlightLevel string: %s" % s)


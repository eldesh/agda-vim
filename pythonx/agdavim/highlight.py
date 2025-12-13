import logging
from enum import Enum, auto, unique

logger = logging.getLogger(__name__)

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


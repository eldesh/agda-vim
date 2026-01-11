from dataclasses import dataclass
from typing import NewType

from .response.filepos import OCPoint


GoalNumber = NewType('GoalNumber', int)

@dataclass(order=True, frozen=True, slots=True)
class AgdaGoal:
    """ Represents a goal in the buffer.

    _buf: (int) Buffer number.
    _num: (GoalNumber) Goal number.
    _contents: (str) Contents of the goal.
    _pos_start: (OCPoint) start position of the goal in the buffer.
    _pos_end: (OCPoint) end position of the goal in the buffer.
    """

    _buf: int
    _num: GoalNumber
    _contents: str
    _pos_start: OCPoint
    _pos_end: OCPoint # _pos_start <= _pos_end

    @property
    def buf(self) -> int:
        return self._buf

    @property
    def num(self) -> GoalNumber:
        return self._num

    @property
    def contents(self) -> str:
        return self._contents

    @property
    def pos_start(self) -> OCPoint:
        return self._pos_start

    @property
    def pos_end(self) -> OCPoint:
        return self._pos_end

    def __str__(self) -> str:
        return "AgdaGoal(buf[%d]: %s@%d, %s..%s)" % (
            self.buf, self.contents, self.num, self.pos_start, self.pos_end)


from __future__ import annotations
from typing import Any, Union, List, Optional, ClassVar
from dataclasses import dataclass
from enum import IntEnum, unique
from abc import ABC, abstractmethod
import logging

from . import sexpr

logger = logging.getLogger(__name__)

class ParseError(Exception):
    _data: str
    _cls: type[Any]
    def __init__(self, data: str, cls: type[Any]):
        super().__init__()
        self._data = data
        self._cls = cls

    def __str__(self):
        return "Failed to parse %s from data: %s" % (self._cls.__name__, self._data)

class Response(ABC):
    TAG: ClassVar[str]

    @classmethod
    def tag(cls) -> str:
        return cls.TAG
    
    @property
    def tag(self) -> str:
        return type(self).TAG

class ExitDoneResponse(Response):
    TAG: ClassVar[str] = "agda2-exit-done"

    def __init__(self):
        super().__init__()
    
    def __str__(self):
        return "(" + self.tag + ")"
    
    @classmethod
    def parse(cls, str) -> 'ExitDoneResponse':
        if sexpr.parse(str) == [cls.TAG]:
            return cls()
        raise ParseError(str, cls)


class AbortDoneResponse(Response):
    TAG: ClassVar[str] = "agda2-abort-done"

    def __init__(self):
        super().__init__()
    
    def __str__(self):
        return "(" + self.tag + ")"
    
    @classmethod
    def parse(cls, str) -> 'AbortDoneResponse':
        if sexpr.parse(str) == [cls.TAG]:
            return cls()
        raise ParseError(str, cls)


class HighlightClearResponse(Response):
    TAG: ClassVar[str] = "agda2-highlight-clear"

    def __init__(self):
        super().__init__()

    def __str__(self):
        return '(' + self.tag + ')'

    @classmethod
    def parse(cls, str) -> 'HighlightClearResponse':
        if sexpr.parse(str) == [cls.TAG]:
            return cls()
        raise ParseError(str, cls)
        

class HighlightLoadAndDeleteActionResponse(Response):
    TAG: ClassVar[str] = "agda2-highlight-load-and-delete-action"

    def __init__(self):
        super().__init__()

    def __str__(self):
        return '(' + self.tag + ')'

    @classmethod
    def parse(cls, str) -> 'HighlightLoadAndDeleteActionResponse':
        if sexpr.parse(str) == [cls.TAG]:
            return cls()
        raise ParseError(str, cls)


class VerboseResponse(Response):
    TAG: ClassVar[str] = "agda2-verbose"

    _message: str

    def __init__(self, message: str):
        super().__init__()
        self._message = message
    
    def __str__(self):
        return '(%s %s)' % (self.tag, self._message)

    @classmethod
    def parse(cls, ss) -> 'VerboseResponse':
        parsed = sexpr.parse(ss)
        if (isinstance(parsed, list)
            and len(parsed) == 2
            and parsed[0] == cls.TAG
            and isinstance(parsed[1], str)):
            return cls(parsed[1])
        raise ParseError(ss, cls)


class InfoActionResponse(Response):
    TAG: ClassVar[str] = "agda2-info-action"

    _name: str
    _text: str
    _append: Union[str, sexpr.Nil]

    def __init__(self, name: str, text: str, append: Union[str, sexpr.Nil]):
        super().__init__()
        self._name = name
        self._text = text
        self._append = append
    
    def __str__(self):
        return '(%s %s %s %s)' % (self.tag, self._name, self._text, self._append)

    @classmethod
    def parse(cls, ss) -> 'InfoActionResponse':
        parsed = sexpr.parse(ss)
        if (isinstance(parsed, list)
            and 3 <= len(parsed) <= 4
            and parsed[0] == cls.TAG
            and isinstance(parsed[1], str)
            and isinstance(parsed[2], str)):
            if len(parsed) == 3:
                return cls(parsed[1], parsed[2])
            if len(parsed) == 4:
                return cls(parsed[1], parsed[2], parsed[3])
        raise ParseError(ss, cls)


class InfoActionAndCopyResponse(Response):
    TAG: ClassVar[str] = "agda2-info-action-and-copy"

    _name: str
    _text: str
    _append: Union[str, sexpr.Nil]

    def __init__(self, name: str, text: str, append: Union[str, sexpr.Nil]):
        super().__init__()
        self._name = name
        self._text = text
        self._append = append
    
    def __str__(self):
        return '(%s %s %s %s)' % (self.tag, self._name, self._text, self._append)

    @classmethod
    def parse(cls, ss) -> 'InfoActionAndCopyResponse':
        parsed = sexpr.parse(ss)
        if (isinstance(parsed, list)
            and 3 <= len(parsed) <= 4
            and parsed[0] == cls.TAG
            and isinstance(parsed[1], str)
            and isinstance(parsed[2], str)):
            if len(parsed) == 3:
                return cls(parsed[1], parsed[2])
            assert len(parsed) == 4
            return cls(parsed[1], parsed[2], parsed[3])
        print("Failed to parse InfoActionAndCopyResponse: %s" % parsed)
        raise ParseError(ss, cls)


class StatusActionResponse(Response):
    TAG: ClassVar[str] = "agda2-status-action"

    _status: str
    def __init__(self, status: str):
        super().__init__()
        self._status = status
    
    def __str__(self):
        return '(%s %s)' % (self.tag, self._status)
    
    @classmethod
    def parse(cls, ss) -> 'StatusActionResponse':
        parsed = sexpr.parse(ss)
        if (isinstance(parsed, list)
            and len(parsed) == 2
            and parsed[0] == cls.TAG
            and isinstance(parsed[1], str)):
            return cls(parsed[1])
        raise ParseError(ss, cls)


@unique
class RemoveTokenBasedHighlighting(IntEnum):
    # remove all token-based highlighting from the file.
    RemoveHighlighting = 0
    KeepHighlighting = 1

    def __str__(self):
        if self == RemoveTokenBasedHighlighting.RemoveHighlighting:
            return sexpr.format("remove")
        else:
            return sexpr.format(sexpr.NIL)

    @classmethod
    def parse(cls, s: str) -> 'RemoveTokenBasedHighlighting':
        parsed = sexpr.parse(s)
        if isinstance(parsed, str) and parsed == "remove":
            return cls.RemoveHighlighting
        if isinstance(parsed, Nil):
            return cls.KeepHighlighting
        raise ValueError("Invalid value for RemoveTokenBasedHighlighting: %s" % s)


class HighlightAddAnnotationsResponse(Response):
    TAG: ClassVar[str] = "agda2-highlight-add-annotations"

    _removeHighlighting: RemoveTokenBasedHighlighting
    _annotations: Optional[sexpr.SExpr]
    def __init__(self, removeHighlighting: RemoveTokenBasedHighlighting, annotations: Optional[sexpr.SExpr] = None):
        super().__init__()
        self._removeHighlighting = removeHighlighting
        self._annotations = annotations
    
    def __str__(self):
        remove = "remove" if self._removeHighlighting == RemoveTokenBasedHighlighting.RemoveHighlighting else sexpr.NIL
        if self._annotations is None:
            return '(%s %s)' % (self.tag, sexpr.format(['quote', remove]))
        else:
            return '(%s %s %s)' % (self.tag,
                sexpr.format(['quote', remove]), sexpr.format(self._annotations))

    @classmethod
    def parse(cls, ss) -> 'HighlightAddAnnotationsResponse':
        parsed = sexpr.parse(ss)
        if (isinstance(parsed, list)
            and 2 <= len(parsed) <= 3
            and parsed[0] == cls.TAG
            and isinstance(parsed[1], list)
            and all(isinstance(x, list) for x in parsed[2:])):
            if parsed[1] == ['quote', 'remove']:
                remove = RemoveTokenBasedHighlighting.RemoveHighlighting
            elif parsed[1] == ['quote', sexpr.NIL]:
                remove = RemoveTokenBasedHighlighting.KeepHighlighting
            else:
                raise ParseError(ss, cls)
            if len(parsed) == 2:
                return cls(remove)
            else:
                return cls(remove, parsed[2])
        raise ParseError(ss, cls)


@dataclass(frozen=True, slots=True)
class InteractionId:
    _id: int

    def __str__(self):
        return str(self._id)

    @classmethod
    def parse(cls, ss: str) -> 'InteractionId':
        return cls(int(ss))


@dataclass(frozen=True, slots=True)
class GiveString:
    text: str
    
    def __str__(self):
        return self.text


@dataclass(frozen=True, slots=True)
class GiveParen:
    def __str__(self):
        return '\'paren'
    
    @classmethod
    def parse(cls, ss: str) -> 'GiveParen':
        if ss == '\'paren':
            return cls()
        raise ParseError(ss, cls)


@dataclass(frozen=True, slots=True)
class GiveNoParen:
    def __str__(self):
        return '\'no-paren'

    @classmethod
    def parse(cls, ss: str) -> 'GiveNoParen':
        if ss == '\'no-paren':
            return cls()
        raise ParseError(ss, cls)

GiveResult = Union[GiveString, GiveParen, GiveNoParen]

def give_result_from_str(ss: str) -> GiveResult:
    try:
        return GiveParen.parse(ss)
    except ParseError:
        pass
    try:
        return GiveNoParen.parse(ss)
    except ParseError:
        pass
    return GiveString(ss)

class GiveActionResponse(Response):
    TAG: ClassVar[str] = "agda2-give-action"

    _interactionId: InteractionId
    _giveResult: GiveResult
    
    def __init__(self, interactionId: InteractionId, giveResult: GiveResult):
        super().__init__()
        self._interactionId = interactionId
        self._giveResult = giveResult
    
    def __str__(self):
        return '(%s %s %s)' % (self.tag, self._interactionId, self._giveResult)

    @classmethod
    def parse(cls, ss) -> 'GiveActionResponse':
        parsed = sexpr.parse(ss)
        if (isinstance(parsed, list)
            and len(parsed) == 3
            and parsed[0] == cls.TAG
            and isinstance(parsed[1], int)
            and isinstance(parsed[2], str)):
            interactionId = InteractionId(parsed[1])
            giveResult = give_result_from_str(parsed[2])
            return cls(interactionId, giveResult)
        raise ParseError(ss, cls)

class GoalsActionResponse(Response):
    TAG: ClassVar[str] = "agda2-goals-action"

    _priority: Optional[int]
    _goals: List[int]
    
    def __init__(self, priority: Optional[int], goals: List[int]):
        super().__init__()
        self._priority = priority
        self._goals = goals

    def __str__(self):
        if self._priority is not None:
            return '((last . %d) . (%s \'(%s)))' % (
                self._priority,
                self.tag,
                ' '.join(str(g) for g in self._goals))
        else:
            return '(%s \'(%s))' % (
                self.tag, ' '.join(str(g) for g in self._goals))

    @property
    def priority(self) -> Optional[int]:
        return self._priority

    @property
    def goals(self) -> List[int]:
        return self._goals

    @classmethod
    def parse(cls, ss) -> 'GoalsActionResponse':
        parsed = sexpr.parse(ss)
        priority = None
        if (isinstance(parsed, sexpr.Pair)
            and isinstance(parsed.car, sexpr.Pair)
            and parsed.car.car == 'last'
            and isinstance(parsed.car.cdr, int)):
            priority = parsed.car.cdr
            cmd = parsed.cdr
        else:
            cmd = parsed
        
        if (isinstance(cmd, list)
            and len(cmd) == 2
            and cmd[0] == cls.TAG
            and isinstance(cmd[1], list)
            and len(cmd[1]) == 2
            and cmd[1][0] == 'quote'
            and all(isinstance(x, int) for x in cmd[1][1])):
            goals = cmd[1][1]
            return cls(priority, goals)
        raise ParseError(ss, cls)

class MakeCaseActionResponse(Response):
    TAG: ClassVar[str] = "agda2-make-case-action"

    _priority: Optional[int]
    _newcls: List[str]
    
    def __init__(self, priority: Optional[int], newcls: List[str]):
        super().__init__()
        self._priority = priority
        self._newcls = newcls

    def __str__(self):
        if self._priority is not None:
            return '((last . %d) . (%s \'(%s)))' % (
                self._priority,
                self.tag,
                ' '.join(sexpr.format(c) for c in self._newcls))
        else:
            return '(%s \'(%s))' % (
                self.tag,
                ' '.join(sexpr.format(c) for c in self._newcls))

    @property
    def priority(self) -> Optional[int]:
        return self._priority

    @property
    def newcls(self) -> List[str]:
        return self._newcls

    @classmethod
    def parse(cls, ss) -> 'MakeCaseActionResponse':
        parsed = sexpr.parse(ss)
        priority = None
        if (isinstance(parsed, sexpr.Pair)
            and isinstance(parsed.car, sexpr.Pair)
            and parsed.car.car == 'last'
            and isinstance(parsed.car.cdr, int)):
            priority = parsed.car.cdr
            cmd = parsed.cdr
        else:
            cmd = parsed
    
        if (isinstance(cmd, list)
            and len(cmd) == 2
            and cmd[0] == cls.TAG
            and isinstance(cmd[1], list)
            and len(cmd[1]) == 2
            and cmd[1][0] == 'quote'
            and all(isinstance(x, str) for x in cmd[1][1])):
            newcls = cmd[1][1]
            return cls(priority, newcls)
        raise ParseError(ss, cls)

class MakeCaseActionExtendlamResponse(Response):
    TAG: ClassVar[str] = "agda2-make-case-action-extendlam"

    _priority: Optional[int]
    _newcls: List[str]
    
    def __init__(self, priority: Optional[int], newcls: List[str]):
        super().__init__()
        self._priority = priority
        self._newcls = newcls

    def __str__(self):
        if self._priority is not None:
            return '((last . %d) . (%s \'(%s)))' % (
                self._priority,
                self.tag,
                ' '.join(sexpr.format(c) for c in self._newcls))
        else:
            return '('' \'(%s))' % (
                self.tag,
                ' '.join(sexpr.format(c) for c in self._newcls))

    @property
    def priority(self) -> Optional[int]:
        return self._priority

    @property
    def newcls(self) -> List[str]:
        return self._newcls

    @classmethod
    def parse(cls, ss) -> 'MakeCaseActionExtendlamResponse':
        parsed = sexpr.parse(ss)
        priority = None
        if (isinstance(parsed, sexpr.Pair)
            and isinstance(parsed.car, sexpr.Pair)
            and parsed.car.car == 'last'
            and isinstance(parsed.car.cdr, int)):
            priority = parsed.car.cdr
            cmd = parsed.cdr
        else:
            cmd = parsed

        if (isinstance(cmd, list)
            and len(cmd) == 2
            and cmd[0] == cls.TAG
            and isinstance(cmd[1], list)
            and len(cmd[1]) == 2
            and cmd[1][0] == 'quote'
            and all(isinstance(x, str) for x in cmd[1][1])):
            newcls = cmd[1][1]
            return cls(priority, newcls)
        raise ParseError(ss, cls)

class SolveAllActionResponse(Response):
    TAG: ClassVar[str] = "agda2-solveAll-action"

    _priority: Optional[int]
    _solutions: List[Union[int, str]]
    
    def __init__(self, priority: Optional[int], solutions: List[Union[int, str]]):
        super().__init__()
        self._priority = priority
        self._solutions = solutions

    def __str__(self):
        if self._priority is not None:
            return '((last . %d) . (%s \'(%s)))' % (
                self._priority,
                self.tag,
                ' '.join(sexpr.format(sol) for sol in self._solutions))
        else:
            return '(%s \'(%s))' % (
                self.tag,
                ' '.join(sexpr.format(sol) for sol in self._solutions))

    @property
    def priority(self) -> Optional[int]:
        return self._priority

    @property
    def solutions(self) -> List[Union[int, str]]:
        return self._solutions

    @classmethod
    def parse(cls, ss) -> 'SolveAllActionResponse':
        parsed = sexpr.parse(ss)
        priority = None
        if (isinstance(parsed, sexpr.Pair)
            and isinstance(parsed.car, sexpr.Pair)
            and parsed.car.car == 'last'
            and isinstance(parsed.car.cdr, int)):
            priority = parsed.car.cdr
            cmd = parsed.cdr
        else:
            cmd = parsed

        if (isinstance(cmd, list)
            and len(cmd) == 2
            and cmd[0] == cls.TAG
            and isinstance(cmd[1], list)
            and len(cmd[1]) == 2
            and cmd[1][0] == 'quote'
            and isinstance(cmd[1][1], list)
            and all(isinstance(x, int) or isinstance(x, str) for x in cmd[1][1])):
            solutions = cmd[1][1]
            return cls(priority, solutions)
        raise ParseError(ss, cls)

class MaybeGotoResponse(Response):
    TAG: ClassVar[str] = "agda2-maybe-goto"

    _priority: Optional[int]
    _filePath: str
    _position: int
    
    def __init__(self, priority: Optional[int], filePath: str, position: int):
        super().__init__()
        self._priority = priority
        self._filePath = filePath
        self._position = position

    def __str__(self):
        if self._priority is not None:
            return '((last . %d) . (%s \'(%s . %d)))' % (
                self._priority,
                self.tag,
                self._filePath,
                self._position)
        else:
            return '(%s \'(%s . %d))' % (
                self.tag,
                self._filePath,
                self._position)

    @property
    def priority(self) -> Optional[int]:
        return self._priority

    @property
    def filePath(self) -> str:
        return self._filePath

    @property
    def position(self) -> int:
        return self._position

    @classmethod
    def parse(cls, ss) -> 'MaybeGotoResponse':
        parsed = sexpr.parse(ss)
        priority = None
        if (isinstance(parsed, sexpr.Pair)
            and isinstance(parsed.car, sexpr.Pair)
            and parsed.car.car == 'last'
            and isinstance(parsed.car.cdr, int)):
            priority = parsed.car.cdr
            cmd = parsed.cdr
        else:
            cmd = parsed

        if (isinstance(cmd, list)
            and len(cmd) == 2
            and cmd[0] == cls.TAG
            and isinstance(cmd[1], list)
            and len(cmd[1]) == 2
            and cmd[1][0] == 'quote'
            and isinstance(cmd[1][1], sexpr.Pair)
            and isinstance(cmd[1][1].car, str)
            and isinstance(cmd[1][1].cdr, int)):
            filePath = cmd[1][1].car
            position = cmd[1][1].cdr
            return cls(priority, filePath, position)
        raise ParseError(ss, cls)


RESPONSE_CLASSES = [
    ExitDoneResponse,
    AbortDoneResponse,
    HighlightClearResponse,
    HighlightLoadAndDeleteActionResponse,
    VerboseResponse,
    InfoActionResponse,
    InfoActionAndCopyResponse,
    StatusActionResponse,
    HighlightAddAnnotationsResponse,
    GiveActionResponse,
    GoalsActionResponse,
    MakeCaseActionResponse,
    MakeCaseActionExtendlamResponse,
    SolveAllActionResponse,
    MaybeGotoResponse
]

def parse_response(ss: str) -> Response:
    for resp_cls in RESPONSE_CLASSES:
        try:
            return resp_cls.parse(ss)
        except ParseError:
            continue
    raise ParseError(ss, Response)

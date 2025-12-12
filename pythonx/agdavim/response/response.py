from __future__ import annotations
from typing import Any, Union, List, Optional, ClassVar, Tuple
from dataclasses import dataclass
from enum import IntEnum, unique
from abc import ABC, abstractmethod
import logging

from . import sexpr
from .sexpr import Nil, Symbol, Pair, QUOTE, qq

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

    @abstractmethod
    def to_sexpr(self) -> sexpr.SExpr:
        raise NotImplementedError(self.__class__)


class ExitDoneResponse(Response):
    TAG: ClassVar[str] = "agda2-exit-done"

    def __init__(self):
        super().__init__()

    def __str__(self):
        return sexpr.format(self.to_sexpr())

    def to_sexpr(self) -> sexpr.SExpr:
        return [Symbol(self.TAG)]

    @classmethod
    def parse(cls, str) -> 'ExitDoneResponse':
        if sexpr.parse(str) == [Symbol(cls.TAG)]:
            return cls()
        raise ParseError(str, cls)


class AbortDoneResponse(Response):
    TAG: ClassVar[str] = "agda2-abort-done"

    def __init__(self):
        super().__init__()

    def __str__(self):
        return sexpr.format(self.to_sexpr())

    def to_sexpr(self) -> sexpr.SExpr:
        return [Symbol(self.TAG)]

    @classmethod
    def parse(cls, str) -> 'AbortDoneResponse':
        if sexpr.parse(str) == [Symbol(cls.TAG)]:
            return cls()
        raise ParseError(str, cls)


class HighlightClearResponse(Response):
    TAG: ClassVar[str] = "agda2-highlight-clear"

    def __init__(self):
        super().__init__()

    def __str__(self):
        return sexpr.format(self.to_sexpr())

    def to_sexpr(self) -> sexpr.SExpr:
        return [Symbol(self.TAG)]

    @classmethod
    def parse(cls, str) -> 'HighlightClearResponse':
        if sexpr.parse(str) == [Symbol(cls.TAG)]:
            return cls()
        raise ParseError(str, cls)


class HighlightLoadAndDeleteActionResponse(Response):
    TAG: ClassVar[str] = "agda2-highlight-load-and-delete-action"

    _file: Optional[str]

    def __init__(self, file: Optional[str]):
        super().__init__()
        self._file = file

    def __str__(self):
        return sexpr.format(self.to_sexpr())

    def to_sexpr(self) -> sexpr.SExpr:
        return [Symbol(self.TAG)] + ([] if self._file is None else [self._file])

    @property
    def file(self) -> Optional[str]:
        return self._file

    @classmethod
    def parse(cls, ss) -> 'HighlightLoadAndDeleteActionResponse':
        parsed = sexpr.parse(ss)
        if (isinstance(parsed, list)
            and 1 <= len(parsed)
            and parsed[0] == Symbol(cls.TAG)):
            if len(parsed) == 2 and isinstance(parsed[1], str):
                return cls(parsed[1])
            return cls()
        raise ParseError(ss, cls)


class VerboseResponse(Response):
    TAG: ClassVar[str] = "agda2-verbose"

    _message: str

    def __init__(self, message: str):
        super().__init__()
        self._message = message

    def __str__(self):
        return sexpr.format(self.to_sexpr())

    def to_sexpr(self) -> sexpr.SExpr:
        return [Symbol(self.TAG), self._message]

    @classmethod
    def parse(cls, ss) -> 'VerboseResponse':
        parsed = sexpr.parse(ss)
        if (isinstance(parsed, list)
            and len(parsed) == 2
            and parsed[0] == Symbol(cls.TAG)
            and isinstance(parsed[1], str)):
            return cls(parsed[1])
        raise ParseError(ss, cls)

    @property
    def message(self) -> str:
        return self._message


class InfoActionResponse(Response):
    TAG: ClassVar[str] = "agda2-info-action"

    _name: str
    _text: str
    _append: bool

    def __init__(self, name: str, text: str, append: bool):
        super().__init__()
        self._name = name
        self._text = text
        self._append = append

    def __str__(self):
        return sexpr.format(self.to_sexpr())

    def to_sexpr(self) -> sexpr.SExpr:
        return [Symbol(self.TAG), self._name, self._text, True if self._append else sexpr.NIL]

    @classmethod
    def parse(cls, ss) -> 'InfoActionResponse':
        parsed = sexpr.parse(ss)
        if (isinstance(parsed, list)
            and len(parsed) == 4
            and parsed[0] == Symbol(cls.TAG)
            and isinstance(parsed[1], str)
            and isinstance(parsed[2], str)
            and (isinstance(parsed[3], sexpr.Nil)
                or (isinstance(parsed[3], bool) and parsed[3]))):
            return cls(parsed[1], parsed[2], isinstance(parsed[3], bool))
        raise ParseError(ss, cls)

    @property
    def name(self) -> str:
        return self._name

    @property
    def text(self) -> str:
        return self._text

    @property
    def append(self) -> bool:
        return self._append


class InfoActionAndCopyResponse(Response):
    TAG: ClassVar[str] = "agda2-info-action-and-copy"

    _name: str
    _text: str
    _append: bool

    def __init__(self, name: str, text: str, append: bool):
        super().__init__()
        self._name = name
        self._text = text
        self._append = append

    def __str__(self):
        return sexpr.format(self.to_sexpr())

    def to_sexpr(self) -> sexpr.SExpr:
        return [Symbol(self.TAG), self._name, self._text, 't' if self._append else sexpr.NIL]

    @classmethod
    def parse(cls, ss) -> 'InfoActionAndCopyResponse':
        parsed = sexpr.parse(ss)
        if (isinstance(parsed, list)
            and len(parsed) <= 4
            and parsed[0] == Symbol(cls.TAG)
            and isinstance(parsed[1], str)
            and isinstance(parsed[2], str)
            and (isinstance(parsed[3], Nil)
                or (isinstance(parsed[3], bool) and parsed[3]))):
            return cls(parsed[1], parsed[2], isinstance(parsed[3], bool))
        raise ParseError(ss, cls)

    @property
    def name(self) -> str:
        return self._name

    @property
    def text(self) -> str:
        return self._text

    @property
    def append(self) -> bool:
        return self._append


class StatusActionResponse(Response):
    TAG: ClassVar[str] = "agda2-status-action"

    _status: str
    def __init__(self, status: str):
        super().__init__()
        self._status = status

    def __str__(self):
        return sexpr.format(self.to_sexpr())

    def to_sexpr(self) -> sexpr.SExpr:
        return [Symbol(self.TAG), self._status]

    @classmethod
    def parse(cls, ss) -> 'StatusActionResponse':
        parsed = sexpr.parse(ss)
        if (isinstance(parsed, list)
            and len(parsed) == 2
            and parsed[0] == Symbol(cls.TAG)
            and isinstance(parsed[1], str)):
            return cls(parsed[1])
        raise ParseError(ss, cls)

    @property
    def status(self) -> str:
        return self._status


@unique
class RemoveTokenBasedHighlighting(IntEnum):
    # remove all token-based highlighting from the file.
    RemoveHighlighting = 0
    KeepHighlighting = 1

    def __str__(self):
        return sexpr.format(self.to_sexpr())

    def to_sexpr(self) -> sexpr.SExpr:
        if self == RemoveTokenBasedHighlighting.RemoveHighlighting:
            return Symbol("remove")
        else:
            return sexpr.NIL

    @classmethod
    def parse(cls, s: str) -> 'RemoveTokenBasedHighlighting':
        parsed = sexpr.parse(s)
        if isinstance(parsed, Symbol) and parsed.name == "remove":
            return cls.RemoveHighlighting
        if isinstance(parsed, Nil):
            return cls.KeepHighlighting
        raise ValueError("Invalid value for RemoveTokenBasedHighlighting: %s" % s)


class FilePosition:
    _file: str
    _pos: int

    def __init__(self, file: str, pos: int):
        self._file = file
        self._pos = pos

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
        return Pair(Symbol(self._file), self._pos)

    def __str__(self):
        return sexpr.format(self.to_sexpr())


class HighlightAnnotation:
    """
    Represents a highlight annotation of the form:
    > (FROM TO ASPECTS [TOKEN-BASED] [INFO] [FILEPOS])
    """
    _from: int
    _to: int
    _aspects: List[str]
    _token_based: Optional[Union[bool, Nil]]
    _info: Optional[Union[str, Nil]]
    _filepos: Optional[FilePosition]

    def __init__(self, from_: int, to: int, aspects: List[str],
                 token_based: Optional[Union[bool, Nil]] = None,
                 info: Optional[Union[str, Nil]] = None,
                 filepos: Optional[Tuple[str, int]] = None):
        self._from = from_
        self._to = to
        self._aspects = aspects
        self._token_based = token_based
        self._info = info
        self._filepos = filepos

    def to_sexpr(self) -> sexpr.SExpr:
        filepos = [] if self._filepos is None else [self._filepos.to_sexpr()]
        info = [] if self._info is None else [self._info]
        token_based = [] if self._token_based is None else [self._token_based]
        return [self._from, self._to, self._aspects] + token_based + info + filepos

    def __str__(self):
        return sexpr.format(self.to_sexpr())

    @classmethod
    def parse(cls, expr: sexpr.SExpr) -> 'HighlightAnnotation':
        # e.g. [Symbol(name='quote'), [94, 95, [Symbol(name='function')], nil, nil, Pair(car=Symbol(name='Issue4954-2.agda'), cdr=94)]]
        if (isinstance(expr, list)
            and 3 <= len(expr) <= 6
            and isinstance(expr[0], int)
            and isinstance(expr[1], int)
            and isinstance(expr[2], list)
            and all(isinstance(x, Symbol) for x in expr[2])):
            from_ = expr[0]
            to = expr[1]
            aspects = expr[2]
            token_based = None
            info = None
            filepos = None
            if len(expr) >= 4:
                if isinstance(expr[3], (bool, Nil)):
                    token_based = expr[3]
                else:
                    raise ParseError(expr, cls)
            if len(expr) >= 5:
                if isinstance(expr[4], (str, Nil)):
                    info = expr[4]
                else:
                    raise ParseError(expr, cls)
            if len(expr) == 6:
                if (isinstance(expr[5], Pair)
                    and isinstance(expr[5].car, Symbol)
                    and isinstance(expr[5].cdr, int)):
                    filepos = FilePosition(expr[5].car.name, expr[5].cdr)
                else:
                    raise ParseError(expr, cls)
            return cls(from_, to, aspects, token_based, info, filepos)
        raise ParseError(expr, cls)


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
    def token_based(self) -> Optional[Union[bool, Nil]]:
        return self._token_based

    @property
    def info(self) -> Optional[Union[str, Nil]]:
        return self._info

    @property
    def filepos(self) -> Optional[FilePosition]:
        return self._filepos


class HighlightAddAnnotationsResponse(Response):
    TAG: ClassVar[str] = "agda2-highlight-add-annotations"

    _removeHighlighting: RemoveTokenBasedHighlighting
    _annotations: List[HighlightAnnotation]

    def __init__(self, removeHighlighting: RemoveTokenBasedHighlighting, annotations: List[HighlightAnnotation] = None):
        super().__init__()
        self._removeHighlighting = removeHighlighting
        self._annotations = annotations

    def __str__(self):
        return sexpr.format(self.to_sexpr())

    def to_sexpr(self) -> sexpr.SExpr:
        remove = self._removeHighlighting.to_sexpr()
        return [Symbol(self.tag), qq(remove)] + [qq(ann.to_sexpr()) for ann in self._annotations]

    @classmethod
    def _remove_of(cls, expr) -> 'RemoveTokenBasedHighlighting':
        if expr == qq(Symbol('remove')):
            return RemoveTokenBasedHighlighting.RemoveHighlighting
        if expr == qq(sexpr.NIL):
            return RemoveTokenBasedHighlighting.KeepHighlighting
        raise ParseError(expr, RemoveTokenBasedHighlighting)

    @classmethod
    def parse(cls, ss) -> 'HighlightAddAnnotationsResponse':
        parsed = sexpr.parse(ss)
        if (isinstance(parsed, list)
            and 2 <= len(parsed)
            and parsed[0] == Symbol(cls.TAG)
            and isinstance(parsed[1], list)
            and all(sexpr.isqq(x) for x in parsed[2:])):
            remove = cls._remove_of(parsed[1])
            annotations = [HighlightAnnotation.parse(expr[1]) for expr in parsed[2:]]
            return cls(remove, annotations)
        raise ParseError(ss, cls)

    @property
    def removeHighlighting(self) -> RemoveTokenBasedHighlighting:
        return self._removeHighlighting

    @property
    def annotations(self) -> List[HighlightAnnotation]:
        return self._annotations


@dataclass(frozen=True, slots=True)
class InteractionId:
    _id: int

    def __str__(self):
        return str(self._id)

    @property
    def id(self) -> int:
        return self._id

    @classmethod
    def parse(cls, ss: str) -> 'InteractionId':
        return cls(int(ss))


@dataclass(frozen=True, slots=True)
class GiveString:
    text: str

    def __str__(self):
        return self.text

    @property
    def text(self) -> str:
        return self.text


@dataclass(frozen=True, slots=True)
class GiveParen:
    def __str__(self):
        return sexpr.format(self.to_sexpr())
        
    def to_sexpr(self) -> sexpr.SExpr:
        return qq('paren')

    @classmethod
    def parse(cls, ss: str) -> 'GiveParen':
        if ss == '\'paren':
            return cls()
        raise ParseError(ss, cls)


@dataclass(frozen=True, slots=True)
class GiveNoParen:
    def __str__(self):
        return sexpr.format(self.to_sexpr())

    def to_sexpr(self) -> sexpr.SExpr:
        return qq('no-paren')

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
        return sexpr.format(self.to_sexpr())

    def to_sexpr(self) -> sexpr.SExpr:
        return [Symbol(self.tag), self._interactionId._id, str(self._giveResult)]

    @classmethod
    def parse(cls, ss) -> 'GiveActionResponse':
        parsed = sexpr.parse(ss)
        if (isinstance(parsed, list)
            and len(parsed) == 3
            and parsed[0] == Symbol(cls.TAG)
            and isinstance(parsed[1], int)
            and isinstance(parsed[2], str)):
            interactionId = InteractionId(parsed[1])
            giveResult = give_result_from_str(parsed[2])
            return cls(interactionId, giveResult)
        raise ParseError(ss, cls)

    @property
    def interactionId(self) -> InteractionId:
        return self._interactionId

    @property
    def giveResult(self) -> GiveResult:
        return self._giveResult


class GoalsActionResponse(Response):
    TAG: ClassVar[str] = "agda2-goals-action"

    _priority: Optional[int]
    _goals: List[int]

    def __init__(self, priority: Optional[int], goals: List[int]):
        super().__init__()
        self._priority = priority
        self._goals = goals

    def __str__(self):
        return sexpr.format(self.to_sexpr())

    def to_sexpr(self) -> sexpr.SExpr:
        if self._priority is not None:
            return Pair(Pair(Symbol('last'), self._priority), [Symbol(self.tag), qq(self._goals)])
        else:
            return [Symbol(self.tag), qq(self._goals)]

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
            and parsed.car.car == Symbol('last')
            and isinstance(parsed.car.cdr, int)):
            priority = parsed.car.cdr
            cmd = parsed.cdr
        else:
            cmd = parsed
        
        if (isinstance(cmd, list)
            and len(cmd) == 2
            and cmd[0] == Symbol(cls.TAG)
            and isinstance(cmd[1], list)
            and len(cmd[1]) == 2
            and cmd[1][0] == QUOTE
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
        return sexpr.format(self.to_sexpr())

    def to_sexpr(self) -> sexpr.SExpr:
        if self._priority is not None:
            return Pair(Pair(Symbol('last'), self._priority), [Symbol(self.tag), qq(self._newcls)])
        else:
            return [Symbol(self.tag), qq(self._newcls)]

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
            and parsed.car.car == Symbol('last')
            and isinstance(parsed.car.cdr, int)):
            priority = parsed.car.cdr
            cmd = parsed.cdr
        else:
            cmd = parsed

        if (isinstance(cmd, list)
            and len(cmd) == 2
            and cmd[0] == Symbol(cls.TAG)
            and isinstance(cmd[1], list)
            and len(cmd[1]) == 2
            and cmd[1][0] == QUOTE
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
        return sexpr.format(self.to_sexpr())

    def to_sexpr(self) -> sexpr.SExpr:
        if self._priority is not None:
            return Pair(Pair(Symbol('last'), self._priority), [Symbol(self.tag), qq(self._newcls)])
        else:
            return [Symbol(self.tag), qq(self._newcls)]

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
            and parsed.car.car == Symbol('last')
            and isinstance(parsed.car.cdr, int)):
            priority = parsed.car.cdr
            cmd = parsed.cdr
        else:
            cmd = parsed

        if (isinstance(cmd, list)
            and len(cmd) == 2
            and cmd[0] == Symbol(cls.TAG)
            and isinstance(cmd[1], list)
            and len(cmd[1]) == 2
            and cmd[1][0] == QUOTE
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
        return sexpr.format(self.to_sexpr())

    def to_sexpr(self) -> sexpr.SExpr:
        if self._priority is not None:
            return Pair(Pair(Symbol('last'), self._priority), [Symbol(self.tag), qq(self._solutions)])
        else:
            return [Symbol(self.tag), qq(self._solutions)]

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
            and parsed.car.car == Symbol('last')
            and isinstance(parsed.car.cdr, int)):
            priority = parsed.car.cdr
            cmd = parsed.cdr
        else:
            cmd = parsed

        if (isinstance(cmd, list)
            and len(cmd) == 2
            and cmd[0] == Symbol(cls.TAG)
            and isinstance(cmd[1], list)
            and len(cmd[1]) == 2
            and cmd[1][0] == QUOTE
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
        return sexpr.format(self.to_sexpr())

    def to_sexpr(self) -> sexpr.SExpr:
        if self._priority is not None:
            return Pair(Pair(Symbol('last'), self._priority), [Symbol(self.tag), qq(Pair(self._filePath, self._position))])
        else:
            return [Symbol(self.tag), qq(Pair(self._filePath, self._position))]

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
            and parsed.car.car == Symbol('last')
            and isinstance(parsed.car.cdr, int)):
            priority = parsed.car.cdr
            cmd = parsed.cdr
        else:
            cmd = parsed

        if (isinstance(cmd, list)
            and len(cmd) == 2
            and cmd[0] == Symbol(cls.TAG)
            and isinstance(cmd[1], list)
            and len(cmd[1]) == 2
            and cmd[1][0] == QUOTE
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

from __future__ import annotations
from typing import Any, Callable, List, Dict, MutableSequence, Tuple, Sequence, overload, MutableMapping


def bindeval(expr: str) -> Any: ...


def Function(name: str) -> Callable[..., Any]: ...


def command(cmd: str) -> None: ...


def eval(expr: str) -> Any: ...


class Buffer(MutableSequence[str]):
    vars: MutableMapping[str, object]
    name: str
    number: int

    @overload
    def append(self, value: str) -> None: ...
    @overload
    def append(self, value: str, nr: int) -> None: ...
    @overload
    def append(self, value: List[str]) -> None: ...
    @overload
    def append(self, value: List[str], nr: int) -> None: ...


class TabPage:
    number: int
    windows: Sequence[Window]
    vars: MutableMapping[str, object]
    window: Window
    valid: bool


class Window:
    buffer: Buffer
    cursor: Tuple[int, int] # (row, col)
    height: int
    width: int
    vars: MutableMapping[str, object]
    options: object
    number: int
    row: int
    col: int
    tabpage: TabPage
    valid: bool


class Current:
    buffer: Buffer
    window: Window
    line: str


current: Current

buffers: List[Buffer]

vars: Dict[str, bytes]

tabpages: Sequence[TabPage]

windows: Sequence[Window]

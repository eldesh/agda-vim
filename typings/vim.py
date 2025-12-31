from typing import Any, Callable, List, Dict, MutableSequence, Tuple


def bindeval(expr: str) -> Any: ...


def Function(name: str) -> Callable[..., Any]: ...


def command(cmd: str) -> None: ...


def eval(expr: str) -> Any: ...


class Buffer(MutableSequence[str]):
    number: int
    name: str


class Window:
    cursor: Tuple[int, int] # (row, col)


class Current:
    buffer: Buffer
    window: Window
    line: str


current: Current

buffers: List[Buffer]

vars: Dict[str, bytes]

from __future__ import annotations
from typing import Any, Callable, Union, overload, Optional, List

import vim
from .response.filepos import OBPoint

GroundType = Union[None, bool, int, float, str, List['GroundType']]


def bindeval(expr: str) -> Any:
    return vim.bindeval(expr)


def Function(name: str) -> Callable[..., Any]:
    """Get a Vim function by name."""
    return vim.Function(name)


def command(cmd: str) -> None:
    vim.command(cmd)


def eval(expr: str) -> Any:
    return vim.eval(expr)


prop_add_: Callable[[int, int, dict[str, GroundType]], int] = Function("prop_add")

prop_find_: Callable[[dict[str, GroundType]], dict[str, GroundType]] = Function("prop_find")

prop_list_: Callable[[int, dict[str, GroundType]], List[dict[str, GroundType]]] = Function("prop_list")

input_: Callable[..., str] = Function("input")

inputsave_: Callable[[], int] = Function("inputsave")

inputrestore_: Callable[[], int] = Function("inputrestore")

prop_remove_: Callable[..., int] = Function("prop_remove")

charidx_: Callable[[str, int], int] = Function("charidx")

byteidx_: Callable[[str, int], int] = Function("byteidx")

def prop_add(line: int, col: int, prop: dict[str, GroundType]) -> int:
    return prop_add_(line, col, prop)

def prop_find(prop: dict[str, GroundType]) -> dict[str, GroundType]:
    return prop_find_(prop)

def prop_list(lnum: int, prop: dict[str, GroundType]) -> List[dict[str, GroundType]]:
    return prop_list_(lnum, prop)


@overload
def prop_remove(props: dict[str, GroundType]) -> int:
    pass

@overload
def prop_remove(props: dict[str, GroundType], lnum: int) -> int:
    pass

@overload
def prop_remove(props: dict[str, GroundType], lnum: int, lnumend: int) -> int:
    pass

def prop_remove(props: dict[str, GroundType], lnum: Optional[int] = None, lnumend: Optional[int] = None) -> int:
    if lnum is None:
        return prop_remove_(props)
    elif lnumend is None:
        return prop_remove_(props, lnum)
    else:
        return prop_remove_(props, lnum, lnumend)

def input(prompt: str, text: Optional[str] = None) -> str:
    if text is not None:
        return input_(prompt, text)
    return input_(prompt)

def inputsave() -> int:
    return inputsave_()

def inputrestore() -> int:
    return inputrestore_()

def current_position() -> OBPoint:
    row, col = vim.current.window.cursor
    return OBPoint(row, col+1)

def charidx(line: str, col: int) -> int:
    return charidx_(line, col)

def byteidx(line: str, col: int) -> int:
    return byteidx_(line, col)

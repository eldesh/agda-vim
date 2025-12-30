from __future__ import annotations
from typing import Any, Callable, Union, overload, Optional, List

import vim

GroundType = Union[None, bool, int, float, str, List['GroundType']]


def bindeval(expr: str) -> Any:
    if hasattr(vim, "bindeval", None):
        return vim.bindeval(expr)
    else:
        return vim.eval(expr)


def Function(name: str) -> Callable[..., Any]:
    """Get a Vim function by name."""
    if callable(getattr(vim, "Function", None)):
        return vim.Function(name)
    else:
        return vim.bindeval("function('%s')" % name)


def command(cmd: str) -> None:
    vim.command(cmd)


def eval(expr: str) -> Any:
    return vim.eval(expr)


prop_add_: Callable[[int, int, dict[str, GroundType]], int] = Function("prop_add")

prop_find_: Callable[[dict[str, GroundType]], dict[str, GroundType]] = Function("prop_find")

prop_list_: Callable[[int, dict[str, GroundType]], List[dict[str, GroundType]]] = Function("prop_list")

@overload
def prop_remove_(props: dict[str, GroundType]) -> int:
    pass

@overload
def prop_remove_(props: dict[str, GroundType], lnum: int) -> int:
    pass

@overload
def prop_remove_(props: dict[str, GroundType], lnum: int, lnumend: int) -> int:
    pass

def prop_remove_(props: dict[str, GroundType], lnum: Optional[int] = None, lnumend: Optional[int] = None) -> int:
    if lnum is None:
        return Function("prop_remove")(props)
    elif lnumend is None:
        return Function("prop_remove")(props, lnum)
    else:
        return Function("prop_remove")(props, lnum, lnumend)


def prop_add(line: int, col: int, prop: dict[str, GroundType]) -> int:
    return prop_add_(line, col, prop)

def prop_find(prop: dict[str, GroundType]) -> dict[str, GroundType]:
    return prop_find_(prop)

def prop_list(lnum: int, prop: dict[str, GroundType]) -> List[dict[str, GroundType]]:
    return prop_list_(lnum, prop)

def prop_remove(props: dict[str, GroundType], lnum: Optional[int] = None, lnumend: Optional[int] = None) -> int:
    if lnum is None:
        return prop_remove_(props)
    elif lnumend is None:
        return prop_remove_(props, lnum)
    else:
        return prop_remove_(props, lnum, lnumend)

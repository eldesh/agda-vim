from __future__ import annotations
from typing import Any, Callable, Union, overload, Optional

import vim

GroundType = Union[None, bool, int, float, str]


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


def prop_remove(props: dict[str, GroundType], lnum: Optional[int] = None, lnumend: Optional[int] = None) -> int:
    if lnum is None:
        return prop_remove_(props)
    elif lnumend is None:
        return prop_remove_(props, lnum)
    else:
        return prop_remove_(props, lnum, lnumend)

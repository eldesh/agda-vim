import vim
import logging
from typing import Callable, Union
from sys import version_info
from functools import wraps
from itertools import chain

from .protocol import ComputeMode, NormaliseType, NormaliseAsIsType


logger = logging.getLogger(__name__)

python_cmd = 'py' if version_info.major == 2 else 'py3'


def vim_func(vim_fname_or_func=None, conv=None):
    '''Expose a python function to vim, optionally overriding its name.'''

    def wrap_func(func, vim_fname, conv):
        module = func.__module__
        fname = func.__name__
        vim_fname = vim_fname or fname
        arg_names = func.__code__.co_varnames[:func.__code__.co_argcount]
        arg_defaults = list(zip(arg_names[-len(func.__defaults__ or ()):], func.__defaults__ or []))
        defaults_len = len(func.__defaults__ or ())

        @wraps(func)
        def from_vim(vim_arg_dict):
            '''Convert vim arguments to python and call the function.'''
            logger.debug("vim_arg_dict: %s" % vim_arg_dict)
            args = {}
            # Handle non-defaulted arguments.
            for k in arg_names[:-defaults_len]:
                val = vim_arg_dict[k]
                if k in conv:
                    val = conv[k](val)
                args[k] = val
            # Handle defaulted arguments.
            for i, k in enumerate(arg_names[-defaults_len:]):
                try:
                    val = vim_arg_dict[k]
                except KeyError:
                    _key, val = arg_defaults[i]
                if k in conv:
                    val = conv[k](val)
                args[k] = val
            return func(**args)

        func.from_vim = from_vim

        vim_params = chain(arg_names[0:len(arg_names) - defaults_len], ['...'] if defaults_len > 0 else [])
        vimfunc_def = '''
            function! {vim_fname}({vim_signature})
                {python_cmd} {module}.{fname}.from_vim(vim.eval(\'a:\'))
            endfunction
        '''.format(
            python_cmd=python_cmd,
            vim_fname=vim_fname,
            vim_signature=', '.join(vim_params),
            fname=fname,
            module=module
        )
        #print("vimfunc_def: %s" % vimfunc_def)
        vim.command(vimfunc_def)
        return func

    if callable(vim_fname_or_func):
        return wrap_func(func=vim_fname_or_func, vim_fname=None, conv={})

    def wrapper(func):
        return wrap_func(func=func, vim_fname=vim_fname_or_func, conv=conv or {})
    return wrapper


def vim_bool(s: Union[bool, str]) -> bool:
    if isinstance(s, bool):
        return s
    if s == 'False':
        return False
    if s == 'True':
        return True
    raise ValueError("Cannot convert %s to bool" % s)

def vim_int_range(start: int, stop: int, step: int = 1) -> Callable[[Union[int, str]], int]:
    r = range(start, stop, step)
    def inner(s: Union[int, str]) -> int:
        val = int(s)
        if val in r:
            return val
        raise ValueError("Value %s is not in range %s" % (val, r))
    return inner

def vim_compute_mode(s: Union[int, str]) -> ComputeMode:
    return ComputeMode.from_int(int(s))

def vim_normalise(s: Union[int, str]) -> NormaliseType:
    return NormaliseType.from_int(int(s))

def vim_normalise_asis(s: Union[int, str]) -> NormaliseAsIsType:
    return NormaliseAsIsType.from_int(int(s))


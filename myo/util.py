import re

from amino import Right, Left, Map, Maybe, __, F, Either, List


def parse_int(i):
    return Right(i) if isinstance(i, int) else (
        Right(int(i)) if isinstance(i, str) and i.isdigit() else
        Left('could not parse int {}'.format(i))
    )


def parse_id(value, rex, desc):
    return (
        Maybe(rex.match(str(value)))
        .map(__.group(1))
        .map(int)
        .to_either("could not match {} id {}".format(desc, value))
        .or_else(lambda: parse_int(value)))


def optional_params(m: Map, *keys: str):
    return Map(List.wrap(keys) / (lambda a: (a, m.get(a))))


def bool_params(m, *keys):
    return Map(List.wrap(keys) // (lambda a: m.get(a) / (lambda b: (a, b))))


def view_params(m: Map, *extra):
    return optional_params(m, 'min_size', 'max_size', 'fixed_size', 'position',
                           'weight', 'minimized_size', *extra)


def pane_params(m: Map):
    return view_params(m)


def pane_bool_params(m: Map):
    return bool_params(m, 'pin', 'focus', 'kill')

_py_callback_re = re.compile('^py:(.+)')
_vim_callback_re = re.compile('^vim:(.+)')


def _cb_err(data):
    return 'invalid callback string: {}'.format(data)


def parse_python_callback(data: str):
    return (
        Maybe(_py_callback_re.match(data)) /
        __.group(1) /
        Either.import_path
    ).to_either(_cb_err(data))


def parse_vim_callback(data: str):
    return Left(_cb_err(data))


def parse_callback_spec(data: str):
    return parse_python_callback(data).or_else(F(parse_vim_callback, data))


def amend_options(opt: Map, key: str, value: Maybe):
    return value / (lambda a: opt + (key, a)) | opt

__all__ = ('parse_int', 'optional_params', 'view_params', 'parse_id',
           'parse_callback_spec', 'pane_params')

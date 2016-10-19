from amino import Right, Left, Map, Maybe, __

from myo.util.ident import Ident, ident_field


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


def amend_options(opt: Map, key: str, value: Maybe):
    return value / (lambda a: opt + (key, a)) | opt

__all__ = ('parse_int', 'parse_id', 'Ident', 'ident_field')

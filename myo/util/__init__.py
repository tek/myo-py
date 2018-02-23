from amino import Map, Maybe, __
from amino.util.numeric import parse_int

from chiasma.util.id import Ident


def parse_id(value, rex, desc):
    return (
        Maybe(rex.match(str(value)))
        .map(__.group(1))
        .map(int)
        .to_either("could not match {} id {}".format(desc, value))
        .or_else(lambda: parse_int(value)))


def amend_options(opt: Map, key: str, value: Maybe):
    return value / (lambda a: opt + (key, a)) | opt


__all__ = ('parse_int', 'parse_id', 'Ident')

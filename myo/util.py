from tryp import Right, Left, Map, List, Maybe, __


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


def view_params(m: Map):
    return optional_params(m, 'min_size', 'max_size', 'fixed_size', 'position',
                           'weight')

__all__ = ('parse_int', 'optional_params', 'view_params')

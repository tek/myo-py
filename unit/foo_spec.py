from typing import TypeVar

from kallikrein import k, Expectation

from ribosome.nvim.io.state import NS
from ribosome.compute.ribosome import Ribosome


A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')
D = TypeVar('D')


class Bar:
    pass


class Foo:
    pass


floatRiboState = NS[Ribosome[float, C, D, B], A]
BarRiboState = floatRiboState[C, Bar, B, A]
FooRiboState = BarRiboState[C, Foo, A]


def expand_types(tpe: type) -> type:
    args = tpe.__args__
    return (
        tpe
        if args is None
        else expand_types()
    )


class FooSpec:
    '''
    foo $foo
    '''

    def foo(self) -> Expectation:
        t = FooRiboState[str, int]
        o1 = t.__origin__
        o2 = o1.__origin__
        o3 = o2.__origin__
        # print(t)
        # print(t.__args__)
        # print(o1.__args__)
        # print(o2.__args__)
        # print(o3.__args__)
        return k(1) == 1


__all__ = ('FooSpec',)

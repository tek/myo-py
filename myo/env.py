from amino import _, List, Nil, Either, Maybe
from amino.dat import Dat

from myo.util import Ident
from myo.data.command import Command, TestLineParams


class Env(Dat['Env']):

    @staticmethod
    def cons(
            test_params: TestLineParams=None,
    ) -> 'Env':
        return Env(Maybe.optional(test_params))

    def __init__(
            self,
            test_params: Maybe[TestLineParams],
    ) -> None:
        self.test_params = test_params

__all__ = ('Env',)

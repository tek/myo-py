from amino import _, List, Nil, Either, Maybe
from amino.dat import Dat

from myo.util import Ident
from myo.data.command import Command, TestLineParams, HistoryEntry


class Env(Dat['Env']):

    @staticmethod
    def cons(
            test_params: TestLineParams=None,
            history: List[HistoryEntry]=Nil,
    ) -> 'Env':
        return Env(Maybe.optional(test_params), history)

    def __init__(
            self,
            test_params: Maybe[TestLineParams],
            history: List[HistoryEntry]=Nil,
    ) -> None:
        self.test_params = test_params
        self.history = history

__all__ = ('Env',)

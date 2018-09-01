from kallikrein import k, Expectation
from kallikrein.matchers.either import be_right

from amino.test.spec import SpecBase
from amino import Dat, do, Either, Do
from amino.json import dump_json, decode_json

from chiasma.util.id import Ident, StrIdent


class A(Dat['A']):

    def __init__(self, id: Ident) -> None:
        self.id = id


@do(Either[str, Expectation])
def ident_spec(a: A) -> Do:
    json = yield dump_json(a)
    yield decode_json(json)


class JsonSpec(SpecBase):
    '''
    codec an Ident $ident
    '''

    def ident(self) -> Expectation:
        a = A(StrIdent('a'))
        return k(ident_spec(a)).must(be_right(a))


__all__ = ('JsonSpec',)

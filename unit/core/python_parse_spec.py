from myo.output.parser.python import Parser, FileEntry, PyErrorEntry

from unit._support.spec import UnitSpec

from kallikrein import Expectation, k
from kallikrein.matchers import contain
from kallikrein.matchers.length import have_length

from amino import List, _, __

_errmsg = 'error 23'

trace = '''Traceback (most recent call last):
  File "/path/to/file", line 23, in funcname
    yield
  File "/path/to/file", line 23, in funcname
    yield
RuntimeError: {err}

Cause:
  File "/path/to/file", line 23, in funcname
    yield
  File "/path/to/file", line 23
    wrong =
           ^
SyntaxError: {err}

trailing garbage
'''.format(err=_errmsg)


class PythonParseSpec(UnitSpec):
    '''parse python stack trace $parse
    '''

    def parse(self) -> Expectation:
        parser = Parser()
        e = parser.events(List.lines(trace))
        e.should.have.length_of(2)
        en = e.head / _.entries
        en2 = e.last / _.entries | List()
        return (
            k(en / _.length).must(contain(3)) &
            k(en / __.map(type)).must(contain(List(FileEntry, FileEntry, PyErrorEntry))) &
            k(en // _.last / _.error).must(contain(_errmsg)) &
            (k(e.head // __.lines.lift(2) / _.target) == (en // _.head)) &
            k(en2).must(have_length(4))
        )

__all__ = ('PythonParseSpec',)

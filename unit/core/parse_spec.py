from myo.output.parser.python import Parser, FileEntry
from myo.output.data import ErrorEntry

from unit._support.spec import UnitSpec

from amino import List, _, __

_errmsg = 'error 23'

trace = '''
Traceback (most recent call last):
  File "/path/to/file", line 23, in funcname
    yield
  File "/path/to/file", line 23, in funcname
    yield
RuntimeError: {err}

Cause:
  File "/path/to/file", line 23, in funcname
    yield
  File "/path/to/file", line 23, in funcname
    yield
RuntimeError: {err}

trailing garbage
'''.format(err=_errmsg)


class ParseSpec(UnitSpec):

    def python(self):
        parser = Parser()
        e = parser.events(List.lines(trace))
        e.should.have.length_of(2)
        (e.head / _.entries.length).should.contain(3)
        (e.head / __.entries.map(type)).should.contain(
            List(FileEntry, FileEntry, ErrorEntry))
        (e.head // _.entries.last / _.msg).should.contain(_errmsg)

__all__ = ('ParseSpec',)

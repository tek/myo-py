from myo.output.parser.python import Parser, FileEntry, PyErrorEntry

from unit._support.spec import UnitSpec

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

    def parse(self):
        parser = Parser()
        e = parser.events(List.lines(trace))
        e.should.have.length_of(2)
        en = e.head / _.entries
        (en / _.length).should.contain(3)
        (en / __.map(type)).should.contain(
            List(FileEntry, FileEntry, PyErrorEntry))
        (en // _.last / _.error).should.contain(_errmsg)
        (e.head // __.lines.lift(2) / _.target).should.equal(en // _.head)
        en2 = e.last / _.entries | List()
        en2.should.have.length_of(4)

__all__ = ('PythonParseSpec',)

from myo.output.parser.sbt import Parser, FileEntry, ColEntry
from myo.output.data import ErrorEntry

from unit._support.spec import UnitSpec

from amino import List, _, __

_errmsg = 'error 23'

trace = '''
[info] Compiling 1 Scala source to /path/to/file...
[error] /path/to/file.scala:69: not found: value codeLine
[error]     codeLine
[error]     ^
[error] path/to/file.scala:71: {err};
[error]  found   : WrongType
[error]     (which expands to)  ReallyWrongType
[error]  required: CorrectType
[error]       codeLine
[error]           ^
[error] one error found
[error] (compile:compileIncremental) Compilation failed
[error] Total time: 0 s, completed Jan 1, 1900 00:00:00 AM
>
'''.format(err=_errmsg)


class SbtParseSpec(UnitSpec):

    def parse(self):
        parser = Parser()
        e = parser.events(List.lines(trace))
        e.should.have.length_of(2)
        (e / _.entries.length).should.equal(List(3, 6))
        (e.head / __.entries.map(type)).should.contain(
            List(FileEntry, ErrorEntry, ColEntry))
        (e.last // _.entries.head / _.error).should.contain(_errmsg)

__all__ = ('SbtParseSpec',)

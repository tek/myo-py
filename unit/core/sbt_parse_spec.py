from myo.output.parser.sbt import Parser, FileEntry, ColEntry, CodeEntry
from myo.output.data import ParseResult

from unit._support.spec import UnitSpec

from amino import List, _, __

_errmsg = 'error 23'
_line = 23
_col = 3

trace = '''
[info] Compiling 1 Scala source to /path/to/file...
[error] /path/to/file.scala:{line}: not found: value codeLine
[error]     codeLine
[error] {col}^
[error] path/to/file.scala:71: {err};
[error]  found   : WrongType
[error]     (which expands to)  ReallyWrongType
[error]  required: CorrectType
[error]       codeLine
[error]           ^
[error] two errors found
[error] (compile:compileIncremental) Compilation failed
[error] Total time: 0 s, completed Jan 1, 1900 00:00:00 AM
>
'''.format(err=_errmsg, line=_line, col=' ' * (_col))


class SbtParseSpec(UnitSpec):

    def parse(self):
        parser = Parser()
        e = parser.events(List.lines(trace))
        e.should.have.length_of(2)
        (e / _.entries.length).should.equal(List(3, 6))
        (e.head / __.entries.map(type)).should.contain(
            List(FileEntry, CodeEntry, ColEntry))
        (e.last // _.entries.head / _.error).should.contain(_errmsg)
        res = ParseResult(head=List('head'), events=e)
        (res.lines.lift(1) / _.target).should.equal(e.head)
        (e.head / _.coords).should.contain((_line, _col))

__all__ = ('SbtParseSpec',)

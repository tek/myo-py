from myo.output.parser.sbt import Parser, FileEntry, ColEntry, CodeEntry
from myo.output.data import ParseResult

from unit._support.spec import UnitSpec

from kallikrein import Expectation, k
from kallikrein.matchers.length import have_length
from kallikrein.matchers import contain

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
    '''parse sbt output $parse
    '''

    def parse(self) -> Expectation:
        parser = Parser()
        e = parser.events(List.lines(trace))
        res = ParseResult(head=List('head'), events=e)
        return (
            k(e).must(have_length(2)) &
            (k(e / _.entries.length) == List(3, 6)) &
            k(e.head / __.entries.map(type)).must(contain(List(FileEntry, CodeEntry, ColEntry))) &
            k(e.last // _.entries.head / _.error).must(contain(_errmsg)) &
            (k(res.lines.lift(1) / _.target) == e.head) &
            k(e.head / _.coords).must(contain((_line, _col)))
        )

__all__ = ('SbtParseSpec',)

from myo.output.syntax.base import OutputSyntax
from myo.output.data import ErrorEntry
from myo.output.parser.sbt import FileEntry

from amino import Task, Map, _


class Syntax(OutputSyntax):

    def __init__(self, vim, syntax) -> None:
        super().__init__(vim)
        self.syntax = syntax

    @property
    def _handlers(self):
        return Map({
            ErrorEntry: self._error,
            FileEntry: self._file,
        })

    def __call__(self, lines):
        return (lines.with_index.flat_map2(self._line)).sequence(Task)

    def _line(self, index, line):
        def run(entry):
            return (
                self._handlers.get(type(entry)) /
                (lambda a: a(index, line, entry))
            )
        return line.entry // run

    def _line_re(self, index, rest='.*'):
        return '\%{}l{}'.format(index + 1, rest)

    def _whole_line_re(self, index, rest='.*'):
        return '^{}$'.format(self._line_re(index, rest))

    def _match(self, grp, rex):
        return Task.call(self.syntax.match, grp, rex)

    def _match_line(self, grp, index):
        return self._match(grp, self._whole_line_re(index))

    def _error(self, index, line, entry):
        col = line.target.col / _.col | 1
        rex = '\%{}c.'.format(col)
        return (
            self._match_line('Error', index) +
            Task.call(self.syntax.match, 'ErrorMsg', self._line_re(index, rex),
                      containedin='Error')
        )

    def _file(self, index, line, entry):
        path = '^{}'.format(self._line_re(index, '\S\+'))
        line = self._line_re(index, ' \zs\d\+')
        return self._match('Directory', path) + self._match('Directory', line)

__all__ = ('Syntax',)

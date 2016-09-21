from myo.output.syntax.base import OutputSyntax

from amino import Task, Map


class Syntax(OutputSyntax):

    @property
    def _handlers(self):
        return Map({
        })

    def __call__(self, lines):
        return ((lines.with_index.flat_map2(self._line)).sequence(Task) +
                self._file + self._error + self._highlight)

    def _line(self, index, line):
        def run(entry):
            return (
                self._handlers.get(type(entry)) /
                (lambda a: a(index, line, entry))
            )
        return line.entry // run

    @property
    def _file(self):
        path = '.\+\ze '
        line = ' \zs\d\+\ze'
        fun = '\( \d\+ \)\@<=\zs.*'
        return (
            self._cont('Directory', path, 'MyoFile') +
            self._cont('Directory', line, 'MyoFile') +
            self._cont('Function', fun, 'MyoFile')
        )

    @property
    def _error(self):
        exc = '^\S\+'
        msg = '\({} \)\@<=\zs.*'.format(exc)
        return (self._cont('Exception', exc, 'MyoPyError') +
                self._cont('Error', msg, 'MyoPyError'))

    @property
    def _highlight(self):
        return (self._hi('Exception', ctermfg=2) +
                self._hi('Function', ctermfg=2))

__all__ = ('Syntax',)

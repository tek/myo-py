from myo.output.syntax.base import OutputSyntax


class Syntax(OutputSyntax):

    def __call__(self, lines):
        return self._file + self._error + self._highlight

    @property
    def _file(self):
        path = '.\+\ze '
        line = ' \zs\d\+\ze'
        fun = '\( \d\+ \)\@<=\zs.*'
        return (
            self._cont('MyoPath', path, 'MyoFile') +
            self._cont('MyoPath', line, 'MyoFile') +
            self._cont('MyoFunction', fun, 'MyoFile')
        )

    @property
    def _error(self):
        exc = '^\S\+'
        msg = '\({} \)\@<=\zs.*'.format(exc)
        return (self._cont('MyoException', exc, 'MyoPyError') +
                self._cont('MyoError', msg, 'MyoPyError'))

    @property
    def _highlight(self):
        return (
            self._hi('MyoException', ctermfg=2) +
            self._hi('MyoFunction', ctermfg=2) +
            self._hi('MyoCode', ctermfg=6)
        )

__all__ = ('Syntax',)

import abc

from amino import Task
from amino.lazy import lazy

from ribosome.nvim.components import Syntax
from ribosome.util.callback import VimCallback


class OutputSyntax(VimCallback):

    @lazy
    def syntax(self):
        return Syntax(self.target)

    def _line_re(self, index, rest='.*'):
        return '\%{}l{}'.format(index + 1, rest)

    def _whole_line_re(self, index, rest='.*'):
        return '^{}$'.format(self._line_re(index, rest))

    def _match(self, grp, rex, *a, **kw):
        return Task.call(self.syntax.match, grp, rex, *a, **kw)

    def _match_line(self, grp, index, *a, **kw):
        return self._match(grp, self._whole_line_re(index), *a, **kw)

    def _cont(self, grp, rex, cont):
        return self._match(grp, rex, 'contained', containedin=cont)

    def _link(self, left, right):
        return Task.call(self.syntax.link, left, right)

    def _hi(self, grp, *a, **kw):
        return Task.call(self.syntax.highlight, grp, *a, **kw)


class SimpleSyntax(OutputSyntax):

    def __call__(self, lines):
        return Task.call(self.syntax, lines)

    @abc.abstractmethod
    def syntax(self, lines):
        ...


class LineGroups(OutputSyntax):

    def __call__(self, lines):
        'transparent'
        return ((lines.with_index.map2(self._line)).sequence(Task) +
                self._highlight)

    def _line(self, index, line):
        def run(grp):
            prefixed = '{}{}'.format('Myo', grp)
            return self._match_line(prefixed, index)
        return line.syntax_group / run | Task.zero

    @property
    def _highlight(self):
        return (
            self._link('MyoError', 'Error') +
            self._link('MyoPath', 'Directory')
        )

__all__ = ('OutputSyntax', 'SimpleSyntax')

from integration._support.command import CmdSpec

from ribosome.test.integration.klk import later

from kallikrein import kf
from amino import List


class ShowSpec(CmdSpec):

    @property
    def _plugins(self):
        return super()._plugins.cat('integration._support.plugins.dummy')

    def _set_vars(self) -> None:
        super()._set_vars()
        self.vim.vars.set_p('tmux_use_defaults', False)

    def commands(self) -> None:
        langs = List('python', 'nvim')
        parser = 'py:foo.bar'
        shell = 'py'
        target = List(
            'SC <test>',
            'S py: ⎡langs -> {}⎤'.format(langs.mk_string(',')),
            'SC test: ⎡parser -> {}⎤ ∘ ⎡shell -> {}⎤'.format(parser, shell),
        )
        self.json_cmd_sync('MyoShell {}'.format(shell), line='python',
                           langs=langs)
        self._create_command('test', 'print(1)', shell=shell, parser=parser)
        self.vim.cmd_sync('MyoCommandShow')
        check = lambda: self._log_out.should.equal(target)
        later(check)

    def history(self) -> None:
        langs = List('python', 'nvim')
        parser = 'py:foo.bar'
        shell = 'py'
        target = List(
            'SC test: ⎡parser -> py:foo.bar⎤ ∘ ⎡shell -> py⎤',
            'S py: ⎡langs -> python,nvim⎤'
        )
        self.json_cmd_sync('MyoShell {}'.format(shell), line='python',
                           langs=langs)
        self._create_command('test', 'print(1)', shell=shell, parser=parser)
        self.vim.cmd_sync(f'MyoRun {shell}')
        self.vim.cmd_sync('MyoRun test')
        self._wait(1)
        self.vim.cmd_sync('MyoCommandHistoryShow')
        return later(kf(lambda: self._log_out) == target)

__all__ = ('ShowSpec',)

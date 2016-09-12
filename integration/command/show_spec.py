from integration._support.command import CmdSpec

from amino.test import later
from amino import List


class ShowSpec(CmdSpec):

    def _set_vars(self):
        super()._set_vars()
        self.vim.vars.set_p('tmux_use_defaults', False)

    def output(self):
        langs = List('python', 'nvim')
        parser = 'py:foo.bar'
        shell = 'py'
        target = List(
            'S py: ⎡langs -> {}⎤'.format(langs.mk_string(',')),
            'SC test: ⎡parser -> {}⎤ ∘ ⎡shell -> {}⎤'.format(parser, shell),
        )
        self.json_cmd_sync('MyoShell {}'.format(shell), line='python',
                           langs=langs)
        self.json_cmd_sync('MyoShellCommand test', line='print(1)',
                           shell=shell, parser=parser)
        self.vim.cmd_sync('MyoCommandShow')
        check = lambda: self._log_out.should_not.equal(target)
        later(check)

__all__ = ('ShowSpec',)

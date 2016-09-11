from integration._support.command import CmdSpec

from amino.test import later


class DispatchSpec(CmdSpec):

    def autocmd(self):
        name = 'test'
        self.vim.autocmd('User', 'MyoRunCommand',
                         'let g:c = g:myo_last_command.name').run_sync()
        self.json_cmd('MyoShellCommand {}'.format(name), line='')
        self.vim.cmd_sync('MyoRun {}'.format(name))
        later(lambda: self.vim.var('c').should.contain(name))

__all__ = ('DispatchSpec',)

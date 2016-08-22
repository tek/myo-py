from integration._support.tmux import TmuxCmdSpec

from psutil import Process
from amino.test import later


class DispatchSpec(TmuxCmdSpec):

    def simple(self):
        target = 'cmd test'
        self.json_cmd('MyoShellCommand test', line="echo '{}'".format(target))
        self.json_cmd('MyoTmuxOpenPane make')
        self.json_cmd('MyoRun test', pane='make')
        self._output_contains(target)

    def _shell(self, create):
        s = 'cmd test {}'
        i = 5342
        target = s.format(i)
        line = 'print(\'{}\'.format(\'{}\'))'.format(s, i)
        self.json_cmd('MyoTmuxCreatePane py', parent='main')
        self.json_cmd('MyoShell py', line='python', target='py')
        create(line)
        self._output_contains(target)

    def run_in_shell(self):
        def create(line):
            self.json_cmd('MyoRun py')
            self.json_cmd('MyoRunInShell py', line=line)
        self._shell(create)

    def kill_shell_command(self):
        def create(line):
            self.json_cmd('MyoShellCommand test', line=line, shell='py')
            self.json_cmd('MyoRun test')
        def pid():
            expr = '''data.pane("py") // (lambda a: a.pid) | -1'''
            return self.vim.call('MyoTmuxEval', expr) | -2
        self._shell(create)
        later(lambda: pid().should.be.greater_than(0))
        Process(pid()).kill()
        later(lambda: pid().should.equal(-1))

__all__ = ('DispatchSpec',)

from integration._support.tmux import TmuxCmdSpec

from psutil import Process
from amino.test import later

_test_line = 'this is a test'


def _test_ctor():
    return 'echo \'{}\''.format(_test_line)


def _test_shell_ctor():
    return 'print(\'{}\')'.format(_test_line)


class DispatchSpec(TmuxCmdSpec):

    def simple(self):
        target = 'cmd test'
        self.json_cmd('MyoShellCommand test', line="echo '{}'".format(target))
        self.json_cmd('MyoTmuxOpenPane make')
        self.json_cmd('MyoRun test')
        self._output_contains(target)

    def _create_shell(self):
        self.json_cmd('MyoTmuxCreatePane py', parent='main')
        self.json_cmd('MyoShell py', line='python', target='py')

    def _shell(self, create):
        s = 'cmd test {}'
        i = 5342
        target = s.format(i)
        line = 'print(\'{}\'.format(\'{}\'))'.format(s, i)
        self._create_shell()
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

    def pvar_test_target(self):
        self.vim.buffer.set_pvar('test_target', 'test')
        self.json_cmd_sync('MyoTmuxCreatePane test', parent='main')
        self.json_cmd_sync('MyoTest',
                           ctor='py:integration.tmux.dispatch_spec._test_ctor')
        self._pane_count(3)

    def pvar_test_shell(self):
        self.vim.buffer.set_pvar('test_shell', 'py')
        ctor = 'py:integration.tmux.dispatch_spec._test_shell_ctor'
        self._create_shell()
        self.json_cmd_sync('MyoTest', ctor=ctor)
        self._output_contains(_test_line)

    def nostart(self):
        self.json_cmd('MyoTmuxCreatePane py', parent='main')
        self.json_cmd('MyoShell py', line='python', target='py', start=False)
        self._wait(0.2)
        self._pane_count(1)

    def start(self):
        self.json_cmd('MyoTmuxCreatePane py', parent='main')
        self.json_cmd('MyoShell py', line='python', target='py', start=True)
        self._pane_count(2)

__all__ = ('DispatchSpec',)

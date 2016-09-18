from integration._support.tmux import TmuxCmdSpec

from psutil import Process
from amino.test import later
from amino import __, _

_test_line = 'this is a test'


def _test_ctor():
    return 'echo \'{}\''.format(_test_line)


def _test_shell_ctor():
    return 'print(\'{}\')'.format(_test_line)


class DispatchSpec(TmuxCmdSpec):

    def simple(self):
        target = 'cmd test'
        self.json_cmd('MyoShellCommand test', line="echo '{}'".format(target))
        self._open_pane('make')
        self.json_cmd('MyoRun test')
        self._output_contains(target)

    def _shell(self, create):
        s = 'cmd test {}'
        i = 5342
        target = s.format(i)
        line = 'print(\'{}\'.format(\'{}\'))'.format(s, i)
        self._py_shell()
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
        self.vim.buffer.vars.set_p('test_target', 'test')
        self._create_pane('test', parent='main')
        self.json_cmd_sync('MyoTest',
                           ctor='py:integration.tmux.dispatch_spec._test_ctor')
        self._pane_count(3)

    def pvar_test_shell(self):
        self.vim.buffer.vars.set_p('test_shell', 'py')
        ctor = 'py:integration.tmux.dispatch_spec._test_shell_ctor'
        self._py_shell()
        self.json_cmd_sync('MyoTest', ctor=ctor)
        self._output_contains(_test_line)

    def nostart(self):
        self._create_pane('py', parent='main')
        self.json_cmd('MyoShell py', line='python', target='py', start=False)
        self._wait(0.2)
        self._pane_count(1)

    def start(self):
        self._create_pane('py', parent='main')
        self.json_cmd('MyoShell py', line='python', target='py', start=True)
        self._pane_count(2)

    def quit_copy_mode(self):
        def copy_mode(v):
            later(lambda: (self._panes.last / _.in_copy_mode)
                  .should.contain(v))
        target = 'cmd test'
        self.json_cmd('MyoShellCommand test', line="echo '{}'".format(target))
        self._open_pane('make')
        later(lambda: self._pane_count(2))
        self._panes.last / __.cmd('copy-mode')
        copy_mode(True)
        self.json_cmd('MyoRun test')
        copy_mode(False)
        self._output_contains(target)

    def kill_process(self):
        pid = lambda: self._panes.last // _.command_pid | 0
        self.json_cmd('MyoShellCommand test', line='tee', kill=True,
                      signals=['int'])
        self.vim.cmd_sync('MyoRun test')
        later(lambda: pid().should.be.greater_than(0))
        pid1 = pid()
        self.vim.cmd_sync('MyoRun test')
        later(lambda: pid().should.be.greater_than(0))
        later(lambda: pid().should_not.equal(pid1))

__all__ = ('DispatchSpec',)

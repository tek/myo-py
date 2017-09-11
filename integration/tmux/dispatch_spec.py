from psutil import Process
from typing import Tuple, Callable

from ribosome.test.integration.klk import later

from kallikrein import Expectation, kf, k
from kallikrein.matchers.comparison import greater, not_equal, eq
from kallikrein.matchers import contain
from amino import __, _, List, Just, Maybe

from ribosome.util.callback import VimCallback

from integration._support.tmux import TmuxCmdSpec

_test_line = 'this is a test'
_eval_args_line = 'test {} / {}'


def r() -> str:
    return List.random_string()


def _test_ctor() -> Maybe[str]:
    return Just('echo \'{}\''.format(_test_line))


def _test_shell_ctor() -> Maybe[str]:
    return Just('print(\'{}\')'.format(_test_line))


class EvalArgsCallback(VimCallback):

    def __call__(self, *args: Tuple[str, str]) -> Maybe[str]:
        a1, a2 = args
        return Just('echo \'{}\''.format(_eval_args_line.format(a1, a2)))


class DispatchSpec(TmuxCmdSpec):
    ''' dispatch tmux commands

    simple command in default pane `make` $simple
    run command in an explicitly specified pane $target_pane
    run a command in a shell $run_in_shell
    update pane pid when it was killed externally $kill_shell_command
    read target pane from variable $pvar_test_target
    read command shell from variable $pvar_test_shell
    don't autostart a shell if specified $nostart
    autostart a shell if specified $start
    quit active copy mode when running command $quit_copy_mode
    kill running process when running command $kill_process
    kill running process when dispatching in pane $pane_kill
    kill running process via command $manual_kill
    killing closed pane prints an error $kill_nonexisting
    evaluate a vim function for the command line $vim_eval_func
    pass args to the eval function $eval_args
    close and reopen pane with the reboot command $reboot
    '''

    def simple(self) -> Expectation:
        target = r()
        cmd = r()
        self._create_command(cmd, "echo '{}'".format(target))
        self._open_pane('make')
        self._run_command(cmd)
        return self._output_contains(target)

    def target_pane(self) -> Expectation:
        marker = r()
        pane = r()
        cmd = r()
        sz = 3
        self._open_pane('make')
        self._create_pane(pane, parent='main', fixed_size=sz)
        self._create_command(cmd, "echo '{}'".format(marker), target=pane)
        self._run_command(cmd)
        self._pane_count(3)
        self._pane_output_contains(2, marker)
        return self._height(2, sz)

    def _shell(self, create: Callable[[str], None]) -> Expectation:
        s = 'cmd test {}'
        i = 5342
        target = s.format(i)
        line = 'print(\'{}\'.format(\'{}\'))'.format(s, i)
        self._py_shell()
        self._wait(.1)
        create(line)
        return self._output_contains(target)

    def run_in_shell(self) -> Expectation:
        def create(line: str) -> Expectation:
            self.json_cmd_sync('MyoRun py')
            self.json_cmd_sync('MyoRunInShell py', line=line)
        return self._shell(create)

    def kill_shell_command(self) -> Expectation:
        def create(line: str) -> Expectation:
            self._create_command('test', line, shell='py')
            self.json_cmd('MyoRun test')
        def pid() -> int:
            expr = '''data.pane("py") // (lambda a: a.pid) | -1'''
            return self.vim.call('MyoTmuxEval', expr) | -2
        self._shell(create)
        later(kf(pid).must(greater(0)))
        Process(pid()).kill()
        return later(kf(pid) == -1)

    def pvar_test_target(self) -> Expectation:
        self.vim.buffer.vars.set_p('test_target', 'test')
        self._create_pane('test', parent='main')
        self.json_cmd_sync('MyoTest',
                           ctor='py:integration.tmux.dispatch_spec._test_ctor')
        return self._pane_count(3)

    def pvar_test_shell(self) -> Expectation:
        self.vim.buffer.vars.set_p('test_shell', 'py')
        ctor = 'py:integration.tmux.dispatch_spec._test_shell_ctor'
        self._py_shell()
        self.json_cmd_sync('MyoTest', ctor=ctor)
        return self._output_contains(_test_line)

    def nostart(self) -> Expectation:
        self._create_pane('py', parent='main')
        self.json_cmd('MyoShell py', line='python', target='py', start=False)
        self._wait(0.2)
        return self._pane_count(1)

    def start(self) -> Expectation:
        self._create_pane('py', parent='main')
        self.json_cmd('MyoShell py', line='python', target='py', start=True)
        return self._pane_count(2)

    def quit_copy_mode(self) -> Expectation:
        def copy_mode(v: bool) -> Expectation:
            return later(
                kf(lambda: self._panes.last / _.in_copy_mode).must(contain(v))
            )
        target = 'cmd test'
        self._create_command('test', "echo '{}'".format(target))
        self._open_pane('make')
        self._pane_count(2)
        self._panes.last / __.cmd('copy-mode')
        copy_mode(True)
        self.json_cmd('MyoRun test')
        copy_mode(False)
        return self._output_contains(target)

    def kill_process(self) -> Expectation:
        def pid() -> int:
            return self._panes.last // _.command_pid | 0
        self._create_command('test', 'tee', kill=True, signals=['int'])
        self.vim.cmd_sync('MyoRun test')
        pid()
        later(kf(pid).must(greater(0)))
        pid1 = pid()
        self.vim.cmd_sync('MyoRun test')
        self._wait(.5)
        later(kf(pid).must(greater(0)))
        return later(kf(pid).must(not_equal(pid1)))

    def pane_kill(self) -> Expectation:
        def pid() -> int:
            return self._panes.last // _.command_pid | 0
        self._create_command('test', 'tee', signals=['int'])
        self.json_cmd('MyoUpdate pane make', kill=True)
        self._open_pane('make')
        self._pane_count(2)
        self._panes.last / __.send_keys('tail')
        check = kf(pid).must(greater(0))
        later(check)
        pid1 = pid()
        self.vim.cmd_sync('MyoRun test')
        later(check)
        return kf(pid) == pid1

    def manual_kill(self) -> Expectation:
        self.vim.cmd_sync('MyoRunLine make tail')
        later(kf(
            lambda: self._output.exists(lambda a: 'tail' in a)).must(eq(True)))
        k(self._cmd_pid(1)).must(greater(0))
        self.vim.cmd('MyoTmuxKill make')
        return later(kf(self._cmd_pid, 1) == 0)

    def kill_nonexisting(self) -> Expectation:
        self.vim.cmd('MyoTmuxKill make')
        return self._log_contains('pane not found: make')

    def vim_eval_func(self) -> Expectation:
        text = r()
        name = 'test'
        func = 'TestLine'
        callback = 'vim:{}'.format(func)
        cmd = 'echo "{}"'.format(text)
        self.vim.cmd_sync(
            '''function {}()
            return '{}'
            endfunction'''.format(func, cmd))
        self._create_command(name, callback, eval=True)
        self.json_cmd_sync('MyoRun {}'.format(name))
        return self._output_contains(text)

    def eval_args(self) -> Expectation:
        name = 'test'
        line = 'py:integration.tmux.dispatch_spec.EvalArgsCallback'
        args = List(r(), r())
        self._create_command(name, line, args=args, eval=True)
        self.json_cmd_sync('MyoRun {}'.format(name))
        text = _eval_args_line.format(*args)
        return self._output_contains(text)

    def reboot(self) -> Expectation:
        line = List.random_string()
        self._py_shell()
        self._run_command('py')
        self.json_cmd_sync('MyoRunInShell py', line='print(\'{}\')'.format(line))
        self._pane_output_contains(1, line)
        self.json_cmd_sync('MyoRebootCommand py')
        return self._pane_output_contains_not(3, line)

__all__ = ('DispatchSpec',)

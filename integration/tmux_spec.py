import re
from psutil import Process

from amino import List, _, Maybe, __
from amino.test import later
from amino.test.path import fixture_path, base_dir

from myo.output import ParseResult, OutputEvent, OutputEntry

from integration._support.base import TmuxIntegrationSpec
from integration._support.vimtest import vimtest
from integration._support.command import CmdSpec


class _TmuxSpec(TmuxIntegrationSpec):

    @property
    def _plugins(self):
        self._debug = True
        return super()._plugins.cons('myo.plugins.tmux')


class CutSizeSpec(_TmuxSpec):

    def cut_size(self):
        def check():
            panes = self.sessions.head // _.windows.head / _.panes | List()
            panes.should.have.length_of(2)
        self.json_cmd('MyoTmuxCreatePane pan', parent='root', min_size=0.5,
                      weight=0.1)
        self.json_cmd('MyoTmuxOpenPane pan')
        later(check)


class DistributeSizeSpec(_TmuxSpec):

    def distribute(self):
        h1 = 7
        def check():
            panes = self.sessions.head // _.windows.head / _.panes | List()
            sizes = panes[1:] / _.size / _[1]
            sizes.head.should.contain(h1)
        self.json_cmd('MyoTmuxCreateLayout test', parent='root')
        self.json_cmd('MyoTmuxCreatePane pan1', parent='test', min_size=5,
                      max_size=h1, weight=1)
        self._wait(.1)
        self.json_cmd('MyoTmuxCreatePane pan2', parent='test', min_size=10,
                      max_size=40, weight=9)
        self._wait(.1)
        self.json_cmd('MyoTmuxOpenPane pan1')
        self._wait(.1)
        self.json_cmd('MyoTmuxOpenPane pan2')
        later(check)


class _DefaultLayoutSpec(_TmuxSpec):

    def _set_vars(self):
        super()._set_vars()
        self.vim.set_pvar('tmux_use_defaults', True)


class DistributeSize2Spec(_DefaultLayoutSpec):

    def _set_vars(self):
        super()._set_vars()
        self.vim_width = 10
        self.vim.set_pvar('tmux_vim_width', self.vim_width)

    def distribute(self):
        def check():
            widths = self.sessions.head // _.windows // _.panes / _.size[0]
            target = List(self.vim_width, self.win_width - self.vim_width)
            widths.should.equal(target)
        self.json_cmd('MyoTmuxOpenPane make')
        later(check)


class ClosePaneSpec(_DefaultLayoutSpec):

    def _check(self, length: int):
        def go():
            panes = self.sessions.head // _.windows // _.panes
            panes.should.have.length_of(length)
        return later(go)

    def close(self):
        self.json_cmd('MyoTmuxOpenPane make')
        self._check(2)
        self.vim.cmd('MyoTmuxClosePane make')
        self._check(1)
        self.vim.cmd('MyoTmuxClosePane make')
        self._wait(0.1)
        self._check(1)
        self.json_cmd('MyoTmuxOpenPane make')
        self._check(2)
        self.vim.cmd('MyoTmuxClosePane make')
        self._check(1)

    def auto_close(self):
        self.json_cmd('MyoTmuxOpenPane make')
        self._check(2)
        self.vim.doautocmd('VimLeave')
        self._check(1)


class _TmuxCmdSpec(_TmuxSpec, CmdSpec):

    def _set_vars(self):
        super()._set_vars()
        self.vim.set_pvar('tmux_use_defaults', True)
        self.vim.set_pvar('tmux_vim_width', 10)
        self.vim.set_pvar('tmux_watcher_interval', 0.1)


class DispatchSpec(_TmuxCmdSpec):

    def simple(self):
        s = 'cmd test'
        def check():
            panes = self.sessions.head // _.windows.head / _.panes | List()
            out = panes // _.capture
            out.should.contain(s)
        self.json_cmd('MyoShellCommand test', line="echo '{}'".format(s))
        self.json_cmd('MyoTmuxOpenPane make')
        self.json_cmd('MyoRun test', pane='make')
        later(check)

    def _shell(self, create):
        s = 'cmd test {}'
        i = 5342
        target = s.format(i)
        def check():
            panes = self.sessions.head // _.windows.head / _.panes | List()
            out = panes // _.capture
            out.should.contain(target)
        line = 'print(\'{}\'.format(\'{}\'))'.format(s, i)
        self.json_cmd('MyoTmuxCreatePane py', parent='main')
        self.json_cmd('MyoShell py', line='python', target='py')
        create(line)
        later(check)

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


class ShowSpec(_TmuxSpec):

    def output(self):
        def check():
            self._log_out.should_not.be.empty
        self.vim.cmd('MyoTmuxShow')
        later(check)

_parse_head = 'parsed output:'
_event_head = 'event 1:'


def _parse_echo(data):
    matcher = re.compile('^line (\d+)')
    matches = data / matcher.match // Maybe / __.group(1)
    entries = matches / (lambda a: OutputEntry(text='entry {}'.format(a)))
    event = OutputEvent(head=_event_head, entries=entries)
    return ParseResult(head=_parse_head, events=List(event))


class ParseSpec(_TmuxCmdSpec):

    def custom(self):
        l1 = 'line 1'
        lines = List(l1, 'line 2', 'line 3')
        s = lines.mk_string('\\n')
        heads = List(_parse_head, _event_head)
        target = heads + lines / __.replace('line', 'entry')
        def check1():
            panes = self.sessions.head // _.windows.head / _.panes | List()
            out = panes // _.capture
            out.should.contain(l1)
        check2 = lambda: self.vim.buffer.content.should.equal(target)
        self.json_cmd('MyoShellCommand test', line="echo '{}'".format(s),
                      target='make',
                      parser='py:integration.tmux_spec._parse_echo')
        self.json_cmd('MyoTmuxOpenPane make')
        self.json_cmd('MyoRun test')
        later(check1)
        self.json_cmd('MyoParse')
        later(check2)

_test_line = 'this is a test'


def _test_ctor():
    return 'echo \'{}\''.format(_test_line)


class VimTestSpec(_TmuxCmdSpec):

    def simple(self):
        self.json_cmd('MyoTest', ctor='py:integration.tmux_spec._test_ctor')
        self._wait(2)

    @vimtest
    def vimtest(self):
        fname = fixture_path('tmux', 'vim_test', 'test.py')
        target = str(fname.relative_to(base_dir().parent))
        def check():
            panes = self.sessions.head // _.windows.head / _.panes | List()
            out = panes // _.capture
            out.exists(lambda a: target in a).should.be.true
        self.vim.cmd_sync('noswapfile edit {}'.format(fname))
        self.vim.cursor(5, 0)
        self.json_cmd('MyoVimTest')
        later(check)

__all__ = ('CutSizeSpec', 'DistributeSizeSpec', 'DispatchSpec', 'ParseSpec',
           'ShowSpec', 'ClosePaneSpec', 'DistributeSize2Spec', 'VimTestSpec')

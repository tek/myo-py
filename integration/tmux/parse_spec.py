import re

from amino import Maybe, List, __
from amino.test import later
from amino.test.path import fixture_path, base_dir

from myo.output.data import OutputEntry, OutputEvent, ParseResult

from integration._support.tmux import TmuxCmdSpec
from integration._support.vimtest import vimtest

_parse_head = 'parsed output:'
_event_head = 'event 1:'


def _parse_echo(data):
    matcher = re.compile('^line (\d+)')
    matches = data / matcher.match // Maybe / __.group(1)
    entries = matches / (lambda a: OutputEntry(text='entry {}'.format(a)))
    event = OutputEvent(head=_event_head, entries=entries)
    return ParseResult(head=_parse_head, events=List(event))


class ParseSpec(TmuxCmdSpec):

    def custom(self):
        l1 = 'line 1'
        lines = List(l1, 'line 2', 'line 3')
        s = lines.mk_string('\\n')
        heads = List(_parse_head, _event_head)
        target = heads + lines / __.replace('line', 'entry')
        check2 = lambda: self.vim.buffer.content.should.equal(target)
        self.json_cmd('MyoShellCommand test', line="echo '{}'".format(s),
                      target='make',
                      parser='py:integration.tmux.parse_spec._parse_echo')
        self.json_cmd('MyoTmuxOpenPane make')
        self.json_cmd('MyoRun test')
        self._output_contains(l1)
        self.json_cmd('MyoParse')
        later(check2)

_test_line = 'this is a test'


def _test_ctor():
    return 'echo \'{}\''.format(_test_line)


class VimTestSpec(TmuxCmdSpec):

    @vimtest
    def vimtest(self):
        self.vim.set_var('test#python#runner', 'nose')
        fname = fixture_path('tmux', 'vim_test', 'test.py')
        target = str(fname.relative_to(base_dir().parent))
        def check1():
            self._output.exists(lambda a: target in a).should.be.true
        self.vim.cmd_sync('noswapfile edit {}'.format(fname))
        self.vim.cursor(5, 1)
        self.json_cmd('MyoVimTest')
        later(check1)
        target2 = 'RuntimeError: supernova'
        check2 = lambda: self.vim.buffer.content.last.should.contain(target2)
        self.json_cmd_sync('MyoParse', langs=['python'])
        later(check2)
        self.vim.cursor(6, 1)
        self.vim.cmd_sync('call feedkeys("\\<cr>")')
        check3 = lambda: self.vim.buffer.name.should.equal(str(fname))
        later(check3)

__all__ = ('ParseSpec',)

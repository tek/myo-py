import re

from amino import Maybe, List, __, _
from amino.test import later
from amino.test.path import fixture_path

from ribosome.machine import state

from myo.output.data import OutputEntry, OutputEvent, ParseResult
from myo.plugins.command.message import RunVimTest

from integration._support.tmux import TmuxCmdSpec
from integration._support.vimtest import vimtest

_parse_head = 'parsed output:'
_event_head = 'event 1:'


def _parse_echo(data):
    matcher = re.compile('^line (\d+)')
    matches = data / matcher.match // Maybe / __.group(1)
    entries = matches / (lambda a: OutputEntry(text='entry {}'.format(a)))
    event = OutputEvent(head=List(_event_head), entries=entries)
    return ParseResult(head=List(_parse_head), events=List(event))


class TmuxParseSpec(TmuxCmdSpec):

    def custom(self):
        l3 = 'line 3'
        lines = List('line 1', 'line 2', l3)
        s = lines.mk_string('\\n')
        heads = List(_parse_head, _event_head)
        target = heads + lines / __.replace('line', 'entry')
        self.json_cmd('MyoShellCommand com', line="echo '{}'".format(s),
                      target='make',
                      parser='py:integration.tmux.parse_spec._parse_echo')
        self._open_pane('make')
        self.json_cmd('MyoRun com')
        self._output_contains(l3)
        self.json_cmd('MyoParse')
        check = lambda: self.vim.buffer.content.should.equal(target)
        later(check)

    def shell(self):
        self.vim.vars.set_p('jump_to_error', False)
        self.vim.vars.set_p('lang_reifier', False)
        err = List.random_string()
        line = 'raise Exception(\'{}\')'.format(err)
        target = 'Exception: {}'.format(err)
        self._py_shell()
        self.json_cmd_sync('MyoShellCommand test', line=line, shell='py',
                           langs=['python'])
        self.json_cmd_sync('MyoRun test')
        self._output_contains(target)
        self.json_cmd_sync('MyoRun test')
        later(lambda: self._output.filter(_ == target).should.have.length_of(2)
              )
        self.json_cmd_sync('MyoParse')
        later(lambda: self.vim.buffer.content.should.have.length_of(3))


class PythonVimTestSpec(TmuxCmdSpec):

    @property
    def _fname(self):
        return fixture_path('tmux', 'vim_test', 'test.py')

    @property
    def _target(self):
        return 'RuntimeError: supernova'

    def _pre_start(self):
        self.vim.vars.set_p('tmux_no_watcher', True)
        self.vim.vars.set_p('jump_to_error', False)
        self.vim.vars.set('test#python#runner', 'nose')
        self.vim.vars.set_p('output_reifier',
                            'py:myo.output.reifier.base.LiteralReifier')
        super()._pre_start()
        self.vim.cmd_sync('noswapfile edit {}'.format(self._fname))
        self.vim.buffer.vars.set_p('test_langs', ['python'])

    def _run_test(self):
        check = lambda: self._output.should.contain(self._target)
        self.vim.cursor(4, 1)
        len_pre = self._output.length
        self.json_cmd('MyoVimTest')
        later(lambda: self._output.length.should.be.greater_than(len_pre))
        later(check)

    def _run_parse(self):
        check = lambda: self.vim.buffer.content.last.should.contain(
            self._target)
        self.json_cmd_sync('MyoParse')
        later(check)

    @vimtest
    def complete(self):
        self._run_test()
        self._run_parse()
        self.vim.cursor(6, 1)
        self.vim.cmd_sync('call feedkeys("\\<cr>")')
        check1 = lambda: self.vim.buffer.name.should.equal(str(self._fname))
        later(check1)
        self.vim.focus(1).run_sync()
        self.vim.cmd_sync('call feedkeys("q")')
        check2 = lambda: self.vim.buffers.should.have.length_of(1)
        later(check2)

    @vimtest
    def twice(self):
        self._run_test()
        self._run_parse()
        self.vim.window.close()
        self._run_test()
        self._run_parse()

__all__ = ('TmuxParseSpec', 'PythonVimTestSpec')

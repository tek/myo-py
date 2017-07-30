import re

from amino import Maybe, List, __, _, Path
from ribosome.test.integration.klk import later

from kallikrein import Expectation, kf
from kallikrein.matchers import contain
from kallikrein.matchers.length import have_length
from kallikrein.matchers.comparison import ge
from amino.test.path import fixture_path

from ribosome.record import encode_json

from myo.output.data import OutputEntry, OutputEvent, ParseResult
from myo.command import ShellCommand, TransientCommandJob

from integration._support.tmux import TmuxCmdSpec
from integration._support.vimtest import vimtest

_parse_head = 'parsed output:'
_event_head = 'event 1:'


def _parse_echo(data: List[str]) -> ParseResult:
    matcher = re.compile('^line (\d+)')
    matches = data / matcher.match // Maybe / __.group(1)
    entries = matches / (lambda a: OutputEntry(text='entry {}'.format(a)))
    event = OutputEvent(head=List(_event_head), entries=entries)
    return ParseResult(head=List(_parse_head), events=List(event))


class TmuxParseSpec(TmuxCmdSpec):
    '''parse output from a tmux pane
    custom python func as parser set by `parser` command option $custom
    parser output in a shell $shell
    '''

    def custom(self) -> Expectation:
        l3 = 'line 3'
        lines = List('line 1', 'line 2', l3)
        s = lines.mk_string('\\n')
        heads = List(_parse_head, _event_head)
        target = heads + lines / __.replace('line', 'entry')
        self._create_command(
            'com',
            "echo '{}'".format(s),
            target='make',
            parser='py:integration.tmux.parse_spec._parse_echo'
        )
        self._open_pane('make')
        self.json_cmd('MyoRun com')
        self._output_contains(l3)
        self.json_cmd('MyoParse')
        return self._buffer_content(target)

    def shell(self) -> Expectation:
        self.vim.vars.set_p('jump_to_error', False)
        self.vim.vars.set_p('lang_reifier', False)
        err = List.random_string()
        line = 'raise Exception(\'{}\')'.format(err)
        target = 'Exception: {}'.format(err)
        self._py_shell()
        self._create_command('test', line, shell='py', langs=['python'])
        self.json_cmd_sync('MyoRun test')
        self._output_contains(target)
        self.json_cmd_sync('MyoRun test')
        later(kf(lambda: self._output.filter(_ == target)).must(have_length(2)))
        self.json_cmd_sync('MyoParse')
        text = '  File "<stdin>", line 1, in <module>'
        return self._buffer_line(0, text)


class PythonVimTestBase(TmuxCmdSpec):

    @property
    def _fname(self) -> Path:
        return fixture_path('tmux', 'vim_test', 'test.py')

    @property
    def _target(self) -> str:
        return 'RuntimeError: supernova'

    def _set_vars(self) -> None:
        super()._set_vars()
        self.vim.vars.set_p('tmux_no_watcher', True)
        self.vim.vars.set_p('jump_to_error', False)
        self.vim.vars.set('test#python#runner', 'nose')
        self.vim.vars.set_p('output_reifier', 'py:myo.output.reifier.base.LiteralReifier')

    def _pre_start(self) -> None:
        super()._pre_start()
        self.vim.cmd_sync('noswapfile edit {}'.format(self._fname))
        self.vim.buffer.vars.set_p('test_langs', ['python'])

    def _check_test(self, len_pre: int) -> Expectation:
        later(kf(lambda: self._output.length).must(ge(len_pre)))
        return self._output_contains(self._target)

    def _run_test(self) -> Expectation:
        self.vim.cursor(4, 1)
        len_pre = self._output.length
        self.json_cmd('MyoVimTest')
        return self._check_test(len_pre)

    def _run_parse(self) -> Expectation:
        self.json_cmd_sync('MyoParse')
        return self._buffer_line(-1, contain(self._target))


class PythonVimTestSpec(PythonVimTestBase):
    '''run tests using the `vim-test` plugin
    complete process using vim key mappings $complete
    run tests twice in a row, closing the window in between $twice
    '''

    @vimtest
    def complete(self) -> Expectation:
        self._run_test()
        self._run_parse()
        self.vim.cursor(4, 1)
        self.vim.cmd_sync('call feedkeys("\\<cr>")')
        self._buffer_name(str(self._fname))
        self.vim.focus(1).run_sync()
        self.vim.cmd_sync('call feedkeys("q")')
        return self._buffer_count(1)

    @vimtest
    def twice(self) -> Expectation:
        self._run_test()
        self._run_parse()
        self.vim.window.close()
        self._run_test()
        return self._run_parse()


class PythonVimTestLoadHistorySpec(PythonVimTestBase):
    '''run a vim-test history job that was saved in the session $history
    '''

    @property
    def _line(self) -> str:
        return 'nosetests {}:Namespace.test_something'.format(self._fname)

    def _set_vars(self) -> None:
        super()._set_vars()
        cmd = ShellCommand(line='', name='<test>')
        job = TransientCommandJob(override_line=self._line,
                                  command=cmd,
                                  name='test_line_<test>_VIroI',
                                  override_langs=List('python'))
        history = encode_json([job]).get_or_raise
        self.vim.vars.set('Myo_history', history)

    @vimtest
    def history(self) -> Expectation:
        len_pre = self._output.length
        self.json_cmd('MyoRunLatest')
        self._check_test(len_pre)
        return self._run_parse()

__all__ = ('TmuxParseSpec', 'PythonVimTestSpec', 'PythonVimTestLoadHistorySpec')

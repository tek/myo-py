from kallikrein import Expectation, k
from kallikrein.matchers import contain
from kallikrein.matchers.lines import have_lines

from amino.test import fixture_path
from amino import List, Map, do, Do, Lists, IO, Just, Nil
from amino.test.spec import SpecBase

from ribosome.nvim.io.compute import NvimIO
from ribosome.test.rpc import json_cmd
from ribosome.nvim.io.api import N
from ribosome.test.integration.tmux import tmux_plugin_test
from ribosome.test.klk.matchers.buffer import current_buffer_contains
from ribosome.nvim.io.state import NS
from ribosome.compute.run import run_prog
from ribosome.compute.api import prog
from ribosome.nvim.api.command import nvim_command_output, nvim_command
from ribosome.test.integration.external import external_state_test

from myo import myo_config
from myo.settings import auto_jump
from myo.components.command.compute.parse_handlers import ParseHandlers
from myo.output.lang.scala.syntax import scala_syntax
from myo.output.lang.scala.report import scala_report, col_marker
from myo.components.command.compute.output import render_parse_result
from myo.components.command.compute.parsed_output import ParsedOutput
from myo.config.plugin_state import MyoState

from test.klk.tmux import pane_content_matches
from test.tmux import tmux_test_config
from test.output.scala import scala_output_events
from test.command import command_spec_test_config
from test.output.util import myo_syntax

vars = Map(
    myo_auto_jump=0,
)
test_config = tmux_test_config(config=myo_config, extra_vars=vars)


pane_ident = 'make'
file = fixture_path('tmux', 'scala_parse', 'errors')
statements = List(
    'import pathlib',
    f'''print(pathlib.Path('{file}').read_text())''',
)

target = f'''/path/to/file.scala  3
expected class or object definition
  {col_marker}name
/path/to/other_file.scala  7
terrible mistake
  x.{col_marker}otherName[Data]'''


@do(NvimIO[Expectation])
def parse_spec() -> Do:
    file_content = yield N.from_io(IO.delay(Lists.file, file))
    line = yield N.from_maybe(file_content.head, f'no content in fixture')
    yield json_cmd('MyoAddSystemCommand', ident='python', line='python', target=pane_ident)
    yield json_cmd('MyoLine', shell='python', lines=statements, langs=List('scala'))
    executed = yield pane_content_matches(contain(line), 1, timeout=10)
    yield json_cmd('MyoParse')
    return executed


@do(NvimIO[Expectation])
def report_spec() -> Do:
    executed = yield parse_spec()
    content = yield current_buffer_contains(target)
    yield N.sleep(3)
    return executed & content


target_syntax = '''MyoPath        xxx match /^.*\ze\( .*$\)\@=/  contained containedin=MyoLocation
MyoLineNumber  xxx match /\( \)\@<=\zs\d\+\ze/  contained containedin=MyoLocation
MyoError       xxx match /^.*$/  contained nextgroup=MyoCode skipwhite skipnl
MyoLocation    xxx match /^.*.*$/  contains=MyoPath,MyoLineNumber nextgroup=MyoError skipwhite skipnl
MyoCode        xxx match /^  .*$/  contained contains=@scala,MyoColMarker
MyoColMarker   xxx match /†/  contained conceal containedin=MyoCode nextgroup=MyoCol
MyoCol         xxx match /./  contained'''

target_highlight = '''MyoPath        xxx links to Directory
MyoLineNumber  xxx links to Directory
MyoError       xxx links to Error
MyoLocation    xxx cleared
MyoCode        xxx cleared
MyoColMarker   xxx cleared
MyoCol         xxx links to Search'''


@do(NS[MyoState, Expectation])
def syntax_spec() -> Do:
    yield NS.lift(auto_jump.update(False))
    parse_handlers = ParseHandlers.cons(syntax=Just(scala_syntax), reporter=Just(scala_report))
    yield run_prog(prog.result(render_parse_result), List(ParsedOutput(parse_handlers, Nil, scala_output_events)))
    syn = yield NS.lift(nvim_command_output('syntax'))
    hi = yield NS.lift(nvim_command_output('highlight'))
    return k(myo_syntax(syn)).must(have_lines(target_syntax)) & k(myo_syntax(hi)).must(have_lines(target_highlight))


class ScalaParseSpec(SpecBase):
    '''
    parse scala compiler errors
    report $report
    syntax $syntax
    '''

    def report(self) -> Expectation:
        return tmux_plugin_test(test_config, report_spec)

    def syntax(self) -> Expectation:
        return external_state_test(command_spec_test_config, syntax_spec)


__all__ = ('ScalaParseSpec',)

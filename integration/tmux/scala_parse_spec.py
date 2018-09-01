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
from ribosome.nvim.api.command import nvim_command
from ribosome.test.integration.external import external_state_test
from ribosome.nvim.api.option import option_set

from myo import myo_config
from myo.config.settings import auto_jump
from myo.components.command.compute.parse_handlers import ParseHandlers
from myo.output.lang.scala.syntax import scala_syntax
from myo.output.lang.scala.report import scala_report, col_marker, found_marker, separator_marker, req_marker
from myo.components.command.compute.output import render_parse_result
from myo.components.command.compute.parsed_output import ParsedOutput
from myo.config.plugin_state import MyoState

from test.klk.tmux import pane_content_matches
from test.tmux import tmux_test_config
from test.output.scala import scala_output_events
from test.command import command_spec_test_config
from test.output.util import myo_syntax, myo_highlight

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
  !I param: Type
  Foo.bar invalid because
  !I param2: Class
  {col_marker}implicitly[Class]
/path/to/file.scala  3
type mismatch
  Type[{found_marker}Int {separator_marker}| List[String]{req_marker}]
  func(†param)
/path/to/file.scala  3
type mismatch
  {found_marker}Vector[Int] {separator_marker}| List[String]{req_marker}
  func(†param)'''


@do(NvimIO[Expectation])
def parse_spec() -> Do:
    file_content = yield N.from_io(IO.delay(Lists.file, file))
    line = yield N.from_maybe(file_content.head, f'no content in fixture')
    yield json_cmd('MyoAddSystemCommand', ident='python', line='python', target=pane_ident)
    yield json_cmd('MyoLine', shell='python', lines=statements, langs=List('scala'))
    executed = yield pane_content_matches(contain(line), 1, timeout=10)
    yield json_cmd('MyoParse')
    return executed


@do(NvimIO[None])
def test_highlights() -> Do:
    yield nvim_command('highlight Error cterm=bold ctermfg=1')
    yield nvim_command('highlight Statement ctermfg=2')
    yield nvim_command('highlight Type ctermfg=3')
    yield nvim_command('highlight Search cterm=reverse ctermfg=3')


@do(NvimIO[Expectation])
def report_spec() -> Do:
    # yield test_highlights()
    yield option_set('splitbelow', True)
    executed = yield parse_spec()
    content = yield current_buffer_contains(target)
    return executed & content


target_syntax = '''MyoPath        xxx match /^.*\ze\( .*$\)\@=/  contained containedin=MyoLocation
MyoLineNumber  xxx match /\( \)\@<=\zs\d\+\ze/  contained containedin=MyoLocation
MyoError       xxx start=/^./ end=/\ze.*\(\|†\)/  contained contains=MyoSplain,MyoSplainFoundReq nextgroup=MyoCode skipwhite skipnl
MyoLocation    xxx match /^.*.*$/  contains=MyoPath,MyoLineNumber nextgroup=MyoError skipwhite skipnl
MyoCode        xxx match /.*/  contained contains=@scala,MyoColMarker
MyoSplain      xxx start=/\s*!I/ end=/\ze.*\(\|†\)/  contained contains=MyoSplainParam,MyoSplainCandidate nextgroup=MyoCode skipwhite skipnl
MyoSplainFoundReq xxx match /^.*+.\{-}< | .\{-}-.*$/  contained contains=MyoSplainFound,MyoSplainReq
MyoColMarker   xxx match /†/  contained conceal nextgroup=MyoCol
MyoCol         xxx match /./  contained
MyoSplainParam xxx match /^\s*!I.*/  contained contains=MyoSplainParamMarker containedin=MyoSplain
MyoSplainCandidate xxx match /\S\+\ze invalid because/  contained containedin=MyoSplain
MyoSplainParamMarker xxx match /!I/  contained contains=MyoSplainParamMarkerBang nextgroup=MyoSplainParamName
MyoSplainParamName xxx match /[^:]\+\ze:/  contained nextgroup=MyoSplainParamType
MyoSplainParamMarkerBang xxx match /!/  contained nextgroup=MyoSplainParamMarkerI
MyoSplainParamMarkerI xxx match /I/  contained nextgroup=MyoSplainParamName skipwhite
MyoSplainParamType xxx start=/./ end=/\ze.*\(invalid because\|†\)/  contained
MyoSplainFound xxx match /+.\{-}</  contained contains=MyoSplainFoundReqMarker nextgroup=MyoSplainReq
MyoSplainReq   xxx match / | \zs.\{-}\ze-/  contained nextgroup=MyoSplainFoundReqMarker
MyoSplainFoundReqMarker xxx match /+\|<\|-/  contained conceal'''

target_highlight = '''MyoPath        xxx links to Directory
MyoLineNumber  xxx links to Directory
MyoError       xxx links to Error
MyoLocation    xxx cleared
MyoCode        xxx cleared
MyoSplain      xxx cleared
MyoSplainFoundReq xxx cleared
MyoColMarker   xxx cleared
MyoCol         xxx links to Search
MyoSplainParam xxx cleared
MyoSplainCandidate xxx links to Error
MyoSplainParamMarker xxx cleared
MyoSplainParamName xxx links to Type
MyoSplainParamMarkerBang xxx links to Error
MyoSplainParamMarkerI xxx links to Directory
MyoSplainParamType xxx links to Statement
MyoSplainFound xxx links to Error
MyoSplainReq   xxx links to Statement
MyoSplainFoundReqMarker xxx cleared'''


@do(NS[MyoState, Expectation])
def syntax_spec() -> Do:
    yield NS.lift(auto_jump.update(False))
    parse_handlers = ParseHandlers.cons(syntax=Just(scala_syntax), reporter=Just(scala_report))
    yield run_prog(prog.result(render_parse_result), List(ParsedOutput(parse_handlers, Nil, scala_output_events)))
    syn = yield NS.lift(myo_syntax())
    hi = yield NS.lift(myo_highlight())
    return k(syn).must(have_lines(target_syntax)) & k(hi).must(have_lines(target_highlight))


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

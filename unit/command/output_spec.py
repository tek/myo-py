from kallikrein import k, Expectation
from kallikrein.matchers.lines import have_lines

from amino import do, Just, Do
from amino.test.spec import SpecBase

from test.output.python import output_events
from test.command import command_spec_test_config

from ribosome.nvim.io.state import NS
from ribosome.test.unit import unit_test

from myo.config.plugin_state import MyoState
from myo.components.command.compute.parse_handlers import ParseHandlers
from myo.output.lang.python.report import python_report
from myo.components.command.compute.output import parse_report
from myo.components.command.compute.parsed_output import ParsedOutput
from myo.output.data.report import format_report
from myo.output.format.path import project_relative_path


target_report = '''unit/_fixtures/command/parse/file.py  2 funcname
    yield
unit/_fixtures/command/parse/file.py  3 funcname
    yield
RuntimeError: error
unit/_fixtures/command/parse/file.py  6 funcname
    yield
unit/_fixtures/command/parse/file.py  7 funcname
    yield
SyntaxError: error
'''


@do(NS[MyoState, Expectation])
def reporter_spec() -> Do:
    parse_handlers = ParseHandlers.cons(reporter=Just(python_report), path_formatter=Just(project_relative_path))
    report = yield parse_report(ParsedOutput(parse_handlers, output_events, output_events))
    formatted = format_report(report)
    return k(formatted).must(have_lines(target_report))


class OutputSpec(SpecBase):
    '''
    python reporter $reporter
    '''

    def reporter(self) -> Expectation:
        return unit_test(command_spec_test_config, reporter_spec)


__all__ = ('OutputSpec',)

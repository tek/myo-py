from kallikrein import k, Expectation
from kallikrein.matchers.length import have_length
from kallikrein.matchers.either import be_right

from test.command import command_spec_test_config

from amino import Lists, do, Do
from amino.test.spec import SpecBase

from ribosome.nvim.io.state import NS
from ribosome.test.unit import unit_test

from myo.output.parser.scala import scala_parser
from myo.output.parser.base import parse_events
from myo.output.data.report import ParseReport
from myo.components.command.compute.output import report_line_number, parse_report
from myo.config.plugin_state import MyoState
from myo.components.command.compute.parsed_output import ParsedOutput
from myo.components.command.compute.parse_handlers import ParseHandlers

output = '''[error] /path/to/file.scala:3:1: expected class or object definition
[error] name
[error] ^
[error] /path/to/other_file.scala:7:2: terrible mistake
[error] x.otherName
[error]   ^
[error] one error found
'''
lines = Lists.lines(output)


@do(NS[MyoState, ParseReport])
def cons_report() -> Do:
    events = yield NS.e(parse_events(scala_parser, lines))
    output = ParsedOutput(ParseHandlers.cons(), events, events)
    yield parse_report(output)


@do(NS[MyoState, Expectation])
def error_spec() -> Do:
    report = yield cons_report()
    return k(report.lines).must(have_length(6))


@do(NS[MyoState, Expectation])
def line_number_spec() -> Do:
    report = yield cons_report()
    return k(report_line_number(1)(report)).must(be_right(3))


class ScalaParseSpec(SpecBase):
    '''
    parse a scala error $error
    find an output line for an event $event
    '''

    def error(self) -> Expectation:
        return unit_test(command_spec_test_config, error_spec)

    def event(self) -> Expectation:
        return unit_test(command_spec_test_config, line_number_spec)


__all__ = ('ScalaParseSpec',)

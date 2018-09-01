from kallikrein import k, Expectation
from kallikrein.matchers.length import have_length
from kallikrein.matchers.either import be_right
from kallikrein.matchers.lines import have_lines

from test.command import command_spec_test_config

from amino import Lists, do, Do
from amino.test.spec import SpecBase

from ribosome.nvim.io.state import NS
from ribosome.test.unit import unit_test

from myo.output.parser.scala import scala_parser
from myo.output.parser.base import parse_events
from myo.output.data.report import ParseReport, format_report
from myo.components.command.compute.output import report_line_number, parse_report
from myo.config.plugin_state import MyoState
from myo.components.command.compute.parsed_output import ParsedOutput
from myo.components.command.compute.parse_handlers import ParseHandlers
from myo.output.configs import scala_config
from myo.output.lang.scala.report import found_marker, separator_marker, req_marker

output = '''[error] /path/to/file.scala:3:1: expected class or object definition
[error] name
[error] ^
[error] /path/to/other_file.scala:7:2: terrible mistake
[error] !I param: Type
[error] Foo.bar invalid because
[error] !I param2: Class
[error]   implicitly[Class]
[error]   ^
[error] /path/to/file.scala:3:1: type mismatch
[error]   Type[Int | List[String]]
[error]   func(param)
[error]        ^
[error] one error found
'''
lines = Lists.lines(output)


@do(NS[MyoState, ParseReport])
def cons_report() -> Do:
    events = yield NS.e(parse_events(scala_parser, lines))
    config = yield NS.e(ParseHandlers.from_config(scala_config.parse))
    output = ParsedOutput(config, events, events)
    yield parse_report(output)


@do(NS[MyoState, Expectation])
def error_spec() -> Do:
    report = yield cons_report()
    return k(report.lines).must(have_length(13))


@do(NS[MyoState, Expectation])
def line_number_spec() -> Do:
    report = yield cons_report()
    return k(report_line_number(1)(report)).must(be_right(3))


target_report = f'''/path/to/file.scala  3
expected class or object definition
  †name
/path/to/other_file.scala  7
terrible mistake
  !I param: Type
  Foo.bar invalid because
  !I param2: Class
  †implicitly[Class]
/path/to/file.scala  3
type mismatch
  Type[{found_marker}Int {separator_marker}| List[String]{req_marker}]
  func(†param)'''


@do(NS[MyoState, Expectation])
def format_spec() -> Do:
    report = yield cons_report()
    formatted = format_report(report)
    return k(formatted).must(have_lines(target_report))


class ScalaParseSpec(SpecBase):
    '''
    parse a scala error $error
    find an output line for an event $event
    format a report $report
    '''

    def error(self) -> Expectation:
        return unit_test(command_spec_test_config, error_spec)

    def event(self) -> Expectation:
        return unit_test(command_spec_test_config, line_number_spec)

    def report(self) -> Expectation:
        return unit_test(command_spec_test_config, format_spec)


__all__ = ('ScalaParseSpec',)

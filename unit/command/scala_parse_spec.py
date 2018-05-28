from kallikrein import k, Expectation, kf
from kallikrein.matchers.length import have_length
from kallikrein.matchers.maybe import be_just
from kallikrein.matchers.either import be_right
from kallikrein.matchers.match_with import match_with

from amino import Lists, _, do, Either, Do
from amino.test.spec import SpecBase

from myo.output.parser.scala import scala_parser
from myo.output.parser.base import parse_events
from myo.output.data.report import parse_report, ParseReport
from myo.components.command.compute.output import report_line_number

output = '''[error] /path/to/file.scala:3:1: expected class or object definition
[error] name
[error] ^
[error] /path/to/other_file.scala:7:2: terrible mistake
[error] x.otherName
[error]   ^
[error] one error found
'''
lines = Lists.lines(output)


@do(Either[str, ParseReport])
def cons_report() -> Do:
    events = yield parse_events(scala_parser, lines)
    return parse_report(events)


@do(Either[str, Expectation])
def line_number_spec() -> Do:
    report = yield cons_report()
    line = yield report_line_number(1)(report)
    return k(line) == 3


class ScalaParseSpec(SpecBase):
    '''
    parse a scala error $error
    find an output line for an event $event
    '''

    def error(self) -> Expectation:
        return k(cons_report().map(lambda a: a.lines)).must(be_right(have_length(6)))

    def event(self) -> Expectation:
        return kf(line_number_spec).must(be_right(match_with(lambda a: a)))


__all__ = ('ScalaParseSpec',)

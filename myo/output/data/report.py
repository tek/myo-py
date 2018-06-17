from typing import TypeVar

from amino import Dat, List, ADT, do, Do, Maybe
from amino.state import State
from amino.case import Case

from myo.output.data.output import OutputEvent, OutputLine, Location

A = TypeVar('A')
B = TypeVar('B')


class DisplayLine(ADT['DisplayLine']):
    pass


class PlainDisplayLine(DisplayLine):

    def __init__(self, text: str) -> None:
        self.text = text


class SyntaxDisplayLine(DisplayLine):

    def __init__(self, text: str, syntax: str) -> None:
        self.text = text
        self.syntax = syntax


class ReportLine(ADT['ReportLine']):
    pass


class PlainReportLine(ReportLine):

    def __init__(self, text: str) -> None:
        self.text = text


class EventReportLine(ReportLine):

    @staticmethod
    def cons(
            line: DisplayLine,
            event: int,
            location: Location=None,
    ) -> 'EventReportLine':
        return EventReportLine(
            line,
            event,
            Maybe.optional(location),
        )

    def __init__(self, line: DisplayLine, event: int, location: Maybe[Location]) -> None:
        self.line = line
        self.event = event
        self.location = location


class ParseReport(Dat['ParseReport']):

    @staticmethod
    def cons(
            lines: List[ReportLine],
            event_indexes: List[int],
    ) -> 'ParseReport':
        return ParseReport(
            lines,
            event_indexes,
        )

    def __init__(self, lines: List[ReportLine], event_indexes: List[int]) -> None:
        self.lines = lines
        self.event_indexes = event_indexes


def output_line_report(line: OutputLine[A], event: int, location: Maybe[Location]) -> List[ReportLine]:
    return List(EventReportLine(line.text, event, location))


def event_report(index: int, event: OutputEvent[A, B]) -> List[ReportLine]:
    return (
        (event.head / PlainReportLine) +
        (event.lines.flat_map(lambda a: output_line_report(a, index, event.location)))
    )


@do(State[int, int])
def event_index(lines: List[ReportLine]) -> Do:
    count = lines.length
    current = yield State.get()
    yield State.set(current + count)
    return current


class line_report(Case[DisplayLine, str], alg=DisplayLine):

    def plain(self, line: PlainDisplayLine) -> str:
        return line.text

    def syntax(self, line: SyntaxDisplayLine) -> str:
        return line.text


def format_report(report: ParseReport) -> List[str]:
    return report.lines.map(lambda a: line_report.match(a.line))


__all__ = ('ReportLine', 'format_report',)

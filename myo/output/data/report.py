from typing import TypeVar

from amino import Dat, List, ADT, do, Do, Maybe
from amino.state import State

from myo.output.data.output import OutputEvent, OutputLine, Location

A = TypeVar('A')


class ReportLine(ADT['ReportLine']):
    pass


class PlainReportLine(ReportLine):

    def __init__(self, text: str) -> None:
        self.text = text


class EventReportLine(ReportLine):

    @staticmethod
    def cons(
            text: str,
            event: int,
            location: Location=None,
    ) -> 'EventReportLine':
        return EventReportLine(
            text,
            event,
            Maybe.optional(location),
        )

    def __init__(self, text: str, event: int, location: Maybe[Location]) -> None:
        self.text = text
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


def event_report(index: int, event: OutputEvent[A]) -> List[ReportLine]:
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


def parse_report(events: List[OutputEvent[A]]) -> ParseReport:
    events_lines = events.with_index.map2(event_report)
    lines = events_lines.join
    event_indexes = events_lines.traverse(event_index, State).run_a(0).value
    return ParseReport(lines, event_indexes)


def format_report(report: ParseReport) -> List[str]:
    return report.lines.map(lambda a: a.text)


__all__ = ('ReportLine', 'parse_report', 'format_report',)

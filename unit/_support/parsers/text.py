from networkx import DiGraph

from amino import Maybe, do, Nothing, Do, Nil, List, Dat, Regex

from myo.output.data.output import OutputEvent, OutputLine
from myo.output.parser.base import Parser, EdgeData


class TextLine(Dat['TextLine']):

    @staticmethod
    def cons(text: str) -> 'TextLine':
        return TextLine(text)

    def __init__(self, text: str) -> None:
        self.text = text


text_edge = EdgeData.strict(
    regex=Regex(f'(?P<text>.+)'),
    cons_output_line=TextLine.cons,
)


def text_graph() -> DiGraph:
    g = DiGraph()
    g.add_edge('start', 'start', data=text_edge)
    return g


def text_event(line: OutputLine[TextLine]) -> OutputEvent[TextLine]:
    return OutputEvent.cons(List(line), Nothing, Nil)


def text_events(lines: List[OutputLine[TextLine]]) -> List[OutputEvent[TextLine]]:
    return lines.map(text_event)


text_parser = Parser(text_graph(), text_events)

__all__ = ('text_parser',)

from amino import List, Just, Nil

from myo.output.data.output import OutputEvent, OutputLine, Location
from myo.output.parser.scala import ScalaEvent, FileLine, CodeLine, ColLine

path = '/path/to/other_file.scala'
loc_line = '[error] /path/to/other_file.scala:7:2: terrible mistake'
code_line = '[error] x.otherName[Data]'
col_line = '[error]   ^'
scala_output_events = List(
    OutputEvent.cons(
        ScalaEvent.cons(
            OutputLine(loc_line, FileLine(path, 7, 6, 'terrible mistake', '')),
            List(OutputLine(code_line, CodeLine.cons('x.otherName[Data]'))),
            Just(OutputLine(col_line, ColLine(6, ''))),
        ),
        Nil,
        Just(Location(path, 7, 6))
    ),
)

__all__ = ('output_events',)

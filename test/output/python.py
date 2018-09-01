from amino.test import fixture_path
from amino import Path, Just, List
from amino.lenses.lens import lens

from myo.output.data.output import OutputLine, OutputEvent
from myo.output.parser.python import FileLine, ColLine, CodeLine, ErrorLine, stack_frame_event, ErrorEvent
from myo.components.command.compute.parsed_output import ParsedOutput
from myo.components.command.compute.parse_handlers import ParseHandlers

line, col = 2, 5
line1 = 3
line2 = 6
line3 = 7
file_path = fixture_path('command', 'parse', 'file.py')
output_line = OutputLine(
    f'  File "{file_path}", line {line}, in funcname',
    FileLine(
        Path(file_path),
        line,
        Just('funcname'),
    )
)
col5 = Just(OutputLine('    ^', ColLine(5)))
line_lens = lens.meta.line
code = OutputLine('    yield', CodeLine('yield'))
error_1 = OutputLine('RuntimeError: error', ErrorLine('error', 'RuntimeError'))
error_2 = OutputLine('SyntaxError: error', ErrorLine('error', 'SyntaxError'))
output_events = List(
    stack_frame_event(output_line, Just(code), col5),
    stack_frame_event(line_lens.set(line1)(output_line), Just(code), col5),
    OutputEvent.cons(ErrorEvent(error_1), List(error_1)),
    stack_frame_event(line_lens.set(line2)(output_line), Just(code), col5),
    stack_frame_event(line_lens.set(line3)(output_line), Just(code), col5),
    OutputEvent.cons(ErrorEvent(error_2), List(error_2)),
)
parsed_output = ParsedOutput(ParseHandlers.cons(), output_events, output_events)
trace_file = fixture_path('tmux', 'python_parse', 'trace')


__all__ = ('output_events', 'line', 'col', 'file_path', 'parsed_output',)

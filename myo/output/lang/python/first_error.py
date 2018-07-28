from amino import List
from amino.logging import module_log

from myo.output.data.output import OutputEvent

from ribosome.nvim.io.state import NS
from myo.output.parser.python import PythonLine, PythonEvent, ErrorEvent
from myo.components.command.compute.tpe import CommandRibosome

log = module_log()


def python_first_error(output: List[OutputEvent[PythonLine, PythonEvent]]) -> NS[CommandRibosome, int]:
    index = output.index_where(lambda a: isinstance(a.meta, ErrorEvent)).map(lambda a: abs(a - 1))
    return NS.pure(index.get_or_strict(0))


__all__ = ('python_first_error',)

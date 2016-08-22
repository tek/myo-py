from ribosome.machine import may_handle, Error, RunTask, handle
from ribosome.machine.base import io

import amino
from amino import __, F, L, _, may, Right

from myo.state import MyoComponent, MyoTransitions
from myo.plugins.core.dispatch import VimDispatcher
from myo.plugins.core.message import StageI, Initialized, ParseOutput
from myo.output import VimCompiler, CustomOutputHandler
from myo.util import parse_callback_spec


class CoreTransitions(MyoTransitions):

    @may_handle(StageI)
    def stage_1(self):
        return Initialized().pub.at(1)

    @may_handle(Initialized)
    def initialized(self):
        started = io(__.set_pvar('started', True))
        return (self.data.set(initialized=True) + VimDispatcher(self.vim),
                started)

    @may_handle(Error)
    def error(self):
        m = self.msg.message
        handler = (F(self.log.caught_exception, 'transition') if
                   amino.development and isinstance(m, Exception) else
                   self.log.error)
        handler(m)

    @handle(ParseOutput)
    def parse_output(self):
        return self._error_handler(self.msg.command).join / (
            lambda parser:
            RunTask(
                parser.parse(self.msg.output, self.msg.path) // parser.display)
        )

    def _error_handler(self, cmd):
        return cmd.parser.flat_map(self._special_error_handler).or_else(
            cmd.parser //
            parse_callback_spec /
            __.map(L(CustomOutputHandler)(self.vim, _))
        )

    @may
    def _special_error_handler(self, spec: str):
        if spec == 'compiler':
            return Right(VimCompiler(self.vim))


class Plugin(MyoComponent):
    Transitions = CoreTransitions

__all__ = ('Plugin',)

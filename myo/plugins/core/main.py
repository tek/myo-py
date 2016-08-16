import re

from trypnv.machine import may_handle, io, Error, RunTask

import tryp
from tryp import __, F, List, Maybe, Either, L, _

from myo.state import MyoComponent, MyoTransitions
from myo.plugins.core.dispatch import VimDispatcher
from myo.plugins.core.message import StageI, Initialized, ParseOutput
from myo.output import VimCompiler, CustomOutputHandler

_parser_re = re.compile('^py:(.+)')


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
                   tryp.development and isinstance(m, Exception) else
                   self.log.error)
        handler(m)

    @may_handle(ParseOutput)
    def parse_output(self):
        parser = self._error_handler(self.msg.command)
        return RunTask(parser.parse(self.msg.output) // parser.display)

    def _error_handler(self, cmd):
        path = cmd.parser / _parser_re.match // Maybe / __.group(1)
        def extended(path):
            parts = List.wrap(path.rsplit('.', 1))
            return (
                parts.lift_all(0, 1)
                .to_either('invalid module path: {}'.format(path))
                .flat_map2(Either.import_name) /
                L(CustomOutputHandler)(self.vim, _)
            )
        return path // extended | VimCompiler(self.vim)


class Plugin(MyoComponent):
    Transitions = CoreTransitions

__all__ = ('Plugin',)

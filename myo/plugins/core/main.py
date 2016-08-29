from ribosome.machine import may_handle, Error, RunTask, handle
from ribosome.machine.base import io

import amino
from amino import __, F, L, _, may, Right, Just, List

from myo.state import MyoComponent, MyoTransitions
from myo.plugins.core.dispatch import VimDispatcher
from myo.plugins.core.message import StageI, Initialized, ParseOutput
from myo.output import VimCompiler, CustomOutputHandler, Parsing
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
        langs = self.msg.options.get('langs') / List.wrap | cmd.langs
        parser = self.msg.options.get('parser').or_else(cmd.parser)
        return (
            (parser // self._special_error_handler)
            .or_else(
                parser //
                parse_callback_spec /
                __.map(L(CustomOutputHandler)(self.vim, _))
            ).or_else(self._langs_parsing(langs))
        )

    @may
    def _special_error_handler(self, spec: str):
        if spec == 'compiler':
            return Right(VimCompiler(self.vim))

    def _langs_parsing(self, langs):
        return langs.empty.no.either('command has no langs',
                                     Just(Parsing(self.vim, langs)))


class Plugin(MyoComponent):
    Transitions = CoreTransitions

__all__ = ('Plugin',)

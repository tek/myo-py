from ribosome.machine import may_handle, Error, RunTask, handle
from ribosome.machine.base import io
from ribosome.machine.transition import Fatal

import amino
from amino import __, F, L, _, Right, Just, List, Left, Either

from myo.state import MyoComponent, MyoTransitions
from myo.plugins.core.dispatch import VimDispatcher
from myo.plugins.core.message import StageI, Initialized, ParseOutput
from myo.output import VimCompiler, CustomOutputHandler, Parsing
from myo.util import parse_callback_spec
from myo.output.machine import ResultAdapter


class CoreTransitions(MyoTransitions):

    @may_handle(StageI)
    def stage_1(self):
        return Initialized().pub.at(1)

    @may_handle(Initialized)
    def initialized(self):
        started = io(__.vars.set_p('started', True))
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
        opt = self.msg.options
        filters = self._callbacks('output_filters') | List()
        reifier = self.vim.vars.p('output_reifier') // Either.import_path
        formatters = self._callbacks('output_formatters') | List()
        def handle(parser):
            def dispatch(result):
                adapter = ResultAdapter(self.vim, result, filters, reifier,
                                        formatters)
                return parser.display(adapter, opt)
            return RunTask(parser.parse(self.msg.output, self.msg.path) //
                           dispatch)
        return self._error_handler(self.msg.command).join / handle

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
        ).lmap(Fatal)

    def _special_error_handler(self, spec: str):
        return (Right(Right(VimCompiler(self.vim)))
                if spec == 'compiler' else
                Left('no special error handler found'))

    def _langs_parsing(self, langs):
        return langs.empty.no.either('command has no langs',
                                     Just(Parsing(self.vim, langs)))


class Plugin(MyoComponent):
    Transitions = CoreTransitions

    def new_state(self):
        pass

__all__ = ('Plugin',)

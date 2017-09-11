import amino
from amino import __, List, Left, IO, Map, _, L

from ribosome.machine import may_handle, Error, handle
from ribosome.machine.base import unit_nio
from ribosome.machine.transition import Fatal
from ribosome.machine.messages import RunIO

from myo.state import MyoComponent, MyoTransitions
from myo.plugins.core.dispatch import VimDispatcher
from myo.plugins.core.message import StageI, Initialized, ParseOutput
from myo.output import VimCompiler, CustomOutputHandler, Parsing
from myo.output.main import OutputHandler
from myo.command import CommandJob

error_no_output_events = 'no events in parse result'


class CoreTransitions(MyoTransitions):

    @may_handle(StageI)
    def stage_1(self):
        return Initialized().pub.at(1)

    @may_handle(Initialized)
    def initialized(self):
        started = unit_nio(__.vars.set_p('started', True))
        return (self.data.set(initialized=True) + VimDispatcher(self.vim), started)

    @may_handle(Error)
    def error(self):
        m = self.msg.message
        handler = (L(self.log.caught_exception)('transition', _) if
                   amino.development and isinstance(m, Exception) else
                   self.log.error)
        handler(m)

    @handle(ParseOutput)
    def parse_output(self):
        opt = self.msg.options
        job = self._ensure_job(self.msg.job)
        def handle(parser):
            def display(result):
                return (
                    IO.now(Left(Fatal(error_no_output_events)))
                    if result.events.empty else
                    parser.display(result, opt)
                )
            return RunIO(parser.parse(self.msg.output, self.msg.path) // display)
        return self._error_handler(job) / handle

    def _error_handler(self, job):
        langs = self.msg.options.get('langs') / List.wrap | job.langs
        parser_spec = self.msg.options.get('parser').o(job.command.parser)
        def check(p):
            return (p if isinstance(p, OutputHandler) else
                    CustomOutputHandler(self.vim, p))
        return (
            self._inst_callbacks(parser_spec, None, self._special_parsers) /
            check
        ).o(self._langs_parsing(langs)).lmap(Fatal)

    @property
    def _special_parsers(self):
        return Map(compiler=VimCompiler)

    def _langs_parsing(self, langs):
        return langs.empty.no.either('command has no langs',
                                     Parsing(self.vim, langs))

    def _ensure_job(self, data):
        return (data if isinstance(data, CommandJob) else
                CommandJob(command=data))


class Plugin(MyoComponent):
    Transitions = CoreTransitions

    def new_state(self):
        pass

__all__ = ('Plugin',)

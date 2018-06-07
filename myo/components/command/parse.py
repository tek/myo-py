from typing import TypeVar, Callable

from ribosome.nvim.io.state import NS
from ribosome.compute.ribosome_api import Ribo

from chiasma.util.id import Ident, IdentSpec

from amino import do, Do, List, Dat, __, Maybe, IO, Lists, Just, Nothing, Nil, _
from amino.logging import module_log
from amino.case import Case

from myo.output.data.output import OutputEvent
from myo.components.command.data import CommandData
from myo.data.command import Command, Interpreter, ShellInterpreter, CommandConfig
from myo.components.command.compute.output import render_parse_result
from myo.components.command.compute.tpe import CommandRibosome
from myo.settings import display_parse_result
from myo.command.history import most_recent_command
from myo.output.main import ParseConfig, parse_with_langs
from myo.util.callback import resolve_callbacks

log = module_log()
A = TypeVar('A')
D = TypeVar('D')


def match_command_config(cmd: Command, shell: Maybe[Command]) -> Callable[[CommandConfig], bool]:
    def match_command_config(conf: CommandConfig) -> bool:
        return conf.ident == cmd.ident or shell.ident.contains(conf.ident)
    return match_command_config


def command_config_option(cmd: Maybe[CommandConfig], shell: Maybe[CommandConfig]
                          ) -> Callable[[Callable[[CommandConfig], A], Callable[[A, A], A]], Maybe[A]]:
    def command_config_option(get: Callable[[CommandConfig], A], combine: Callable[[A, A], A]) -> Maybe[A]:
        primary = cmd.flat_map(get)
        secondary = shell.flat_map(get)
        return (
            primary
            .map(
                lambda a:
                secondary.map(lambda b: combine(a, b))
                .get_or_strict(a)
            )
            .o(secondary)
        )
    return command_config_option


def command_conf_by_ident(ident: Ident) -> NS[CommandRibosome, Maybe[CommandConfig]]:
    return Ribo.inspect_comp(lambda a: a.command_configs.find(lambda b: b.ident == ident))


@do(NS[CommandRibosome, None])
def parse_config(cmd: Command, shell: Maybe[Command]) -> Do:
    cmd_conf = yield command_conf_by_ident(cmd.ident)
    shell_conf = yield shell.map(lambda a: a.command_conf_by_ident(a.ident)).get_or(NS.pure, Nothing)
    shell_langs = shell.map(lambda a: a.langs).get_or_strict(Nil)
    option = command_config_option(cmd_conf, shell_conf)
    cmd_conf_langs = option(lambda a: a.parsers, lambda a, b: a + b).get_or_strict(Nil)
    filter = option(lambda a: a.output_filter, lambda a, b: a + b).get_or_strict(Nil)
    first_error = option(lambda a: a.output_first_error, lambda a, b: a)
    path_truncator = option(lambda a: a.output_path_truncator, lambda a, b: a)
    langs = (cmd.langs + shell_langs + cmd_conf_langs).distinct
    yield NS.pure(ParseConfig(langs, filter, first_error, path_truncator))


@do(NS[CommandRibosome, List[OutputEvent]])
def parse_with_config(output: List[str], config: ParseConfig) -> Do:
    yield NS.e(parse_with_langs(output, config.langs))


@do(NS[CommandRibosome, List[OutputEvent]])
def parse_output(cmd: Command, output: List[str], shell: Maybe[Command]) -> Do:
    config = yield parse_config(cmd, shell)
    log.debug(f'parsing output with {config}')
    events = yield parse_with_config(output, config)
    filters = yield NS.e(resolve_callbacks(config.filter))
    yield filters.fold_m(NS.pure(events))(lambda z, f: f(z))


@do(NS[CommandData, List[str]])
def cmd_output(ident: Ident) -> Do:
    cmd_log = yield NS.inspect_either(__.log_by_ident(ident))
    text = yield NS.from_io(IO.delay(cmd_log.read_text))
    return Lists.lines(text)


class shell_for_command(Case[Interpreter, NS[CommandData, Maybe[Command]]], alg=Interpreter):

    @do(NS[CommandData, Maybe[Command]])
    def shell_interpreter(self, interpreter: ShellInterpreter) -> Do:
        shell = yield NS.inspect_either(lambda a: a.command_by_ident(interpreter.target))
        return Just(shell)

    def case_default(self, interpreter: Interpreter) -> NS[CommandData, Maybe[Command]]:
        return NS.pure(Nothing)


@do(NS[CommandRibosome, None])
def parse_command(cmd: Command, shell: Maybe[Command]) -> Do:
    output = yield Ribo.zoom_comp(cmd_output(cmd.ident))
    yield parse_output(cmd, output, shell)


@do(NS[CommandRibosome, None])
def parse_most_recent() -> Do:
    cmd = yield Ribo.zoom_comp(most_recent_command())
    shell = yield Ribo.zoom_comp(shell_for_command.match(cmd.interpreter))
    yield parse_command(cmd, shell)


__all__ = ('parse_command', 'parse_most_recent',)

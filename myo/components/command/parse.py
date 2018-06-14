from typing import TypeVar, Callable

from ribosome.nvim.io.state import NS
from ribosome.compute.ribosome_api import Ribo

from chiasma.util.id import Ident

from amino import do, Do, List, __, Maybe, IO, Lists, Just, Nothing, Nil
from amino.logging import module_log
from amino.case import Case

from myo.output.data.output import OutputEvent
from myo.components.command.data import CommandData
from myo.data.command import Command, Interpreter, ShellInterpreter, CommandConfig
from myo.components.command.compute.tpe import CommandRibosome
from myo.command.history import most_recent_command
from myo.output.main import parse_with_langs
from myo.output.config import LangConfig, ParseConfig
from myo.output.configs import default_lang_configs, global_config_defaults
from myo.components.command.compute.parsed_output import ParsedOutput
from myo.components.command.compute.parse_handlers import ParseHandlers
from myo.settings import builtin_output_config

log = module_log()
A = TypeVar('A')
D = TypeVar('D')


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


def find_lang_config(configs: List[LangConfig], name: str) -> Maybe[ParseConfig]:
    return configs.find(lambda a: a.name == name).map(lambda a: a.parse)


def lang_config(use_builtins: bool) -> Callable[[str], NS[CommandRibosome, Maybe[ParseConfig]]]:
    @do(NS[CommandRibosome, Maybe[ParseConfig]])
    def lang_config(lang: str) -> Do:
        configs = yield Ribo.inspect_comp(lambda a: a.lang_configs)
        specific = find_lang_config(configs, lang)
        return (
            specific.or_else_call(find_lang_config, default_lang_configs, lang)
            if use_builtins else
            specific
        )
    return lang_config


@do(NS[CommandRibosome, ParseConfig])
def parse_config(cmd: Command, shell: Maybe[Command]) -> Do:
    use_builtins = yield Ribo.setting(builtin_output_config)
    cmd_conf = yield command_conf_by_ident(cmd.ident)
    shell_conf = yield shell.map(lambda a: command_conf_by_ident(a.ident)).get_or(NS.pure, Nothing)
    shell_langs = shell.map(lambda a: a.langs).get_or_strict(Nil)
    langs = (cmd.langs + shell_langs).distinct
    lang_confs = yield langs.flat_traverse((lang_config)(use_builtins), NS)
    cmd_lang_conf = ParseConfig.cons(langs=langs)
    global_conf = global_config_defaults.parse
    local_confs = (cmd_conf.to_list + shell_conf.to_list).map(lambda a: a.parse)
    nonglobal_confs = (local_confs + lang_confs).cons(cmd_lang_conf)
    confs = (
        nonglobal_confs.cat(global_conf)
        if use_builtins else
        nonglobal_confs
    )
    yield NS.pure(confs.fold(ParseConfig))


@do(NS[CommandRibosome, List[OutputEvent]])
def parse_with_config(output: List[str], langs: List[str]) -> Do:
    yield NS.e(parse_with_langs(output, langs))


@do(NS[CommandRibosome, ParsedOutput])
def parse_output(cmd: Command, output: List[str], shell: Maybe[Command]) -> Do:
    config = yield parse_config(cmd, shell)
    handlers = yield NS.e(ParseHandlers.from_config(config))
    log.debug(f'parsing output with {handlers}')
    events = yield parse_with_config(output, config.langs)
    filtered = yield handlers.filter.fold_m(NS.pure(events))(lambda z, f: f(z))
    return ParsedOutput(handlers, events, filtered)


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


@do(NS[CommandRibosome, ParsedOutput])
def parse_command(cmd: Command, shell: Maybe[Command]) -> Do:
    output = yield Ribo.zoom_comp(cmd_output(cmd.ident))
    yield parse_output(cmd, output, shell)


@do(NS[CommandRibosome, ParsedOutput])
def parse_most_recent() -> Do:
    cmd = yield Ribo.zoom_comp(most_recent_command())
    shell = yield Ribo.zoom_comp(shell_for_command.match(cmd.interpreter))
    yield parse_command(cmd, shell)


__all__ = ('parse_command', 'parse_most_recent',)

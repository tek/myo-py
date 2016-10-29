from amino import Task, L, Just, _

from ribosome.unite import UniteSource


class UniteNames():
    history_candidates = '_myo_unite_history'
    commands_candidates = '_myo_unite_commands'
    run = '_myo_unite_run_command'
    commands = 'myo_commands'
    command = 'myo_command'
    history = 'myo_history'
    syntax = '_myo_unite_syntax'


def commands_syntax(syntax):
    m = L(Task.call)(syntax.match, _, _)
    hi = L(Task.call)(syntax.highlight, _)
    name = '^\s*\[\S\+\]'
    return (
        m('name', name) +
        hi('name', ctermfg=3) +
        m('line', '\({} \)\@<=.*'.format(name)) +
        hi('line', ctermfg=4)
    )


class HistorySource(UniteSource):

    def __init__(self) -> None:
        super().__init__(UniteNames.history, UniteNames.history_candidates,
                         UniteNames.command, Just(UniteNames.syntax))

    def syntax_task(self, syntax):
        return commands_syntax(syntax)


class CommandsSource(UniteSource):

    def __init__(self) -> None:
        super().__init__(UniteNames.commands, UniteNames.commands_candidates,
                         UniteNames.command, Just(UniteNames.syntax))

    def syntax_task(self, syntax):
        return commands_syntax(syntax)

__all__ = ('HistorySource', 'UniteNames', 'CommandsSource')

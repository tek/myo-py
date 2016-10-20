from amino import Task, L, Just, _

from ribosome.unite import UniteSource


class UniteNames():
    history_candidates = '_myo_unite_history'
    run = '_myo_unite_run_project'
    history = 'myo_history'
    syntax = '_myo_unite_syntax'


class HistorySource(UniteSource):

    def __init__(self) -> None:
        super().__init__(UniteNames.history, UniteNames.history_candidates,
                         UniteNames.history, Just(UniteNames.syntax))

    def syntax_task(self, syntax):
        m = L(Task.call)(syntax.match, _, _)
        hi = L(Task.call)(syntax.highlight, _)
        name = '^\s*\[\S\+\]'
        return (
            m('name', name) +
            hi('name', ctermfg=3) +
            m('line', '\({} \)\@<=.*'.format(name)) +
            hi('line', ctermfg=4)
        )


__all__ = ('HistorySource', 'UniteNames')

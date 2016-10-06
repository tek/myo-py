from myo.logging import Logging


class PanesFacade(Logging):

    def __init__(self, window) -> None:
        self.window = window

    def close_id(self, id: int):
        return self.server.cmd('kill-pane', '-t', '%{}'.format(id))

__all__ = ('PanesFacade',)

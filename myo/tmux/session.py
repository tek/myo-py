import tmuxp

from trypnv.record import field, Record


class Session(Record):
    id = field(str)


class SessionHandler:

    def __init__(self, server: tmuxp.Server) -> None:
        self.server = server

    def create_pane(self, pane):
        pass

__all__ = ('Session',)

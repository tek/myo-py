from ribosome.util.callback import VimCallback

from amino import _


class DuplicatesFilter(VimCallback):

    def __call__(self, result):
        return result.modder.events(_.distinct)

__all__ = ('DuplicatesFilter',)

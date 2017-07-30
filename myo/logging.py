import amino.logging
from ribosome.logging import ribosome_logger

from amino.lazy import lazy

log = myo_root_logger = ribosome_logger('myo')


def myo_logger(name: str) -> amino.logging.Logger:
    return myo_root_logger.getChild(name)


class Logging(amino.logging.Logging):

    @lazy
    def _log(self) -> amino.logging.Logger:
        return myo_logger(self.__class__.__name__)

__all__ = ('myo_logger', 'Logging')

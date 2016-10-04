import logging
from typing import Callable

import amino.logging
import ribosome.logging
from ribosome.logging import ribosome_logger, pr

from amino.lazy import lazy


log = myo_root_logger = ribosome_logger('myo')


def myo_logger(name: str):
    return myo_root_logger.getChild(name)


class Logging(amino.logging.Logging):

    @lazy
    def _log(self) -> amino.logging.Logger:  # type: ignore
        return myo_logger(self.__class__.__name__)


def print_info(out: Callable[[str], None]):
    lname = lambda l: logging.getLevelName(l.getEffectiveLevel())
    hlname = lambda h: logging.getLevelName(h.level)
    def handler(h):
        return '{}({})'.format(h.__class__.__name__, hlname(h))
    def logger(l):
        handlers = ','.join(list(map(handler, l.handlers)))
        info = '{}: {} {}'.format(l.name, lname(l), handlers)
        out(info)
    logger(amino.logging.amino_root_logger)
    logger(ribosome.logging.ribosome_root_logger)
    logger(myo_root_logger)

__all__ = ('myo_logger', 'Logging')

import logging
from typing import Callable

import tryp.logging
import trypnv.logging
from trypnv.logging import trypnv_logger

from tryp.lazy import lazy


log = myo_root_logger = trypnv_logger('myo')


def myo_logger(name: str):
    return myo_root_logger.getChild(name)


class Logging(tryp.logging.Logging):

    @lazy
    def _log(self) -> tryp.logging.Logger:  # type: ignore
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
    logger(tryp.logging.tryp_root_logger)
    logger(trypnv.logging.trypnv_root_logger)
    logger(myo_root_logger)

__all__ = ('myo_logger', 'Logging')

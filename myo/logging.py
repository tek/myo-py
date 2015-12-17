import logging  # type: ignore

from trypnv.logging import trypnv_logger

from tryp.lazy import lazy  # type: ignore


log = myo_root_logger = trypnv_logger('myo')


def myo_logger(name: str):
    return myo_root_logger.getChild(name)


class Logging(object):

    @property
    def log(self) -> logging.Logger:
        return self._log   # type: ignore

    @lazy
    def _log(self) -> logging.Logger:
        return myo_logger(self.__class__.__name__)

__all__ = ['myo_logger']

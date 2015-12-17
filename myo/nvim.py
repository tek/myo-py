from pathlib import Path

import neovim  # type: ignore

import trypnv

from myo.logging import Logging


class NvimFacade(Logging, trypnv.nvim.NvimFacade):

    def __init__(self, nvim: neovim.Nvim) -> None:
        trypnv.nvim.NvimFacade.__init__(self, nvim, 'myo')

__all__ = ['NvimFacade']

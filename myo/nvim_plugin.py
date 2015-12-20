from pathlib import Path

import neovim  # type: ignore

from tryp import List

from trypnv import command, NvimStatePlugin, msg_command, json_msg_command

from myo.plugins.core import Init
from myo.main import Myo
from myo.nvim import NvimFacade
from myo.logging import Logging
from myo.plugins.command import AddVimCommand, Run, AddCommand


class MyoNvimPlugin(NvimStatePlugin, Logging):

    def __init__(self, vim: neovim.Nvim) -> None:
        super(MyoNvimPlugin, self).__init__(NvimFacade(vim))
        self.myo = None  # type: Myo

    def state(self):
        return self.myo

    @command()
    def myo_reload(self):
        self.myo_quit()
        self.myo_start()

    @command()
    def myo_quit(self):
        if self.myo is not None:
            self.vim.clean()
            self.myo = None

    @command()
    def myo_start(self):
        config_path = self.vim.ppath('config_path')\
            .get_or_else(Path('/dev/null'))
        plugins = self.vim.pl('plugins') | List()
        self.myo = Myo(self.vim.proxy, Path(config_path), plugins)
        self.myo.start()
        self.myo.send(Init())

    @command()
    def myo_plug(self, plug_name, cmd_name, *args):
        self.myo.plug_command(plug_name, cmd_name, args)

    @json_msg_command(AddVimCommand)
    def myo_vim_command(self):
        pass

    @json_msg_command(AddCommand)
    def myo_command(self):
        pass

    @msg_command(Run)
    def myo_run(self):
        pass

__all__ = ('MyoNvimPlugin',)

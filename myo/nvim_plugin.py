from pathlib import Path

import neovim

from tryp import List

from trypnv import command, NvimStatePlugin, msg_command, json_msg_command

from myo.plugins.core.main import StageI
from myo.main import Myo
from myo.nvim import NvimFacade
from myo.logging import Logging
from myo.plugins.command import AddVimCommand, Run, AddCommand
from myo.plugins.tmux.messages import (TmuxCreatePane, TmuxCreateSession,
                                       TmuxCreateLayout, TmuxSpawnSession,
                                       TmuxTest)
from myo.plugins.tmux import TmuxOpenPane


class MyoNvimPlugin(NvimStatePlugin, Logging):

    def __init__(self, vim: neovim.Nvim) -> None:
        super(MyoNvimPlugin, self).__init__(NvimFacade(vim))
        self.myo = None  # type: Myo
        self._post_initialized = False

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

    @command(sync=True)
    def myo_start(self):
        config_path = self.vim.ppath('config_path')\
            .get_or_else(Path('/dev/null'))
        plugins = self.vim.pl('plugins') | List()
        self.myo = Myo(self.vim.proxy, Path(config_path), plugins)
        self.myo.start()
        self.myo.wait_for_running()
        self.myo.send(StageI())

    @command()
    def myo_post_startup(self):
        self._post_initialized = True
        if self.myo is not None:
            pass
        else:
            self.log.error('myo startup failed')

    @command()
    def myo_plug(self, plug_name, cmd_name, *args):
        self.myo.plug_command(plug_name, cmd_name, args)

    @json_msg_command(AddVimCommand)
    def myo_vim_command(self):
        pass

    @json_msg_command(AddCommand)
    def myo_command(self):
        pass

    @json_msg_command(TmuxCreateSession)
    def myo_tmux_create_session(self):
        pass

    @msg_command(TmuxSpawnSession)
    def myo_tmux_spawn_session(self):
        pass

    @json_msg_command(TmuxCreateLayout)
    def myo_tmux_create_layout(self):
        pass

    @json_msg_command(TmuxCreatePane)
    def myo_tmux_create_pane(self):
        pass

    @json_msg_command(TmuxOpenPane)
    def myo_tmux_open_pane(self):
        pass

    @msg_command(Run)
    def myo_run(self):
        pass

    @msg_command(TmuxTest)
    def myo_tmux_test(self):
        pass

__all__ = ('MyoNvimPlugin',)

from pathlib import Path

import neovim

from tryp import List

from trypnv import command, NvimStatePlugin, msg_command, json_msg_command

from myo.plugins.core.main import StageI
from myo.main import Myo
from myo.nvim import NvimFacade
from myo.logging import Logging
from myo.plugins.command import (AddVimCommand, Run, AddShellCommand, AddShell,
                                 ShellRun)
from myo.plugins.tmux.messages import (TmuxCreatePane, TmuxCreateSession,
                                       TmuxCreateLayout, TmuxSpawnSession,
                                       TmuxInfo, TmuxClosePane)
from myo.plugins.tmux import TmuxOpenPane


class MyoNvimPlugin(NvimStatePlugin, Logging):

    def __init__(self, vim: neovim.Nvim) -> None:
        super().__init__(NvimFacade(vim))
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
            self.myo.stop()
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

    @json_msg_command(AddShellCommand)
    def myo_shell_command(self):
        pass

    @json_msg_command(AddShell)
    def myo_shell(self):
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

    @msg_command(TmuxClosePane)
    def myo_tmux_close_pane(self):
        pass

    @json_msg_command(Run)
    def myo_run(self):
        pass

    @json_msg_command(ShellRun)
    def myo_run_in_shell(self):
        pass

    @msg_command(TmuxInfo)
    def myo_tmux_show(self):
        pass

    @neovim.autocmd('VimLeave', sync=True)
    def vim_leave(self):
        self.myo_quit()

__all__ = ('MyoNvimPlugin',)

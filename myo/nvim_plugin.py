from pathlib import Path

import neovim

from amino import List, L, _, I

from ribosome import command, NvimStatePlugin, msg_command, json_msg_command
from ribosome.machine.scratch import Mapping
from ribosome.request import msg_function

from myo.plugins.core.main import StageI
from myo.main import Myo
from myo.logging import Logging
from myo.plugins.command.message import (AddVimCommand, Run, AddShellCommand,
                                         AddShell, ShellRun, RunTest,
                                         RunVimTest)
from myo.plugins.tmux.message import (TmuxCreatePane, TmuxCreateSession,
                                      TmuxCreateLayout, TmuxSpawnSession,
                                      TmuxInfo, TmuxClosePane, TmuxPack)
from myo.plugins.tmux import TmuxOpenPane
from myo.plugins.core.message import Parse


class MyoNvimPlugin(NvimStatePlugin, Logging):

    def __init__(self, vim: neovim.Nvim) -> None:
        super().__init__(vim)
        self.myo = None  # type: Myo
        self._post_initialized = False

    @property
    def name(self):
        return 'myo'

    @property
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

    @msg_command(TmuxPack)
    def myo_tmux_pack(self):
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

    @json_msg_command(Parse)
    def myo_parse(self):
        pass

    @json_msg_command(RunTest)
    def myo_test(self):
        pass

    @json_msg_command(RunVimTest)
    def myo_vim_test(self):
        pass

    def _eval(self, args, go):
        result = List.wrap(args).head.to_either('expression needed') // go
        return result.cata(self.log.error, I)

    @neovim.function('MyoEval', sync=True)
    def myo_eval(self, args):
        return self._eval(args, self.myo.eval_expr)

    @neovim.function('MyoTmuxEval', sync=True)
    def myo_tmux_eval(self, args):
        def mod(data, plugins):
            d = data.sub_states.get('tmux') | data
            p = plugins.get('tmux') | plugins
            return d, p
        return self._eval(args, L(self.myo.eval_expr)(_, mod))

    @neovim.autocmd('VimLeave', sync=True)
    def vim_leave(self):
        self.myo_quit()

    @msg_function(Mapping)
    def myo_mapping(self):
        pass

__all__ = ('MyoNvimPlugin',)

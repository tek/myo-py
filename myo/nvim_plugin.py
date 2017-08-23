from pathlib import Path

import neovim

from amino import List, L, _, I, Map, Path

from ribosome import command, NvimStatePlugin, msg_command, json_msg_command
from ribosome.machine.scratch import Mapping
from ribosome.request import msg_function
import ribosome.nvim.components
from ribosome.machine.state import UpdateRecord
from ribosome.unite import mk_unite_candidates, mk_unite_action
from ribosome.unite.plugin import unite_plugin

from myo.plugins.core.main import StageI
from myo.main import Myo
from myo.logging import Logging
from myo.plugins.command.message import (AddVimCommand, Run, AddShellCommand,
                                         AddShell, ShellRun, RunTest,
                                         RunVimTest, CommandShow, RunLatest,
                                         RunLine, RunChained, RebootCommand,
                                         DeleteHistory, CommandHistoryShow)
from myo.plugins.tmux.message import (TmuxCreatePane, TmuxCreateSession,
                                      TmuxCreateLayout, TmuxSpawnSession,
                                      TmuxInfo, TmuxClosePane, TmuxPack,
                                      TmuxMinimize, TmuxRestore, TmuxToggle,
                                      TmuxFocus, TmuxOpenOrToggle, TmuxKill)
from myo.plugins.tmux import TmuxOpen
from myo.plugins.core.message import Parse, Resized
from myo.plugins.unite.message import UniteHistory, UniteCommands
from myo.plugins.unite.main import UniteNames
from myo.plugins.unite.format import unite_format
from myo.output.machine import EventPrev, EventNext

unite_candidates = mk_unite_candidates(UniteNames)
unite_action = mk_unite_action(UniteNames)


@unite_plugin('myo')
@neovim.plugin
class MyoNvimPlugin(NvimStatePlugin, Logging, name='myo'):

    def __init__(self, vim: neovim.Nvim) -> None:
        super().__init__(vim)
        self.myo: Myo = None

    @property
    def name(self):
        return 'myo'

    def state(self) -> Myo:
        if self.myo is None:
            self.start_plugin()
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

    def start_plugin(self) -> None:
        config_path = self.vim.vars.ppath('config_path').get_or_else(Path('/dev/null'))
        plugins = self.vim.vars.pl('plugins') | self._default_plugins
        self.myo = Myo(self.vim.proxy, Path(config_path), plugins)
        self.myo.start()
        self.myo.wait_for_running()
        self.myo.send(StageI())

    @command(sync=True)
    def myo_start(self):
        self.start_plugin()

    @property
    def _default_plugins(self):
        return List('command', 'tmux', 'unite')

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

    @json_msg_command(TmuxOpen)
    def myo_tmux_open(self):
        pass

    @msg_command(TmuxClosePane)
    def myo_tmux_close_pane(self):
        pass

    @msg_command(TmuxPack)
    def myo_tmux_pack(self):
        pass

    @json_msg_command(TmuxMinimize)
    def myo_tmux_minimize(self):
        pass

    @json_msg_command(TmuxRestore)
    def myo_tmux_restore(self):
        pass

    @json_msg_command(TmuxToggle)
    def myo_tmux_toggle(self):
        pass

    @msg_command(TmuxOpenOrToggle)
    def myo_tmux_open_or_toggle(self):
        pass

    @msg_command(TmuxFocus)
    def myo_tmux_focus(self):
        pass

    @json_msg_command(TmuxKill)
    def myo_tmux_kill(self):
        pass

    @json_msg_command(Run)
    def myo_run(self):
        pass

    @msg_command(RunLine)
    def myo_run_line(self):
        pass

    @json_msg_command(ShellRun)
    def myo_run_in_shell(self):
        pass

    @json_msg_command(RunLatest)
    def myo_run_latest(self):
        pass

    @msg_command(RunChained)
    def myo_run_chained(self):
        pass

    @json_msg_command(RebootCommand)
    def myo_reboot_command(self):
        pass

    @msg_command(TmuxInfo)
    def myo_tmux_show(self):
        pass

    @msg_command(CommandShow)
    def myo_command_show(self):
        pass

    @msg_command(CommandHistoryShow)
    def myo_command_history_show(self):
        pass

    @json_msg_command(Parse)
    def myo_parse(self):
        pass

    @msg_command(EventPrev)
    def myo_event_prev(self):
        pass

    @msg_command(EventNext)
    def myo_event_next(self):
        pass

    @json_msg_command(RunTest)
    def myo_test(self):
        pass

    @json_msg_command(RunVimTest)
    def myo_vim_test(self):
        pass

    @json_msg_command(UpdateRecord)
    def myo_update(self):
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
        ribosome.nvim.components.shutdown = True
        self.myo_quit()

    @neovim.autocmd('VimResized', sync=False)
    def vim_resized(self):
        if self.myo is not None:
            self.myo.send(Resized())

    @msg_function(Mapping)
    def myo_mapping(self):
        pass

    @msg_command(UniteHistory)
    def myo_unite_history(self):
        pass

    @msg_command(UniteCommands)
    def myo_unite_commands(self):
        pass

    @unite_candidates('history')
    def myo_unite_history_candidates(self, args):
        return self.myo.data.commands.history / unite_format

    @unite_candidates('commands')
    def myo_unite_commands_candidates(self, args):
        return self.myo.data.commands.commands / unite_format

    @unite_action('run', 'name')
    def myo_unite_run(self, ident):
        return Run(ident, options=Map())

    @unite_action('delete', 'ident')
    def myo_unite_delete(self, ident):
        return DeleteHistory(ident)

__all__ = ('MyoNvimPlugin',)

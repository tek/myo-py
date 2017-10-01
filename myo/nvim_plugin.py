from amino import List, L, _, I, Map

from ribosome import msg_command, json_msg_command, AutoPlugin, function
from ribosome.machine.scratch import Mapping
from ribosome.request.function import msg_function
from ribosome.machine.state import UpdateRecord
from ribosome.unite import mk_unite_candidates, mk_unite_action
from ribosome.unite.plugin import unite_plugin
from ribosome.settings import Config
from ribosome.request.autocmd import autocmd

from myo.logging import Logging
from myo.components.command.message import (AddVimCommand, Run, AddShellCommand, AddShell, ShellRun, RunTest,
                                            RunVimTest, CommandShow, RunLatest, RunLine, RunChained, RebootCommand,
                                            DeleteHistory, CommandHistoryShow)
from myo.components.tmux.message import (TmuxCreatePane, TmuxCreateSession, TmuxCreateLayout, TmuxSpawnSession,
                                         TmuxInfo, TmuxClosePane, TmuxPack, TmuxMinimize, TmuxRestore, TmuxToggle,
                                         TmuxFocus, TmuxOpenOrToggle, TmuxKill)
from myo.components.tmux.message import TmuxOpen
from myo.components.core.message import Parse, Resized
from myo.components.unite.message import UniteHistory, UniteCommands
from myo.components.unite.main import UniteNames, Unite
from myo.components.unite.format import unite_format
from myo.output.machine import EventPrev, EventNext
from myo.env import Env
from myo.components.core.main import Core
from myo.components.command.main import CommandComponent
from myo.components.tmux.main import Tmux
from myo.settings import ProteomeSettings

unite_candidates = mk_unite_candidates(UniteNames)
unite_action = mk_unite_action(UniteNames)

config: Config = Config(
    name='myo',
    prefix='myo',
    state_type=Env,
    components=Map(core=Core, command=CommandComponent, tmux=Tmux, unite=Unite),
    settings=ProteomeSettings(),
    request_handlers=List(
        # RequestHandler.msg_cmd(Msg)('msg', prefix=Plain, sync=True)
    ),
    core_components=List('core'),
    default_components=List('command', 'tmux', 'unite'),
)


@unite_plugin('myo')
class MyoNvimPlugin(AutoPlugin, Logging):

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

    @function()
    def myo_eval(self, args):
        return self._eval(args, self.root.eval_expr)

    @function()
    def myo_tmux_eval(self, args):
        def mod(data, components):
            d = data.sub_states.get('tmux') | data
            p = components.get('tmux') | components
            return d, p
        return self._eval(args, L(self.root.eval_expr)(_, mod))

    @autocmd()
    def vim_resized(self):
        if self.root is not None:
            self.root.send(Resized())

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
        return self.root.data.commands.history / unite_format

    @unite_candidates('commands')
    def myo_unite_commands_candidates(self, args):
        return self.root.data.commands.commands / unite_format

    @unite_action('run', 'name')
    def myo_unite_run(self, ident):
        return Run(ident, options=Map())

    @unite_action('delete', 'ident')
    def myo_unite_delete(self, ident):
        return DeleteHistory(ident)

__all__ = ('MyoNvimPlugin',)

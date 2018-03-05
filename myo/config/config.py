from amino import List, Map

# from ribosome.request.handler.handler import RequestHandler
# from ribosome.components.scratch import Mapping
# from ribosome.trans.messages import UpdateRecord
from ribosome.config.config import Config

# from myo.logging import Logging
# from myo.components.command.message import (AddVimCommand, Run, AddShellCommand, AddShell, ShellRun, RunTest,
#                                             RunVimTest, CommandShow, RunLatest, RunLine, RunChained, RebootCommand,
#                                             CommandHistoryShow)
# from myo.components.tmux.message import (TmuxCreatePane, TmuxCreateSession, TmuxCreateLayout, TmuxSpawnSession,
#                                          TmuxInfo, TmuxClosePane, TmuxPack, TmuxMinimize, TmuxRestore, TmuxToggle,
#                                          TmuxFocus, TmuxOpenOrToggle, TmuxKill)
# from myo.components.tmux.message import TmuxOpen
# from myo.components.core.message import Parse, Resized
# from myo.components.unite.message import UniteHistory, UniteCommands
# from myo.components.unite.main import UniteNames, Unite
# from myo.components.unite.format import unite_format
# from myo.output.machine import EventPrev, EventNext
from myo.env import Env
# from myo.components.core.main import Core
# from myo.components.command.main import Cmd
# from myo.components.tmux.main import Tmux
from myo.settings import MyoSettings
from myo.config.component import MyoComponent
from myo.components.core.config import core
from myo.components.command.config import command
from myo.components.tmux.config import tmux
from myo.components.ui.config import ui

# unite_candidates = mk_unite_candidates(UniteNames)
# unite_action = mk_unite_action(UniteNames)

myo_config: Config = Config.cons(
    name='myo',
    prefix='myo',
    state_ctor=Env.cons,
    component_config_type=MyoComponent,
    components=Map(core=core, command=command, ui=ui, tmux=tmux),
    settings=MyoSettings(),
    request_handlers=List(
        # RequestHandler.msg_cmd(AddVimCommand)(json=true),
        # RequestHandler.msg_cmd(AddShellCommand)(json=true),
        # RequestHandler.msg_cmd(AddShell)(json=true),
        # RequestHandler.msg_cmd(TmuxCreateSession)(json=true),
        # RequestHandler.msg_cmd(TmuxSpawnSession)(),
        # RequestHandler.msg_cmd(TmuxCreateLayout)(json=true),
        # RequestHandler.msg_cmd(TmuxCreatePane)(json=true),
        # RequestHandler.msg_cmd(TmuxOpen)(json=true),
        # RequestHandler.msg_cmd(TmuxClosePane)(),
        # RequestHandler.msg_cmd(TmuxPack)(),
        # RequestHandler.msg_cmd(TmuxMinimize)(json=true),
        # RequestHandler.msg_cmd(TmuxRestore)(json=true),
        # RequestHandler.msg_cmd(TmuxToggle)(json=true),
        # RequestHandler.msg_cmd(TmuxOpenOrToggle)(),
        # RequestHandler.msg_cmd(TmuxFocus)(),
        # RequestHandler.msg_cmd(TmuxKill)(json=true),
        # RequestHandler.msg_cmd(Run)(json=true),
        # RequestHandler.msg_cmd(RunLine)(),
        # RequestHandler.msg_cmd(ShellRun)(json=true),
        # RequestHandler.msg_cmd(RunLatest)(json=true),
        # RequestHandler.msg_cmd(RunChained)(),
        # RequestHandler.msg_cmd(RebootCommand)(json=true),
        # RequestHandler.msg_cmd(TmuxInfo)(),
        # RequestHandler.msg_cmd(CommandShow)(),
        # RequestHandler.msg_cmd(CommandHistoryShow)(),
        # RequestHandler.msg_cmd(Parse)(json=true),
        # RequestHandler.msg_cmd(EventPrev)(),
        # RequestHandler.msg_cmd(EventNext)(),
        # RequestHandler.msg_cmd(RunTest)(json=true),
        # RequestHandler.msg_cmd(RunVimTest)(json=true),
        # RequestHandler.msg_cmd(UpdateRecord)(json=true),
        # RequestHandler.msg_function(Mapping)(),
        # RequestHandler.msg_cmd(UniteHistory)(),
        # RequestHandler.msg_cmd(UniteCommands)(),
        # RequestHandler.msg_autocmd(Resized)(),
    ),
    core_components=List('core'),
    default_components=List('command', 'ui', 'tmux'),
)


# @unite_plugin('myo')
# class MyoNvimPlugin(AutoPlugin, Logging):

#     def _eval(self, args, go):
#         result = List.wrap(args).head.to_either('expression needed') // go
#         return result.cata(self.log.error, I)

#     @function()
#     def myo_eval(self, args):
#         return self._eval(args, self.root.eval_expr)

#     @function()
#     def myo_tmux_eval(self, args):
#         def mod(data, components):
#             d = data.sub_states.get('tmux') | data
#             p = components.get('tmux') | components
#             return d, p
#         return self._eval(args, L(self.root.eval_expr)(_, mod))

#     @unite_candidates('history')
#     def myo_unite_history_candidates(self, args):
#         return self.root.data.commands.history / unite_format

#     @unite_candidates('commands')
#     def myo_unite_commands_candidates(self, args):
#         return self.root.data.commands.commands / unite_format

#     @unite_action('run', 'name')
#     def myo_unite_run(self, ident):
#         return Run(ident, options=Map())

#     @unite_action('delete', 'ident')
#     def myo_unite_delete(self, ident):
#         return DeleteHistory(ident)

__all__ = ('myo_config')

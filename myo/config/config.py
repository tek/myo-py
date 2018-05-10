from amino import List, Map

from ribosome.config.config import Config

from myo.env import Env
from myo.components.core.config import core
from myo.components.command.config import command
from myo.components.tmux.config import tmux
from myo.components.ui.config import ui
from myo.components.core.compute.init import init

myo_config: Config = Config.cons(
    name='myo',
    prefix='myo',
    state_ctor=Env.cons,
    components=Map(core=core, command=command, ui=ui, tmux=tmux),
    core_components=List('core'),
    default_components=List('command', 'ui', 'tmux'),
    init=init,
)

__all__ = ('myo_config')

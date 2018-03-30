from typing import Tuple, Any

from amino import do, Do, Map

from ribosome.nvim.io.compute import NvimIO
from ribosome.test.integration.run import DispatchHelper, dispatch_helper
from ribosome.dispatch.component import ComponentData
from ribosome.plugin_state import DispatchAffiliation, ComponentDispatch
from ribosome.config.config import Config
from ribosome.nvim.io.api import N

from myo.env import Env
from myo.components.command.config import command
from myo.config.component import MyoComponent
from myo.settings import MyoSettings


command_spec_config = Config.cons(
    name='myo',
    prefix='myo',
    state_ctor=Env.cons,
    components=Map(command=command),
    component_config_type=MyoComponent,
    settings=MyoSettings(),
)


@do(NvimIO[Tuple[DispatchHelper, ComponentData[Env, DispatchAffiliation]]])
def command_spec_data(**command_data: Any) -> Do:
    helper = yield dispatch_helper(command_spec_config, 'command')
    helper1 = helper.update_component('command', **command_data)
    compo = yield N.from_either(helper.state.component('command'))
    compo_data = helper1.state.data_for(compo)
    return helper1, ComponentDispatch(compo), compo_data

__all__ = ('command_spec_data',)

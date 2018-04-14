from typing import Tuple, Any

from amino import do, Do, Map

from ribosome.nvim.io.compute import NvimIO
from ribosome.test.integration.run import RequestHelper, request_helper
from ribosome.config.config import Config
from ribosome.nvim.io.api import N

from myo.env import Env
from myo.components.command.config import command
from myo.settings import MyoSettings


command_spec_config = Config.cons(
    name='myo',
    prefix='myo',
    state_ctor=Env.cons,
    components=Map(command=command),
    settings=MyoSettings(),
)


@do(NvimIO[Tuple[RequestHelper, Any]])
def command_spec_data(**command_data: Any) -> Do:
    helper = yield request_helper(command_spec_config, 'command')
    return helper.update_component('command', **command_data)


__all__ = ('command_spec_data',)

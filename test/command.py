from typing import Any

from amino import Map, List

from ribosome.config.config import Config
from ribosome.test.config import TestConfig
from ribosome.nvim.io.state import NS
from ribosome.data.plugin_state import PS

from myo.env import Env
from myo.components.command.config import command
from myo.components.command.data import CommandData
from myo.components.core.config import core

from test.data import update_data


command_spec_config = Config.cons(
    name='myo',
    prefix='myo',
    state_ctor=Env.cons,
    components=Map(core=core, command=command),
)
vars = Map(
    myo_builtin_output_config=False,
)
command_spec_test_config = TestConfig.cons(command_spec_config, components=List('command'), vars=vars)


def update_command_data(**command_data: Any) -> NS[PS, None]:
    return update_data(CommandData, **command_data)


__all__ = ('command_spec_test_config', 'update_command_data',)

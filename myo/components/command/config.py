from amino import List, Map, Maybe, Just, Nothing
from amino.boolean import true

from ribosome.config.component import Component
from ribosome.rpc.api import rpc
from ribosome.compute.program import Program
from ribosome.data.mapping import Mappings

from myo.components.command.compute.add import add_system_command, add_vim_command, add_shell_command
from myo.components.command.compute.run import run, run_line, internal_can_run, run_internal_command, rerun
from myo.config.component import MyoComponent
from myo.components.command.data import CommandData
from myo.components.command.compute.parse import parse
from myo.components.command.compute.output import (current_event_jump, jump_mapping, quit_mapping, quit_output,
                                                 prev_mapping, prev_event, next_mapping, next_event)
from myo.command.run_task import RunTask
from myo.components.command.compute.test import vim_test
from myo.components.command.compute.vim_test_wrappers import (test_determine_runner, test_executable,
                                                              test_build_position, test_build_args)
from myo.components.command.compute.kill import kill
from myo.components.command.compute.reboot import reboot
from myo.components.command.compute.history import history
from myo.components.command.compute.init import command_init


def run_handler_for(task: RunTask) -> Maybe[Program]:
    return Just(run_internal_command) if internal_can_run(task) else Nothing


command: Component[CommandData, MyoComponent] = Component.cons(
    'command',
    state_type=CommandData,
    rpc=List(
        rpc.write(add_vim_command).conf(json=true),
        rpc.write(add_system_command).conf(json=true),
        rpc.write(add_shell_command).conf(json=true),
        rpc.write(run).conf(json=true),
        rpc.write(run_line).conf(name=Just('line'), json=true),
        rpc.write(rerun),
        rpc.write(parse).conf(json=true),
        rpc.write(current_event_jump),
        rpc.write(quit_output),
        rpc.write(prev_event),
        rpc.write(next_event),
        rpc.write(vim_test).conf(json=true),
        rpc.write(kill),
        rpc.write(reboot),
        rpc.read(history),
        rpc.read(test_determine_runner),
        rpc.read(test_executable),
        rpc.read(test_build_position),
        rpc.read(test_build_args),
    ),
    config=MyoComponent.cons(run=run_handler_for, init=command_init),
    mappings=Mappings.cons(
        (jump_mapping, current_event_jump),
        (quit_mapping, quit_output),
        (prev_mapping, prev_event),
        (next_mapping, next_event),
    ),
)

__all__ = ('command',)

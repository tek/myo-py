from amino import List, Map, Maybe, Just, Nothing
from amino.boolean import true

from ribosome.config.component import Component
from ribosome.request.handler.handler import RequestHandler
from ribosome.compute.prog import Program
from ribosome.data.mapping import Mappings

from myo.components.command.compute.add import add_system_command, add_vim_command, add_shell_command
from myo.components.command.compute.run import run_command, run_line, internal_can_run, run_internal_command
from myo.config.component import MyoComponent
from myo.components.command.data import CommandData
from myo.components.command.compute.parse import parse
from myo.components.command.compute.output import (current_entry_jump, jump_mapping, quit_mapping, quit_output,
                                                 prev_mapping, prev_entry, next_mapping, next_entry)
from myo.command.run_task import RunTask
from myo.components.command.compute.test import vim_test
from myo.components.command.compute.init import init


def run_handler_for(task: RunTask) -> Maybe[Program]:
    return Just(run_internal_command) if internal_can_run(task) else Nothing


command = Component.cons(
    'command',
    state_type=CommandData,
    request_handlers=List(
        RequestHandler.trans_cmd(add_vim_command)(json=true),
        RequestHandler.trans_cmd(add_system_command)(json=true),
        RequestHandler.trans_cmd(add_shell_command)(json=true),
        RequestHandler.trans_cmd(run_command)(json=true),
        RequestHandler.trans_cmd(run_line)(name='line', json=true),
        RequestHandler.trans_cmd(parse)(json=true),
        RequestHandler.trans_cmd(current_entry_jump)(),
        RequestHandler.trans_cmd(quit_output)(),
        RequestHandler.trans_cmd(prev_entry)(),
        RequestHandler.trans_cmd(next_entry)(),
        RequestHandler.trans_cmd(vim_test)(),
        RequestHandler.trans_function(init)(),
    ),
    config=MyoComponent.cons(run=run_handler_for, init=init),
    mappings=Mappings.cons(Map({
        jump_mapping: current_entry_jump,
        quit_mapping: quit_output,
        prev_mapping: prev_entry,
        next_mapping: next_entry,
    })),
)

__all__ = ('command',)

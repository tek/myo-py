from amino import List, Map, Maybe, Just, Nothing
from amino.boolean import true

from ribosome.dispatch.component import Component
from ribosome.request.handler.handler import RequestHandler
from ribosome.dispatch.mapping import Mappings
from ribosome.trans.handler import TransHandler

from myo.components.command.trans.add import add_system_command, add_vim_command, add_shell_command
from myo.components.command.trans.run import run_command, run_line, internal_can_run, run_internal_command
from myo.config.component import MyoComponent
from myo.components.command.data import CommandData
from myo.components.command.trans.parse import parse
from myo.components.command.trans.output import (current_entry_jump, jump_mapping, quit_mapping, quit_output,
                                                 prev_mapping, prev_entry, next_mapping, next_entry)
from myo.command.run_task import RunTask
from myo.components.command.trans.test import vim_test
from myo.components.command.trans.init import stage1


def run_handler_for(task: RunTask) -> Maybe[TransHandler]:
    return Just(run_internal_command) if internal_can_run(task) else Nothing


command = Component.cons(
    'command',
    state_ctor=CommandData.cons,
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
        RequestHandler.trans_cmd(stage1)(),
    ),
    config=MyoComponent.cons(run_handler_for),
    mappings=Mappings.cons(Map({
        jump_mapping: current_entry_jump,
        quit_mapping: quit_output,
        prev_mapping: prev_entry,
        next_mapping: next_entry,
    }))
)

__all__ = ('command',)

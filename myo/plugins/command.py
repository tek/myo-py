from trypnv.machine import may_handle, message

from myo.state import MyoComponent
from myo.command import Command, VimCommand

Run = message('Run', 'command')
AddCommand = message('AddCommand', 'params')
AddVimCommand = message('AddVimCommand', 'name', 'params')


class Plugin(MyoComponent):

    @may_handle(AddCommand)
    def add_command(self, env, msg):
        self.log.verbose(msg.params)
        return env + Command(*msg.params)

    @may_handle(AddVimCommand)
    def add_vim_command(self, env, msg):
        self.log.verbose(msg.params)
        return env + VimCommand(*msg.params)

    @may_handle(Run)
    def run(self, env, msg):
        self.log.error(msg.command)

__all__ = ('Plugin', 'AddVimCommand', 'AddCommand')

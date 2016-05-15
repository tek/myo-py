from trypnv.machine import may_handle, message, handle

from myo.state import MyoComponent, MyoTransitions
from myo.command import Command, VimCommand, ShellCommand

Run = message('Run', 'command')
AddCommand = message('AddCommand', 'params')
AddShellCommand = message('AddShellCommand', 'params')
AddVimCommand = message('AddVimCommand', 'name', 'params')


class Plugin(MyoComponent):

    class Transitions(MyoTransitions):

        @may_handle(AddCommand)
        def add_command(self):
            self.log.verbose(self.msg.params)
            return self.data + Command(**self.msg.params)

        @may_handle(AddVimCommand)
        def add_vim_command(self):
            self.log.verbose(self.msg.params)
            return self.data + VimCommand(**self.msg.params)

        @may_handle(AddShellCommand)
        def add_shell_command(self):
            self.log.verbose(self.msg.params)
            self.log.verbose(self.data + ShellCommand(**self.msg.params))
            return self.data + ShellCommand(**self.msg.params)

        @handle(Run)
        def run(self):
            return (self.data.command(self.msg.command) //
                    self.data.dispatch_message)

__all__ = ('Plugin', 'AddVimCommand', 'AddCommand')

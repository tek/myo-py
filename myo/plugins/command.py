from trypnv.machine import may_handle, message, handle

from myo.state import MyoComponent, MyoTransitions

from tryp import L, _
from myo.command import Command, VimCommand, ShellCommand

Run = message('Run', 'command', 'options')
AddCommand = message('AddCommand', 'name', 'options')
AddShellCommand = message('AddShellCommand', 'name', 'options')
AddVimCommand = message('AddVimCommand', 'name', 'options')


class Plugin(MyoComponent):

    class Transitions(MyoTransitions):

        @may_handle(AddCommand)
        def add_command(self):
            return self.data + Command(name=self.msg.name, **self.msg.options)

        @may_handle(AddVimCommand)
        def add_vim_command(self):
            return self.data + VimCommand(name=self.msg.name,
                                          **self.msg.options)

        @may_handle(AddShellCommand)
        def add_shell_command(self):
            return self.data + ShellCommand(name=self.msg.name,
                                            **self.msg.options)

        @handle(Run)
        def run(self):
            return (
                self.data.command(self.msg.command) //
                L(self.data.dispatch_message)(_, self.msg.options) /
                _.pub
            )

__all__ = ('Plugin', 'AddVimCommand', 'AddCommand')

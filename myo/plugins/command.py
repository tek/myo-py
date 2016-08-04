from collections import namedtuple

from trypnv.machine import may_handle, message, handle

from myo.state import MyoComponent, MyoTransitions

from tryp import L, _
from myo.command import Command, VimCommand, ShellCommand, Shell

Run = message('Run', 'command', 'options')
ShellRun = message('ShellRun', 'shell', 'options')
AddCommand = message('AddCommand', 'name', 'options')
AddShellCommand = message('AddShellCommand', 'name', 'options')
AddShell = message('AddShell', 'name', 'options')
AddVimCommand = message('AddVimCommand', 'name', 'options')

RunInShell = namedtuple('RunInShell', ['shell'])


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

        @may_handle(AddShell)
        def add_shell(self):
            return self.data + Shell(name=self.msg.name, **self.msg.options)

        @handle(Run)
        def run(self):
            return (
                self.data.command(self.msg.command) //
                L(self.data.dispatch_message)(_, self.msg.options) /
                _.pub
            )

        @handle(ShellRun)
        def run_in_shell(self):
            return (
                self.data.shell(self.msg.shell) /
                RunInShell //
                L(self.data.dispatch_message)(_, self.msg.options) /
                _.pub
            )

__all__ = ('Plugin', 'AddVimCommand', 'AddCommand', 'Run', 'AddShell',
           'AddShellCommand')

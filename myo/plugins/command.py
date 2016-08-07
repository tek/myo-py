from collections import namedtuple

from trypnv.machine import may_handle, message, handle, Nop

from myo.state import MyoComponent, MyoTransitions

from tryp import L, _, List
from myo.command import Command, VimCommand, ShellCommand, Shell
from myo.util import optional_params

Run = message('Run', 'command', 'options')
ShellRun = message('ShellRun', 'shell', 'options')
AddCommand = message('AddCommand', 'name', 'options')
AddShellCommand = message('AddShellCommand', 'name', 'options')
AddShell = message('AddShell', 'name', 'options')
AddVimCommand = message('AddVimCommand', 'name', 'options')
SetShellTarget = message('SetShellTarget', 'shell', 'target')

RunInShell = namedtuple('RunInShell', ['shell'])


class Plugin(MyoComponent):

    class Transitions(MyoTransitions):

        def _create(self, tpe: type, mand_keys: List[str], opt_keys: List[str],
                    **strict):
            o = self.msg.options
            opt = optional_params(o, *opt_keys)
            missing = lambda: mand_keys.filter(o.has_key)
            err = lambda: 'cannot create {} without params: {}'.format(missing)
            mand = o.get_all_map(*mand_keys).to_either(err)
            return mand / (lambda a: tpe(**a, **opt, **strict))

        def _add(self, tpe: type, mand_keys: List[str], opt_keys: List[str],
                 **strict):
            return (
                self._create(tpe, mand_keys, opt_keys, **strict) /
                self.data.cat
            )

        @handle(AddCommand)
        def add_command(self):
            return self._add(Command, List('line'), List(), name=self.msg.name)

        @may_handle(AddVimCommand)
        def add_vim_command(self):
            return self._add(VimCommand, List('line'), List(),
                             name=self.msg.name)

        @handle(AddShellCommand)
        def add_shell_command(self):
            return self._add(ShellCommand, List('line'), List('shell'),
                             name=self.msg.name)

        @handle(AddShell)
        def add_shell(self):
            mand = List('line')
            opt = List('target')
            return self._create(Shell, mand, opt, name=self.msg.name) / (
                lambda shell: (
                    self.data + shell,
                    shell.target / L(SetShellTarget)(shell, _) / _.pub | Nop
                )
            )

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
           'AddShellCommand', 'SetShellTarget')

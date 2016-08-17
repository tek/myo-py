from trypnv.machine import message

Run = message('Run', 'command', 'options')
ShellRun = message('ShellRun', 'shell', 'options')
Dispatch = message('Dispatch', 'command', 'options')
AddCommand = message('AddCommand', 'name', 'options')
AddShellCommand = message('AddShellCommand', 'name', 'options')
AddShell = message('AddShell', 'name', 'options')
AddVimCommand = message('AddVimCommand', 'name', 'options')
SetShellTarget = message('SetShellTarget', 'shell', 'target')
CommandExecuted = message('CommandExecuted', 'command')

__all__ = ('Run', 'ShellRun', 'Dispatch', 'AddCommand', 'AddShellCommand',
           'AddShell', 'AddVimCommand', 'SetShellTarget', 'CommandExecuted')

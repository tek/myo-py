from ribosome.machine import message, json_message

Run = json_message('Run', 'command')
ShellRun = json_message('ShellRun', 'shell')
RunTest = json_message('RunTest')
RunVimTest = json_message('RunVimTest')
Dispatch = json_message('Dispatch', 'command')
AddCommand = json_message('AddCommand', 'name')
AddShellCommand = json_message('AddShellCommand', 'name')
AddShell = json_message('AddShell', 'name')
AddVimCommand = json_message('AddVimCommand', 'name')
SetShellTarget = message('SetShellTarget', 'shell', 'target')
CommandExecuted = message('CommandExecuted', 'command')

__all__ = ('Run', 'ShellRun', 'Dispatch', 'AddCommand', 'AddShellCommand',
           'AddShell', 'AddVimCommand', 'SetShellTarget', 'CommandExecuted',
           'RunTest', 'RunVimTest')

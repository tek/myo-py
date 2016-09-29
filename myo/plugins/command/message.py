from ribosome.machine import message, json_message

Run = json_message('Run', 'command')
RunLine = message('RunLine', varargs='args')
ShellRun = json_message('ShellRun', 'shell')
RunLatest = json_message('RunLatest')
RunTest = json_message('RunTest')
RunVimTest = json_message('RunVimTest')
Dispatch = json_message('Dispatch', 'command')
AddCommand = json_message('AddCommand', 'name')
AddShellCommand = json_message('AddShellCommand', 'name')
AddShell = json_message('AddShell', 'name')
AddVimCommand = json_message('AddVimCommand', 'name')
SetShellTarget = message('SetShellTarget', 'shell', 'target')
CommandAdded = json_message('CommandAdded', 'command')
CommandExecuted = message('CommandExecuted', 'command')
CommandShow = message('CommandShow')
LoadHistory = message('LoadHistory')
StoreHistory = message('StoreHistory')

__all__ = ('Run', 'ShellRun', 'Dispatch', 'AddCommand', 'AddShellCommand',
           'AddShell', 'AddVimCommand', 'SetShellTarget', 'CommandExecuted',
           'RunTest', 'RunVimTest', 'CommandAdded', 'CommandShow', 'RunLatest',
           'LoadHistory', 'StoreHistory', 'RunLine')

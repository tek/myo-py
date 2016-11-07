from ribosome.machine import message, json_message

Run = json_message('Run', 'command')
RunLine = message('RunLine', 'target', varargs='args')
ShellRun = json_message('ShellRun', 'shell')
RunLatest = json_message('RunLatest')
RunTest = json_message('RunTest')
RunVimTest = json_message('RunVimTest')
RunIn = json_message('RunIn', 'target', 'line')
RunChained = message('RunChained', varargs='commands')
Dispatch = json_message('Dispatch', 'command')
AddCommand = json_message('AddCommand', 'name')
AddShellCommand = json_message('AddShellCommand', 'name')
AddShell = json_message('AddShell', 'name')
AddVimCommand = json_message('AddVimCommand', 'name')
SetShellTarget = message('SetShellTarget', 'shell', 'target')
CommandAdded = json_message('CommandAdded', 'command')
CommandExecuted = message('CommandExecuted', 'job', 'log_path')
CommandShow = message('CommandShow')
LoadHistory = message('LoadHistory')
StoreHistory = message('StoreHistory')

__all__ = ('Run', 'ShellRun', 'Dispatch', 'AddCommand', 'AddShellCommand',
           'AddShell', 'AddVimCommand', 'SetShellTarget', 'CommandExecuted',
           'RunTest', 'RunVimTest', 'CommandAdded', 'CommandShow', 'RunLatest',
           'LoadHistory', 'StoreHistory', 'RunLine', 'RunIn', 'RunChained')

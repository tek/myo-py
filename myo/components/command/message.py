from ribosome.trans.message_base import pmessage, json_pmessage

Run = json_pmessage('Run', 'command')
RunLine = pmessage('RunLine', 'target', varargs='args')
ShellRun = json_pmessage('ShellRun', 'shell')
RunLatest = json_pmessage('RunLatest')
RunTest = json_pmessage('RunTest')
RunVimTest = json_pmessage('RunVimTest')
RunIn = json_pmessage('RunIn', 'target', 'line')
RunChained = pmessage('RunChained', varargs='commands')
RebootCommand = json_pmessage('RebootCommand', 'command')
Dispatch = json_pmessage('Dispatch', 'command')
AddCommand = json_pmessage('AddCommand', 'name')
AddShellCommand = json_pmessage('AddShellCommand', 'name')
AddShell = json_pmessage('AddShell', 'name')
AddVimCommand = json_pmessage('AddVimCommand', 'name')
SetShellTarget = pmessage('SetShellTarget', 'shell', 'target')
CommandAdded = json_pmessage('CommandAdded', 'command')
CommandExecuted = pmessage('CommandExecuted', 'job', 'log_path')
CommandShow = pmessage('CommandShow')
CommandHistoryShow = pmessage('CommandHistoryShow')
LoadHistory = pmessage('LoadHistory')
StoreHistory = pmessage('StoreHistory')
DeleteHistory = pmessage('DeleteHistory', 'ident')
StoreTestParams = pmessage('StoreTestParams', 'params')

__all__ = ('Run', 'RunLine', 'ShellRun', 'RunLatest', 'RunTest', 'RunVimTest', 'RunIn', 'RunChained', 'RebootCommand',
           'Dispatch', 'AddCommand', 'AddShellCommand', 'AddShell', 'AddVimCommand', 'SetShellTarget', 'CommandAdded',
           'CommandExecuted', 'CommandShow', 'CommandHistoryShow', 'LoadHistory', 'StoreHistory', 'DeleteHistory',
           'StoreTestParams')

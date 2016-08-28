from ribosome.machine import message, json_message

TmuxRunCommand = json_message('TmuxRunCommand', 'command')
TmuxRunShell = json_message('TmuxRunShell', 'shell')
TmuxRunCommandInShell = message('TmuxRunCommandInShell', 'shell', 'command',
                                'options')
TmuxRunLineInShell = json_message('TmuxRunLineInShell', 'shell')
TmuxCreateSession = json_message('TmuxCreateSession')
TmuxSpawnSession = message('TmuxSpawnSession', 'id')
TmuxCreateLayout = json_message('TmuxCreateLayout', 'name')
TmuxCreatePane = json_message('TmuxCreatePane', 'name')
TmuxOpenPane = json_message('TmuxOpenPane', 'name')
TmuxClosePane = message('TmuxClosePane', 'name')
TmuxFindVim = message('TmuxFindVim')
TmuxLoadDefaults = message('TmuxLoadDefaults')
TmuxInfo = message('TmuxInfo')
TmuxParse = json_message('TmuxParse')
TmuxPack = message('TmuxPack')
SetCommandLog = message('SetCommandLog', 'cmd_ident', 'pane_ident')

StartWatcher = message('StartWatcher')
QuitWatcher = message('QuitWatcher')
WatchCommand = message('WatchCommand', 'command', 'pane')

__all__ = ('TmuxRunCommand', 'TmuxOpenPane', 'TmuxCreatePane',
           'TmuxCreateSession', 'TmuxCreateLayout', 'TmuxCreateLayout',
           'TmuxSpawnSession', 'TmuxFindVim', 'TmuxLoadDefaults',
           'TmuxClosePane', 'TmuxRunCommandInShell', 'TmuxRunLineInShell',
           'TmuxRunShell', 'StartWatcher', 'WatchCommand', 'QuitWatcher',
           'TmuxParse', 'SetCommandLog', 'TmuxPack')

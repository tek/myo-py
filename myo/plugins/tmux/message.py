from ribosome.machine import message, json_message

TmuxRunCommand = json_message('TmuxRunCommand', 'job')
TmuxRunCommandInShell = message('TmuxRunCommandInShell', 'shell', 'command',
                                'options')
TmuxRunLineInShell = json_message('TmuxRunLineInShell', 'shell')
TmuxRunTransient = json_message('TmuxRunTransient', 'cmd')
TmuxRebootCommand = json_message('TmuxRebootCommand', 'job')
TmuxCreateSession = json_message('TmuxCreateSession')
TmuxSpawnSession = message('TmuxSpawnSession', 'id')
TmuxCreateLayout = json_message('TmuxCreateLayout', 'name')
TmuxCreatePane = json_message('TmuxCreatePane', 'name')
TmuxOpen = json_message('TmuxOpen', 'name')
TmuxClosePane = message('TmuxClosePane', 'name')
TmuxFindVim = message('TmuxFindVim')
TmuxLoadDefaults = message('TmuxLoadDefaults')
TmuxInfo = message('TmuxInfo')
TmuxParse = json_message('TmuxParse')
TmuxPack = message('TmuxPack')
TmuxPostOpen = json_message('TmuxPostOpen', 'ident')
TmuxPostCommand = message('TmuxPostCommand', 'job', 'pane_ident')
TmuxFixFocus = message('TmuxFixFocus', 'pane')
TmuxFocus = message('TmuxFocus', 'pane')
TmuxMinimize = json_message('TmuxMinimize', 'pane')
TmuxRestore = json_message('TmuxRestore', 'pane')
TmuxToggle = json_message('TmuxToggle', 'pane')
TmuxOpenOrToggle = json_message('TmuxOpenOrToggle', 'pane')
TmuxKill = json_message('TmuxKill', 'pane')
UpdateVimWindow = message('UpdateVimWindow')

StartWatcher = message('StartWatcher')
QuitWatcher = message('QuitWatcher')
WatchCommand = message('WatchCommand', 'command', 'pane')

__all__ = ('TmuxRunCommand', 'TmuxOpen', 'TmuxCreatePane', 'TmuxCreateSession',
           'TmuxCreateLayout', 'TmuxCreateLayout', 'TmuxSpawnSession',
           'TmuxFindVim', 'TmuxLoadDefaults', 'TmuxClosePane',
           'TmuxRunCommandInShell', 'TmuxRunLineInShell',
           'StartWatcher', 'WatchCommand', 'QuitWatcher', 'TmuxParse',
           'TmuxPack', 'TmuxPostOpen', 'TmuxFixFocus', 'TmuxMinimize',
           'TmuxRestore', 'TmuxToggle', 'TmuxFocus', 'TmuxOpenOrToggle',
           'TmuxKill', 'UpdateVimWindow', 'TmuxRunTransient',
           'TmuxPostCommand', 'TmuxRebootCommand')

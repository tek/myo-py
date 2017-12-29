from ribosome.trans.message_base import pmessage, json_pmessage

TmuxRunCommand = json_pmessage('TmuxRunCommand', 'job')
TmuxRunCommandInShell = pmessage('TmuxRunCommandInShell', 'shell', 'command',
                                'options')
TmuxRunLineInShell = json_pmessage('TmuxRunLineInShell', 'shell')
TmuxRunTransient = json_pmessage('TmuxRunTransient', 'cmd')
TmuxRebootCommand = json_pmessage('TmuxRebootCommand', 'job')
TmuxCreateSession = json_pmessage('TmuxCreateSession')
TmuxSpawnSession = pmessage('TmuxSpawnSession', 'id')
TmuxCreateLayout = json_pmessage('TmuxCreateLayout', 'name')
TmuxCreatePane = json_pmessage('TmuxCreatePane', 'name')
TmuxOpen = json_pmessage('TmuxOpen', 'name')
TmuxClosePane = pmessage('TmuxClosePane', 'name')
TmuxFindVim = pmessage('TmuxFindVim')
TmuxLoadDefaults = pmessage('TmuxLoadDefaults')
TmuxInfo = pmessage('TmuxInfo')
TmuxParse = json_pmessage('TmuxParse')
TmuxPack = pmessage('TmuxPack')
TmuxPostOpen = json_pmessage('TmuxPostOpen', 'ident')
TmuxPostCommand = pmessage('TmuxPostCommand', 'job', 'pane_ident')
TmuxFixFocus = pmessage('TmuxFixFocus', 'pane')
TmuxFocus = pmessage('TmuxFocus', 'pane')
TmuxMinimize = json_pmessage('TmuxMinimize', 'pane')
TmuxRestore = json_pmessage('TmuxRestore', 'pane')
TmuxToggle = json_pmessage('TmuxToggle', 'pane')
TmuxOpenOrToggle = json_pmessage('TmuxOpenOrToggle', 'pane')
TmuxKill = json_pmessage('TmuxKill', 'pane')
UpdateVimWindow = pmessage('UpdateVimWindow')

StartWatcher = pmessage('StartWatcher')
QuitWatcher = pmessage('QuitWatcher')
WatchCommand = pmessage('WatchCommand', 'command', 'pane')

__all__ = ('TmuxRunCommand', 'TmuxOpen', 'TmuxCreatePane', 'TmuxCreateSession', 'TmuxCreateLayout', 'TmuxCreateLayout',
           'TmuxSpawnSession', 'TmuxFindVim', 'TmuxLoadDefaults', 'TmuxClosePane', 'TmuxRunCommandInShell',
           'TmuxRunLineInShell', 'StartWatcher', 'WatchCommand', 'QuitWatcher', 'TmuxParse', 'TmuxPack', 'TmuxPostOpen',
           'TmuxFixFocus', 'TmuxMinimize', 'TmuxRestore', 'TmuxToggle', 'TmuxFocus', 'TmuxOpenOrToggle', 'TmuxKill',
           'UpdateVimWindow', 'TmuxRunTransient', 'TmuxPostCommand', 'TmuxRebootCommand')

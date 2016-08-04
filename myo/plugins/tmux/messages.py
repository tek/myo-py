from trypnv.machine import message

TmuxRunCommand = message('TmuxRunCommand', 'command', 'options')
TmuxRunShell = message('TmuxRunShell', 'shell', 'options')
TmuxRunCommandInShell = message('TmuxRunCommandInShell', 'shell', 'command',
                                'options')
TmuxRunLineInShell = message('TmuxRunLineInShell', 'shell', 'options')
TmuxCreateSession = message('TmuxCreateSession', 'options')
TmuxSpawnSession = message('TmuxSpawnSession', 'id')
TmuxCreateLayout = message('TmuxCreateLayout', 'name', 'options')
TmuxCreatePane = message('TmuxCreatePane', 'name', 'options')
TmuxOpenPane = message('TmuxOpenPane', 'name', 'options')
TmuxClosePane = message('TmuxClosePane', 'name')
TmuxFindVim = message('TmuxFindVim')
TmuxLoadDefaults = message('TmuxLoadDefaults')
TmuxInfo = message('TmuxInfo')
SetShellTarget = message('SetShellTarget', 'shell', 'pane')

__all__ = ('TmuxRunCommand', 'TmuxOpenPane', 'TmuxCreatePane',
           'TmuxCreateSession', 'TmuxCreateLayout', 'TmuxCreateLayout',
           'TmuxSpawnSession', 'TmuxFindVim', 'TmuxLoadDefaults',
           'TmuxClosePane', 'TmuxRunCommandInShell', 'TmuxRunLineInShell',
           'TmuxRunShell', 'SetShellTarget')

from trypnv.machine import message

TmuxRunCommand = message('TmuxRun', 'command', 'options')
TmuxCreateSession = message('TmuxCreateSession', 'options')
TmuxSpawnSession = message('TmuxSpawnSession', 'id')
TmuxCreateLayout = message('TmuxCreateLayout', 'options')
TmuxCreatePane = message('TmuxCreatePane', 'options')
TmuxOpenPane = message('TmuxOpenPane', 'name', 'options')
TmuxFindVim = message('TmuxFindVim')
TmuxLoadDefaults = message('TmuxLoadDefaults')
TmuxTest = message('TmuxTest')

__all__ = ('TmuxRunCommand', 'TmuxOpenPane', 'TmuxCreatePane',
           'TmuxCreateSession', 'TmuxCreateLayout', 'TmuxCreateLayout',
           'TmuxSpawnSession', 'TmuxFindVim', 'TmuxLoadDefaults')

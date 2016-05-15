from trypnv.machine import message

TmuxRun = message('TmuxRun', 'command', 'options')
TmuxCreateSession = message('TmuxCreateSession', 'options')
TmuxSpawnSession = message('TmuxSpawnSession', 'id')
TmuxCreateLayout = message('TmuxCreateLayout', 'options')
TmuxCreatePane = message('TmuxCreatePane', 'options')
TmuxOpenPane = message('TmuxOpenPane', 'name', 'options')
TmuxFindVim = message('TmuxFindVim')

__all__ = ('TmuxRun', 'TmuxOpenPane', 'TmuxCreatePane', 'TmuxCreateSession',
           'TmuxCreateLayout')

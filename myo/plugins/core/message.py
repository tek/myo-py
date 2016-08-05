from trypnv.machine import message

RunVimCommand = message('RunVimCommand', 'command')
AddDispatcher = message('AddDispatcher')
StageI = message('StageI')
StageII = message('StageII')
Initialized = message('Initialized')

__all__ = ('RunVimCommand', 'AddDispatcher', 'StageI', 'StageII',
           'Initialized')

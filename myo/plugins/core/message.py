from trypnv.machine import message

RunVimCommand = message('RunVimCommand', 'command')
AddDispatcher = message('AddDispatcher')
StageI = message('StageI')
StageII = message('StageII')
Initialized = message('Initialized')
ParseOutput = message('ParseOutput', 'content', 'options')

__all__ = ('RunVimCommand', 'AddDispatcher', 'StageI', 'StageII',
           'Initialized', 'ParseOutput')

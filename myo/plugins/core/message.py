from ribosome.machine import message

RunVimCommand = message('RunVimCommand', 'command')
AddDispatcher = message('AddDispatcher')
StageI = message('StageI')
StageII = message('StageII')
Initialized = message('Initialized')
Parse = message('Parse', 'options')
ParseOutput = message('ParseOutput', 'command', 'output', 'path', 'options')

__all__ = ('RunVimCommand', 'AddDispatcher', 'StageI', 'StageII',
           'Initialized', 'ParseOutput', 'Parse')

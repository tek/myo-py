from ribosome.machine import message, json_message

RunVimCommand = message('RunVimCommand', 'command')
AddDispatcher = message('AddDispatcher')
StageI = message('StageI')
StageII = message('StageII')
Initialized = message('Initialized')
Parse = json_message('Parse')
ParseOutput = json_message('ParseOutput', 'command', 'output', 'path')

__all__ = ('RunVimCommand', 'AddDispatcher', 'StageI', 'StageII',
           'Initialized', 'ParseOutput', 'Parse')

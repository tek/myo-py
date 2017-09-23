from ribosome.machine.message_base import message, json_message

RunVimCommand = message('RunVimCommand', 'command')
AddDispatcher = message('AddDispatcher')
Initialized = message('Initialized')
Parse = json_message('Parse')
ParseOutput = json_message('ParseOutput', 'job', 'output', 'path')
Resized = message('Resized')

__all__ = ('RunVimCommand', 'AddDispatcher', 'Initialized', 'ParseOutput', 'Parse', 'Resized')

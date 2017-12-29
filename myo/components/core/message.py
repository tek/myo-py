from ribosome.trans.message_base import pmessage, json_pmessage

RunVimCommand = pmessage('RunVimCommand', 'command')
AddDispatcher = pmessage('AddDispatcher')
Initialized = pmessage('Initialized')
Parse = json_pmessage('Parse')
ParseOutput = json_pmessage('ParseOutput', 'job', 'output', 'path')
Resized = pmessage('Resized')

__all__ = ('RunVimCommand', 'AddDispatcher', 'Initialized', 'ParseOutput', 'Parse', 'Resized')

from trypnv.machine import message

RunVimCommand = message('RunVimCommand', 'command')
AddDispatcher = message('AddDispatcher')

__all__ = ('RunVimCommand', 'AddDispatcher')

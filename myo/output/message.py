from ribosome.machine import message, json_message

JumpCurrent = message('JumpCurrent')
JumpCursor = message('JumpCursor')
Jump = message('Jump', 'target')
SetLoc = message('SetLoc', 'index', opt_fields=(('jump', True),))
InitialError = message('InitialError')
DisplayLines = message('DisplayLines')
SetResult = json_message('SetResult', 'result')
ToggleFilters = message('ToggleFilters')
EventNext = message('EventNext')
EventPrev = message('EventPrev')
CursorToCurrent = message('CursorToCurrent')

__all__ = ('JumpCurrent', 'JumpCursor', 'Jump', 'SetLoc', 'InitialError', 'DisplayLines', 'SetResult', 'ToggleFilters',
           'EventNext', 'EventPrev', 'CursorToCurrent')

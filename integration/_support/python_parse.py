events = '''  File "/path/to/file", line 2, in funcname
    yield
  File "/path/to/file", line 3, in funcname
    yield
RuntimeError: error
  File "/path/to/file", line 6, in funcname
    yield
  File "/path/to/file", line 7
    wrong =
SyntaxError: error'''

formatted_events = '''/path/to/file  2 funcname
    yield
/path/to/file  3 funcname
    yield
RuntimeError: error
/path/to/file  6 funcname
    yield
/path/to/file  7
    wrong =
SyntaxError: error'''

__all__ = ('events', 'formatted_events',)

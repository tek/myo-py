events = '''  File "/path/to/file", line 2, in funcname
    yield
  File "/path/to/file", line 3, in funcname
    yield
RuntimeError: error
  File "/path/to/file", line 2, in funcname
    yield
  File "/path/to/file", line 3
    wrong =
SyntaxError: error'''

__all__ = ('events',)
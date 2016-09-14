from myo.nvim_plugin import MyoNvimPlugin

from amino import Task


class MyoSpecPlugin(MyoNvimPlugin):

    def __init__(self, vim) -> None:
        # Task.record_stack = True
        super().__init__(vim)

__all__ = ('MyoSpecPlugin',)

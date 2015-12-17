from trypnv.machine import may_handle, message, Message

from myo.state import MyoComponent
from myo.env import Env


Init = message('Init')
Ready = message('Ready')
BufEnter = message('BufEnter', 'buffer')
Initialized = message('Initialized')


class Plugin(MyoComponent):

    @may_handle(Init)
    def init(self, env: Env, msg):
        return BufEnter(self.vim.current_buffer).pub, Initialized()

    @may_handle(Initialized)
    def initialized(self, env, msg):
        return env.set(initialized=True)

__all__ = ['Plugin', 'Init', 'Ready']

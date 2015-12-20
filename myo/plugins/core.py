from trypnv.machine import may_handle, message

from myo.state import MyoComponent
from myo.env import Env


Init = message('Init')
Initialized = message('Initialized')


class Plugin(MyoComponent):

    @may_handle(Init)
    def init(self, env: Env, msg):
        return Initialized()

    @may_handle(Initialized)
    def initialized(self, env, msg):
        return env.set(initialized=True)

__all__ = ['Plugin', 'Init']

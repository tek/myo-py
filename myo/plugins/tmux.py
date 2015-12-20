from trypnv.machine import may_handle, message

from myo.state import MyoComponent

Dispatch = message('Dispatch', 'command', 'options')


class Plugin(MyoComponent):

    @may_handle(Dispatch)
    def dispatch(self, env, msg):
        self.log.verbose(msg.command)
        self.log.verbose(msg.options)

__all__ = ('Plugin')

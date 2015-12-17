from trypnv.machine import may_handle, message, Message

from myo.state import MyoComponent

Run = message('Run', 'command')


class AddVimCommand(Message):

    def __init__(self, params):
        self.params = params


class Plugin(MyoComponent):

    @may_handle(AddVimCommand)
    def add_vim_command(self, env, msg):
        self.log.error(msg.params)

    @may_handle(Run)
    def run(self, env, msg):
        self.log.error(msg.command)

__all__ = ['Plugin', 'AddVimCommand']

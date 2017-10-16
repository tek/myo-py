from ribosome.settings import PluginSettings, state_dir_help_default, float_setting, str_setting

state_dir_help = f'''{state_dir_help_default}
Stored data consists of:
* command history
* last test command line
* last shell used for testing
* layout state
'''
tmux_watcher_interval_help = f'''Tmux panes can be observed for events, like processes terminating.
This specifies the polling interval.
'''
tmux_socket_help = '''The tmux server can be chosen by its socket path. This is mainly intended for tests.
'''


class MyoSettings(PluginSettings):

    def __init__(self) -> None:
        super().__init__('myo', state_dir_help)
        self.tmux_watcher_interval = float_setting('tmux_watcher_interval', 'tmux process polling interval',
                                                   tmux_watcher_interval_help, True, 1.0)
        self.tmux_socket = str_setting('tmux_socket', 'tmux socket path', tmux_socket_help, True, None)

__all__ = ('MyoSettings',)

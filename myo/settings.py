from amino import Right
from amino.boolean import true

from ribosome.config.setting import float_setting, str_setting, int_setting, bool_setting

state_dir_help = f'''
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
vim_tmux_pane_help = '''Skip discovery of the tmux pane hosting neovim by its process id and use the supplied pane id
instead. Particularly helpful for tests.
'''
display_parse_result_help = '''After parsing the output of an executed command, display errors in a scratch buffer.
'''
auto_jump_help = '''When loading the output buffer or cycling through output events, jump to the code location without
hitting the jump key.
'''
vim_test_filename_modifier_help = '''A vim-test setting that is applied to file names.
'''
init_default_ui_help = '''Create space, window, layout and pane for vim and the default execution target at startup.
The default target pane will be positioned to the right of vim.
'''
test_ui_help = '''Tests run with vim-test will be executed in this ui. Can be `tmux` or `internal`.
'''
test_pane_help = '''Tests run with vim-test will be executed in this pane.
'''


tmux_watcher_interval = float_setting('tmux_watcher_interval', 'tmux process polling interval',
                                      tmux_watcher_interval_help, True, Right(1.0))
tmux_socket = str_setting('tmux_socket', 'tmux socket path', tmux_socket_help, True)
vim_tmux_pane = int_setting('vim_tmux_pane', 'vim tmux pane id', vim_tmux_pane_help, True)
display_parse_result = bool_setting('display_parse_result', 'display parse result', display_parse_result_help, True,
                                    Right(true))
auto_jump = bool_setting('auto_jump', 'jump when changing output events', auto_jump_help, True, Right(true))
vim_test_filename_modifier = str_setting('test#filename_modifier', 'vim-test filename modifier',
                                         vim_test_filename_modifier_help, False, Right(':.'))
init_default_ui = bool_setting('init_default_ui', 'initialize vim and make panes', init_default_ui_help, True,
                               Right(true))
test_ui = str_setting('test_ui', 'ui for running tests', test_ui_help, True, Right('tmux'))
test_pane = str_setting('test_pane', 'pane for running tests', test_pane_help, True, Right('make'))


__all__ = ('tmux_watcher_interval', 'tmux_socket', 'vim_tmux_pane', 'display_parse_result', 'auto_jump',
           'vim_test_filename_modifier', 'init_default_ui', 'test_ui', 'test_pane',)

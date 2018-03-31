from kallikrein import Expectation, kf
from kallikrein.matchers.length import have_length

import neovim

from chiasma.test.tmux_spec import tmux_spec_socket
from chiasma.io.compute import TmuxIO
from chiasma.commands.pane import send_keys

from amino import List, do, Do, Path, env

from ribosome.nvim.api.variable import variable_set_prefixed
from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.api.data import Buffer
from ribosome.nvim.api.command import nvim_command
from ribosome.test.integration.klk import later
from ribosome.test.integration.spec import wait_for

from integration._support.spec import TmuxDefaultSpec


class VimPaneSpec(TmuxDefaultSpec):
    '''
    open the pane `make` $open_make
    '''

    def start_neovim(self) -> None:
        env_args = self.vim_proc_env.map2(lambda k, v: f'{k}={v}').cons('env')
        cmd = env_args + self.nvim_cmdline
        if 'VIRTUAL_ENV' in env:
            send_keys(0, List(f'source $VIRTUAL_ENV/bin/activate')).unsafe(self.tmux)
        send_keys(0, List(cmd.join_tokens)).unsafe(self.tmux)
        wait_for(Path(self.nvim_socket).is_socket)
        self.neovim = neovim.attach('socket', path=self.nvim_socket)
        self.neovim.command('python3 sys.path.insert(0, \'{}\')'.format(self.python_path))
        self.vim = self.create_nvim_api(self.neovim)

    def _pre_start(self) -> None:
        @do(NvimIO[None])
        def run() -> Do:
            yield variable_set_prefixed('tmux_socket', tmux_spec_socket)
        run().unsafe(self.vim)
        super()._pre_start()

    def open_make(self) -> Expectation:
        @do(NvimIO[List[Buffer]])
        def run() -> Do:
            yield nvim_command('MyoOpenPane', 'make')
        run().unsafe(self.vim)
        return later(kf(TmuxIO.read('list-panes').unsafe, self.tmux).must(have_length(2)))


__all__ = ('VimPaneSpec',)

from kallikrein import Expectation

from amino.test.spec import SpecBase
from amino import do, Do, List, Lists
from amino.logging import module_log

from ribosome.nvim.io.compute import NvimIO
from ribosome.test.integration.tmux import screenshot, tmux_plugin_test
from ribosome.config.config import Config
from ribosome.compute.api import prog
from ribosome.nvim.io.state import NS
from ribosome.config.basic_config import NoData
from ribosome.rpc.api import rpc
from ribosome.nvim.api.function import nvim_call_function
from ribosome.nvim.api.ui import current_buffer, set_buffer_content
from ribosome.nvim.io.api import N
from ribosome.nvim.api.command import nvim_command, nvim_command_output

from test.tmux import tmux_test_config
from test.output.util import myo_syntax, myo_highlight

from myo.components.command.compute.output import setup_syntax
from myo.output.lang.haskell.syntax import haskell_syntax

log = module_log()


report = '''/path/to/file.hs  38
  !instance: foobar
  TypeClass Data
/path/to/file.hs  43
  Variable not in scope:
  doSomething :: TypeA -> Monad a0
/path/to/file.hs  5
  type mismatch
  t0 Data1 -> StateT (ReaderT e0) ()
  StateT (ReaderT (GHC.Conc.Sync.TVar Data)) a0'''


@prog.unit
@do(NS[NoData, None])
def render() -> Do:
    buf = yield NS.lift(current_buffer())
    yield NS.lift(set_buffer_content(buf, Lists.lines(report)))
    yield setup_syntax(haskell_syntax, 1)


config: Config = Config.cons(
    name='haskell_report',
    rpc=List(
        rpc.write(render),
    ),
    internal_component=False,
)
test_config = tmux_test_config(config)


@do(NvimIO[None])
def test_highlights() -> Do:
    yield nvim_command('highlight Error cterm=bold ctermfg=1')


@do(NvimIO[Expectation])
def report_spec() -> Do:
    yield test_highlights()
    yield nvim_call_function('HaskellReportRender')
    yield N.sleep(2)
    yield screenshot('command', 'haskell_report', 'render')


class HaskellReportSpec(SpecBase):
    '''
    render a report $report
    '''

    def report(self) -> Expectation:
        return tmux_plugin_test(test_config, report_spec)


__all__ = ('HaskellReportSpec',)

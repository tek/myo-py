from kallikrein import Expectation, k
from kallikrein.matchers.lines import have_lines
from kallikrein.matchers import contain
from kallikrein.matchers.end_with import end_with

from integration._support.spec import ExternalSpec, DefaultSpec
from integration._support.command.setup import command_spec_data

from chiasma.util.id import Ident

from amino import do, Do, _, __, List, Lists
from amino.test import fixture_path

from ribosome.nvim.io.compute import NvimIO
from ribosome.test.klk import kn
from ribosome.nvim.io.api import N
from ribosome.nvim.api.function import define_function
from ribosome.nvim.api.ui import buffers, buffer_content
from ribosome.dispatch.execute import eval_trans
from ribosome.dispatch.run import DispatchState
from ribosome.nvim.api.variable import variable_set_prefixed
from ribosome.nvim.api.command import nvim_command

from myo.components.command.trans.test import vim_test, vim_test_command, test_ident
from myo.components.command.trans.run import RunCommandOptions


file = fixture_path('command', 'test', 'code.py')
target = List('  File "<string>", line 1, in <module>', 'RuntimeError: No active exception to reraise')


@do(NvimIO[None])
def mock_test_functions() -> Do:
    yield define_function('MyoTestDetermineRunner', List('file'), f'return "python"')
    yield define_function('MyoTestExecutable', List('runner'), f'return "python"')
    yield define_function('MyoTestBuildPosition', List('runner', 'pos'), f'return ["-c", "raise Exception(1)"]')
    yield define_function('MyoTestBuildArgs', List('runner', 'args'), f'return a:args')


class TestSpec(ExternalSpec):
    '''
    create the test command if it doesn't exist $create_cmd
    run a test comand $run
    '''

    def create_cmd(self) -> Expectation:
        @do(NvimIO[Ident])
        def run() -> Do:
            helper, aff, data = yield command_spec_data()
            yield mock_test_functions()
            (s1, ig) = yield vim_test_command.fun().run(helper.component_res(data))
            comp = yield N.e(s1.data.comp.commands.head.to_either('no commands'))
            return comp.ident
        return kn(self.vim, run).must(contain(test_ident))

    def run(self) -> Expectation:
        @do(NvimIO[None])
        def run() -> Do:
            helper, aff, data = yield command_spec_data()
            ds = DispatchState(helper.state, aff)
            yield mock_test_functions()
            (s1, ignore) = yield eval_trans.match(vim_test(RunCommandOptions.cons())).run(ds)
            cmd = yield N.e(s1.state.data_by_name('command'))
            log = yield N.e(cmd.log_by_ident(test_ident))
            return Lists.lines(log.read_text())
        return kn(self.vim, run).must(contain(end_with(target)))


# TODO test empty `ParseOutput`
class TestISpec(DefaultSpec):
    '''run a test command $run
    '''

    def _pre_start(self) -> None:
        variable_set_prefixed('components', List('command')).unsafe(self.vim)
        super()._pre_start()

    def run(self) -> Expectation:
        self._wait(.5)
        @do(NvimIO[List[str]])
        def run() -> Do:
            yield nvim_command('MyoStage1')
            self._wait(.5)
            yield mock_test_functions()
            yield self.json_cmd_sync('MyoVimTest')
            yield nvim_command('MyoParse')
            self._wait(.5)
            bufs = yield buffers()
            buf = yield N.from_maybe(bufs.lift(1), 'scratch buffer wasn\'t opened')
            yield buffer_content(buf)
        return kn(self.vim, run).must(contain(have_lines(target)))


__all__ = ('TestSpec',)
